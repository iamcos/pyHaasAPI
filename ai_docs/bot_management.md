# Bot Management Guide for pyHaasAPI

## Overview

Bot management in pyHaasAPI allows you to create, deploy, monitor, and control live trading bots. Bots are the live execution of trading strategies that can be created from backtested labs or configured directly.

## Core Concepts

### Bot Components

- **Bot**: Live trading instance with a specific strategy
- **Script**: The trading strategy being executed
- **Account**: The trading account used for live trades
- **Market**: The trading pair being traded
- **Settings**: Configuration including leverage, position mode, etc.
- **Parameters**: Strategy-specific parameters

### Bot States

```python
# Bot activation states
is_activated: bool      # True if bot is active
is_paused: bool        # True if bot is paused
is_favorite: bool      # True if bot is marked as favorite

# Bot status indicators
account_error: bool    # True if account has issues
script_error: bool     # True if script has errors
trade_amount_error: bool  # True if trade amount is invalid
```

## Bot Creation

### Creating Bot from Lab

```python
from pyHaasAPI import api
from pyHaasAPI.model import AddBotFromLabRequest

# Create bot from successful backtest
bot_request = AddBotFromLabRequest(
    lab_id="your_lab_id",
    backtest_id="successful_backtest_id",
    bot_name="My Trading Bot",
    account_id="your_account_id",
    market="BINANCE_BTC_USDT_",
    leverage=0  # No leverage for spot trading
)

bot = api.add_bot_from_lab(executor, bot_request)
print(f"Bot created: {bot.bot_name} (ID: {bot.bot_id})")
```

### Creating Bot Directly

```python
from pyHaasAPI import api
from pyHaasAPI.model import CreateBotRequest, CloudMarket

# Create bot directly
bot_request = CreateBotRequest(
    bot_name="Direct Bot",
    script=script_object,  # HaasScriptItemWithDependencies
    account_id="your_account_id",
    market=market_object,   # CloudMarket instance
    leverage=10.0,
    interval=15,
    chartstyle=301
)

bot = api.add_bot(executor, bot_request)
print(f"Bot created: {bot.bot_name} (ID: {bot.bot_id})")
```

### Creating Futures Bot

```python
# Create futures bot with specific settings
futures_bot = api.add_bot_from_lab_with_futures(
    executor,
    lab_id="your_lab_id",
    backtest_id="successful_backtest_id",
    bot_name="Futures Bot",
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL",
    leverage=10.0,
    position_mode=0,  # ONE_WAY
    margin_mode=0     # CROSS
)
```

## Bot Configuration

### Bot Settings

```python
from pyHaasAPI.model import HaasScriptSettings

settings = HaasScriptSettings(
    bot_id="bot_id",
    bot_name="Bot Name",
    account_id="account_id",
    market_tag="BINANCE_BTC_USDT_",
    position_mode=0,      # 0=ONE_WAY, 1=HEDGE
    margin_mode=0,        # 0=CROSS, 1=ISOLATED
    leverage=10.0,        # Leverage (0.0-125.0)
    trade_amount=100.0,   # Trade amount
    interval=15,          # Chart interval
    chart_style=300,      # Chart style
    order_template=500,   # Order template
    script_parameters={}  # Strategy parameters
)
```

### Updating Bot Settings

```python
# Update bot settings
bot.settings.trade_amount = 200.0
bot.settings.leverage = 5.0
updated_bot = api.edit_bot_parameter(executor, bot)
```

### Editing Bot Parameters

```python
# Get current bot parameters
bot = api.get_bot(executor, bot_id)

# Update specific parameters
bot.settings.script_parameters["param1"] = "new_value"
bot.settings.script_parameters["param2"] = 123.45

# Apply changes
updated_bot = api.edit_bot_parameter(executor, bot)
```

## Bot Lifecycle Management

### Activating Bots

```python
# Activate a bot
activated_bot = api.activate_bot(executor, bot_id, cleanreports=False)
print(f"Bot activated: {activated_bot.bot_name}")

# Activate with clean reports
activated_bot = api.activate_bot(executor, bot_id, cleanreports=True)
```

### Pausing and Resuming

```python
# Pause a bot
paused_bot = api.pause_bot(executor, bot_id)
print(f"Bot paused: {paused_bot.bot_name}")

# Resume a paused bot
resumed_bot = api.resume_bot(executor, bot_id)
print(f"Bot resumed: {resumed_bot.bot_name}")
```

### Deactivating Bots

```python
# Deactivate a bot
deactivated_bot = api.deactivate_bot(executor, bot_id, cancelorders=False)
print(f"Bot deactivated: {deactivated_bot.bot_name}")

# Deactivate and cancel all orders
deactivated_bot = api.deactivate_bot(executor, bot_id, cancelorders=True)
```

