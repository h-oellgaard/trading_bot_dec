# 📈 Trend Following Strategy Documentation

## Overview

The **Trend Following Strategy** is a sophisticated trading algorithm that combines SMA/EMA crossovers with trailing stop loss protection and automated profit splitting. This strategy is designed to follow market trends while protecting gains and managing risk effectively.

## 🎯 Strategy Features

### Core Components
- **SMA Crossover Entry**: Uses Simple Moving Average crossovers for buy signals
- **EMA Exit Signal**: Uses Exponential Moving Average for exit timing
- **Trailing Stop Loss**: Protects profits by automatically selling on price drops
- **Profit Splitting**: Automatically divides profits into tax, reinvestment, and withdrawal
- **Position Tracking**: Comprehensive monitoring of entry prices, highest prices, and unrealized P&L
- **Capital Management**: Full capital utilization with proper position sizing

### Risk Management
- **Trailing Stop Protection**: Configurable percentage-based stop loss
- **Exit Signal Confirmation**: Requires multiple candles for exit confirmation
- **Capital Preservation**: All remaining value returned to capital on losses
- **Parameter Validation**: Comprehensive input validation to prevent errors

## 📊 Strategy Parameters

### Entry Parameters
- **SMA Short Window** (default: 5): Short-term moving average period
- **SMA Long Window** (default: 12): Long-term moving average period
- **Initial Capital** (default: $10,000): Starting trading capital

### Exit Parameters
- **EMA Short Window** (default: 5): EMA period for exit signals
- **Exit Candles** (default: 3): Number of candles EMA must be below SMA for exit
- **Trailing Stop Percentage** (default: 5%): Stop loss percentage from highest price

### Profit Management
- **Tax Percentage** (default: 40%): Portion of profit allocated to taxes
- **Reinvestment Percentage** (default: 45%): Portion of profit reinvested
- **Withdrawal Percentage** (default: 15%): Portion of profit withdrawn

## 🔄 Trading Logic

### Buy Signal Generation
1. **SMA Crossover Detection**: Short SMA crosses above long SMA
2. **Position Creation**: Uses all available capital to buy
3. **Entry Tracking**: Records entry price and initial highest price
4. **Capital Allocation**: All capital allocated to position

### Exit Signal Generation
1. **Trailing Stop Check**: Monitors price drops from highest point
2. **EMA Exit Signal**: EMA below SMA for specified number of candles
3. **Priority Handling**: Trailing stop takes priority over EMA exit
4. **Position Closure**: Sells entire position when exit conditions met

### Profit Splitting
1. **Profit Calculation**: Determines profit/loss on position closure
2. **Tax Allocation**: Calculates tax portion (only on profits)
3. **Reinvestment**: Adds reinvested portion back to available capital
4. **Withdrawal Tracking**: Records withdrawal amount for reporting

## 📈 Performance Tracking

### Key Metrics
- **Total Return**: Overall percentage return on initial capital
- **Total Profit**: Cumulative profit/loss from all trades
- **Total Trades**: Number of completed trades
- **Average Profit per Trade**: Mean profit/loss per trade
- **Win Rate**: Percentage of profitable trades (planned feature)

### Position Status
- **Entry Price**: Price at which position was opened
- **Current Price**: Latest market price
- **Highest Price**: Peak price reached since entry
- **Unrealized P&L**: Current profit/loss on open position
- **Trailing Stop Price**: Current stop loss level
- **Days in Position**: Duration of current position

## 🛠️ Usage Examples

### Basic Strategy Initialization
```python
from src.strategies.trend_following import TrendFollowingStrategy

# Default configuration
strategy = TrendFollowingStrategy()

# Custom configuration
strategy = TrendFollowingStrategy(
    sma_short=7,
    sma_long=21,
    ema_short=7,
    trailing_stop_percentage=3.0,
    exit_candles=2,
    initial_capital=50000
)
```

### Custom Profit Splitting
```python
from src.strategies.trend_following import TrendFollowingStrategy, ProfitSplit

# Custom profit split
profit_split = ProfitSplit(
    tax_percentage=30,
    reinvest_percentage=60,
    withdrawal_percentage=10
)

strategy = TrendFollowingStrategy(profit_split=profit_split)
```

### Signal Generation
```python
from src.domain.strategy import MarketData

# Create market data
market_data = MarketData(
    prices=[100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
    volume=[1000] * 11,
    timestamp=[datetime.now() - timedelta(minutes=i) for i in range(11)]
)

# Generate trading signal
signal = strategy.generate_signal(market_data)
print(f"Signal: {signal}")  # "BUY", "SELL", or None
```

