from typing import Optional, Dict, Any, List
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..domain.strategy import TradingStrategy, MarketData

@dataclass
class Position:
    """Represents a trading position with tracking information."""
    entry_price: float
    entry_time: datetime
    highest_price: float
    highest_time: datetime
    amount: float
    symbol: str

@dataclass
class ProfitSplit:
    """Represents profit splitting configuration."""
    tax_percentage: float = 40.0
    reinvest_percentage: float = 45.0
    withdrawal_percentage: float = 15.0
    
    def validate(self):
        """Validate that percentages sum to 100%."""
        total = self.tax_percentage + self.reinvest_percentage + self.withdrawal_percentage
        if abs(total - 100.0) > 0.01:
            raise ValueError(f"Profit split percentages must sum to 100%, got {total}%")

class TrendFollowingStrategy(TradingStrategy):
    """
    Trend-following strategy with SMA/EMA crossovers and trailing stop loss.
    
    Features:
    - SMA crossover for entry signals
    - EMA/SMA crossover for exit signals
    - Trailing stop loss protection
    - Profit splitting (tax, reinvest, withdrawal)
    - Position tracking and management
    """
    
    def __init__(self, 
                 sma_short: int = 5,
                 sma_long: int = 12,
                 ema_short: int = 5,
                 trailing_stop_percentage: float = 5.0,
                 exit_candles: int = 3,
                 initial_capital: float = 10000.0,
                 profit_split: Optional[ProfitSplit] = None):
        """
        Initialize the trend-following strategy.
        
        Args:
            sma_short: Short-term SMA window for entry signals
            sma_long: Long-term SMA window for entry signals
            ema_short: Short-term EMA window for exit signals
            trailing_stop_percentage: Trailing stop loss percentage
            exit_candles: Number of candles EMA must be below SMA for exit
            initial_capital: Initial trading capital
            profit_split: Profit splitting configuration
        """
        # Validate parameters
        if sma_short >= sma_long:
            raise ValueError("Short SMA must be smaller than long SMA")
        if trailing_stop_percentage <= 0 or trailing_stop_percentage > 50:
            raise ValueError("Trailing stop must be between 0 and 50%")
        if exit_candles < 1:
            raise ValueError("Exit candles must be at least 1")
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive")
        
        # Strategy parameters
        self.sma_short = sma_short
        self.sma_long = sma_long
        self.ema_short = ema_short
        self.trailing_stop_percentage = trailing_stop_percentage
        self.exit_candles = exit_candles
        self.initial_capital = initial_capital
        
        # Profit splitting
        self.profit_split = profit_split or ProfitSplit()
        self.profit_split.validate()
        
        # Position tracking
        self.current_position: Optional[Position] = None
        self.available_capital = initial_capital
        self.total_profit = 0.0
        self.total_trades = 0
        
        # Signal tracking for exit conditions
        self.ema_below_sma_count = 0
        self.last_signal_time = None
        
        print(f"📊 Trend Following Strategy initialized:")
        print(f"   SMA Short: {sma_short}, SMA Long: {sma_long}")
        print(f"   EMA Short: {ema_short}")
        print(f"   Trailing Stop: {trailing_stop_percentage}%")
        print(f"   Exit Candles: {exit_candles}")
        print(f"   Initial Capital: ${initial_capital:,.2f}")
        print(f"   Profit Split: Tax {self.profit_split.tax_percentage}%, "
              f"Reinvest {self.profit_split.reinvest_percentage}%, "
              f"Withdraw {self.profit_split.withdrawal_percentage}%")

    def generate_signal(self, market_data: MarketData) -> Optional[str]:
        """
        Generate trading signals based on SMA/EMA crossovers and trailing stop.
        
        Args:
            market_data: Market data containing price information
            
        Returns:
            Optional[str]: "BUY", "SELL", or None
        """
        if len(market_data.prices) < self.sma_long + 1:
            print(f"⚠️  Insufficient data: {len(market_data.prices)} < {self.sma_long + 1}")
            return None
        
        current_price = market_data.prices[-1]
        current_time = datetime.now()
        
        # Calculate indicators
        sma_short_current = np.mean(market_data.prices[-self.sma_short:])
        sma_long_current = np.mean(market_data.prices[-self.sma_long:])
        
        # Calculate previous values for crossover detection
        sma_short_prev = np.mean(market_data.prices[-self.sma_short-1:-1])
        sma_long_prev = np.mean(market_data.prices[-self.sma_long-1:-1])
        
        # Calculate EMA for exit signals
        ema_short_current = self._calculate_ema(market_data.prices, self.ema_short)
        
        # Check for trailing stop loss
        if self.current_position:
            trailing_stop_triggered = self._check_trailing_stop(current_price)
            if trailing_stop_triggered:
                return self._execute_sell_signal("TRAILING_STOP", current_price, current_time)
        
        # Check for exit signal (EMA below SMA for N candles)
        if self.current_position:
            exit_signal = self._check_exit_signal(sma_long_current, ema_short_current)
            if exit_signal:
                return self._execute_sell_signal("EXIT_SIGNAL", current_price, current_time)
        
        # Check for buy signal (SMA crossover)
        if not self.current_position:
            buy_signal = self._check_buy_signal(sma_short_prev, sma_long_prev, 
                                              sma_short_current, sma_long_current)
            if buy_signal:
                return self._execute_buy_signal(current_price, current_time)
        
        return None

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return np.mean(prices)
        
        alpha = 2.0 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
        
        return ema

    def _check_buy_signal(self, sma_short_prev: float, sma_long_prev: float,
                         sma_short_current: float, sma_long_current: float) -> bool:
        """Check for SMA crossover buy signal."""
        # Short SMA crosses above long SMA
        return (sma_short_prev <= sma_long_prev and 
                sma_short_current > sma_long_current)

    def _check_exit_signal(self, sma_long: float, ema_short: float) -> bool:
        """Check for EMA below SMA exit signal."""
        if ema_short < sma_long:
            self.ema_below_sma_count += 1
        else:
            self.ema_below_sma_count = 0
        
        return self.ema_below_sma_count >= self.exit_candles

    def _check_trailing_stop(self, current_price: float) -> bool:
        """Check if trailing stop loss is triggered."""
        if not self.current_position:
            return False
        
        # Update highest price if current price is higher
        if current_price > self.current_position.highest_price:
            self.current_position.highest_price = current_price
            self.current_position.highest_time = datetime.now()
        
        # Check if price has dropped below trailing stop threshold
        stop_price = self.current_position.highest_price * (1 - self.trailing_stop_percentage / 100)
        return current_price <= stop_price

    def _execute_buy_signal(self, price: float, time: datetime) -> str:
        """Execute buy signal and create position."""
        if self.available_capital <= 0:
            print("⚠️  No available capital for buy signal")
            return None
        
        # Calculate position size (use all available capital)
        position_size = self.available_capital / price
        
        # Create position
        self.current_position = Position(
            entry_price=price,
            entry_time=time,
            highest_price=price,
            highest_time=time,
            amount=position_size,
            symbol="CRYPTO"  # This should be passed from market data
        )
        
        # Update capital
        self.available_capital = 0.0
        
        print(f"🎯 BUY signal executed:")
        print(f"   Entry Price: ${price:,.2f}")
        print(f"   Position Size: {position_size:.6f}")
        print(f"   Available Capital: ${self.available_capital:,.2f}")
        
        return "BUY"

    def _execute_sell_signal(self, reason: str, price: float, time: datetime) -> str:
        """Execute sell signal and close position."""
        if not self.current_position:
            print("⚠️  No position to sell")
            return None
        
        # Calculate profit/loss
        entry_value = self.current_position.entry_price * self.current_position.amount
        exit_value = price * self.current_position.amount
        profit = exit_value - entry_value
        profit_percentage = (profit / entry_value) * 100
        
        # Update totals
        self.total_profit += profit
        self.total_trades += 1
        
        # Split profit if positive
        if profit > 0:
            tax_amount = profit * (self.profit_split.tax_percentage / 100)
            reinvest_amount = profit * (self.profit_split.reinvest_percentage / 100)
            withdrawal_amount = profit * (self.profit_split.withdrawal_percentage / 100)
            
            # Add reinvested amount back to capital
            self.available_capital = reinvest_amount
        else:
            # If loss, all remaining value goes back to capital
            self.available_capital = exit_value
            tax_amount = reinvest_amount = withdrawal_amount = 0.0
        
        print(f"🎯 SELL signal executed ({reason}):")
        print(f"   Exit Price: ${price:,.2f}")
        print(f"   Profit/Loss: ${profit:,.2f} ({profit_percentage:+.2f}%)")
        print(f"   Tax: ${tax_amount:,.2f}")
        print(f"   Reinvest: ${reinvest_amount:,.2f}")
        print(f"   Withdraw: ${withdrawal_amount:,.2f}")
        print(f"   Available Capital: ${self.available_capital:,.2f}")
        
        # Clear position
        self.current_position = None
        self.ema_below_sma_count = 0
        
        return "SELL"

    def get_parameters(self) -> Dict[str, Any]:
        """Get the current strategy parameters."""
        return {
            "sma_short": self.sma_short,
            "sma_long": self.sma_long,
            "ema_short": self.ema_short,
            "trailing_stop_percentage": self.trailing_stop_percentage,
            "exit_candles": self.exit_candles,
            "initial_capital": self.initial_capital,
            "available_capital": self.available_capital,
            "total_profit": self.total_profit,
            "total_trades": self.total_trades,
            "profit_split": {
                "tax_percentage": self.profit_split.tax_percentage,
                "reinvest_percentage": self.profit_split.reinvest_percentage,
                "withdrawal_percentage": self.profit_split.withdrawal_percentage
            },
            "current_position": {
                "entry_price": self.current_position.entry_price if self.current_position else None,
                "entry_time": self.current_position.entry_time.isoformat() if self.current_position else None,
                "highest_price": self.current_position.highest_price if self.current_position else None,
                "amount": self.current_position.amount if self.current_position else None
            },
            "ema_below_sma_count": self.ema_below_sma_count
        }
    
    def get_position_status(self) -> Dict[str, Any]:
        """Get detailed position status."""
        if not self.current_position:
            return {"status": "NO_POSITION"}
        
        current_price = 0.0  # This should be passed from market data
        unrealized_pnl = (current_price - self.current_position.entry_price) * self.current_position.amount
        unrealized_pnl_percentage = (unrealized_pnl / (self.current_position.entry_price * self.current_position.amount)) * 100
        
        return {
            "status": "IN_POSITION",
            "entry_price": self.current_position.entry_price,
            "current_price": current_price,
            "highest_price": self.current_position.highest_price,
            "amount": self.current_position.amount,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percentage": unrealized_pnl_percentage,
            "trailing_stop_price": self.current_position.highest_price * (1 - self.trailing_stop_percentage / 100),
            "days_in_position": (datetime.now() - self.current_position.entry_time).days
        }
    
    def reset_position(self):
        """Reset current position (useful for testing)."""
        if self.current_position:
            # Return capital to available
            self.available_capital += self.current_position.entry_price * self.current_position.amount
            self.current_position = None
            self.ema_below_sma_count = 0
            print("🔄 Position reset")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        total_return = ((self.available_capital + self.total_profit) / self.initial_capital - 1) * 100
        
        return {
            "initial_capital": self.initial_capital,
            "current_capital": self.available_capital,
            "total_profit": self.total_profit,
            "total_trades": self.total_trades,
            "total_return_percentage": total_return,
            "average_profit_per_trade": self.total_profit / self.total_trades if self.total_trades > 0 else 0,
            "win_rate": "N/A"  # Would need to track individual trade results
        }
