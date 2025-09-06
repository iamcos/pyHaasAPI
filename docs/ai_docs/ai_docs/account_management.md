# Account Management Guide for pyHaasAPI

## Overview

Account management in pyHaasAPI allows you to interact with trading accounts, view balances, manage positions, and handle account-specific operations. This includes both simulated and real trading accounts across different exchanges.

## Core Concepts

### Account Types

- **Real Accounts**: Live trading accounts connected to exchanges
- **Simulated Accounts**: Test accounts for backtesting and development
- **Test Net Accounts**: Exchange test environments

### Account Properties

```python
from pyHaasAPI.model import UserAccount

# Account properties
account_id: str          # Unique account identifier
name: str               # Account display name
exchange_code: str      # Exchange (BINANCE, KRAKEN, etc.)
exchange_type: int      # Account type identifier
status: int             # Account status
is_simulated: bool      # True for simulated accounts
is_test_net: bool       # True for test net accounts
is_public: bool         # True for public accounts
is_white_label: bool    # True for white label accounts
position_mode: int      # Position mode for futures
margin_settings: Any    # Margin configuration
version: int            # Account version
```

## Account Discovery

### Getting All Accounts

```python
from pyHaasAPI import api

# Get all accounts
accounts = api.get_accounts(executor)

for account in accounts:
    print(f"Account: {account.name}")
    print(f"  ID: {account.account_id}")
    print(f"  Exchange: {account.exchange_code}")
    print(f"  Type: {'Simulated' if account.is_simulated else 'Real'}")
    print(f"  Status: {account.status}")
```

### Filtering Accounts

```python
def filter_accounts(accounts, **filters):
    """Filter accounts based on criteria"""
    filtered = accounts
    
    if 'exchange' in filters:
        filtered = [acc for acc in filtered if acc.exchange_code == filters['exchange']]
    
    if 'simulated' in filters:
        filtered = [acc for acc in filtered if acc.is_simulated == filters['simulated']]
    
    if 'active' in filters:
        filtered = [acc for acc in filtered if acc.status == 1]  # Assuming 1 = active
    
    return filtered

# Usage examples
binance_accounts = filter_accounts(accounts, exchange="BINANCE")
simulated_accounts = filter_accounts(accounts, simulated=True)
active_accounts = filter_accounts(accounts, active=True)
```

## Account Information

### Getting Account Details

```python
# Get detailed account information
account_data = api.get_account_data(executor, account_id)

print(f"Account: {account_data.account_id}")
print(f"Exchange: {account_data.exchange}")
print(f"Type: {account_data.type}")
print(f"Wallets: {len(account_data.wallets)}")
```

### Getting Account Balance

```python
# Get balance for specific account
balance = api.get_account_balance(executor, account_id)

for wallet in balance.get('wallets', []):
    currency = wallet.get('currency', 'N/A')
    available = wallet.get('available', 0)
    reserved = wallet.get('reserved', 0)
    total = wallet.get('total', 0)
    
    print(f"Currency: {currency}")
    print(f"  Available: {available}")
    print(f"  Reserved: {reserved}")
    print(f"  Total: {total}")
```

### Getting All Account Balances

```python
# Get balances for all accounts
all_balances = api.get_all_account_balances(executor)

for account_balance in all_balances:
    account_id = account_balance.get('account_id', 'N/A')
    wallets = account_balance.get('wallets', [])
    
    print(f"Account: {account_id}")
    for wallet in wallets:
        currency = wallet.get('currency', 'N/A')
        total = wallet.get('total', 0)
        print(f"  {currency}: {total}")
```

## Account Operations

### Getting Account Orders

```python
# Get all orders for an account
orders = api.get_account_orders(executor, account_id)

for order in orders.get('orders', []):
    order_id = order.get('id', 'N/A')
    market = order.get('market', 'N/A')
    side = order.get('side', 'N/A')
    amount = order.get('amount', 'N/A')
    price = order.get('price', 'N/A')
    status = order.get('status', 'N/A')
    
    print(f"Order: {order_id}")
    print(f"  Market: {market}")
    print(f"  Side: {side}")
    print(f"  Amount: {amount}")
    print(f"  Price: {price}")
    print(f"  Status: {status}")
```

