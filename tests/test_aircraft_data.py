import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api_scripts.fetch_flights import fetch_flights

# Fetch flights and inspect
flights_data = fetch_flights('DEL', 'departures')

if flights_data and 'departures' in flights_data:
    flights = flights_data['departures'][:5]
    
    print('Sample API responses for aircraft data:')
    print()
    
    for i, flight in enumerate(flights, 1):
        print(f'Flight {i}: {flight.get("number")}')
        print(f'  Has aircraft key: {"aircraft" in flight}')
        
        if 'aircraft' in flight:
            aircraft = flight['aircraft']
            print(f'  Aircraft data: {json.dumps(aircraft, indent=4)}')
            print(f'  Has "reg": {"reg" in aircraft}')
            print(f'  Has "registration": {"registration" in aircraft}')
        else:
            print('  NO aircraft key in flight data!')
        print()
