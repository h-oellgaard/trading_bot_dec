Feature: Improved SMA Cross Strategy
  As a trader
  I want a robust SMA Cross strategy with debouncing and overfitting protection
  So that I can make reliable trading decisions without excessive noise

  Background:
    Given the trading bot is initialized with improved SMA Cross strategy
    And the short window is set to 7 periods
    And the long window is set to 21 periods
    And the cooldown period is set to 60 seconds
    And the minimum data points is set to 50

  @overfitting_protection
  Scenario: Warn about overfitting with small window sizes
    Given I try to initialize the strategy with short_window=2 and long_window=3
    When the strategy is created
    Then I should see a critical warning about very small window sizes
    And the warning should recommend short_window=7 and long_window=21

  @overfitting_protection
  Scenario: Warn about potential overfitting with small windows
    Given I try to initialize the strategy with short_window=3 and long_window=8
    When the strategy is created
    Then I should see a warning about small window sizes
    And the warning should suggest using larger windows

  @overfitting_protection
  Scenario: No warnings with recommended window sizes
    Given I initialize the strategy with short_window=7 and long_window=21
    When the strategy is created
    Then I should see no overfitting warnings
    And the strategy should initialize successfully

  @debouncing
  Scenario: Prevent signal flip-flopping with cooldown period
    Given the strategy generates a BUY signal
    When I immediately call generate_signal again
    Then the strategy should return no signal
    And log that cooldown is active
    And show remaining cooldown time

  @debouncing
  Scenario: Allow new signal after cooldown period expires
    Given the strategy generated a BUY signal 70 seconds ago
    When I call generate_signal
    Then the strategy should process the signal normally
    And not apply cooldown restrictions

  @signal_suppression
  Scenario: Suppress repeated identical signals
    Given the strategy generated a BUY signal
    When the same BUY condition occurs again
    Then the strategy should suppress the repeated signal
    And log that the signal was suppressed

  @signal_suppression
  Scenario: Allow different signal after previous signal
    Given the strategy generated a BUY signal
    When a SELL condition occurs
    Then the strategy should generate the SELL signal
    And not suppress it due to signal suppression

  @data_requirements
  Scenario: Require minimum data points for signal generation
    Given I have only 30 price data points
    When the strategy tries to generate a signal
    Then the strategy should return no signal
    And log that data is below minimum threshold

  @data_requirements
  Scenario: Generate signal with sufficient data points
    Given I have 100 price data points
    When the strategy tries to generate a signal
    Then the strategy should process the signal normally
    And not reject due to insufficient data

  @signal_strength
  Scenario: Calculate signal strength for close SMAs
    Given I have price data with close SMA values
    When I call get_signal_strength
    Then I should get a low signal strength percentage
    And the value should be less than 2%

  @signal_strength
  Scenario: Calculate signal strength for wide SMA separation
    Given I have price data with wide SMA separation
    When I call get_signal_strength
    Then I should get a high signal strength percentage
    And the value should be greater than 5%

  @market_trend
  Scenario: Detect bullish market trend
    Given I have price data showing an upward trend
    When I call get_market_trend
    Then the result should be "BULLISH"
    And the SMAs should be properly separated

  @market_trend
  Scenario: Detect bearish market trend
    Given I have price data showing a downward trend
    When I call get_market_trend
    Then the result should be "BEARISH"
    And the SMAs should be properly separated

  @market_trend
  Scenario: Detect sideways market trend
    Given I have price data showing sideways movement
    When I call get_market_trend
    Then the result should be "SIDEWAYS"
    And the SMA separation should be minimal

  @parameter_configuration
  Scenario: Conservative parameter settings
    Given I initialize the strategy with conservative settings
    And short_window=10 and long_window=30
    And cooldown_period=300 and min_data_points=100
    When the strategy is created
    Then it should initialize without warnings
    And the parameters should be set correctly

  @parameter_configuration
  Scenario: Aggressive parameter settings
    Given I initialize the strategy with aggressive settings
    And short_window=5 and long_window=15
    And cooldown_period=60 and min_data_points=30
    When the strategy is created
    Then it should show a warning about small windows
    But still initialize successfully

  @parameter_configuration
  Scenario: Balanced parameter settings
    Given I initialize the strategy with balanced settings
    And short_window=7 and long_window=21
    And cooldown_period=120 and min_data_points=50
    When the strategy is created
    Then it should initialize without warnings
    And use the recommended default values

  @signal_generation
  Scenario: Generate BUY signal on bullish crossover
    Given I have sufficient historical price data
    And the short-term SMA is about to cross above the long-term SMA
    When the crossover occurs
    Then the strategy should generate a "BUY" signal
    And log the signal with timestamp
    And update the last_signal tracking

  @signal_generation
  Scenario: Generate SELL signal on bearish crossover
    Given I have sufficient historical price data
    And the short-term SMA is about to cross below the long-term SMA
    When the crossover occurs
    Then the strategy should generate a "SELL" signal
    And log the signal with timestamp
    And update the last_signal tracking

  @signal_generation
  Scenario: No signal when no crossover occurs
    Given I have sufficient historical price data
    And the SMAs are moving in parallel
    When I call generate_signal
    Then the strategy should return no signal
    And not update the last_signal tracking

  @signal_tracking
  Scenario: Track signal parameters correctly
    Given the strategy has generated several signals
    When I call get_parameters
    Then I should see the current strategy parameters
    And the last_signal should be recorded
    And the last_signal_time should be recorded

  @signal_tracking
  Scenario: Reset signal tracking
    Given the strategy has generated signals
    When I call reset_signal_tracking
    Then the last_signal should be set to None
    And the last_signal_time should be set to None
    And a reset confirmation should be logged

  @error_handling
  Scenario: Handle invalid window size configuration
    Given I try to set short_window greater than long_window
    When I initialize the strategy
    Then it should raise a ValueError
    And provide a clear error message

  @error_handling
  Scenario: Handle insufficient data for trend detection
    Given I have less than the long_window data points
    When I call get_market_trend
    Then it should return "INSUFFICIENT_DATA"
    And not crash the application

  @performance
  Scenario: Efficient signal generation with large datasets
    Given I have 1000 price data points
    When I call generate_signal multiple times
    Then the response time should be under 100ms
    And memory usage should remain stable

  @integration
  Scenario: Integrate with trading engine
    Given the improved SMA strategy is configured
    And the trading engine is initialized
    When the engine processes market data
    Then the strategy should generate appropriate signals
    And the engine should handle the signals correctly
    And all debouncing logic should work as expected 