### Getting Account Positions

```python
# Get all positions for an account
positions = api.get_account_positions(executor, account_id)

for position in positions.get('positions', []):
    market = position.get('market', 'N/A')
    side = position.get('side', 'N/A')
    amount = position.get('amount', 'N/A')
    entry_price = position.get('entry_price', 'N/A')
    current_price = position.get('current_price', 'N/A')
    pnl = position.get('pnl', 'N/A')
    
    print(f"Position: {market}")
    print(f"  Side: {side}")
    print(f"  Amount: {amount}")
    print(f"  Entry Price: {entry_price}")
    print(f"  Current Price: {current_price}")
    print(f"  P&L: {pnl}")
```

### Getting Account Trades

```python
# Get trade history for an account
trades = api.get_account_trades(executor, account_id)

for trade in trades:
    trade_id = trade.get('id', 'N/A')
    market = trade.get('market', 'N/A')
    side = trade.get('side', 'N/A')
    amount = trade.get('amount', 'N/A')
    price = trade.get('price', 'N/A')
    fee = trade.get('fee', 'N/A')
    timestamp = trade.get('timestamp', 'N/A')
    
    print(f"Trade: {trade_id}")
    print(f"  Market: {market}")
    print(f"  Side: {side}")
    print(f"  Amount: {amount}")
    print(f"  Price: {price}")
    print(f"  Fee: {fee}")
    print(f"  Time: {timestamp}")
```

## Account Management

### Renaming Accounts

```python
# Rename an account
success = api.rename_account(executor, account_id, "New Account Name")

if success:
    print("Account renamed successfully")
else:
    print("Failed to rename account")
```

### Depositing Funds

```python
# Deposit funds to account
success = api.deposit_funds(
    executor,
    account_id=account_id,
    currency="USDT",
    wallet_id="wallet_id",
    amount=1000.0
)

if success:
    print("Funds deposited successfully")
else:
    print("Failed to deposit funds")
```

### Deleting Accounts

```python
# Delete an account
success = api.delete_account(executor, account_id)

if success:
    print("Account deleted successfully")
else:
    print("Failed to delete account")
```

## Simulated Account Management

### Creating Simulated Accounts

```python
# Create a simulated account
simulated_account = api.add_simulated_account(
    executor,
    name="Test Account",
    driver_code="SIMULATED",
    driver_type=0  # Simulated account type
)

print(f"Simulated account created: {simulated_account.get('account_id', 'N/A')}")
```

### Testing Account Connections

```python
# Test account connection
test_result = api.test_account(
    executor,
    driver_code="BINANCE",
    driver_type=1,  # Real account type
    version=1,
    public_key="your_api_key",
    private_key="your_secret_key",
    extra_key=""  # Optional passphrase
)

if test_result.get('success'):
    print("Account connection test successful")
else:
    print(f"Account connection test failed: {test_result.get('error', 'Unknown error')}")
```

## Futures Account Features

### Position and Margin Modes

```python
from pyHaasAPI.model import PositionMode, MarginMode

# Set position mode (ONE_WAY vs HEDGE)
api.set_position_mode(executor, account_id, market, PositionMode.ONE_WAY)

# Set margin mode (CROSS vs ISOLATED)
api.set_margin_mode(executor, account_id, market, MarginMode.CROSS)

# Set leverage
api.set_leverage(executor, account_id, market, 10.0)
```

### Getting Margin Settings

```python
# Get current margin settings
settings = api.get_margin_settings(executor, account_id, market)
print(f"Position Mode: {settings.get('position_mode')}")
print(f"Margin Mode: {settings.get('margin_mode')}")
print(f"Leverage: {settings.get('leverage')}")

# Get individual settings
position_mode = api.get_position_mode(executor, account_id, market)
margin_mode = api.get_margin_mode(executor, account_id, market)
leverage = api.get_leverage(executor, account_id, market)
```

