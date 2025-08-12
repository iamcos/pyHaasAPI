# Lab Management Guide for pyHaasAPI

## Overview

Lab management is a core feature of pyHaasAPI that enables backtesting of trading strategies. Labs provide a controlled environment for testing strategies before deploying them as live trading bots.

## Core Concepts

### Lab Components

- **Lab**: A backtesting environment with specific configuration
- **Script**: The trading strategy to test
- **Account**: The trading account to simulate
- **Market**: The trading pair to test on
- **Parameters**: Configurable settings for the strategy
- **Backtest**: The actual execution of the strategy

### Lab States

```python
from pyHaasAPI.parameters import LabStatus

# Lab status values
LabStatus.CREATED = 0      # Lab created but not started
LabStatus.QUEUED = 1       # Lab queued for execution
LabStatus.RUNNING = 2      # Lab currently running
LabStatus.COMPLETED = 3    # Lab completed successfully
LabStatus.CANCELLED = 4    # Lab cancelled
LabStatus.ERROR = 5        # Lab failed with error
```

## Lab Creation

### Basic Lab Creation

```python
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, CloudMarket

# Create a basic lab
req = CreateLabRequest.with_generated_name(
    script_id="your_script_id",
    account_id="your_account_id",
    market=market_object,  # CloudMarket instance
    exchange_code="BINANCE",
    interval=15,  # minutes
    default_price_data_style="CandleStick"
)

lab = api.create_lab(executor, req)
print(f"Lab created: {lab.name} (ID: {lab.lab_id})")
```

### Advanced Lab Creation with Custom Settings

```python
from pyHaasAPI.lab_manager import LabManager, LabSettings, LabConfig

lab_manager = LabManager(executor)

# Custom settings
settings = LabSettings(
    leverage=10.0,
    position_mode=0,  # ONE_WAY
    margin_mode=0,    # CROSS
    interval=1,       # 1 minute
    chart_style=300,
    trade_amount=100.0,
    order_template=500,
    price_data_style="CandleStick"
)

# Custom configuration
config = LabConfig(
    max_parallel=10,
    max_generations=30,
    max_epochs=3,
    max_runtime=0,  # No time limit
    auto_restart=0
)

# Create optimized lab
result = lab_manager.create_optimized_lab(
    script_id="your_script_id",
    account_id="your_account_id",
    market=market_object,
    exchange_code="BINANCE",
    lab_name="My Custom Lab",
    config=config,
    settings=settings
)
```

## Market Naming Conventions

### Spot Markets

All market tags must use the format: `<EXCHANGE>_<BASE>_<QUOTE>_`

```python
# Examples
"BINANCE_BTC_USDT_"
"KRAKEN_ETH_BTC_"
"COINBASE_ADA_USD_"
```

### Futures Markets

Futures markets use extended format: `<EXCHANGE>_<BASE>_<QUOTE>_<CONTRACT_TYPE>`

```python
# Examples
"BINANCEQUARTERLY_BTC_USD_PERPETUAL"
"BINANCEQUARTERLY_BTC_USD_QUARTERLY"
"BINANCEQUARTERLY_ETH_USD_PERPETUAL"
```

### Market Formatting

```python
from pyHaasAPI.model import CloudMarket

# Format spot market
market_tag = market.format_market_tag("BINANCE")

# Format futures market
futures_market_tag = market.format_futures_market_tag(
    "BINANCEQUARTERLY", 
    "PERPETUAL"
)
```

## Lab Configuration

### Lab Settings

```python
from pyHaasAPI.lab_manager import LabSettings

settings = LabSettings(
    leverage=10.0,           # Leverage (0.0-125.0)
    position_mode=0,         # 0=ONE_WAY, 1=HEDGE
    margin_mode=0,           # 0=CROSS, 1=ISOLATED
    interval=1,              # Chart interval in minutes
    chart_style=300,         # Chart style
    trade_amount=100.0,      # Trade amount
    order_template=500,      # Order template
    price_data_style="CandleStick"
)
```

### Lab Configuration

```python
from pyHaasAPI.lab_manager import LabConfig

config = LabConfig(
    max_parallel=10,         # Max parallel backtests
    max_generations=30,      # Max generations for optimization
    max_epochs=3,            # Max epochs per generation
    max_runtime=0,           # Max runtime in seconds (0=unlimited)
    auto_restart=0           # Auto restart on failure
)
```

## Parameter Management

