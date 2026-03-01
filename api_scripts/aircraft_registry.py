"""
Static aircraft registry mapping models to manufacturers and ICAO codes.
This provides data for aircraft that the API doesn't return.
"""

AIRCRAFT_REGISTRY = {
    # Full model names (as they appear in API responses)
    "Airbus A320": {"manufacturer": "Airbus", "icao_type_code": "A320"},
    "Airbus A320 NEO": {"manufacturer": "Airbus", "icao_type_code": "A20N"},
    "Airbus A321": {"manufacturer": "Airbus", "icao_type_code": "A321"},
    "Airbus A321 NEO": {"manufacturer": "Airbus", "icao_type_code": "A21N"},
    "Airbus A330": {"manufacturer": "Airbus", "icao_type_code": "A330"},
    "Airbus A330-200": {"manufacturer": "Airbus", "icao_type_code": "A332"},
    "Airbus A330-300": {"manufacturer": "Airbus", "icao_type_code": "A333"},
    "Airbus A340": {"manufacturer": "Airbus", "icao_type_code": "A340"},
    "Airbus A340-300": {"manufacturer": "Airbus", "icao_type_code": "A343"},
    "Airbus A350": {"manufacturer": "Airbus", "icao_type_code": "A350"},
    "Airbus A350-900": {"manufacturer": "Airbus", "icao_type_code": "A359"},
    "Airbus A350-1000": {"manufacturer": "Airbus", "icao_type_code": "A35K"},
    "Boeing 737": {"manufacturer": "Boeing", "icao_type_code": "B737"},
    "Boeing 737-700": {"manufacturer": "Boeing", "icao_type_code": "B73G"},
    "Boeing 737-800": {"manufacturer": "Boeing", "icao_type_code": "B738"},
    "Boeing 737-900": {"manufacturer": "Boeing", "icao_type_code": "B739"},
    "Boeing 737 MAX 8": {"manufacturer": "Boeing", "icao_type_code": "B38M"},
    "Boeing 737 MAX 9": {"manufacturer": "Boeing", "icao_type_code": "B39M"},
    "Boeing 747": {"manufacturer": "Boeing", "icao_type_code": "B747"},
    "Boeing 747-400": {"manufacturer": "Boeing", "icao_type_code": "B744"},
    "Boeing 747-8": {"manufacturer": "Boeing", "icao_type_code": "B748"},
    "Boeing 757": {"manufacturer": "Boeing", "icao_type_code": "B757"},
    "Boeing 757-200": {"manufacturer": "Boeing", "icao_type_code": "B752"},
    "Boeing 757-300": {"manufacturer": "Boeing", "icao_type_code": "B753"},
    "Boeing 767": {"manufacturer": "Boeing", "icao_type_code": "B767"},
    "Boeing 767-300": {"manufacturer": "Boeing", "icao_type_code": "B763"},
    "Boeing 767-300 Passenger (winglets)": {"manufacturer": "Boeing", "icao_type_code": "B763"},
    "Boeing 777": {"manufacturer": "Boeing", "icao_type_code": "B777"},
    "Boeing 777-200": {"manufacturer": "Boeing", "icao_type_code": "B772"},
    "Boeing 777-300": {"manufacturer": "Boeing", "icao_type_code": "B773"},
    "Boeing 777-300ER": {"manufacturer": "Boeing", "icao_type_code": "B77L"},
    "Boeing 787": {"manufacturer": "Boeing", "icao_type_code": "B787"},
    "Boeing 787-8": {"manufacturer": "Boeing", "icao_type_code": "B788"},
    "Boeing 787-9": {"manufacturer": "Boeing", "icao_type_code": "B789"},
    "Boeing 787-10": {"manufacturer": "Boeing", "icao_type_code": "B78X"},
    "ATR 72": {"manufacturer": "ATR", "icao_type_code": "AT72"},
    "ATR 72-500": {"manufacturer": "ATR", "icao_type_code": "AT75"},
    "Embraer E170": {"manufacturer": "Embraer", "icao_type_code": "E170"},
    "Embraer E175": {"manufacturer": "Embraer", "icao_type_code": "E175"},
    "Embraer E190": {"manufacturer": "Embraer", "icao_type_code": "E190"},
    "Embraer E195": {"manufacturer": "Embraer", "icao_type_code": "E195"},
    
    # ICAO codes (legacy support for backward compatibility)
    "A320": {"manufacturer": "Airbus", "icao_type_code": "A320"},
    "A321": {"manufacturer": "Airbus", "icao_type_code": "A321"},
    "A330": {"manufacturer": "Airbus", "icao_type_code": "A330"},
    "A333": {"manufacturer": "Airbus", "icao_type_code": "A333"},
    "A350": {"manufacturer": "Airbus", "icao_type_code": "A350"},
    "B737": {"manufacturer": "Boeing", "icao_type_code": "B737"},
    "B738": {"manufacturer": "Boeing", "icao_type_code": "B738"},
    "B747": {"manufacturer": "Boeing", "icao_type_code": "B747"},
    "B777": {"manufacturer": "Boeing", "icao_type_code": "B777"},
    "B787": {"manufacturer": "Boeing", "icao_type_code": "B787"},
    "AT72": {"manufacturer": "ATR", "icao_type_code": "AT72"},
}


def get_aircraft_details(model: str) -> dict:
    """
    Get aircraft manufacturer and ICAO type code from registry.
    Handles both ICAO codes ("B737") and full names ("Boeing 737-800").
    
    Args:
        model (str): Aircraft model code or full name
    
    Returns:
        dict: Dictionary with 'manufacturer' and 'icao_type_code' keys
    """
    if not model:
        return {"manufacturer": None, "icao_type_code": None}
    
    model = str(model).strip()
    
    # Direct lookup (handles both full names and ICAO codes)
    if model in AIRCRAFT_REGISTRY:
        return AIRCRAFT_REGISTRY[model]
    
    # Case-insensitive lookup
    model_lower = model.lower()
    for key in AIRCRAFT_REGISTRY.keys():
        if key.lower() == model_lower:
            return AIRCRAFT_REGISTRY[key]
    
    # Partial match: if model string contains registry key
    for key in AIRCRAFT_REGISTRY.keys():
        if key in model or key.lower() in model.lower():
            return AIRCRAFT_REGISTRY[key]
    
    # Default: return None (allow NULL in DB)
    return {"manufacturer": None, "icao_type_code": None}
