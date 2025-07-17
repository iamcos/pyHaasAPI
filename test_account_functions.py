#!/usr/bin/env python3
"""
Test script for new account management functions
Demonstrates rename_account, get_account_balance, and deposit_funds
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
            print(f"  {i}. {acc.name} (ID: {acc.account_id}, Exchange: {acc.exchange_code})")
        
        return executor, accounts
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None, None

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
    print("🧪 Testing Account Management Functions")
    print("=" * 50)
    
    # Test connection and get accounts
    executor, accounts = test_connection_and_accounts()
    
    if not executor or not accounts:
        print("\n❌ Cannot proceed without connection and accounts")
        return
    
    # Use the first account for testing
    test_account = accounts[0]
    account_id = test_account.account_id
    original_name = test_account.name
    
    print(f"\n🎯 Using account for testing: {original_name} (ID: {account_id})")
    
    # Test 1: Get balance
    test_get_balance(executor, account_id)
    
    # Test 2: Rename account (with a test name)
    test_name = f"{original_name}_TEST"
    rename_success = test_rename_account(executor, account_id, test_name)
    
    # Test 3: Rename back to original name
    if rename_success:
        test_rename_account(executor, account_id, original_name)
    
    # Test 4: Deposit funds (simulated - you may want to adjust parameters)
    # Note: This is a test with small amount - adjust as needed
    test_deposit_funds(executor, account_id, "USDC", "USDC", 100.0)
    
    print("\n✅ Account management function tests completed!")

if __name__ == "__main__":
    main() 