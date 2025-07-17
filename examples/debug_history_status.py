#!/usr/bin/env python3
"""
Debug History Status - see raw API response
"""

import json
import requests
from pyHaasAPI import api

def main():
    """Debug the history status API call"""
    print("🔍 Debugging History Status API...")
    
    # Initialize and authenticate using the API
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    
    print(f"✅ Authenticated - User ID: {executor.state.user_id}")
    print(f"✅ Interface Key: {executor.state.interface_key}")
    
    # Make the raw request to see what's happening
    url = "http://127.0.0.1:8090/SetupAPI.php"
    params = {
        "channel": "GET_HISTORY_STATUS",
        "interfacekey": executor.state.interface_key,
        "userid": executor.state.user_id
    }
    
    print(f"🔗 Making request to: {url}")
    print(f"📋 Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        
        data = response.json()
        print(f"📊 Raw response: {json.dumps(data, indent=2)}")
        
        # Try the API function too
        print("\n🔍 Testing API function...")
        history_status = api.get_history_status(executor)
        print(f"📊 API function result: {history_status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 