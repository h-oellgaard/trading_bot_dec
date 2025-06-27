#!/usr/bin/env python3
"""
Test SMA Strategy Analysis with Real Bitcoin Data
Analyzes the provided Bitcoin price data to show how the SMA strategy would perform.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_sma(prices, window):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(window=window).mean()

def analyze_sma_strategy():
    """Analyze how the SMA strategy would perform on this data"""
    print("=== Bitcoin SMA Strategy Analysis ===\n")
    
    # Bitcoin price data from the table (chronological order from May 26 to Jun 24)
    prices = [
        104015, 105689, 107773, 108957, 109409,  # May 26-30
        104703, 105631, 105843, 105433, 104731,  # May 31 - Jun 4
        101594, 104410, 105681, 105692, 110262,  # Jun 5-9
        110213, 108680, 105979, 106046, 105483,  # Jun 10-14
        105554, 106951, 104683, 104723, 104691,  # Jun 15-19
        103290, 101533, 100853, 105512, 105976   # Jun 20-24
    ]
    
    # Create dates (starting from May 26, 2025)
    start_date = datetime(2025, 5, 26)
    dates = [start_date + timedelta(days=i) for i in range(len(prices))]
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'close': prices
    })
    
    print("Price Data Summary:")
    print(f"Date Range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Total Days: {len(df)}")
    print(f"Price Range: ${df['close'].min():,} - ${df['close'].max():,}")
    print(f"Price Change: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
    print()
    
    # Calculate SMAs
    short_window = 7
    long_window = 21
    short_sma = calculate_sma(prices, short_window)
    long_sma = calculate_sma(prices, long_window)
    
    print("=== SMA Analysis Results ===\n")
    
    # Find crossover points
    crossovers = []
    for i in range(long_window, len(prices)):
        if short_sma.iloc[i-1] <= long_sma.iloc[i-1] and short_sma.iloc[i] > long_sma.iloc[i]:
            crossovers.append(('BUY', df['date'].iloc[i], df['close'].iloc[i], 
                              short_sma.iloc[i], long_sma.iloc[i]))
        elif short_sma.iloc[i-1] >= long_sma.iloc[i-1] and short_sma.iloc[i] < long_sma.iloc[i]:
            crossovers.append(('SELL', df['date'].iloc[i], df['close'].iloc[i],
                              short_sma.iloc[i], long_sma.iloc[i]))
    
    print("SMA Crossover Analysis:")
    print(f"7-day SMA: {short_sma.iloc[-1]:.0f}")
    print(f"21-day SMA: {long_sma.iloc[-1]:.0f}")
    print(f"Current Trend: {'BULLISH' if short_sma.iloc[-1] > long_sma.iloc[-1] else 'BEARISH'}")
    print()
    
    if crossovers:
        print("Crossover Events:")
        for signal, date, price, short_val, long_val in crossovers:
            strength = ((short_val - long_val) / long_val) * 100
            print(f"  {date.strftime('%Y-%m-%d')}: {signal} at ${price:,} (Strength: {strength:+.2f}%)")
    else:
        print("No crossovers detected in this period")
    
    print()
    
    # Performance analysis
    print("=== Performance Analysis ===\n")
    
    # Calculate potential returns if we followed the strategy
    if len(crossovers) >= 2:
        buy_price = crossovers[0][2]  # First BUY signal
        sell_price = crossovers[-1][2] if crossovers[-1][0] == 'SELL' else df['close'].iloc[-1]
        
        if crossovers[-1][0] == 'SELL':
            potential_return = ((sell_price - buy_price) / buy_price) * 100
            print(f"Potential Strategy Return: {potential_return:+.2f}%")
        else:
            current_return = ((df['close'].iloc[-1] - buy_price) / buy_price) * 100
            print(f"Current Unrealized Return: {current_return:+.2f}%")
    
    # Volatility analysis
    returns = df['close'].pct_change().dropna()
    volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
    print(f"Annualized Volatility: {volatility:.2f}%")
    
    # Trend analysis
    price_change = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
    print(f"Overall Price Change: {price_change:+.2f}%")
    
    print()
    
    # Strategy assessment
    print("=== Strategy Assessment ===\n")
    
    if len(crossovers) > 0:
        print("✅ Strategy would have generated signals")
        print("✅ Clear trend identification possible")
        print("✅ Sufficient data for analysis")
    else:
        print("⚠️  No crossovers detected - strategy may be too conservative")
        print("⚠️  Consider shorter SMA periods for more active trading")
    
    # Check for noise tolerance
    recent_volatility = returns.tail(7).std() * 100
    if recent_volatility > 5:
        print("⚠️  High recent volatility - signals may be noisy")
    else:
        print("✅ Low volatility - signals likely more reliable")
    
    print()
    print("=== Recommendations ===\n")
    
    if len(crossovers) == 0:
        print("1. Consider shorter SMA periods (e.g., 5/15 instead of 7/21)")
        print("2. This period shows sideways movement - strategy may need adjustment")
        print("3. Monitor for breakout opportunities")
    else:
        print("1. Strategy appears suitable for this market")
        print("2. Consider implementing stop-loss orders")
        print("3. Monitor signal strength for entry/exit timing")
    
    print()
    print("=== Detailed Analysis ===\n")
    
    # Show recent price movement
    print("Recent Price Movement (Last 7 days):")
    recent_prices = df.tail(7)
    for _, row in recent_prices.iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')}: ${row['close']:,}")
    
    print()
    print("SMA Values (Last 7 days):")
    recent_sma = pd.DataFrame({
        'date': df['date'].tail(7),
        'price': df['close'].tail(7),
        '7-day SMA': short_sma.tail(7),
        '21-day SMA': long_sma.tail(7)
    })
    
    for _, row in recent_sma.iterrows():
        if not pd.isna(row['7-day SMA']):
            print(f"  {row['date'].strftime('%Y-%m-%d')}: Price=${row['price']:,}, "
                  f"7SMA={row['7-day SMA']:.0f}, 21SMA={row['21-day SMA']:.0f}")

if __name__ == "__main__":
    analyze_sma_strategy() 