#!/usr/bin/env python3
"""
Test script to demonstrate the Trend Following Strategy features
"""

import sys
import os
import numpy as np
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.strategies.trend_following import TrendFollowingStrategy, ProfitSplit, Position
from src.domain.strategy import MarketData

def create_sample_market_data(prices, volumes=None, timestamps=None):
    """Create sample market data for testing"""
    if volumes is None:
        volumes = [1000.0] * len(prices)
    if timestamps is None:
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(len(prices)-1, -1, -1)]
    
    return MarketData(prices=prices, volume=volumes, timestamp=timestamps)

def test_strategy_initialization():
    """Test strategy initialization with different parameters"""
    print("🔍 Testing Strategy Initialization")
    print("=" * 50)
    
    # Test default initialization
    print("\n1. Default initialization:")
    strategy = TrendFollowingStrategy()
    params = strategy.get_parameters()
    print(f"   SMA Short: {params['sma_short']}")
    print(f"   SMA Long: {params['sma_long']}")
    print(f"   EMA Short: {params['ema_short']}")
    print(f"   Trailing Stop: {params['trailing_stop_percentage']}%")
    print(f"   Initial Capital: ${params['initial_capital']:,.2f}")
    
    # Test custom profit split
    print("\n2. Custom profit split:")
    custom_split = ProfitSplit(tax_percentage=30, reinvest_percentage=60, withdrawal_percentage=10)
    strategy_custom = TrendFollowingStrategy(profit_split=custom_split)
    params = strategy_custom.get_parameters()
    print(f"   Tax: {params['profit_split']['tax_percentage']}%")
    print(f"   Reinvest: {params['profit_split']['reinvest_percentage']}%")
    print(f"   Withdraw: {params['profit_split']['withdrawal_percentage']}%")
    
    return strategy

def test_buy_signal_generation():
    """Test buy signal generation with SMA crossover"""
    print("\n🔍 Testing Buy Signal Generation")
    print("=" * 50)
    
    strategy = TrendFollowingStrategy(sma_short=3, sma_long=5, initial_capital=10000)
    
    # Create data with SMA crossover
    # First 5 prices: SMA_short < SMA_long
    # Last 3 prices: SMA_short > SMA_long (crossover)
    prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
    market_data = create_sample_market_data(prices)
    
    print(f"\n1. Testing SMA crossover:")
    print(f"   Prices: {prices[-10:]}")  # Show last 10 prices
    
    # Calculate SMAs manually for verification
    sma_short = np.mean(prices[-3:])
    sma_long = np.mean(prices[-5:])
    sma_short_prev = np.mean(prices[-4:-1])
    sma_long_prev = np.mean(prices[-6:-1])
    
    print(f"   Current SMA(3): {sma_short:.2f}, SMA(5): {sma_long:.2f}")
    print(f"   Previous SMA(3): {sma_short_prev:.2f}, SMA(5): {sma_long_prev:.2f}")
    
    signal = strategy.generate_signal(market_data)
    print(f"   Generated signal: {signal}")
    
    if signal == "BUY":
        position_status = strategy.get_position_status()
        print(f"   Position created: {position_status}")
    
    return strategy

def test_trailing_stop_functionality():
    """Test trailing stop loss functionality"""
    print("\n🔍 Testing Trailing Stop Functionality")
    print("=" * 50)
    
    strategy = TrendFollowingStrategy(
        sma_short=3, 
        sma_long=5, 
        trailing_stop_percentage=5.0,
        initial_capital=10000
    )
    
    # First, create a position
    prices_buy = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
    market_data_buy = create_sample_market_data(prices_buy)
    buy_signal = strategy.generate_signal(market_data_buy)
    
    if buy_signal == "BUY":
        print(f"\n1. Position created at ${prices_buy[-1]:,.2f}")
        
        # Test price rising (should update highest price)
        prices_rising = [110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124]
        market_data_rising = create_sample_market_data(prices_rising)
        
        print(f"\n2. Price rising to ${prices_rising[-1]:,.2f}")
        signal = strategy.generate_signal(market_data_rising)
        print(f"   Signal: {signal}")
        
        position_status = strategy.get_position_status()
        print(f"   Highest price: ${strategy.current_position.highest_price:,.2f}")
        print(f"   Trailing stop: ${strategy.current_position.highest_price * 0.95:,.2f}")
        
        # Test trailing stop trigger
        prices_dropping = [120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106]
        market_data_dropping = create_sample_market_data(prices_dropping)
        
        print(f"\n3. Price dropping to ${prices_dropping[-1]:,.2f}")
        signal = strategy.generate_signal(market_data_dropping)
        print(f"   Signal: {signal}")
        
        if signal == "SELL":
            print(f"   Trailing stop triggered!")
            print(f"   Available capital: ${strategy.available_capital:,.2f}")
    
    return strategy

def test_profit_splitting():
    """Test profit splitting functionality"""
    print("\n🔍 Testing Profit Splitting")
    print("=" * 50)
    
    strategy = TrendFollowingStrategy(
        sma_short=3, 
        sma_long=5, 
        initial_capital=10000
    )
    
    # Create a position
    prices_buy = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
    market_data_buy = create_sample_market_data(prices_buy)
    strategy.generate_signal(market_data_buy)
    
    if strategy.current_position:
        print(f"\n1. Position created at ${strategy.current_position.entry_price:,.2f}")
        
        # Simulate profit by manually setting highest price
        strategy.current_position.highest_price = 12000  # 20% profit
        print(f"   Position value increased to ${strategy.current_position.highest_price:,.2f}")
        
        # Trigger sell (simulate trailing stop)
        prices_sell = [12000, 11900, 11800, 11700, 11600, 11500, 11400, 11300, 11200, 11100, 11000, 10900, 10800, 10700, 10600]
        market_data_sell = create_sample_market_data(prices_sell)
        
        print(f"\n2. Selling at ${prices_sell[-1]:,.2f}")
        signal = strategy.generate_signal(market_data_sell)
        print(f"   Signal: {signal}")
        
        if signal == "SELL":
            print(f"   Total profit: ${strategy.total_profit:,.2f}")
            print(f"   Available capital: ${strategy.available_capital:,.2f}")
            print(f"   Total trades: {strategy.total_trades}")
    
    return strategy

