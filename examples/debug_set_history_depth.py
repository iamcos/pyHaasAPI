#!/usr/bin/env python3
"""
Debug Set History Depth Response
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import requests
import json
from pyHaasAPI import api

def main():
    """Debug the set_history_depth API response"""
    print("🔍 Debugging Set History Depth Response...")
    
    # Authenticate
    executor = api.RequestsExecutor(
        host=os.getenv("HAAS_API_HOST"),
        port=int(os.getenv("HAAS_API_PORT")),
        state=api.Guest()
    ).authenticate(
        email=os.getenv("HAAS_API_EMAIL"),
        password=os.getenv("HAAS_API_PASSWORD")
    )
    print("✅ Authenticated!")
    
    # Get a test market
    history_status = api.get_history_status(executor)
    test_market = list(history_status.keys())[0]
    
    print(f"📊 Testing with market: {test_market}")
    
    # Make raw request to see actual response
    url = "http://127.0.0.1:8090/SetupAPI.php"
    params = {
        "channel": "SET_HISTORY_DEPTH",
        "market": test_market,
        "monthdepth": 8,
        "interfacekey": executor.state.interface_key,
        "userid": executor.state.user_id
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        raw_data = response.json()
        print(f"📊 Raw API Response:")
        print(json.dumps(raw_data, indent=2))
        
        # Test the API function
        print(f"\n🔍 Testing API function...")
        try:
            success = api.set_history_depth(executor, test_market, 8)
            print(f"📊 API function result: {success}")
        except Exception as e:
            print(f"❌ API function error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 