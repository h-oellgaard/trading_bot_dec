"""
Unit tests for data_fetcher module.
Tests get_order_format parsing from Firi orderbook.
"""
import os
from unittest.mock import patch, MagicMock

import pytest

from data_fetcher import FiriDataFetcher


@pytest.fixture(autouse=True)
def firi_env():
    """Ensure Firi env vars are set for data fetcher init."""
    with patch.dict(os.environ, {"FIRI_API_KEY": "test", "FIRI_SECRET": "test"}, clear=False):
        yield


def test_get_order_format_parses_orderbook():
    """
    GIVEN Firi depth API returns bids with price and amount strings
    WHEN get_order_format is called
    THEN returns (price_decimals, amount_decimals) inferred from format.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "bids": [["437255.22", "0.00227098"]],
        "asks": [["437260.50", "0.00100000"]],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("data_fetcher.httpx.get", return_value=mock_response):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/DKK")

    assert result == (2, 8)


def test_get_order_format_handles_different_precision():
    """
    GIVEN orderbook has 4 decimal price and 6 decimal amount
    WHEN get_order_format is called
    THEN returns correct decimals.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "bids": [["1234.5678", "0.123456"]],
        "asks": [],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("data_fetcher.httpx.get", return_value=mock_response):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/NOK")

    assert result == (4, 6)


def test_get_order_format_returns_none_on_404():
    """
    GIVEN depth API returns 404 for all market formats
    WHEN get_order_format is called
    THEN returns None.
    """
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("data_fetcher.httpx.get", return_value=mock_response):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/DKK")

    assert result is None


def test_get_order_format_empty_bids_returns_none():
    """
    GIVEN depth API returns empty bids
    WHEN get_order_format is called
    THEN returns None.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"bids": [], "asks": []}
    mock_response.raise_for_status = MagicMock()

    with patch("data_fetcher.httpx.get", return_value=mock_response):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/DKK")

    assert result is None


def test_get_order_format_handles_dict_bid_format():
    """
    GIVEN orderbook returns bid as dict with price/amount keys
    WHEN get_order_format is called
    THEN parses and returns correct decimals.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "bids": [{"price": "450000.22", "amount": "0.00123456"}],
        "asks": [],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("data_fetcher.httpx.get", return_value=mock_response):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/DKK")

    assert result == (2, 8)


def test_get_order_format_integer_price():
    """
    GIVEN orderbook has integer price (no decimals) and amount with trailing zeros
    WHEN get_order_format is called
    THEN returns 0 for price_decimals, strips trailing zeros from amount.
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "bids": [["500000", "0.00100000"]],
        "asks": [],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("data_fetcher.httpx.get", return_value=mock_response):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/DKK")

    # "500000" has 0 decimals; "0.00100000" -> "001" after rstrip = 3 decimals
    assert result == (0, 3)


def test_get_order_format_retries_on_404_then_succeeds():
    """
    GIVEN first market format returns 404, second succeeds
    WHEN get_order_format is called
    THEN returns format from successful response.
    """
    mock_404 = MagicMock()
    mock_404.status_code = 404

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {
        "bids": [["437255.22", "0.00227098"]],
        "asks": [],
    }
    mock_200.raise_for_status = MagicMock()

    with patch("data_fetcher.httpx.get", side_effect=[mock_404, mock_200]):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/DKK")

    assert result == (2, 8)


def test_get_order_format_handles_http_error():
    """
    GIVEN depth API raises HTTPError for all formats
    WHEN get_order_format is called
    THEN returns None.
    """
    import httpx

    with patch("data_fetcher.httpx.get", side_effect=httpx.HTTPError("Connection error")):
        fetcher = FiriDataFetcher()
        result = fetcher.get_order_format("BTC/DKK")

    assert result is None
