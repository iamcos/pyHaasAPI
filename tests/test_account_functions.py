#!/usr/bin/env python3
"""
Test script for new account management functions
Demonstrates rename_account, get_account_balance, and deposit_funds
"""
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
from pyHaasAPI import api

def test_connection_and_accounts():
    print("🔐 Testing connection to HaasOnline API...")
    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        print("✅ Authentication successful!")
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
    print("🧪 Testing Account Management Functions")
    print("=" * 50)
    executor, accounts = test_connection_and_accounts()
    if not executor or not accounts:
        print("\n❌ Cannot proceed without connection and accounts")
        return
    test_account = accounts[0]
    account_id = test_account.account_id
    original_name = test_account.name
    print(f"\n🎯 Using account for testing: {original_name} (ID: {account_id})")
    test_get_balance(executor, account_id)
    test_name = f"{original_name}_TEST"
    rename_success = test_rename_account(executor, account_id, test_name)
    if rename_success:
        test_rename_account(executor, account_id, original_name)
    test_deposit_funds(executor, account_id, "USDC", "USDC", 100.0)
    print("\n✅ Account management function tests completed!")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 