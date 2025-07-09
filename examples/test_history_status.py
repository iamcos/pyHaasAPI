#!/usr/bin/env python3
"""
Test History Status using same auth pattern as example
"""

import json
from pyHaasAPI import api

def main():
    """Test history status using the same auth pattern"""
    print("🔍 Testing History Status with example auth pattern...")
    
    # Use the same authentication pattern as the example
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="garrypotterr@gmail.com",
        password="IQYTCQJIQYTCQJ"
    )
    print("✅ Authenticated!")
    
    try:
        # Get history status
        history_status = api.get_history_status(executor)
        
        print(f"📊 Response received: {len(history_status)} markets")
        
        if history_status:
            print("\n📋 Sample Markets:")
            for i, (market, info) in enumerate(history_status.items()):
                if i < 5:  # Show first 5
                    print(f"  {market}: {info}")
        else:
            print("❌ No markets returned")
        
        # Save response
        with open('test_history_status.json', 'w') as f:
            json.dump(history_status, f, indent=2)
        print(f"\n💾 Response saved to: test_history_status.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 