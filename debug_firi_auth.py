#!/usr/bin/env python3
"""
Debug Firi Authentication Issues
Tests authentication and captures specific error messages from Firi API
"""

import sys
import os
import requests
import time
import hmac
import hashlib
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.firi_config import FIRI_CONFIG

def test_firi_auth():
    """Test Firi authentication and capture specific error messages"""
    print("🔍 Firi Authentication Debug Test")
    print("=" * 50)
    
    # Test configuration
    api_key = FIRI_CONFIG['api_key']
    client_id = FIRI_CONFIG['client_id']
    secret = FIRI_CONFIG['secret']
    base_url = FIRI_CONFIG['base_url']
    
    print(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
    print(f"Client ID: {client_id}")
    print(f"Secret: {secret[:8]}...{secret[-4:] if len(secret) > 12 else '***'}")
    print()
    
    # Test 1: Get server time
    print("1. Testing server time endpoint...")
    try:
        response = requests.get(f"{base_url}/time")
        response.raise_for_status()
        server_time = response.json().get('time')
        print(f"   ✅ Server time: {server_time}")
        print(f"   ✅ Local time: {int(time.time())}")
        print(f"   ✅ Time difference: {abs(server_time - int(time.time()))} seconds")
    except Exception as e:
        print(f"   ❌ Failed to get server time: {e}")
        server_time = int(time.time())
    
    print()
    
    # Test 2: Test signature generation
    print("2. Testing signature generation...")
    try:
        # According to Firi docs: body should contain timestamp and validity as strings
        timestamp = server_time
        validity = "2000"
        
        # For GET requests, signature body is just timestamp and validity
        signature_body = {
            "timestamp": str(timestamp),
            "validity": validity
        }
        
        # Convert to JSON string for HMAC
        message = json.dumps(signature_body)
        
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"   ✅ Message: {message}")
        print(f"   ✅ Signature: {signature}")
        print(f"   ✅ Timestamp: {timestamp}")
        print(f"   ✅ Validity: {validity}")
    except Exception as e:
        print(f"   ❌ Failed to generate signature: {e}")
        return
    
    print()
    
    # Test 3: Test authenticated request with correct headers
    print("3. Testing authenticated request with correct headers...")
    
    headers = {
        'Content-Type': 'application/json',
        'firi-access-key': api_key,  # Correct API key header
        'firi-user-signature': signature,  # Correct signature header
        'firi-user-clientid': client_id,  # Correct client ID header
    }
    
    print(f"   Headers: {json.dumps(headers, indent=2)}")
    print()
    
    # Test different endpoints with correct authentication
    test_endpoints = [
        '/v1/orders?count=5',
        '/v1/balance',
        '/v1/orders/closed?count=5'
    ]
    
    for endpoint in test_endpoints:
        print(f"   Testing endpoint: {endpoint}")
        try:
            # Add timestamp and validity as query parameters
            separator = '&' if '?' in endpoint else '?'
            url = f"{base_url}{endpoint}{separator}timestamp={timestamp}&validity=2000"
            
            response = requests.get(url, headers=headers)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print(f"   ✅ Success: {response.json()}")
            else:
                print(f"   ❌ Error Response: {response.text}")
                
                # Try to parse error message
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        print(f"   🔍 Error Type: {error_data['error']}")
                    if 'message' in error_data:
                        print(f"   🔍 Error Message: {error_data['message']}")
                except:
                    print(f"   🔍 Raw Error: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        print()
    
    # Test 4: Test without authentication
    print("4. Testing without authentication...")
    try:
        response = requests.get(f"{base_url}/v1/markets")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            markets = response.json()
            print(f"   ✅ Markets found: {len(markets)}")
            print(f"   ✅ Sample markets: {[m.get('symbol', 'Unknown') for m in markets[:3]]}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    print()
    
    # Test 5: Test different header combinations
    print("5. Testing different header combinations...")
    
    header_combinations = [
        {
            'name': 'All headers',
            'headers': {
                'Content-Type': 'application/json',
                'API-key': api_key,
                'X-Client-ID': client_id,
                'X-Signature': signature,
                'X-Timestamp': str(timestamp),
                'X-Validity': validity
            }
        },
        {
            'name': 'Authorization Bearer',
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'X-Client-ID': client_id,
                'X-Signature': signature,
                'X-Timestamp': str(timestamp),
                'X-Validity': validity
            }
        },
        {
            'name': 'API-key only (no other auth headers)',
            'headers': {
                'Content-Type': 'application/json',
                'API-key': api_key
            }
        },
        {
            'name': 'Without X-Client-ID',
            'headers': {
                'Content-Type': 'application/json',
                'API-key': api_key,
                'X-Signature': signature,
                'X-Timestamp': str(timestamp),
                'X-Validity': validity
            }
        },
        {
            'name': 'Lowercase headers',
            'headers': {
                'content-type': 'application/json',
                'api-key': api_key,
                'x-client-id': client_id,
                'x-signature': signature,
                'x-timestamp': str(timestamp),
                'x-validity': validity
            }
        },
        {
            'name': 'Without Content-Type',
            'headers': {
                'API-key': api_key,
                'X-Client-ID': client_id,
                'X-Signature': signature,
                'X-Timestamp': str(timestamp),
                'X-Validity': validity
            }
        },
        {
            'name': 'Without Validity',
            'headers': {
                'Content-Type': 'application/json',
                'API-key': api_key,
                'X-Client-ID': client_id,
                'X-Signature': signature,
                'X-Timestamp': str(timestamp)
            }
        }
    ]
    
    for combo in header_combinations:
        print(f"   Testing: {combo['name']}")
        try:
            response = requests.get(f"{base_url}/v1/orders?count=5", headers=combo['headers'])
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Error: {response.text[:200]}...")
            else:
                print(f"   ✅ SUCCESS!")
        except Exception as e:
            print(f"   Failed: {e}")
        print()
    
    # Test 6: Test balance endpoint with correct path
    print("6. Testing balance endpoint with correct path...")
    try:
        response = requests.get(f"{base_url}/v1/balance", headers={
            'Content-Type': 'application/json',
            'API-key': api_key,
            'X-Client-ID': client_id,
            'X-Signature': signature,
            'X-Timestamp': str(timestamp),
            'X-Validity': validity
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Balance data: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    print()
    
    # Test 7: Test with API key as query parameter...
    try:
        response = requests.get(f"{base_url}/v1/orders?count=5&api_key={api_key}", headers={
            'Content-Type': 'application/json',
            'X-Client-ID': client_id,
            'X-Signature': signature,
            'X-Timestamp': str(timestamp),
            'X-Validity': validity
        })
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error: {response.text[:200]}...")
        else:
            print(f"   ✅ SUCCESS!")
    except Exception as e:
        print(f"   Failed: {e}")
    
    print()
    
    # Test 8: Test different API key header formats
    print("8. Testing different API key header formats...")
    
    api_key_formats = [
        {'name': 'X-API-Key', 'header': 'X-API-Key'},
        {'name': 'x-api-key', 'header': 'x-api-key'},
        {'name': 'Api-Key', 'header': 'Api-Key'},
        {'name': 'api-key', 'header': 'api-key'},
        {'name': 'APIKey', 'header': 'APIKey'},
        {'name': 'apikey', 'header': 'apikey'},
        {'name': 'X-Api-Key', 'header': 'X-Api-Key'},
        {'name': 'X-APIKEY', 'header': 'X-APIKEY'},
        {'name': 'X-API-KEY', 'header': 'X-API-KEY'},
        {'name': 'Authorization: ApiKey', 'header': 'Authorization', 'value': f'ApiKey {api_key}'},
        {'name': 'Authorization: APIKey', 'header': 'Authorization', 'value': f'APIKey {api_key}'},
        {'name': 'Authorization: apikey', 'header': 'Authorization', 'value': f'apikey {api_key}'},
        {'name': 'Authorization: API-Key', 'header': 'Authorization', 'value': f'API-Key {api_key}'},
    ]
    
    for format_test in api_key_formats:
        print(f"   Testing: {format_test['name']}")
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Client-ID': client_id,
                'X-Signature': signature,
                'X-Timestamp': str(timestamp),
                'X-Validity': validity
            }
            
            if 'value' in format_test:
                headers[format_test['header']] = format_test['value']
            else:
                headers[format_test['header']] = api_key
            
            response = requests.get(f"{base_url}/v1/orders?count=5", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with {format_test['name']}!")
                break
            elif response.status_code != 401:
                print(f"   Different error: {response.text[:100]}...")
            else:
                print(f"   Still 401: {response.text[:100]}...")
        except Exception as e:
            print(f"   Failed: {e}")
        print()
    
    # Test 9: Test without signature (maybe API key is enough)
    print("9. Testing with API key only (no signature)...")
    try:
        response = requests.get(f"{base_url}/v1/orders?count=5", headers={
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'X-Client-ID': client_id
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ SUCCESS with API key only!")
        else:
            print(f"   Error: {response.text[:200]}...")
    except Exception as e:
        print(f"   Failed: {e}")
    
    print()
    
    # Test 10: Test with different client ID header
    print("10. Testing different client ID header formats...")
    client_id_formats = [
        {'name': 'X-Client-ID', 'header': 'X-Client-ID'},
        {'name': 'x-client-id', 'header': 'x-client-id'},
        {'name': 'Client-ID', 'header': 'Client-ID'},
        {'name': 'client-id', 'header': 'client-id'},
        {'name': 'ClientID', 'header': 'ClientID'},
        {'name': 'clientid', 'header': 'clientid'},
    ]
    
    for format_test in client_id_formats:
        print(f"   Testing: {format_test['name']}")
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': api_key,
                'X-Signature': signature,
                'X-Timestamp': str(timestamp),
                'X-Validity': validity
            }
            headers[format_test['header']] = client_id
            
            response = requests.get(f"{base_url}/v1/orders?count=5", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with {format_test['name']}!")
                break
            elif response.status_code != 401:
                print(f"   Different error: {response.text[:100]}...")
            else:
                print(f"   Still 401: {response.text[:100]}...")
        except Exception as e:
            print(f"   Failed: {e}")
        print()

if __name__ == "__main__":
    test_firi_auth() 