### Adjusting Margin Settings

```python
# Adjust multiple margin settings at once
api.adjust_margin_settings(
    executor,
    account_id=account_id,
    market=market,
    position_mode=PositionMode.ONE_WAY,
    margin_mode=MarginMode.CROSS,
    leverage=10.0
)
```

## Order Management

### Placing Orders

```python
# Place a limit order
order_id = api.place_order(
    executor,
    account_id=account_id,
    market="BINANCE_BTC_USDT_",
    side="buy",           # "buy" or "sell"
    price=50000.0,        # Order price
    amount=0.001,         # Order amount
    order_type=0,         # 0=limit, 1=market
    tif=0,                # 0=GTC (Good Till Canceled)
    source="Manual"       # Order source
)

print(f"Order placed: {order_id}")
```

### Canceling Orders

```python
# Cancel a specific order
success = api.cancel_order(executor, account_id, order_id)

if success:
    print("Order canceled successfully")
else:
    print("Failed to cancel order")
```

### Getting All Orders

```python
# Get all orders across all accounts
all_orders = api.get_all_orders(executor)

for order in all_orders:
    print(f"Order: {order.get('id', 'N/A')}")
    print(f"  Account: {order.get('account_id', 'N/A')}")
    print(f"  Market: {order.get('market', 'N/A')}")
    print(f"  Side: {order.get('side', 'N/A')}")
    print(f"  Status: {order.get('status', 'N/A')}")
```

### Getting All Positions

```python
# Get all positions across all accounts
all_positions = api.get_all_positions(executor)

for position in all_positions:
    print(f"Position: {position.get('market', 'N/A')}")
    print(f"  Account: {position.get('account_id', 'N/A')}")
    print(f"  Side: {position.get('side', 'N/A')}")
    print(f"  Amount: {position.get('amount', 'N/A')}")
    print(f"  P&L: {position.get('pnl', 'N/A')}")
```

## Account Analysis

### Account Performance Analysis

```python
def analyze_account_performance(account_id):
    """Analyze account performance"""
    # Get account balance
    balance = api.get_account_balance(executor, account_id)
    
    # Get account trades
    trades = api.get_account_trades(executor, account_id)
    
    # Calculate performance metrics
    total_trades = len(trades)
    winning_trades = 0
    total_pnl = 0.0
    
    for trade in trades:
        pnl = float(trade.get('pnl', 0))
        total_pnl += pnl
        if pnl > 0:
            winning_trades += 1
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    print(f"Account Performance Analysis")
    print(f"  Total Trades: {total_trades}")
    print(f"  Winning Trades: {winning_trades}")
    print(f"  Win Rate: {win_rate:.2f}%")
    print(f"  Total P&L: {total_pnl:.2f}")
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl
    }
```

### Balance Monitoring

```python
def monitor_account_balances():
    """Monitor all account balances"""
    all_balances = api.get_all_account_balances(executor)
    
    total_balance = {}
    
    for account_balance in all_balances:
        account_id = account_balance.get('account_id', 'N/A')
        wallets = account_balance.get('wallets', [])
        
        print(f"Account: {account_id}")
        for wallet in wallets:
            currency = wallet.get('currency', 'N/A')
            total = float(wallet.get('total', 0))
            
            print(f"  {currency}: {total}")
            
            # Aggregate total balance
            if currency not in total_balance:
                total_balance[currency] = 0
            total_balance[currency] += total
    
    print("\nTotal Balance Across All Accounts:")
    for currency, amount in total_balance.items():
        print(f"  {currency}: {amount}")
    
    return total_balance
```

## Best Practices

### 1. Account Validation

```python
def validate_account(account_id):
    """Validate account exists and is accessible"""
    try:
        # Try to get account data
        account_data = api.get_account_data(executor, account_id)
        
        # Check if account is active
        if account_data:
            print(f"✅ Account valid: {account_id}")
            return True
        else:
            print(f"❌ Account not found: {account_id}")
            return False
            
    except Exception as e:
        print(f"❌ Account validation failed: {account_id} - {e}")
        return False
```

