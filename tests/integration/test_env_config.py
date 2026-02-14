"""
Integration tests using actual .env file.
Verifies TradingBot uses config from trading_config.py (EMA periods, pair, poll interval).
Sensitive vars (credentials) still come from .env. Skips if .env does not exist (e.g. in CI).
"""
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv

from settings.trading_config import (
    TRADING_PAIR,
    SHORT_EMA_PERIOD,
    MEDIUM_EMA_PERIOD,
    LONG_EMA_PERIOD,
    POLL_INTERVAL,
)

# Project root (tests/integration/ -> tests/ -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def _load_env():
    """Load .env from project root. Returns True if loaded, False if file missing."""
    if not ENV_PATH.exists():
        return False
    load_dotenv(ENV_PATH)
    return True


def _mock_firebase_handler():
    """Return a mock Firebase handler that won't break logging."""
    h = MagicMock()
    h.level = logging.WARNING
    return h


@pytest.fixture
def env_loaded():
    """Load .env and skip if not found."""
    if not _load_env():
        pytest.skip(".env file not found - run locally with .env present")
    yield


@pytest.mark.integration
def test_bot_uses_ema_periods_from_trading_config(env_loaded):
    """
    GIVEN trading_config.py defines SHORT/MEDIUM/LONG_EMA_PERIOD
    WHEN TradingBot is initialized
    THEN strategy uses those values.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", MagicMock()):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()

                    assert bot.strategy.short_ema_period == SHORT_EMA_PERIOD
                    assert bot.strategy.medium_ema_period == MEDIUM_EMA_PERIOD
                    assert bot.strategy.long_ema_period == LONG_EMA_PERIOD


@pytest.mark.integration
def test_bot_uses_trading_pair_from_trading_config(env_loaded):
    """
    GIVEN trading_config.py defines TRADING_PAIR
    WHEN TradingBot is initialized
    THEN bot.pair matches.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", MagicMock()):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    assert bot.pair == TRADING_PAIR


@pytest.mark.integration
def test_bot_uses_poll_interval_from_trading_config(env_loaded):
    """
    GIVEN trading_config.py defines POLL_INTERVAL
    WHEN TradingBot is initialized
    THEN bot.poll_interval matches.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", MagicMock()):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    assert bot.poll_interval == POLL_INTERVAL


@pytest.mark.integration
def test_bot_uses_trailing_stop_and_cooldown_from_env(env_loaded):
    """
    GIVEN .env exists with TRAILING_STOP_LOSS_PERCENT, COOLDOWN_CANDLES
    WHEN TradingBot is initialized
    THEN bot uses those values.
    """
    import os

    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", MagicMock()):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    expected_stop = float(os.getenv("TRAILING_STOP_LOSS_PERCENT", "7.0"))
                    expected_cooldown = int(os.getenv("COOLDOWN_CANDLES", "25"))
                    assert bot.trailing_stop_loss_percent == expected_stop
                    assert bot.cooldown_candles == expected_cooldown
