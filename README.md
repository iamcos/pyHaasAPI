# pyHaasAPI

A comprehensive Python library for interacting with the HaasOnline Trading Bot API.

## 🚀 Quick Start

```python
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest

# Authenticate
executor = api.RequestsExecutor(host="127.0.0.1", port=8090, state=api.Guest())
auth_executor = executor.authenticate(email="your_email", password="your_password")

# Create a lab with proper market and account assignment
from pyHaasAPI.model import CloudMarket
market = CloudMarket(category="SPOT", price_source="BINANCE", primary="BTC", secondary="USDT")

req = CreateLabRequest.with_generated_name(
    script_id="your_script_id",
    account_id="your_account_id", 
    market=market,
    exchange_code="BINANCE",
    interval=1,
    default_price_data_style="CandleStick"
)

lab = api.create_lab(auth_executor, req)
print(f"Lab created: {lab.lab_id}")
```

## 📚 Documentation

- [Lab Management](./docs/lab_management.md) - Complete guide to creating and managing labs
- [Market and Account Assignment Fix](./docs/MARKET_ACCOUNT_ASSIGNMENT_FIX.md) - Detailed explanation of the fix for market/account assignment issues
- [API Reference](./docs/api_reference.md) - Complete API documentation
- [Examples](./examples/) - Working examples and tutorials

## 🔧 Recent Fixes

### Market and Account Assignment Fix ✅

**Issue**: Labs were being created with incorrect or empty market tags and account IDs, causing them to be queued with wrong market information.

**Solution**: Fixed HTTP method and data format issues in the API layer, ensuring proper market and account assignment.

**Key Changes**:
- Fixed POST request handling for lab updates
- Added proper JSON encoding for complex objects
- Fixed indentation and syntax errors
- Enhanced parameter handling for both dict and object types

**Verification**: The `examples/lab_full_rundown.py` script now successfully creates labs with correct market tags and account IDs.

## 🎯 Key Features

- **Lab Management**: Create, update, clone, and delete labs
- **Market Operations**: Fetch markets, prices, and order books
- **Account Management**: Manage trading accounts and balances
- **Script Management**: Upload, edit, and manage trading scripts
- **Backtesting**: Run comprehensive backtests with parameter optimization
- **Bot Management**: Create and manage live trading bots
- **Order Management**: Place and manage trading orders

## 📦 Installation

```bash
pip install pyHaasAPI
```

## 🔑 Authentication

```python
from pyHaasAPI import api

# Create executor
executor = api.RequestsExecutor(
    host="127.0.0.1",  # HaasOnline API host
    port=8090,         # HaasOnline API port
    state=api.Guest()
)

# Authenticate
auth_executor = executor.authenticate(
    email="your_email@example.com",
    password="your_password"
)
```

## 🧪 Examples

### Basic Lab Creation

```python
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest, CloudMarket

# Setup market and account
market = CloudMarket(category="SPOT", price_source="BINANCE", primary="BTC", secondary="USDT")
account_id = "your_account_id"
script_id = "your_script_id"

# Create lab with proper market assignment
req = CreateLabRequest.with_generated_name(
    script_id=script_id,
    account_id=account_id,
    market=market,
    exchange_code="BINANCE",
    interval=1,
    default_price_data_style="CandleStick"
)

lab = api.create_lab(auth_executor, req)
print(f"Lab created with market: {lab.settings.market_tag}")
```

### Running a Backtest

```python
from pyHaasAPI import lab
from pyHaasAPI.domain import BacktestPeriod

# Run a 30-day backtest
period = BacktestPeriod(period_type=BacktestPeriod.Type.DAY, count=30)
results = lab.backtest(auth_executor, lab.lab_id, period)

print(f"Backtest completed with {len(results.items)} configurations")
```

### Bulk Lab Creation

```python
from pyHaasAPI.market_manager import MarketManager

# Create labs for multiple trading pairs
market_manager = MarketManager(auth_executor)
trading_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

for pair in trading_pairs:
    validation = market_manager.validate_market_setup("BINANCE", pair.split('/')[0], pair.split('/')[1])
    if validation["ready"]:
        # Create lab using the working pattern
        req = CreateLabRequest.with_generated_name(
            script_id=script_id,
            account_id=validation["account"].account_id,
            market=validation["market"],
            exchange_code="BINANCE",
            interval=1,
            default_price_data_style="CandleStick"
        )
        lab = api.create_lab(auth_executor, req)
        print(f"Created lab for {pair}: {lab.lab_id}")
```

## 🛠️ Development

### Running Tests

```bash
# Run the working example
python -m examples.lab_full_rundown

# Run specific tests
python -m pytest tests/
```

### Project Structure

```
pyHaasAPI/
├── pyHaasAPI/           # Core library
│   ├── api.py          # API client and functions
│   ├── lab.py          # Lab management functions
│   ├── model.py        # Data models and types
│   └── ...
├── examples/           # Working examples
│   ├── lab_full_rundown.py  # Complete workflow example
│   ├── bulk_create_labs_for_pairs.py  # Bulk lab creation
│   └── ...
├── docs/              # Documentation
│   ├── lab_management.md
│   ├── MARKET_ACCOUNT_ASSIGNMENT_FIX.md
│   └── ...
└── tests/             # Test suite
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [docs](./docs/) directory
- **Examples**: See the [examples](./examples/) directory
- **Issues**: Report bugs and feature requests on GitHub

## 🔄 Changelog

### Latest Changes
- ✅ Fixed market and account assignment issues
- ✅ Enhanced lab creation with proper market tag formatting
- ✅ Improved parameter handling for both dict and object types
- ✅ Added comprehensive documentation and examples
- ✅ Fixed HTTP method and data format issues in API layer

For detailed information about recent fixes, see [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md).
