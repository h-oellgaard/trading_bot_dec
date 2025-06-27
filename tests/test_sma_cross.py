import pytest
from src.domain.strategy import MarketData
from src.strategies.sma_cross import SmaCrossStrategy

@pytest.mark.unit
def test_sma_cross_initialization():
    """Test strategy initialization with valid parameters."""
    strategy = SmaCrossStrategy(short_window=3, long_window=5)
    assert strategy.short_window == 3
    assert strategy.long_window == 5

@pytest.mark.unit
def test_sma_cross_invalid_parameters():
    """Test strategy initialization with invalid parameters."""
    with pytest.raises(ValueError):
        SmaCrossStrategy(short_window=5, long_window=3)

@pytest.mark.unit
def test_sma_cross_buy_signal(mock_market_data):
    """Test generation of buy signal on bullish crossover."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    signal = strategy.generate_signal(mock_market_data)
    assert signal == "BUY"

@pytest.mark.unit
def test_sma_cross_sell_signal():
    """Test generation of sell signal on bearish crossover."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    # Previous: short SMA = 110, long SMA = 110 (equal)
    # Now: short SMA = 105, long SMA = 106.67 (short crosses below long)
    market_data = MarketData(
        prices=[110.0, 110.0, 110.0, 110.0, 100.0],
        volume=[1000.0]*5,
        timestamp=[1.0, 2.0, 3.0, 4.0, 5.0]
    )
    signal = strategy.generate_signal(market_data)
    assert signal == "SELL"

@pytest.mark.unit
def test_sma_cross_no_signal():
    """Test no signal generation when no crossover occurs."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    market_data = MarketData(
        prices=[100.0, 101.0, 102.0, 103.0, 104.0],
        volume=[1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
        timestamp=[1.0, 2.0, 3.0, 4.0, 5.0]
    )
    signal = strategy.generate_signal(market_data)
    assert signal is None

@pytest.mark.unit
def test_sma_cross_insufficient_data():
    """Test behavior with insufficient data points."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    market_data = MarketData(
        prices=[100.0, 101.0],
        volume=[1000.0, 1000.0],
        timestamp=[1.0, 2.0]
    )
    signal = strategy.generate_signal(market_data)
    assert signal is None

@pytest.mark.unit
def test_sma_cross_parameters():
    """Test getting strategy parameters."""
    strategy = SmaCrossStrategy(short_window=2, long_window=3)
    params = strategy.get_parameters()
    assert params == {
        "short_window": 2,
        "long_window": 3
    } 