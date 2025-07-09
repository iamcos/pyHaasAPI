#!/usr/bin/env python3
"""
Raw History Status Test - see actual API response
"""

import json
import requests
from pyHaasAPI import api

def main():
    """Test to see the raw API response"""
    print("🔍 Testing Raw History Status API Response...")
    
    # Authenticate
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="garrypotterr@gmail.com",
        password="IQYTCQJIQYTCQJ"
    )
    print("✅ Authenticated!")
    
    # Make raw request to see actual response
    url = "http://127.0.0.1:8090/SetupAPI.php"
    params = {
        "channel": "GET_HISTORY_STATUS",
        "interfacekey": executor.state.interface_key,
        "userid": executor.state.user_id
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        raw_data = response.json()
        print(f"📊 Raw API Response:")
        print(json.dumps(raw_data, indent=2))
        
        # Check if it has Success/Error/Data structure
        if 'Success' in raw_data:
            print(f"\n✅ Success: {raw_data['Success']}")
            print(f"❌ Error: {raw_data.get('Error', 'None')}")
            print(f"📊 Data keys: {list(raw_data.get('Data', {}).keys())}")
            
            if raw_data.get('Data'):
                print(f"📊 Number of markets in Data: {len(raw_data['Data'])}")
                # Show first few markets
                for i, (market, info) in enumerate(raw_data['Data'].items()):
                    if i < 3:
                        print(f"  {market}: {info}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 