Feature: SMA Strategy Integration Tests
  As a trader
  I want the SMA strategy to work seamlessly with the trading system
  So that I can deploy it in production with confidence

  Background:
    Given the trading bot framework is initialized
    And the Firi exchange is configured
    And the logger is configured to capture messages

  @end_to_end
  Scenario: Complete trading cycle with SMA strategy
    Given I have real market data for ETHDKK
    And the SMA strategy is initialized with recommended parameters
    When I run a complete trading cycle
    Then the strategy should analyze the market data
    And generate appropriate signals based on SMA crossovers
    And log all analysis and decisions
    And the trading cycle should complete successfully

  @end_to_end
  Scenario: Multiple trading cycles with signal generation
    Given I have historical market data spanning multiple periods
    And the SMA strategy is configured with debouncing
    When I run multiple trading cycles
    Then signals should be generated when conditions are met
    And debouncing should prevent excessive trading
    And all cycles should complete without errors

  @integration
  Scenario: SMA strategy with Firi market data
    Given I fetch real-time market data from Firi
    And the SMA strategy is initialized
    When I process the Firi market data
    Then the strategy should handle the data format correctly
    And generate signals based on the market conditions
    And log the integration process

  @integration
  Scenario: SMA strategy with data persistence
    Given I have a configured data manager
    And the SMA strategy generates signals
    When I persist the trading data
    Then the signals should be stored correctly
    And the market data should be archived
    And the persistence should be logged

  @error_handling
  Scenario: Handle API errors gracefully
    Given the Firi API is experiencing issues
    And the SMA strategy is running
    When an API error occurs
    Then the strategy should continue operating
    And the error should be logged
    And the system should retry after a delay

  @error_handling
  Scenario: Handle insufficient market data
    Given I have limited market data available
    And the SMA strategy requires minimum data points
    When I try to generate signals
    Then the strategy should handle the insufficient data gracefully
    And log the data requirement issue
    And wait for more data before generating signals

  @performance
  Scenario: Strategy performance under load
    Given I have a large dataset of market data
    And the SMA strategy is processing multiple symbols
    When I run the strategy for an extended period
    Then the performance should remain acceptable
    And memory usage should be stable
    And the performance metrics should be logged

  @performance
  Scenario: Fast signal generation for real-time trading
    Given I have real-time market data streaming
    And the SMA strategy is configured for speed
    When I generate signals in real-time
    Then the signal generation should complete within 100ms
    And the latency should be logged
    And the real-time performance should be acceptable

  @configuration
  Scenario: Strategy configuration validation
    Given I have various configuration parameters
    When I validate the SMA strategy configuration
    Then all parameters should be validated correctly
    And invalid configurations should be rejected
    And the validation results should be logged

  @configuration
  Scenario: Dynamic parameter updates
    Given the SMA strategy is running with initial parameters
    When I update the strategy parameters dynamically
    Then the new parameters should be applied correctly
    And the strategy should continue operating
    And the parameter update should be logged

  @monitoring
  Scenario: Strategy health monitoring
    Given the SMA strategy is running continuously
    When I monitor the strategy health
    Then the health status should be reported
    And performance metrics should be collected
    And any issues should be logged

  @monitoring
  Scenario: Signal quality monitoring
    Given the SMA strategy is generating signals
    When I monitor signal quality
    Then signal accuracy should be tracked
    And false signals should be identified
    And the quality metrics should be logged

  @security
  Scenario: Secure API credential handling
    Given the SMA strategy uses API credentials
    When I initialize the strategy
    Then the credentials should be handled securely
    And no sensitive data should be logged
    And the security measures should be verified

  @security
  Scenario: Input data validation
    Given I receive market data from external sources
    When I validate the input data
    Then malicious or corrupted data should be rejected
    And the validation should be logged
    And the system should remain secure

  @recovery
  Scenario: Strategy recovery after failure
    Given the SMA strategy encounters an error
    When I attempt to recover the strategy
    Then the strategy should restart successfully
    And the recovery process should be logged
    And the system should resume normal operation

  @recovery
  Scenario: Data recovery after system restart
    Given the trading system is restarted
    And historical data is available
    When I restore the SMA strategy state
    Then the strategy should resume with correct state
    And the recovery should be logged
    And no data should be lost 