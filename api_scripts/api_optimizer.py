"""
API Optimization Layer for managing rate limits and caching.
Implements smart caching, throttling, and retry logic to maximize free tier usage.
"""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = "api_cache"
CACHE_EXPIRY_HOURS = 0  # Disabled: always fetch fresh API responses
RATE_LIMIT_RETRY_DELAY = 60  # Start with 60 seconds

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)


class APICache:
    """Persistent cache for API responses to minimize API calls."""
    
    @staticmethod
    def _get_cache_path(endpoint: str, param: str) -> str:
        """Generate cache file path for an endpoint."""
        safe_param = param.replace("/", "_").replace(":", "_")
        return os.path.join(CACHE_DIR, f"{endpoint}_{safe_param}.json")
    
    @staticmethod
    def _is_cache_valid(cache_path: str) -> bool:
        """Check if cache file is still valid (not expired)."""
        if not os.path.exists(cache_path):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_path)
        max_age = CACHE_EXPIRY_HOURS * 3600
        
        return file_age < max_age
    
    @staticmethod
    def get(endpoint: str, param: str) -> Optional[Dict]:
        """Get cached response if available and valid."""
        if CACHE_EXPIRY_HOURS <= 0:
            return None

        cache_path = APICache._get_cache_path(endpoint, param)
        
        if APICache._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Cache HIT: {endpoint} {param}")
                return data
            except Exception as e:
                logger.warning(f"Cache read error: {str(e)[:50]}")
        
        logger.debug(f"Cache MISS: {endpoint} {param}")
        return None
    
    @staticmethod
    def set(endpoint: str, param: str, data: Dict) -> None:
        """Save response to cache."""
        if CACHE_EXPIRY_HOURS <= 0:
            return

        cache_path = APICache._get_cache_path(endpoint, param)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cache SAVE: {endpoint} {param}")
        except Exception as e:
            logger.warning(f"Cache write error: {str(e)[:50]}")
    
    @staticmethod
    def clear_expired():
        """Clean up expired cache files."""
        if not os.path.exists(CACHE_DIR):
            return
        
        cleared = 0
        for filename in os.listdir(CACHE_DIR):
            cache_path = os.path.join(CACHE_DIR, filename)
            if not APICache._is_cache_valid(cache_path):
                try:
                    os.remove(cache_path)
                    cleared += 1
                except Exception as e:
                    logger.warning(f"Cache clear error: {str(e)[:50]}")
        
        if cleared > 0:
            logger.info(f"Cleared {cleared} expired cache files")


class RateLimitHandler:
    """Handles API rate limiting with exponential backoff."""
    
    def __init__(self):
        self.retry_after = 0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
    
    def should_retry(self) -> bool:
        """Check if we should retry after rate limit."""
        return self.consecutive_failures < self.max_consecutive_failures
    
    def handle_rate_limit(self) -> int:
        """Calculate wait time for rate limit."""
        wait_time = RATE_LIMIT_RETRY_DELAY * (2 ** self.consecutive_failures)
        wait_time = min(wait_time, 300)  # Cap at 5 minutes
        
        logger.warning(f"Rate limited! Waiting {wait_time}s before retry...")
        return wait_time
    
    def reset(self):
        """Reset rate limit counter on success."""
        self.consecutive_failures = 0
        self.retry_after = 0
    
    def record_failure(self):
        """Record a rate limit failure."""
        self.consecutive_failures += 1


class OptimizedAPICall:
    """Wrapper for API calls with caching, throttling, and retry logic."""
    
    _rate_limiter = RateLimitHandler()
    _last_request_time = 0
    _request_throttle_delay = 0.5  # Minimum delay between requests (seconds)
    
    @staticmethod
    def call(
        url: str,
        headers: Dict,
        endpoint_name: str = "unknown",
        cache_key: str = None,
        timeout: int = 10
    ) -> Optional[Dict]:
        """
        Make an optimized API call with caching and rate-limit handling.
        
        Args:
            url: Full API endpoint URL
            headers: Request headers (including API key)
            endpoint_name: Name of endpoint for logging
            cache_key: Key for caching (if None, no caching)
            timeout: Request timeout in seconds
        
        Returns:
            API response as dict, or None if failed
        """
        
        # Check cache first if enabled
        if cache_key:
            cached = APICache.get(endpoint_name, cache_key)
            if cached:
                return cached
        
        # Throttle requests to avoid hammering API
        OptimizedAPICall._throttle()
        
        retry_count = 0
        max_retries = 2
        
        while retry_count <= max_retries:
            try:
                logger.info(f"API CALL: {endpoint_name} {cache_key or ''}")
                
                response = requests.get(url, headers=headers, timeout=timeout)
                
                # Handle rate limiting
                if response.status_code == 429:
                    OptimizedAPICall._rate_limiter.record_failure()
                    
                    if OptimizedAPICall._rate_limiter.should_retry() and retry_count < max_retries:
                        wait_time = OptimizedAPICall._rate_limiter.handle_rate_limit()
                        time.sleep(wait_time)
                        retry_count += 1
                        continue
                    else:
                        logger.error(f"Rate limit exceeded (max retries): {endpoint_name}")
                        return None
                
                # Check for other errors
                response.raise_for_status()
                
                data = response.json()
                
                # Reset rate limiter on success
                OptimizedAPICall._rate_limiter.reset()
                
                # Cache successful response
                if cache_key and data:
                    APICache.set(endpoint_name, cache_key, data)
                
                logger.info(f"API SUCCESS: {endpoint_name}")
                return data
                
            except requests.exceptions.Timeout:
                logger.error(f"Timeout: {endpoint_name}")
                retry_count += 1
                if retry_count <= max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff
            
            except requests.exceptions.ConnectionError:
                logger.error(f"Connection error: {endpoint_name}")
                retry_count += 1
                if retry_count <= max_retries:
                    time.sleep(2 ** retry_count)
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error ({endpoint_name}): {str(e)[:50]}")
                return None
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {endpoint_name}")
                return None
        
        logger.error(f"All retries exhausted: {endpoint_name}")
        return None
    
    @staticmethod
    def _throttle():
        """Enforce minimum delay between API requests."""
        elapsed = time.time() - OptimizedAPICall._last_request_time
        if elapsed < OptimizedAPICall._request_throttle_delay:
            time.sleep(OptimizedAPICall._request_throttle_delay - elapsed)
        
        OptimizedAPICall._last_request_time = time.time()


def get_cache_stats() -> Dict:
    """Get statistics about cache usage."""
    if not os.path.exists(CACHE_DIR):
        return {"cached_files": 0, "total_size_mb": 0}
    
    files = os.listdir(CACHE_DIR)
    total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files)
    
    return {
        "cached_files": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2)
    }
