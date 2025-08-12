#!/usr/bin/env python3
"""
Quick test of new account management functions
"""
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
from pyHaasAPI import api

def main():
    print("🚀 Quick Account Management Test")
    print("=" * 40)
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
    # Get first account for testing
    accounts = api.get_accounts(executor)
    if not accounts:
        print("❌ No accounts found!")
        return
    test_account = accounts[0]
    account_id = test_account.account_id
    original_name = test_account.name
    print(f"\n🎯 Using account: {original_name} (ID: {account_id})")
    # Test 1: Get account balance
    print("\n💰 Test 1: Getting account balance...")
    try:
        balance = api.get_account_balance(executor, account_id)
        print(f"✅ Balance retrieved: {balance}")
    except Exception as e:
        print(f"❌ Balance failed: {e}")
    # Test 2: Rename account
    print("\n✏️ Test 2: Renaming account...")
    new_name = f"{original_name}_RENAMED"
    try:
        result = api.rename_account(executor, account_id, new_name)
        if result:
            print(f"✅ Account renamed to: {new_name}")
        else:
            print("❌ Account rename failed")
    except Exception as e:
        print(f"❌ Rename failed: {e}")
    # Test 3: Rename back
    print("\n✏️ Test 3: Renaming back...")
    try:
        result = api.rename_account(executor, account_id, original_name)
        if result:
            print(f"✅ Account renamed back to: {original_name}")
        else:
            print("❌ Account rename back failed")
    except Exception as e:
        print(f"❌ Rename back failed: {e}")
    # Test 4: Deposit funds
    print("\n💸 Test 4: Depositing funds...")
    try:
        result = api.deposit_funds(executor, account_id, "USDC", "USDC", 1000.0)
        if result:
            print("✅ Funds deposited successfully!")
        else:
            print("❌ Fund deposit failed")
    except Exception as e:
        print(f"❌ Deposit failed: {e}")
    # Test 5: Test account credentials (with invalid keys)
    print("\n🔑 Test 5: Testing account credentials...")
    try:
        result = api.test_account(executor, "BYBITSPOT", 0, 5, "invalid_key", "invalid_secret")
        print(f"✅ Credential test completed: {result}")
    except Exception as e:
        print(f"❌ Credential test failed: {e}")
    print("\n✅ Account management tests completed!")

if __name__ == "__main__":
    # Place the main execution logic here
    pass 