### Performance Monitoring
```python
# Get current parameters
params = strategy.get_parameters()
print(f"Available Capital: ${params['available_capital']:,.2f}")
print(f"Total Profit: ${params['total_profit']:,.2f}")

# Get position status
position_status = strategy.get_position_status()
if position_status['status'] == 'IN_POSITION':
    print(f"Entry Price: ${position_status['entry_price']:,.2f}")
    print(f"Unrealized P&L: ${position_status['unrealized_pnl']:,.2f}")

# Get performance summary
performance = strategy.get_performance_summary()
print(f"Total Return: {performance['total_return_percentage']:.2f}%")
print(f"Average Profit per Trade: ${performance['average_profit_per_trade']:,.2f}")
```

## ⚙️ Configuration Options

### Conservative Settings
```python
strategy = TrendFollowingStrategy(
    sma_short=10,
    sma_long=30,
    ema_short=10,
    trailing_stop_percentage=3.0,
    exit_candles=5,
    initial_capital=10000
)
```

### Aggressive Settings
```python
strategy = TrendFollowingStrategy(
    sma_short=3,
    sma_long=7,
    ema_short=3,
    trailing_stop_percentage=7.0,
    exit_candles=1,
    initial_capital=10000
)
```

### Balanced Settings (Recommended)
```python
strategy = TrendFollowingStrategy(
    sma_short=7,
    sma_long=21,
    ema_short=7,
    trailing_stop_percentage=5.0,
    exit_candles=3,
    initial_capital=10000
)
```

## 🧪 Testing

### Unit Tests
Run the comprehensive test suite:
```bash
python test_trend_following_strategy.py
```

### BDD Tests
Run behavior-driven tests:
```bash
behave features/trend_following_strategy.feature
```

### Test Coverage
The strategy includes tests for:
- Strategy initialization and parameter validation
- Buy signal generation with SMA crossovers
- Trailing stop functionality
- Profit splitting calculations
- EMA exit signals
- Performance tracking
- Error handling and edge cases

## 📋 Best Practices

### Parameter Selection
1. **SMA Windows**: Use longer windows for more stable signals
2. **Trailing Stop**: Balance between profit protection and premature exits
3. **Exit Candles**: Higher values reduce false exits but increase risk
4. **Profit Split**: Consider tax implications and reinvestment goals

### Risk Management
1. **Start Small**: Begin with smaller capital amounts
2. **Monitor Performance**: Regularly review strategy performance
3. **Adjust Parameters**: Fine-tune based on market conditions
4. **Diversify**: Consider using multiple strategies or assets

### Market Conditions
1. **Trending Markets**: Strategy performs best in trending conditions
2. **Sideways Markets**: May generate false signals
3. **Volatile Markets**: Trailing stop helps protect against volatility
4. **Low Liquidity**: Consider impact on execution prices

## 🔧 Integration

### Trading Engine Integration
```python
from src.engine import TradingEngine
from src.strategies.trend_following import TrendFollowingStrategy

# Create strategy
strategy = TrendFollowingStrategy()

# Initialize trading engine
engine = TradingEngine(
    strategy=strategy,
    symbols=['BTC', 'ETH'],
    interval=60
)

# Start trading
engine.start()
```

### Data Manager Integration
```python
from src.data_manager import DataManager

# Initialize data manager
data_manager = DataManager()

# Get market data for strategy
market_data = data_manager.get_market_data('BTC', 50)

# Generate signal
signal = strategy.generate_signal(market_data)
```

## 🚨 Important Notes

### Limitations
- **Market Dependency**: Performance varies with market conditions
- **Parameter Sensitivity**: Results sensitive to parameter selection
- **Execution Risk**: Real-world execution may differ from backtests
- **Tax Considerations**: Consult tax advisor for proper tax treatment

### Warnings
- **Overfitting Risk**: Avoid optimizing parameters on limited data
- **Capital Risk**: Only trade with capital you can afford to lose
- **Market Risk**: Cryptocurrency markets are highly volatile
- **Technical Risk**: Ensure proper testing before live trading

### Recommendations
- **Paper Trading**: Test strategy thoroughly before live implementation
- **Regular Review**: Monitor and adjust strategy parameters regularly
- **Risk Management**: Always use proper position sizing and stop losses
- **Documentation**: Keep detailed records of all trades and decisions

## 📞 Support

For questions or issues with the Trend Following Strategy:
1. Review the test files for usage examples
2. Check the BDD feature files for behavior specifications
3. Examine the source code for implementation details
4. Run the test suite to verify functionality

---

*This strategy is designed for educational and research purposes. Always conduct thorough testing and consider professional advice before implementing in live trading environments.*
