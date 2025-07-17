#!/usr/bin/env python3
"""
Test script for simulated account management functions
Demonstrates add_simulated_account, rename_account, get_account_balance, and deposit_funds
"""

import os
from dotenv import load_dotenv
load_dotenv()

from pyHaasAPI import api
from config import settings

def test_connection_and_accounts():
    """Test connection and list all accounts"""
    print("🔐 Testing connection to HaasOnline API...")
    
    try:
        # Authenticate
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        
        print("✅ Authentication successful!")
        
        # Get all accounts
        print("\n📋 Getting all accounts...")
        accounts = api.get_accounts(executor)
        
        if not accounts:
            print("❌ No accounts found!")
            return None, None
        
        print(f"✅ Found {len(accounts)} account(s):")
        for i, acc in enumerate(accounts, 1):
            print(f"  {i}. {acc.name} (ID: {acc.account_id}, Exchange: {acc.exchange_code}, Simulated: {acc.is_simulated})")
        
        return executor, accounts
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None, None

def test_add_simulated_account(executor, name, driver_code, driver_type):
    """Test adding a new simulated account"""
    print(f"\n➕ Adding simulated account: {name} with driver {driver_code} (type {driver_type})...")
    
    try:
        result = api.add_simulated_account(executor, name, driver_code, driver_type)
        print("✅ Simulated account created successfully!")
        print(f"Account data: {result}")
        
        # Extract account ID from response
        if isinstance(result, dict) and 'Data' in result:
            account_data = result['Data']
            if isinstance(account_data, dict) and 'AID' in account_data:
                return account_data['AID']
        
        print("⚠️ Could not extract account ID from response")
        return None
        
    except Exception as e:
        print(f"❌ Failed to add simulated account: {e}")
        return None

def test_get_balance(executor, account_id):
    """Test getting account balance"""
    print(f"\n💰 Getting balance for account {account_id}...")
    
    try:
        balance = api.get_account_balance(executor, account_id)
        print("✅ Balance retrieved successfully!")
        print(f"Balance data: {balance}")
        return True
    except Exception as e:
        print(f"❌ Failed to get balance: {e}")
        return False

def test_rename_account(executor, account_id, new_name):
    """Test renaming an account"""
    print(f"\n✏️ Renaming account {account_id} to '{new_name}'...")
    
    try:
        result = api.rename_account(executor, account_id, new_name)
        if result:
            print("✅ Account renamed successfully!")
        else:
            print("❌ Account rename failed!")
        return result
    except Exception as e:
        print(f"❌ Failed to rename account: {e}")
        return False

def test_deposit_funds(executor, account_id, currency, wallet_id, amount):
    """Test depositing funds to an account"""
    print(f"\n💸 Depositing {amount} {currency} to account {account_id}...")
    
    try:
        result = api.deposit_funds(executor, account_id, currency, wallet_id, amount)
        if result:
            print("✅ Funds deposited successfully!")
        else:
            print("❌ Fund deposit failed!")
        return result
    except Exception as e:
        print(f"❌ Failed to deposit funds: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Simulated Account Management Functions")
    print("=" * 60)
    
    # Test connection and get accounts
    executor, accounts = test_connection_and_accounts()
    
    if not executor or not accounts:
        print("\n❌ Cannot proceed without connection and accounts")
        return
    
    # Test 1: Add a new simulated account
    test_account_name = "TEST_FUTURES_ACCOUNT"
    driver_code = "BINANCEQUARTERLY"
    driver_type = 2
    
    new_account_id = test_add_simulated_account(executor, test_account_name, driver_code, driver_type)
    
    if not new_account_id:
        print("\n❌ Cannot proceed without a test account")
        return
    
    print(f"\n🎯 Using new simulated account: {test_account_name} (ID: {new_account_id})")
    
    # Test 2: Get balance for the new account
    test_get_balance(executor, new_account_id)
    
    # Test 3: Rename the account
    new_name = f"{test_account_name}_RENAMED"
    rename_success = test_rename_account(executor, new_account_id, new_name)
    
    # Test 4: Rename back to original name
    if rename_success:
        test_rename_account(executor, new_account_id, test_account_name)
    
    # Test 5: Deposit funds to the account
    test_deposit_funds(executor, new_account_id, "USDC", "USDC", 1000.0)
    
    # Test 6: Get updated balance after deposit
    print(f"\n💰 Getting updated balance after deposit...")
    test_get_balance(executor, new_account_id)
    
    # Test 7: List all accounts again to see the new one
    print(f"\n📋 Listing all accounts after adding simulated account...")
    updated_accounts = api.get_accounts(executor)
    print(f"✅ Now have {len(updated_accounts)} account(s):")
    for i, acc in enumerate(updated_accounts, 1):
        print(f"  {i}. {acc.name} (ID: {acc.account_id}, Exchange: {acc.exchange_code}, Simulated: {acc.is_simulated})")
    
    print("\n✅ Simulated account management function tests completed!")

if __name__ == "__main__":
    main() 