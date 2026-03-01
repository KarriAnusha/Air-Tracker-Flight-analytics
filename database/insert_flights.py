from database.db_utils import execute_query
from datetime import datetime, timedelta


def _parse_iso(dt_str):
    if not dt_str:
        return None
    try:
        # Handle both "YYYY-MM-DD HH:MM+TZ" and ISO strings.
        return datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
    except ValueError:
        return None


def _fix_midnight_rollover(scheduled_str, actual_str):
    """
    Fix API rows where actual time is on the next day but date is not advanced.
    If actual is >12h earlier than scheduled, shift actual by +1 day.
    """
    if not scheduled_str or not actual_str:
        return actual_str

    scheduled_dt = _parse_iso(scheduled_str)
    actual_dt = _parse_iso(actual_str)
    if not scheduled_dt or not actual_dt:
        return actual_str

    if (scheduled_dt - actual_dt) > timedelta(hours=12):
        fixed_dt = actual_dt + timedelta(days=1)
        return fixed_dt.isoformat(sep=" ")

    return actual_str

def insert_flight(flight: dict, origin_iata: str = None):
    query = """
    INSERT INTO flights (
        flight_number, aircraft_registration,
        origin_iata, destination_iata,
        scheduled_departure, actual_departure,
        scheduled_arrival, actual_arrival,
        status, airline_code
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT DO NOTHING;
    """

    # Airline code
    airline = flight.get("airline")
    if isinstance(airline, dict):
        airline = airline.get("iata")

    # Aircraft registration
    aircraft = flight.get("aircraft")
    if isinstance(aircraft, dict):
        aircraft = aircraft.get("reg") or aircraft.get("registration")
    else:
        aircraft = None

    # Avoid FK failures when API has not yet assigned an aircraft.
    if aircraft in ("Not Yet Assigned", "", "TBD", "N/A"):
        aircraft = None

    # Flight number
    flight_number = flight.get("number")
    if isinstance(flight_number, dict):
        flight_number = flight_number.get("iata")

    departure = flight.get("departure") or {}
    arrival = flight.get("arrival") or {}

    # Extract times from nested structure
    scheduled_dep = None
    actual_dep = None
    if departure.get("scheduledTime"):
        scheduled_dep = departure["scheduledTime"].get("local")
    if departure.get("actualTime"):
        actual_dep = departure["actualTime"].get("local")
    elif departure.get("revisedTime"):
        actual_dep = departure["revisedTime"].get("local")

    scheduled_arr = None
    actual_arr = None
    if arrival.get("scheduledTime"):
        scheduled_arr = arrival["scheduledTime"].get("local")
    if arrival.get("actualTime"):
        actual_arr = arrival["actualTime"].get("local")
    elif arrival.get("revisedTime"):
        actual_arr = arrival["revisedTime"].get("local")

    # Correct midnight rollover anomalies in API local timestamps.
    actual_dep = _fix_midnight_rollover(scheduled_dep, actual_dep)
    actual_arr = _fix_midnight_rollover(scheduled_arr, actual_arr)

    # Extract airport IATAs
    dest_iata = arrival.get("airport", {}).get("iata")
    
    # Skip flights with missing destination airport
    if not dest_iata:
        return False

    # Populate status: use API value if available, otherwise default to 'On Time'
    status = flight.get("status") or "On Time"
    
    # Normalize status: convert "Unknown" to "Expected" for flights without actual departure
    if status == "Unknown" and not actual_dep:
        status = "Expected"

    values = (
        flight_number,
        aircraft,
        origin_iata,
        dest_iata,
        scheduled_dep,
        actual_dep,
        scheduled_arr,
        actual_arr,
        status,
        airline
    )

    execute_query(query, values)
    return True

