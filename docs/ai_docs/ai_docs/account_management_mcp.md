# Account Management Tools for MCP Server

This document describes the account management tools exposed via the `mcp_server` for interacting with HaasOnline Trade Server (HTS) simulated accounts.

## Available Tools

### 1. Create Simulated Account

**Endpoint:** `/create_simulated_account`
**Method:** `POST`
**Description:** Creates a new simulated trading account on HTS.

**Parameters:**
- `account_name` (string, required): The desired name for the new account.
- `driver_code` (string, required): The exchange driver code (e.g., "BINANCEFUTURES").
- `driver_type` (integer, required): The type of driver (e.g., 2 for simulated).

**Example Usage (via `curl`):**
```bash
curl -X POST "http://localhost:8000/create_simulated_account" \
     -H "Content-Type: application/json" \
     -d '{
           "account_name": "MyNewSimAccount",
           "driver_code": "BINANCEFUTURES",
           "driver_type": 2
         }'
```

### 2. Delete Simulated Account

**Endpoint:** `/delete_simulated_account/{account_id}`
**Method:** `DELETE`
**Description:** Deletes a simulated trading account from HTS.

**Parameters:**
- `account_id` (string, required): The ID of the account to delete.

**Example Usage (via `curl`):**
```bash
curl -X DELETE "http://localhost:8000/delete_simulated_account/YOUR_ACCOUNT_ID"
```

### 3. Deposit Funds

**Endpoint:** `/deposit_funds`
**Method:** `POST`
**Description:** Deposits funds into a specified account.

**Parameters:**
- `account_id` (string, required): The ID of the account to deposit into.
- `currency` (string, required): The currency to deposit (e.g., "USDT", "BTC").
- `wallet_id` (string, required): The wallet ID for the currency (usually same as currency).
- `amount` (float, required): The amount to deposit.

**Example Usage (via `curl`):**
```bash
curl -X POST "http://localhost:8000/deposit_funds" \
     -H "Content-Type: application/json" \
     -d '{
           "account_id": "YOUR_ACCOUNT_ID",
           "currency": "USDT",
           "wallet_id": "USDT",
           "amount": 10000.0
         }'
```

### 4. Withdraw Funds

**Endpoint:** `/withdraw_funds`
**Method:** `POST`
**Description:** Withdraws funds from a specified account.

**Parameters:**
- `account_id` (string, required): The ID of the account to withdraw from.
- `currency` (string, required): The currency to withdraw (e.g., "USDT", "BTC").
- `wallet_id` (string, required): The wallet ID for the currency (usually same as currency).
- `amount` (float, required): The amount to withdraw.

**Example Usage (via `curl`):**
```bash
curl -X POST "http://localhost:8000/withdraw_funds" \
     -H "Content-Type: application/json" \
     -d '{
           "account_id": "YOUR_ACCOUNT_ID",
           "currency": "USDT",
           "wallet_id": "USDT",
           "amount": 500.0
         }'
```

### 5. Get All Accounts

**Endpoint:** `/get_all_accounts`
**Method:** `GET`
**Description:** Retrieves a list of all accounts associated with the authenticated user.

**Example Usage (via `curl`):**
```bash
curl "http://localhost:8000/get_all_accounts"
```

### 6. Get Account Balance

**Endpoint:** `/get_account_balance/{account_id}`
**Method:** `GET`
**Description:** Retrieves the balance information for a specific account.

**Parameters:**
- `account_id` (string, required): The ID of the account to retrieve balance for.

**Example Usage (via `curl`):**
```bash
curl "http://localhost:8000/get_account_balance/YOUR_ACCOUNT_ID"
```

