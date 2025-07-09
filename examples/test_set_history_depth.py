#!/usr/bin/env python3
"""
Test Set History Depth

This script tests the set_history_depth function with a single market
to verify it works before running the bulk operation.
"""

from pyHaasAPI import api


def main():
    """Test set_history_depth with a single market"""
    print("🧪 Testing Set History Depth...")
    
    # Initialize and authenticate
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="your_email@example.com",
        password="your_password"
    )
    print("✅ Authenticated!")
    
    try:
        # Get current history status
        print("\n📋 Getting current history status...")
        history_status = api.get_history_status(executor)
        
        if not history_status:
            print("❌ No markets found!")
            return
        
        # Pick the first market for testing
        test_market = list(history_status.keys())[0]
        current_info = history_status[test_market]
        current_months = current_info.get('MaxMonths', 0)
        
        print(f"📊 Testing with market: {test_market}")
        print(f"📊 Current months: {current_months}")
        
        # Test setting to a different value
        test_months = 3
        print(f"\n🔄 Setting {test_market} to {test_months} months...")
        
        success = api.set_history_depth(executor, test_market, test_months)
        
        if success:
            print("✅ Success! History depth set successfully")
            
            # Check if it was actually updated
            print("\n📋 Checking updated status...")
            updated_status = api.get_history_status(executor)
            updated_info = updated_status.get(test_market, {})
            updated_months = updated_info.get('MaxMonths', 0)
            
            print(f"📊 Updated months: {updated_months}")
            
            if updated_months == test_months:
                print("✅ Confirmed: History depth was updated correctly!")
            else:
                print(f"⚠️  Note: Expected {test_months} but got {updated_months}")
        else:
            print("❌ Failed to set history depth")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main() 