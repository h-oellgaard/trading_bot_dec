Feature: Trend-following strategy with crossovers and trailing stop
  As a crypto trader
  I want to trade based on SMA/EMA signals and protect gains with a trailing stop
  So that I can follow market trends while reducing downside risk

  Background:
    Given I start with $10,000 capital
    And I use SMA (5) as short-term and SMA (12) as long-term
    And I use EMA (5) as short-term for exit evaluation
    And I set a trailing stop loss of 5%
    And I split profit on sell: 40% tax, 45% reinvested, 15% withdrawn

  @buy_signal
  Scenario: Buy when short SMA crosses above long SMA
    Given SMA_short was below SMA_long yesterday
    And SMA_short is above SMA_long today
    And I have no open position
    When the crossover occurs
    Then I should BUY using all available capital
    And track the entry price and highest price since buy

  @sell_signal
  Scenario: Sell when short EMA is below long SMA for 3 candles
    Given I am in a position
    And EMA_short has been below SMA_long for 3 consecutive days
    When the condition is met
    Then I should SELL all holdings
    And split any profit into tax, reinvest, and withdrawal

  @trailing_stop
  Scenario: Trigger trailing stop loss if price drops 5% from high
    Given I am in a position
    And the price has dropped 5% below the highest price since buy
    When this drop occurs
    Then I should SELL all holdings
    And split any profit accordingly

  @no_trade
  Scenario: Do nothing if no conditions are met
    Given none of the crossover or trailing conditions are active
    When I evaluate the market
    Then I should hold my current position

  @profit_splitting
  Scenario: Correctly split profits on successful trades
    Given I am in a position with $1,000 profit
    When I sell the position
    Then I should pay $400 in tax
    And I should reinvest $450
    And I should withdraw $150

  @loss_handling
  Scenario: Handle losses without profit splitting
    Given I am in a position with $500 loss
    When I sell the position
    Then I should not pay any tax
    And I should not reinvest any amount
    And I should not withdraw any amount
    And all remaining capital should be available for trading

  @position_tracking
  Scenario: Track position details accurately
    Given I buy a position at $50,000
    And the price rises to $55,000
    And then drops to $52,000
    When I check my position status
    Then the entry price should be $50,000
    And the highest price should be $55,000
    And the trailing stop should be $52,250
    And the unrealized profit should be $2,000

  @ema_calculation
  Scenario: Calculate EMA correctly for exit signals
    Given I have price data for the last 10 periods
    When I calculate the 5-period EMA
    Then the EMA should be weighted more heavily toward recent prices
    And the EMA should be more responsive than SMA

  @multiple_signals
  Scenario: Handle multiple signal types in priority order
    Given I am in a position
    And both trailing stop and EMA exit conditions are met
    When I evaluate the market
    Then I should prioritize the trailing stop signal
    And execute the sell order immediately

  @capital_management
  Scenario: Manage capital allocation properly
    Given I have $10,000 available capital
    When I receive a buy signal
    Then I should use all $10,000 to buy
    And my available capital should be $0
    And my position size should be calculated correctly

  @performance_tracking
  Scenario: Track overall performance metrics
    Given I have completed 5 trades
    And I have $2,000 total profit
    When I request a performance summary
    Then the total return should be calculated correctly
    And the average profit per trade should be $400
    And the total number of trades should be 5 