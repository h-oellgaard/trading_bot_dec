Feature: SMA Strategy Parameters and Initialization
  As a trader
  I want to configure SMA strategy parameters safely
  So that I avoid overfitting and get reliable signals

  Background:
    Given the trading bot framework is initialized
    And the logger is configured to capture messages

  @overfitting_protection
  Scenario: Critical warning for very small window sizes
    Given I try to initialize SMA strategy with short_window=2 and long_window=3
    When the strategy is created
    Then I should see a critical warning message
    And the warning should contain "CRITICAL: Very small window sizes detected!"
    And the warning should recommend "short_window=7, long_window=21"
    And the strategy should still initialize successfully

  @overfitting_protection
  Scenario: Warning for small window sizes
    Given I try to initialize SMA strategy with short_window=3 and long_window=8
    When the strategy is created
    Then I should see a warning message
    And the warning should contain "WARNING: Small window sizes may lead to overfitting"
    And the warning should suggest "short >= 7, long >= 21"
    And the strategy should initialize successfully

  @overfitting_protection
  Scenario: No warnings for recommended window sizes
    Given I initialize SMA strategy with short_window=7 and long_window=21
    When the strategy is created
    Then I should see no overfitting warnings
    And the strategy should initialize successfully
    And the parameters should be set correctly

  @validation
  Scenario: Reject invalid window size configuration
    Given I try to set short_window=10 and long_window=5
    When I initialize the strategy
    Then a ValueError should be raised
    And the error message should contain "Short window must be smaller than long window"

  @validation
  Scenario: Accept valid window size configuration
    Given I set short_window=5 and long_window=20
    When I initialize the strategy
    Then no ValueError should be raised
    And the strategy should initialize successfully

  @parameter_configuration
  Scenario: Conservative parameter settings
    Given I initialize SMA strategy with conservative settings
    And short_window=10 and long_window=30
    And cooldown_period=300 and min_data_points=100
    When the strategy is created
    Then it should initialize without warnings
    And the short_window should be 10
    And the long_window should be 30
    And the cooldown_period should be 300
    And the min_data_points should be 100

  @parameter_configuration
  Scenario: Aggressive parameter settings
    Given I initialize SMA strategy with aggressive settings
    And short_window=5 and long_window=15
    And cooldown_period=60 and min_data_points=30
    When the strategy is created
    Then it should show a warning about small windows
    And the parameters should be set correctly
    And the strategy should still initialize successfully

  @parameter_configuration
  Scenario: Balanced parameter settings (recommended)
    Given I initialize SMA strategy with balanced settings
    And short_window=7 and long_window=21
    And cooldown_period=120 and min_data_points=50
    When the strategy is created
    Then it should initialize without warnings
    And use the recommended default values
    And the initialization should be logged

  @initialization
  Scenario: Default parameter initialization
    Given I initialize SMA strategy without parameters
    When the strategy is created
    Then the short_window should be 7
    And the long_window should be 21
    And the cooldown_period should be 60
    And the min_data_points should be 50
    And the initialization should be logged

  @initialization
  Scenario: Custom parameter initialization
    Given I initialize SMA strategy with custom parameters
    And short_window=12 and long_window=26
    And cooldown_period=180 and min_data_points=75
    When the strategy is created
    Then all custom parameters should be set correctly
    And the initialization should be logged with parameter values

  @edge_cases
  Scenario: Handle identical SMA values
    Given I have price data where short and long SMAs are identical
    When I call get_signal_strength
    Then the signal strength should be 0.0%
    And get_market_trend should return "SIDEWAYS"

  @edge_cases
  Scenario: Handle very close SMA values
    Given I have price data where SMAs differ by less than 0.1%
    When I call get_signal_strength
    Then the signal strength should be less than 0.1%
    And get_market_trend should return "SIDEWAYS"

  @performance
  Scenario: Fast initialization with large parameters
    Given I set very large window sizes (short=50, long=200)
    When I initialize the strategy
    Then the initialization should complete within 10ms
    And memory usage should remain reasonable 