# Bulk Lab Creation Tutorial: Clone Labs to Multiple Markets

## Overview

This tutorial shows you how to use the pyHaasAPI to automatically create labs for multiple trading pairs using a single script. The process clones an existing lab (preserving all settings and parameters) and creates new labs for each specified market pair.

## Prerequisites

- pyHaasAPI installed and configured
- HaasOnline Trading Server running
- An existing lab to use as a template (e.g., "Example" lab)
- Valid account credentials

## Quick Start

### 1. Basic Usage

Create labs for specific markets using a comma-separated list:

```bash
python examples/flexible_lab_workflow.py --markets "BTC/USDT,ETH/USDT,SOL/USDT" --account-id "your-account-id"
```

### 2. Using a Markets File

Create a text file with your markets (one per line):

```txt
# my_markets.txt
BTC/USDT
ETH/USDT
SOL/USDT
ADA/USDT
XRP/USDT
```

Then run:

```bash
python examples/flexible_lab_workflow.py --markets-file my_markets.txt --account-id "your-account-id"
```

## Available Options

### Market Selection
- `--markets "BTC/USDT,ETH/USDT"` - Specify markets directly
- `--markets-file markets.txt` - Use markets from a file
- `--list-markets` - Show available markets

### Account Selection
- `--account-id "account-uuid"` - Use specific account
- `--list-accounts` - Show available accounts

### Lab Configuration
- `--source-lab "MyLab"` - Use different source lab (default: "Example")
- `--exchange "BINANCE"` - Specify exchange (default: BINANCE)

### Time Range
- `--start-time "2025-04-07 13:00"` - Custom start time
- `--end-time "2025-04-08 13:00"` - Custom end time

## Step-by-Step Process

### 1. Find Your Account ID

First, list available accounts:

```bash
python examples/flexible_lab_workflow.py --list-accounts
```

This will show something like:
```
📋 Available Accounts:
   My Binance Account (ID: 4ba07e12-0e45-48d4-9826-be139680957c)
   Test Account (ID: 12345678-1234-1234-1234-123456789abc)
```

### 2. Check Available Markets

List available markets to ensure your pairs are supported:

```bash
python examples/flexible_lab_workflow.py --list-markets
```

### 3. Validate Your Markets

Test your market list without creating labs:

```bash
python examples/flexible_lab_workflow.py --markets "BTC/USDT,ETH/USDT,INVALID/PAIR" --validate-only
```

### 4. Create Labs

Run the full workflow:

```bash
python examples/flexible_lab_workflow.py \
  --markets "BTC/USDT,ETH/USDT,SOL/USDT,ADA/USDT" \
  --account-id "4ba07e12-0e45-48d4-9826-be139680957c" \
  --source-lab "Example"
```

## What Happens Behind the Scenes

The script automatically:

1. **Authenticates** with your HaasOnline server
2. **Validates** all specified markets against available pairs
3. **Finds** the source lab (e.g., "Example")
4. **Clones** the lab for each market pair
5. **Updates** market tags and account IDs
6. **Ensures** proper backtest configuration parameters
7. **Starts** backtests for all labs
8. **Reports** success/failure for each lab

## Advanced Usage

### Custom Time Ranges

```bash
python examples/flexible_lab_workflow.py \
  --markets "BTC/USDT,ETH/USDT" \
  --account-id "your-account-id" \
  --start-time "2025-01-01 00:00" \
  --end-time "2025-01-31 23:59"
```

### Different Exchange

```bash
python examples/flexible_lab_workflow.py \
  --markets "BTC/USDT,ETH/USDT" \
  --account-id "your-account-id" \
  --exchange "KUCOIN"
```

### Custom Source Lab

```bash
python examples/flexible_lab_workflow.py \
  --markets "BTC/USDT,ETH/USDT" \
  --account-id "your-account-id" \
  --source-lab "MyCustomLab"
```

## Output and Monitoring

The script provides detailed output showing:

- ✅ **Authentication status**
- 📊 **Market validation results**
- 🔍 **Source lab identification**
- 📋 **Account selection**
- 🚀 **Lab creation progress**
- 📊 **Final results summary**

Example output:
```
🚀 Starting flexible workflow for 4 markets...
📋 Processing market 1/4: BTC_USDT_Backtest
✅ Success: BTC_USDT_Backtest (Lab: abc123-def456)
📋 Processing market 2/4: ETH_USDT_Backtest
✅ Success: ETH_USDT_Backtest (Lab: ghi789-jkl012)

📊 Final Results Summary:
✅ Successful: 4/4
❌ Failed: 0/4
Success Rate: 100.0%

🚀 All successful labs are now running backtests!
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your `.env` file credentials
   - Ensure HaasOnline server is running

2. **Account Not Found**
   - Use `--list-accounts` to see available accounts
   - Verify the account ID format

3. **Invalid Markets**
   - Use `--list-markets` to see available pairs
   - Check market format (e.g., "BTC/USDT" not "BTCUSDT")

4. **Source Lab Not Found**
   - Use `--source-lab` to specify a different lab
   - Create an "Example" lab first

### Error Handling

The script includes comprehensive error handling:
- **Market validation** before processing
- **Account verification** before use
- **Lab existence checks**
- **Individual lab error reporting**
- **Graceful failure** for invalid markets

## Best Practices

1. **Always validate first** using `--validate-only`
2. **Use specific account IDs** for production
3. **Test with a few markets** before bulk operations
4. **Monitor lab progress** in HaasOnline interface
5. **Keep market lists** in separate files for reuse

## API Integration

For programmatic use, the core functions are:

```python
from pyHaasAPI import api

# Single lab creation
result = api.clone_and_backtest_lab(
    executor=executor,
    source_lab_id="source_lab_id",
    new_lab_name="BTC_USDT_Backtest",
    market_tag="BINANCE_BTC_USDT_",
    account_id="your_account_id",
    start_unix=1744009200,
    end_unix=1752994800
)

# Bulk lab creation
market_configs = [
    {"name": "BTC_USDT_Backtest", "market_tag": "BINANCE_BTC_USDT_", "account_id": "your_account_id"},
    {"name": "ETH_USDT_Backtest", "market_tag": "BINANCE_ETH_USDT_", "account_id": "your_account_id"}
]

results = api.bulk_clone_and_backtest_labs(
    executor=executor,
    source_lab_id="source_lab_id",
    market_configs=market_configs,
    start_unix=1744009200,
    end_unix=1752994800
)
```

## Conclusion

This tutorial demonstrates how to efficiently create labs for multiple markets using pyHaasAPI. The flexible workflow script handles all the complexity of lab cloning, market configuration, and backtest execution automatically.

The system is designed to be robust and user-friendly, with comprehensive error handling and validation to ensure successful lab creation across multiple markets. 