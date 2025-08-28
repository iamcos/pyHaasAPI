# pyHaasAPI

A comprehensive Python library for HaasOnline API integration with advanced trading automation capabilities.

## 🚀 Features

- **Complete API Coverage**: Full HaasOnline API integration with type-safe models
- **Advanced Analysis**: Trade-level backtest data extraction with intelligent debugging
- **Market Intelligence**: Multi-exchange market discovery and classification
- **Lab Management**: Bulk lab cloning and automated configuration
- **Account Management**: Standardized account creation and naming schemas
- **Parameter Intelligence**: Advanced parameter optimization with strategic values

## 📦 Installation

```bash
pip install pyHaasAPI
```

## 🔧 Quick Start

```python
from pyHaasAPI import api
from pyHaasAPI.analysis import BacktestDataExtractor
from pyHaasAPI.markets import MarketDiscovery

# Get authenticated executor
executor = api.get_authenticated_executor()

# Extract trade data from backtest results
extractor = BacktestDataExtractor()
summary = extractor.extract_backtest_data("backtest_results.json")
print(f"Extracted {len(summary.trades)} trades with {summary.win_rate:.1f}% win rate")
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
