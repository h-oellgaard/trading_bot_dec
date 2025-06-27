#!/usr/bin/env python3
"""
Debug script to test Firi API authentication headers and signature generation
"""

import sys
import os
import requests
import hmac
import hashlib
import time
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import configuration
try:
    from config.firi_config import FIRI_CONFIG
except ImportError:
    print("❌ Error: Could not import Firi configuration.")
    sys.exit(1)

def test_different_auth_formats():
    """Test different authentication header formats"""
    
    print("🔍 Testing Firi API Authentication Headers")
    print("=" * 60)
    
    api_key = FIRI_CONFIG['api_key']
    client_id = FIRI_CONFIG['client_id']
    secret = FIRI_CONFIG['secret']
    base_url = FIRI_CONFIG['base_url']
    
    # Test endpoint that should work with authentication
    test_endpoint = "/v1/orders"
    url = f"{base_url}{test_endpoint}"
    
    # Get server time
    try:
        time_response = requests.get(f"{base_url}/time")
        if time_response.status_code == 200:
            server_time = time_response.json().get('time')
            print(f"✅ Server time: {server_time}")
        else:
            server_time = int(time.time())
            print(f"⚠️  Using local time: {server_time}")
    except:
        server_time = int(time.time())
        print(f"⚠️  Using local time: {server_time}")
    
    # Test different header formats
    header_formats = [
        {
            "name": "Current Format (X- prefix)",
            "headers": {
                'Content-Type': 'application/json',
                'X-API-Key': api_key,
                'X-Client-ID': client_id,
                'X-Signature': None,  # Will be calculated
                'X-Timestamp': str(server_time),
                'X-Validity': '60'
            }
        },
        {
            "name": "API- prefix Format",
            "headers": {
                'Content-Type': 'application/json',
                'API-KEY': api_key,
                'API-SIGNATURE': None,  # Will be calculated
                'API-TIMESTAMP': str(server_time)
            }
        },
        {
            "name": "Authorization Header Format",
            "headers": {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'X-Signature': None,  # Will be calculated
                'X-Timestamp': str(server_time)
            }
        },
        {
            "name": "Minimal Headers",
            "headers": {
                'X-API-Key': api_key,
                'X-Signature': None,  # Will be calculated
                'X-Timestamp': str(server_time)
            }
        }
    ]
    
    # Test different signature generation methods
    signature_methods = [
        {
            "name": "Current Method (secret + validity + timestamp + client_id)",
            "generate": lambda: hmac.new(
                secret.encode('utf-8'),
                f"{secret}60{server_time}{client_id}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        },
        {
            "name": "Standard HMAC (timestamp + method + path + body)",
            "generate": lambda: hmac.new(
                secret.encode('utf-8'),
                f"{server_time}GET{test_endpoint}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        },
        {
            "name": "Simple HMAC (timestamp + client_id)",
            "generate": lambda: hmac.new(
                secret.encode('utf-8'),
                f"{server_time}{client_id}".encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
        }
    ]
    
    for header_format in header_formats:
        print(f"\n📋 Testing: {header_format['name']}")
        print("-" * 40)
        
        for sig_method in signature_methods:
            try:
                # Generate signature
                signature = sig_method["generate"]()
                
                # Set signature in headers
                headers = header_format["headers"].copy()
                for key, value in headers.items():
                    if value is None:
                        headers[key] = signature
                
                print(f"   🔐 Signature Method: {sig_method['name']}")
                print(f"   📝 Signature: {signature[:20]}...")
                
                # Make request
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS! Status: {response.status_code}")
                    data = response.json()
                    print(f"   📄 Response: {json.dumps(data, indent=2)[:100]}...")
                    return True  # Found working combination
                elif response.status_code == 401:
                    print(f"   ❌ 401 Unauthorized")
                    # Try to get error details
                    try:
                        error_data = response.json()
                        print(f"   📄 Error: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"   📄 Error: {response.text[:100]}")
                elif response.status_code == 404:
                    print(f"   ❌ 404 Not Found")
                else:
                    print(f"   ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    return False

def test_curl_equivalent():
    """Test with curl-like minimal headers"""
    
    print("\n" + "=" * 60)
    print("🔧 Testing with curl-equivalent headers")
    print("=" * 60)
    
    api_key = FIRI_CONFIG['api_key']
    client_id = FIRI_CONFIG['client_id']
    secret = FIRI_CONFIG['secret']
    base_url = FIRI_CONFIG['base_url']
    
    # Get server time
    try:
        time_response = requests.get(f"{base_url}/time")
        server_time = time_response.json().get('time') if time_response.status_code == 200 else int(time.time())
    except:
        server_time = int(time.time())
    
    # Generate signature using current method
    message = f"{secret}60{server_time}{client_id}"
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Minimal headers (like curl would use)
    headers = {
        'X-API-Key': api_key,
        'X-Client-ID': client_id,
        'X-Signature': signature,
        'X-Timestamp': str(server_time),
        'X-Validity': '60'
    }
    
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"👤 Client ID: {client_id}")
    print(f"⏰ Timestamp: {server_time}")
    print(f"🔐 Signature: {signature[:20]}...")
    print(f"📝 Message: {message[:50]}...")
    
    # Test with orders endpoint
    url = f"{base_url}/v1/orders"
    print(f"\n🌐 Testing URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            data = response.json()
            print(f"📄 Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    success = test_different_auth_formats()
    if not success:
        test_curl_equivalent() 