import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db_connection import get_connection

conn = get_connection()
cur = conn.cursor()

tables = ['flights','airport','aircraft','airport_delays']
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'{t}:', cur.fetchone()[0])
    except Exception as e:
        print(f'{t}: ERROR', e)

print('\nTop routes sample:')
cur.execute('SELECT origin_iata,destination_iata,COUNT(*) as flight_count FROM flights GROUP BY origin_iata,destination_iata ORDER BY flight_count DESC LIMIT 5')
print(cur.fetchall())

print('\nTop departures sample:')
cur.execute('SELECT f.origin_iata, COUNT(*) as departure_count FROM flights f GROUP BY f.origin_iata ORDER BY departure_count DESC LIMIT 5')
print(cur.fetchall())

print('\nTop arrivals sample:')
cur.execute('SELECT f.destination_iata, COUNT(*) as arrival_count FROM flights f GROUP BY f.destination_iata ORDER BY arrival_count DESC LIMIT 5')
print(cur.fetchall())

cur.close()
conn.close()
