#!/usr/bin/env python3
"""
Simple History Status Test using pyHaasAPI
"""

import json
from pyHaasAPI import api

def main():
    """Simple test to get history status using the API"""
    print("🔍 Testing History Status API...")
    
    # Initialize and authenticate using the API
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    
    try:
        # Use the existing API function
        history_status = api.get_history_status(executor)
        
        print(f"✅ Response received: {len(history_status)} markets")
        
        # Show the first few markets
        print("\n📊 Sample Markets:")
        for i, (market, info) in enumerate(history_status.items()):
            if i < 5:  # Show first 5
                print(f"  {market}: {info}")
        
        # Save full response
        with open('simple_history_status.json', 'w') as f:
            json.dump(history_status, f, indent=2)
        print(f"\n💾 Full response saved to: simple_history_status.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 