### Getting Script Parameters

```python
from pyHaasAPI import api

# Get script record with parameter definitions
script_record = api.get_script_record(executor, script_id)

# Extract parameter information
for param in script_record.parameters:
    print(f"Parameter: {param.title}")
    print(f"  Type: {param.type}")
    print(f"  Default: {param.default}")
    print(f"  Min: {param.min}")
    print(f"  Max: {param.max}")
    print(f"  Options: {param.options}")
```

### Updating Lab Parameters

```python
from pyHaasAPI.parameters import ScriptParameter

# Create parameter updates
parameters = [
    ScriptParameter(
        title="param1",
        value="new_value"
    ),
    ScriptParameter(
        title="param2", 
        value=123.45
    )
]

# Update lab parameters
updated_lab = api.update_lab_parameters(
    executor, 
    lab_id, 
    parameters
)
```

### Parameter Optimization

```python
from pyHaasAPI.parameter_handler import ParameterHandler

param_handler = ParameterHandler()

# Generate parameter ranges for optimization
optimization_plan = param_handler.generate_optimization_plan(
    script_record,
    param_ranges={
        "param1": (0.1, 2.0, 0.1),  # (min, max, step)
        "param2": (10, 100, 10)
    },
    max_combinations=50
)

# Apply optimization to lab
lab_manager._apply_parameter_optimization(lab_id, optimization_plan)
```

## Lab Execution

### Starting a Backtest

```python
from pyHaasAPI.model import StartLabExecutionRequest
import time

# Create execution request
execution_req = StartLabExecutionRequest(
    lab_id=lab.lab_id,
    start_unix=int(time.time()) - (24 * 3600),  # 24 hours ago
    end_unix=int(time.time()),                   # Now
    send_email=False
)

# Start execution
result = api.start_lab_execution(executor, execution_req)
print(f"Backtest started: {result}")
```

### Monitoring Execution

```python
# Get execution status
status = api.get_lab_execution_update(executor, lab_id)
print(f"Status: {status.status}")
print(f"Progress: {status.progress}%")
print(f"Message: {status.message}")

# Wait for completion
def wait_for_completion(lab_id, timeout_minutes=30):
    start_time = time.time()
    while time.time() - start_time < timeout_minutes * 60:
        status = api.get_lab_execution_update(executor, lab_id)
        if status.status in [LabStatus.COMPLETED, LabStatus.ERROR, LabStatus.CANCELLED]:
            return status
        time.sleep(5)
    return None
```

### Getting Results

```python
from pyHaasAPI.model import GetBacktestResultRequest

# Get backtest results
req = GetBacktestResultRequest(
    lab_id=lab_id,
    next_page_id=-1,
    page_lenght=1000
)

results = api.get_backtest_result(executor, req)

# Analyze results
for result in results.items:
    print(f"Backtest ID: {result.backtest_id}")
    print(f"ROI: {result.summary.ReturnOnInvestment}")
    print(f"Profit: {result.summary.RealizedProfits}")
    print(f"Trades: {len(result.summary.Trades) if result.summary.Trades else 0}")
```

## Lab Management Operations

### Listing Labs

```python
# Get all labs
labs = api.get_all_labs(executor)

for lab in labs:
    print(f"Lab: {lab.name}")
    print(f"  ID: {lab.lab_id}")
    print(f"  Status: {lab.status}")
    print(f"  Created: {lab.created_at}")
    print(f"  Backtests: {lab.completed_backtests}")
```

### Getting Lab Details

```python
# Get detailed lab information
lab_details = api.get_lab_details(executor, lab_id)

print(f"Lab: {lab_details.name}")
print(f"Script: {lab_details.script_id}")
print(f"Account: {lab_details.settings.account_id}")
print(f"Market: {lab_details.settings.market_tag}")
print(f"Parameters: {len(lab_details.parameters)}")
```

### Updating Lab Details

```python
# Update lab name
lab_details.name = "New Lab Name"
updated_lab = api.update_lab_details(executor, lab_details)
```

### Cloning Labs

```python
# Clone existing lab
cloned_lab = api.clone_lab(executor, source_lab_id, "Cloned Lab Name")
print(f"Cloned lab: {cloned_lab.name} (ID: {cloned_lab.lab_id})")
```

### Deleting Labs

```python
# Delete lab
api.delete_lab(executor, lab_id)
print("Lab deleted successfully")
```

### Deleting All Labs Except One

