#!/usr/bin/env python3
"""
Get Account Data Example
------------------------
Demonstrates how to retrieve all user accounts and then fetch detailed data for each.

Run with: python -m examples.get_account_data_example
"""
from config import settings
from pyHaasAPI import api
import os

def main():
    # Ensure API credentials are set in the .env file
    if not settings.API_EMAIL or not settings.API_PASSWORD:
        print("Error: API_EMAIL and API_PASSWORD must be set in your .env file.")
        print("Please create a .env file in the project root with:")
        print("API_HOST=127.0.0.1")
        print("API_PORT=8090")
        print("API_EMAIL=your_email@example.com")
        print("API_PASSWORD=your_password")
        return

    print("Attempting to authenticate with HaasOnline API...")
    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        print("Authentication successful.")
    except api.HaasApiError as e:
        print(f"Authentication failed: {e}")
        print("Please check your API_EMAIL, API_PASSWORD, API_HOST, and API_PORT in the .env file.")
        return
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}")
        return

    # 1. Get all accounts
    print("\nFetching all accounts...")
    try:
        accounts = api.get_accounts(executor)
        if not accounts:
            print("No accounts found.")
            return

        print(f"Found {len(accounts)} account(s):")
        for acc in accounts:
            print(f"  - Account ID: {acc.account_id}, Name: {acc.name}, Exchange Code: {acc.exchange_code}, Exchange Type: {acc.exchange_type}")

            # 2. Get detailed data for each account
            print(f"    Fetching detailed data for account: {acc.name} ({acc.account_id})...")
            try:
                account_data = api.get_account_data(executor, acc.account_id)
                print(f"      Exchange: {acc.exchange_code}")
                print(f"      Account Type: {acc.exchange_type}")
                print(f"      Wallets:")
                if account_data.wallets:
                    for wallet in account_data.wallets:
                        print(f"        - Currency: {wallet.get('C')}, Total: {wallet.get('T')}, Available: {wallet.get('A')}")
                else:
                    print("        No wallet data available.")
                print("-" * 40) # Separator for readability

            except api.HaasApiError as e:
                print(f"      Failed to get detailed data for account {acc.account_id}: {e}")
            except Exception as e:
                print(f"      An unexpected error occurred while fetching detailed account data: {e}")
            print("----------------------------------------")

    except api.HaasApiError as e:
        print(f"Failed to get accounts: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while fetching accounts: {e}")

if __name__ == "__main__":
    main()
