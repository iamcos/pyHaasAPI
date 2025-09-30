#!/usr/bin/env python3
"""
Quick Account Type Test
-----------------------
Quickly test specific account types to see what's available.

This script tests the account type mentioned in the user query:
- BINANCEQUARTERLY with driver_type=2

Plus a few other common combinations to get immediate results.

Run with: python scripts/market_data/quick_account_test.py
"""

import os
import sys
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables first

from config import settings
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.exceptions import HaasApiError

def test_account_type(executor, driver_code: str, driver_type: int, name: str = None):
    """Test a specific account type"""
    if name is None:
        name = f"Test_{driver_code}_{driver_type}"
    
    print(f"🧪 Testing: {driver_code} (Type {driver_type})")
    
    try:
        # Try to create a simulated account
        result = api.add_simulated_account(
            executor,
            name=name,
            driver_code=driver_code,
            driver_type=driver_type
        )
        
        if result and "AID" in result:
            account_id = result["AID"]
            print(f"  ✅ SUCCESS! Created account: {account_id}")
            
            # Get account details
            try:
                accounts = api.get_accounts(executor)
                new_account = next((acc for acc in accounts if acc.account_id == account_id), None)
                if new_account:
                    print(f"  📊 Account Details:")
                    print(f"     Name: {new_account.name}")
                    print(f"     Exchange: {new_account.exchange_code}")
                    print(f"     Type: {new_account.exchange_type}")
                    print(f"     Simulated: {new_account.is_simulated}")
                    print(f"     Test Net: {new_account.is_test_net}")
            except Exception as e:
                print(f"  ⚠️ Could not get account details: {e}")
            
            # Clean up - delete the test account
            try:
                api.delete_account(executor, account_id)
                print(f"  🗑️ Deleted test account")
            except Exception as e:
                print(f"  ⚠️ Could not delete test account: {e}")
            
            return True, result
            
        else:
            print(f"  ❌ FAILED: API returned success but no account ID")
            print(f"     Response: {result}")
            return False, result
            
    except HaasApiError as e:
        print(f"  ❌ FAILED: API Error - {e}")
        return False, str(e)
    except Exception as e:
        print(f"  ❌ FAILED: Unexpected error - {e}")
        return False, str(e)

def main():
    """Main function"""
    print("🚀 Quick Account Type Test")
    print("=" * 40)
    
    # Environment variables already loaded at module level
    
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
    
    # Get existing accounts first
    print("\n📊 Current accounts:")
    try:
        accounts = api.get_accounts(executor)
        print(f"Found {len(accounts)} existing accounts:")
        for account in accounts:
            print(f"  - {account.name} ({account.exchange_code}, Type {account.exchange_type})")
    except Exception as e:
        print(f"❌ Error getting existing accounts: {e}")
    
    # Test specific account types
    print("\n🧪 Testing Account Types:")
    print("-" * 40)
    
    # Test all discovered account types
    test_cases = [
        # Binance family
        ("BINANCEQUARTERLY", 2, "Binance COINS"),  # From user's curl command
        ("BINANCE", 0, "Binance Spot"),
        ("BINANCE", 1, "Binance Futures"),
        ("BINANCE", 2, "Binance Quarterly"),
        ("BINANCEFUTURES", 2, "USDTFUTURES"),  # New from user's curl command
        
        # Bybit family
        ("BYBITSPOT", 0, "Bybit Spot"),
        ("BYBIT", 2, "Bybit"),
        ("BYBITUSDT", 2, "Bybit USDT"),
        
        # Bitget family
        ("BITGET", 0, "Bitget"),
        ("BITGETFUTURESUSDT", 2, "Bitget USDT Futures"),
        
        # Other exchanges
        ("BIT2ME", 0, "Bit2me"),  # New from user's curl command
        ("BITFINEX", 0, "Bitfinex"),  # Similar to Bit2me
        ("BITMEX", 2, "Bitmex"),
        ("KRAKEN", 0, "Kraken"),
        ("KRAKENFUTURES", 2, "Kraken Futures"),
        ("KUCOIN", 0, "KuCoin"),
        ("KUCOINFUTURES", 2, "KuCoin Futures"),
        ("OKEX", 0, "OKEx"),
        ("OKCOINFUTURES", 2, "OKCoin Futures"),
        ("OKEXSWAP", 2, "OKEx Swap"),
        ("PHEMEXCONTRACTS", 2, "Phemex Contracts"),
        ("POLONIEX", 0, "Poloniex"),
        ("POLONIEXFUTURES", 2, "Poloniex Futures"),
        ("WOOX", 0, "WOOX"),
        ("WOOXFUTURES", 2, "WOOX Futures"),
    ]
    
    working_types = []
    
    for driver_code, driver_type, name in test_cases:
        success, result = test_account_type(executor, driver_code, driver_type, name)
        if success:
            working_types.append((driver_code, driver_type, name))
        print()  # Empty line for readability
        time.sleep(1)  # Small delay between tests
    
    # Summary
    print("=" * 40)
    print("📋 SUMMARY")
    print("=" * 40)
    print(f"✅ Working account types: {len(working_types)}")
    print(f"❌ Failed account types: {len(test_cases) - len(working_types)}")
    
    if working_types:
        print("\n🎉 Working Account Types:")
        for driver_code, driver_type, name in working_types:
            print(f"  - {driver_code} (Type {driver_type}): {name}")
        
        print("\n💡 Usage Example:")
        print("```python")
        print("from pyHaasAPI_v1 import api")
        print("")
        print("# Create a simulated account")
        print("result = api.add_simulated_account(")
        print("    executor,")
        print("    name='My Account',")
        print(f"    driver_code='{working_types[0][0]}',")
        print(f"    driver_type={working_types[0][1]}")
        print(")")
        print("```")
    else:
        print("\n😞 No working account types found.")
        print("This might indicate:")
        print("  - Different driver codes/types on your server")
        print("  - API permissions issues")
        print("  - Server configuration differences")

if __name__ == "__main__":
    main() 