"""
Trading bot configuration.
Values loaded from env with fallbacks. Add to .env to override.
Trading params (pair, EMA, poll) come from trading_config.py.
"""
import os

from dotenv import load_dotenv

from settings.trading_config import CANDLE_INTERVAL

load_dotenv()
CANDLE_LIMIT = int(os.getenv("CANDLE_LIMIT", "100"))
STARTUP_CANDLE_LIMIT = int(os.getenv("STARTUP_CANDLE_LIMIT", "200"))

# Firebase
MIN_FIREBASE_CANDLES = int(os.getenv("MIN_FIREBASE_CANDLES", "50"))

# Trading: when False, only fetch prices and log signals (no orders, no balance checks)
TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() in ("true", "1", "yes")

# Buy order: fixed spend in quote currency per buy (e.g. 200 DKK for ETH/DKK), including fee in the sense
# that quantity is sized so total quote outlay matches scripts/test_trade.py (fee reduces notional before price).
BUY_QUOTE_AMOUNT = float(os.getenv("BUY_QUOTE_AMOUNT", "200"))
FIRI_FEE_PERCENT = float(os.getenv("FIRI_FEE_PERCENT", "0.7"))

# Cooldown (1 candle = N seconds). Derived from CANDLE_INTERVAL unless overridden.
_INTERVAL_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}
_SECONDS_DEFAULT = _INTERVAL_SECONDS.get(CANDLE_INTERVAL, 3600)
SECONDS_PER_CANDLE = int(os.getenv("SECONDS_PER_CANDLE", str(_SECONDS_DEFAULT)))
