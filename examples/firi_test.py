#!/usr/bin/env python3
"""
Firi Trading Platform Integration Test Script
This script tests the Firi exchange integration with your API credentials.
"""

import sys
import os
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import configuration
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from config.firi_config import FIRI_CONFIG
except ImportError:
    print("❌ Error: Could not import Firi configuration.")
    print("Make sure config/firi_config.py exists and contains your API credentials.")
    sys.exit(1)

from exchange.firi_exchange import FiriExchange


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/firi_test.log')
        ]
    )


def test_basic_functionality():
    """Test basic Firi API functionality"""
    print("🔥 Firi Trading Platform Integration Test")
    print("=" * 60)
    
    # Initialize Firi exchange
    try:
        exchange = FiriExchange(
            api_key=FIRI_CONFIG['api_key'],
            client_id=FIRI_CONFIG['client_id'],
            secret=FIRI_CONFIG['secret'],
            base_url=FIRI_CONFIG['base_url'],
            sandbox=FIRI_CONFIG['sandbox']
        )
        print("✅ Firi exchange initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Firi exchange: {e}")
        return False
    
    # Test 1: Basic connection test
    print("\n" + "=" * 60)
    print("📡 TEST 1: Basic Connection Test")
    print("=" * 60)
    
    connection_results = exchange.test_connection()
    
    if connection_results['connection']:
        print("\n🎉 Basic connection test PASSED!")
        return True
    else:
        print("\n❌ Basic connection test FAILED!")
        return False


def test_trading_functionality():
    """Test trading functionality (with small test orders)"""
    print("\n" + "=" * 60)
    print("💰 TEST 2: Trading Functionality Test")
    print("=" * 60)
    
    # Initialize Firi exchange
    exchange = FiriExchange(
        api_key=FIRI_CONFIG['api_key'],
        client_id=FIRI_CONFIG['client_id'],
        secret=FIRI_CONFIG['secret'],
        base_url=FIRI_CONFIG['base_url'],
        sandbox=FIRI_CONFIG['sandbox']
    )
    
    # Test trading functionality with ETHDKK
    trading_results = exchange.test_trading_functionality(
        test_symbol="ETHDKK",
        test_amount=0.01  # Minimum allowed amount for Firi
    )
    
    if trading_results['price_retrieval']:
        print("\n🎉 Trading functionality test PASSED!")
        return True
    else:
        print("\n⚠️  Trading functionality test has issues!")
        return False


