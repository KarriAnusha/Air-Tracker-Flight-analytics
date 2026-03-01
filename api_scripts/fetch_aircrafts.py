"""
Module for fetching aircraft data from AeroDataBox API.

This module provides functions to retrieve detailed aircraft information
including registration, model, manufacturer, ICAO type code, and owner.
Uses AeroDataBox's dedicated aircraft database endpoint.
Integrated with API optimization layer for caching and rate-limit handling.
"""

import logging
from typing import Dict, Optional
from api_scripts.config import API_HOST, HEADERS
from api_scripts.api_optimizer import OptimizedAPICall

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_aircraft(registration: str) -> Optional[Dict]:
    """
    Fetch aircraft data by registration from AeroDataBox API.
    
    NOTE: This function is disabled. Aircraft lookup returns 400 errors.
    Use static registry enrichment instead in insert_aircraft().
    
    Args:
        registration (str): The registration/tail number of the aircraft (e.g., 'N123AB')
    
    Returns:
        None (disabled)
    """
    logger.warning(f"Aircraft registration lookup disabled for {registration}. Using static registry instead.")
    return None


def fetch_aircraft_by_model(model: str) -> Optional[Dict]:
    """
    Fetch aircraft database entry by model code from AeroDataBox.
    
    Args:
        model (str): Aircraft model code (e.g., 'A320', 'B737')
    
    Returns:
        dict: Aircraft model data from API, or None if not found
    """
    
    url = f"https://{API_HOST}/aircrafts/models/{model}"
    
    return OptimizedAPICall.call(
        url=url,
        headers=HEADERS,
        endpoint_name="aircraft_by_model",
        cache_key=model,
        timeout=10
    )
