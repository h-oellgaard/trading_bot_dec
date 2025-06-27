#!/usr/bin/env python3
"""
Test Markets and Endpoints
Check what markets are available and their exact format
"""

import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from exchange.firi_exchange import FiriExchange
from config.firi_config import FIRI_CONFIG

def test_markets():
    """Test markets and endpoints"""
    print("🔍 Testing Firi Markets and Endpoints")
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
    
    # Test 1: Get all markets
    print("\n1. Getting all markets...")
    try:
        markets = firi.get_markets()
        print(f"   ✅ Found {len(markets)} markets")
        
        # Show first few markets in detail
        for i, market in enumerate(markets[:5]):
            print(f"   Market {i+1}: {json.dumps(market, indent=4)}")
            
        # Look for DKK markets
        dkk_markets = [m for m in markets if 'DKK' in str(m)]
        print(f"\n   🇩🇰 Found {len(dkk_markets)} DKK markets:")
        for market in dkk_markets:
            print(f"      - {market}")
            
    except Exception as e:
        print(f"   ❌ Error getting markets: {e}")
        return
    
    # Test 2: Try to get ticker for first market
    if markets:
        first_market = markets[0]
        market_symbol = first_market.get('id', 'Unknown')
        print(f"\n2. Testing ticker for first market: {market_symbol}")
        
        try:
            ticker = firi.get_ticker(market_symbol)
            if ticker:
                print(f"   ✅ Ticker data: {json.dumps(ticker, indent=4)}")
            else:
                print("   ❌ No ticker data returned")
        except Exception as e:
            print(f"   ❌ Error getting ticker: {e}")
    
    # Test 3: Try to get orderbook for first market
    if markets:
        first_market = markets[0]
        market_symbol = first_market.get('id', 'Unknown')
        print(f"\n3. Testing orderbook for first market: {market_symbol}")
        
        try:
            orderbook = firi.get_orderbook(market_symbol, depth=5)
            if orderbook:
                print(f"   ✅ Orderbook data: {json.dumps(orderbook, indent=4)}")
            else:
                print("   ❌ No orderbook data returned")
        except Exception as e:
            print(f"   ❌ Error getting orderbook: {e}")
    
    # Test 4: Try to get historical data for first market
    if markets:
        first_market = markets[0]
        market_symbol = first_market.get('id', 'Unknown')
        print(f"\n4. Testing historical data for first market: {market_symbol}")
        
        try:
            history = firi.get_historical_data(market_symbol, interval='1h', limit=5)
            if history:
                print(f"   ✅ Historical data: {len(history)} records")
                for record in history[:3]:
                    print(f"      - {record}")
            else:
                print("   ❌ No historical data returned")
        except Exception as e:
            print(f"   ❌ Error getting historical data: {e}")
    
    # Test 5: Test ETHDKK specifically
    print(f"\n5. Testing ETHDKK specifically...")
    try:
        ticker = firi.get_ticker("ETHDKK")
        if ticker:
            print(f"   ✅ ETHDKK ticker data: {json.dumps(ticker, indent=4)}")
        else:
            print("   ❌ No ETHDKK ticker data returned")
    except Exception as e:
        print(f"   ❌ Error getting ETHDKK ticker: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Markets test completed!")

if __name__ == "__main__":
    test_markets() 