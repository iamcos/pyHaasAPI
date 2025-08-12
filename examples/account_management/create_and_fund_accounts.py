from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import UserAccount

print(f"pyHaasAPI module loaded from: {api.__file__}")

print(f"pyHaasAPI module loaded from: {api.__file__}")
print(f"pyHaasAPI.api module loaded from: {api.__file__}")
import time
import math
import json

def create_and_fund_accounts(server_name: str):
    account_names = [
        "4AA-10k", "4AB-10k", "4AC-10k", "4AD-10k", "4AE-10k", "4AF-10k", "4AG-10k", "4AH-10k", "4AI-10k", "4AJ-10k",
        "4AK-10k", "4AL-10k", "4AM-10k", "4AN-10k", "4AO-10k", "4AP-10k", "4AQ-10k", "4AR-10k", "4AS-10k", "4AT-10k",
        "4AU-10k", "4AV-10k", "4AW-10k", "4AX-10k", "4AY-10k", "4AZ-10k", "4BA-10k", "4BB-10k", "4BC-10k", "4BD-10k",
        "4BE-10k", "4BF-10k", "4BG-10k", "4BH-10k", "4BI-10k", "4BJ-10k", "4BK-10k", "4BL-10k", "4BM-10k", "4BN-10k",
        "4BO-10k", "4BP-10k", "4BQ-10k", "4BR-10k", "4BS-10k", "4BT-10k", "4BU-10k", "4BV-10k", "4BW-10k", "4BX-10k",
        "4BY-10k", "4BZ-10k", "4CA-10k", "4CB-10k", "4CC-10k", "4CD-10k", "4CE-10k", "4CF-10k", "4CG-10k", "4CH-10k",
        "4CI-10k", "4CJ-10k", "4CK-10k", "4CL-10k", "4CM-10k", "4CN-10k", "4CO-10k", "4CP-10k", "4CQ-10k", "4CR-10k",
        "4CS-10k", "4CT-10k", "4CU-10k", "4CV-10k", "4CW-10k", "4CX-10k", "4CY-10k", "4CZ-10k", "4DA-10k", "4DB-10k",
        "4DC-10k", "4DD-10k", "4DE-10k", "4DF-10k", "4DG-10k", "4DH-10k", "4DI-10k", "4DJ-10k", "4DK-10k", "4DL-10k",
        "4DM-10k", "4DN-10k", "4DO-10k", "4DP-10k", "4DQ-10k", "4DR-10k", "4DS-10k", "4DT-10k", "4DU-10k", "4DV-10k"
    ]
    
    special_account_name = "for tests 10k"
    deposit_amount = 10000.0
    currencies_to_try = ["USDT", "USD"]
    report_data = []

    try:
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        ).authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )

        # --- Delete all existing accounts ---
        print("--- Deleting all existing accounts ---")
        existing_accounts = api.get_accounts(executor)
        for account in existing_accounts:
            # Do not delete the special account if it exists from a previous run
            # and do not delete any accounts that are not simulated (to be safe)
            if account.name != special_account_name and account.is_simulated:
                print(f"Deleting account: {account.name} (ID: {account.account_id})")
                try:
                    delete_account(executor, account.account_id) # Use the explicitly imported function
                    print(f"  Successfully deleted {account.name}.")
                except api.HaasApiError as e:
                    print(f"  Error deleting account {account.name}: {e}")
                except Exception as e:
                    print(f"  An unexpected error occurred while deleting account {account.name}: {e}")
                time.sleep(0.1) # Small delay
        print("--- Finished deleting accounts ---")
        print()

        # --- Get available exchanges ---
        print("--- Discovering available exchanges ---")
        all_markets = api.get_all_markets(executor)
        available_exchanges = list(set([market.price_source for market in all_markets]))
        if not available_exchanges:
            print("Error: No available exchanges found. Cannot create accounts.")
            return
        print(f"Available exchanges: {available_exchanges}")
        print("--- Finished discovering exchanges ---")
        print()

        # --- Create and fund the 100 accounts ---
        print("--- Creating and Funding 100 Accounts ---")
        num_exchanges = len(available_exchanges)
        for i, name in enumerate(account_names):
            exchange_code = available_exchanges[i % num_exchanges] # Cycle through exchanges
            report_entry = {
                "account_name": name,
                "account_id": "",
                "exchange": exchange_code,
                "creation_status": "Failed",
                "creation_error": "",
                "funding_status": "Skipped",
                "funding_error": ""
            }
            print(f"Processing account: {name} on exchange: {exchange_code}")
            try:
                new_account: UserAccount = api.add_simulated_account(executor, name, exchange_code)
                account_id = new_account.account_id
                report_entry["account_id"] = account_id
                report_entry["creation_status"] = "Success"
                print(f"  Created account '{name}' with ID: {account_id}")
                
                # Fund the account
                funded = False
                for curr in currencies_to_try:
                    account_data = api.get_account_data(executor, account_id)
                    target_wallet = next((w for w in account_data.wallets if w.get('C') == curr), None)

                    if target_wallet:
                        wallet_id = target_wallet.get('Id')
                        if wallet_id:
                            print(f"  Funding account '{name}' with {deposit_amount} {curr} (Wallet ID: {wallet_id})...")
                            api.deposit_funds(executor, account_id, curr, wallet_id, deposit_amount)
                            report_entry["funding_status"] = "Success"
                            report_entry["funding_currency"] = curr
                            print(f"  Successfully funded '{name}'.")
                            funded = True
                            break
                        else:
                            report_entry["funding_error"] = f"Could not find Wallet ID for {curr} in account '{name}'."
                            print(f"  Warning: {report_entry['funding_error']} Skipping funding with {curr}.")
                    else:
                        report_entry["funding_error"] = f"Could not find {curr} wallet for account '{name}'."
                        print(f"  Warning: {report_entry['funding_error']} Skipping funding with {curr}.")
                
                if not funded:
                    report_entry["funding_status"] = "Failed"
                    report_entry["funding_error"] = f"Could not fund with any of {currencies_to_try}."
                    print(f"  Warning: Could not fund account '{name}' with any of {currencies_to_try}.")

            except api.HaasApiError as e:
                report_entry["creation_error"] = str(e)
                print(f"  HaasAPI Error for account {name}: {e}")
            except Exception as e:
                report_entry["creation_error"] = str(e)
                print(f"  An unexpected error occurred for account {name}: {e}")
            report_data.append(report_entry)
            time.sleep(0.1) # Small delay to avoid overwhelming the API

        # --- Create the special "for tests 10k" account ---
        print(f"\n--- Creating Special Account: {special_account_name} ---")
        special_account_report_entry = {
            "account_name": special_account_name,
            "account_id": "",
            "exchange": "",
            "creation_status": "Failed",
            "creation_error": "",
            "funding_status": "Skipped",
            "funding_error": ""
        }
        try:
            # Ensure this account is created on a default exchange if others are deleted
            special_account_exchange = available_exchanges[0] if available_exchanges else "BINANCE" 
            special_account_report_entry["exchange"] = special_account_exchange
            new_special_account: UserAccount = api.add_simulated_account(executor, special_account_name, special_account_exchange)
            special_account_report_entry["account_id"] = new_special_account.account_id
            special_account_report_entry["creation_status"] = "Success"
            print(f"  Created special account '{special_account_name}' with ID: {new_special_account.account_id} on exchange {special_account_exchange}")
            print(f"  Note: This account is intentionally not funded with any coins other than the initial 10k USDT.")
        except api.HaasApiError as e:
            special_account_report_entry["creation_error"] = str(e)
            print(f"  HaasAPI Error for special account {special_account_name}: {e}")
        except Exception as e:
            special_account_report_entry["creation_error"] = str(e)
            print(f"  An unexpected error occurred for special account {special_account_name}: {e}")
        report_data.append(special_account_report_entry)

        print("\nAccount creation and funding process completed.")

    except api.HaasApiError as e:
        print(f"Authentication Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}")

    # --- Generate Report ---
    report_filename = f"account_creation_report_{server_name}.md"
    with open(report_filename, "w") as f:
        f.write(f"# Account Creation and Funding Report - Server: {server_name}\n\n")
        f.write("| Account Name | Account ID | Exchange | Creation Status | Funding Status | Funding Currency | Error Details |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for entry in report_data:
            error_details = f"Creation: {entry['creation_error']}" if entry['creation_error'] else ""
            if entry['funding_error']:
                error_details += f" Funding: {entry['funding_error']}" if error_details else f"Funding: {entry['funding_error']}"
            funding_currency = entry.get("funding_currency", "N/A")
            
            f.write(f"| {entry['account_name']} | {entry['account_id']} | {entry['exchange']} | {entry['creation_status']} | {entry['funding_status']} | {funding_currency} | {error_details} |\n")
    print(f"Detailed report saved to {report_filename}")

if __name__ == "__main__":
    # Pass the current server name as an argument
    current_server = "srv03" # This will be dynamically set in future automation
    create_and_fund_accounts(current_server)