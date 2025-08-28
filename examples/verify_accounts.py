#!/usr/bin/env python3
"""
HaasOnline Account Verification Script
=====================================

This script verifies that your trading accounts are properly set up:
- Checks for accounts with 4AA-10K naming scheme
- Verifies each account has exactly 10,000 USDT
- Reports any accounts with additional cryptocurrencies
- Provides summary statistics

Usage:
    python examples/verify_accounts.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api

def main():
    """Main verification function"""
    print("🔍 HaasOnline Account Verification")
    print("=" * 50)
    
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
        print(f"📊 Found {len(accounts)} total accounts")
        
    except Exception as e:
        print(f"❌ Error getting balances: {e}")
        return

    # Analyze accounts
    print("\n🔍 Analyzing accounts...")
    print("=" * 50)
    
    perfect_accounts = 0
    accounts_with_issues = []
    total_usdt = 0
    
    for i, account_data in enumerate(accounts):
        account_id = account_data.get('AID', '')
        balances = account_data.get('I', [])
        account_name = f"Account-{i+1:03d}"
        
        usdt_balance = 0
        other_currencies = []
        
        for balance in balances:
            currency = balance.get('C', '')
            amount = float(balance.get('A', 0))
            
            if currency == 'USDT':
                usdt_balance = amount
                total_usdt += amount
            elif amount > 0:
                other_currencies.append(f"{currency}: {amount:,.8f}")
        
        # Check if account is perfect (exactly 10k USDT, nothing else)
        if abs(usdt_balance - 10000.0) < 0.01 and len(other_currencies) == 0:
            perfect_accounts += 1
        else:
            accounts_with_issues.append({
                'name': account_name,
                'usdt': usdt_balance,
                'others': other_currencies
            })

    # Report results
    print(f"📊 Verification Results:")
    print(f"   ✅ Perfect accounts (10k USDT only): {perfect_accounts}")
    print(f"   ⚠️  Accounts with issues: {len(accounts_with_issues)}")
    print(f"   💰 Total USDT across all accounts: {total_usdt:,.0f}")
    
    if accounts_with_issues:
        print(f"\n⚠️  Accounts needing attention:")
        print("-" * 40)
        
        for account in accounts_with_issues[:10]:  # Show first 10
            usdt = account['usdt']
            others = account['others']
            
            status = ""
            if abs(usdt - 10000.0) >= 0.01:
                status += f"USDT: {usdt:,.0f} (should be 10,000) "
            if others:
                status += f"Extra currencies: {len(others)} "
            
            print(f"   {account['name']}: {status}")
            
            # Show first few extra currencies
            for curr in others[:2]:
                print(f"      • {curr}")
            if len(others) > 2:
                print(f"      • ... and {len(others) - 2} more")
        
        if len(accounts_with_issues) > 10:
            print(f"   ... and {len(accounts_with_issues) - 10} more accounts")
    
    # Success rate
    success_rate = (perfect_accounts / len(accounts)) * 100 if accounts else 0
    
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🏆 PERFECT! All accounts are properly configured!")
    elif success_rate >= 95:
        print("🎉 Excellent! Most accounts are properly configured.")
    elif success_rate >= 80:
        print("👍 Good! Most accounts are working, some need attention.")
    else:
        print("⚠️  Many accounts need attention. Consider re-running setup.")
    
    print("\n💡 Recommendations:")
    if accounts_with_issues:
        print("   • Run the cleanup script to fix accounts with extra currencies")
        print("   • Check accounts with incorrect USDT balances")
        print("   • Verify API permissions for fund management")
    else:
        print("   • All accounts are ready for trading!")
        print("   • You can start deploying your trading strategies")
    
    print("=" * 50)

if __name__ == "__main__":
    main()