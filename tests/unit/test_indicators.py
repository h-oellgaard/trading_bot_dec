"""
Unit tests for indicators module.
"""
import pytest
from datetime import datetime, timedelta
from models import Candle
from indicators import (
    calculate_sma,
    calculate_ema,
    get_latest_sma,
    get_latest_ema,
    sma_crossover,
    ema_below_sma_for_periods,
    ema_above_ema_for_periods
)


@pytest.fixture
def sample_candles():
    """Generate sample candles for testing."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    candles = []
    prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 110, 112, 111, 113, 115]
    
    for i, price in enumerate(prices):
        candles.append(Candle(
            timestamp=base_time + timedelta(hours=i),
            open=price,
            high=price + 1,
            low=price - 1,
            close=price,
            volume=100.0
        ))
    
    return candles


def test_calculate_sma(sample_candles):
    """Test SMA calculation."""
    period = 5
    sma_values = calculate_sma(sample_candles, period)
    
    # First period-1 values should be None
    assert sma_values[0] is None
    assert sma_values[period - 2] is None
    
    # First SMA value should be average of first 5 closes
    first_sma = sma_values[period - 1]
    expected = sum(c.close for c in sample_candles[:period]) / period
    assert abs(first_sma - expected) < 0.01
    
    # All subsequent values should be calculated
    assert all(sma is not None for sma in sma_values[period - 1:])


def test_calculate_ema(sample_candles):
    """Test EMA calculation."""
    period = 5
    ema_values = calculate_ema(sample_candles, period)
    
    # First period-1 values should be None
    assert ema_values[0] is None
    assert ema_values[period - 2] is None
    
    # First EMA value should be SMA
    first_ema = ema_values[period - 1]
    expected_sma = sum(c.close for c in sample_candles[:period]) / period
    assert abs(first_ema - expected_sma) < 0.01
    
    # All subsequent values should be calculated
    assert all(ema is not None for ema in ema_values[period - 1:])


def test_get_latest_sma(sample_candles):
    """Test getting latest SMA value."""
    period = 5
    latest_sma = get_latest_sma(sample_candles, period)
    
    assert latest_sma is not None
    assert isinstance(latest_sma, float)


def test_get_latest_ema(sample_candles):
    """Test getting latest EMA value."""
    period = 5
    latest_ema = get_latest_ema(sample_candles, period)
    
    assert latest_ema is not None
    assert isinstance(latest_ema, float)


def test_sma_crossover(sample_candles):
    """Test SMA crossover detection."""
    # Create candles where short SMA crosses above long SMA
    # Short period = 3, Long period = 5
    short_period = 3
    long_period = 5
    
    # Need enough candles
    if len(sample_candles) >= long_period + 1:
        result = sma_crossover(sample_candles, short_period, long_period)
        assert isinstance(result, bool)


def test_ema_below_sma_for_periods(sample_candles):
    """Test EMA below SMA for periods detection."""
    ema_period = 3
    sma_period = 5
    periods = 3
    
    result = ema_below_sma_for_periods(sample_candles, ema_period, sma_period, periods)
    assert isinstance(result, bool)


def test_ema_above_ema_for_periods(sample_candles):
    """Test EMA above EMA for periods detection."""
    medium_ema_period = 3
    long_ema_period = 5
    periods = 3
    
    result = ema_above_ema_for_periods(sample_candles, medium_ema_period, long_ema_period, periods)
    assert isinstance(result, bool)


def test_insufficient_data():
    """Test behavior with insufficient data."""
    candles = [Candle(
        timestamp=datetime.now(),
        open=100,
        high=101,
        low=99,
        close=100,
        volume=10
    )]
    
    sma = calculate_sma(candles, period=10)
    assert all(v is None for v in sma)
    
    ema = calculate_ema(candles, period=10)
    assert all(v is None for v in ema)

