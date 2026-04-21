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
    multiplier = 2.0 / (period + 1)

    # First valid EMA at index (period - 1)
    initial_sma = sum(candle.close for candle in candles[0:period]) / period
    ema_values.append(initial_sma)

    for i in range(period, len(candles)):
        # Use candle at index i, previous EMA at index i-1
        ema = (candles[i].close - ema_values[-1]) * multiplier + ema_values[-1]
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


def ema_crossover(candles: List[Candle], short_period: int, long_period: int) -> bool:
    """
    Check if short EMA has crossed above long EMA (golden cross).
    
    Args:
        candles: List of Candle objects (must have at least long_period + 1 candles)
        short_period: Period for short EMA
        long_period: Period for long EMA
        
    Returns:
        True if short EMA crossed above long EMA, False otherwise
    """
    if len(candles) < long_period + 1:
        return False
    
    short_ema = calculate_ema(candles, short_period)
    long_ema = calculate_ema(candles, long_period)
    
    # Need at least 2 values to detect crossover
    if short_ema[-1] is None or short_ema[-2] is None:
        return False
    if long_ema[-1] is None or long_ema[-2] is None:
        return False
    
    # Check if short EMA crossed above long EMA
    previous_short_below = short_ema[-2] < long_ema[-2]
    current_short_above = short_ema[-1] > long_ema[-1]
    
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


def ema_below_ema_for_periods(
    candles: List[Candle],
    short_ema_period: int,
    long_ema_period: int,
    periods: int = 3
) -> bool:
    """
    Check if short EMA has been below long EMA for specified number of periods.
    
    Args:
        candles: List of Candle objects
        short_ema_period: Period for short EMA calculation
        long_ema_period: Period for long EMA calculation
        periods: Number of consecutive periods to check
        
    Returns:
        True if short EMA has been below long EMA for the specified periods, False otherwise
    """
    if len(candles) < max(short_ema_period, long_ema_period) + periods - 1:
        return False
    
    short_ema_values = calculate_ema(candles, short_ema_period)
    long_ema_values = calculate_ema(candles, long_ema_period)
    
    # Check last 'periods' values
    for i in range(periods):
        idx = len(candles) - 1 - i
        if short_ema_values[idx] is None or long_ema_values[idx] is None:
            return False
        if short_ema_values[idx] >= long_ema_values[idx]:
            return False
    
    return True


def ema_above_ema_for_periods(
    candles: List[Candle],
    medium_ema_period: int,
    long_ema_period: int,
    periods: int = 3
) -> bool:
    """
    Check if medium EMA has been above long EMA for specified number of periods.
    
    Args:
        candles: List of Candle objects
        medium_ema_period: Period for medium EMA calculation
        long_ema_period: Period for long EMA calculation
        periods: Number of consecutive periods to check
        
    Returns:
        True if medium EMA has been above long EMA for the specified periods, False otherwise
    """
    if len(candles) < max(medium_ema_period, long_ema_period) + periods - 1:
        return False
    
    medium_ema_values = calculate_ema(candles, medium_ema_period)
    long_ema_values = calculate_ema(candles, long_ema_period)
    
    # Check last 'periods' values
    for i in range(periods):
        idx = len(candles) - 1 - i
        if medium_ema_values[idx] is None or long_ema_values[idx] is None:
            return False
        if medium_ema_values[idx] <= long_ema_values[idx]:
            return False
    
    return True


def detect_ema_cross_and_confirm(
    candles: List[Candle],
    short_period: int,
    medium_period: int,
    confirmation_period: int = 2
) -> bool:
    """
    Detect if the short EMA crosses below the medium EMA and confirm the trend.

    Args:
        candles: List of Candle objects (sorted by timestamp).
        short_period: Period for the short EMA.
        medium_period: Period for the medium EMA.
        confirmation_period: Number of periods to confirm the trend.

    Returns:
        True if the cross and confirmation occur, False otherwise.
    """
    if len(candles) < max(short_period, medium_period) + confirmation_period:
        print("Not enough candles for calculation.")
        return False

    short_ema = calculate_ema(candles, short_period)
    medium_ema = calculate_ema(candles, medium_period)

    print("Short EMA:", short_ema)
    print("Medium EMA:", medium_ema)

    # Check for cross
    if short_ema[-confirmation_period - 1] > medium_ema[-confirmation_period - 1] and \
       short_ema[-confirmation_period] < medium_ema[-confirmation_period]:
        print("Crossover detected.")
        # Confirm the trend
        for i in range(-confirmation_period, 0):
            if short_ema[i] >= medium_ema[i]:
                print(f"Trend confirmation failed at index {i}.")
                return False
        print("Trend confirmed.")
        return True

    print("No crossover detected.")
    return False


def ema_death_cross(candles: List[Candle], short_period: int, long_period: int) -> bool:
    """Check if short EMA crossed below long EMA"""
    if len(candles) < long_period + 1:
        return False

    short_ema = calculate_ema(candles, short_period)
    long_ema = calculate_ema(candles, long_period)

    if any(v is None for v in [short_ema[-1], short_ema[-2], long_ema[-1], long_ema[-2]]):
        return False

    # Previous: short > long, Current: short < long
    return short_ema[-2] > long_ema[-2] and short_ema[-1] < long_ema[-1]


def confirm_trend_direction(
    candles: List[Candle],
    short_period: int,
    long_period: int,
    direction: str,  # 'above' or 'below'
    min_periods: int = 2
) -> bool:
    """Confirm trend has persisted for N periods"""
    short_ema = calculate_ema(candles, short_period)
    long_ema = calculate_ema(candles, long_period)

    for i in range(min_periods):
        idx = -(i + 1)
        if short_ema[idx] is None or long_ema[idx] is None:
            return False
        if direction == 'below' and short_ema[idx] >= long_ema[idx]:
            return False
        if direction == 'above' and short_ema[idx] <= long_ema[idx]:
            return False

    return True

