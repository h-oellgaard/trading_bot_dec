"""Settings module - config values with env fallbacks."""

from settings.config import (
    CANDLE_INTERVAL,
    CANDLE_LIMIT,
    STARTUP_CANDLE_LIMIT,
    MIN_FIREBASE_CANDLES,
    BUY_QUOTE_AMOUNT,
    FIRI_FEE_PERCENT,
    SECONDS_PER_CANDLE,
    TRADING_ENABLED,
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
    "STARTUP_CANDLE_LIMIT",
    "MIN_FIREBASE_CANDLES",
    "BUY_QUOTE_AMOUNT",
    "FIRI_FEE_PERCENT",
    "SECONDS_PER_CANDLE",
    "TRADING_ENABLED",
    "TRADING_PAIR",
    "SHORT_EMA_PERIOD",
    "MEDIUM_EMA_PERIOD",
    "LONG_EMA_PERIOD",
    "POLL_INTERVAL",
]
