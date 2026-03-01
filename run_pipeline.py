from api_scripts.fetch_airports import fetch_airport
from api_scripts.fetch_flights import fetch_flights
from api_scripts.fetch_delays import fetch_airport_statistics

from database.insert_airport import insert_airport
from database.insert_aircraft import insert_aircraft
from database.insert_flights import insert_flight
from database.insert_delays import insert_delay
from database.db_utils import execute_query
from datetime import datetime, timedelta
import os

# deferring to a central configuration file so the list is
# shared across the pipeline and the web application.
from config import SEED_AIRPORTS

AIRPORTS = SEED_AIRPORTS  # 15 major airports only

# For delays: fetch flights from 5 major hubs only (to limit API calls)
FLIGHT_AIRPORTS = ["DEL", "BOM", "BLR", "DXB", "LHR"]


def _delay_scope():
    """
    Return delay fetch scope from env vars.

    Env vars:
    - DELAY_AIRPORTS: comma-separated IATA list (example: DEL,BOM,BLR)
    - DELAY_DAYS: number of days back including today (default: 1)
    """
    raw_airports = os.getenv("DELAY_AIRPORTS", "").strip()
    if raw_airports:
        chosen = [code.strip().upper() for code in raw_airports.split(",") if code.strip()]
        delay_airports = [code for code in chosen if code in AIRPORTS]
    else:
        # Safe default for free-tier quotas.
        delay_airports = AIRPORTS[:3]

    if not delay_airports:
        delay_airports = AIRPORTS[:3]

    try:
        delay_days = int(os.getenv("DELAY_DAYS", "1"))
    except ValueError:
        delay_days = 1
    delay_days = max(1, min(delay_days, 30))

    return delay_airports, delay_days


