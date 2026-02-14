"""
Trading strategy module.
Implements the trading logic based on technical indicators.
"""
from typing import Optional, Tuple
from models import Candle, Signal, SignalType
from indicators import ema_below_ema_for_periods, ema_above_ema_for_periods, get_latest_ema
import uuid
from datetime import datetime


class TradingStrategy:
    """Trading strategy implementation."""
    
    def __init__(
        self,
        short_ema_period: int = 10,
        medium_ema_period: int = 20,
        long_ema_period: int = 50
    ):
        """
        Initialize trading strategy using three EMA indicators.
        
        Args:
            short_ema_period: Period for short EMA
            medium_ema_period: Period for medium EMA
            long_ema_period: Period for long EMA
        """
        self.short_ema_period = short_ema_period
        self.medium_ema_period = medium_ema_period
        self.long_ema_period = long_ema_period
    
    def generate_signal(
        self,
        candles: list[Candle],
        has_open_trade: bool,
        in_cooldown: bool = False
    ) -> Signal:
        """
        Generate trading signal based on strategy rules using three EMAs.
        
        Strategy:
        - SELL: When short EMA goes below medium EMA and stays there for 3 candles
        - BUY: When medium EMA goes above long EMA and stays there for 3 candles
        - Cooldown: 25 candles after a sell before allowing new buy
        
        Args:
            candles: List of Candle objects (must be sorted by timestamp)
            has_open_trade: Whether there is currently an open trade
            in_cooldown: Whether we are in cooldown period after a sell
            
        Returns:
            Signal object
        """
        if len(candles) < self.long_ema_period + 3:
            # Not enough data
            return Signal(
                signal_id=str(uuid.uuid4()),
                signal_type=SignalType.HOLD,
                timestamp=datetime.now(),
                price=candles[-1].close if candles else 0.0,
                reason="Insufficient data for signal generation"
            )
        
        current_price = candles[-1].close
        timestamp = datetime.now()
        
        # Get latest indicator values
        short_ema = get_latest_ema(candles, self.short_ema_period)
        medium_ema = get_latest_ema(candles, self.medium_ema_period)
        long_ema = get_latest_ema(candles, self.long_ema_period)
        
        # Check if we have valid indicator values
        if short_ema is None or medium_ema is None or long_ema is None:
            return Signal(
                signal_id=str(uuid.uuid4()),
                signal_type=SignalType.HOLD,
                timestamp=timestamp,
                price=current_price,
                short_ema=short_ema,
                medium_ema=medium_ema,
                long_ema=long_ema,
                reason="Insufficient data for indicators"
            )
        
        # SELL signal: Short EMA below medium EMA for 3 candles
        if has_open_trade:
            if ema_below_ema_for_periods(
                candles,
                self.short_ema_period,
                self.medium_ema_period,
                periods=3
            ):
                return Signal(
                    signal_id=str(uuid.uuid4()),
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    short_ema=short_ema,
                    medium_ema=medium_ema,
                    long_ema=long_ema,
                    reason=f"Short EMA ({short_ema:.2f}) below medium EMA ({medium_ema:.2f}) for 3 periods"
                )
        
        # BUY signal: Medium EMA above long EMA for 3 candles (only if not in cooldown)
        if not has_open_trade and not in_cooldown:
            if ema_above_ema_for_periods(
                candles,
                self.medium_ema_period,
                self.long_ema_period,
                periods=3
            ):
                return Signal(
                    signal_id=str(uuid.uuid4()),
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    short_ema=short_ema,
                    medium_ema=medium_ema,
                    long_ema=long_ema,
                    reason=f"Medium EMA ({medium_ema:.2f}) above long EMA ({long_ema:.2f}) for 3 periods"
                )
        
        # Default: HOLD
        hold_reason = "No signal conditions met"
        if in_cooldown:
            hold_reason = "In cooldown period after sell"
        
        return Signal(
            signal_id=str(uuid.uuid4()),
            signal_type=SignalType.HOLD,
            timestamp=timestamp,
            price=current_price,
            short_ema=short_ema,
            medium_ema=medium_ema,
            long_ema=long_ema,
            reason=hold_reason
        )
    
    def should_trailing_stop_loss(
        self,
        entry_price: float,
        current_price: float,
        highest_price: float,
        trailing_stop_percent: float
    ) -> Tuple[bool, float]:
        """
        Check if trailing stop loss condition is met.
        
        Trailing stop loss: If price drops 7% from the highest price reached,
        trigger stop loss.
        
        Args:
            entry_price: Entry price of the trade
            current_price: Current market price
            highest_price: Highest price reached since entry
            trailing_stop_percent: Trailing stop loss percentage (e.g., 7.0)
            
        Returns:
            Tuple of (should_trigger, new_highest_price)
        """
        # Update highest price if current price is higher
        new_highest_price = max(highest_price, current_price)
        
        # Check if price has dropped trailing_stop_percent from highest
        if new_highest_price > 0:
            drop_percent = ((new_highest_price - current_price) / new_highest_price) * 100
            if drop_percent >= trailing_stop_percent:
                return True, new_highest_price
        
        return False, new_highest_price

