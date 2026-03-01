"""
Module for fetching airport data from AeroDataBox API.

This module provides functions to retrieve detailed airport information
including codes, location data, and timezone information.
Integrated with API optimization layer for caching and rate-limit handling.
"""

import logging
from typing import Dict, Optional
from api_scripts.config import API_HOST, HEADERS
from api_scripts.api_optimizer import OptimizedAPICall

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_airport(iata_code: str) -> Optional[Dict]:
    """
    Fetch airport data by IATA code from AeroDataBox API.
    
    Args:
        iata_code (str): The IATA code of the airport (e.g., 'DEL', 'LAX')
    
    Returns:
        dict: Airport data from API, or None if request fails
        
    Example:
        >>> airport_data = fetch_airport('DEL')
        >>> print(airport_data['name'])  # 'Indira Gandhi International Airport'
    """
    
    url = f"https://{API_HOST}/airports/iata/{iata_code}"
    
    return OptimizedAPICall.call(
        url=url,
        headers=HEADERS,
        endpoint_name="airport_by_iata",
        cache_key=iata_code,
        timeout=10
    )
