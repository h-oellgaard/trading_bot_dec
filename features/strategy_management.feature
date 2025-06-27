Feature: Strategy Management and Switching
  As a trader
  I want to manage and switch between different trading strategies
  So that I can adapt to changing market conditions and optimize performance

  Background:
    Given the trading bot is initialized with multiple strategies available
    And the current strategy is SMA Cross
    And strategy switching is enabled

  Scenario: Switch from SMA Cross to RSI strategy
    Given the current strategy is SMA Cross
    And RSI strategy is available and configured
    When I switch to RSI strategy
    Then the bot should stop using SMA Cross
    And start using RSI for signal generation
    And log the strategy change
    And preserve existing position data

  Scenario: Switch from RSI to MACD strategy
    Given the current strategy is RSI
    And MACD strategy is available and configured
    When I switch to MACD strategy
    Then the bot should stop using RSI
    And start using MACD for signal generation
    And log the strategy change
    And preserve existing position data

  Scenario: Enable multiple strategies simultaneously
    Given I have SMA Cross, RSI, and MACD strategies configured
    When I enable multi-strategy mode
    Then the bot should run all three strategies
    And generate signals from each strategy
    And combine signals using voting mechanism
    And log which strategy generated each signal

  Scenario: Strategy performance comparison
    Given I have been running multiple strategies for 30 days
    When I request strategy performance comparison
    Then I should see performance metrics for each strategy:
      | Strategy | Win Rate | Total Trades | Avg Profit |
      | SMA Cross | 65% | 45 | $120 |
      | RSI | 58% | 38 | $95 |
      | MACD | 72% | 52 | $150 |

  Scenario: Automatic strategy selection based on market conditions
    Given the market is trending upward
    And I have trend-following and mean-reversion strategies
    When the bot analyzes market conditions
    Then it should automatically select trend-following strategy
    And log the automatic selection reason

  Scenario: Strategy parameter optimization
    Given I want to optimize SMA Cross parameters
    And I have historical data for backtesting
    When I run parameter optimization
    Then the bot should test different parameter combinations
    And select the best performing parameters
    And apply the optimized parameters

  Scenario: Strategy backtesting
    Given I have 6 months of historical data
    And I want to test a new strategy
    When I run backtesting
    Then the bot should simulate trading with historical data
    And calculate performance metrics
    And generate a detailed backtest report

  Scenario: Strategy validation before live trading
    Given I have a new strategy ready for deployment
    When I validate the strategy
    Then the bot should check strategy parameters
    And verify data requirements
    And perform paper trading for 24 hours
    And only enable live trading if validation passes

  Scenario: Strategy-specific risk management
    Given I have different risk settings for each strategy
    When I switch between strategies
    Then the bot should apply strategy-specific risk parameters
    And adjust position sizes accordingly
    And update stop-loss and take-profit levels

  Scenario: Strategy market regime detection
    Given the market is in a high volatility regime
    And I have volatility-adjusted strategies
    When the bot detects the market regime
    Then it should automatically switch to volatility-adjusted strategy
    And log the regime detection and strategy change

  Scenario: Strategy correlation analysis
    Given I have multiple strategies running
    When I analyze strategy correlations
    Then the bot should identify highly correlated strategies
    And suggest strategy diversification
    And potentially disable redundant strategies

  Scenario: Strategy custom parameters
    Given I want to customize RSI strategy parameters
    When I set custom parameters
    Then the bot should validate the parameters
    And apply the custom settings
    And log the parameter changes

  Scenario: Strategy inheritance and composition
    Given I want to create a composite strategy
    When I combine multiple base strategies
    Then the bot should inherit properties from base strategies
    And allow custom signal combination logic
    And maintain proper logging and monitoring

  Scenario: Strategy hot-swapping without restart
    Given the bot is running with live positions
    When I hot-swap to a new strategy
    Then the bot should continue running without interruption
    And preserve all open positions
    And apply new strategy to future signals only

  Scenario: Strategy performance alerts
    Given a strategy has been underperforming for 7 days
    When the performance threshold is breached
    Then the bot should send an alert about poor performance
    And suggest alternative strategies
    And potentially pause the underperforming strategy

  Scenario: Strategy version control
    Given I have multiple versions of the same strategy
    When I deploy a new strategy version
    Then the bot should maintain version history
    And allow rollback to previous versions
    And track performance differences between versions

  Scenario: Strategy market hours adaptation
    Given different strategies perform better at different times
    When the market hours change
    Then the bot should automatically adjust strategy weights
    And optimize for current market conditions
    And log the time-based strategy adjustments 