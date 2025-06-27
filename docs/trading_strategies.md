# Trading Strategies Documentation

## Overview

The crypto trading bot implements a modular strategy framework that allows for easy addition and testing of different trading algorithms. All strategies inherit from the `TradingStrategy` base class and implement a standardized interface for signal generation.

## Strategy Framework

### Base Strategy Interface

All trading strategies must implement the `TradingStrategy` abstract base class:

```python
class TradingStrategy(ABC):
    @abstractmethod
    def generate_signal(self, market_data: MarketData) -> Optional[str]:
        """Generate trading signal: 'BUY', 'SELL', or None"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get current strategy parameters"""
        pass
```

### Market Data Structure

Strategies receive market data in the following format:

```python
class MarketData:
    def __init__(self, prices: List[float], volume: List[float], timestamp: List[float]):
        self.prices = prices      # Historical price data
        self.volume = volume      # Trading volume data
        self.timestamp = timestamp # Time stamps for each data point
```

## Available Strategies

### 1. Simple Moving Average (SMA) Cross Strategy

**File**: `src/strategies/sma_cross.py`

#### Description
The SMA Cross strategy is a classic trend-following algorithm that generates trading signals based on the crossover of two moving averages. It's one of the most widely used technical analysis tools in cryptocurrency trading. The strategy has been enhanced with debouncing logic and overfitting protection.

#### How It Works
1. **Two Moving Averages**: The strategy uses two simple moving averages:
   - **Short-term SMA**: Faster moving average (default: 7 periods)
   - **Long-term SMA**: Slower moving average (default: 21 periods)

2. **Signal Generation**:
   - **BUY Signal**: When the short-term SMA crosses above the long-term SMA (bullish crossover)
   - **SELL Signal**: When the short-term SMA crosses below the long-term SMA (bearish crossover)
   - **No Signal**: When the moving averages are not crossing

3. **Debouncing Features**:
   - **Cooldown Period**: Minimum time between signals (default: 60 seconds)
   - **Signal Suppression**: Prevents repeated identical signals
   - **Minimum Data Points**: Ensures sufficient historical data (default: 50 points)

#### Mathematical Formula
```
Short SMA = (Price₁ + Price₂ + ... + Priceₙ) / n
Long SMA = (Price₁ + Price₂ + ... + Priceₘ) / m

Where:
- n = short_window (default: 7)
- m = long_window (default: 21)
- Priceᵢ = price at period i
```

#### Signal Logic
```python
# Bullish crossover (BUY)
if prev_short_sma <= prev_long_sma and short_sma > long_sma:
    signal = "BUY"

# Bearish crossover (SELL)  
if prev_short_sma >= prev_long_sma and short_sma < long_sma:
    signal = "SELL"

# Debouncing: Suppress repeated signals
if signal == self.last_signal:
    return None

# Cooldown: Check minimum time between signals
if time_since_last_signal < cooldown_period:
    return None
```

#### Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `short_window` | int | 7 | Number of periods for short-term SMA |
| `long_window` | int | 21 | Number of periods for long-term SMA |
| `cooldown_period` | int | 60 | Minimum seconds between signals |
| `min_data_points` | int | 50 | Minimum data points required |

#### Overfitting Protection
The strategy includes built-in warnings and protection against overfitting:

```python
# Warning for small window sizes
if short_window < 5 or long_window < 10:
    print("⚠️  WARNING: Small window sizes may lead to overfitting")

# Critical warning for very small windows  
if short_window < 3 or long_window < 5:
    print("🚨 CRITICAL: Very small window sizes detected!")
    print("   Recommended minimum: short_window=7, long_window=21")
```

#### Usage Example
```python
from src.strategies.sma_cross import SmaCrossStrategy

# Initialize with improved defaults
strategy = SmaCrossStrategy(short_window=7, long_window=21)

# Custom configuration with debouncing
strategy = SmaCrossStrategy(
    short_window=10,
    long_window=30,
    cooldown_period=300,  # 5 minutes between signals
    min_data_points=100
)

# Use in trading engine
engine = TradingEngine(
    strategy=strategy,
    symbols=['ETHDKK', 'BTCDKK'],
    interval=60
)
```

#### New Features

##### Signal Strength Analysis
```python
# Get signal strength as percentage
strength = strategy.get_signal_strength(market_data)
print(f"Signal strength: {strength:.2f}%")
```

##### Market Trend Detection
```python
# Determine current market trend
trend = strategy.get_market_trend(market_data)
print(f"Market trend: {trend}")  # BULLISH, BEARISH, or SIDEWAYS
```

##### Signal Tracking Reset
```python
# Reset signal tracking (useful for testing)
strategy.reset_signal_tracking()
```

#### Advantages
- ✅ **Simple and reliable**: Easy to understand and implement
- ✅ **Trend-following**: Captures medium to long-term trends
- ✅ **Low computational cost**: Efficient calculation
- ✅ **Widely tested**: Proven strategy in traditional markets
- ✅ **Debouncing protection**: Prevents signal flip-flopping
- ✅ **Overfitting warnings**: Built-in protection against poor parameters
- ✅ **Signal strength analysis**: Additional insights for decision making

#### Disadvantages
- ❌ **Lagging indicator**: Signals come after trend changes
- ❌ **False signals**: Can generate signals in sideways markets
- ❌ **Not suitable for volatile markets**: May miss quick reversals

#### Best Use Cases
- **Trending markets**: Works best when prices are moving in clear trends
- **Medium-term trading**: 1-hour to daily timeframes
- **Less volatile cryptocurrencies**: Bitcoin, Ethereum during stable periods
- **Conservative trading**: When you want to avoid excessive signals