### Deleting Bots

```python
# Delete a bot
api.delete_bot(executor, bot_id)
print("Bot deleted successfully")
```

## Bot Monitoring

### Getting Bot Information

```python
# Get specific bot details
bot = api.get_bot(executor, bot_id)
print(f"Bot: {bot.bot_name}")
print(f"  Status: {'Active' if bot.is_activated else 'Inactive'}")
print(f"  Paused: {'Yes' if bot.is_paused else 'No'}")
print(f"  Script: {bot.script_id}")
print(f"  Account: {bot.account_id}")
print(f"  ROI: {bot.return_on_investment}")
print(f"  Realized Profit: {bot.realized_profit}")
print(f"  Unrealized Profit: {bot.urealized_profit}")
```

### Listing All Bots

```python
# Get all bots
bots = api.get_all_bots(executor)

for bot in bots:
    print(f"Bot: {bot.bot_name}")
    print(f"  ID: {bot.bot_id}")
    print(f"  Active: {bot.is_activated}")
    print(f"  ROI: {bot.return_on_investment}")
    print(f"  Profit: {bot.realized_profit}")
```

### Getting Bot Logs

```python
# Get bot runtime logbook
logs = api.get_bot_runtime_logbook(executor, bot_id, next_page_id=-1, page_length=250)

for log_entry in logs:
    print(log_entry)

# Get bot runtime information
runtime = api.get_bot_runtime(executor, bot_id)
print(f"Runtime data: {runtime}")
```

## Order Management

### Getting Bot Orders

```python
# Get all orders for a bot
orders = api.get_bot_orders(executor, bot_id)

for order in orders:
    print(f"Order: {order.get('id', 'N/A')}")
    print(f"  Side: {order.get('side', 'N/A')}")
    print(f"  Amount: {order.get('amount', 'N/A')}")
    print(f"  Price: {order.get('price', 'N/A')}")
    print(f"  Status: {order.get('status', 'N/A')}")
```

### Getting Bot Positions

```python
# Get all positions for a bot
positions = api.get_bot_positions(executor, bot_id)

for position in positions:
    print(f"Position: {position.get('market', 'N/A')}")
    print(f"  Side: {position.get('side', 'N/A')}")
    print(f"  Amount: {position.get('amount', 'N/A')}")
    print(f"  Entry Price: {position.get('entry_price', 'N/A')}")
    print(f"  Current Price: {position.get('current_price', 'N/A')}")
    print(f"  P&L: {position.get('pnl', 'N/A')}")
```

### Canceling Orders

```python
# Cancel specific order
result = api.cancel_bot_order(executor, bot_id, order_id)
print(f"Order cancellation result: {result}")

# Cancel all bot orders
result = api.cancel_all_bot_orders(executor, bot_id)
print(f"All orders cancellation result: {result}")
```

## Futures Trading Features

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

## Bulk Operations

### Deactivating All Bots

```python
# Deactivate all bots
deactivated_bots = api.deactivate_all_bots(executor)
print(f"Deactivated {len(deactivated_bots)} bots")

for bot in deactivated_bots:
    print(f"  - {bot.bot_name}")
```

### Batch Bot Management

```python
# Example: Activate multiple bots
bot_ids = ["bot1", "bot2", "bot3"]
activated_bots = []

for bot_id in bot_ids:
    try:
        bot = api.activate_bot(executor, bot_id)
        activated_bots.append(bot)
        print(f"Activated: {bot.bot_name}")
    except Exception as e:
        print(f"Failed to activate bot {bot_id}: {e}")
```

## Performance Monitoring

### Profit Tracking

```python
# Monitor bot performance
bot = api.get_bot(executor, bot_id)

print(f"Bot Performance: {bot.bot_name}")
print(f"  Realized Profit: {bot.realized_profit}")
print(f"  Unrealized Profit: {bot.urealized_profit}")
print(f"  Return on Investment: {bot.return_on_investment}%")
print(f"  Total P&L: {bot.realized_profit + bot.urealized_profit}")
```

### Error Monitoring

```python
# Check for bot errors
bot = api.get_bot(executor, bot_id)

if bot.account_error:
    print(f"⚠️  Account error detected for {bot.bot_name}")
    
if bot.script_error:
    print(f"⚠️  Script error detected for {bot.bot_name}")
    
if bot.trade_amount_error:
    print(f"⚠️  Trade amount error detected for {bot.bot_name}")
```

## Best Practices

### 1. Bot Creation Workflow

