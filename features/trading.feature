Feature: Trading Bot Signal Generation
  As a trader
  I want the bot to generate accurate trading signals
  So that I can make profitable trading decisions

  Background:
    Given the trading bot is initialized with SMA Cross strategy
    And the short window is set to 5 periods
    And the long window is set to 20 periods

  Scenario: Generate BUY signal on bullish crossover
    Given I have historical price data showing an upward trend
    When the short-term SMA crosses above the long-term SMA
    Then the bot should generate a "BUY" signal
    And the signal should be logged with timestamp and price

  Scenario: Generate SELL signal on bearish crossover
    Given I have historical price data showing a downward trend
    When the short-term SMA crosses below the long-term SMA
    Then the bot should generate a "SELL" signal
    And the signal should be logged with timestamp and price

  Scenario: No signal when SMAs are parallel
    Given I have historical price data showing sideways movement
    When the short-term and long-term SMAs move in parallel
    Then the bot should generate no signal
    And the status should show "—" for current signal

  Scenario: Handle insufficient data gracefully
    Given I have less than 20 price data points
    When the bot tries to generate a signal
    Then the bot should return no signal
    And log that insufficient data is available

  Scenario: Continuous monitoring with real-time data
    Given the bot is running with 60-second intervals
    When new market data arrives
    Then the bot should update its price history
    And check for new signals
    And log the current price and signal status

  @error_handling
  Scenario: Handle API rate limiting gracefully
    Given the CoinGecko API is rate limited
    When the bot tries to fetch market data
    Then the bot should wait and retry
    And continue operation without crashing

  @error_handling
  Scenario: Handle network connectivity issues
    Given there is no internet connection
    When the bot tries to fetch market data
    Then the bot should log the error
    And use cached data if available
    And continue monitoring

  @performance
  Scenario: Monitor strategy performance over time
    Given the bot has been running for 24 hours
    When I check the performance metrics
    Then I should see the total number of signals generated
    And the win/loss ratio of trades
    And the average time between signals

  @data_management
  Scenario: Persist trading data to storage
    Given a trade signal is generated
    When the bot processes the signal
    Then the trade should be saved to the database
    And include timestamp, price, and signal type

  @strategy_management
  Scenario: Switch between different trading strategies
    Given the bot is running with SMA Cross strategy
    When I switch to RSI strategy
    Then the bot should use the new strategy
    And generate signals based on RSI indicators

  @risk_management
  Scenario: Implement stop-loss protection
    Given I have an open BUY position
    When the price drops by 5%
    Then the bot should automatically close the position
    And log the stop-loss execution

  @risk_management
  Scenario: Implement take-profit targets
    Given I have an open BUY position
    When the price increases by 10%
    Then the bot should automatically close the position
    And log the take-profit execution

  @market_conditions
  Scenario: Handle high volatility periods
    Given the market is experiencing high volatility
    When price movements exceed normal ranges
    Then the bot should adjust signal sensitivity
    And potentially pause trading if volatility is extreme

  @market_conditions
  Scenario: Handle low liquidity conditions
    Given the market has low trading volume
    When the bot generates a signal
    Then the bot should check liquidity before executing
    And potentially delay execution if liquidity is insufficient

  @configuration
  Scenario: Load configuration from environment variables
    Given environment variables are set for API keys and settings
    When the bot starts up
    Then it should load the configuration automatically
    And validate all required settings

  @configuration
  Scenario: Validate strategy parameters
    Given I try to set invalid SMA parameters
    When the bot initializes the strategy
    Then it should raise a validation error
    And provide helpful error messages

  @logging
  Scenario: Comprehensive logging of all activities
    Given the bot is running
    When various events occur (data fetch, signal generation, errors)
    Then all events should be logged with appropriate levels
    And include relevant context and timestamps

  @monitoring
  Scenario: Health check and system monitoring
    Given the bot has been running for several hours
    When I check the system health
    Then I should see memory usage statistics
    And API response times
    And error rates
    And overall system status 