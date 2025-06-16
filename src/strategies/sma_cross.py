from typing import Optional, Dict, Any
import numpy as np

from ..domain.strategy import TradingStrategy, MarketData

class SmaCrossStrategy(TradingStrategy):
    """Simple Moving Average Cross strategy."""
    
    def __init__(self, short_window: int = 3, long_window: int = 5):
        """
        Initialize the SMA Cross strategy.
        
        Args:
            short_window: Short-term SMA window size
            long_window: Long-term SMA window size
        """
        if short_window >= long_window:
            raise ValueError("Short window must be smaller than long window")
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, market_data: MarketData) -> Optional[str]:
        """
        Generate trading signals based on SMA crossovers.
        
        Args:
            market_data: Market data containing price information
            
        Returns:
            Optional[str]: "BUY" on bullish crossover, "SELL" on bearish crossover, None otherwise
        """
        if len(market_data.prices) < self.long_window:
            return None

        # Calculate SMAs
        short_sma = np.mean(market_data.prices[-self.short_window:])
        long_sma = np.mean(market_data.prices[-self.long_window:])
        
        # Previous values
        prev_short_sma = np.mean(market_data.prices[-self.short_window-1:-1])
        prev_long_sma = np.mean(market_data.prices[-self.long_window-1:-1])
        
        # Check for crossovers
        if prev_short_sma <= prev_long_sma and short_sma > long_sma:
            return "BUY"
        elif prev_short_sma >= prev_long_sma and short_sma < long_sma:
            return "SELL"
        
        return None

    def get_parameters(self) -> Dict[str, Any]:
        """Get the current strategy parameters."""
        return {
            "short_window": self.short_window,
            "long_window": self.long_window
        } 