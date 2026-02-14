"""
Unit tests for main.py TradingBot.
Uses mocks to avoid Firebase/Firi API dependencies.
"""
import logging
import os
from unittest.mock import MagicMock, patch

import pytest


def _mock_firebase_handler():
    """Return a mock Firebase handler that won't break logging."""
    h = MagicMock()
    h.level = logging.WARNING
    return h


def test_poll_interval_from_env():
    """
    GIVEN POLL_INTERVAL=30 in environment
    WHEN TradingBot is initialized
    THEN bot.poll_interval is 30 seconds.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = None  # Use env defaults
    with patch.dict(os.environ, {"POLL_INTERVAL": "30"}, clear=False):
        with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
            with patch("main.FiriTrader", MagicMock()):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                        from main import TradingBot

                        bot = TradingBot()
                        assert bot.poll_interval == 30


def test_poll_interval_custom_value():
    """
    GIVEN POLL_INTERVAL=60 in environment
    WHEN TradingBot is initialized
    THEN bot.poll_interval is 60 seconds.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = None  # Use env defaults
    with patch.dict(os.environ, {"POLL_INTERVAL": "60"}, clear=False):
        with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
            with patch("main.FiriTrader", MagicMock()):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                        from main import TradingBot

                        bot = TradingBot()
                        assert bot.poll_interval == 60


def test_firi_format_applied_at_startup():
    """
    GIVEN Firi orderbook returns price/amount format
    WHEN TradingBot is initialized
    THEN trader uses Firi's price_decimals and quantity_decimals.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_trader = MagicMock()

    with patch.dict(os.environ, {"POLL_INTERVAL": "30"}, clear=False):
        with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
            with patch("main.FiriTrader", return_value=mock_trader):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                        from main import TradingBot

                        bot = TradingBot()
                        mock_data_fetcher.get_order_format.assert_called_once_with("BTC/DKK")
                        assert mock_trader.price_decimals == 2
                        assert mock_trader.quantity_decimals == 8


def test_firi_format_none_keeps_trader_defaults():
    """
    GIVEN get_order_format returns None (Firi unavailable)
    WHEN TradingBot is initialized
    THEN trader keeps its default price_decimals and quantity_decimals.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = None
    mock_trader = MagicMock()
    mock_trader.price_decimals = 2
    mock_trader.quantity_decimals = 8

    with patch.dict(os.environ, {"POLL_INTERVAL": "30"}, clear=False):
        with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
            with patch("main.FiriTrader", return_value=mock_trader):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                        from main import TradingBot

                        bot = TradingBot()
                        # Trader was never reassigned - still has original values
                        assert mock_trader.price_decimals == 2
                        assert mock_trader.quantity_decimals == 8


def test_firi_format_uses_trading_pair_from_env():
    """
    GIVEN TRADING_PAIR=ETH/NOK in environment
    WHEN TradingBot is initialized
    THEN get_order_format is called with ETH/NOK.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)
    mock_trader = MagicMock()

    with patch.dict(os.environ, {"POLL_INTERVAL": "30", "TRADING_PAIR": "ETH/NOK"}, clear=False):
        with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
            with patch("main.FiriTrader", return_value=mock_trader):
                with patch("main.FirebaseStore", MagicMock()):
                    with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                        from main import TradingBot

                        bot = TradingBot()
                        mock_data_fetcher.get_order_format.assert_called_once_with("ETH/NOK")
