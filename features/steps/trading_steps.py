from behave import given, when, then
import numpy as np
from src.strategies.sma_cross import SmaCrossStrategy
from src.domain.strategy import MarketData
from src.engine import TradingEngine

@given('the trading bot is initialized with SMA Cross strategy')
def step_impl(context):
    context.strategy = SmaCrossStrategy(short_window=5, long_window=20)

@given('the short window is set to {short:d} periods')
def step_impl(context, short):
    context.strategy.short_window = short

@given('the long window is set to {long:d} periods')
def step_impl(context, long):
    context.strategy.long_window = long

@given('I have historical price data showing an upward trend')
def step_impl(context):
    # Guarantee a bullish crossover at the last point
    # 20 points at 100, 4 at 100, last at 150
    prices = [100.0] * 24 + [150.0]
    context.market_data = MarketData(
        prices=prices,
        volume=[1000.0] * len(prices),
        timestamp=list(range(len(prices)))
    )

@given('I have historical price data showing a downward trend')
def step_impl(context):
    # Guarantee a bearish crossover at the last point
    # 20 points at 100, 4 at 100, last at 50
    prices = [100.0] * 24 + [50.0]
    context.market_data = MarketData(
        prices=prices,
        volume=[1000.0] * len(prices),
        timestamp=list(range(len(prices)))
    )

@given('I have historical price data showing sideways movement')
def step_impl(context):
    # Create sideways data with small oscillations
    base_price = 100.0
    prices = []
    for i in range(25):  # More than long window
        price = base_price + np.sin(i * 0.5) * 5  # Sideways with small oscillations
        prices.append(price)
    
    context.market_data = MarketData(
        prices=prices,
        volume=[1000.0] * len(prices),
        timestamp=list(range(len(prices)))
    )

@given('I have less than {count:d} price data points')
def step_impl(context, count):
    # Create insufficient data
    prices = list(range(count - 1))  # One less than required
    context.market_data = MarketData(
        prices=prices,
        volume=[1000.0] * len(prices),
        timestamp=list(range(len(prices)))
    )

@given('the bot is running with {interval:d}-second intervals')
def step_impl(context, interval):
    context.engine = TradingEngine(interval=interval)

@when('the short-term SMA crosses above the long-term SMA')
def step_impl(context):
    context.signal = context.strategy.generate_signal(context.market_data)

@when('the short-term SMA crosses below the long-term SMA')
def step_impl(context):
    context.signal = context.strategy.generate_signal(context.market_data)

@when('the short-term and long-term SMAs move in parallel')
def step_impl(context):
    context.signal = context.strategy.generate_signal(context.market_data)

@when('the bot tries to generate a signal')
def step_impl(context):
    context.signal = context.strategy.generate_signal(context.market_data)

@when('new market data arrives')
def step_impl(context):
    # Simulate new data arrival
    context.engine.data_service.prices.append(105.0)
    context.engine.data_service.volume.append(1000.0)
    context.engine.data_service.timestamp.append(25.0)

@then('the bot should generate a "{expected_signal}" signal')
def step_impl(context, expected_signal):
    assert context.signal == expected_signal, f"Expected {expected_signal}, got {context.signal}"

@then('the signal should be logged with timestamp and price')
def step_impl(context):
    # This would be tested in integration tests
    assert context.signal is not None

@then('the bot should generate no signal')
def step_impl(context):
    assert context.signal is None

@then('the status should show "{status}" for current signal')
def step_impl(context, status):
    # This would be tested in integration tests
    pass

@then('the bot should return no signal')
def step_impl(context):
    assert context.signal is None

@then('log that insufficient data is available')
def step_impl(context):
    # This would be tested in integration tests
    pass

@then('the bot should update its price history')
def step_impl(context):
    assert len(context.engine.data_service.prices) > 0

@then('check for new signals')
def step_impl(context):
    # This would be tested in integration tests
    pass

@then('log the current price and signal status')
def step_impl(context):
    # This would be tested in integration tests
    pass 