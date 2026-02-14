"""
Unit tests for trader module.
Tests rounding of price and quantity for trade execution.
"""
import pytest

from trader import round_price, round_quantity


def test_round_price_two_decimals():
    """Price rounds to 2 decimals (DKK)."""
    assert round_price(450123.456789) == 450123.46
    assert round_price(100.1) == 100.1
    assert round_price(99.999) == 100.0


def test_round_price_custom_decimals():
    """Price can use custom decimal places."""
    assert round_price(450123.456789, decimals=0) == 450123.0
    assert round_price(450123.456789, decimals=4) == 450123.4568


def test_round_quantity_eight_decimals():
    """Quantity rounds to 8 decimals (BTC satoshi precision)."""
    assert round_quantity(0.002345678901234567) == 0.00234568
    assert round_quantity(0.1) == 0.1
    assert round_quantity(1.123456789) == 1.12345679


def test_round_quantity_custom_decimals():
    """Quantity can use custom decimal places."""
    assert round_quantity(0.123456789, decimals=2) == 0.12
    assert round_quantity(0.123456789, decimals=4) == 0.1235


def test_round_quantity_no_excessive_decimals():
    """Quantity has no more than 8 decimals by default."""
    q = round_quantity(0.00234567890123456789)
    # Check string representation has at most 8 decimal places
    q_str = f"{q:.10f}".rstrip("0").rstrip(".")
    decimal_places = len(q_str.split(".")[-1]) if "." in q_str else 0
    assert decimal_places <= 8


def test_round_price_no_excessive_decimals():
    """Price has no more than 2 decimals by default."""
    p = round_price(450123.4567890123)
    p_str = f"{p:.10f}".rstrip("0").rstrip(".")
    decimal_places = len(p_str.split(".")[-1]) if "." in p_str else 0
    assert decimal_places <= 2
