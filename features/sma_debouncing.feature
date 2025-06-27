Feature: SMA Strategy Debouncing and Cooldown
  As a trader
  I want the SMA strategy to prevent signal flip-flopping
  So that I avoid excessive trading and reduce transaction costs

  Background:
    Given the SMA strategy is initialized with short_window=7 and long_window=21
    And the logger is configured to capture messages
    And the cooldown period is set to 120 seconds

  @debouncing
  Scenario: Prevent rapid signal changes during cooldown
    Given I generate a BUY signal at timestamp 1000
    And the cooldown period is 120 seconds
    When I try to generate another signal at timestamp 1100
    Then no new signal should be generated
    And the reason should be logged as "Signal suppressed during cooldown"
    And the remaining cooldown time should be logged

  @debouncing
  Scenario: Allow new signal after cooldown expires
    Given I generate a BUY signal at timestamp 1000
    And the cooldown period is 120 seconds
    When I try to generate a signal at timestamp 1300
    Then a new signal should be generated if conditions are met
    And the cooldown should be reset

  @debouncing
  Scenario: Different signal types reset cooldown
    Given I generate a BUY signal at timestamp 1000
    And the cooldown period is 120 seconds
    When I generate a SELL signal at timestamp 1300
    Then the SELL signal should be generated
    And the cooldown should be reset for the new signal type

  @debouncing
  Scenario: Same signal type during cooldown is suppressed
    Given I generate a BUY signal at timestamp 1000
    And the cooldown period is 120 seconds
    When I try to generate another BUY signal at timestamp 1100
    Then the second BUY signal should be suppressed
    And the suppression should be logged

  @cooldown_tracking
  Scenario: Track cooldown time accurately
    Given I generate a signal at timestamp 1000
    And the cooldown period is 120 seconds
    When I check cooldown status at timestamp 1150
    Then the remaining cooldown time should be 30 seconds
    And the cooldown status should be logged

  @cooldown_tracking
  Scenario: Cooldown expires exactly on time
    Given I generate a signal at timestamp 1000
    And the cooldown period is 120 seconds
    When I try to generate a signal at timestamp 1120
    Then a new signal should be generated
    And the cooldown should be considered expired

  @signal_suppression
  Scenario: Suppress weak signals during cooldown
    Given I generate a strong BUY signal at timestamp 1000
    And a weak BUY signal occurs at timestamp 1100
    When I process the weak signal during cooldown
    Then the weak signal should be suppressed
    And the reason should be "Signal suppressed during cooldown"

  @signal_suppression
  Scenario: Allow strong signals to override cooldown
    Given I generate a weak BUY signal at timestamp 1000
    And a very strong BUY signal occurs at timestamp 1100
    When I process the strong signal during cooldown
    Then the strong signal should override the cooldown
    And the override should be logged with justification

  @performance
  Scenario: Fast cooldown checking
    Given I have generated multiple signals
    When I check cooldown status
    Then the cooldown check should complete within 1ms
    And the performance should be logged

  @edge_cases
  Scenario: Handle zero cooldown period
    Given I set cooldown_period=0
    When I generate consecutive signals
    Then all signals should be generated without suppression
    And the zero cooldown should be logged

  @edge_cases
  Scenario: Handle very long cooldown period
    Given I set cooldown_period=3600
    When I generate a signal
    Then the cooldown should be set to 3600 seconds
    And the long cooldown should be logged as a warning

  @edge_cases
  Scenario: Handle negative timestamps
    Given I have a signal with timestamp -1000
    When I check cooldown status
    Then the cooldown calculation should handle negative time correctly
    And the edge case should be logged

  @integration
  Scenario: Cooldown with real market data
    Given I have real market price data
    And I generate a signal based on SMA crossover
    When I receive new price data within cooldown period
    Then the signal generation should respect cooldown
    And the market data should be logged 