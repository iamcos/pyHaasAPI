#!/usr/bin/env python3
"""
Check existing accounts and their details
"""

import requests
import json

MCP_SERVER_URL = "http://127.0.0.1:8000"

def get_all_accounts():
    """Get all existing accounts"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/get_all_accounts")
        if response.status_code == 200:
            data = response.json()
            if data.get("Success"):
                return data.get("Data", [])
        return []
    except Exception as e:
        print(f"Error getting accounts: {e}")
        return []

def get_account_balance(account_id: str):
    """Get account balance"""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/get_account_balance/{account_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("Success"):
                return data.get("Data")
        return None
    except Exception as e:
        print(f"Error getting balance for {account_id}: {e}")
        return None

def main():
    print("🔍 Checking existing accounts...")
    
    accounts = get_all_accounts()
    
    if not accounts:
        print("❌ No accounts found or server not accessible")
        return
    
    print(f"✅ Found {len(accounts)} accounts:")
    print()
    
    test_accounts = []
    
    for i, account in enumerate(accounts, 1):
        account_id = account.get("account_id", "N/A")
        account_name = account.get("name", "N/A")
        driver_type = account.get("driver_type", "N/A")
        
        print(f"{i:2d}. {account_name}")
        print(f"    ID: {account_id}")
        print(f"    Driver: {driver_type}")
        
        # Check if this looks like a test account
        if "test" in account_name.lower() or "тест" in account_name.lower() or "10к" in account_name:
            test_accounts.append(account)
            print(f"    🎯 POTENTIAL TEST ACCOUNT")
            
            # Get balance
            balance = get_account_balance(account_id)
            if balance:
                current_balance = balance.get("balance", 0)
                print(f"    💰 Balance: {current_balance}")
        
        print()
    
    if test_accounts:
        print(f"🎯 Found {len(test_accounts)} potential test accounts:")
        for account in test_accounts:
            print(f"  - {account.get('name')} ({account.get('account_id')})")
    else:
        print("⚠️  No test accounts found")
        print("💡 We may need to use an existing account or create one manually")
    
    # Show raw account data for debugging
    print(f"\n🔧 Raw account data (first account):")
    if accounts:
        print(json.dumps(accounts[0], indent=2))

if __name__ == "__main__":
    main()