#### Risk Management
- **Stop Loss**: Recommended 5-10% below entry price
- **Take Profit**: 2:1 or 3:1 risk-reward ratio
- **Position Sizing**: 1-2% of portfolio per trade
- **Cooldown Period**: Use longer cooldowns (300+ seconds) for conservative trading
- **Minimum Data**: Ensure at least 50-100 data points before trading

#### Parameter Recommendations

##### Conservative Settings
```python
strategy = SmaCrossStrategy(
    short_window=10,
    long_window=30,
    cooldown_period=300,  # 5 minutes
    min_data_points=100
)
```

##### Aggressive Settings
```python
strategy = SmaCrossStrategy(
    short_window=5,
    long_window=15,
    cooldown_period=60,   # 1 minute
    min_data_points=30
)
```

##### Balanced Settings (Recommended)
```python
strategy = SmaCrossStrategy(
    short_window=7,
    long_window=21,
    cooldown_period=120,  # 2 minutes
    min_data_points=50
)
```

## Strategy Configuration

### Parameter Optimization
Each strategy can be optimized by adjusting its parameters:

```python
# Conservative settings (fewer signals, more reliable)
conservative_sma = SmaCrossStrategy(short_window=10, long_window=30)

# Aggressive settings (more signals, higher risk)
aggressive_sma = SmaCrossStrategy(short_window=3, long_window=7)
```

### Backtesting Parameters
Common parameter ranges for backtesting:

| Strategy | Parameter | Min | Max | Step |
|----------|-----------|-----|-----|------|
| SMA Cross | short_window | 2 | 20 | 1 |
| SMA Cross | long_window | 5 | 50 | 5 |

## Adding New Strategies

### Step 1: Create Strategy Class
Create a new file in `src/strategies/`:

```python
from typing import Optional, Dict, Any
from ..domain.strategy import TradingStrategy, MarketData

class MyCustomStrategy(TradingStrategy):
    def __init__(self, param1: float = 1.0, param2: int = 14):
        self.param1 = param1
        self.param2 = param2
    
    def generate_signal(self, market_data: MarketData) -> Optional[str]:
        # Your signal generation logic here
        if self._check_buy_condition(market_data):
            return "BUY"
        elif self._check_sell_condition(market_data):
            return "SELL"
        return None
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "param1": self.param1,
            "param2": self.param2
        }
```

### Step 2: Register Strategy
Add the strategy to the trading engine:

```python
from src.strategies.my_custom_strategy import MyCustomStrategy

strategy = MyCustomStrategy(param1=1.5, param2=20)
engine = TradingEngine(strategy=strategy, symbols=['ETHDKK'])
```

## Planned Strategies

### 1. RSI (Relative Strength Index) Strategy
- **Type**: Momentum oscillator
- **Signals**: Oversold/overbought conditions
- **Parameters**: Period (14), overbought threshold (70), oversold threshold (30)

### 2. MACD (Moving Average Convergence Divergence) Strategy
- **Type**: Trend and momentum indicator
- **Signals**: MACD line crosses signal line
- **Parameters**: Fast EMA (12), slow EMA (26), signal EMA (9)

### 3. Bollinger Bands Strategy
- **Type**: Volatility indicator
- **Signals**: Price touches upper/lower bands
- **Parameters**: Period (20), standard deviation multiplier (2)

### 4. Volume-Weighted Average Price (VWAP) Strategy
- **Type**: Volume-based indicator
- **Signals**: Price crosses above/below VWAP
- **Parameters**: Period (14)

## Strategy Performance Metrics

### Key Performance Indicators (KPIs)
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Total Return**: Overall portfolio performance

### Risk Metrics
- **Value at Risk (VaR)**: Maximum expected loss
- **Maximum Consecutive Losses**: Longest losing streak
- **Average Trade Duration**: Time between entry and exit

## Best Practices

### 1. Strategy Selection
- **Market Conditions**: Choose strategies based on current market volatility
- **Time Horizon**: Match strategy timeframe to your trading goals
- **Risk Tolerance**: Consider your risk appetite when selecting parameters

### 2. Parameter Optimization
- **Walk-Forward Analysis**: Test parameters on out-of-sample data
- **Cross-Validation**: Use multiple time periods for validation
- **Overfitting Prevention**: Avoid over-optimizing on historical data

### 3. Risk Management
- **Position Sizing**: Never risk more than 1-2% per trade
- **Stop Losses**: Always use stop losses to limit downside
- **Diversification**: Use multiple strategies or assets

### 4. Monitoring and Maintenance
- **Regular Review**: Monitor strategy performance monthly
- **Parameter Updates**: Adjust parameters based on market changes
- **Strategy Rotation**: Switch strategies based on market conditions

## Integration with Firi Exchange

The strategies are designed to work seamlessly with the Firi trading platform:

```python
from src.exchange.firi_exchange import FiriExchange
from src.strategies.sma_cross import SmaCrossStrategy

# Initialize exchange and strategy
exchange = FiriExchange(api_key, client_id, secret)
strategy = SmaCrossStrategy(short_window=5, long_window=20)

# Get market data from Firi
market_data = exchange.get_historical_data('ETHDKK', interval='1h', limit=50)

# Generate trading signal
signal = strategy.generate_signal(market_data)

if signal == "BUY":
    # Execute buy order on Firi
    exchange.place_order('ETHDKK', 'bid', price, amount)
```

## Conclusion

The trading bot provides a robust framework for implementing and testing various trading strategies. The current SMA Cross strategy offers a solid foundation for trend-following trading, while the modular architecture allows for easy expansion with additional strategies.

For optimal results, combine multiple strategies, implement proper risk management, and continuously monitor and adjust your approach based on market conditions and performance metrics. 