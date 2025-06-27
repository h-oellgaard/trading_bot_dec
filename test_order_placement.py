#!/usr/bin/env python3
"""
Test Order Placement with Firi Exchange
Tests the order placement functionality with the updated authentication
"""

import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from exchange.firi_exchange import FiriExchange
from config.firi_config import FIRI_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_order_placement():
    """Test order placement functionality"""
    print("🔥 Testing Firi Order Placement")
    print("=" * 50)
    
    # Initialize Firi exchange
    firi = FiriExchange(
        api_key=FIRI_CONFIG['api_key'],
        client_id=FIRI_CONFIG['client_id'],
        secret=FIRI_CONFIG['secret'],
        base_url=FIRI_CONFIG['base_url'],
        sandbox=FIRI_CONFIG['sandbox']
    )
    
    print("✅ Firi exchange initialized")
    
    # Test 1: Get current market data
    print("\n1. Getting current market data...")
    try:
        ticker = firi.get_ticker("ETHDKK")
        if ticker:
            current_price = float(ticker.get('last', 0))
            print(f"   ✅ Current ETHDKK price: {current_price}")
        else:
            print("   ❌ Failed to get current price")
            return
    except Exception as e:
        print(f"   ❌ Error getting market data: {e}")
        return
    
    # Test 2: Get current orders
    print("\n2. Getting current orders...")
    try:
        orders = firi.get_orders(count=5)
        print(f"   ✅ Found {len(orders)} current orders")
        for order in orders:
            print(f"      - {order.get('market', 'Unknown')} {order.get('type', 'Unknown')} {order.get('amount', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Error getting orders: {e}")
    
    # Test 3: Place a test order (bid - buy order)
    print("\n3. Testing order placement (bid)...")
    try:
        # Place a bid order slightly below current price
        bid_price = current_price * 0.99  # 1% below current price
        test_amount = "0.001"  # Small test amount
        
        order_data = {
            'market': 'ETHDKK',
            'type': 'bid',
            'price': str(bid_price),
            'amount': test_amount
        }
        
        print(f"   📝 Placing bid order: {order_data}")
        result = firi.place_order(
            market='ETHDKK',
            order_type='bid',
            price=str(bid_price),
            amount=test_amount
        )
        
        if result:
            print(f"   ✅ Order placed successfully!")
            print(f"      Order ID: {result.get('id', 'Unknown')}")
            print(f"      Market: {result.get('market', 'Unknown')}")
            print(f"      Type: {result.get('type', 'Unknown')}")
            print(f"      Price: {result.get('price', 'Unknown')}")
            print(f"      Amount: {result.get('amount', 'Unknown')}")
        else:
            print("   ❌ Failed to place order")
            
    except Exception as e:
        print(f"   ❌ Error placing bid order: {e}")
    
    # Test 4: Place a test order (ask - sell order)
    print("\n4. Testing order placement (ask)...")
    try:
        # Place an ask order slightly above current price
        ask_price = current_price * 1.01  # 1% above current price
        test_amount = "0.001"  # Small test amount
        
        order_data = {
            'market': 'ETHDKK',
            'type': 'ask',
            'price': str(ask_price),
            'amount': test_amount
        }
        
        print(f"   📝 Placing ask order: {order_data}")
        result = firi.place_order(
            market='ETHDKK',
            order_type='ask',
            price=str(ask_price),
            amount=test_amount
        )
        
        if result:
            print(f"   ✅ Order placed successfully!")
            print(f"      Order ID: {result.get('id', 'Unknown')}")
            print(f"      Market: {result.get('market', 'Unknown')}")
            print(f"      Type: {result.get('type', 'Unknown')}")
            print(f"      Price: {result.get('price', 'Unknown')}")
            print(f"      Amount: {result.get('amount', 'Unknown')}")
        else:
            print("   ❌ Failed to place order")
            
    except Exception as e:
        print(f"   ❌ Error placing ask order: {e}")
    
    # Test 5: Get updated orders
    print("\n5. Getting updated orders...")
    try:
        orders = firi.get_orders(count=10)
        print(f"   ✅ Found {len(orders)} total orders")
        for order in orders:
            print(f"      - ID: {order.get('id', 'Unknown')} | {order.get('market', 'Unknown')} {order.get('type', 'Unknown')} {order.get('amount', 'Unknown')} @ {order.get('price', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Error getting updated orders: {e}")
    
    # Test 6: Test closed orders with market parameter
    print("\n6. Testing closed orders...")
    try:
        closed_orders = firi.get_closed_orders(market='ETHDKK', count=5)
        print(f"   ✅ Found {len(closed_orders)} closed orders for ETHDKK")
        for order in closed_orders:
            print(f"      - ID: {order.get('id', 'Unknown')} | {order.get('market', 'Unknown')} {order.get('type', 'Unknown')} {order.get('matched', 'Unknown')} matched")
    except Exception as e:
        print(f"   ❌ Error getting closed orders: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Order placement test completed!")

if __name__ == "__main__":
    test_order_placement() 