def run_pipeline():
    # Lightweight schema migration for projects that started before owner support.
    execute_query("ALTER TABLE aircraft ADD COLUMN IF NOT EXISTS owner TEXT;")

    # Phase 1: Fetch and insert all airports first
    print(f"\n{'='*50}")
    print("PHASE 1: Fetching all airports")
    print(f"{'='*50}")
    
    all_airports = set()
    airport_cache = {}
    
    # First pass: collect all unique airports
    for airport_code in AIRPORTS:
        print(f"[1.1] Fetching airport data for {airport_code}...")
        try:
            airport_data = fetch_airport(airport_code)
            if airport_data:
                iata = airport_data.get('iata')
                print(f"    [OK] Got: {iata}")
                airport_cache[iata] = airport_data
                all_airports.add(iata)
        except Exception as e:
            print(f"    [SKIP] {airport_code}: {str(e)[:40]}")
    
    # Insert all airports
    print(f"\n[1.2] Inserting {len(all_airports)} airports...")
    for iata, airport_data in airport_cache.items():
        try:
            insert_airport(airport_data)
            print(f"    [OK] {iata}")
        except Exception as e:
            print(f"    [FAIL] {iata}: {str(e)[:50]}")
    
    # Phase 2: Fetch and process flights
    print(f"\n{'='*50}")
    print("PHASE 2: Fetching flights and aircraft")
    print(f"{'='*50}")
    
    flight_count = 0
    for airport_code in FLIGHT_AIRPORTS:
        for direction in ["departures", "arrivals"]:
            print(f"\n[2.1] Fetching {direction} for {airport_code}...")
            try:
                flights_response = fetch_flights(airport_code, direction)
                if flights_response:
                    flights_data = flights_response.get(direction, [])
                    print(f"    [OK] Got {len(flights_data)} flights")
                else:
                    print(f"    [SKIP] No flights data returned")
                    flights_data = []
            except Exception as e:
                print(f"    [SKIP] {airport_code} {direction}: {str(e)[:40]}")
                flights_data = []

            for i, flight in enumerate(flights_data[:50], 1):  # Limit to 50 flights per airport per direction
                try:
                    dep_airport = flight.get("departure", {}).get("airport", {}).get("iata")
                    dest_airport = flight.get("arrival", {}).get("airport", {}).get("iata")

                    if direction == "departures":
                        # Keep only routes that terminate in seed airports.
                        if dest_airport not in AIRPORTS:
                            continue
                        origin_for_insert = airport_code
                    else:
                        # Keep only routes that originate in seed airports.
                        if dep_airport not in AIRPORTS:
                            continue
                        origin_for_insert = dep_airport

                    # Aircraft - extract from flight data and insert
                    aircraft_data = flight.get("aircraft", {})
                    if aircraft_data and aircraft_data.get("reg"):
                        try:
                            # Prepare aircraft data with all available fields
                            aircraft_insert_data = {
                                "reg": aircraft_data.get("reg") or aircraft_data.get("registration"),
                                "model": aircraft_data.get("model"),
                                "manufacturer": aircraft_data.get("manufacturer"),
                                "icaoType": aircraft_data.get("icaoType"),
                                "owner": aircraft_data.get("owner")
                            }
                            insert_aircraft(aircraft_insert_data)
                        except Exception:
                            pass  # Aircraft insert errors are not critical

                    # Flight - only insert flights that remained after the filter
                    success = insert_flight(flight, origin_iata=origin_for_insert)
                    if success:
                        flight_count += 1
                        if i % 10 == 0:
                            print(f"    [OK] Inserted {i} {direction}")
                except Exception as e:
                    print(f"    [FAIL] Flight error: {str(e)[:60]}")

    # Repair historical midnight-rollover anomalies in existing rows.
    execute_query(
        """
        UPDATE flights
        SET actual_departure = actual_departure + INTERVAL '1 day'
        WHERE actual_departure IS NOT NULL
          AND scheduled_departure IS NOT NULL
          AND (scheduled_departure - actual_departure) > INTERVAL '12 hours';
        """
    )
    execute_query(
        """
        UPDATE flights
        SET actual_arrival = actual_arrival + INTERVAL '1 day'
        WHERE actual_arrival IS NOT NULL
          AND scheduled_arrival IS NOT NULL
          AND (scheduled_arrival - actual_arrival) > INTERVAL '12 hours';
        """
    )
    
    # Phase 3: Fetch and insert airport delay statistics
    print(f"\n{'='*50}")
    print("PHASE 3: Fetching airport delay statistics (7 days)")
    print(f"{'='*50}")

    # Ensure upsert key exists for delay records on already-provisioned databases.
    # 1) Remove historical duplicates so index creation can succeed.
    execute_query(
        """
        WITH ranked AS (
            SELECT
                delay_id,
                ROW_NUMBER() OVER (
                    PARTITION BY airport_iata, delay_date
                    ORDER BY delay_id DESC
                ) AS rn
            FROM airport_delays
        )
        DELETE FROM airport_delays d
        USING ranked r
        WHERE d.delay_id = r.delay_id
          AND r.rn > 1;
        """
    )

    # 2) Create the unique key used by ON CONFLICT upserts.
    execute_query(
        "CREATE UNIQUE INDEX IF NOT EXISTS airport_delays_airport_date_uidx "
        "ON airport_delays (airport_iata, delay_date);"
    )
    
    delay_count = 0
    today = datetime.now()
    
    delay_airports, delay_days = _delay_scope()
    print(f"Delay scope: {len(delay_airports)} airport(s), {delay_days} day(s)")

    # Fetch historical delay data for selected scope.
    for days_back in range(delay_days):
        delay_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        print(f"\n[3.{days_back+1}] Fetching delays for {delay_date}...")
        
        for iata_code in delay_airports:
            try:
                stats_data = fetch_airport_statistics(iata_code, delay_date)
                if stats_data:
                    # Prepare delay data with the date
                    delay_insert_data = {
                        "date": delay_date,
                        "statistics": stats_data.get("statistics", {})
                    }
                    insert_delay(iata_code, delay_insert_data)
                    delay_count += 1
                    if delay_count % 10 == 0:
                        print(f"    [OK] Inserted {delay_count} delay records")
            except Exception as e:
                pass  # Delay insert errors are not critical; continue
    
    print(f"\n{'='*50}")
    print(f"[DONE] Pipeline completed!")
    print(f"  Airports: {len(all_airports)}")
    print(f"  Flights: {flight_count}")
    print(f"  Delay records: {delay_count}")
    print(f"{'='*50}")


if __name__ == "__main__":
    run_pipeline()

