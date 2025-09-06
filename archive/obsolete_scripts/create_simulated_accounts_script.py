import requests
import json
import string
import time # Import time for sleep

MCP_SERVER_URL = "http://localhost:8000"
TARGET_BALANCE = 10000.0
CURRENCY = "USDT"
WALLET_ID = "simulated_wallet" # Placeholder for simulated accounts

def call_mcp_tool(tool_name, arguments):
    url = f"{MCP_SERVER_URL}/call_tool"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "tool_name": tool_name,
        "arguments": arguments
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling tool {tool_name}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.text}")
        return {"success": False, "error": str(e)}

def create_and_fund_account(account_name, driver_code, driver_type):
    print(f"Processing account: {account_name}")
    account_id = None

    # 1. Try to get all accounts to check if it already exists
    get_all_accounts_response = call_mcp_tool("get_all_accounts", {})
    if get_all_accounts_response.get("success") and get_all_accounts_response.get("data"):
        for acc in get_all_accounts_response["data"]:
            if acc.get("Name") == account_name:
                account_id = acc.get("AccountId")
                print(f"Account '{account_name}' already exists with ID: {account_id}")
                break
    
    # 2. If account does not exist, create it
    if not account_id:
        print(f"Creating account: {account_name}")
        create_response = call_mcp_tool(
            "create_simulated_account",
            {
                "account_name": account_name,
                "driver_code": driver_code,
                "driver_type": driver_type
            }
        )
        if create_response.get("success") and create_response.get("data"):
            account_id = create_response["data"].get("AccountId")
            if not account_id:
                print(f"Failed to get AccountId for '{account_name}' after creation: {create_response.get('data')}")
                return
        else:
            print(f"Failed to create account '{account_name}': {create_response.get('error')}")
            return

    # 3. Check current balance
    current_balance = 0.0
    balance_response = call_mcp_tool("get_account_balance", {"account_id": account_id})
    if balance_response.get("success") and balance_response.get("data"):
        # Assuming the balance data structure is like {'Currency': 'USDT', 'Available': 123.45}
        # Need to iterate through balances if multiple currencies are returned
        for balance_item in balance_response["data"]:
            if balance_item.get("Currency") == CURRENCY:
                current_balance = float(balance_item.get("Available", 0.0))
                print(f"Current balance for '{account_name}' ({CURRENCY}): {current_balance}")
                break
    else:
        print(f"Failed to get balance for '{account_name}': {balance_response.get('error')}. Assuming 0.0.")

    # 4. Adjust balance
    if current_balance > TARGET_BALANCE:
        amount_to_withdraw = current_balance - TARGET_BALANCE
        print(f"Withdrawing {amount_to_withdraw} {CURRENCY} from '{account_name}'...")
        withdraw_response = call_mcp_tool(
            "withdraw_funds",
            {
                "account_id": account_id,
                "currency": CURRENCY,
                "wallet_id": WALLET_ID,
                "amount": amount_to_withdraw
            }
        )
        if withdraw_response.get("success"):
            print(f"Successfully withdrew {amount_to_withdraw} {CURRENCY} from '{account_name}'.")
        else:
            print(f"Failed to withdraw funds from '{account_name}': {withdraw_response.get('error')}")
    elif current_balance < TARGET_BALANCE:
        amount_to_deposit = TARGET_BALANCE - current_balance
        print(f"Depositing {amount_to_deposit} {CURRENCY} to '{account_name}'...")
        deposit_response = call_mcp_tool(
            "deposit_funds",
            {
                "account_id": account_id,
                "currency": CURRENCY,
                "wallet_id": WALLET_ID,
                "amount": amount_to_deposit
            }
        )
        if deposit_response.get("success"):
            print(f"Successfully deposited {amount_to_deposit} {CURRENCY} to '{account_name}'.")
        else:
            print(f"Failed to deposit funds to '{account_name}': {deposit_response.get('error')}")
    else:
        print(f"Balance for '{account_name}' is already {TARGET_BALANCE} {CURRENCY}. No adjustment needed.")

def generate_account_names(count):
    names = []
    first_char_start = ord('A')
    second_char_start = ord('A')
    
    for i in range(count):
        first_char_offset = i // 26
        second_char_offset = i % 26
        
        first_char = chr(first_char_start + first_char_offset)
        second_char = chr(second_char_start + second_char_offset)
        
        names.append(f"[Sim] 4{first_char}{second_char}-10k")
    return names

if __name__ == "__main__":
    # Give the MCP server a moment to start up and register tools
    print("Waiting for MCP server to initialize...")
    time.sleep(5) 
    print("Starting account processing...")

    # Generate 100 accounts
    account_names = generate_account_names(100)
    for name in account_names:
        create_and_fund_account(name, "BINANCE", 0)

    # Create test accounts
    create_and_fund_account("For tests 10k 1", "BINANCE", 0)
    create_and_fund_account("For tests 10k 2", "BINANCE", 0)

    print("\nAccount creation and funding process complete.")