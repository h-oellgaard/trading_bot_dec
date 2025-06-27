from typing import Optional, Dict, Any
import numpy as np
from datetime import datetime, timedelta

from ..domain.strategy import TradingStrategy, MarketData

class SmaCrossStrategy(TradingStrategy):
    """Simple Moving Average Cross strategy with improved robustness."""
    
    def __init__(self, short_window: int = 7, long_window: int = 21, 
                 cooldown_period: int = 60, min_data_points: int = 50):
        """
        Initialize the SMA Cross strategy with improved defaults.
        
        Args:
            short_window: Short-term SMA window size (default: 7)
            long_window: Long-term SMA window size (default: 21)
            cooldown_period: Minimum seconds between signals (default: 60)
            min_data_points: Minimum data points required (default: 50)
        """
        if short_window >= long_window:
            raise ValueError("Short window must be smaller than long window")
        
        # Warn about potential overfitting with very small windows
        if short_window < 5 or long_window < 10:
            print("⚠️  WARNING: Small window sizes may lead to overfitting and excessive noise.")
            print("   Consider using larger windows (short >= 7, long >= 21) for more reliable signals.")
        
        if short_window < 3 or long_window < 5:
            print("🚨 CRITICAL: Very small window sizes detected!")
            print("   This will likely result in excessive false signals and poor performance.")
            print("   Recommended minimum: short_window=7, long_window=21")
        
        self.short_window = short_window
        self.long_window = long_window
        self.cooldown_period = cooldown_period
        self.min_data_points = min_data_points
        
        # Signal tracking for debouncing
        self.last_signal = None
        self.last_signal_time = None
        
        print(f"📊 SMA Cross Strategy initialized:")
        print(f"   Short window: {short_window} periods")
        print(f"   Long window: {long_window} periods")
        print(f"   Cooldown period: {cooldown_period} seconds")
        print(f"   Minimum data points: {min_data_points}")

    def generate_signal(self, market_data: MarketData) -> Optional[str]:
        """
        Generate trading signals based on SMA crossovers with debouncing.
        
        Args:
            market_data: Market data containing price information
            
        Returns:
            Optional[str]: "BUY" on bullish crossover, "SELL" on bearish crossover, None otherwise
        """
        # Check if we have enough data
        if len(market_data.prices) < self.long_window + 1:
            print(f"⚠️  Insufficient data: {len(market_data.prices)} < {self.long_window + 1}")
            return None
        
        if len(market_data.prices) < self.min_data_points:
            print(f"⚠️  Data below minimum threshold: {len(market_data.prices)} < {self.min_data_points}")
            return None

        # Check cooldown period
        current_time = datetime.now()
        if (self.last_signal_time and 
            (current_time - self.last_signal_time).total_seconds() < self.cooldown_period):
            print(f"⏰ Cooldown active: {self.cooldown_period - (current_time - self.last_signal_time).total_seconds():.1f}s remaining")
            return None

        # Calculate current SMAs
        short_sma = np.mean(market_data.prices[-self.short_window:])
        long_sma = np.mean(market_data.prices[-self.long_window:])
        
        # Calculate previous SMAs (one period back)
        prev_short_sma = np.mean(market_data.prices[-self.short_window-1:-1])
        prev_long_sma = np.mean(market_data.prices[-self.long_window-1:-1])

        # Debug information (only in verbose mode)
        debug_mode = False  # Set to True for detailed logging
        if debug_mode:
            print(f"📈 Current SMAs: Short={short_sma:.2f}, Long={long_sma:.2f}")
            print(f"📉 Previous SMAs: Short={prev_short_sma:.2f}, Long={prev_long_sma:.2f}")

        # Check for crossovers
        signal = None
        if prev_short_sma <= prev_long_sma and short_sma > long_sma:
            signal = "BUY"
        elif prev_short_sma >= prev_long_sma and short_sma < long_sma:
            signal = "SELL"
        
        # Suppress repeated identical signals
        if signal == self.last_signal:
            print(f"🔄 Suppressing repeated {signal} signal")
            return None
        
        # Update signal tracking
        if signal:
            self.last_signal = signal
            self.last_signal_time = current_time
            print(f"🎯 {signal} signal generated at {current_time.strftime('%H:%M:%S')}")
        
        return signal

    def get_parameters(self) -> Dict[str, Any]:
        """Get the current strategy parameters."""
        return {
            "short_window": self.short_window,
            "long_window": self.long_window,
            "cooldown_period": self.cooldown_period,
            "min_data_points": self.min_data_points,
            "last_signal": self.last_signal,
            "last_signal_time": self.last_signal_time.isoformat() if self.last_signal_time else None
        }
    
    def reset_signal_tracking(self):
        """Reset signal tracking (useful for testing or strategy reset)."""
        self.last_signal = None
        self.last_signal_time = None
        print("🔄 Signal tracking reset")
    
    def get_signal_strength(self, market_data: MarketData) -> Optional[float]:
        """
        Calculate signal strength based on SMA separation.
        
        Args:
            market_data: Market data containing price information
            
        Returns:
            Optional[float]: Signal strength as percentage (0-100), None if no signal
        """
        if len(market_data.prices) < self.long_window:
            return None
        
        short_sma = np.mean(market_data.prices[-self.short_window:])
        long_sma = np.mean(market_data.prices[-self.long_window:])
        
        # Calculate separation as percentage
        separation = abs(short_sma - long_sma) / long_sma * 100
        
        return separation
    
    def get_market_trend(self, market_data: MarketData) -> str:
        """
        Determine current market trend based on SMA relationship.
        
        Args:
            market_data: Market data containing price information
            
        Returns:
            str: "BULLISH", "BEARISH", or "SIDEWAYS"
        """
        if len(market_data.prices) < self.long_window:
            return "INSUFFICIENT_DATA"
        
        short_sma = np.mean(market_data.prices[-self.short_window:])
        long_sma = np.mean(market_data.prices[-self.long_window:])
        
        # Calculate separation percentage
        separation = abs(short_sma - long_sma) / long_sma * 100
        
        if short_sma > long_sma and separation > 0.5:
            return "BULLISH"
        elif short_sma < long_sma and separation > 0.5:
            return "BEARISH"
        else:
            return "SIDEWAYS" 