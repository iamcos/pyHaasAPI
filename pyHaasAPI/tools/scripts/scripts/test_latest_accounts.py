#!/usr/bin/env python3
"""
Test Latest Account Types
------------------------
Tests the most recently discovered account types.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from config import settings
from pyHaasAPI import api
from pyHaasAPI.exceptions import HaasApiError
import time

def test_account_type(executor, driver_code: str, driver_type: int, name: str = None):
    """Test creating and deleting a specific account type"""
    if name is None:
        name = f"Test {driver_code}"
    
    print(f"🧪 Testing: {driver_code} (Type {driver_type})")
    
    try:
        # Create account
        result = api.add_simulated_account(
            executor,
            name=name,
            driver_code=driver_code,
            driver_type=driver_type
        )
        
        if result and hasattr(result, 'account_id'):
            account_id = result.account_id
            print(f"  ✅ SUCCESS! Created account: {account_id}")
            
            # Get account details
            time.sleep(2)  # Wait for account to be fully created
            accounts = api.get_accounts(executor)
            account = next((acc for acc in accounts if acc.account_id == account_id), None)
            
            if account:
                print(f"  📊 Account Details:")
                print(f"     Name: {account.name}")
                print(f"     Exchange: {account.exchange_code}")
                print(f"     Type: {account.exchange_type}")
                print(f"     Simulated: {account.is_simulated}")
                print(f"     Test Net: {account.is_test_net}")
            
            # Delete account
            time.sleep(1)
            delete_result = api.delete_account(executor, account_id)
            if delete_result:
                print(f"  🗑️ Deleted test account")
            else:
                print(f"  ⚠️ Failed to delete account")
            
            return True, result
            
    except HaasApiError as e:
        print(f"  ❌ FAILED: API Error - {e}")
        return False, str(e)
    except Exception as e:
        print(f"  ❌ FAILED: Unexpected error - {e}")
        return False, str(e)

def main():
    """Main function"""
    print("🚀 Testing Latest Account Types")
    print("=" * 40)
    
    # Authenticate
    print("🔐 Authenticating...")
    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Test the latest account types discovered by user
    print("\n🧪 Testing Latest Account Types:")
    print("-" * 40)
    
    latest_account_types = [
        ("PHEMEXCONTRACTS", 2, "Phemex Contracts"),
        ("POLONIEX", 0, "Poloniex"),
        ("POLONIEXFUTURES", 2, "Poloniex Futures"),
        ("WOOX", 0, "WOOX"),
        ("WOOXFUTURES", 2, "WOOX Futures"),
    ]
    
    working_types = []
    
    for driver_code, driver_type, name in latest_account_types:
        success, result = test_account_type(executor, driver_code, driver_type, name)
        if success:
            working_types.append((driver_code, driver_type, name))
        print()  # Empty line for readability
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print("=" * 40)
    print("📋 SUMMARY")
    print("=" * 40)
    print(f"✅ Working latest account types: {len(working_types)}")
    print(f"❌ Failed latest account types: {len(latest_account_types) - len(working_types)}")
    
    if working_types:
        print("\n🎉 Latest Working Account Types:")
        for driver_code, driver_type, name in working_types:
            print(f"  - {driver_code} (Type {driver_type}): {name}")
        
        print("\n💡 Usage Example:")
        print("```python")
        print("from pyHaasAPI import api")
        print("")
        print("# Create a latest account type")
        print("result = api.add_simulated_account(")
        print("    executor,")
        print("    name='My Latest Account',")
        print(f"    driver_code='{working_types[0][0]}',")
        print(f"    driver_type={working_types[0][1]}")
        print(")")
        print("```")
    else:
        print("\n😞 No latest working account types found.")

if __name__ == "__main__":
    main() 