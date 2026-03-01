"""
Module for fetching flight delay and statistics data from AeroDataBox API.

This module provides functions to retrieve flight status, delay statistics,
and operational metrics.
"""

import requests
from typing import Dict, Optional
import logging
import time
from datetime import datetime
from api_scripts.config import API_HOST, HEADERS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_airport_delays(flight_number: str) -> Optional[Dict]:
    """
    Fetch delay and status information for a specific flight.
    [DEPRECATED - Use fetch_airport_statistics instead]
    
    Args:
        flight_number (str): The flight number (e.g., 'BA123')
    
    Returns:
        dict: Flight delay and status data from API, or None if request fails
    """
    # This function is kept for backward compatibility but not actively used
    return None


def _to_int(value) -> Optional[int]:
    """Best-effort cast to int; returns None for empty/non-numeric values."""
    try:
        if value is None:
            return None
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _duration_to_minutes(value: Optional[str]) -> Optional[int]:
    """Convert HH:MM:SS-like duration strings to minutes."""
    if not value or not isinstance(value, str):
        return None
    try:
        parts = value.split(":")
        if len(parts) != 3:
            return None
        hours, minutes, seconds = (int(parts[0]), int(parts[1]), int(parts[2]))
        return int(round((hours * 3600 + minutes * 60 + seconds) / 60))
    except (TypeError, ValueError):
        return None


def _normalize_current_delay_snapshot(payload: Dict) -> Optional[Dict]:
    """
    Normalize current /airports/iata/{code}/delays payload.

    Example fields:
    - departuresDelayInformation.numTotal / numCancelled / medianDelay / delayIndex
    - arrivalsDelayInformation.numTotal / numCancelled / medianDelay / delayIndex
    """
    dep = payload.get("departuresDelayInformation") or {}
    arr = payload.get("arrivalsDelayInformation") or {}
    if not dep and not arr:
        return None

    dep_total = _to_int(dep.get("numTotal")) or 0
    arr_total = _to_int(arr.get("numTotal")) or 0
    total = dep_total + arr_total

    dep_cancel = _to_int(dep.get("numCancelled")) or 0
    arr_cancel = _to_int(arr.get("numCancelled")) or 0
    cancelled = dep_cancel + arr_cancel

    dep_idx = dep.get("delayIndex")
    arr_idx = arr.get("delayIndex")
    dep_idx = float(dep_idx) if dep_idx is not None else None
    arr_idx = float(arr_idx) if arr_idx is not None else None

    weighted_idx = None
    if total > 0:
        dep_w = dep_total / total
        arr_w = arr_total / total
        d = dep_idx if dep_idx is not None else 0.0
        a = arr_idx if arr_idx is not None else 0.0
        weighted_idx = (d * dep_w) + (a * arr_w)

    delayed = _to_int(total * weighted_idx) if (weighted_idx is not None and total > 0) else None

    dep_med = _duration_to_minutes(dep.get("medianDelay"))
    arr_med = _duration_to_minutes(arr.get("medianDelay"))
    med_values = [v for v in [dep_med, arr_med] if v is not None]
    median = _to_int(sum(med_values) / len(med_values)) if med_values else None

    return {
        "statistics": {
            "totalFlights": total if total > 0 else None,
            "delayedFlights": delayed,
            "cancelledFlights": cancelled,
            "averageDelay": median,
            "medianDelay": median,
        }
    }


