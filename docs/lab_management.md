# Lab Management

This section details how to manage labs using the pyHaasAPI library.

## Creating a Lab

To create a new lab, use the `create_lab` function. This requires a `CreateLabRequest` object specifying the script ID, account ID, market, interval, and other parameters.

### Basic Lab Creation

```python
from pyHaasAPI.api import create_lab
from pyHaasAPI.model import CreateLabRequest

# ... (Assuming auth_executor is already initialized) ...

lab = create_lab(auth_executor, CreateLabRequest(
    script_id="YOUR_SCRIPT_ID",  # Replace with actual script ID
    name="My Test Lab",
    account_id="YOUR_ACCOUNT_ID",  # Replace with actual account ID
    market="YOUR_MARKET_TAG",  # e.g., "BINANCE_BTC_USDT_"
    interval=15,
    default_price_data_style="CandleStick"
))

print(f"Lab created with ID: {lab.lab_id}")
```

### Recommended: Using with_generated_name() for Proper Market Assignment

For reliable market and account assignment, use the `CreateLabRequest.with_generated_name()` method:

```python
from pyHaasAPI.api import create_lab
from pyHaasAPI.model import CreateLabRequest, CloudMarket

# Create CloudMarket object
market = CloudMarket(
    category="SPOT",
    price_source="BINANCE",
    primary="BTC",
    secondary="USDT"
)

# Use the recommended pattern for proper market tag formatting
req = CreateLabRequest.with_generated_name(
    script_id="YOUR_SCRIPT_ID",
    account_id="YOUR_ACCOUNT_ID",
    market=market,
    exchange_code="BINANCE",
    interval=15,
    default_price_data_style="CandleStick"
)

lab = create_lab(auth_executor, req)
print(f"Lab created with ID: {lab.lab_id}")
print(f"Market tag: {lab.settings.market_tag}")
print(f"Account ID: {lab.settings.account_id}")
```

### Verifying Lab Creation

Always verify that the lab was created with correct settings:

```python
from pyHaasAPI.api import get_lab_details

# Get fresh lab details
lab_details = get_lab_details(auth_executor, lab.lab_id)

# Verify critical settings
settings = lab_details.settings
print(f"Market Tag: '{settings.market_tag}'")
print(f"Account ID: '{settings.account_id}'")
print(f"Trade Amount: {settings.trade_amount}")
print(f"Chart Style: {settings.chart_style}")
print(f"Order Template: {settings.order_template}")

# Check for critical issues
if not settings.market_tag or settings.market_tag == "":
    print("❌ CRITICAL: Market tag is empty!")
if not settings.account_id or settings.account_id == "":
    print("❌ CRITICAL: Account ID is empty!")
```

## Starting Lab Execution

Once a lab is created, start its execution using `start_lab_execution` and a `StartLabExecutionRequest` object specifying the start and end times.

```python
from pyHaasAPI.api import start_lab_execution
from pyHaasAPI.model import StartLabExecutionRequest
from datetime import datetime

# ... (Assuming lab object is already created) ...

end_time = int(datetime.now().timestamp())
start_time = end_time - (24 * 60 * 60 * 30) # 30 days ago

lab_details = start_lab_execution(auth_executor, StartLabExecutionRequest(
    lab_id=lab.lab_id,
    start_unix=start_time,
    end_unix=end_time,
    send_email=False
))

print(f"Lab execution started: {lab_details}")
```

## Monitoring Lab Status

Use `get_lab_details` to monitor the lab's status. The function returns a `LabDetails` object containing the current status and other information.

```python
from pyHaasAPI.api import get_lab_details

details = get_lab_details(auth_executor, lab.lab_id)
print(f"Lab status: {details.status}")
```

## Getting Backtest Results

After the lab completes, retrieve the backtest results using `get_backtest_result` and a `GetBacktestResultRequest` object.

```python
from pyHaasAPI.api import get_backtest_result
from pyHaasAPI.model import GetBacktestResultRequest

results = get_backtest_result(auth_executor, GetBacktestResultRequest(
    lab_id=lab.lab_id,
    next_page_id=0,
    page_lenght=100
))

print(f"Backtest results: {results}")
```

## Updating Lab Details

To update lab settings, use `update_lab_details`. This function properly handles the API requirements for lab updates.

```python
from pyHaasAPI.api import update_lab_details, get_lab_details

# Get current lab details
lab_details = get_lab_details(auth_executor, lab.lab_id)

# Update settings
lab_details.settings.market_tag = "BINANCE_ETH_USDT_"
lab_details.settings.trade_amount = 200.0

# Update the lab
updated_lab = update_lab_details(auth_executor, lab_details)
print(f"Lab updated: {updated_lab.name}")
```

## Deleting a Lab

To delete a lab, use the `delete_lab` function.

```python
from pyHaasAPI.api import delete_lab

delete_lab(auth_executor, lab.lab_id)
print("Lab deleted successfully")
```

## Best Practices

### 1. Market and Account Assignment

- **Always use `CreateLabRequest.with_generated_name()`** for proper market tag formatting
- **Match accounts to markets by exchange code** to ensure compatibility
- **Verify settings after creation** to catch any assignment issues early

### 2. Error Handling

The `HaasApiError` exception is raised for API errors. Implement appropriate error handling in your code.

```python
from pyHaasAPI.exceptions import HaasApiError

try:
    lab = create_lab(auth_executor, req)
    # Verify creation
    lab_details = get_lab_details(auth_executor, lab.lab_id)
    if not lab_details.settings.market_tag:
        raise HaasApiError("Lab created with empty market tag")
except HaasApiError as e:
    print(f"API Error: {e}")
```

### 3. Settings Preservation

When updating labs, always preserve critical settings:

```python
# Get current settings before making changes
original_settings = lab_details.settings

# Make your changes
lab_details.settings.trade_amount = 150.0

# Preserve critical fields
lab_details.settings.market_tag = original_settings.market_tag
lab_details.settings.account_id = original_settings.account_id

# Update
updated_lab = update_lab_details(auth_executor, lab_details)
```

### 4. Bulk Operations

For bulk lab creation, use the pattern from `examples/bulk_create_labs_for_pairs.py`:

```python
# Match accounts to markets by exchange code
account_for_market = next(
    (a for a in accounts if a.exchange_code.upper() == market.price_source.upper()), 
    None
)

# Create lab with proper market tag
market_tag = f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
req = CreateLabRequest.with_generated_name(
    script_id=script_id,
    account_id=account_for_market.account_id,
    market=market,
    exchange_code=market.price_source,
    interval=1,
    default_price_data_style="CandleStick"
)
```

## Troubleshooting

### Common Issues

1. **Empty Market Tag**: Use `CreateLabRequest.with_generated_name()` and verify after creation
2. **Empty Account ID**: Ensure account exists and is properly matched to market exchange
3. **Settings Lost During Updates**: Always preserve critical settings when updating labs
4. **API Errors**: Check that you're using the correct HTTP method and data format

### Debugging

Enable debug logging to see API requests:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing

Use the working example to verify your setup:

```bash
python -m examples.lab_full_rundown
```

## Related Documentation

- [Market and Account Assignment Fix](./MARKET_ACCOUNT_ASSIGNMENT_FIX.md) - Detailed explanation of the fix
- [Market Operations](./market_selection.org) - How to select valid markets
- [Account Management](./account_selection.org) - How to manage accounts
