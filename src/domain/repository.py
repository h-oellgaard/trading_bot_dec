from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from .coin import Coin
from .trade import Trade


class PriceData:
    """Domain model for price data"""
    
    def __init__(self, symbol: str, price: float, volume: float, 
                 timestamp: datetime, source: str = "coingecko"):
        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.timestamp = timestamp
        self.source = source
    
    def __repr__(self):
        return f"PriceData(symbol='{self.symbol}', price={self.price}, volume={self.volume}, timestamp={self.timestamp})"


class MarketData:
    """Domain model for aggregated market data"""
    
    def __init__(self, symbol: str, prices: List[float], volumes: List[float], 
                 timestamps: List[datetime], source: str = "coingecko"):
        self.symbol = symbol
        self.prices = prices
        self.volumes = volumes
        self.timestamps = timestamps
        self.source = source
    
    def __len__(self):
        return len(self.prices)
    
    def get_latest_price(self) -> Optional[float]:
        return self.prices[-1] if self.prices else None
    
    def get_latest_volume(self) -> Optional[float]:
        return self.volumes[-1] if self.volumes else None
    
    def get_latest_timestamp(self) -> Optional[datetime]:
        return self.timestamps[-1] if self.timestamps else None


class PriceDataRepository(ABC):
    """Abstract repository for price data persistence"""
    
    @abstractmethod
    def save_price_data(self, price_data: PriceData) -> bool:
        """Save a single price data point"""
        pass
    
    @abstractmethod
    def save_batch_price_data(self, price_data_list: List[PriceData]) -> bool:
        """Save multiple price data points in batch"""
        pass
    
    @abstractmethod
    def get_price_data(self, symbol: str, start_time: Optional[datetime] = None, 
                      end_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[PriceData]:
        """Retrieve price data for a symbol within a time range"""
        pass
    
    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[PriceData]:
        """Get the most recent price data for a symbol"""
        pass
    
    @abstractmethod
    def get_market_data(self, symbol: str, periods: int) -> Optional[MarketData]:
        """Get market data for a symbol with specified number of periods"""
        pass
    
    @abstractmethod
    def delete_old_data(self, before_date: datetime) -> int:
        """Delete price data older than specified date, returns number of deleted records"""
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[str]:
        """Get list of all symbols in the repository"""
        pass
    
    @abstractmethod
    def get_data_statistics(self, symbol: str) -> Dict[str, Any]:
        """Get statistics about stored data for a symbol"""
        pass


class TradeRepository(ABC):
    """Abstract repository for trade data persistence"""
    
    @abstractmethod
    def save_trade(self, trade: Trade) -> bool:
        """Save a trade"""
        pass
    
    @abstractmethod
    def get_trades(self, symbol: Optional[str] = None, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, limit: Optional[int] = None) -> List[Trade]:
        """Retrieve trades with optional filters"""
        pass
    
    @abstractmethod
    def get_trade_by_id(self, trade_id: str) -> Optional[Trade]:
        """Get a specific trade by ID"""
        pass
    
    @abstractmethod
    def update_trade_status(self, trade_id: str, status: str) -> bool:
        """Update trade status"""
        pass
    
    @abstractmethod
    def get_trading_statistics(self, symbol: Optional[str] = None, 
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get trading statistics"""
        pass 