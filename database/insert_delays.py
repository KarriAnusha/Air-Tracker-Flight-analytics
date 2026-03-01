from database.db_utils import execute_query

def insert_delay(iata_code: str, data: dict):
    stats = data.get("statistics") or {}

    query = """
    INSERT INTO airport_delays (
        airport_iata, delay_date, total_flights,
        delayed_flights, avg_delay_min,
        median_delay_min, canceled_flights
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (airport_iata, delay_date)
    DO UPDATE SET
        total_flights = EXCLUDED.total_flights,
        delayed_flights = EXCLUDED.delayed_flights,
        avg_delay_min = EXCLUDED.avg_delay_min,
        median_delay_min = EXCLUDED.median_delay_min,
        canceled_flights = EXCLUDED.canceled_flights;
    """

    values = (
        iata_code,
        data.get("date"),
        stats.get("totalFlights"),
        stats.get("delayedFlights"),
        stats.get("averageDelay"),
        stats.get("medianDelay"),
        stats.get("cancelledFlights")
    )

    execute_query(query, values)

