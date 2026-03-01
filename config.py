# Configuration for Air Tracker application

# List of airports that should be included in the analysis
# This serves as the "seed" set and is used throughout the app and
# data pipeline to restrict data to just these airport codes.
SEED_AIRPORTS = [
    "DEL",  # Delhi
    "BOM",  # Mumbai
    "BLR",  # Bangalore
    "HYD",  # Hyderabad
    "MAA",  # Chennai
    "CCU",  # Kolkata
    "COK",  # Kochi
    "AMD",  # Ahmedabad
    "PNQ",  # Pune
    "IXM",  # Indore
    "JAI",  # Jaipur
    "LKO",  # Lucknow
    "VTZ",  # Vizag
    "DXB",  # Dubai
    "LHR"   # London
]


def _sql_list():
    """Return the airport list as a SQL-friendly comma-separated string.

    Example:  `'DEL','BOM','BLR'`  (no surrounding parentheses)
    """
    return ",".join(f"'{code}'" for code in SEED_AIRPORTS)


def flight_filter_clause():
    """Return a WHERE clause fragment restricting flights to the seed airports.

    The resulting string filters on origin or destination matching one of the
    seed codes. It can be injected directly into a query using f-strings.
    """
    codes = _sql_list()
    return f"(origin_iata IN ({codes}) OR destination_iata IN ({codes}))"


def airport_filter_clause(alias: str = "", column: str = "iata_code"):
    """Return a WHERE clause fragment restricting airports to the seeds.

    Parameters
    ----------
    alias : str
        Optional table alias (including trailing dot, e.g. "ap.") so the
        caller can use the clause in joins.
    column : str
        Column name to check (default "iata_code", can also be "airport_iata").
    """
    codes = _sql_list()
    if alias and not alias.endswith("."):
        alias += "."
    return f"{alias}{column} IN ({codes})"


def num_seed_airports() -> int:
    """Return the number of seed airports (15)."""
    return len(SEED_AIRPORTS)
