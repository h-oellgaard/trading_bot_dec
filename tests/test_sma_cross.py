import pytest
from src.domain.strategy import MarketData
from src.strategies.sma_cross import SmaCrossStrategy

def test_sma_cross_initialization():
    """Test strategy initialization with valid parameters."""
    strategy = SmaCrossStrategy(short_window=3, long_window=5)
    assert strategy.short_window == 3
    assert strategy.long_window == 5

def test_sma_cross_invalid_parameters():
    """Test strategy initialization with invalid parameters."""
    with pytest.raises(ValueError):
        SmaCrossStrategy(short_window=5, long_window=3)

def test_sma_cross_buy_signal():
    """Test generation of buy signal on bullish crossover."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    # Create data that will cause a bullish crossover
    market_data = MarketData(
        prices=[100, 102, 104, 103, 106],
        volume=[1000, 1000, 1000, 1000, 1000],
        timestamp=[1, 2, 3, 4, 5]
    )
    signal = strategy.generate_signal(market_data)
    assert signal == "BUY"

def test_sma_cross_sell_signal():
    """Test generation of sell signal on bearish crossover."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    # Create data that will cause a bearish crossover
    market_data = MarketData(
        prices=[106, 104, 102, 100, 98],
        volume=[1000, 1000, 1000, 1000, 1000],
        timestamp=[1, 2, 3, 4, 5]
    )
    signal = strategy.generate_signal(market_data)
    assert signal == "SELL"

def test_sma_cross_no_signal():
    """Test no signal generation when no crossover occurs."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    # Create data with no crossover
    market_data = MarketData(
        prices=[100, 101, 102, 103, 104],
        volume=[1000, 1000, 1000, 1000, 1000],
        timestamp=[1, 2, 3, 4, 5]
    )
    signal = strategy.generate_signal(market_data)
    assert signal is None

def test_sma_cross_insufficient_data():
    """Test behavior with insufficient data points."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    # Create data with insufficient points
    market_data = MarketData(
        prices=[100, 101],
        volume=[1000, 1000],
        timestamp=[1, 2]
    )
    signal = strategy.generate_signal(market_data)
    assert signal is None 