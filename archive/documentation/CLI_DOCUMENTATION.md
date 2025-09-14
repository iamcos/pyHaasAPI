# pyHaasAPI CLI Documentation

## Overview

The pyHaasAPI library provides a comprehensive set of command-line tools for automated trading bot management, lab analysis, and account management. This documentation covers all available CLI tools and their usage patterns.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core CLI Tools](#core-cli-tools)
3. [Mass Bot Creation](#mass-bot-creation)
4. [Bot Management](#bot-management)
5. [Walk Forward Optimization (WFO)](#walk-forward-optimization-wfo)
6. [Account Management](#account-management)
7. [Price Data Tools](#price-data-tools)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

1. **Environment Setup**: Ensure you have a `.env` file with your HaasOnline credentials:
   ```bash
   HAAS_EMAIL=your-email@example.com
   HAAS_PASSWORD=your-password
   HAAS_HOST=127.0.0.1
   HAAS_PORT=8090
   ```

2. **Installation**: Install the library in development mode:
   ```bash
   pip install -e .
   ```

### Basic Usage

```bash
# Analyze a single lab and create top 3 bots
python -m pyHaasAPI.cli analyze lab-id --create-count 3 --activate

# Create bots for all qualifying labs
python -m pyHaasAPI.cli.mass_bot_creator --top-count 5 --activate

# List all available labs
python -m pyHaasAPI.cli list-labs
```

## Core CLI Tools

### 1. Main CLI Interface (`python -m pyHaasAPI.cli`)

The main CLI provides a unified interface for basic operations:

#### Analyze Lab
```bash
python -m pyHaasAPI.cli analyze <lab-id> [options]
```

**Options:**
- `--create-count N`: Number of bots to create (default: 3)
- `--activate`: Activate bots immediately after creation
- `--verify`: Verify bot configuration after creation

**Example:**
```bash
python -m pyHaasAPI.cli analyze e4616b35-8065-4095-966b-546de68fd493 --create-count 5 --activate --verify
```

#### List Labs
```bash
python -m pyHaasAPI.cli list-labs
```

**Output:** Lists all available labs with their status and basic information.

#### Complete Workflow
```bash
python -m pyHaasAPI.cli complete-workflow <lab-id> [options]
```

**Options:**
- `--create-count N`: Number of bots to create (default: 3)
- `--activate`: Activate bots after creation
- `--verify`: Verify bot configuration

**Example:**
```bash
python -m pyHaasAPI.cli complete-workflow e4616b35-8065-4095-966b-546de68fd493 --create-count 3 --activate --verify
```

## Mass Bot Creation

### 2. Mass Bot Creator (`python -m pyHaasAPI.cli.mass_bot_creator`)

The primary tool for creating bots from multiple labs with advanced filtering options.

#### Basic Usage
```bash
python -m pyHaasAPI.cli.mass_bot_creator [options]
```

#### Key Options

**Lab Selection:**
- `--lab-ids lab1,lab2,lab3`: Create bots only from specified labs
- `--exclude-lab-ids lab1,lab2`: Exclude specific labs from processing
- `--min-backtests N`: Minimum number of backtests required (default: 0)
- `--min-winrate 0.6`: Minimum win rate threshold (0.0-1.0, default: 0.0)

**Bot Creation:**
- `--top-count N`: Number of top bots to create per lab (default: 5)
- `--analyze-count N`: Number of backtests to analyze per lab (default: 100)
- `--activate`: Activate bots immediately after creation

**Trade Amount Configuration:**
- `--target-amount 2000`: Target USDT amount for trade amounts (default: 2000)
- `--method usdt|wallet`: Trade amount calculation method (default: usdt)
- `--wallet-percentage 20`: Wallet percentage for trade amounts (when method=wallet)

**Testing:**
- `--dry-run`: Show what would be created without actually creating bots

#### Examples

**Create top 5 bots from all labs:**
```bash
python -m pyHaasAPI.cli.mass_bot_creator --top-count 5 --activate
```

**Create bots only from labs with 50+ backtests and 60%+ win rate:**
```bash
python -m pyHaasAPI.cli.mass_bot_creator --min-backtests 50 --min-winrate 0.6 --top-count 3
```

**Create bots from specific labs only:**
```bash
python -m pyHaasAPI.cli.mass_bot_creator --lab-ids lab1,lab2,lab3 --top-count 3 --activate
```

**Exclude certain labs:**
```bash
python -m pyHaasAPI.cli.mass_bot_creator --exclude-lab-ids lab1,lab2 --top-count 5
```

**Dry run to see what would be created:**
```bash
python -m pyHaasAPI.cli.mass_bot_creator --dry-run --top-count 3
```

**Custom trade amounts:**
```bash
python -m pyHaasAPI.cli.mass_bot_creator --target-amount 1500 --method usdt --top-count 3
```

## Bot Management

### 3. Bot Trade Amount Manager (`python -m pyHaasAPI.cli.fix_bot_trade_amounts`)

Tool for managing and fixing bot trade amounts with various calculation methods.

#### Basic Usage
```bash
python -m pyHaasAPI.cli.fix_bot_trade_amounts [options]
```

#### Key Options

**Bot Selection:**
- `--bot-ids bot1,bot2,bot3`: Fix only specified bots
- `--exclude-bot-ids bot1,bot2`: Exclude specific bots from fixing
- `--all-bots`: Fix all bots (default behavior)

**Trade Amount Configuration:**
- `--target-amount 2000`: Target USDT amount (default: 2000)
- `--method usdt|wallet`: Calculation method (default: usdt)
- `--wallet-percentage 20`: Wallet percentage (when method=wallet)

**Leverage Recommendations:**
- `--leverage 20`: Current leverage setting for recommendations
- `--show-recommendations`: Display leverage-based risk recommendations

**Testing:**
- `--dry-run`: Show what would be changed without making changes

#### Examples

**Fix all bots to $2000 USDT equivalent:**
```bash
python -m pyHaasAPI.cli.fix_bot_trade_amounts --target-amount 2000
```

**Fix specific bots only:**
```bash
python -m pyHaasAPI.cli.fix_bot_trade_amounts --bot-ids bot1,bot2 --target-amount 1500
```

**Use wallet percentage instead of USDT amount:**
```bash
python -m pyHaasAPI.cli.fix_bot_trade_amounts --method wallet --wallet-percentage 20
```

**Get leverage recommendations:**
```bash
python -m pyHaasAPI.cli.fix_bot_trade_amounts --show-recommendations --leverage 20
```

**Dry run to see changes:**
```bash
python -m pyHaasAPI.cli.fix_bot_trade_amounts --dry-run --target-amount 2000
```

## Walk Forward Optimization (WFO)

### 4. WFO Analyzer (`python -m pyHaasAPI.cli.wfo_analyzer`)

The Walk Forward Optimization (WFO) analyzer provides comprehensive analysis of trading strategies across different time periods and market conditions.

#### Basic Usage
```bash
python -m pyHaasAPI.cli.wfo_analyzer --lab-id <lab-id> --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> [options]
```

#### Key Options

**Required Arguments:**
- `--lab-id`: Lab ID to analyze
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)

**WFO Configuration:**
- `--training-days`: Training period duration in days (default: 365)
- `--testing-days`: Testing period duration in days (default: 90)
- `--step-days`: Step size in days (default: 30)
- `--mode`: WFO mode - rolling/fixed/expanding (default: rolling)

**Performance Criteria:**
- `--min-trades`: Minimum trades required (default: 10)
- `--min-win-rate`: Minimum win rate (default: 0.4)
- `--min-profit-factor`: Minimum profit factor (default: 1.1)
- `--max-drawdown`: Maximum drawdown threshold (default: 0.3)

**Output Options:**
- `--output`: Output CSV file path
- `--dry-run`: Show what would be analyzed without running

#### Examples

**Basic WFO Analysis:**
```bash
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31
```

**Custom Training/Testing Periods:**
```bash
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --training-days 180 --testing-days 60
```

**Different WFO Modes:**
```bash
# Rolling window mode (default)
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --mode rolling

# Fixed window mode
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --mode fixed

# Expanding window mode
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --mode expanding
```

**Performance Criteria:**
```bash
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --min-trades 20 --min-win-rate 0.5 --min-profit-factor 1.2
```

**Dry Run and Output:**
```bash
# Dry run to see what would be analyzed
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --dry-run

# Custom output file
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --output wfo_report.csv
```

#### WFO Output

The WFO analyzer generates comprehensive reports including:

- **Period Analysis**: Individual WFO period results with training and testing metrics
- **Summary Metrics**: Average returns, Sharpe ratios, drawdowns, and consistency ratios
- **Stability Analysis**: Return volatility, consistency, and performance degradation
- **Best/Worst Periods**: Identification of best and worst performing periods
- **CSV Export**: Detailed results exported to CSV for further analysis

#### WFO Modes Explained

1. **Rolling Window**: Training window moves forward with each step, maintaining constant size
2. **Fixed Window**: Training window stays fixed, testing window moves forward
3. **Expanding Window**: Training window grows with each step, testing window stays constant size

## Account Management

### 4. Account Cleanup Tool (`python -m pyHaasAPI.cli.account_cleanup`)

Tool for cleaning up and organizing simulated accounts with proper naming conventions.

#### Basic Usage
```bash
python -m pyHaasAPI.cli.account_cleanup [options]
```

#### Key Options

**Account Selection:**
- `--account-type BINANCEFUTURES`: Account type to clean up (default: BINANCEFUTURES)
- `--name-pattern "4**-10k"`: Name pattern to match (default: "4**-10k")

**Naming Configuration:**
- `--prefix "[Sim]"`: Prefix to add to account names (default: "[Sim]")
- `--dry-run`: Show what would be renamed without making changes

#### Examples

**Clean up Binance Futures accounts with 4**-10k pattern:**
```bash
python -m pyHaasAPI.cli.account_cleanup
```

**Dry run to see what would be renamed:**
```bash
python -m pyHaasAPI.cli.account_cleanup --dry-run
```

**Custom naming pattern:**
```bash
python -m pyHaasAPI.cli.account_cleanup --name-pattern "test-*" --prefix "[Test]"
```

## Price Data Tools

### 5. Price Tracker (`python -m pyHaasAPI.cli.price_tracker`)

Tool for real-time price data tracking and market analysis.

#### Basic Usage
```bash
python -m pyHaasAPI.cli.price_tracker <market> [options]
```

#### Key Options

- `--market MARKET`: Market to track (e.g., BINANCEFUTURES_BTC_USDT_PERPETUAL)
- `--interval N`: Update interval in seconds (default: 5)
- `--count N`: Number of updates to show (default: unlimited)

#### Examples

**Track BTC price:**
```bash
python -m pyHaasAPI.cli.price_tracker BINANCEFUTURES_BTC_USDT_PERPETUAL
```

**Track multiple markets:**
```bash
python -m pyHaasAPI.cli.price_tracker BINANCEFUTURES_ETH_USDT_PERPETUAL --interval 10
```

## Advanced Usage

### Workflow Examples

#### Complete Bot Management Workflow

1. **Clean up accounts:**
   ```bash
   python -m pyHaasAPI.cli.account_cleanup --dry-run
   python -m pyHaasAPI.cli.account_cleanup
   ```

2. **Create bots for all qualifying labs:**
   ```bash
   python -m pyHaasAPI.cli.mass_bot_creator --min-backtests 50 --top-count 5 --activate
   ```

3. **Fix trade amounts for all bots:**
   ```bash
   python -m pyHaasAPI.cli.fix_bot_trade_amounts --target-amount 2000
   ```

4. **Verify bot configuration:**
   ```bash
   python -m pyHaasAPI.cli list-labs
   ```

#### Selective Bot Creation

1. **Create bots from specific labs only:**
   ```bash
   python -m pyHaasAPI.cli.mass_bot_creator --lab-ids lab1,lab2 --top-count 3 --activate
   ```

2. **Exclude certain labs:**
   ```bash
   python -m pyHaasAPI.cli.mass_bot_creator --exclude-lab-ids lab1,lab2 --min-backtests 100 --top-count 5
   ```

3. **High-quality bots only:**
   ```bash
   python -m pyHaasAPI.cli.mass_bot_creator --min-winrate 0.7 --min-backtests 100 --top-count 3
   ```

#### Risk Management

1. **Get leverage recommendations:**
   ```bash
   python -m pyHaasAPI.cli.fix_bot_trade_amounts --show-recommendations --leverage 20
   ```

2. **Use conservative trade amounts:**
   ```bash
   python -m pyHaasAPI.cli.fix_bot_trade_amounts --method wallet --wallet-percentage 10
   ```

3. **Dry run before making changes:**
   ```bash
   python -m pyHaasAPI.cli.mass_bot_creator --dry-run --top-count 5
   python -m pyHaasAPI.cli.fix_bot_trade_amounts --dry-run --target-amount 2000
   ```

## Bot Configuration Standards

### Standard Bot Settings

All bots created through the CLI follow these standardized configurations:

- **Position Mode**: HEDGE (1) - Always use hedge mode for risk management
- **Margin Mode**: CROSS (0) - Use cross margin for better capital efficiency  
- **Leverage**: 20x - Standard leverage for futures trading
- **Trade Amount**: $2,000 USDT equivalent - Risk management standard
- **Account Assignment**: Individual accounts - Each bot gets its own account

### Bot Naming Convention

Bots are named using the format:
```
LabName - ScriptName - ROI pop/gen WR%
```

**Example:**
```
1 ADX BB STOCH Scalper 2.7 years UNI beta Data Interval 20/30 - 1875 13/19 65%
```

Where:
- `1` = Lab name/number
- `ADX BB STOCH Scalper` = Script name
- `2.7 years UNI beta Data Interval 20/30` = Market/timeframe info
- `1875` = ROI percentage
- `13/19` = Population/Generation
- `65%` = Win rate

## Troubleshooting

### Common Issues

#### Authentication Errors
```bash
Error: Authentication failed
```
**Solution:** Check your `.env` file and ensure credentials are correct.

#### No Labs Found
```bash
No labs found matching criteria
```
**Solution:** Check lab IDs and ensure labs are in "COMPLETED" status.

#### Bot Creation Failures
```bash
Failed to create bot: Pydantic validation error
```
**Solution:** This is often a display issue - the bot was actually created successfully. Check the HaasOnline interface.

#### Account Assignment Issues
```bash
No available accounts for bot assignment
```
**Solution:** Run account cleanup tool or create more simulated accounts.

### Debug Mode

Add `--dry-run` to any command to see what would happen without making changes:

```bash
python -m pyHaasAPI.cli.mass_bot_creator --dry-run --top-count 3
python -m pyHaasAPI.cli.fix_bot_trade_amounts --dry-run --target-amount 2000
python -m pyHaasAPI.cli.account_cleanup --dry-run
```

### Logging

All CLI tools provide detailed logging output showing:
- Lab analysis progress
- Bot creation status
- Account assignment details
- Trade amount calculations
- Error messages and warnings

### Performance Tips

1. **Use caching**: The system automatically caches backtest data to speed up subsequent runs
2. **Batch operations**: Use mass bot creator for multiple labs instead of individual lab analysis
3. **Filter early**: Use `--min-backtests` and `--min-winrate` to avoid processing low-quality labs
4. **Dry run first**: Always use `--dry-run` for large operations to verify settings

## Integration with pyHaasAPI Library

The CLI tools are built on top of the core pyHaasAPI library and can be used alongside programmatic access:

```python
from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager

# Use the same underlying classes that power the CLI
cache = UnifiedCacheManager()
analyzer = HaasAnalyzer(cache)
analyzer.connect()

# Analyze and create bots programmatically
result = analyzer.analyze_lab("lab-id", top_count=5)
bots = analyzer.create_and_activate_bots(result, create_count=3, activate=True)
```

This allows for both CLI automation and custom programmatic workflows using the same robust underlying functionality.

## CLI Tool Summary

### Available Commands

| Tool | Purpose | Key Features |
|------|---------|--------------|
| `python -m pyHaasAPI.cli` | Main CLI interface | Lab analysis, bot creation, workflow management |
| `python -m pyHaasAPI.cli.mass_bot_creator` | Mass bot creation | Advanced filtering, lab selection, quality control |
| `python -m pyHaasAPI.cli.fix_bot_trade_amounts` | Bot trade amount management | Price-based calculation, risk recommendations |
| `python -m pyHaasAPI.cli.account_cleanup` | Account management | Account renaming, organization, cleanup |
| `python -m pyHaasAPI.cli.price_tracker` | Price data tracking | Real-time prices, market analysis |

### Quick Reference

**Most Common Commands:**
```bash
# Create bots for all labs
python -m pyHaasAPI.cli.mass_bot_creator --top-count 5 --activate

# Fix trade amounts
python -m pyHaasAPI.cli.fix_bot_trade_amounts --target-amount 2000

# Clean up accounts
python -m pyHaasAPI.cli.account_cleanup

# Analyze single lab
python -m pyHaasAPI.cli analyze lab-id --create-count 3 --activate
```

**Safety Commands:**
```bash
# Always dry run first
python -m pyHaasAPI.cli.mass_bot_creator --dry-run --top-count 5
python -m pyHaasAPI.cli.fix_bot_trade_amounts --dry-run --target-amount 2000
python -m pyHaasAPI.cli.account_cleanup --dry-run
```
