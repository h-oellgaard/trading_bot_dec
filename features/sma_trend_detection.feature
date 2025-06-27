Feature: SMA Strategy Trend Detection
  As a trader
  I want the SMA strategy to accurately detect market trends
  So that I can understand the overall market direction

  Background:
    Given the SMA strategy is initialized with short_window=7 and long_window=21
    And the logger is configured to capture messages

  @trend_detection
  Scenario: Detect strong bullish trend
    Given I have price data showing consistent upward movement
    And the short SMA is significantly above the long SMA
    And the trend has persisted for multiple periods
    When I call get_market_trend
    Then it should return "BULLISH"
    And the trend strength should be calculated
    And the trend analysis should be logged

  @trend_detection
  Scenario: Detect strong bearish trend
    Given I have price data showing consistent downward movement
    And the short SMA is significantly below the long SMA
    And the trend has persisted for multiple periods
    When I call get_market_trend
    Then it should return "BEARISH"
    And the trend strength should be calculated
    And the trend analysis should be logged

  @trend_detection
  Scenario: Detect sideways market
    Given I have price data showing no clear direction
    And the SMAs are close to each other
    And the price movement is minimal
    When I call get_market_trend
    Then it should return "SIDEWAYS"
    And the trend analysis should be logged

  @trend_strength
  Scenario: Calculate trend strength for bullish market
    Given I have price data with short SMA at 105 and long SMA at 100
    When I call get_trend_strength
    Then the trend strength should be 5.0%
    And the calculation should be logged

  @trend_strength
  Scenario: Calculate trend strength for bearish market
    Given I have price data with short SMA at 95 and long SMA at 100
    When I call get_trend_strength
    Then the trend strength should be -5.0%
    And the calculation should be logged

  @trend_strength
  Scenario: Zero trend strength for sideways market
    Given I have price data with both SMAs at 100
    When I call get_trend_strength
    Then the trend strength should be 0.0%
    And the calculation should be logged

  @trend_persistence
  Scenario: Detect trend persistence
    Given I have price data showing a trend for 10 consecutive periods
    When I call get_trend_persistence
    Then the trend should be considered persistent
    And the persistence count should be logged

  @trend_persistence
  Scenario: Detect trend reversal
    Given I have price data showing a trend reversal
    And the SMAs have crossed in the opposite direction
    When I call get_trend_persistence
    Then the trend should be considered reversed
    And the reversal should be logged

  @market_regime
  Scenario: Identify trending market regime
    Given I have price data showing clear directional movement
    And the trend has persisted for multiple periods
    When I call get_market_regime
    Then it should return "TRENDING"
    And the regime analysis should be logged

  @market_regime
  Scenario: Identify ranging market regime
    Given I have price data showing sideways movement
    And the price is bouncing between support and resistance
    When I call get_market_regime
    Then it should return "RANGING"
    And the regime analysis should be logged

  @market_regime
  Scenario: Identify volatile market regime
    Given I have price data showing high volatility
    And the SMAs are crossing frequently
    When I call get_market_regime
    Then it should return "VOLATILE"
    And the regime analysis should be logged

  @edge_cases
  Scenario: Handle flat market with no movement
    Given I have price data with constant price values
    When I call get_market_trend
    Then it should return "SIDEWAYS"
    And the flat market should be logged

  @edge_cases
  Scenario: Handle extreme price movements
    Given I have price data with sudden large price changes
    When I call get_market_trend
    Then the trend should be calculated correctly
    And the extreme movement should be logged
    And risk warnings should be included

  @edge_cases
  Scenario: Handle insufficient data for trend analysis
    Given I have less than the minimum required data points
    When I call get_market_trend
    Then it should return "UNKNOWN"
    And the insufficient data should be logged

  @performance
  Scenario: Fast trend detection
    Given I have 1000 data points of price history
    When I call get_market_trend
    Then the trend detection should complete within 10ms
    And the performance should be logged

  @integration
  Scenario: Trend detection with real market data
    Given I have real market price data
    When I analyze the trend over multiple timeframes
    Then the trend detection should be consistent
    And the analysis should be logged 