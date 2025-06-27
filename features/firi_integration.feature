Feature: Firi Exchange Integration
  As a trader
  I want to integrate with the Firi trading platform
  So that I can access market data and execute trades

  Background:
    Given the Firi exchange is initialized with valid API credentials
    And the base URL is set to "https://api.firi.com"
    And sandbox mode is disabled

  @market_data
  Scenario: Retrieve available markets
    Given the Firi API is accessible
    When I request the list of available markets
    Then I should receive a list of markets
    And the response should include market symbols and prices
    And DKK markets should be available

  @market_data
  Scenario: Get current price for ETHDKK
    Given ETHDKK market exists
    When I request the current price for ETHDKK
    Then I should receive a valid price
    And the price should be greater than 0
    And the price should be in DKK

  @market_data
  Scenario: Get current price for BTCDKK
    Given BTCDKK market exists
    When I request the current price for BTCDKK
    Then I should receive a valid price
    And the price should be greater than 0
    And the price should be in DKK

  @market_data
  Scenario: Get order book for a market
    Given a valid market symbol exists
    When I request the order book
    Then I should receive bid and ask orders
    And the order book should have a depth of at least 1

  @market_data
  Scenario: Get historical market data
    Given a valid market symbol exists
    When I request historical data
    Then I should receive price history
    And the data should include timestamps
    And the data should be ordered chronologically

  @authentication
  Scenario: Successful API authentication
    Given valid API credentials are provided
    When I make an authenticated request
    Then the request should be successful
    And no authentication errors should occur

  @authentication
  Scenario: Handle invalid API credentials
    Given invalid API credentials are provided
    When I make an authenticated request
    Then the request should fail with 401 error
    And an appropriate error message should be returned

  @authentication
  Scenario: Handle missing API key
    Given no API key is provided
    When I make an authenticated request
    Then the request should fail with authentication error
    And the error should indicate "API key is missing"

  @error_handling
  Scenario: Handle 404 errors for non-existent endpoints
    Given I request a non-existent endpoint
    When the request is made
    Then the response should be 404 Not Found
    And the error should be handled gracefully
    And the application should continue running

  @error_handling
  Scenario: Handle network connectivity issues
    Given there is no internet connection
    When I try to fetch market data
    Then the request should fail gracefully
    And an appropriate error should be logged
    And the application should not crash

  @error_handling
  Scenario: Handle API rate limiting
    Given the API rate limit is exceeded
    When I make multiple requests
    Then the requests should be rate limited
    And the application should implement backoff
    And eventually succeed when rate limit resets

  @trading_permissions
  Scenario: Check trading permissions
    Given the API key has read-only permissions
    When I try to place a trade order
    Then the request should fail with 401 Unauthorized
    And the error should indicate insufficient permissions

  @trading_permissions
  Scenario: Place order with trading permissions
    Given the API key has trading permissions
    And I have sufficient balance
    When I place a buy order for ETHDKK
    Then the order should be placed successfully
    And an order ID should be returned
    And the order should be logged

  @trading_permissions
  Scenario: Cancel order
    Given I have an active order
    When I cancel the order
    Then the order should be cancelled successfully
    And the cancellation should be confirmed

  @account_management
  Scenario: Get account information
    Given account endpoints are available
    When I request account information
    Then I should receive account details
    And the response should include account ID and email

  @account_management
  Scenario: Get account balance
    Given balance endpoints are available
    When I request account balance
    Then I should receive balance information
    And the response should include available and total balances

  @data_validation
  Scenario: Validate market data format
    Given market data is received from Firi
    When I process the data
    Then the data should have the expected format
    And all required fields should be present
    And the data should be properly typed

  @data_validation
  Scenario: Handle malformed API responses
    Given the API returns malformed data
    When I try to process the response
    Then the error should be caught and logged
    And the application should continue running
    And a fallback should be used if available

  @performance
  Scenario: Efficient market data retrieval
    Given multiple markets need to be monitored
    When I fetch data for all markets
    Then the requests should complete within reasonable time
    And the data should be cached appropriately
    And memory usage should remain stable

  @performance
  Scenario: Handle large order books
    Given a market has a large order book
    When I request the full order book
    Then the request should complete successfully
    And the data should be processed efficiently
    And memory usage should be reasonable

  @integration
  Scenario: Integrate with trading strategy
    Given the Firi exchange is connected
    And a trading strategy is configured
    When the strategy generates a signal
    Then the signal should be sent to Firi
    And the order should be executed if permissions allow
    And the result should be logged

  @integration
  Scenario: Real-time market monitoring
    Given the bot is monitoring multiple markets
    When new market data arrives
    Then the data should be processed in real-time
    And signals should be generated if conditions are met
    And all activities should be logged

  @configuration
  Scenario: Load Firi configuration from file
    Given a valid configuration file exists
    When the application starts
    Then the Firi configuration should be loaded
    And the exchange should be initialized correctly
    And all required parameters should be validated

  @configuration
  Scenario: Handle missing configuration
    Given the configuration file is missing
    When the application starts
    Then an appropriate error should be shown
    And the application should exit gracefully
    And helpful instructions should be provided

  @logging
  Scenario: Comprehensive API logging
    Given API requests are being made
    When I check the logs
    Then all API calls should be logged
    And the logs should include request details
    And the logs should include response status
    And errors should be logged with context

  @monitoring
  Scenario: Monitor API health
    Given the Firi integration is running
    When I check the system health
    Then I should see API response times
    And I should see success/error rates
    And I should see connection status
    And I should see rate limit usage 