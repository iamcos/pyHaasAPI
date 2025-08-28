#!/usr/bin/env python3
"""
Test script for the Account Manager
===================================

Example usage of the consolidated AccountManager for testing account creation,
management, and reservation functionality.

Usage:
    python examples/test_account_manager.py

Author: AI Assistant
Version: 1.0
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pyHaasAPI import api
from lab_to_bot_automation.account_manager import AccountManager, AccountConfig

def main():
    """Test the AccountManager functionality"""
    print("🧪 Testing Account Manager")
    print("=" * 50)

    # Connect to HaasOnline API
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

    # Create AccountManager with custom config for testing
    config = AccountConfig(
        account_suffix="-test",  # Use different suffix for testing
        initial_balance=1000.0,  # Smaller balance for testing
        creation_delay=0.5  # Longer delay for testing
    )

    account_manager = AccountManager(haas_executor, config)

    print("\n📊 Testing Account Discovery...")
    try:
        accounts = account_manager.get_existing_accounts()
        print(f"   Found {len(accounts)} existing accounts")

        # Show a few examples
        for account in accounts[:3]:
            print(f"   • {account.name}: {account.balance_usdt} USDT ({'has bot' if account.has_bot else 'free'})")

    except Exception as e:
        print(f"   ❌ Error discovering accounts: {e}")

    print("\n🏗️  Testing Account Creation...")
    try:
        # Generate a few test account names
        test_names = account_manager.generate_account_names("Z", 3)  # Use Z to avoid conflicts
        print(f"   Generated test names: {test_names}")

        # Create one test account
        test_account = account_manager.create_and_fund_account(test_names[0])
        if test_account:
            print(f"   ✅ Successfully created and funded: {test_account.name}")
            print(f"      ID: {test_account.account_id}")
            print(f"      Balance: {test_account.balance_usdt} USDT")
        else:
            print("   ❌ Failed to create test account")

    except Exception as e:
        print(f"   ❌ Error creating test account: {e}")

    print("\n🎯 Testing Account Reservation...")
    try:
        # Try to reserve 2 accounts for bots
        reserved_accounts = account_manager.reserve_accounts_for_bots(2)
        print(f"   Reserved {len(reserved_accounts)} accounts for bot creation:")

        for account in reserved_accounts:
            print(f"   • {account.name} (ID: {account.account_id})")

    except Exception as e:
        print(f"   ❌ Error reserving accounts: {e}")

    print("\n✅ Account Manager Testing Complete!")
    print("=" * 50)
    print("💡 The AccountManager is ready for use in the Lab to Bot Automation system!")

if __name__ == "__main__":
    main()

