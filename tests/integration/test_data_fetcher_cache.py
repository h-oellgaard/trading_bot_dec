"""
Integration test for caching logic against the live Firi API.
"""
import os
import pytest
from data_fetcher import FiriDataFetcher

@pytest.mark.skipif("FIRI_API_KEY" not in os.environ, reason="Requires Firi API credentials")
def test_live_data_fetcher_caching_and_limits():
    """
    Test live FiriDataFetcher to ensure limits and caching logic works.
    This will make actual HTTP requests.
    """
    fetcher = FiriDataFetcher()
    
    # 1. First run, cold start
    limit = 50
    candles_first = fetcher.get_candles("ETH/DKK", interval="1h", limit=limit)
    
    assert len(candles_first) > 0
    assert len(candles_first) <= len(fetcher._cached_candles)
    
    first_cache_len = len(fetcher._cached_candles)
    
    # 2. Second run, light fetch
    candles_second = fetcher.get_candles("ETH/DKK", interval="1h", limit=limit)
    
    # Cache length should be at least same, max length is 1000
    assert len(fetcher._cached_candles) >= first_cache_len
    assert len(fetcher._cached_candles) <= 1000
    
    # Check no duplicate timestamps in cache
    cache_timestamps = [c.timestamp for c in fetcher._cached_candles]
    assert len(cache_timestamps) == len(set(cache_timestamps))
    
    # Returned candles should still respect limit
    assert len(candles_second) <= limit
