#!/usr/bin/env python3
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json
from datetime import datetime, date
from pathlib import Path

load_dotenv()

# Connect to database
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", "5432")
)

cur = conn.cursor(cursor_factory=RealDictCursor)

def serialize_datetime(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj

queries = {
    "1. Total flights per aircraft model": """
SELECT a.model,
       COUNT(*) AS flight_count
FROM flights f
JOIN aircraft a ON f.aircraft_registration = a.registration
GROUP BY a.model
ORDER BY flight_count DESC;
""",
    "2. Aircraft (>5 flights)": """
SELECT a.registration,
       a.model,
       COUNT(*) AS flight_count
FROM flights f
JOIN aircraft a ON f.aircraft_registration = a.registration
GROUP BY a.registration, a.model
HAVING COUNT(*) > 5
ORDER BY flight_count DESC;
""",
    "3. Airports with outbound flights (>5)": """
SELECT ap.name,
       ap.iata_code,
       COUNT(*) AS outbound_count
FROM flights f
JOIN airport ap ON f.origin_iata = ap.iata_code
GROUP BY ap.name, ap.iata_code
HAVING COUNT(*) > 5
ORDER BY outbound_count DESC;
""",
    "4. Top 3 destination airports by arrivals": """
SELECT ap.name,
       ap.city,
       ap.iata_code,
       COUNT(*) AS arrivals
FROM flights f
JOIN airport ap ON f.destination_iata = ap.iata_code
GROUP BY ap.name, ap.city, ap.iata_code
ORDER BY arrivals DESC
LIMIT 3;
""",
    "5. Flights with Domestic/International label": """
SELECT f.flight_number,
       orig.name   AS origin,
       dest.name   AS destination,
       CASE WHEN orig.country = dest.country THEN 'Domestic' ELSE 'International' END AS route_type
FROM flights f
LEFT JOIN airport orig ON f.origin_iata = orig.iata_code
LEFT JOIN airport dest ON f.destination_iata = dest.iata_code;
""",
    "6. 5 most recent arrivals at DEL": """
SELECT f.flight_number,
       f.aircraft_registration,
       orig.name AS departure_airport,
       COALESCE(f.actual_arrival, f.scheduled_arrival) AS arrival_time
FROM flights f
LEFT JOIN airport orig ON f.origin_iata = orig.iata_code
WHERE f.destination_iata = 'DEL'
ORDER BY COALESCE(f.actual_arrival, f.scheduled_arrival) DESC
LIMIT 5;
""",
    "7. Airports with no arriving flights": """
SELECT ap.iata_code,
       ap.name,
       ap.city
FROM airport ap
LEFT JOIN flights f ON ap.iata_code = f.destination_iata
WHERE f.flight_id IS NULL;
""",
    "8. Flights by airline and status": """
SELECT f.airline_code,
       SUM(CASE WHEN f.status = 'On Time' THEN 1 ELSE 0 END)    AS on_time,
       SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END)    AS delayed,
       SUM(CASE WHEN f.status = 'Cancelled' THEN 1 ELSE 0 END)  AS cancelled,
       COUNT(*)                                                AS total
FROM flights f
GROUP BY f.airline_code
ORDER BY total DESC;
""",
    "9. Cancelled flights": """
SELECT f.flight_number,
       f.aircraft_registration,
       orig.name AS origin,
       dest.name AS destination,
       f.scheduled_departure
FROM flights f
LEFT JOIN airport orig ON f.origin_iata = orig.iata_code
LEFT JOIN airport dest ON f.destination_iata = dest.iata_code
WHERE f.status = 'Cancelled'
ORDER BY f.scheduled_departure DESC;
""",
    "10. City pairs with >2 aircraft models": """
SELECT orig.iata_code AS origin_iata,
       dest.iata_code AS destination_iata,
       orig.city        AS origin_city,
       dest.city        AS destination_city,
       COUNT(DISTINCT a.model) AS distinct_models
FROM flights f
LEFT JOIN aircraft a ON f.aircraft_registration = a.registration
LEFT JOIN airport orig ON f.origin_iata = orig.iata_code
LEFT JOIN airport dest ON f.destination_iata = dest.iata_code
GROUP BY orig.iata_code, dest.iata_code, orig.city, dest.city
HAVING COUNT(DISTINCT a.model) > 2
ORDER BY distinct_models DESC;
""",
    "11. Delayed arrivals % by destination airport": """
SELECT ap.iata_code,
       ap.name,
       ap.city,
       COUNT(*) AS total_arrivals,
       SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) AS delayed_arrivals,
       ROUND(100.0 * SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) / NULLIF(COUNT(*),0), 2) AS pct_delayed
FROM flights f
JOIN airport ap ON f.destination_iata = ap.iata_code
GROUP BY ap.iata_code, ap.name, ap.city
ORDER BY pct_delayed DESC;
"""
}

results = {}

for title, query in queries.items():
    try:
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")
        cur.execute(query)
        rows = cur.fetchall()
        results[title] = rows
        
        if not rows:
            print("(No results)")
        else:
            # Print header
            headers = list(rows[0].keys())
            print("  ".join(f"{h:<20}" for h in headers))
            print("-" * len("  ".join(f"{h:<20}" for h in headers)))
            
            # Print rows
            for row in rows:
                values = [str(serialize_datetime(row[h])) for h in headers]
                print("  ".join(f"{v:<20}" for v in values))
        
        print(f"\nTotal rows: {len(rows)}")
    except Exception as e:
        print(f"ERROR: {e}")
        results[title] = {"error": str(e)}

cur.close()
conn.close()

# Save results to JSON in project root
project_root = Path(__file__).resolve().parent.parent
output_file = project_root / "query_results.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n{'='*80}")
print(f"Results saved to {output_file}")
