#!/usr/bin/env python3
"""
Complete test script for all account management functions
Demonstrates: add_simulated_account, test_account, delete_account, rename_account, 
get_account_balance, and deposit_funds
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

def test_test_account_credentials(executor, driver_code, driver_type, version, public_key, private_key, extra_key=""):
    """Test exchange account credentials"""
    print(f"\n🔑 Testing account credentials for {driver_code}...")
    print(f"  Driver Type: {driver_type}")
    print(f"  Version: {version}")
    print(f"  Public Key: {public_key[:8]}...{public_key[-4:] if len(public_key) > 12 else public_key}")
    print(f"  Private Key: {private_key[:8]}...{private_key[-4:] if len(private_key) > 12 else private_key}")
    if extra_key:
        print(f"  Extra Key: {extra_key[:8]}...{extra_key[-4:] if len(extra_key) > 12 else extra_key}")
    
    try:
        result = api.test_account(executor, driver_code, driver_type, version, public_key, private_key, extra_key)
        print("✅ Account credentials test completed!")
        print(f"Test result: {result}")
        
        # Check if test was successful
        if isinstance(result, dict):
            success = result.get('Success', False)
            error = result.get('Error', '')
            if success:
                print("✅ Credentials are valid!")
            else:
                print(f"❌ Credentials are invalid: {error}")
        
        return result
        
    except Exception as e:
        print(f"❌ Failed to test account credentials: {e}")
        return None

def test_delete_account(executor, account_id):
    """Test deleting an account"""
    print(f"\n🗑️ Deleting account {account_id}...")
    
    try:
        result = api.delete_account(executor, account_id)
        if result:
            print("✅ Account deleted successfully!")
        else:
            print("❌ Account deletion failed!")
        return result
    except Exception as e:
        print(f"❌ Failed to delete account: {e}")
        return False

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
    print("🧪 Testing Complete Account Management Functions")
    print("=" * 70)
    
    # Test connection and get accounts
    executor, accounts = test_connection_and_accounts()
    
    if not executor or not accounts:
        print("\n❌ Cannot proceed without connection and accounts")
        return
    
    # Test 1: Test account credentials (with invalid keys for demonstration)
    print("\n" + "="*50)
    print("TEST 1: Testing Account Credentials")
    print("="*50)
    
    # Test with invalid credentials (as shown in your example)
    test_test_account_credentials(
        executor=executor,
        driver_code="BYBITSPOT",
        driver_type=0,
        version=5,
        public_key="123123",  # Invalid - too short
        private_key="123123123",
        extra_key=""
    )
    
    # Test 2: Add a new simulated account
    print("\n" + "="*50)
    print("TEST 2: Adding Simulated Account")
    print("="*50)
    
    test_account_name = "TEST_FUTURES_ACCOUNT"
    driver_code = "BINANCEQUARTERLY"
    driver_type = 2
    
    new_account_id = test_add_simulated_account(executor, test_account_name, driver_code, driver_type)
    
    if not new_account_id:
        print("\n❌ Cannot proceed without a test account")
        return
    
    print(f"\n🎯 Using new simulated account: {test_account_name} (ID: {new_account_id})")
    
    # Test 3: Get balance for the new account
    print("\n" + "="*50)
    print("TEST 3: Getting Account Balance")
    print("="*50)
    test_get_balance(executor, new_account_id)
    
    # Test 4: Rename the account
    print("\n" + "="*50)
    print("TEST 4: Renaming Account")
    print("="*50)
    new_name = f"{test_account_name}_RENAMED"
    rename_success = test_rename_account(executor, new_account_id, new_name)
    
    # Test 5: Rename back to original name
    if rename_success:
        test_rename_account(executor, new_account_id, test_account_name)
    
    # Test 6: Deposit funds to the account
    print("\n" + "="*50)
    print("TEST 5: Depositing Funds")
    print("="*50)
    test_deposit_funds(executor, new_account_id, "USDC", "USDC", 1000.0)
    
    # Test 7: Get updated balance after deposit
    print(f"\n💰 Getting updated balance after deposit...")
    test_get_balance(executor, new_account_id)
    
    # Test 8: List all accounts again to see the new one
    print("\n" + "="*50)
    print("TEST 6: Listing Updated Accounts")
    print("="*50)
    updated_accounts = api.get_accounts(executor)
    print(f"✅ Now have {len(updated_accounts)} account(s):")
    for i, acc in enumerate(updated_accounts, 1):
        print(f"  {i}. {acc.name} (ID: {acc.account_id}, Exchange: {acc.exchange_code}, Simulated: {acc.is_simulated})")
    
    # Test 9: Delete the test account (optional - uncomment if you want to test deletion)
    print("\n" + "="*50)
    print("TEST 7: Account Deletion (SKIPPED - Uncomment to test)")
    print("="*50)
    print("⚠️ Account deletion test is commented out for safety.")
    print("   Uncomment the following lines in the script to test deletion:")
    print("   test_delete_account(executor, new_account_id)")
    
    # Uncomment the next line to test account deletion:
    # test_delete_account(executor, new_account_id)
    
    print("\n✅ Complete account management function tests completed!")

if __name__ == "__main__":
    main() 