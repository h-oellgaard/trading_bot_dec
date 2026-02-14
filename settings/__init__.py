"""Settings module - config values with env fallbacks."""

from settings.config import (
    CANDLE_INTERVAL,
    CANDLE_LIMIT,
    MIN_FIREBASE_CANDLES,
    BUY_BALANCE_FRACTION,
    SECONDS_PER_CANDLE,
)
from settings.trading_config import (
    TRADING_PAIR,
    SHORT_EMA_PERIOD,
    MEDIUM_EMA_PERIOD,
    LONG_EMA_PERIOD,
    POLL_INTERVAL,
)

__all__ = [
    "CANDLE_INTERVAL",
    "CANDLE_LIMIT",
    "MIN_FIREBASE_CANDLES",
    "BUY_BALANCE_FRACTION",
    "SECONDS_PER_CANDLE",
    "TRADING_PAIR",
    "SHORT_EMA_PERIOD",
    "MEDIUM_EMA_PERIOD",
    "LONG_EMA_PERIOD",
    "POLL_INTERVAL",
]
