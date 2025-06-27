#!/usr/bin/env python3
"""
Test script to demonstrate the improved SMA Cross strategy features
"""

import sys
import os
import numpy as np
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.strategies.sma_cross import SmaCrossStrategy
from src.domain.strategy import MarketData

def create_sample_market_data(prices, volumes=None, timestamps=None):
    """Create sample market data for testing"""
    if volumes is None:
        volumes = [1000.0] * len(prices)
    if timestamps is None:
        timestamps = [datetime.now() - timedelta(minutes=i) for i in range(len(prices)-1, -1, -1)]
    
    return MarketData(prices=prices, volume=volumes, timestamp=timestamps)

def test_overfitting_warnings():
    """Test the overfitting warnings"""
    print("🔍 Testing Overfitting Warnings")
    print("=" * 50)
    
    # Test critical warning
    print("\n1. Testing critical warning (very small windows):")
    try:
        strategy = SmaCrossStrategy(short_window=2, long_window=3)
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test warning
    print("\n2. Testing warning (small windows):")
    try:
        strategy = SmaCrossStrategy(short_window=3, long_window=8)
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test normal initialization
    print("\n3. Testing normal initialization (recommended windows):")
    strategy = SmaCrossStrategy(short_window=7, long_window=21)
    
    return strategy

def test_debouncing_logic():
    """Test the debouncing and signal suppression logic"""
    print("\n🔍 Testing Debouncing Logic")
    print("=" * 50)
    
    strategy = SmaCrossStrategy(short_window=3, long_window=5, cooldown_period=10)
    
    # Create sample data with a clear crossover
    prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]  # Upward trend
    market_data = create_sample_market_data(prices)
    
    print(f"\n1. First signal generation:")
    signal1 = strategy.generate_signal(market_data)
    print(f"   Signal: {signal1}")
    
    print(f"\n2. Immediate second call (should be suppressed):")
    signal2 = strategy.generate_signal(market_data)
    print(f"   Signal: {signal2}")
    
    print(f"\n3. Check parameters:")
    params = strategy.get_parameters()
    print(f"   Last signal: {params['last_signal']}")
    print(f"   Last signal time: {params['last_signal_time']}")
    
    return strategy

def test_signal_strength():
    """Test signal strength analysis"""
    print("\n🔍 Testing Signal Strength Analysis")
    print("=" * 50)
    
    strategy = SmaCrossStrategy(short_window=3, long_window=5)
    
    # Create data with different SMA separations
    prices_close = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]  # Close SMAs
    prices_wide = [100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150]   # Wide separation
    
    market_data_close = create_sample_market_data(prices_close)
    market_data_wide = create_sample_market_data(prices_wide)
    
    strength_close = strategy.get_signal_strength(market_data_close)
    strength_wide = strategy.get_signal_strength(market_data_wide)
    
    print(f"Signal strength (close SMAs): {strength_close:.2f}%")
    print(f"Signal strength (wide separation): {strength_wide:.2f}%")
    
    return strategy

def test_market_trend():
    """Test market trend detection"""
    print("\n🔍 Testing Market Trend Detection")
    print("=" * 50)
    
    strategy = SmaCrossStrategy(short_window=3, long_window=5)
    
    # Create different market scenarios
    prices_bullish = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118, 120]  # Bullish
    prices_bearish = [120, 118, 116, 114, 112, 110, 108, 106, 104, 102, 100]  # Bearish
    prices_sideways = [100, 101, 100, 102, 99, 101, 100, 102, 99, 101, 100]   # Sideways
    
    market_data_bullish = create_sample_market_data(prices_bullish)
    market_data_bearish = create_sample_market_data(prices_bearish)
    market_data_sideways = create_sample_market_data(prices_sideways)
    
    trend_bullish = strategy.get_market_trend(market_data_bullish)
    trend_bearish = strategy.get_market_trend(market_data_bearish)
    trend_sideways = strategy.get_market_trend(market_data_sideways)
    
    print(f"Trend (bullish data): {trend_bullish}")
    print(f"Trend (bearish data): {trend_bearish}")
    print(f"Trend (sideways data): {trend_sideways}")
    
    return strategy

def test_parameter_recommendations():
    """Test different parameter configurations"""
    print("\n🔍 Testing Parameter Recommendations")
    print("=" * 50)
    
    # Conservative settings
    print("\n1. Conservative Settings:")
    conservative = SmaCrossStrategy(
        short_window=10,
        long_window=30,
        cooldown_period=300,
        min_data_points=100
    )
    print(f"   Parameters: {conservative.get_parameters()}")
    
    # Aggressive settings
    print("\n2. Aggressive Settings:")
    aggressive = SmaCrossStrategy(
        short_window=5,
        long_window=15,
        cooldown_period=60,
        min_data_points=30
    )
    print(f"   Parameters: {aggressive.get_parameters()}")
    
    # Balanced settings
    print("\n3. Balanced Settings (Recommended):")
    balanced = SmaCrossStrategy(
        short_window=7,
        long_window=21,
        cooldown_period=120,
        min_data_points=50
    )
    print(f"   Parameters: {balanced.get_parameters()}")

def main():
    """Main test function"""
    print("🚀 Testing Improved SMA Cross Strategy")
    print("=" * 60)
    
    try:
        # Test overfitting warnings
        strategy = test_overfitting_warnings()
        
        # Test debouncing logic
        test_debouncing_logic()
        
        # Test signal strength
        test_signal_strength()
        
        # Test market trend detection
        test_market_trend()
        
        # Test parameter recommendations
        test_parameter_recommendations()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\n📋 Summary of Improvements:")
        print("   • Better default parameters (7/21 instead of 3/5)")
        print("   • Overfitting warnings and protection")
        print("   • Debouncing logic with cooldown periods")
        print("   • Signal suppression to prevent flip-flopping")
        print("   • Signal strength analysis")
        print("   • Market trend detection")
        print("   • Parameter recommendations for different risk levels")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 