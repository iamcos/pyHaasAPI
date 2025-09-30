# CLI Reference

This document provides comprehensive reference for the pyHaasAPI v2 command-line interface.

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [Lab Commands](#lab-commands)
- [Bot Commands](#bot-commands)
- [Analysis Commands](#analysis-commands)
- [Account Commands](#account-commands)
- [Script Commands](#script-commands)
- [Market Commands](#market-commands)
- [Backtest Commands](#backtest-commands)
- [Order Commands](#order-commands)
- [Configuration](#configuration)
- [Examples](#examples)

## Overview

The pyHaasAPI v2 CLI provides a unified command-line interface for all operations. It's built with async support, type safety, and comprehensive error handling.

### Basic Usage

```bash
# Main CLI entry point
python -m pyHaasAPI_v2.cli <command> <action> [options]

# Get help
python -m pyHaasAPI_v2.cli --help
python -m pyHaasAPI_v2.cli <command> --help
```

### Command Structure

```
python -m pyHaasAPI_v2.cli <command> <action> [options]
```

Where:
- `<command>`: One of `lab`, `bot`, `analysis`, `account`, `script`, `market`, `backtest`, `order`
- `<action>`: The specific action to perform
- `[options]`: Command-specific options and global options

## Global Options

These options are available for all commands:

### Connection Options

- `--host HOST`: API host (default: 127.0.0.1)
- `--port PORT`: API port (default: 8090)
- `--timeout TIMEOUT`: Request timeout in seconds (default: 30.0)

### Logging Options

- `--log-level LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--verbose, -v`: Enable verbose output

### Type Safety Options

- `--strict-mode`: Enable strict mode for type checking

### General Options

- `--dry-run`: Perform a dry run without making changes
- `--help, -h`: Show help message

## Lab Commands

Lab management operations.

### List Labs

```bash
python -m pyHaasAPI_v2.cli lab list [options]
```

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# List all labs in table format
python -m pyHaasAPI_v2.cli lab list

# List labs and save to CSV
python -m pyHaasAPI_v2.cli lab list --output-format csv --output-file labs.csv

# List labs in JSON format
python -m pyHaasAPI_v2.cli lab list --output-format json
```

### Create Lab

```bash
python -m pyHaasAPI_v2.cli lab create --name NAME --script-id SCRIPT_ID [options]
```

**Required Options:**
- `--name NAME`: Lab name
- `--script-id SCRIPT_ID`: Script ID

**Optional Options:**
- `--description DESCRIPTION`: Lab description

**Examples:**
```bash
# Create a new lab
python -m pyHaasAPI_v2.cli lab create --name "Test Lab" --script-id "script_123"

# Create lab with description
python -m pyHaasAPI_v2.cli lab create --name "Test Lab" --script-id "script_123" --description "A test lab for development"
```

### Analyze Lab

```bash
python -m pyHaasAPI_v2.cli lab analyze --lab-id LAB_ID [options]
```

**Required Options:**
- `--lab-id LAB_ID`: Lab ID to analyze

**Optional Options:**
- `--top-count COUNT`: Number of top results to show [default: 10]
- `--generate-reports`: Generate analysis reports
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Analyze lab and show top 5 results
python -m pyHaasAPI_v2.cli lab analyze --lab-id "lab_123" --top-count 5

# Analyze lab and generate reports
python -m pyHaasAPI_v2.cli lab analyze --lab-id "lab_123" --generate-reports --output-format csv
```

### Execute Lab

```bash
python -m pyHaasAPI_v2.cli lab execute --lab-id LAB_ID
```

**Required Options:**
- `--lab-id LAB_ID`: Lab ID to execute

**Examples:**
```bash
# Execute a lab
python -m pyHaasAPI_v2.cli lab execute --lab-id "lab_123"
```

### Delete Lab

```bash
python -m pyHaasAPI_v2.cli lab delete --lab-id LAB_ID
```

**Required Options:**
- `--lab-id LAB_ID`: Lab ID to delete

**Examples:**
```bash
# Delete a lab
python -m pyHaasAPI_v2.cli lab delete --lab-id "lab_123"
```

### Get Lab Status

```bash
python -m pyHaasAPI_v2.cli lab status --lab-id LAB_ID
```

**Required Options:**
- `--lab-id LAB_ID`: Lab ID to check status

**Examples:**
```bash
# Get lab status
python -m pyHaasAPI_v2.cli lab status --lab-id "lab_123"
```

## Bot Commands

Bot management operations.

### List Bots

```bash
python -m pyHaasAPI_v2.cli bot list [options]
```

**Options:**
- `--status STATUS`: Filter by status (active, inactive, paused, error)
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# List all bots
python -m pyHaasAPI_v2.cli bot list

# List only active bots
python -m pyHaasAPI_v2.cli bot list --status active

# List bots and save to CSV
python -m pyHaasAPI_v2.cli bot list --output-format csv --output-file bots.csv
```

### Create Bots

```bash
python -m pyHaasAPI_v2.cli bot create --from-lab LAB_ID [options]
```

**Required Options:**
- `--from-lab LAB_ID`: Lab ID to create bots from

**Optional Options:**
- `--count COUNT`: Number of bots to create [default: 1]
- `--activate`: Activate bots after creation

**Examples:**
```bash
# Create 3 bots from lab
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_123" --count 3

# Create and activate bots
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_123" --count 3 --activate
```

### Activate Bots

```bash
python -m pyHaasAPI_v2.cli bot activate [options]
```

**Options:**
- `--bot-ids IDS`: Comma-separated bot IDs
- `--all`: Activate all inactive bots

**Examples:**
```bash
# Activate specific bots
python -m pyHaasAPI_v2.cli bot activate --bot-ids "bot1,bot2,bot3"

# Activate all inactive bots
python -m pyHaasAPI_v2.cli bot activate --all
```

### Deactivate Bots

```bash
python -m pyHaasAPI_v2.cli bot deactivate [options]
```

**Options:**
- `--bot-ids IDS`: Comma-separated bot IDs
- `--all`: Deactivate all active bots

**Examples:**
```bash
# Deactivate specific bots
python -m pyHaasAPI_v2.cli bot deactivate --bot-ids "bot1,bot2,bot3"

# Deactivate all active bots
python -m pyHaasAPI_v2.cli bot deactivate --all
```

### Pause Bots

```bash
python -m pyHaasAPI_v2.cli bot pause --bot-ids IDS
```

**Required Options:**
- `--bot-ids IDS`: Comma-separated bot IDs

**Examples:**
```bash
# Pause specific bots
python -m pyHaasAPI_v2.cli bot pause --bot-ids "bot1,bot2"
```

### Resume Bots

```bash
python -m pyHaasAPI_v2.cli bot resume --bot-ids IDS
```

**Required Options:**
- `--bot-ids IDS`: Comma-separated bot IDs

**Examples:**
```bash
# Resume specific bots
python -m pyHaasAPI_v2.cli bot resume --bot-ids "bot1,bot2"
```

### Delete Bot

```bash
python -m pyHaasAPI_v2.cli bot delete --bot-id BOT_ID
```

**Required Options:**
- `--bot-id BOT_ID`: Bot ID to delete

**Examples:**
```bash
# Delete a bot
python -m pyHaasAPI_v2.cli bot delete --bot-id "bot_123"
```

## Analysis Commands

Analysis and reporting operations.

### Analyze Labs

```bash
python -m pyHaasAPI_v2.cli analysis labs [options]
```

**Options:**
- `--lab-id LAB_ID`: Specific lab ID to analyze
- `--top-count COUNT`: Number of top results to show [default: 10]
- `--generate-reports`: Generate analysis reports
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path
- `--min-roi ROI`: Minimum ROI filter
- `--min-winrate RATE`: Minimum win rate filter
- `--min-trades TRADES`: Minimum trades filter

**Examples:**
```bash
# Analyze all labs
python -m pyHaasAPI_v2.cli analysis labs

# Analyze specific lab
python -m pyHaasAPI_v2.cli analysis labs --lab-id "lab_123" --top-count 5

# Analyze with filters and generate reports
python -m pyHaasAPI_v2.cli analysis labs --min-roi 100 --min-winrate 0.6 --generate-reports
```

### Analyze Bots

```bash
python -m pyHaasAPI_v2.cli analysis bots [options]
```

**Options:**
- `--bot-id BOT_ID`: Specific bot ID to analyze
- `--performance-metrics`: Include performance metrics
- `--generate-reports`: Generate analysis reports
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Analyze all bots
python -m pyHaasAPI_v2.cli analysis bots

# Analyze specific bot with performance metrics
python -m pyHaasAPI_v2.cli analysis bots --bot-id "bot_123" --performance-metrics
```

### Walk Forward Optimization

```bash
python -m pyHaasAPI_v2.cli analysis wfo --lab-id LAB_ID --start-date DATE --end-date DATE [options]
```

**Required Options:**
- `--lab-id LAB_ID`: Lab ID for WFO analysis
- `--start-date DATE`: Start date (YYYY-MM-DD)
- `--end-date DATE`: End date (YYYY-MM-DD)

**Optional Options:**
- `--generate-reports`: Generate WFO reports
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Perform WFO analysis
python -m pyHaasAPI_v2.cli analysis wfo --lab-id "lab_123" --start-date "2022-01-01" --end-date "2023-12-31"

# WFO analysis with report generation
python -m pyHaasAPI_v2.cli analysis wfo --lab-id "lab_123" --start-date "2022-01-01" --end-date "2023-12-31" --generate-reports
```

### Performance Analysis

```bash
python -m pyHaasAPI_v2.cli analysis performance [options]
```

**Options:**
- `--generate-reports`: Generate performance reports
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Analyze performance metrics
python -m pyHaasAPI_v2.cli analysis performance

# Generate performance report
python -m pyHaasAPI_v2.cli analysis performance --generate-reports --output-format csv
```

### Generate Reports

```bash
python -m pyHaasAPI_v2.cli analysis reports [options]
```

**Options:**
- `--lab-id LAB_ID`: Lab ID for report generation
- `--bot-id BOT_ID`: Bot ID for report generation
- `--format FORMAT`: Report format (json, csv, html, markdown) [default: csv]
- `--output-dir DIR`: Output directory [default: reports]

**Examples:**
```bash
# Generate lab analysis report
python -m pyHaasAPI_v2.cli analysis reports --lab-id "lab_123" --format csv

# Generate bot analysis report
python -m pyHaasAPI_v2.cli analysis reports --bot-id "bot_123" --format html
```

## Account Commands

Account management operations.

### List Accounts

```bash
python -m pyHaasAPI_v2.cli account list [options]
```

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# List all accounts
python -m pyHaasAPI_v2.cli account list

# List accounts and save to CSV
python -m pyHaasAPI_v2.cli account list --output-format csv --output-file accounts.csv
```

### Get Account Balance

```bash
python -m pyHaasAPI_v2.cli account balance --account-id ACCOUNT_ID
```

**Required Options:**
- `--account-id ACCOUNT_ID`: Account ID

**Examples:**
```bash
# Get account balance
python -m pyHaasAPI_v2.cli account balance --account-id "account_123"
```

### Account Settings

```bash
python -m pyHaasAPI_v2.cli account settings --account-id ACCOUNT_ID [options]
```

**Required Options:**
- `--account-id ACCOUNT_ID`: Account ID

**Options:**
- `--leverage LEVERAGE`: Set leverage
- `--margin-mode MODE`: Set margin mode (cross, isolated)
- `--position-mode MODE`: Set position mode (hedge, one_way)

**Examples:**
```bash
# Set account leverage
python -m pyHaasAPI_v2.cli account settings --account-id "account_123" --leverage 20

# Set margin and position modes
python -m pyHaasAPI_v2.cli account settings --account-id "account_123" --margin-mode cross --position-mode hedge
```

### Account Orders

```bash
python -m pyHaasAPI_v2.cli account orders --account-id ACCOUNT_ID [options]
```

**Required Options:**
- `--account-id ACCOUNT_ID`: Account ID

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get account orders
python -m pyHaasAPI_v2.cli account orders --account-id "account_123"

# Get account orders and save to CSV
python -m pyHaasAPI_v2.cli account orders --account-id "account_123" --output-format csv
```

### Account Positions

```bash
python -m pyHaasAPI_v2.cli account positions --account-id ACCOUNT_ID [options]
```

**Required Options:**
- `--account-id ACCOUNT_ID`: Account ID

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get account positions
python -m pyHaasAPI_v2.cli account positions --account-id "account_123"
```

## Script Commands

Script management operations.

### List Scripts

```bash
python -m pyHaasAPI_v2.cli script list [options]
```

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# List all scripts
python -m pyHaasAPI_v2.cli script list

# List scripts and save to CSV
python -m pyHaasAPI_v2.cli script list --output-format csv --output-file scripts.csv
```

### Create Script

```bash
python -m pyHaasAPI_v2.cli script create --name NAME --source SOURCE [options]
```

**Required Options:**
- `--name NAME`: Script name
- `--source SOURCE`: Script source code

**Optional Options:**
- `--description DESCRIPTION`: Script description

**Examples:**
```bash
# Create a new script
python -m pyHaasAPI_v2.cli script create --name "Test Script" --source "print('Hello, World!')"

# Create script with description
python -m pyHaasAPI_v2.cli script create --name "Test Script" --source "print('Hello, World!')" --description "A test script"
```

### Edit Script

```bash
python -m pyHaasAPI_v2.cli script edit --script-id SCRIPT_ID [options]
```

**Required Options:**
- `--script-id SCRIPT_ID`: Script ID

**Options:**
- `--name NAME`: New script name
- `--source SOURCE`: New script source code
- `--description DESCRIPTION`: New script description

**Examples:**
```bash
# Edit script name
python -m pyHaasAPI_v2.cli script edit --script-id "script_123" --name "Updated Script"

# Edit script source code
python -m pyHaasAPI_v2.cli script edit --script-id "script_123" --source "print('Updated!')"
```

### Delete Script

```bash
python -m pyHaasAPI_v2.cli script delete --script-id SCRIPT_ID
```

**Required Options:**
- `--script-id SCRIPT_ID`: Script ID to delete

**Examples:**
```bash
# Delete a script
python -m pyHaasAPI_v2.cli script delete --script-id "script_123"
```

### Test Script

```bash
python -m pyHaasAPI_v2.cli script test --script-id SCRIPT_ID
```

**Required Options:**
- `--script-id SCRIPT_ID`: Script ID to test

**Examples:**
```bash
# Test a script
python -m pyHaasAPI_v2.cli script test --script-id "script_123"
```

### Publish Script

```bash
python -m pyHaasAPI_v2.cli script publish --script-id SCRIPT_ID
```

**Required Options:**
- `--script-id SCRIPT_ID`: Script ID to publish

**Examples:**
```bash
# Publish a script
python -m pyHaasAPI_v2.cli script publish --script-id "script_123"
```

## Market Commands

Market data operations.

### List Markets

```bash
python -m pyHaasAPI_v2.cli market list [options]
```

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# List all markets
python -m pyHaasAPI_v2.cli market list

# List markets and save to CSV
python -m pyHaasAPI_v2.cli market list --output-format csv --output-file markets.csv
```

### Get Price Data

```bash
python -m pyHaasAPI_v2.cli market price --market MARKET [options]
```

**Required Options:**
- `--market MARKET`: Market tag

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get price data for BTC/USDT
python -m pyHaasAPI_v2.cli market price --market "BTC_USDT_PERPETUAL"

# Get price data and save to JSON
python -m pyHaasAPI_v2.cli market price --market "BTC_USDT_PERPETUAL" --output-format json
```

### Get Historical Data

```bash
python -m pyHaasAPI_v2.cli market history --market MARKET [options]
```

**Required Options:**
- `--market MARKET`: Market tag

**Options:**
- `--days DAYS`: Number of days for history
- `--interval INTERVAL`: Data interval
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get 30 days of historical data
python -m pyHaasAPI_v2.cli market history --market "BTC_USDT_PERPETUAL" --days 30

# Get historical data with specific interval
python -m pyHaasAPI_v2.cli market history --market "BTC_USDT_PERPETUAL" --days 7 --interval "1h"
```

### Validate Market

```bash
python -m pyHaasAPI_v2.cli market validate --market MARKET
```

**Required Options:**
- `--market MARKET`: Market tag to validate

**Examples:**
```bash
# Validate a market
python -m pyHaasAPI_v2.cli market validate --market "BTC_USDT_PERPETUAL"
```

## Backtest Commands

Backtest operations.

### List Backtests

```bash
python -m pyHaasAPI_v2.cli backtest list --lab-id LAB_ID [options]
```

**Required Options:**
- `--lab-id LAB_ID`: Lab ID

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# List backtests for a lab
python -m pyHaasAPI_v2.cli backtest list --lab-id "lab_123"

# List backtests and save to CSV
python -m pyHaasAPI_v2.cli backtest list --lab-id "lab_123" --output-format csv
```

### Run Backtest

```bash
python -m pyHaasAPI_v2.cli backtest run --lab-id LAB_ID --script-id SCRIPT_ID [options]
```

**Required Options:**
- `--lab-id LAB_ID`: Lab ID
- `--script-id SCRIPT_ID`: Script ID

**Options:**
- `--market MARKET`: Market tag

**Examples:**
```bash
# Run a backtest
python -m pyHaasAPI_v2.cli backtest run --lab-id "lab_123" --script-id "script_456"

# Run backtest with specific market
python -m pyHaasAPI_v2.cli backtest run --lab-id "lab_123" --script-id "script_456" --market "BTC_USDT_PERPETUAL"
```

### Get Backtest Results

```bash
python -m pyHaasAPI_v2.cli backtest results --backtest-id BACKTEST_ID [options]
```

**Required Options:**
- `--backtest-id BACKTEST_ID`: Backtest ID

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get backtest results
python -m pyHaasAPI_v2.cli backtest results --backtest-id "backtest_123"

# Get backtest results and save to JSON
python -m pyHaasAPI_v2.cli backtest results --backtest-id "backtest_123" --output-format json
```

### Get Backtest Chart

```bash
python -m pyHaasAPI_v2.cli backtest chart --backtest-id BACKTEST_ID [options]
```

**Required Options:**
- `--backtest-id BACKTEST_ID`: Backtest ID

**Options:**
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get backtest chart
python -m pyHaasAPI_v2.cli backtest chart --backtest-id "backtest_123"

# Get backtest chart and save to file
python -m pyHaasAPI_v2.cli backtest chart --backtest-id "backtest_123" --output-file chart.png
```

### Get Backtest Log

```bash
python -m pyHaasAPI_v2.cli backtest log --backtest-id BACKTEST_ID [options]
```

**Required Options:**
- `--backtest-id BACKTEST_ID`: Backtest ID

**Options:**
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get backtest log
python -m pyHaasAPI_v2.cli backtest log --backtest-id "backtest_123"

# Get backtest log and save to file
python -m pyHaasAPI_v2.cli backtest log --backtest-id "backtest_123" --output-file log.txt
```

## Order Commands

Order management operations.

### List Orders

```bash
python -m pyHaasAPI_v2.cli order list --bot-id BOT_ID [options]
```

**Required Options:**
- `--bot-id BOT_ID`: Bot ID

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# List orders for a bot
python -m pyHaasAPI_v2.cli order list --bot-id "bot_123"

# List orders and save to CSV
python -m pyHaasAPI_v2.cli order list --bot-id "bot_123" --output-format csv
```

### Place Order

```bash
python -m pyHaasAPI_v2.cli order place --bot-id BOT_ID --side SIDE --amount AMOUNT [options]
```

**Required Options:**
- `--bot-id BOT_ID`: Bot ID
- `--side SIDE`: Order side (buy, sell)
- `--amount AMOUNT`: Order amount

**Options:**
- `--price PRICE`: Order price

**Examples:**
```bash
# Place a market order
python -m pyHaasAPI_v2.cli order place --bot-id "bot_123" --side buy --amount 1000

# Place a limit order
python -m pyHaasAPI_v2.cli order place --bot-id "bot_123" --side buy --amount 1000 --price 50000
```

### Cancel Order

```bash
python -m pyHaasAPI_v2.cli order cancel --order-id ORDER_ID
```

**Required Options:**
- `--order-id ORDER_ID`: Order ID to cancel

**Examples:**
```bash
# Cancel an order
python -m pyHaasAPI_v2.cli order cancel --order-id "order_123"
```

### Get Order Status

```bash
python -m pyHaasAPI_v2.cli order status --order-id ORDER_ID
```

**Required Options:**
- `--order-id ORDER_ID`: Order ID

**Examples:**
```bash
# Get order status
python -m pyHaasAPI_v2.cli order status --order-id "order_123"
```

### Get Order History

```bash
python -m pyHaasAPI_v2.cli order history --bot-id BOT_ID [options]
```

**Required Options:**
- `--bot-id BOT_ID`: Bot ID

**Options:**
- `--output-format FORMAT`: Output format (json, csv, table) [default: table]
- `--output-file FILE`: Output file path

**Examples:**
```bash
# Get order history for a bot
python -m pyHaasAPI_v2.cli order history --bot-id "bot_123"

# Get order history and save to CSV
python -m pyHaasAPI_v2.cli order history --bot-id "bot_123" --output-format csv
```

## Configuration

### Environment Variables

The CLI uses the following environment variables:

```bash
# Required
export API_EMAIL="your_email@example.com"
export API_PASSWORD="your_password"

# Optional
export API_HOST="127.0.0.1"
export API_PORT="8090"
export API_TIMEOUT="30.0"
export API_STRICT_MODE="false"
```

### Configuration Files

You can also use configuration files:

```yaml
# config.yaml
api:
  host: "127.0.0.1"
  port: 8090
  timeout: 30.0
  strict_mode: false

auth:
  email: "your_email@example.com"
  password: "your_password"

logging:
  level: "INFO"
  verbose: false
```

## Examples

### Complete Workflow Example

```bash
# 1. List all labs
python -m pyHaasAPI_v2.cli lab list

# 2. Analyze a lab
python -m pyHaasAPI_v2.cli lab analyze --lab-id "lab_123" --top-count 5 --generate-reports

# 3. Create bots from lab analysis
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_123" --count 3 --activate

# 4. Check bot status
python -m pyHaasAPI_v2.cli bot list --status active

# 5. Monitor bot performance
python -m pyHaasAPI_v2.cli analysis bots --performance-metrics
```

### Batch Operations Example

```bash
# 1. Analyze multiple labs
python -m pyHaasAPI_v2.cli analysis labs --generate-reports --output-format csv

# 2. Create bots from multiple labs
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_123" --count 5
python -m pyHaasAPI_v2.cli bot create --from-lab "lab_456" --count 3

# 3. Activate all bots
python -m pyHaasAPI_v2.cli bot activate --all

# 4. Monitor all bots
python -m pyHaasAPI_v2.cli analysis bots --performance-metrics
```

### Data Export Example

```bash
# 1. Export all labs to CSV
python -m pyHaasAPI_v2.cli lab list --output-format csv --output-file all_labs.csv

# 2. Export all bots to JSON
python -m pyHaasAPI_v2.cli bot list --output-format json --output-file all_bots.json

# 3. Export account data
python -m pyHaasAPI_v2.cli account list --output-format csv --output-file all_accounts.csv

# 4. Export market data
python -m pyHaasAPI_v2.cli market list --output-format csv --output-file all_markets.csv
```

### Analysis and Reporting Example

```bash
# 1. Perform comprehensive analysis
python -m pyHaasAPI_v2.cli analysis labs --generate-reports --output-format csv

# 2. Walk Forward Optimization
python -m pyHaasAPI_v2.cli analysis wfo --lab-id "lab_123" --start-date "2022-01-01" --end-date "2023-12-31" --generate-reports

# 3. Performance analysis
python -m pyHaasAPI_v2.cli analysis performance --generate-reports

# 4. Generate custom reports
python -m pyHaasAPI_v2.cli analysis reports --lab-id "lab_123" --format html --output-dir reports/
```

---

This CLI reference provides comprehensive documentation for all pyHaasAPI v2 command-line operations. For more detailed examples and usage patterns, see the [Examples](examples.md) document.