To delete all labs except for a specific one, you can use the `delete_all_labs_except` endpoint on the MCP server. This is useful for cleaning up multiple test labs while preserving a golden configuration.

```python
# Example using curl to delete all labs except "Simple RSING VWAP Strategy"
# Replace "Simple RSING VWAP Strategy" with the actual name of the lab you want to keep.
curl -X DELETE http://localhost:8000/labs/delete_all_except/Simple%20RSING%20VWAP%20Strategy
```

This operation will iterate through all existing labs and delete any that do not match the provided `lab_name_to_keep`.

## Advanced Features

### Bulk Operations

```python
# Bulk clone and backtest
market_configs = [
    {"market": "BINANCE_BTC_USDT_", "account": "account1"},
    {"market": "BINANCE_ETH_USDT_", "account": "account2"},
    {"market": "KRAKEN_BTC_USD_", "account": "account3"}
]

results = api.bulk_clone_and_backtest_labs(
    executor,
    source_lab_id,
    market_configs,
    start_unix=int(time.time()) - (24 * 3600),
    end_unix=int(time.time()),
    delay_between_labs=2.0
)
```

### History Management

```python
# Ensure market history is ready
ready = api.ensure_market_history_ready(
    executor,
    market="BINANCE_BTC_USDT_",
    months=36,
    poll_interval=5,
    timeout=300
)

if ready:
    print("Market history is ready for backtesting")
else:
    print("Market history not ready")
```

### Futures Trading

```python
# Create futures lab
futures_lab = api.create_futures_lab(
    executor,
    script_id="your_script_id",
    account_id="your_account_id",
    market="BINANCEQUARTERLY_BTC_USD_PERPETUAL",
    exchange_code="BINANCEQUARTERLY",
    contract_type="PERPETUAL",
    interval=1,
    leverage=10.0,
    position_mode=0,  # ONE_WAY
    margin_mode=0     # CROSS
)
```

## Best Practices

### 1. Market Selection

```python
# Use exchange-specific market fetching for better performance
from pyHaasAPI.price import PriceAPI

price_api = PriceAPI(executor)
exchanges = ["BINANCE", "KRAKEN"]  # Skip COINBASE (has issues)

for exchange in exchanges:
    try:
        markets = price_api.get_trade_markets(exchange)
        # Process markets
    except Exception as e:
        print(f"Failed to get {exchange} markets: {e}")
        continue
```

### 2. Parameter Validation

```python
# Always validate parameters before setting them
def validate_parameter(script_record, param_name, value):
    for param in script_record.parameters:
        if param.title == param_name:
            if param.type == 0:  # INTEGER
                return int(value) >= param.min and int(value) <= param.max
            elif param.type == 1:  # DECIMAL
                return float(value) >= param.min and float(value) <= param.max
            elif param.type == 4:  # SELECTION
                return value in param.options
    return False
```

### 3. Error Handling

```python
try:
    lab = api.create_lab(executor, req)
except api.HaasApiError as e:
    print(f"Failed to create lab: {e}")
    # Handle specific error cases
    if "market" in str(e).lower():
        print("Check market configuration")
    elif "account" in str(e).lower():
        print("Check account configuration")
```

### 4. Resource Cleanup

```python
# Clean up invalid labs
def cleanup_labs():
    labs = api.get_all_labs(executor)
    for lab in labs:
        if lab.status == LabStatus.ERROR:
            try:
                api.delete_lab(executor, lab.lab_id)
                print(f"Deleted error lab: {lab.name}")
            except Exception as e:
                print(f"Failed to delete lab {lab.name}: {e}")
```

## Troubleshooting

### Common Issues

1. **Market History Not Ready**
   - Use `ensure_market_history_ready()` before backtesting
   - Set appropriate history depth with `set_history_depth()`

2. **Parameter Validation Errors**
   - Check parameter types and ranges
   - Use `get_script_record()` to get valid parameters

3. **Lab Creation Failures**
   - Verify script_id, account_id, and market_tag
   - Check license permissions
   - Ensure server is accessible

4. **Backtest Timeouts**
   - Reduce backtest time range
   - Check server performance
   - Use appropriate timeout settings

### Debug Information

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get detailed lab information
lab_details = api.get_lab_details(executor, lab_id)
print(f"Lab settings: {lab_details.settings}")
print(f"Lab config: {lab_details.config}")
print(f"Parameters: {lab_details.parameters}")
``` 