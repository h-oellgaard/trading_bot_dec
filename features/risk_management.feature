Feature: Risk Management
  As a trader
  I want the bot to manage risk automatically
  So that I can protect my capital and maximize profits

  Background:
    Given the trading bot is initialized with risk management enabled
    And the maximum position size is set to 5% of portfolio
    And the maximum daily loss is set to 2% of portfolio

  Scenario: Position sizing based on portfolio percentage
    Given my portfolio value is $10,000
    And I want to open a BUY position
    When the bot calculates position size
    Then the position should not exceed $500 (5% of portfolio)
    And the position size should be logged

  Scenario: Daily loss limit protection
    Given I have open positions worth $8,000
    And my daily loss limit is 2% ($200)
    When my positions lose $250 in a day
    Then the bot should close all positions
    And stop trading for the remainder of the day
    And log the daily loss limit breach

  Scenario: Maximum drawdown protection
    Given my portfolio started at $10,000
    And the maximum drawdown is set to 15%
    When my portfolio value drops to $8,000 (20% loss)
    Then the bot should close all positions
    And stop trading until manual intervention
    And send an alert about the drawdown breach

  Scenario: Correlation-based position limits
    Given I have positions in BTC and ETH
    And the correlation limit is set to 0.8
    When the correlation between BTC and ETH exceeds 0.8
    Then the bot should reduce position sizes
    And close one of the correlated positions

  Scenario: Volatility-adjusted position sizing
    Given the market volatility is high (VIX > 30)
    And I want to open a new position
    When the bot calculates position size
    Then the position should be reduced by 50%
    And the volatility adjustment should be logged

  Scenario: Time-based position management
    Given I have an open position
    And the maximum holding time is 24 hours
    When the position has been open for 25 hours
    Then the bot should automatically close the position
    And log the time-based exit

  Scenario: News-based risk management
    Given there is breaking news about a major crypto exchange
    And the news sentiment is negative
    When the bot detects the news event
    Then it should reduce all position sizes by 75%
    And increase stop-loss sensitivity

  Scenario: Liquidity-based position sizing
    Given I want to trade a low-liquidity coin
    And the 24-hour volume is $100,000
    When the bot calculates position size
    Then the position should be limited to 1% of daily volume
    And the liquidity constraint should be logged

  Scenario: Multiple timeframe risk assessment
    Given I have positions based on 1-hour signals
    And the 4-hour trend is bearish
    When the bot performs risk assessment
    Then it should reduce position sizes
    And close positions against the higher timeframe trend

  Scenario: Portfolio heat map monitoring
    Given I have positions in multiple cryptocurrencies
    When the bot analyzes portfolio concentration
    Then it should identify over-concentration in any single asset
    And suggest position rebalancing if needed 