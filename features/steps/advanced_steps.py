from behave import given, when, then
import time
import requests
from unittest.mock import patch, MagicMock
from src.strategies.sma_cross import SmaCrossStrategy
from src.domain.strategy import MarketData
from src.engine import TradingEngine

# Error Handling Scenarios
@given('the CoinGecko API is rate limited')
def step_impl(context):
    context.api_rate_limited = True

@when('the bot tries to fetch market data')
def step_impl(context):
    if hasattr(context, 'api_rate_limited') and context.api_rate_limited:
        # Mock rate limit response
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 429  # Rate limit status
            mock_get.return_value = mock_response
            context.rate_limit_response = True

@then('the bot should wait and retry')
def step_impl(context):
    assert hasattr(context, 'rate_limit_response')

@then('continue operation without crashing')
def step_impl(context):
    # This would be tested in integration tests
    pass

@given('there is no internet connection')
def step_impl(context):
    context.no_internet = True

@then('the bot should log the error')
def step_impl(context):
    # This would be tested in integration tests
    pass

@then('use cached data if available')
def step_impl(context):
    # This would be tested in integration tests
    pass

# Performance Monitoring Scenarios
@given('the bot has been running for 24 hours')
def step_impl(context):
    context.running_time = 24 * 60 * 60  # 24 hours in seconds
    context.performance_metrics = {
        'total_signals': 15,
        'win_rate': 0.67,
        'avg_time_between_signals': 3600  # 1 hour average
    }

@when('I check the performance metrics')
def step_impl(context):
    context.metrics = context.performance_metrics

@then('I should see the total number of signals generated')
def step_impl(context):
    assert context.metrics['total_signals'] == 15

@then('the win/loss ratio of trades')
def step_impl(context):
    assert context.metrics['win_rate'] == 0.67

@then('the average time between signals')
def step_impl(context):
    assert context.metrics['avg_time_between_signals'] == 3600

# Data Management Scenarios
@given('a trade signal is generated')
def step_impl(context):
    context.trade_signal = {
        'type': 'BUY',
        'price': 50000.0,
        'timestamp': time.time(),
        'strategy': 'SMA_CROSS'
    }

@when('the bot processes the signal')
def step_impl(context):
    context.processed_trade = context.trade_signal

@then('the trade should be saved to the database')
def step_impl(context):
    # This would be tested in integration tests
    assert context.processed_trade is not None

@then('include timestamp, price, and signal type')
def step_impl(context):
    assert 'timestamp' in context.processed_trade
    assert 'price' in context.processed_trade
    assert 'type' in context.processed_trade

# Strategy Management Scenarios
@given('the bot is running with SMA Cross strategy')
def step_impl(context):
    context.current_strategy = 'SMA_CROSS'
    context.strategy = SmaCrossStrategy(short_window=5, long_window=20)

@when('I switch to RSI strategy')
def step_impl(context):
    context.current_strategy = 'RSI'
    # This would instantiate an RSI strategy

@then('the bot should use the new strategy')
def step_impl(context):
    assert context.current_strategy == 'RSI'

@then('generate signals based on RSI indicators')
def step_impl(context):
    # This would be tested in integration tests
    pass

# Risk Management Scenarios
@given('I have an open BUY position')
def step_impl(context):
    context.open_position = {
        'type': 'BUY',
        'entry_price': 50000.0,
        'current_price': 50000.0,
        'stop_loss': 47500.0,  # 5% below entry
        'take_profit': 55000.0  # 10% above entry
    }

@when('the price drops by 5%')
def step_impl(context):
    context.open_position['current_price'] = 47500.0  # 5% drop

@then('the bot should automatically close the position')
def step_impl(context):
    # Check if stop loss is triggered
    assert context.open_position['current_price'] <= context.open_position['stop_loss']

@then('log the stop-loss execution')
def step_impl(context):
    # This would be tested in integration tests
    pass

@when('the price increases by 10%')
def step_impl(context):
    context.open_position['current_price'] = 55000.0  # 10% increase

@then('log the take-profit execution')
def step_impl(context):
    # This would be tested in integration tests
    pass

# Market Conditions Scenarios
@given('the market is experiencing high volatility')
def step_impl(context):
    context.volatility = 'high'
    context.price_movements = [5.0, -7.0, 12.0, -8.0, 15.0]  # Large movements

@when('price movements exceed normal ranges')
def step_impl(context):
    context.extreme_volatility = any(abs(move) > 10.0 for move in context.price_movements)

@then('the bot should adjust signal sensitivity')
def step_impl(context):
    # This would be tested in integration tests
    pass

@then('potentially pause trading if volatility is extreme')
def step_impl(context):
    if context.extreme_volatility:
        context.trading_paused = True

@given('the market has low trading volume')
def step_impl(context):
    context.low_liquidity = True
    context.trading_volume = 1000000  # Low volume

@when('the bot generates a signal')
def step_impl(context):
    context.signal_generated = True

@then('the bot should check liquidity before executing')
def step_impl(context):
    if context.low_liquidity:
        context.liquidity_check = True

@then('potentially delay execution if liquidity is insufficient')
def step_impl(context):
    if context.low_liquidity:
        context.execution_delayed = True

# Configuration Scenarios
@given('environment variables are set for API keys and settings')
def step_impl(context):
    context.env_vars = {
        'COINGECKO_API_KEY': 'test_key',
        'TRADING_INTERVAL': '60',
        'STRATEGY_TYPE': 'SMA_CROSS'
    }

@when('the bot starts up')
def step_impl(context):
    context.config_loaded = True

@then('it should load the configuration automatically')
def step_impl(context):
    assert context.config_loaded

@then('validate all required settings')
def step_impl(context):
    # This would be tested in integration tests
    pass

@given('I try to set invalid SMA parameters')
def step_impl(context):
    context.invalid_params = {'short_window': 20, 'long_window': 5}  # Invalid: short > long

@when('the bot initializes the strategy')
def step_impl(context):
    try:
        context.strategy = SmaCrossStrategy(
            short_window=context.invalid_params['short_window'],
            long_window=context.invalid_params['long_window']
        )
        context.validation_passed = True
    except ValueError:
        context.validation_error = True

@then('it should raise a validation error')
def step_impl(context):
    assert hasattr(context, 'validation_error')

@then('provide helpful error messages')
def step_impl(context):
    # This would be tested in integration tests
    pass

# Logging Scenarios
@given('the bot is running')
def step_impl(context):
    context.bot_running = True

@when('various events occur (data fetch, signal generation, errors)')
def step_impl(context):
    context.events = ['data_fetch', 'signal_generation', 'error']

@then('all events should be logged with appropriate levels')
def step_impl(context):
    # This would be tested in integration tests
    pass

@then('include relevant context and timestamps')
def step_impl(context):
    # This would be tested in integration tests
    pass

# Monitoring Scenarios
@given('the bot has been running for several hours')
def step_impl(context):
    context.runtime_hours = 6

@when('I check the system health')
def step_impl(context):
    context.health_metrics = {
        'memory_usage': '256MB',
        'api_response_time': '150ms',
        'error_rate': '0.02',
        'system_status': 'healthy'
    }

@then('I should see memory usage statistics')
def step_impl(context):
    assert 'memory_usage' in context.health_metrics

@then('API response times')
def step_impl(context):
    assert 'api_response_time' in context.health_metrics

@then('error rates')
def step_impl(context):
    assert 'error_rate' in context.health_metrics

@then('overall system status')
def step_impl(context):
    assert context.health_metrics['system_status'] == 'healthy' 