### 2. Safe Account Operations

```python
def safe_account_operation(operation, account_id, *args, **kwargs):
    """Safely perform account operations with error handling"""
    try:
        # Validate account first
        if not validate_account(account_id):
            return None
        
        # Perform operation
        result = operation(executor, account_id, *args, **kwargs)
        print(f"✅ Operation successful for account {account_id}")
        return result
        
    except api.HaasApiError as e:
        print(f"❌ API error for account {account_id}: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for account {account_id}: {e}")
        return None

# Usage examples
balance = safe_account_operation(api.get_account_balance, account_id)
orders = safe_account_operation(api.get_account_orders, account_id)
```

### 3. Account Monitoring

```python
def monitor_accounts():
    """Monitor all accounts for issues"""
    accounts = api.get_accounts(executor)
    
    issues = []
    
    for account in accounts:
        print(f"Checking account: {account.name}")
        
        # Check account status
        if account.status != 1:  # Assuming 1 = active
            issues.append(f"Account {account.name} is not active (status: {account.status})")
        
        # Check balance
        try:
            balance = api.get_account_balance(executor, account.account_id)
            total_balance = sum(float(wallet.get('total', 0)) for wallet in balance.get('wallets', []))
            
            if total_balance < 10:  # Low balance threshold
                issues.append(f"Account {account.name} has low balance: {total_balance}")
                
        except Exception as e:
            issues.append(f"Failed to check balance for {account.name}: {e}")
    
    if issues:
        print("⚠️  Account Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ All accounts are healthy")
    
    return issues
```

### 4. Account Backup

```python
def backup_account_data(account_id):
    """Backup account data for analysis"""
    backup = {
        'timestamp': time.time(),
        'account_id': account_id,
        'balance': None,
        'orders': None,
        'positions': None,
        'trades': None
    }
    
    try:
        backup['balance'] = api.get_account_balance(executor, account_id)
        backup['orders'] = api.get_account_orders(executor, account_id)
        backup['positions'] = api.get_account_positions(executor, account_id)
        backup['trades'] = api.get_account_trades(executor, account_id)
        
        # Save to file
        filename = f"account_backup_{account_id}_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(backup, f, indent=2)
        
        print(f"✅ Account backup saved: {filename}")
        return backup
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None
```

## Troubleshooting

### Common Issues

1. **Account Not Found**
   - Verify account_id is correct
   - Check if account exists in the system
   - Ensure account is accessible

2. **Insufficient Balance**
   - Check account balance before placing orders
   - Verify currency availability
   - Check for reserved funds

3. **Order Placement Failures**
   - Verify market is open for trading
   - Check order parameters (price, amount)
   - Ensure account has sufficient balance

4. **API Connection Issues**
   - Verify API credentials
   - Check network connectivity
   - Ensure exchange API is accessible

### Debug Information

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed account information
def debug_account(account_id):
    print(f"Debugging account: {account_id}")
    
    try:
        account_data = api.get_account_data(executor, account_id)
        print(f"Account data: {account_data}")
    except Exception as e:
        print(f"Account data error: {e}")
    
    try:
        balance = api.get_account_balance(executor, account_id)
        print(f"Balance: {balance}")
    except Exception as e:
        print(f"Balance error: {e}")
    
    try:
        orders = api.get_account_orders(executor, account_id)
        print(f"Orders: {orders}")
    except Exception as e:
        print(f"Orders error: {e}")
```

### Performance Optimization

```python
# Cache account data for repeated access
account_cache = {}

def get_cached_account_data(account_id, cache_duration=300):
    """Get account data with caching"""
    import time
    
    current_time = time.time()
    
    if account_id in account_cache:
        cached_data, timestamp = account_cache[account_id]
        if current_time - timestamp < cache_duration:
            return cached_data
    
    # Fetch fresh data
    try:
        account_data = api.get_account_data(executor, account_id)
        account_cache[account_id] = (account_data, current_time)
        return account_data
    except Exception as e:
        print(f"Error fetching account data for {account_id}: {e}")
        return None
``` 