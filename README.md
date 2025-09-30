# pyHaasAPI

A modern, async-first Python library for HaasOnline API integration with advanced trading automation capabilities.

## 🆕 What's New in v2.0

- **Modern Async Architecture**: Complete rewrite with async/await support throughout
- **Type Safety**: Comprehensive type hints with Pydantic v2 validation
- **Domain-Separated APIs**: Clean, modular API design with 7 specialized modules
- **Service Layer**: High-level business logic services for complex operations
- **Advanced CLI**: Unified command-line interface with subcommands
- **Comprehensive Testing**: 100% test coverage with performance and error handling tests
- **Enhanced Error Handling**: Structured exception hierarchy with recovery suggestions

## 🚀 Features

- **Complete API Coverage**: Full HaasOnline API integration with type-safe models
- **Advanced Analysis**: Trade-level backtest data extraction with intelligent debugging
- **Market Intelligence**: Multi-exchange market discovery and classification
- **Lab Management**: Bulk lab cloning and automated configuration
- **Account Management**: Standardized account creation and naming schemas
- **Parameter Intelligence**: Advanced parameter optimization with strategic values
- **🆕 Mass Bot Creation**: Create bots from top backtests across all labs with advanced filtering
- **🆕 Smart Trade Amounts**: Price-based trade amount calculation with intelligent precision
- **🆕 Bot Management Tools**: Comprehensive bot configuration and trade amount management
- **🆕 Walk Forward Optimization (WFO)**: Comprehensive WFO analysis with multiple modes and stability scoring

## 📦 Installation

```bash
pip install pyHaasAPI
```

## 🔧 Quick Start

### Modern Async API (v2.0)

```python
import asyncio
from pyHaasAPI import AsyncHaasClient, AuthenticationManager, LabAPI, BotAPI

async def main():
    # Create async client
    client = AsyncHaasClient(host="127.0.0.1", port=8090)
    auth_manager = AuthenticationManager(email="your@email.com", password="password")
    
    # Authenticate
    await auth_manager.authenticate()
    
    # Create API instances
    lab_api = LabAPI(client, auth_manager)
    bot_api = BotAPI(client, auth_manager)
    
    # List all labs
    labs = await lab_api.get_labs()
    print(f"Found {len(labs)} labs")
    
    # Create a bot
    bot = await bot_api.create_bot(
        bot_name="My Bot",
        script_id="script123",
        script_type="HaasScript",
        account_id="account123",
        market="BINANCE_BTC_USDT_"
    )
    print(f"Created bot: {bot.bot_id}")

# Run the async function
asyncio.run(main())
```

### Legacy Sync API (v1.0)

```python
from pyHaasAPI_v1 import api
from pyHaasAPI_v1.analysis import BacktestDataExtractor

# Get authenticated executor
executor = api.get_authenticated_executor()

# Extract trade data from backtest results
extractor = BacktestDataExtractor()
summary = extractor.extract_backtest_data("backtest_results.json")
print(f"Extracted {len(summary.trades)} trades with {summary.win_rate:.1f}% win rate")
```

## 🛠️ CLI Tools

The `pyHaasAPI/cli/` directory contains powerful command-line tools for automated trading:

### Unified CLI (v2.0)
```bash
# Lab management
python -m pyHaasAPI.cli lab list
python -m pyHaasAPI.cli lab create --script-id script123 --name "My Lab"
python -m pyHaasAPI.cli lab analyze lab123 --top-count 5

# Bot management
python -m pyHaasAPI.cli bot list
python -m pyHaasAPI.cli bot create --from-lab lab123 --count 3 --activate
python -m pyHaasAPI.cli bot analyze bot123

# Analysis and backtesting
python -m pyHaasAPI.cli analysis labs --generate-reports
python -m pyHaasAPI.cli backtest execute --lab-id lab123 --iterations 1000
```

### Legacy CLI Tools (v1.0)
```bash
# Mass bot creation
python -m pyHaasAPI_v1.cli.mass_bot_creator --top-count 5 --activate
python -m pyHaasAPI_v1.cli.mass_bot_creator --min-backtests 50 --min-winrate 0.6

# Create bots from specific labs only
python -m pyHaasAPI.cli.mass_bot_creator --lab-ids lab1,lab2 --top-count 3
```

### Bot Trade Amount Management
```bash
# Fix all bots to $2000 USDT equivalent
python -m pyHaasAPI.cli.fix_bot_trade_amounts --target-amount 2000

# Use wallet percentage instead of USDT amount
python -m pyHaasAPI.cli.fix_bot_trade_amounts --method wallet --wallet-percentage 20

# Get leverage recommendations
python -m pyHaasAPI.cli.fix_bot_trade_amounts --show-recommendations
```

### Walk Forward Optimization (WFO)
```bash
# Basic WFO analysis
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31

# Custom training/testing periods
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --training-days 180 --testing-days 60

# Fixed window mode with custom step
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --mode fixed --step-days 45

# Dry run to see what would be analyzed
python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --dry-run
```

### Account Management
```bash
# Clean up simulated accounts with proper naming
python -m pyHaasAPI.cli.account_cleanup

# Track real-time price data
python -m pyHaasAPI.cli.price_tracker BTC_USDT_PERPETUAL
```

## 📋 Examples

The `examples/` directory contains ready-to-use scripts for common tasks:

### Account Management
- **`setup_trading_accounts.py`** - Creates 200 standardized trading accounts (4AA-10K-XXX) with exactly 10,000 USDT each
- **`verify_accounts.py`** - Verifies account setup and balance correctness
- **`cleanup_accounts.py`** - Cleans up accounts to ensure only USDT balances

### Quick Setup
```bash
# Set up your environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your HaasOnline API credentials
echo "API_HOST=127.0.0.1" >> .env
echo "API_PORT=8090" >> .env
echo "API_EMAIL=your_email@example.com" >> .env
echo "API_PASSWORD=your_password" >> .env

# Set up 200 trading accounts
python examples/setup_trading_accounts.py

# Verify the setup
python examples/verify_accounts.py
```

## 📚 Documentation

- [Parameter Optimization Algorithm](docs/PARAMETER_OPTIMIZATION_ALGORITHM.md)
- [Quick Reference Guide](docs/PARAMETER_OPTIMIZATION_QUICK_REFERENCE.md)
- [Complete Documentation](docs/README.md)

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for reliable, scalable trading automation**
