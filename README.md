# Haaslib: A Python Library for Interacting with the HaasOnline API

Haaslib is a Python library designed to simplify interaction with the HaasOnline API.  It provides a robust and efficient way to manage labs, bots, scripts, and other resources within the HaasOnline ecosystem.

## Key Features

* **Simplified API Interaction:** Haaslib abstracts away the complexities of the HaasOnline API, providing a clean and intuitive Pythonic interface.
* **Robust Error Handling:** The library incorporates comprehensive error handling, including custom exceptions for common API errors and detailed logging for debugging.
* **Type Safety:** Leveraging Pydantic models, Haaslib ensures type safety for all API requests and responses, reducing the risk of runtime errors.
* **Efficient Resource Management:** The library provides efficient methods for managing labs, bots, and other resources, with automatic cleanup and resource optimization.
* **Comprehensive Trading Operations:** Full support for bot control (activate, deactivate, pause, resume), order management, and real-time market data.
* **Complete Account Management:** Monitor balances, positions, orders, and trade history across all accounts.
* **Advanced Lab Management:** Create, configure, and execute backtests with parameter optimization and detailed results analysis.

## Quick Start

### Installation

```bash
pip install pyHaasAPI
```

### Basic Usage

```python
from pyHaasAPI import api

# Initialize and authenticate
executor = api.RequestsExecutor(
    host="your-haasonline-server.com",
    port=8090,
    state=api.Guest()
).authenticate(email="your-email", password="your-password")

# Get all markets
markets = api.get_all_markets(executor)

# Get account information
accounts = api.get_accounts(executor)

# Create a lab for backtesting
lab = api.create_lab(executor, CreateLabRequest(...))

# Start lab execution
api.start_lab_execution(executor, StartLabExecutionRequest(...))

# Get lab results
results = api.get_backtest_result(executor, GetBacktestResultRequest(...))

# Create a bot from lab results
bot = api.add_bot_from_lab(executor, AddBotFromLabRequest(...))

# Control bot trading
api.activate_bot(executor, bot.bot_id)  # Start trading
api.pause_bot(executor, bot.bot_id)     # Pause trading
api.resume_bot(executor, bot.bot_id)    # Resume trading
api.deactivate_bot(executor, bot.bot_id) # Stop trading

# Monitor orders and positions
orders = api.get_bot_orders(executor, bot.bot_id)
positions = api.get_bot_positions(executor, bot.bot_id)

# Get market data
price = api.get_market_price(executor, "BINANCE_BTC_USDT")
order_book = api.get_order_book(executor, "BINANCE_BTC_USDT", depth=20)
trades = api.get_last_trades(executor, "BINANCE_BTC_USDT", limit=100)

# Monitor account status
balance = api.get_account_balance(executor, account.account_id)
account_orders = api.get_account_orders(executor, account.account_id)
account_positions = api.get_account_positions(executor, account.account_id)
```

## 🚀 **Efficient Market Fetching**

**IMPORTANT**: For better performance and reliability, use exchange-specific market fetching instead of `get_all_markets()`.

### ❌ **Avoid This (Slow/Unreliable)**
```python
# This can timeout and is slow
markets = api.get_all_markets(executor)
```

### ✅ **Use This Instead (Fast/Reliable)**
```python
from pyHaasAPI.price import PriceAPI

price_api = PriceAPI(executor)
all_markets = []

# Fetch markets by exchange (much faster)
exchanges = ["BINANCE", "KRAKEN"]  # Skip COINBASE as it has issues
for exchange in exchanges:
    try:
        exchange_markets = price_api.get_trade_markets(exchange)
        all_markets.extend(exchange_markets)
        print(f"Found {len(exchange_markets)} {exchange} markets")
    except Exception as e:
        print(f"Failed to get {exchange} markets: {e}")
        continue
```

### **Why This Matters**
- **Speed**: Exchange-specific endpoints are 10x faster than `get_all_markets()`
- **Reliability**: Avoids 504 Gateway Timeout errors from server overload
- **Scalability**: Can fetch markets incrementally by exchange
- **Error Handling**: Individual exchange failures don't break the entire operation

