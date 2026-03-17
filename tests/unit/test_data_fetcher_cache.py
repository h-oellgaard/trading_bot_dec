"""
Unit tests for data_fetcher caching functionality.
"""
import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from data_fetcher import FiriDataFetcher
from models import Candle

@pytest.fixture(autouse=True)
def firi_env():
    """Ensure Firi env vars are set for data fetcher init."""
    with patch.dict(os.environ, {"FIRI_API_KEY": "test", "FIRI_SECRET": "test"}, clear=False):
        yield

def test_data_fetcher_cold_start_caching():
    """
    Test that the first call to get_candles requests a large limit and populates cache.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"timestamp": 1670000000, "price": "100", "amount": "1"},
        {"timestamp": 1670004000, "price": "110", "amount": "1"},
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("data_fetcher.httpx.get", return_value=mock_response) as mock_get:
        fetcher = FiriDataFetcher()
        assert len(fetcher._cached_candles) == 0
        
        limit = 10
        fetcher.get_candles("BTC/DKK", interval="1h", limit=limit)
        
        # Cold start should ask for max trades
        called_url = mock_get.call_args[0][0]
        called_params = mock_get.call_args[1]["params"]
        
        assert "history" in called_url
        assert called_params["count"] >= limit * 10
        assert len(fetcher._cached_candles) > 0

def test_data_fetcher_light_fetch_caching():
    """
    Test that subsequent calls leverage cache and use a light fetch.
    """
    mock_response_1 = MagicMock()
    mock_response_1.status_code = 200
    mock_response_1.json.return_value = [
        {"timestamp": 1670000000, "price": "100", "amount": "1"},
        {"timestamp": 1670004000, "price": "110", "amount": "1"},
        {"timestamp": 1670008000, "price": "120", "amount": "1"},
    ]
    
    # 2nd response has recent trades
    mock_response_2 = MagicMock()
    mock_response_2.status_code = 200
    mock_response_2.json.return_value = [
        {"timestamp": 1670008000, "price": "125", "amount": "2"},
        {"timestamp": 1670012000, "price": "130", "amount": "1"},
    ]

    with patch("data_fetcher.httpx.get", side_effect=[mock_response_1, mock_response_2]) as mock_get:
        fetcher = FiriDataFetcher()
        limit = 2
        
        # Call 1
        res1 = fetcher.get_candles("BTC/DKK", interval="1h", limit=limit)
        assert mock_get.call_args_list[0][1]["params"]["count"] >= limit * 10
        
        # Call 2
        res2 = fetcher.get_candles("BTC/DKK", interval="1h", limit=limit)
        assert mock_get.call_args_list[1][1]["params"]["count"] == 200
        
        # Verify merge logic works (timestamp 1670008000 is merged correctly, updated close price to 125, volume 3)
        cache_timestamps = [c.timestamp.timestamp() for c in fetcher._cached_candles]
        assert len(set(cache_timestamps)) == len(cache_timestamps), "Should not have duplicate timestamps"
        assert len(fetcher._cached_candles) == 4
        
        # Check volume accumulation and price update
        updated_candle = next(c for c in fetcher._cached_candles if c.timestamp.timestamp() == 1670007600.0) # 1670008000 resolves to 1670007600.0 boundary
        assert updated_candle.close == 125.0
        assert updated_candle.volume == 2.0 # The new candle overwrote the old candle completely
