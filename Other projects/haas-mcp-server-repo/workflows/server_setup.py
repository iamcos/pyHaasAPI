from config import settings
from pyHaasAPI import api
import json
import time

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

def delete_all_accounts(executor):
    print("Attempting to delete all existing accounts...")
    while True:
        accounts = api.get_accounts(executor)
        if not accounts:
            print("No more accounts found. All accounts deleted.")
            break
        
        print(f"Found {len(accounts)} accounts to delete.")
        for account in accounts:
            try:
                print(f"Deleting account: {account.name} ({account.account_id})")
                delete_account(executor, account.account_id)
                print(f"Account {account.name} deleted.")
            except api.HaasApiError as e:
                print(f"Error deleting account {account.name}: {e}")
        time.sleep(1) # Give a small delay to avoid overwhelming the API

def create_and_fund_accounts(executor, num_accounts=100, initial_balance=10000.0):
    print(f"\nCreating and funding {num_accounts} new accounts...")
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
    for account_name in account_names:
        print(f"Creating account: {account_name}")
        try:
            # Replicate the curl command for ADD_SIMULATED_ACCOUNT
            new_account_response = executor._execute_inner(
                endpoint="Account",
                response_type=dict,
                query_params={
                    "channel": "ADD_SIMULATED_ACCOUNT",
                    "name": account_name,
                    "drivercode": "BINANCEFUTURES",
                    "drivertype": 2,
                    "interfacekey": executor.state.interface_key,
                    "userid": executor.state.user_id,
                }
            )
            
            if new_account_response.Success and new_account_response.Data:
                new_account_id = new_account_response.Data["AID"]
                print(f"Account '{account_name}' created with ID: {new_account_id}")

                # Withdraw all existing funds (if any)
                balance_data = api.get_account_balance(executor, new_account_id)
                if balance_data.get("I"): # 'I' contains the list of balances
                    for wallet in balance_data["I"]:
                        currency = wallet.get("C")
                        wallet_id = wallet.get("WT")
                        amount = wallet.get("A")
                        if currency and wallet_id and amount and amount > 0:
                            print(f"  Withdrawing {amount} {currency} from {account_name}...")
                            executor._execute_inner(
                                endpoint="Account",
                                response_type=bool,
                                query_params={
                                    "channel": "WITHDRAWAL_FUNDS",
                                    "accountid": new_account_id,
                                    "currency": currency,
                                    "walletid": wallet_id,
                                    "amount": amount,
                                    "interfacekey": executor.state.interface_key,
                                    "userid": executor.state.user_id,
                                }
                            )
                            print(f"  Withdrew {amount} {currency}.")

                # Then, deposit 10,000 USDT
                deposit_success = api.deposit_funds(executor, new_account_id, "USDT", "USDT", initial_balance)
                if deposit_success:
                    print(f"Successfully deposited {initial_balance} USDT to {account_name}.")
                else:
                    print(f"Failed to deposit {initial_balance} USDT to {account_name}.")
            else:
                print(f"Failed to create account '{account_name}': {new_account_response.Error if new_account_response.Error else 'Unknown error'}")

        except api.HaasApiError as e:
            print(f"Error creating or funding account {account_name}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for account {account_name}: {e}")
        time.sleep(0.1) # Small delay between account creations

def setup_haas_server_accounts(executor):
    """
    Sets up the HaasOnline Trade Server with a clean set of simulated accounts.
    Deletes all existing accounts, then creates 100 new accounts with a specific naming scheme,
    and funds each with exactly 10,000 USDT, zeroing out all other currencies.
    """
    delete_all_accounts(executor)
    create_and_fund_accounts(executor)
    print("\nHaasOnline server account setup process complete.")

# The __main__ block is removed as this script will be imported and called by the MCP server.