### **Example Implementation**
See `examples/mcp_scalper_sweep.py` for a complete implementation using efficient market fetching for automated lab deployment and parameter optimization.

## Licensing

**pyHaasAPI is free for individual traders, experimenters, and research institutions.**

### Free Usage
- **Individual Traders & Experimenters**: Personal trading, educational purposes, non-commercial research
- **Research Institutions**: Academic research, university projects, non-profit organizations

### Commercial Licensing
Commercial licensing is required for hedge funds and financial institutions. We offer flexible partnership arrangements including custom integrations, priority support, and advanced features.

For detailed licensing information, see [LICENSING.md](LICENSING.md).

## API Discovery & Reverse Engineering

This library was developed through reverse engineering of the HaasOnline API. Our discovery process included:

### 🔍 **Reverse Engineering Methodology**
- **API Endpoint Mapping**: Identified and documented 108+ API endpoints across 6 main categories
- **Request/Response Analysis**: Mapped field aliases and response structures using Pydantic models
- **Authentication Flow**: Implemented two-step authentication (credentials + one-time code)
- **Parameter Management**: Discovered complex parameter system with type validation and range constraints

### 📊 **Current Implementation Status**
- **✅ 42 endpoints implemented** (39% coverage)
- **🔄 3 areas partially implemented**
- **❌ 66 endpoints remaining** (61% to implement)

### 🎯 **Key Discoveries**
- **Bot Control System**: Complete lifecycle management (create, activate, pause, resume, deactivate)
- **Order Management**: Real-time order tracking and cancellation capabilities
- **Account Monitoring**: Comprehensive balance, position, and trade history access
- **Market Data**: Real-time price feeds, order books, and trade data
- **Lab Optimization**: Advanced backtesting with parameter optimization and result analysis
- **Lab Cloning**: Duplicate successful configurations with all parameters preserved
- **Script Management**: Complete script lifecycle (upload, edit, delete, publish, search)
- **Advanced Analytics**: Detailed backtest runtime data, charts, and execution logs

### 🧪 **Testing & Validation**
- **Reference Implementation**: `examples/lab_parameters.py` serves as comprehensive test suite
- **API Coverage**: Documented in `API_STATUS.md` with detailed implementation tracking
- **Error Handling**: Robust exception management with detailed logging
- **Type Safety**: Full Pydantic model validation for all API interactions

### 📈 **Development Phases**
1. **✅ Phase 1 Complete**: Core trading operations (bot control, order management, market data)
2. **✅ Phase 2 Complete**: Advanced lab features (cloning, analytics, script management)
3. **🔄 Phase 3 In Progress**: Advanced features (white label, templates, analytics)

## Documentation

* [API Reference](docs/api_reference.md)
* [Lab Management](docs/labs.org)
* [API Coverage](docs/api_coverage.org)
* [Implementation Status](API_STATUS.md)

## Examples

* [Lab Parameters](examples/lab_parameters.py) - Complete lab lifecycle with parameter optimization
* [Bot Management](examples/bot_management.py) - Basic bot creation and management
* [Create Bot from Lab](examples/create_bot_from_lab.py) - Convert backtest results to live bot
* [Simple API Test](examples/simple_api_test.py) - Basic API function validation
* [Phase 2 Test](examples/phase2_test.py) - Advanced lab features and script management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Project Structure

The project is structured to promote maintainability and scalability. Key components include:

* `haaslib/`: Contains the core library code.
* `examples/`: Provides example scripts demonstrating the library's usage. These are a great starting point for learning how to use the library.
* `docs/`: Contains documentation for the library.
* `tests/`: Contains unit and integration tests.

## Experiments

See the `experiments/` folder for prototypes and experimental features, such as the Textual TUI backtester for multi-market strategy testing. These are not part of the stable API client but serve as sandboxes for new ideas.

## 🔥 **NEW: Backtest Analysis Capabilities**

The library now provides comprehensive backtest analysis with detailed data access:

### Backtest Results
- **Get backtest configurations**: Retrieve lists of tested parameter combinations
- **Performance metrics**: ROI, profits, fees, drawdowns for each configuration
- **Configuration details**: Generation, population, status information

