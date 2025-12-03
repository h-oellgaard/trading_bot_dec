"""
Data models for the trading bot.
Pure data classes with no business logic.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TradeStatus(Enum):
    """Trade status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class SignalType(Enum):
    """Signal type enumeration."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Candle:
    """OHLC candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Firebase storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Candle":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            open=float(data["open"]),
            high=float(data["high"]),
            low=float(data["low"]),
            close=float(data["close"]),
            volume=float(data.get("volume", 0.0))
        )


@dataclass
class Trade:
    """Trade data model."""
    trade_id: str
    pair: str
    side: str  # "buy" or "sell"
    price: float
    quantity: float
    status: TradeStatus
    timestamp: datetime
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    close_price: Optional[float] = None
    close_timestamp: Optional[datetime] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Firebase storage."""
        return {
            "trade_id": self.trade_id,
            "pair": self.pair,
            "side": self.side,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "close_price": self.close_price,
            "close_timestamp": self.close_timestamp.isoformat() if self.close_timestamp else None,
            "profit_loss": self.profit_loss,
            "profit_loss_percent": self.profit_loss_percent
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Trade":
        """Create from dictionary."""
        return cls(
            trade_id=data["trade_id"],
            pair=data["pair"],
            side=data["side"],
            price=float(data["price"]),
            quantity=float(data["quantity"]),
            status=TradeStatus(data["status"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            take_profit=float(data["take_profit"]) if data.get("take_profit") else None,
            stop_loss=float(data["stop_loss"]) if data.get("stop_loss") else None,
            close_price=float(data["close_price"]) if data.get("close_price") else None,
            close_timestamp=datetime.fromisoformat(data["close_timestamp"]) if data.get("close_timestamp") else None,
            profit_loss=float(data["profit_loss"]) if data.get("profit_loss") else None,
            profit_loss_percent=float(data["profit_loss_percent"]) if data.get("profit_loss_percent") else None
        )


@dataclass
class Signal:
    """Trading signal data model."""
    signal_id: str
    signal_type: SignalType
    timestamp: datetime
    price: float
    short_sma: Optional[float] = None
    long_sma: Optional[float] = None
    short_ema: Optional[float] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Firebase storage."""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "short_sma": self.short_sma,
            "long_sma": self.long_sma,
            "short_ema": self.short_ema,
            "reason": self.reason
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Signal":
        """Create from dictionary."""
        return cls(
            signal_id=data["signal_id"],
            signal_type=SignalType(data["signal_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            price=float(data["price"]),
            short_sma=float(data["short_sma"]) if data.get("short_sma") else None,
            long_sma=float(data["long_sma"]) if data.get("long_sma") else None,
            short_ema=float(data["short_ema"]) if data.get("short_ema") else None,
            reason=data.get("reason")
        )


@dataclass
class PortfolioState:
    """Portfolio state data model."""
    timestamp: datetime
    balance_nok: float
    balance_btc: float
    total_value_nok: float
    open_trades_count: int
    closed_trades_count: int
    total_profit_loss: float
    total_profit_loss_percent: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Firebase storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "balance_nok": self.balance_nok,
            "balance_btc": self.balance_btc,
            "total_value_nok": self.total_value_nok,
            "open_trades_count": self.open_trades_count,
            "closed_trades_count": self.closed_trades_count,
            "total_profit_loss": self.total_profit_loss,
            "total_profit_loss_percent": self.total_profit_loss_percent
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PortfolioState":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            balance_nok=float(data["balance_nok"]),
            balance_btc=float(data["balance_btc"]),
            total_value_nok=float(data["total_value_nok"]),
            open_trades_count=int(data["open_trades_count"]),
            closed_trades_count=int(data["closed_trades_count"]),
            total_profit_loss=float(data["total_profit_loss"]),
            total_profit_loss_percent=float(data["total_profit_loss_percent"])
        )