def _normalize_statistics(payload: Dict) -> Optional[Dict]:
    """Normalize diverse AeroDataBox payloads to the app's expected schema."""
    if not isinstance(payload, dict):
        return None

    # First handle the current-delay snapshot shape.
    snapshot = _normalize_current_delay_snapshot(payload)
    if snapshot:
        return snapshot

    # Supported shapes seen across endpoint variants.
    candidates = []
    if isinstance(payload.get("statistics"), dict):
        candidates.append(payload["statistics"])
    if isinstance(payload.get("delay"), dict):
        candidates.append(payload["delay"])
    if isinstance(payload.get("delays"), dict):
        candidates.append(payload["delays"])
    if isinstance(payload.get("arrivalDelay"), dict):
        candidates.append(payload["arrivalDelay"])
    if isinstance(payload.get("departureDelay"), dict):
        candidates.append(payload["departureDelay"])
    candidates.append(payload)

    mapped = {
        "totalFlights": None,
        "delayedFlights": None,
        "cancelledFlights": None,
        "averageDelay": None,
        "medianDelay": None,
    }

    key_aliases = {
        "totalFlights": ["totalFlights", "total", "totalCount", "flightsTotal", "count"],
        "delayedFlights": [
            "delayedFlights", "delayed", "delayedCount", "flightsDelayed", "delayCount"
        ],
        "cancelledFlights": [
            "cancelledFlights", "canceledFlights", "cancelled", "canceled", "cancelledCount", "canceledCount"
        ],
        "averageDelay": [
            "averageDelay", "avgDelay", "averageDelayMinutes", "avgDelayMinutes", "meanDelayMinutes"
        ],
        "medianDelay": [
            "medianDelay", "medianDelayMinutes", "p50DelayMinutes", "delayMedian"
        ],
    }

    for source in candidates:
        if not isinstance(source, dict):
            continue
        for target_key, aliases in key_aliases.items():
            if mapped[target_key] is not None:
                continue
            for alias in aliases:
                if alias in source:
                    mapped[target_key] = _to_int(source.get(alias))
                    break

    if not any(v is not None for v in mapped.values()):
        return None

    # Keep delayed <= total when both exist.
    if mapped["totalFlights"] is not None and mapped["delayedFlights"] is not None:
        mapped["delayedFlights"] = min(mapped["delayedFlights"], mapped["totalFlights"])

    return {"statistics": mapped}


def fetch_airport_statistics(iata_code: str, date_str: str) -> Optional[Dict]:
    """
    Fetch airport delay statistics for a specific date.

    Args:
        iata_code (str): The IATA code of the airport (e.g., 'DEL')
        date_str (str): Date in YYYY-MM-DD format

    Returns:
        dict: Normalized airport statistics or None when unavailable
    """
    # Use the plan-compatible endpoint; historical path endpoint may be unavailable.
    today_local = datetime.now().strftime("%Y-%m-%d")
    if date_str == today_local:
        candidate_urls = [
            (f"https://{API_HOST}/airports/iata/{iata_code}/delays", None),
        ]
    else:
        candidate_urls = [
            (f"https://{API_HOST}/airports/iata/{iata_code}/delays", {"dateLocal": date_str}),
            (f"https://{API_HOST}/airports/iata/{iata_code}/delays", None),
        ]

    for url, params in candidate_urls:
        try:
            # Retry briefly for transient rate-limits, then fail fast.
            for attempt in range(2):
                response = requests.get(url, headers=HEADERS, params=params, timeout=20)

                if response.status_code == 429:
                    wait_s = [2, 5][attempt]
                    logger.warning(
                        "Delay stats rate-limited for %s on %s (attempt %s/2). Waiting %ss",
                        iata_code, date_str, attempt + 1, wait_s
                    )
                    time.sleep(wait_s)
                    if attempt == 1:
                        # Global rate-limit likely active; do not try alternate endpoint now.
                        return None
                    continue

                # 4xx (except 429 handled above) likely means endpoint/plan mismatch.
                if response.status_code in (400, 401, 402, 403, 404):
                    logger.warning(
                        "Delay stats endpoint rejected for %s on %s (status %s): %s",
                        iata_code, date_str, response.status_code, url
                    )
                    break

                response.raise_for_status()
                normalized = _normalize_statistics(response.json())
                if normalized:
                    return normalized

                logger.warning(
                    "Delay stats payload could not be normalized for %s on %s (%s)",
                    iata_code, date_str, url
                )
                break
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Delay stats request failed for %s on %s (%s): %s",
                iata_code, date_str, url, str(exc)[:120]
            )

    return None
