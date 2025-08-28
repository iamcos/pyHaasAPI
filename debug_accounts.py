#!/usr/bin/env python3
"""
Debug script to examine account balances API response
"""

import os
import sys
from typing import Dict, List, Any

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import pyHaasAPI components
from pyHaasAPI import api

def debug_account_balances():
    """Debug the account balances API response"""
    print("🔍 Debugging account balances API response")
    print("=" * 60)

    try:
        # Initialize executor
        print("🔐 Authenticating with HaasOnline API...")
        executor = api.RequestsExecutor(
            host=os.getenv("API_HOST", "127.0.0.1"),
            port=int(os.getenv("API_PORT", 8090)),
            state=api.Guest()
        )

        executor = executor.authenticate(
            email=os.getenv("API_EMAIL", ""),
            password=os.getenv("API_PASSWORD", "")
        )

        print("✅ Authentication successful!")

        # Test account balances API
        print("\n📊 Testing account balances API...")
        accounts_data = api.get_all_account_balances(executor)

        print(f"Response type: {type(accounts_data)}")
        print(f"Response length (if list): {len(accounts_data) if isinstance(accounts_data, list) else 'N/A'}")

        # Check if it's a list
        if isinstance(accounts_data, list):
            print(f"✅ Response is a list with {len(accounts_data)} items")

            if len(accounts_data) > 0:
                print("\n🔍 Examining first account:")
                first_account = accounts_data[0]
                print(f"  Type: {type(first_account)}")
                print(f"  Attributes: {dir(first_account) if hasattr(first_account, '__dict__') else 'No __dict__'}")

                # Try to access common attributes
                print("\n  Trying to access common attributes:")
                attrs_to_try = ['account_id', 'name', 'balance', 'exchange', 'success', 'data']
                for attr in attrs_to_try:
                    try:
                        value = getattr(first_account, attr, 'NOT_FOUND')
                        print(f"    {attr}: {value} ({type(value).__name__})")
                    except Exception as e:
                        print(f"    {attr}: ERROR - {e}")

                # Print raw data if available
                if hasattr(first_account, '__dict__'):
                    print(f"\n  Raw __dict__: {first_account.__dict__}")
                elif hasattr(first_account, 'data'):
                    print(f"  Raw data: {first_account.data}")
                else:
                    print(f"\n  Raw dict content: {first_account}")

                # Show all keys in the dictionary
                if isinstance(first_account, dict):
                    print(f"\n  All keys: {list(first_account.keys())}")
                    print("\n  Sample values:")
                    for key in list(first_account.keys())[:10]:  # Show first 10 keys
                        value = first_account[key]
                        print(f"    {key}: {value} ({type(value).__name__})")

        else:
            print(f"❌ Response is not a list: {type(accounts_data)}")

            # Check if it has success/data attributes
            if hasattr(accounts_data, 'success'):
                print(f"  Has 'success' attribute: {accounts_data.success}")
            if hasattr(accounts_data, 'data'):
                print(f"  Has 'data' attribute: {type(accounts_data.data)}")
                if isinstance(accounts_data.data, list):
                    print(f"    Data is list with {len(accounts_data.data)} items")
            if hasattr(accounts_data, '__dict__'):
                print(f"  Raw __dict__: {accounts_data.__dict__}")

        print("\n" + "=" * 60)
        print("Debug complete!")

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_account_balances()
