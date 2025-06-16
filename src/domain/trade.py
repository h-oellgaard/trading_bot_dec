from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .coin import Coin

TradeAction = Literal["BUY", "SELL"]

@dataclass
class Trade:
    """Represents a trading transaction."""
    coin: Coin
    action: TradeAction
    amount: float
    price: float
    timestamp: datetime

    def __post_init__(self):
        """Validate the trade data after initialization."""
        if not isinstance(self.coin, Coin):
            raise ValueError("Coin must be a valid Coin instance")
        if self.action not in ["BUY", "SELL"]:
            raise ValueError("Action must be either 'BUY' or 'SELL'")
        if not isinstance(self.amount, (int, float)) or self.amount <= 0:
            raise ValueError("Amount must be a positive number")
        if not isinstance(self.price, (int, float)) or self.price <= 0:
            raise ValueError("Price must be a positive number")
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object") 