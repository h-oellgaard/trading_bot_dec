import pytest
from datetime import datetime
from src.domain.coin import Coin
from src.domain.trade import Trade
from src.domain.strategy import MarketData

@pytest.fixture
def sample_coin():
    """Fixture providing a sample coin for testing."""
    return Coin(symbol="BTC", name="Bitcoin", precision=8)

@pytest.fixture
def sample_trade(sample_coin):
    """Fixture providing a sample trade for testing."""
    return Trade(
        coin=sample_coin,
        action="BUY",
        amount=1.0,
        price=50000.0,
        timestamp=datetime.now()
    )

@pytest.fixture
def sample_market_data():
    """Fixture providing sample market data for testing."""
    return MarketData(
        prices=[100.0, 102.0, 104.0, 103.0, 106.0],
        volume=[1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
        timestamp=[1.0, 2.0, 3.0, 4.0, 5.0]
    )

@pytest.fixture
def mock_market_data():
    """Fixture providing mock market data for testing a bullish crossover."""
    # Previous: short SMA = 100, long SMA = 100 (equal)
    # Now: short SMA = 105, long SMA = 103.33 (short crosses above long)
    return MarketData(
        prices=[100.0, 100.0, 100.0, 100.0, 110.0],
        volume=[1000.0]*5,
        timestamp=[1.0, 2.0, 3.0, 4.0, 5.0]
    ) 