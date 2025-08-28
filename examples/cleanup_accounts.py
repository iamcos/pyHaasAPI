#!/usr/bin/env python3
"""
HaasOnline Account Cleanup Script
================================

This script cleans up trading accounts to ensure they have ONLY 10,000 USDT:
- Removes all non-USDT cryptocurrencies
- Adjusts USDT balance to exactly 10,000
- Provides detailed progress reporting

Usage:
    python examples/cleanup_accounts.py
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api

def main():
    """Main cleanup function"""
    print("🧹 HaasOnline Account Cleanup")
    print("=" * 50)
    print("This script will ensure all accounts have ONLY 10,000 USDT")
    
    # Connect to API
    try:
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        print(f"🔌 Connecting to API: {api_host}:{api_port}")
        
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )
        
        haas_executor = haas_api.authenticate(api_email, api_password)
        print("✅ Connected successfully")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # Get account balances
    try:
        import requests
        
        user_id = getattr(haas_executor.state, 'user_id', None)
        interface_key = getattr(haas_executor.state, 'interface_key', None)
        
        url = f"http://{haas_executor.host}:{haas_executor.port}/AccountAPI.php"
        
        response = requests.get(url, params={
            "channel": "GET_ALL_BALANCES",
            "userid": user_id,
            "interfacekey": interface_key
        })
        
        data = response.json()
        if not data.get('Success'):
            print(f"❌ Failed to get balances: {data.get('Error')}")
            return
            
        accounts = data.get('Data', [])
        
    except Exception as e:
        print(f"❌ Error getting balances: {e}")
        return

    # Find accounts that need cleanup
    accounts_to_clean = []
    
    for i, account_data in enumerate(accounts):
        account_id = account_data.get('AID', '')
        balances = account_data.get('I', [])
        account_name = f"Account-{i+1:03d}"
        
        usdt_balance = 0
        currencies_to_remove = []
        
        for balance in balances:
            currency = balance.get('C', '')
            amount = float(balance.get('A', 0))
            
            if currency == 'USDT':
                usdt_balance = amount
            elif amount > 0:
                currencies_to_remove.append({
                    'currency': currency,
                    'amount': amount,
                    'wallet_id': balance.get('WT', currency)
                })
        
        # Check if account needs cleaning
        needs_usdt_adjustment = abs(usdt_balance - 10000.0) >= 0.01
        needs_currency_removal = len(currencies_to_remove) > 0
        
        if needs_usdt_adjustment or needs_currency_removal:
            accounts_to_clean.append({
                'name': account_name,
                'id': account_id,
                'usdt_balance': usdt_balance,
                'currencies_to_remove': currencies_to_remove,
                'needs_usdt_adjustment': needs_usdt_adjustment
            })

    print(f"📊 Found {len(accounts_to_clean)} accounts that need cleanup")
    
    if not accounts_to_clean:
        print("✅ All accounts are already clean!")
        return

    # Show what will be done
    total_operations = 0
    for account in accounts_to_clean:
        total_operations += len(account['currencies_to_remove'])
        if account['needs_usdt_adjustment']:
            total_operations += 1
    
    print(f"📋 Cleanup plan:")
    print(f"   🗑️  Remove {sum(len(acc['currencies_to_remove']) for acc in accounts_to_clean)} currency balances")
    print(f"   💰 Adjust USDT in {sum(1 for acc in accounts_to_clean if acc['needs_usdt_adjustment'])} accounts")
    print(f"   🔧 Total operations: {total_operations}")

    # Ask for confirmation
    response = input(f"\nProceed with cleanup? (y/N): ").strip().lower()
    if response != 'y':
        print("Cleanup cancelled.")
        return

    # Perform cleanup
    print(f"\n🧹 Cleaning {len(accounts_to_clean)} accounts...")
    print("=" * 50)
    
    success_count = 0
    failure_count = 0
    
    for i, account in enumerate(accounts_to_clean):
        account_name = account['name']
        account_id = account['id']
        
        print(f"[{i+1:3d}/{len(accounts_to_clean)}] Cleaning {account_name}...")
        
        account_success = True
        
        # Remove unwanted currencies
        for currency_info in account['currencies_to_remove']:
            currency = currency_info['currency']
            amount = currency_info['amount']
            wallet_id = currency_info['wallet_id']
            
            print(f"   🗑️  Removing {currency}: {amount:,.8f}...", end=" ")
            
            try:
                response = requests.get(url, params={
                    "channel": "WITHDRAWAL_FUNDS",
                    "accountid": account_id,
                    "currency": currency,
                    "walletid": wallet_id,
                    "amount": amount,
                    "userid": user_id,
                    "interfacekey": interface_key
                })
                
                result = response.json()
                if result.get('Success'):
                    print("✅")
                else:
                    print(f"❌ {result.get('Error', 'Unknown error')}")
                    account_success = False
                    
            except Exception as e:
                print(f"❌ {e}")
                account_success = False
            
            time.sleep(0.1)
        
        # Adjust USDT balance if needed
        if account['needs_usdt_adjustment']:
            current_usdt = account['usdt_balance']
            target_usdt = 10000.0
            difference = target_usdt - current_usdt
            
            if difference > 0:
                print(f"   💰 Adding {difference:,.0f} USDT...", end=" ")
                channel = "DEPOSIT_FUNDS"
                amount = difference
            else:
                print(f"   💰 Removing {abs(difference):,.0f} USDT...", end=" ")
                channel = "WITHDRAWAL_FUNDS"
                amount = abs(difference)
            
            try:
                response = requests.get(url, params={
                    "channel": channel,
                    "accountid": account_id,
                    "currency": "USDT",
                    "walletid": "USDT",
                    "amount": amount,
                    "userid": user_id,
                    "interfacekey": interface_key
                })
                
                result = response.json()
                if result.get('Success'):
                    print("✅")
                else:
                    print(f"❌ {result.get('Error', 'Unknown error')}")
                    account_success = False
                    
            except Exception as e:
                print(f"❌ {e}")
                account_success = False
        
        if account_success:
            success_count += 1
            print(f"   ✅ {account_name} cleaned successfully")
        else:
            failure_count += 1
            print(f"   ❌ {account_name} had failures")
        
        time.sleep(0.5)

    # Final summary
    print("=" * 50)
    print(f"🎉 Cleanup Complete!")
    print(f"📊 Results:")
    print(f"   ✅ Successfully cleaned: {success_count}")
    print(f"   ❌ Failed to clean: {failure_count}")
    print(f"   📊 Total processed: {len(accounts_to_clean)}")
    
    if success_count == len(accounts_to_clean):
        print(f"\n🏆 PERFECT! All accounts now have exactly 10,000 USDT!")
    elif success_count > 0:
        print(f"\n🎯 {success_count} accounts successfully cleaned!")
        if failure_count > 0:
            print(f"⚠️  {failure_count} accounts may need manual attention.")
    
    print(f"\n💡 Next step: Run verify_accounts.py to confirm results")

if __name__ == "__main__":
    main()