### Runtime Data Analysis
- **Position tracking**: Complete position lifecycle with entry/exit details
- **Order management**: All order details and execution information
- **Performance metrics**: Detailed ROI, profits, fees, and risk metrics
- **Strategy signals**: Custom reports with technical indicator signals
- **Configuration data**: All bot settings, parameters, and account info

### Chart Data
- **Price data**: OHLCV data for entire backtest periods
- **Technical indicators**: All indicators used by the strategy
- **Visualization ready**: Complete chart configuration and styling

### Complete Workflow
```
1. Create Lab → 2. Run Backtest → 3. Get Results → 4. Analyze Runtime → 5. Create Bot
```

## 📚 Documentation

- **[API Status](API_STATUS.md)**: Complete implementation status and testing results
- **[Backtest Analysis Discoveries](docs/backtest_analysis_discoveries.md)**: Comprehensive documentation of backtest capabilities
- **[Lab Management Guide](docs/labs.org)**: Detailed lab lifecycle management
- **[API Reference](docs/api_reference.md)**: Complete API function reference

## 🧪 Examples

### Basic Lab Management
```python
from pyHaasAPI import api
from pyHaasAPI.model import CreateLabRequest

# Authenticate
executor = api.RequestsExecutor(host="127.0.0.1", port=8090, state=api.Guest())
executor = executor.authenticate(email="your@email.com", password="your_password")

# Create lab
lab = api.create_lab(executor, CreateLabRequest(
    script_id="your_script_id",
    name="My Trading Lab",
    account_id="your_account_id",
    market="BINANCE_BTC_USDT_",
    interval=15,
    default_price_data_style="CandleStick"
))
```

### Backtest Analysis
```python
from pyHaasAPI.model import GetBacktestResultRequest

# Get backtest results
results = api.get_backtest_result(executor, GetBacktestResultRequest(
    lab_id=lab.lab_id,
    next_page_id=0,
    page_lenght=100
))

# Analyze specific configuration
runtime = api.get_backtest_runtime(executor, lab.lab_id, results.items[0].backtest_id)
chart = api.get_backtest_chart(executor, lab.lab_id, results.items[0].backtest_id)

# Create bot from best configuration
bot = api.add_bot_from_lab(executor, AddBotFromLabRequest(
    lab_id=lab.lab_id,
    backtest_id=results.items[0].backtest_id,
    bot_name="Best Strategy Bot",
    account_id="your_account_id",
    market="BINANCE_BTC_USDT_"
))
```

### Complete Examples
- **[Lab Parameters](examples/lab_parameters.py)**: Complete lab lifecycle with parameter management
- **[Backtest Results Workflow](examples/backtest_results_workflow.py)**: Full backtest analysis workflow
- **[Simple Backtest Results](examples/simple_backtest_results.py)**: Direct API replication
- **[Runtime Data Analysis](examples/examine_runtime_data.py)**: Detailed runtime data structure
- **[Chart Data Analysis](examples/examine_chart_data.py)**: Chart data structure analysis

## 📊 Implementation Status

- **Total Endpoints**: ~108 identified
- **Implemented**: 45 endpoints (42%)
- **Fully Tested**: Backtest analysis, lab management, bot creation
- **Documentation**: Comprehensive guides and examples

## 🔧 Installation

```bash
pip install pyHaasAPI
```

## 🎯 Key Capabilities

### Lab Management
- Create and configure trading labs
- Parameter optimization and backtesting
- Lab cloning and script switching
- Complete lab lifecycle management

### Backtest Analysis
- **Runtime Data**: 10,043+ characters of comprehensive trading data
- **Chart Data**: 536,137+ characters of price and indicator data
- **Performance Metrics**: Detailed ROI, profits, fees, drawdowns
- **Strategy Analysis**: Custom reports with technical signals

### Bot Management
- Create bots from backtest results
- Activate, deactivate, pause, resume bots
- Order management and position tracking
- Real-time bot monitoring

### Market Data
- Real-time price feeds
- Order book data
- Market snapshots
- Trade history

## 🤝 Contributing

Contributions are welcome! Please see our development guidelines and testing procedures in the documentation.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with ❤️ for the HaasOnline Trading Server community*