def test_ema_exit_signal():
    """Test EMA-based exit signal"""
    print("\n🔍 Testing EMA Exit Signal")
    print("=" * 50)
    
    strategy = TrendFollowingStrategy(
        sma_short=3, 
        sma_long=5, 
        ema_short=3,
        exit_candles=2,
        initial_capital=10000
    )
    
    # Create a position
    prices_buy = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
    market_data_buy = create_sample_market_data(prices_buy)
    strategy.generate_signal(market_data_buy)
    
    if strategy.current_position:
        print(f"\n1. Position created")
        
        # Test EMA below SMA for exit signal
        # Create data where EMA stays below SMA for multiple periods
        prices_exit = [110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96]
        market_data_exit = create_sample_market_data(prices_exit)
        
        print(f"\n2. Testing EMA exit signal:")
        print(f"   EMA below SMA count: {strategy.ema_below_sma_count}")
        
        signal = strategy.generate_signal(market_data_exit)
        print(f"   Signal: {signal}")
        print(f"   EMA below SMA count after: {strategy.ema_below_sma_count}")
        
        if signal == "SELL":
            print(f"   EMA exit signal triggered!")
    
    return strategy

def test_performance_tracking():
    """Test performance tracking and reporting"""
    print("\n🔍 Testing Performance Tracking")
    print("=" * 50)
    
    strategy = TrendFollowingStrategy(initial_capital=10000)
    
    # Simulate multiple trades
    print("\n1. Simulating multiple trades:")
    
    # Trade 1: Profit
    strategy.available_capital = 10000
    strategy.current_position = Position(
        entry_price=50000,
        entry_time=datetime.now(),
        highest_price=55000,
        highest_time=datetime.now(),
        amount=0.2,
        symbol="BTC"
    )
    
    # Simulate sell with profit
    strategy._execute_sell_signal("TEST", 55000, datetime.now())
    print(f"   Trade 1: Profit ${strategy.total_profit:,.2f}")
    
    # Trade 2: Loss
    strategy.available_capital = 900  # Reinvested amount
    strategy.current_position = Position(
        entry_price=50000,
        entry_time=datetime.now(),
        highest_price=50000,
        highest_time=datetime.now(),
        amount=0.018,
        symbol="BTC"
    )
    
    # Simulate sell with loss
    strategy._execute_sell_signal("TEST", 45000, datetime.now())
    print(f"   Trade 2: Loss ${strategy.total_profit:,.2f}")
    
    # Get performance summary
    print(f"\n2. Performance Summary:")
    performance = strategy.get_performance_summary()
    for key, value in performance.items():
        if isinstance(value, float):
            print(f"   {key}: {value:,.2f}")
        else:
            print(f"   {key}: {value}")
    
    return strategy

def test_error_handling():
    """Test error handling and validation"""
    print("\n🔍 Testing Error Handling")
    print("=" * 50)
    
    print("\n1. Testing invalid parameters:")
    
    # Test invalid SMA parameters
    try:
        strategy = TrendFollowingStrategy(sma_short=10, sma_long=5)
        print("   ❌ Should have raised error for invalid SMA parameters")
    except ValueError as e:
        print(f"   ✅ Correctly caught error: {e}")
    
    # Test invalid trailing stop
    try:
        strategy = TrendFollowingStrategy(trailing_stop_percentage=60)
        print("   ❌ Should have raised error for invalid trailing stop")
    except ValueError as e:
        print(f"   ✅ Correctly caught error: {e}")
    
    # Test invalid profit split
    try:
        invalid_split = ProfitSplit(tax_percentage=50, reinvest_percentage=60, withdrawal_percentage=10)
        print("   ❌ Should have raised error for invalid profit split")
    except ValueError as e:
        print(f"   ✅ Correctly caught error: {e}")
    
    # Test insufficient data
    strategy = TrendFollowingStrategy()
    insufficient_data = create_sample_market_data([100, 101, 102])  # Only 3 data points
    signal = strategy.generate_signal(insufficient_data)
    print(f"\n2. Insufficient data test: Signal = {signal} (should be None)")

def main():
    """Main test function"""
    print("🚀 Testing Trend Following Strategy")
    print("=" * 60)
    
    try:
        # Test strategy initialization
        strategy = test_strategy_initialization()
        
        # Test buy signal generation
        test_buy_signal_generation()
        
        # Test trailing stop functionality
        test_trailing_stop_functionality()
        
        # Test profit splitting
        test_profit_splitting()
        
        # Test EMA exit signal
        test_ema_exit_signal()
        
        # Test performance tracking
        test_performance_tracking()
        
        # Test error handling
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\n📋 Summary of Trend Following Strategy Features:")
        print("   • SMA crossover for entry signals")
        print("   • EMA/SMA crossover for exit signals")
        print("   • Trailing stop loss protection")
        print("   • Profit splitting (tax, reinvest, withdrawal)")
        print("   • Position tracking and management")
        print("   • Performance monitoring and reporting")
        print("   • Comprehensive error handling and validation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 