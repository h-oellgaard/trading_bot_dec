"""
Technical indicators module.
Pure functions with no side effects - fully testable.
"""
from typing import List
from models import Candle


def calculate_sma(candles: List[Candle], period: int) -> List[float]:
    """
    Calculate Simple Moving Average (SMA).
    
    Args:
        candles: List of Candle objects (must be sorted by timestamp)
        period: Period for SMA calculation
        
    Returns:
        List of SMA values (same length as candles, None for first period-1 values)
    """
    if len(candles) < period:
        return [None] * len(candles)
    
    sma_values = [None] * (period - 1)
    
    for i in range(period - 1, len(candles)):
        sum_close = sum(candle.close for candle in candles[i - period + 1:i + 1])
        sma = sum_close / period
        sma_values.append(sma)
    
    return sma_values


def calculate_ema(candles: List[Candle], period: int) -> List[float]:
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        candles: List of Candle objects (must be sorted by timestamp)
        period: Period for EMA calculation
        
    Returns:
        List of EMA values (same length as candles, None for first period-1 values)
    """
    if len(candles) < period:
        return [None] * len(candles)
    
    ema_values = [None] * (period - 1)
    
    # Calculate initial SMA for first EMA value
    multiplier = 2.0 / (period + 1)
    initial_sma = sum(candle.close for candle in candles[:period]) / period
    ema_values.append(initial_sma)
    
    # Calculate subsequent EMA values
    for i in range(period, len(candles)):
        ema = (candles[i].close - ema_values[i - 1]) * multiplier + ema_values[i - 1]
        ema_values.append(ema)
    
    return ema_values


def get_latest_sma(candles: List[Candle], period: int) -> float:
    """
    Get the latest SMA value.
    
    Args:
        candles: List of Candle objects
        period: Period for SMA calculation
        
    Returns:
        Latest SMA value or None if insufficient data
    """
    sma_values = calculate_sma(candles, period)
    return sma_values[-1] if sma_values else None


def get_latest_ema(candles: List[Candle], period: int) -> float:
    """
    Get the latest EMA value.
    
    Args:
        candles: List of Candle objects
        period: Period for EMA calculation
        
    Returns:
        Latest EMA value or None if insufficient data
    """
    ema_values = calculate_ema(candles, period)
    return ema_values[-1] if ema_values else None


def sma_crossover(candles: List[Candle], short_period: int, long_period: int) -> bool:
    """
    Check if short SMA has crossed above long SMA (golden cross).
    
    Args:
        candles: List of Candle objects (must have at least long_period + 1 candles)
        short_period: Period for short SMA
        long_period: Period for long SMA
        
    Returns:
        True if short SMA crossed above long SMA, False otherwise
    """
    if len(candles) < long_period + 1:
        return False
    
    short_sma = calculate_sma(candles, short_period)
    long_sma = calculate_sma(candles, long_period)
    
    # Need at least 2 values to detect crossover
    if short_sma[-1] is None or short_sma[-2] is None:
        return False
    if long_sma[-1] is None or long_sma[-2] is None:
        return False
    
    # Check if short SMA crossed above long SMA
    previous_short_below = short_sma[-2] < long_sma[-2]
    current_short_above = short_sma[-1] > long_sma[-1]
    
    return previous_short_below and current_short_above


def ema_below_sma_for_periods(
    candles: List[Candle],
    ema_period: int,
    sma_period: int,
    periods: int = 3
) -> bool:
    """
    Check if short EMA has been below long SMA for specified number of periods.
    
    Args:
        candles: List of Candle objects
        ema_period: Period for EMA calculation
        sma_period: Period for SMA calculation
        periods: Number of consecutive periods to check
        
    Returns:
        True if EMA has been below SMA for the specified periods, False otherwise
    """
    if len(candles) < max(ema_period, sma_period) + periods - 1:
        return False
    
    ema_values = calculate_ema(candles, ema_period)
    sma_values = calculate_sma(candles, sma_period)
    
    # Check last 'periods' values
    for i in range(periods):
        idx = len(candles) - 1 - i
        if ema_values[idx] is None or sma_values[idx] is None:
            return False
        if ema_values[idx] >= sma_values[idx]:
            return False
    
    return True

