"""
Integration tests for Firi order format.
Hits real Firi API (public depth endpoint) to verify order format matches.
Requires network access. Skips if Firi is unreachable.
"""
import os

import httpx
import pytest

from trader import round_price, round_quantity

# Firi public depth endpoint - no auth required
FIRI_DEPTH_URL = "https://api.firi.com/v2/markets/{market}/depth"
MARKET_FORMATS = ["BTCDKK", "BTCNOK", "btcdkk", "btc-dkk"]


def _fetch_firi_orderbook() -> tuple[dict | None, str | None]:
    """
    Fetch orderbook from Firi. Returns (data, error).
    Uses public endpoint - no auth needed.
    """
    for market in MARKET_FORMATS:
        try:
            url = FIRI_DEPTH_URL.format(market=market)
            response = httpx.get(url, params={"bids": 1, "asks": 1}, timeout=10.0)
            if response.status_code == 404:
                continue
            response.raise_for_status()
            return response.json(), None
        except Exception:
            continue
    return None, "Could not reach Firi depth API"


def _decimal_places(s: str) -> int:
    """Same logic as data_fetcher.get_order_format."""
    s = s.strip()
    if "." in s:
        return len(s.split(".")[-1].rstrip("0"))
    return 0


def _format_order_for_firi(price: float, amount: float, price_decimals: int, amount_decimals: int) -> tuple[str, str]:
    """Format price and amount as Firi expects (strings with correct decimals)."""
    p = round_price(price, price_decimals)
    q = round_quantity(amount, amount_decimals)
    return (str(p), str(q))


@pytest.mark.integration
def test_firi_orderbook_format_matches_order_spec():
    """
    GIVEN real Firi orderbook from depth API
    WHEN we parse format and format a sample order
    THEN the formatted strings match Firi's expected format (decimal places).
    """
    data, err = _fetch_firi_orderbook()
    if err:
        pytest.skip(f"Firi unreachable: {err}")

    bids = data.get("bids", [])
    if not bids:
        pytest.skip("Firi orderbook has no bids")

    first_bid = bids[0]
    if isinstance(first_bid, (list, tuple)) and len(first_bid) >= 2:
        price_str = str(first_bid[0])
        amount_str = str(first_bid[1])
    elif isinstance(first_bid, dict):
        price_str = str(first_bid.get("price", first_bid.get("0", "0")))
        amount_str = str(first_bid.get("amount", first_bid.get("1", "0")))
    else:
        pytest.skip(f"Unexpected bid format: {type(first_bid)}")

    price_decimals = _decimal_places(price_str)
    amount_decimals = _decimal_places(amount_str)

    # Format a sample order with our round_price/round_quantity
    sample_price = float(price_str)
    sample_amount = float(amount_str)
    formatted_price, formatted_amount = _format_order_for_firi(
        sample_price, sample_amount, price_decimals, amount_decimals
    )

    # Verify formatted strings have correct decimal places
    assert _decimal_places(formatted_price) == price_decimals, (
        f"Price format mismatch: got {formatted_price} ({_decimal_places(formatted_price)} decimals), "
        f"expected {price_decimals} from Firi sample {price_str}"
    )
    assert _decimal_places(formatted_amount) == amount_decimals, (
        f"Amount format mismatch: got {formatted_amount} ({_decimal_places(formatted_amount)} decimals), "
        f"expected {amount_decimals} from Firi sample {amount_str}"
    )


@pytest.mark.integration
def test_firi_get_order_format_matches_live_orderbook():
    """
    GIVEN FiriDataFetcher with env credentials
    WHEN get_order_format is called for BTC/DKK
    THEN returns format matching live Firi orderbook.
    """
    data, err = _fetch_firi_orderbook()
    if err:
        pytest.skip(f"Firi unreachable: {err}")

    bids = data.get("bids", [])
    if not bids:
        pytest.skip("Firi orderbook has no bids")

    first_bid = bids[0]
    if isinstance(first_bid, (list, tuple)) and len(first_bid) >= 2:
        expected_price_decimals = _decimal_places(str(first_bid[0]))
        expected_amount_decimals = _decimal_places(str(first_bid[1]))
    else:
        pytest.skip(f"Unexpected bid format: {type(first_bid)}")

    # Only run data_fetcher test if we have Firi credentials (for base_url)
    if not os.getenv("FIRI_API_KEY") or not os.getenv("FIRI_SECRET"):
        pytest.skip("FIRI_API_KEY/FIRI_SECRET not set - cannot init FiriDataFetcher")

    from data_fetcher import FiriDataFetcher

    fetcher = FiriDataFetcher()
    result = fetcher.get_order_format("BTC/DKK")

    assert result is not None, "get_order_format should return format when Firi is reachable"
    assert result[0] == expected_price_decimals, (
        f"Price decimals mismatch: get_order_format={result[0]}, "
        f"live orderbook={expected_price_decimals}"
    )
    assert result[1] == expected_amount_decimals, (
        f"Amount decimals mismatch: get_order_format={result[1]}, "
        f"live orderbook={expected_amount_decimals}"
    )
