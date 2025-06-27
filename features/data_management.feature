Feature: Data Management and Persistence
  As a trader
  I want the bot to manage data efficiently and persistently
  So that I can track performance and maintain historical records

  Background:
    Given the trading bot is initialized with data persistence enabled
    And the database connection is established
    And data retention policy is set to 2 years

  Scenario: Store trade execution data
    Given a BUY signal is generated at $50,000
    And the trade is executed successfully
    When the bot saves the trade data
    Then the trade should be stored with:
      | Field | Value |
      | symbol | BTC |
      | action | BUY |
      | price | 50000.0 |
      | amount | 0.1 |
      | timestamp | current_time |
      | strategy | SMA_CROSS |
      | status | EXECUTED |

  Scenario: Store market data for analysis
    Given the bot fetches price data every minute
    When new market data arrives
    Then the data should be stored with:
      | Field | Value |
      | symbol | BTC |
      | price | current_price |
      | volume | 24h_volume |
      | timestamp | current_time |
      | source | COINGECKO |

  Scenario: Retrieve historical trade data
    Given I have executed 50 trades in the last month
    When I query the trade history
    Then I should see all trades with pagination
    And be able to filter by date range
    And be able to filter by strategy type

  Scenario: Calculate performance metrics
    Given I have 100 completed trades
    When I request performance analytics
    Then I should see:
      | Metric | Description |
      | total_trades | 100 |
      | win_rate | calculated_percentage |
      | avg_profit | calculated_amount |
      | max_drawdown | calculated_percentage |
      | sharpe_ratio | calculated_ratio |

  Scenario: Data backup and recovery
    Given the database contains 1 year of trading data
    When I initiate a backup
    Then all data should be backed up to secure storage
    And the backup should be encrypted
    And I should be able to restore from backup

  Scenario: Data archival for old records
    Given I have 3 years of trading data
    And the retention policy is 2 years
    When the archival process runs
    Then data older than 2 years should be archived
    And current data should remain accessible
    And archived data should be compressed

  Scenario: Real-time data streaming
    Given the bot is connected to a WebSocket feed
    When price updates arrive in real-time
    Then the data should be processed immediately
    And stored in the database
    And trigger signal generation if needed

  Scenario: Data validation and cleaning
    Given market data contains some anomalies
    When the bot processes the data
    Then outliers should be identified and flagged
    And missing data should be interpolated
    And data quality metrics should be logged

  Scenario: Multi-source data aggregation
    Given I have data from CoinGecko and Binance APIs
    When the bot aggregates the data
    Then it should combine data from multiple sources
    And resolve any conflicts using priority rules
    And store the aggregated result

  Scenario: Data export for external analysis
    Given I want to analyze my trading data in Excel
    When I request a data export
    Then the bot should export data in CSV format
    And include all relevant fields
    And apply proper formatting

  Scenario: Data privacy and security
    Given the database contains sensitive trading information
    When data is accessed or transmitted
    Then all data should be encrypted at rest
    And all connections should use TLS
    And access should be logged and audited

  Scenario: Data retention compliance
    Given regulatory requirements specify 7-year retention
    When the retention policy is updated
    Then data should be retained for the required period
    And deletion should be logged
    And compliance reports should be generated

  Scenario: Data synchronization across instances
    Given I have multiple bot instances running
    When data is updated on one instance
    Then the changes should be synchronized to other instances
    And conflicts should be resolved using timestamps
    And consistency should be maintained

  Scenario: Data compression and optimization
    Given the database has grown to 10GB
    When optimization is performed
    Then old data should be compressed
    And indexes should be optimized
    And query performance should improve

  Scenario: Data migration between versions
    Given I'm upgrading from version 1.0 to 2.0
    When the migration process runs
    Then all existing data should be preserved
    And new schema should be applied
    And data integrity should be verified 