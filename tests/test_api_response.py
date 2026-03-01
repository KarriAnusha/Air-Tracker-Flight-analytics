import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_scripts.fetch_flights import fetch_flights

print("Fetching sample flight data from DEL...")
data = fetch_flights('DEL', 'departures')

if data and data.get('departures'):
    flight = data['departures'][0]
    print("\n=== FIRST FLIGHT DATA ===")
    print(json.dumps(flight, indent=2, default=str))
else:
    print("No flight data returned")