```python
def create_bot_from_lab(lab_id, backtest_id, account_id, market):
    """Create bot from successful backtest"""
    try:
        # Verify backtest was successful
        backtest_results = api.get_backtest_result(executor, {
            "lab_id": lab_id,
            "next_page_id": -1,
            "page_lenght": 1000
        })
        
        # Find the specific backtest
        target_backtest = None
        for result in backtest_results.items:
            if result.backtest_id == backtest_id:
                target_backtest = result
                break
        
        if not target_backtest:
            raise ValueError("Backtest not found")
        
        # Check if backtest was profitable
        if target_backtest.summary.ReturnOnInvestment <= 0:
            print("⚠️  Warning: Backtest was not profitable")
        
        # Create bot
        bot = api.add_bot_from_lab(executor, {
            "lab_id": lab_id,
            "backtest_id": backtest_id,
            "bot_name": f"Bot_{market}_{int(time.time())}",
            "account_id": account_id,
            "market": market,
            "leverage": 0
        })
        
        print(f"✅ Bot created: {bot.bot_name}")
        return bot
        
    except Exception as e:
        print(f"❌ Failed to create bot: {e}")
        return None
```

### 2. Bot Monitoring

```python
def monitor_bots():
    """Monitor all active bots"""
    bots = api.get_all_bots(executor)
    
    for bot in bots:
        if bot.is_activated:
            print(f"🤖 {bot.bot_name}")
            print(f"   ROI: {bot.return_on_investment:.2f}%")
            print(f"   Profit: {bot.realized_profit:.2f}")
            
            # Check for errors
            if bot.account_error or bot.script_error or bot.trade_amount_error:
                print(f"   ⚠️  Errors detected!")
                
            # Check performance
            if bot.return_on_investment < -5:
                print(f"   📉 Poor performance detected")
```

### 3. Risk Management

```python
def check_bot_risk(bot_id):
    """Check bot risk parameters"""
    bot = api.get_bot(executor, bot_id)
    
    risk_factors = []
    
    # Check leverage
    if bot.settings.leverage > 10:
        risk_factors.append(f"High leverage: {bot.settings.leverage}x")
    
    # Check losses
    if bot.realized_profit < -100:
        risk_factors.append(f"Significant losses: {bot.realized_profit}")
    
    # Check error states
    if bot.account_error:
        risk_factors.append("Account errors")
    
    if bot.script_error:
        risk_factors.append("Script errors")
    
    if risk_factors:
        print(f"⚠️  Risk factors for {bot.bot_name}:")
        for factor in risk_factors:
            print(f"   - {factor}")
        return True
    
    return False
```

### 4. Error Handling

```python
def safe_bot_operation(operation, bot_id, *args, **kwargs):
    """Safely perform bot operations with error handling"""
    try:
        result = operation(executor, bot_id, *args, **kwargs)
        print(f"✅ Operation successful for bot {bot_id}")
        return result
    except api.HaasApiError as e:
        print(f"❌ API error for bot {bot_id}: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for bot {bot_id}: {e}")
        return None

# Usage examples
safe_bot_operation(api.activate_bot, bot_id)
safe_bot_operation(api.pause_bot, bot_id)
safe_bot_operation(api.deactivate_bot, bot_id)
```

## Troubleshooting

### Common Issues

1. **Bot Creation Failures**
   - Verify account is active and has sufficient balance
   - Check script is valid and accessible
   - Ensure market is available and trading
   - Verify license permissions

2. **Bot Activation Failures**
   - Check account status and balance
   - Verify script parameters are valid
   - Ensure market is open for trading
   - Check for existing errors

3. **Bot Performance Issues**
   - Monitor logs for script errors
   - Check market conditions
   - Verify parameter settings
   - Review strategy logic

4. **Order Management Issues**
   - Check account balance
   - Verify market is open
   - Check order parameters
   - Monitor for API rate limits

### Debug Information

```python
# Get detailed bot information
bot = api.get_bot(executor, bot_id)
print(f"Bot details: {bot}")

# Get bot runtime
runtime = api.get_bot_runtime(executor, bot_id)
print(f"Runtime: {runtime}")

# Get bot logs
logs = api.get_bot_runtime_logbook(executor, bot_id)
for log in logs[-10:]:  # Last 10 log entries
    print(log)
```

### Performance Optimization

```python
# Batch operations for multiple bots
def batch_bot_operations(bot_ids, operation):
    """Perform operation on multiple bots efficiently"""
    results = []
    for bot_id in bot_ids:
        try:
            result = operation(executor, bot_id)
            results.append((bot_id, result, None))
        except Exception as e:
            results.append((bot_id, None, e))
    return results

# Example: Activate multiple bots
bot_ids = ["bot1", "bot2", "bot3"]
results = batch_bot_operations(bot_ids, api.activate_bot)

for bot_id, result, error in results:
    if error:
        print(f"❌ Failed to activate {bot_id}: {error}")
    else:
        print(f"✅ Activated {bot_id}")
``` 