"""
Trading strategy module.
Implements the trading logic based on technical indicators.
"""
from typing import Optional, Tuple
from models import Candle, Signal, SignalType
from indicators import sma_crossover, ema_below_sma_for_periods, get_latest_sma, get_latest_ema
import uuid
from datetime import datetime


class TradingStrategy:
    """Trading strategy implementation."""
    
    def __init__(
        self,
        short_sma_period: int = 10,
        long_sma_period: int = 30,
        short_ema_period: int = 12,
        long_sma_for_ema: int = 30
    ):
        """
        Initialize trading strategy.
        
        Args:
            short_sma_period: Period for short SMA
            long_sma_period: Period for long SMA
            short_ema_period: Period for short EMA
            long_sma_for_ema: Period for long SMA used in EMA comparison
        """
        self.short_sma_period = short_sma_period
        self.long_sma_period = long_sma_period
        self.short_ema_period = short_ema_period
        self.long_sma_for_ema = long_sma_for_ema
    
    def generate_signal(
        self,
        candles: list[Candle],
        has_open_trade: bool
    ) -> Signal:
        """
        Generate trading signal based on strategy rules.
        
        Strategy:
        - BUY: When short SMA crosses above long SMA
        - SELL: When short EMA lies below long SMA for 3 candles in a row
        
        Args:
            candles: List of Candle objects (must be sorted by timestamp)
            has_open_trade: Whether there is currently an open trade
            
        Returns:
            Signal object
        """
        if len(candles) < max(self.long_sma_period, self.long_sma_for_ema) + 1:
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
        short_sma = get_latest_sma(candles, self.short_sma_period)
        long_sma = get_latest_sma(candles, self.long_sma_period)
        short_ema = get_latest_ema(candles, self.short_ema_period)
        long_sma_for_ema = get_latest_sma(candles, self.long_sma_for_ema)
        
        # SELL signal: Short EMA below long SMA for 3 candles
        if has_open_trade:
            if ema_below_sma_for_periods(
                candles,
                self.short_ema_period,
                self.long_sma_for_ema,
                periods=3
            ):
                return Signal(
                    signal_id=str(uuid.uuid4()),
                    signal_type=SignalType.SELL,
                    timestamp=timestamp,
                    price=current_price,
                    short_sma=short_sma,
                    long_sma=long_sma_for_ema,
                    short_ema=short_ema,
                    reason=f"Short EMA ({short_ema:.2f}) below long SMA ({long_sma_for_ema:.2f}) for 3 periods"
                )
        
        # BUY signal: Short SMA crosses above long SMA
        if not has_open_trade:
            if sma_crossover(candles, self.short_sma_period, self.long_sma_period):
                return Signal(
                    signal_id=str(uuid.uuid4()),
                    signal_type=SignalType.BUY,
                    timestamp=timestamp,
                    price=current_price,
                    short_sma=short_sma,
                    long_sma=long_sma,
                    reason=f"Short SMA ({short_sma:.2f}) crossed above long SMA ({long_sma:.2f})"
                )
        
        # Default: HOLD
        return Signal(
            signal_id=str(uuid.uuid4()),
            signal_type=SignalType.HOLD,
            timestamp=timestamp,
            price=current_price,
            short_sma=short_sma,
            long_sma=long_sma,
            short_ema=short_ema,
            reason="No signal conditions met"
        )
    
    def should_take_profit(self, entry_price: float, current_price: float, take_profit_percent: float) -> bool:
        """
        Check if take profit condition is met.
        
        Args:
            entry_price: Entry price of the trade
            current_price: Current market price
            take_profit_percent: Take profit percentage
            
        Returns:
            True if take profit should be triggered
        """
        profit_percent = ((current_price - entry_price) / entry_price) * 100
        return profit_percent >= take_profit_percent
    
    def should_stop_loss(self, entry_price: float, current_price: float, stop_loss_percent: float) -> bool:
        """
        Check if stop loss condition is met.
        
        Args:
            entry_price: Entry price of the trade
            current_price: Current market price
            stop_loss_percent: Stop loss percentage
            
        Returns:
            True if stop loss should be triggered
        """
        loss_percent = ((entry_price - current_price) / entry_price) * 100
        return loss_percent >= stop_loss_percent

