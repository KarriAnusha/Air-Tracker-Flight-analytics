"""
Module for fetching flight data from AeroDataBox API.

This module provides functions to retrieve flight information including
departure and arrival data, flight status, and operational details.
Integrated with API optimization layer for caching and rate-limit handling.
"""

import logging
from typing import Dict, Optional
from urllib.parse import urlencode
from api_scripts.config import API_HOST, HEADERS
from api_scripts.api_optimizer import OptimizedAPICall

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_flights(iata_code: str, flight_type: str = "departures") -> Optional[Dict]:
    """
    Fetch flight data for a specific airport.
    
    Args:
        iata_code (str): The IATA code of the airport (e.g., 'DEL')
        flight_type (str): Type of flights to fetch ('departures' or 'arrivals')
    
    Returns:
        dict: Flight data from API, or None if request fails
    
    Example:
        >>> flights = fetch_flights('DEL', 'departures')
        >>> print(len(flights.get('departures', [])))  # Number of departure flights
    """
    
    url = f"https://{API_HOST}/flights/airports/iata/{iata_code}"
    
    # Query parameters for flight search
    querystring = {
        "offsetMinutes": "-120",
        "durationMinutes": "720",
        "withLeg": "true",
        "direction": "Both",
        "withCancelled": "true",
        "withCodeshared": "true",
        "withCargo": "true",
        "withPrivate": "true",
        "withLocation": "false"
    }
    
    # Build full URL with query parameters
    full_url = url + "?" + urlencode(querystring)
    
    # Use cache key that includes airport code for better tracking
    cache_key = f"{iata_code}_{flight_type}"
    
    result = OptimizedAPICall.call(
        url=full_url,
        headers=HEADERS,
        endpoint_name="flights_by_airport",
        cache_key=cache_key,
        timeout=10
    )
    
    if result:
        logger.info(f"Successfully fetched flights for {iata_code}")
    
    return result



