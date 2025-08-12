from config import settings
from pyHaasAPI import api
from pyHaasAPI.model import UserAccount

# Define delete_account function locally to avoid import issues
def delete_account(executor, account_id):
    return executor.execute(
        endpoint="Account",
        response_type=bool,
        query_params={
            "channel": "DELETE_ACCOUNT",
            "accountid": account_id,
            "interfacekey": executor.state.interface_key,
            "userid": executor.state.user_id,
        },
    )
import time
import json

def manage_account_balances(server_name: str):
    target_account_names = [
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
    target_account_names.append("for tests 10k")
    
    target_stable_balance = 10000.0
    stable_currencies = ["USDT", "USD"]
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

        # --- Selective Account Deletion ---
        print("--- Deleting non-target accounts ---")
        all_accounts = api.get_accounts(executor)
        for account in all_accounts:
            if account.name not in target_account_names and account.is_simulated:
                print(f"Deleting non-target account: {account.name} (ID: {account.account_id})")
                try:
                    delete_account(executor, account.account_id)
                    print(f"  Successfully deleted {account.name}.")
                except api.HaasApiError as e:
                    print(f"  Error deleting account {account.name}: {e}")
                except Exception as e:
                    print(f"  An unexpected error occurred while deleting account {account.name}: {e}")
                time.sleep(0.1) # Small delay
        print("--- Finished deleting non-target accounts ---")
        print()

        # --- Balance Adjustment for Target Accounts ---
        print("--- Adjusting balances for target accounts ---")
        updated_accounts = api.get_accounts(executor) # Re-fetch accounts after deletion
        for account in updated_accounts:
            if account.name in target_account_names:
                account_report_entry = {
                    "account_name": account.name,
                    "account_id": account.account_id,
                    "exchange": account.exchange_code,
                    "wallet_adjustments": []
                }
                print(f"Processing account: {account.name} (ID: {account.account_id})")
                
                # Use get_account_balance for wallet information
                balance_data = api.get_account_balance(executor, account.account_id)
                wallets = balance_data.get('wallets', [])
                print(f"  Raw balance_data.wallets: {wallets}") # Debugging print
                
                if not wallets:
                    print(f"  No wallets found for account {account.name}. Skipping balance adjustment.")
                    account_report_entry["wallet_adjustments"].append({"currency": "N/A", "initial_balance": 0.0, "adjustment_amount": 0.0, "status": "Skipped", "error": "No wallets found"})
                    report_data.append(account_report_entry)
                    continue

                # Track if a stable currency wallet was found and adjusted
                stable_currency_adjusted = False

                for wallet in wallets:
                    currency = wallet.get('currency')
                    current_balance = wallet.get('total', 0.0)
                    wallet_id = wallet.get('id') # Assuming 'id' is the wallet ID from get_account_balance

                    wallet_adjustment_entry = {
                        "currency": currency,
                        "initial_balance": current_balance,
                        "adjustment_amount": 0.0,
                        "status": "Skipped",
                        "error": ""
                    }

                    if not wallet_id:
                        wallet_adjustment_entry["status"] = "Skipped"
                        wallet_adjustment_entry["error"] = f"Wallet ID not found for {currency}."
                        print(f"  Warning: Wallet ID not found for {currency}. Skipping adjustment.")
                        account_report_entry["wallet_adjustments"].append(wallet_adjustment_entry)
                        continue

                    if currency in stable_currencies:
                        adjustment_amount = target_stable_balance - current_balance
                        wallet_adjustment_entry["adjustment_amount"] = adjustment_amount

                        if abs(adjustment_amount) < 0.001: # Already balanced
                            wallet_adjustment_entry["status"] = "Already Balanced"
                            print(f"  {currency} already balanced at {current_balance:.4f}.")
                        elif adjustment_amount > 0: # Need to deposit
                            print(f"  Depositing {adjustment_amount:.4f} {currency}...")
                            try:
                                api.deposit_funds(executor, account.account_id, currency, wallet_id, adjustment_amount)
                                wallet_adjustment_entry["status"] = "Deposited"
                                print(f"  Successfully deposited {currency}.")
                                stable_currency_adjusted = True
                            except api.HaasApiError as e:
                                wallet_adjustment_entry["error"] = str(e)
                                wallet_adjustment_entry["status"] = "Failed Deposit"
                                print(f"  Error depositing {currency}: {e}")
                            except Exception as e:
                                wallet_adjustment_entry["error"] = str(e)
                                wallet_adjustment_entry["status"] = "Failed Deposit"
                                print(f"  An unexpected error occurred during {currency} deposit: {e}")
                        else: # Need to withdraw
                            withdraw_amount = abs(adjustment_amount)
                            print(f"  Withdrawing {withdraw_amount:.4f} {currency}...")
                            try:
                                api.withdraw_funds(executor, account.account_id, currency, wallet_id, withdraw_amount)
                                wallet_adjustment_entry["status"] = "Withdrew"
                                print(f"  Successfully withdrew {currency}.")
                                stable_currency_adjusted = True
                            except api.HaasApiError as e:
                                wallet_adjustment_entry["error"] = str(e)
                                wallet_adjustment_entry["status"] = "Failed Withdrawal"
                                print(f"  Error withdrawing {currency}: {e}")
                            except Exception as e:
                                wallet_adjustment_entry["error"] = str(e)
                                wallet_adjustment_entry["status"] = "Failed Withdrawal"
                                print(f"  An unexpected error occurred during {currency} withdrawal: {e}")
                    else: # Other currencies, zero out
                        if current_balance > 0.001: # Only withdraw if there's a significant balance
                            print(f"  Zeroing out {currency} balance ({current_balance:.4f})...")
                            try:
                                api.withdraw_funds(executor, account.account_id, currency, wallet_id, current_balance)
                                wallet_adjustment_entry["adjustment_amount"] = -current_balance
                                wallet_adjustment_entry["status"] = "Zeroed Out"
                                print(f"  Successfully zeroed out {currency}.")
                            except api.HaasApiError as e:
                                wallet_adjustment_entry["error"] = str(e)
                                wallet_adjustment_entry["status"] = "Failed Zero Out"
                                print(f"  Error zeroing out {currency}: {e}")
                            except Exception as e:
                                wallet_adjustment_entry["error"] = str(e)
                                wallet_adjustment_entry["status"] = "Failed Zero Out"
                                print(f"  An unexpected error occurred during {currency} zero out: {e}")
                        else:
                            wallet_adjustment_entry["status"] = "Already Zero"
                            print(f"  {currency} already zero or negligible.")
                    account_report_entry["wallet_adjustments"].append(wallet_adjustment_entry)
                
                # If no stable currency wallet was found or adjusted, add a note to the report
                if not stable_currency_adjusted and not any(w["currency"] in stable_currencies for w in wallets):
                    account_report_entry["wallet_adjustments"].append({"currency": "USDT/USD", "initial_balance": 0.0, "adjustment_amount": 0.0, "status": "Skipped", "error": "No USDT/USD wallet found for adjustment."})

                report_data.append(account_report_entry)
                time.sleep(0.1) # Small delay
        print("--- Finished adjusting balances ---")
        print()

        print("Account management process completed.")

    except api.HaasApiError as e:
        print(f"Authentication Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during authentication: {e}")

    # --- Generate Report ---
    report_filename = f"account_balance_report_{server_name}.md"
    with open(report_filename, "w") as f:
        f.write(f"# Account Balance Adjustment Report - Server: {server_name}\n\n")
        f.write("| Account Name | Account ID | Exchange | Currency | Initial Balance | Adjustment Amount | Status | Error Details |\n")
        f.write("|---|---|---|---|---|---|---|---|")
        f.write("\n")
        for account_entry in report_data:
            for wallet_entry in account_entry["wallet_adjustments"]:
                error_details = wallet_entry['error'] if wallet_entry['error'] else ""
                f.write(f"| {account_entry['account_name']} | {account_entry['account_id']} | {account_entry['exchange']} | {wallet_entry['currency']} | {wallet_entry['initial_balance']:.4f} | {wallet_entry['adjustment_amount']:.4f} | {wallet_entry['status']} | {error_details} |\n")
    print(f"Detailed report saved to {report_filename}")

if __name__ == "__main__":
    current_server = "srv03" 
    manage_account_balances(current_server)