"""
Unit tests verifying trading logic actually uses settings/trading_config.py.
Exercises run_iteration and asserts get_candles, strategy, etc. use trading_config values.
"""
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models import Candle
from settings.trading_config import (
    TRADING_PAIR,
    CANDLE_INTERVAL,
    LONG_EMA_PERIOD,
    MEDIUM_EMA_PERIOD,
    POLL_INTERVAL,
    SHORT_EMA_PERIOD,
)
from settings.config import CANDLE_LIMIT

# Formats supported by data_fetcher interval_map (must match data_fetcher.py)
VALID_CANDLE_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}


def test_candle_interval_has_acceptable_format():
    """
    GIVEN trading_config defines CANDLE_INTERVAL
    WHEN we validate it
    THEN it matches format used by data_fetcher (e.g. 1m, 5m, 15m, 30m, 1h, 4h, 1d).
    """
    assert CANDLE_INTERVAL in VALID_CANDLE_INTERVALS, (
        f"CANDLE_INTERVAL '{CANDLE_INTERVAL}' is not valid. "
        f"Must be one of: {sorted(VALID_CANDLE_INTERVALS)}"
    )


# POLL_INTERVAL: seconds between iterations. Min 1s, max 24h (avoids API hammering / runaway sleep)
POLL_INTERVAL_MIN = 1
POLL_INTERVAL_MAX = 86400


def test_ema_periods_are_integers():
    """
    GIVEN trading_config defines SHORT_EMA_PERIOD, MEDIUM_EMA_PERIOD, LONG_EMA_PERIOD
    WHEN we validate them
    THEN each is an integer.
    """
    for name, value in [
        ("SHORT_EMA_PERIOD", SHORT_EMA_PERIOD),
        ("MEDIUM_EMA_PERIOD", MEDIUM_EMA_PERIOD),
        ("LONG_EMA_PERIOD", LONG_EMA_PERIOD),
    ]:
        assert isinstance(value, int), (
            f"{name} must be an integer, got {type(value).__name__}"
        )


def test_poll_interval_has_acceptable_format():
    """
    GIVEN trading_config defines POLL_INTERVAL
    WHEN we validate it
    THEN it is an integer in seconds, between 1 and 86400 (1s to 24h).
    """
    assert isinstance(POLL_INTERVAL, int), (
        f"POLL_INTERVAL must be an integer, got {type(POLL_INTERVAL).__name__}"
    )
    assert POLL_INTERVAL_MIN <= POLL_INTERVAL <= POLL_INTERVAL_MAX, (
        f"POLL_INTERVAL {POLL_INTERVAL} is out of range. "
        f"Must be between {POLL_INTERVAL_MIN} and {POLL_INTERVAL_MAX} seconds."
    )


def _mock_firebase_handler():
    h = MagicMock()
    h.level = logging.WARNING
    return h


def _make_candles(count: int) -> list[Candle]:
    """Create enough candles for strategy (needs at least long_ema_period)."""
    base = datetime(2024, 1, 1, 0, 0, 0)
    prices = [100.0 + i for i in range(count)]
    return [
        Candle(timestamp=base + timedelta(hours=i), open=p, high=p, low=p, close=p, volume=100.0)
        for i, p in enumerate(prices)
    ]


def test_run_iteration_get_candles_uses_trading_config():
    """
    GIVEN trading_config defines TRADING_PAIR, CANDLE_INTERVAL
    WHEN run_iteration executes
    THEN get_candles is called with pair and interval from trading_config.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_candles.return_value = _make_candles(LONG_EMA_PERIOD + 10)
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    mock_firebase = MagicMock()
    mock_firebase.get_open_trades.return_value = []
    mock_firebase.get_recent_trades.return_value = []
    mock_firebase.get_price_snapshots.return_value = []

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    bot.run_iteration()

                    mock_data_fetcher.get_candles.assert_called()
                    call_kwargs = mock_data_fetcher.get_candles.call_args[1]
                    assert call_kwargs["pair"] == TRADING_PAIR
                    assert call_kwargs["interval"] == CANDLE_INTERVAL
                    assert call_kwargs["limit"] == CANDLE_LIMIT


def test_run_iteration_strategy_uses_ema_periods_from_trading_config():
    """
    GIVEN trading_config defines SHORT/MEDIUM/LONG_EMA_PERIOD
    WHEN run_iteration generates a signal
    THEN strategy uses those EMA periods (signal reflects correct EMA calc).
    """
    mock_data_fetcher = MagicMock()
    # Rising prices -> BUY signal
    candles = _make_candles(LONG_EMA_PERIOD + 10)
    mock_data_fetcher.get_candles.return_value = candles
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    mock_firebase = MagicMock()
    mock_firebase.get_open_trades.return_value = []
    mock_firebase.get_recent_trades.return_value = []

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    assert bot.strategy.short_ema_period == SHORT_EMA_PERIOD
                    assert bot.strategy.medium_ema_period == MEDIUM_EMA_PERIOD
                    assert bot.strategy.long_ema_period == LONG_EMA_PERIOD

                    bot.run_iteration()

                    # Strategy was used with correct period - signal has EMA values
                    mock_firebase.save_signal.assert_called_once()
                    saved_signal = mock_firebase.save_signal.call_args[0][0]
                    assert saved_signal.short_ema is not None
                    assert saved_signal.medium_ema is not None
                    assert saved_signal.long_ema is not None


def test_firebase_calls_use_pair_from_trading_config():
    """
    GIVEN trading_config defines TRADING_PAIR
    WHEN run_iteration runs
    THEN Firebase methods (get_open_trades, save_signal, etc.) receive pair from bot.pair.
    """
    mock_data_fetcher = MagicMock()
    mock_data_fetcher.get_candles.return_value = _make_candles(LONG_EMA_PERIOD + 10)
    mock_data_fetcher.get_order_format.return_value = (2, 8)

    mock_firebase = MagicMock()
    mock_firebase.get_open_trades.return_value = []
    mock_firebase.get_recent_trades.return_value = []

    with patch("main.FiriDataFetcher", return_value=mock_data_fetcher):
        with patch("main.FiriTrader", MagicMock()):
            with patch("main.FirebaseStore", return_value=mock_firebase):
                with patch("main.FirebaseLoggingHandler", return_value=_mock_firebase_handler()):
                    from main import TradingBot

                    bot = TradingBot()
                    assert bot.pair == TRADING_PAIR

                    bot.run_iteration()

                    mock_firebase.get_open_trades.assert_called_with(pair=TRADING_PAIR)
