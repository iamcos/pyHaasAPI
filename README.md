# pyHaasAPI

A modern Python 3.11+ client for the HaasOnline Trading Bot API, featuring advanced futures trading support with PERPETUAL and QUARTERLY contracts, position modes, margin modes, and leverage settings.

## 🚀 Features

- **Modern Python 3.11+**: Uses the latest Python features including match statements, union types (`|`), and `Self` type hints
- **Futures Trading Support**: Full support for PERPETUAL and QUARTERLY contracts
- **Advanced Trading Modes**: Position modes (ONE-WAY vs HEDGE), margin modes (CROSS vs ISOLATED)
- **Leverage Management**: Configurable leverage settings up to 125x (exchange dependent)
- **Type Safety**: Comprehensive type hints with Pydantic models
- **Async Support**: Both synchronous and asynchronous API clients
- **Comprehensive Documentation**: Full API reference and examples

## 📋 Requirements

- **Python 3.11 or higher** (required for modern syntax features)
- HaasOnline Trading Bot server running locally or remotely
- Valid HaasOnline account with API access

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pyHaasAPI.git
cd pyHaasAPI

# Create a virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

## ⚠️ SECURITY WARNING ⚠️

**DO NOT EXPOSE PRIVATE DATA IN SCRIPTS! USE .env FILE!!!**

- **NEVER** hardcode API keys, passwords, emails, or any sensitive credentials in your scripts
- **ALWAYS** use environment variables loaded from a `.env` file
- **NEVER** commit credentials to version control
- **ALWAYS** use `config/settings.py` to load credentials from environment variables
- **NEVER** share scripts containing hardcoded credentials

Example of **CORRECT** usage:
```python
from config import settings
executor = executor.authenticate(
    email=settings.API_EMAIL,  # Loaded from .env
    password=settings.API_PASSWORD  # Loaded from .env
)
```

Example of **WRONG** usage:
```python
# ❌ NEVER DO THIS!
executor = executor.authenticate(
    email="admin@admin.com",  # Hardcoded credentials
    password="adm2inadm4in!"  # Hardcoded credentials
)
```

## 🔧 Configuration

Create a `.env` file in the project root:

```env
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your_email@example.com
API_PASSWORD=your_password
```

## 🚀 Quick Start

### Basic Authentication

```python
from pyHaasAPI import api
from config import settings

# Create and authenticate executor
executor = api.RequestsExecutor(
    host=settings.API_HOST,
    port=settings.API_PORT,
    state=api.Guest()
).authenticate(
    email=settings.API_EMAIL,
    password=settings.API_PASSWORD
)
```

### Futures Trading Example

```python
from pyHaasAPI import api
from pyHaasAPI.model import CloudMarket, PositionMode, MarginMode

# Create futures market
btc_perpetual = CloudMarket(
    category="FUTURES",
    price_source="BINANCEQUARTERLY",
    primary="BTC",
    secondary="USD",
    contract_type="PERPETUAL"
)

# Format market tag
market_tag = btc_perpetual.format_futures_market_tag("BINANCEQUARTERLY", "PERPETUAL")
# Result: "BINANCEQUARTERLY_BTC_USD_PERPETUAL"

# Set position mode to ONE-WAY
api.set_position_mode(
    executor,
    account_id="your_account_id",
    market=market_tag,
    position_mode=PositionMode.ONE_WAY
)

# Set margin mode to CROSS
api.set_margin_mode(
    executor,
    account_id="your_account_id",
    market=market_tag,
    margin_mode=MarginMode.CROSS
)

# Set leverage to 50x
api.set_leverage(
    executor,
    account_id="your_account_id",
    market=market_tag,
    leverage=50.0
)
```

### Creating Futures Labs

```python
from pyHaasAPI.model import CreateLabRequest, PriceDataStyle

# Create lab for perpetual contract
lab_request = CreateLabRequest.with_futures_market(
    script_id="your_script_id",
    account_id="your_account_id",
    market=btc_perpetual,
    exchange_code="BINANCEQUARTERLY",
    interval=1,
    default_price_data_style=PriceDataStyle.CandleStick,
    contract_type="PERPETUAL"
)

# Add futures-specific settings
lab_request.leverage = 50.0
lab_request.position_mode = PositionMode.ONE_WAY
lab_request.margin_mode = MarginMode.CROSS

# Create the lab
lab = api.create_lab(executor, lab_request)
```

## 📚 Documentation

- [Account Types Reference](docs/account_types_reference.md) - Complete reference for all supported exchange account types
- [Futures Trading Guide](docs/futures_trading_guide.md) - Complete guide to futures trading features
- [API Reference](docs/api_reference.md) - Full API documentation
- [Examples](examples/) - Working examples for all features

## 🔍 Key Features Explained

### Contract Types

- **PERPETUAL**: No expiration date, most common for crypto futures
- **QUARTERLY**: Expires every 3 months, good for longer-term strategies

### Position Modes

- **ONE-WAY (0)**: Only one position at a time, simpler for beginners
- **HEDGE (1)**: Can have both long and short positions simultaneously

### Margin Modes

- **CROSS (0)**: All balance used as margin, more efficient
- **ISOLATED (1)**: Each position has allocated margin, better risk management

### Market Format

- **Spot**: `BINANCE_BTC_USDT_`
- **Perpetual**: `BINANCEQUARTERLY_BTC_USD_PERPETUAL`
- **Quarterly**: `BINANCEQUARTERLY_BTC_USD_QUARTERLY`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with coverage
pytest --cov=pyHaasAPI
```

## 📦 Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Format code
black pyHaasAPI/ tests/ examples/

# Sort imports
isort pyHaasAPI/ tests/ examples/

# Type checking
mypy pyHaasAPI/

# Linting
flake8 pyHaasAPI/ tests/ examples/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This library is for educational and research purposes. Trading cryptocurrencies involves substantial risk of loss. Use at your own risk.

## 🆘 Support

- [Documentation](docs/)
- [Issues](https://github.com/yourusername/pyHaasAPI/issues)
- [Examples](examples/)

---

**Note**: This library requires Python 3.11+ for modern syntax features like match statements and union types. Make sure you're using the correct Python version!