def test_market_data():
    """Test market data retrieval"""
    print("\n" + "=" * 60)
    print("📊 TEST 3: Market Data Test")
    print("=" * 60)
    
    # Initialize Firi exchange
    exchange = FiriExchange(
        api_key=FIRI_CONFIG['api_key'],
        client_id=FIRI_CONFIG['client_id'],
        secret=FIRI_CONFIG['secret'],
        base_url=FIRI_CONFIG['base_url'],
        sandbox=FIRI_CONFIG['sandbox']
    )
    
    try:
        # Get available markets
        print("1. Getting available markets...")
        markets = exchange.get_markets()
        if markets:
            print(f"   ✅ Found {len(markets)} markets")
            
            # Show DKK markets specifically
            dkk_markets = exchange.get_dkk_markets()
            print(f"   🇩🇰 Found {len(dkk_markets)} DKK markets")
            for market in dkk_markets:
                print(f"      {market.get('id')}: {market.get('last')} DKK")
        else:
            print("   ❌ No markets found")
            return False
        
        # Get current price for ETHDKK
        print("\n2. Getting current ETHDKK price...")
        ethdkk_price = exchange.get_current_price("ETHDKK")
        if ethdkk_price:
            print(f"   ✅ ETHDKK current price: {ethdkk_price} DKK")
        else:
            print("   ❌ Could not get ETHDKK price")
            return False
        
        # Get current price for BTCDKK
        print("\n3. Getting current BTCDKK price...")
        btcdkk_price = exchange.get_current_price("BTCDKK")
        if btcdkk_price:
            print(f"   ✅ BTCDKK current price: {btcdkk_price} DKK")
        else:
            print("   ❌ Could not get BTCDKK price")
            return False
        
        print("\n🎉 Market data test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False


def test_account_info():
    """Test account information retrieval"""
    print("\n" + "=" * 60)
    print("👤 TEST 4: Account Information Test")
    print("=" * 60)
    
    # Initialize Firi exchange
    exchange = FiriExchange(
        api_key=FIRI_CONFIG['api_key'],
        client_id=FIRI_CONFIG['client_id'],
        secret=FIRI_CONFIG['secret'],
        base_url=FIRI_CONFIG['base_url'],
        sandbox=FIRI_CONFIG['sandbox']
    )
    
    try:
        # Get account info
        print("1. Getting account information...")
        account_info = exchange.get_account_info()
        if account_info:
            print("   ✅ Account information retrieved")
            print(f"   👤 Account ID: {account_info.get('accountId', 'Unknown')}")
            print(f"   📧 Email: {account_info.get('email', 'Unknown')}")
        else:
            print("   ❌ Could not get account information")
            return False
        
        # Get balance
        print("\n2. Getting account balance...")
        balance = exchange.get_balance()
        if balance:
            print(f"   ✅ Balance retrieved: {len(balance)} currencies")
            for bal in balance[:5]:  # Show first 5 balances
                currency = bal.get('currency', 'Unknown')
                available = bal.get('available', 0)
                total = bal.get('total', 0)
                print(f"      {currency}: Available={available}, Total={total}")
        else:
            print("   ❌ Could not get balance")
            return False
        
        # Get orders
        print("\n3. Getting recent orders...")
        orders = exchange.get_orders(limit=5)
        if orders is not None:
            print(f"   ✅ Orders retrieved: {len(orders)} orders")
            for order in orders[:3]:
                order_id = order.get('orderId', 'Unknown')
                symbol = order.get('symbol', 'Unknown')
                side = order.get('side', 'Unknown')
                status = order.get('status', 'Unknown')
                print(f"      {order_id}: {symbol} {side} - {status}")
        else:
            print("   ❌ Could not get orders")
            return False
        
        # Get trades
        print("\n4. Getting recent trades...")
        trades = exchange.get_trades(limit=5)
        if trades is not None:
            print(f"   ✅ Trades retrieved: {len(trades)} trades")
            for trade in trades[:3]:
                trade_id = trade.get('tradeId', 'Unknown')
                symbol = trade.get('symbol', 'Unknown')
                side = trade.get('side', 'Unknown')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                print(f"      {trade_id}: {symbol} {side} {quantity} @ {price}")
        else:
            print("   ❌ Could not get trades")
            return False
        
        print("\n🎉 Account information test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Account information test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🔥 Firi Trading Platform Integration Test Suite")
    print("=" * 60)
    print(f"📅 Test started at: {datetime.now()}")
    print(f"🔧 Sandbox mode: {FIRI_CONFIG['sandbox']}")
    print(f"🌐 API URL: {FIRI_CONFIG['base_url']}")
    
    # Setup logging
    setup_logging()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    test_results = {
        'basic_connection': False,
        'trading_functionality': False,
        'market_data': False,
        'account_info': False
    }
    
    try:
        # Run tests
        test_results['basic_connection'] = test_basic_functionality()
        
        if test_results['basic_connection']:
            test_results['market_data'] = test_market_data()
            test_results['account_info'] = test_account_info()
            test_results['trading_functionality'] = test_trading_functionality()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 FINAL TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"✅ Tests passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print()
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print()
        if success_rate >= 75:
            print("🎉 Firi integration is working well!")
        elif success_rate >= 50:
            print("⚠️  Firi integration has some issues but is partially working.")
        else:
            print("❌ Firi integration has significant issues.")
        
        print(f"\n📅 Test completed at: {datetime.now()}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        logging.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main() 