from database.db_utils import execute_query


def insert_airport(data: dict):
    query = """
    INSERT INTO airport (
        icao_code, iata_code, name, city, country,
        continent, latitude, longitude, timezone
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (iata_code) DO NOTHING;
    """

    country = data.get("country")
    if isinstance(country, dict):
        country = country.get("name")

    continent = data.get("continent")
    if isinstance(continent, dict):
        continent = continent.get("name")

    location = data.get("location") or {}
    
    # Prioritize fullName over shortName for airport name
    airport_name = data.get("fullName") or data.get("shortName") or data.get("name")
    
    # Prioritize municipalityName, fallback to city
    city = data.get("municipalityName") or data.get("city")

    values = (
        data.get("icao"),
        data.get("iata"),
        airport_name,
        city,
        country,
        continent,
        location.get("lat"),
        location.get("lon"),
        data.get("timeZone")
    )

    execute_query(query, values)

