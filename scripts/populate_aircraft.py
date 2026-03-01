#!/usr/bin/env python3
"""
Script to populate aircraft table with cached flight data and enrich with registry data.
"""

import os
import psycopg2
from dotenv import load_dotenv
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure project root is on sys.path when running from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_scripts.aircraft_registry import get_aircraft_details

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

# Step 1: Get all unique aircraft registrations from flights table
print("Step 1: Extracting unique aircraft registrations from flights...")
cur.execute("""
    SELECT DISTINCT aircraft_registration 
    FROM flights 
    WHERE aircraft_registration IS NOT NULL
""")

registrations = [row[0] for row in cur.fetchall()]
print(f"  Found {len(registrations)} unique aircraft registrations")

# Step 2: For each registration, we need to find the model
# We'll need to look at the flights table to find models
print("\nStep 2: Mapping registrations to models from API cache...")
cur.execute("""
    SELECT 
        f.aircraft_registration,
        a.model
    FROM flights f
    LEFT JOIN aircraft a ON f.aircraft_registration = a.registration
    WHERE f.aircraft_registration IS NOT NULL
    GROUP BY f.aircraft_registration, a.model
""")

aircraft_data = {}
for reg, model in cur.fetchall():
    if reg not in aircraft_data:
        aircraft_data[reg] = model

print(f"  Mapped {len(aircraft_data)} aircraft")

# Step 3: Insert aircraft with enriched data from registry
print("\nStep 3: Inserting aircraft with manufacturer and ICAO codes...")

insert_query = """
    INSERT INTO aircraft (registration, model, manufacturer, icao_type_code, owner)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (registration) DO UPDATE SET
        manufacturer = EXCLUDED.manufacturer,
        icao_type_code = EXCLUDED.icao_type_code
"""

inserted = 0
for reg, model in aircraft_data.items():
    if model:
        # Get details from registry
        details = get_aircraft_details(model)
        manufacturer = details.get("manufacturer")
        icao_type_code = details.get("icao_type_code")
        
        try:
            cur.execute(insert_query, (reg, model, manufacturer, icao_type_code, None))
            inserted += 1
            
            if inserted % 10 == 0:
                print(f"  [OK] Inserted {inserted} aircraft...")
        except Exception as e:
            logger.error(f"  [FAIL] Aircraft {reg}: {str(e)[:50]}")

conn.commit()

# Step 4: Verify results
print(f"\n{'='*60}")
print("VERIFICATION")
print(f"{'='*60}")

cur.execute("SELECT COUNT(*) FROM aircraft")
total = cur.fetchone()[0]
print(f"Total aircraft: {total}")

cur.execute("SELECT COUNT(*) FROM aircraft WHERE manufacturer IS NOT NULL")
mfg_count = cur.fetchone()[0]
print(f"Aircraft with manufacturer: {mfg_count}")

cur.execute("SELECT COUNT(*) FROM aircraft WHERE icao_type_code IS NOT NULL")
icao_count = cur.fetchone()[0]
print(f"Aircraft with ICAO type code: {icao_count}")

# Sample data
print(f"\n{'='*60}")
print("SAMPLE DATA")
print(f"{'='*60}")
cur.execute("""
    SELECT registration, model, manufacturer, icao_type_code 
    FROM aircraft 
    LIMIT 10
""")

for reg, model, mfg, icao in cur.fetchall():
    print(f"  {reg:<15} {model:<10} {str(mfg):<20} {icao}")

cur.close()
conn.close()

print(f"\n[DONE] Aircraft table enriched with manufacturer and ICAO codes!")
