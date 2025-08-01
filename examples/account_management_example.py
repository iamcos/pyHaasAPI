#!/usr/bin/env python3
"""
Account Management Example
-------------------------
Demonstrates account management:
- List accounts
- Filter accounts
- Add simulated account
- Rename account
- Delete account

Run with: python -m examples.account_management_example
"""
from config import settings
from pyHaasAPI import api
import time

def main():
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )

    # 1. List all accounts
    accounts = api.get_accounts(executor)
    print("All accounts:")
    for acc in accounts:
        print(f"  {acc.account_id}: {acc.name} (Simulated: {getattr(acc, 'is_simulated', False)})")

    # 2. Filter simulated accounts
    simulated = [acc for acc in accounts if getattr(acc, 'is_simulated', False)]
    print(f"Simulated accounts: {[acc.account_id for acc in simulated]}")

    # 3. Add a simulated account only if none exists
    new_acc = None
    if not simulated:
        try:
            result = api.add_simulated_account(executor, name="SimTest", driver_code="SIM", driver_type=1)
            print(f"Simulated account created: {result}")
            time.sleep(2)
            accounts = api.get_accounts(executor)
            new_acc = next((a for a in accounts if a.name == "SimTest"), None)
            if not new_acc:
                print("Failed to find new simulated account!")
                return
        except Exception as e:
            print(f"Failed to create simulated account: {e}")
            print("Available driver codes/types may differ on your server. Please check the HaasOnline UI for supported simulated account types.")
            print("To add a simulated account: Log in to the HaasOnline web UI, go to 'Accounts', and add a new simulated account.")
            return
    else:
        new_acc = simulated[0]
        print(f"Using existing simulated account: {new_acc.account_id}")

    # 4. Rename the new account
    api.rename_account(executor, new_acc.account_id, new_name="SimTestRenamed")
    print(f"Renamed account {new_acc.account_id} to SimTestRenamed")
    time.sleep(2)

    # 5. Delete the new account
    api.delete_account(executor, new_acc.account_id)
    print(f"Deleted account {new_acc.account_id}")

if __name__ == "__main__":
    main() 