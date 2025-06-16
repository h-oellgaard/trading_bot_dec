from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class MarketData:
    """Represents market data for analysis."""
    def __init__(self, prices: List[float], volume: List[float], timestamp: List[float]):
        self.prices = prices
        self.volume = volume
        self.timestamp = timestamp

class TradingStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    @abstractmethod
    def generate_signal(self, market_data: MarketData) -> Optional[str]:
        """
        Generate a trading signal based on market data.
        
        Args:
            market_data: Market data for analysis
            
        Returns:
            Optional[str]: "BUY", "SELL", or None if no signal
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get the current parameters of the strategy.
        
        Returns:
            Dict[str, Any]: Strategy parameters
        """
        pass 