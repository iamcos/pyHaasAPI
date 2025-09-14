#!/usr/bin/env python3
"""
Test New Account Types
---------------------
Tests the newly discovered account types from user feedback.
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
    print("🚀 Testing New Account Types")
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
    
    # Test the new account types discovered by user
    print("\n🧪 Testing New Account Types:")
    print("-" * 40)
    
    new_account_types = [
        ("KRAKENFUTURES", 2, "Kraken Futures"),
        ("KUCOIN", 0, "KuCoin"),
        ("KUCOINFUTURES", 2, "KuCoin Futures"),
        ("OKEX", 0, "OKEx"),
        ("OKCOINFUTURES", 2, "OKCoin Futures"),
        ("OKEXSWAP", 2, "OKEx Swap"),
    ]
    
    working_types = []
    
    for driver_code, driver_type, name in new_account_types:
        success, result = test_account_type(executor, driver_code, driver_type, name)
        if success:
            working_types.append((driver_code, driver_type, name))
        print()  # Empty line for readability
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print("=" * 40)
    print("📋 SUMMARY")
    print("=" * 40)
    print(f"✅ Working new account types: {len(working_types)}")
    print(f"❌ Failed new account types: {len(new_account_types) - len(working_types)}")
    
    if working_types:
        print("\n🎉 New Working Account Types:")
        for driver_code, driver_type, name in working_types:
            print(f"  - {driver_code} (Type {driver_type}): {name}")
        
        print("\n💡 Usage Example:")
        print("```python")
        print("from pyHaasAPI import api")
        print("")
        print("# Create a new account type")
        print("result = api.add_simulated_account(")
        print("    executor,")
        print("    name='My New Account',")
        print(f"    driver_code='{working_types[0][0]}',")
        print(f"    driver_type={working_types[0][1]}")
        print(")")
        print("```")
    else:
        print("\n😞 No new working account types found.")

if __name__ == "__main__":
    main() 