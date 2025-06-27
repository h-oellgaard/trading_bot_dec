Feature: SMA Strategy Signal Generation
  As a trader
  I want the SMA strategy to generate accurate trading signals
  So that I can make informed trading decisions

  Background:
    Given the SMA strategy is initialized with short_window=7 and long_window=21
    And the logger is configured to capture messages

  @signal_generation
  Scenario: Strong bullish signal generation
    Given I have price data showing a clear uptrend
    And the short SMA crosses above the long SMA
    When I call generate_signal
    Then a BUY signal should be generated
    And the signal strength should be greater than 2.0%
    And the market trend should be "BULLISH"

  @signal_generation
  Scenario: Strong bearish signal generation
    Given I have price data showing a clear downtrend
    And the short SMA crosses below the long SMA
    When I call generate_signal
    Then a SELL signal should be generated
    And the signal strength should be greater than 2.0%
    And the market trend should be "BEARISH"

  @signal_generation
  Scenario: Weak signal suppression
    Given I have price data with minimal SMA crossover
    And the price difference is less than 0.5%
    When I call generate_signal
    Then no signal should be generated
    And the reason should be logged as "Signal too weak"

  @noise_tolerance
  Scenario: Filter out noise from small price changes
    Given I have price data with frequent small fluctuations
    And the SMA crossover is less than 0.1%
    When I call generate_signal
    Then no signal should be generated
    And the reason should be "Signal below noise threshold"

  @edge_cases
  Scenario: Handle flat market with no price movement
    Given I have price data with constant price values
    When I call generate_signal
    Then no signal should be generated
    And the market trend should be "SIDEWAYS"

  @performance
  Scenario: Fast signal generation
    Given I have 1000 data points of price history
    When I call generate_signal
    Then the signal generation should complete within 50ms 