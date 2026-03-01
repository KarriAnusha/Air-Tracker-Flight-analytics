import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from api_scripts.fetch_flights import fetch_flights

# Fetch flights and inspect aircraft data
flights_data = fetch_flights('DEL', 'departures')

if flights_data and 'departures' in flights_data:
    flights = flights_data['departures'][:5]
    
    print('Aircraft data from API (looking for owner field):')
    print()
    
    for i, flight in enumerate(flights, 1):
        print(f'Flight {i}: {flight.get("number")}')
        
        if 'aircraft' in flight:
            aircraft = flight['aircraft']
            print(f'  Aircraft keys available: {list(aircraft.keys())}')
            print(f'  Full aircraft data: {json.dumps(aircraft, indent=4)}')
        print()
