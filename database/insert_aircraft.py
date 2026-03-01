from database.db_utils import execute_query
from api_scripts.aircraft_registry import get_aircraft_details
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_aircraft(data: dict):
    if not data.get("reg"):
        return

    query = """
    INSERT INTO aircraft (
        registration, model, manufacturer, icao_type_code, owner
    )
    VALUES (%s,%s,%s,%s,%s)
    ON CONFLICT (registration) DO UPDATE SET
        manufacturer = EXCLUDED.manufacturer,
        icao_type_code = EXCLUDED.icao_type_code,
        owner = COALESCE(EXCLUDED.owner, aircraft.owner);
    """

    # Get model from API flight data
    model = data.get("model")
    
    # Initialize from API response (flight data)
    manufacturer = data.get("manufacturer")
    icao_type_code = data.get("icaoType")
    
    # Fallback to static registry if missing
    # The registry has comprehensive manufacturer and ICAO codes for common aircraft
    if not manufacturer or not icao_type_code:
        aircraft_details = get_aircraft_details(model)
        if not manufacturer and aircraft_details.get("manufacturer"):
            manufacturer = aircraft_details.get("manufacturer")
        if not icao_type_code and aircraft_details.get("icao_type_code"):
            icao_type_code = aircraft_details.get("icao_type_code")

    values = (
        data.get("reg"),
        model,
        manufacturer,
        icao_type_code,
        data.get("owner")
    )

    try:
        execute_query(query, values)
    except Exception as e:
        logger.error(f"Failed to insert aircraft {data.get('reg')}: {str(e)[:60]}")
