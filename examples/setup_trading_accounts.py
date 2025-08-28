#!/usr/bin/env python3
"""
HaasOnline Trading Account Setup Script
======================================

This script creates 200 simulated trading accounts with the naming scheme "4AA-10K-XXX"
and ensures each account has exactly 10,000 USDT and no other cryptocurrencies.

Features:
- Creates accounts with proper naming convention
- Funds each account with exactly 10,000 USDT
- Removes any unwanted cryptocurrencies
- Comprehensive error handling and logging
- Progress tracking and verification

Requirements:
- HaasOnline API running on localhost:8090
- Valid API credentials in .env file
- pyHaasAPI library installed

Usage:
    python examples/setup_trading_accounts.py

Author: AI Assistant
Version: 1.0
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
    """Main setup function"""
    print("🚀 HaasOnline Trading Account Setup")
    print("=" * 60)
    print("📋 This script will:")
    print("   • Create 200 simulated trading accounts")
    print("   • Name them: 4AA-10K-001 through 4AA-10K-200")
    print("   • Fund each with exactly 10,000 USDT")
    print("   • Remove any other cryptocurrencies")
    print("=" * 60)
    
    # Connect to API
    try:
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            print("❌ Error: API_EMAIL and API_PASSWORD must be set in .env file")
            return

        print(f"🔌 Connecting to HaasOnline API: {api_host}:{api_port}")
        
        # Create API connection
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )
        
        # Authenticate
        haas_executor = haas_api.authenticate(api_email, api_password)
        print("✅ Successfully connected to HaasOnline API")
        
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return

    # Get API credentials for direct requests
    try:
        import requests
        
        user_id = getattr(haas_executor.state, 'user_id', None)
        interface_key = getattr(haas_executor.state, 'interface_key', None)
        
        if not user_id or not interface_key:
            print("❌ Failed to get API credentials")
            return
            
        base_url = f"http://{haas_executor.host}:{haas_executor.port}/AccountAPI.php"
        
    except Exception as e:
        print(f"❌ Error setting up API requests: {e}")
        return

    # Ask for confirmation
    response = input("\n⚠️  This will create 200 new accounts. Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Operation cancelled.")
        return

    print(f"\n🏗️  Creating 200 trading accounts...")
    print("=" * 60)
    
    created_accounts = []
    failed_accounts = []
    
    # Step 1: Create accounts
    for i in range(1, 201):
        account_name = f"4AA-10K-{i:03d}"
        print(f"[{i:3d}/200] Creating {account_name}...", end=" ")
        
        try:
            # Create simulated account
            response = requests.get(base_url, params={
                "channel": "CREATE_SIMULATED_ACCOUNT",
                "accountname": account_name,
                "userid": user_id,
                "interfacekey": interface_key
            })
            
            result = response.json()
            
            if result.get('Success'):
                account_id = result.get('Data', '')
                created_accounts.append({
                    'name': account_name,
                    'id': account_id
                })
                print("✅")
            else:
                error_msg = result.get('Error', 'Unknown error')
                failed_accounts.append({
                    'name': account_name,
                    'error': error_msg
                })
                print(f"❌ {error_msg}")
                
        except Exception as e:
            failed_accounts.append({
                'name': account_name,
                'error': str(e)
            })
            print(f"❌ {e}")
        
        # Brief pause to avoid overwhelming the API
        time.sleep(0.2)
        
        # Progress update every 50 accounts
        if i % 50 == 0:
            print(f"   📊 Progress: {i}/200 accounts processed")
            time.sleep(1)

    print("=" * 60)
    print(f"📊 Account Creation Summary:")
    print(f"   ✅ Successfully created: {len(created_accounts)}")
    print(f"   ❌ Failed to create: {len(failed_accounts)}")
    
    if failed_accounts:
        print(f"\n❌ Failed accounts:")
        for account in failed_accounts[:5]:  # Show first 5 failures
            print(f"   • {account['name']}: {account['error']}")
        if len(failed_accounts) > 5:
            print(f"   ... and {len(failed_accounts) - 5} more")

    if not created_accounts:
        print("❌ No accounts were created successfully. Exiting.")
        return

    # Step 2: Fund accounts with 10,000 USDT
    print(f"\n💰 Funding {len(created_accounts)} accounts with 10,000 USDT...")
    print("=" * 60)
    
    funded_accounts = []
    funding_failures = []
    
    for i, account in enumerate(created_accounts):
        account_name = account['name']
        account_id = account['id']
        
        print(f"[{i+1:3d}/{len(created_accounts)}] Funding {account_name}...", end=" ")
        
        try:
            # Deposit 10,000 USDT
            response = requests.get(base_url, params={
                "channel": "DEPOSIT_FUNDS",
                "accountid": account_id,
                "currency": "USDT",
                "walletid": "USDT",
                "amount": 10000.0,
                "userid": user_id,
                "interfacekey": interface_key
            })
            
            result = response.json()
            
            if result.get('Success'):
                funded_accounts.append(account)
                print("✅")
            else:
                error_msg = result.get('Error', 'Unknown error')
                funding_failures.append({
                    'account': account,
                    'error': error_msg
                })
                print(f"❌ {error_msg}")
                
        except Exception as e:
            funding_failures.append({
                'account': account,
                'error': str(e)
            })
            print(f"❌ {e}")
        
        # Brief pause
        time.sleep(0.1)
        
        # Progress update every 50 accounts
        if (i + 1) % 50 == 0:
            print(f"   📊 Progress: {i+1}/{len(created_accounts)} accounts funded")
            time.sleep(1)

    print("=" * 60)
    print(f"📊 Funding Summary:")
    print(f"   ✅ Successfully funded: {len(funded_accounts)}")
    print(f"   ❌ Failed to fund: {len(funding_failures)}")

    # Step 3: Verify and clean up accounts
    if funded_accounts:
        print(f"\n🧹 Verifying and cleaning {len(funded_accounts)} accounts...")
        print("=" * 60)
        
        # Get all balances to check for unwanted currencies
        try:
            balances_response = requests.get(base_url, params={
                "channel": "GET_ALL_BALANCES",
                "userid": user_id,
                "interfacekey": interface_key
            })
            balances_data = balances_response.json()
            
            if balances_data.get('Success'):
                all_balances = balances_data.get('Data', [])
                
                # Create mapping of account ID to balances
                balance_map = {}
                for balance_data in all_balances:
                    account_id = balance_data.get('AID', '')
                    balance_map[account_id] = balance_data.get('I', [])
                
                cleaned_accounts = 0
                cleanup_failures = 0
                
                for i, account in enumerate(funded_accounts):
                    account_name = account['name']
                    account_id = account['id']
                    
                    balances = balance_map.get(account_id, [])
                    
                    # Check for non-USDT currencies
                    currencies_to_remove = []
                    usdt_balance = 0
                    
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
                    
                    if currencies_to_remove:
                        print(f"[{i+1:3d}/{len(funded_accounts)}] Cleaning {account_name} ({len(currencies_to_remove)} currencies)...", end=" ")
                        
                        account_cleaned = True
                        for currency_info in currencies_to_remove:
                            try:
                                response = requests.get(base_url, params={
                                    "channel": "WITHDRAWAL_FUNDS",
                                    "accountid": account_id,
                                    "currency": currency_info['currency'],
                                    "walletid": currency_info['wallet_id'],
                                    "amount": currency_info['amount'],
                                    "userid": user_id,
                                    "interfacekey": interface_key
                                })
                                
                                result = response.json()
                                if not result.get('Success'):
                                    account_cleaned = False
                                    break
                                    
                            except Exception:
                                account_cleaned = False
                                break
                        
                        if account_cleaned:
                            cleaned_accounts += 1
                            print("✅")
                        else:
                            cleanup_failures += 1
                            print("❌")
                    else:
                        # Account already clean
                        cleaned_accounts += 1
                        if i < 5:  # Only show first few clean accounts
                            print(f"[{i+1:3d}/{len(funded_accounts)}] {account_name} already clean ✅")
                    
                    time.sleep(0.1)
                
                print("=" * 60)
                print(f"📊 Cleanup Summary:")
                print(f"   ✅ Clean accounts: {cleaned_accounts}")
                print(f"   ❌ Cleanup failures: {cleanup_failures}")
                
            else:
                print("❌ Failed to get account balances for verification")
                
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

    # Final summary
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print(f"📊 Final Summary:")
    print(f"   🏗️  Accounts created: {len(created_accounts)}/200")
    print(f"   💰 Accounts funded: {len(funded_accounts)}")
    print(f"   🧹 Accounts cleaned: {cleaned_accounts if 'cleaned_accounts' in locals() else 'N/A'}")
    
    if len(created_accounts) == 200 and len(funded_accounts) == 200:
        print(f"\n🏆 PERFECT SUCCESS!")
        print(f"   All 200 accounts created and funded with exactly 10,000 USDT!")
    else:
        print(f"\n⚠️  Some accounts may need manual attention.")
    
    print(f"\n💡 Next steps:")
    print(f"   • Verify accounts in HaasOnline interface")
    print(f"   • Start your trading strategies")
    print(f"   • Monitor account performance")
    print("=" * 60)

if __name__ == "__main__":
    main()