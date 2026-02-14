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

# Firebase
MIN_FIREBASE_CANDLES = int(os.getenv("MIN_FIREBASE_CANDLES", "50"))

# Buy order
BUY_BALANCE_FRACTION = float(os.getenv("BUY_BALANCE_FRACTION", "0.95"))

# Cooldown (1 candle = N seconds for cooldown calculation)
SECONDS_PER_CANDLE = int(os.getenv("SECONDS_PER_CANDLE", "3600"))
