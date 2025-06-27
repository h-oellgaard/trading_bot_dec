#!/usr/bin/env python3
"""
Example script demonstrating Firestore data persistence for the crypto trading bot.
This script shows how to use the DataManager to collect, store, and retrieve price data.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import time

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_manager import DataManager
from domain.trade import Trade
from domain.coin import Coin
from strategies.sma_cross import SmaCrossStrategy


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('firestore_example.log')
        ]
    )


def demonstrate_price_data_persistence():
    """Demonstrate price data collection and persistence"""
    print("\n=== Price Data Persistence Demo ===")
    
    # Initialize data manager (uses default project if GOOGLE_APPLICATION_CREDENTIALS is set)
    data_manager = DataManager()
    
    # Symbols to collect data for
    symbols = ['bitcoin', 'ethereum', 'cardano']
    
    print(f"Starting data collection for: {symbols}")
    
    # Start background data collection
    data_manager.start_data_collection(symbols, interval=30)  # Collect every 30 seconds
    
    try:
        # Let it collect data for a few minutes
        print("Collecting data for 3 minutes...")
        time.sleep(180)  # 3 minutes
        
        # Stop collection
        data_manager.stop_data_collection()
        
        # Show collected data
        print("\n--- Collected Data Statistics ---")
        for symbol in symbols:
            stats = data_manager.get_data_statistics(symbol)
            print(f"{symbol.upper()}: {stats}")
        
        # Show available symbols
        available_symbols = data_manager.get_available_symbols()
        print(f"\nAvailable symbols in database: {available_symbols}")
        
    except KeyboardInterrupt:
        print("\nStopping data collection...")
        data_manager.stop_data_collection()


def demonstrate_market_data_retrieval():
    """Demonstrate retrieving market data for strategy analysis"""
    print("\n=== Market Data Retrieval Demo ===")
    
    data_manager = DataManager()
    strategy = SmaCrossStrategy(short_window=5, long_window=20)
    
    # Get market data for Bitcoin
    symbol = 'bitcoin'
    periods = 30
    
    print(f"Retrieving {periods} periods of market data for {symbol}...")
    market_data = data_manager.get_market_data(symbol, periods)
    
    if market_data:
        print(f"Retrieved {len(market_data)} periods of data")
        print(f"Latest price: ${market_data.get_latest_price():,.2f}")
        print(f"Latest volume: {market_data.get_latest_volume():,.0f}")
        print(f"Latest timestamp: {market_data.get_latest_timestamp()}")
        
        # Generate trading signal
        signal = strategy.generate_signal(market_data)
        print(f"Generated signal: {signal}")
    else:
        print("No market data available")


def demonstrate_trade_persistence():
    """Demonstrate trade data persistence"""
    print("\n=== Trade Data Persistence Demo ===")
    
    data_manager = DataManager()
    
    # Create some sample trades
    btc_coin = Coin(symbol='bitcoin', name='Bitcoin', precision=8)
    eth_coin = Coin(symbol='ethereum', name='Ethereum', precision=8)
    
    trades = [
        Trade(
            coin=btc_coin,
            action='BUY',
            amount=0.1,
            price=50000.0,
            timestamp=datetime.now() - timedelta(hours=2),
            strategy='SMA_CROSS'
        ),
        Trade(
            coin=eth_coin,
            action='SELL',
            amount=2.0,
            price=3000.0,
            timestamp=datetime.now() - timedelta(hours=1),
            strategy='SMA_CROSS'
        ),
        Trade(
            coin=btc_coin,
            action='BUY',
            amount=0.05,
            price=51000.0,
            timestamp=datetime.now(),
            strategy='SMA_CROSS'
        )
    ]
    
    # Save trades
    print("Saving sample trades...")
    for trade in trades:
        success = data_manager.save_trade(trade)
        print(f"Trade {trade.id}: {'Saved' if success else 'Failed'}")
    
    # Retrieve trades
    print("\n--- Retrieved Trades ---")
    all_trades = data_manager.get_trades()
    for trade in all_trades:
        print(f"ID: {trade.id}, {trade.coin.symbol} {trade.action} {trade.amount} @ ${trade.price:,.2f}")
    
    # Get trading statistics
    print("\n--- Trading Statistics ---")
    stats = data_manager.get_trading_statistics()
    print(f"Total trades: {stats.get('total_trades', 0)}")
    print(f"Buy trades: {stats.get('buy_trades', 0)}")
    print(f"Sell trades: {stats.get('sell_trades', 0)}")
    print(f"Total volume: ${stats.get('total_volume', 0):,.2f}")


def demonstrate_data_cleanup():
    """Demonstrate data cleanup functionality"""
    print("\n=== Data Cleanup Demo ===")
    
    data_manager = DataManager()
    
    # Clean up data older than 7 days (for demo purposes)
    print("Cleaning up data older than 7 days...")
    deleted_count = data_manager.cleanup_old_data(days_to_keep=7)
    print(f"Deleted {deleted_count} old records")


def main():
    """Main function to run all demonstrations"""
    print("🔥 Firestore Data Persistence Demo")
    print("=" * 50)
    
    setup_logging()
    
    try:
        # Run demonstrations
        demonstrate_price_data_persistence()
        demonstrate_market_data_retrieval()
        demonstrate_trade_persistence()
        demonstrate_data_cleanup()
        
        print("\n✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        logging.error(f"Demo error: {e}", exc_info=True)


if __name__ == "__main__":
    main() 