# API Reference

This document provides comprehensive API reference for pyHaasAPI v2.

## Table of Contents

- [Core Components](#core-components)
- [API Modules](#api-modules)
- [Service Layer](#service-layer)
- [Tools](#tools)
- [CLI](#cli)
- [Data Models](#data-models)
- [Exceptions](#exceptions)

## Core Components

### AsyncHaasClient

The main async HTTP client for interacting with the HaasOnline API.

```python
from pyHaasAPI_v2 import AsyncHaasClient

client = AsyncHaasClient(
    host="127.0.0.1",
    port=8090,
    timeout=30.0
)
```

#### Methods

- `execute(request: Dict[str, Any]) -> Dict[str, Any]`: Execute a raw API request
- `get(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]`: GET request
- `post(endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]`: POST request
- `put(endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]`: PUT request
- `delete(endpoint: str) -> Dict[str, Any]`: DELETE request

### AuthenticationManager

Handles authentication and token management.

```python
from pyHaasAPI_v2 import AuthenticationManager

auth_manager = AuthenticationManager(
    email="your_email@example.com",
    password="your_password",
    auto_refresh=True
)
```

#### Methods

- `authenticate() -> bool`: Authenticate with the API
- `refresh_token() -> bool`: Refresh the authentication token
- `logout() -> None`: Logout and cleanup
- `is_authenticated() -> bool`: Check authentication status

### Type Validation

Runtime type checking and validation system.

```python
from pyHaasAPI_v2 import TypeValidator, TypeChecker

# Direct validation
validator = TypeValidator()
result = validator.validate_type("test", str)

# Decorator-based validation
checker = TypeChecker()

@checker.check_types
def my_function(value: str) -> str:
    return value
```

#### Classes

- `TypeValidator`: Direct type validation
- `TypeChecker`: Decorator-based type checking
- `TypeGuard`: Type guard utilities
- `TypeConverter`: Safe type conversion

### Async Utilities

Utilities for async operations, rate limiting, and batch processing.

```python
from pyHaasAPI_v2 import AsyncRateLimiter, AsyncRetryHandler, AsyncBatchProcessor

# Rate limiting
rate_limiter = AsyncRateLimiter(max_requests=100, time_window=60.0)

# Retry logic
retry_handler = AsyncRetryHandler(max_retries=3, base_delay=1.0)

# Batch processing
batch_processor = AsyncBatchProcessor(batch_size=10, max_concurrent=5)
```

## API Modules

### LabAPI

Lab management operations.

```python
from pyHaasAPI_v2.api import LabAPI

lab_api = LabAPI(async_client)
```

#### Methods

- `get_labs() -> List[Dict[str, Any]]`: Get all labs
- `create_lab(name: str, script_id: str, description: str = "") -> Dict[str, Any]`: Create a lab
- `delete_lab(lab_id: str) -> bool`: Delete a lab
- `get_lab_details(lab_id: str) -> Dict[str, Any]`: Get lab details
- `update_lab_details(lab_id: str, updates: Dict[str, Any]) -> bool`: Update lab details
- `start_lab_execution(lab_id: str) -> bool`: Start lab execution
- `cancel_lab_execution(lab_id: str) -> bool`: Cancel lab execution
- `get_lab_execution_update(lab_id: str) -> Dict[str, Any]`: Get execution status

### BotAPI

Bot management operations.

```python
from pyHaasAPI_v2.api import BotAPI

bot_api = BotAPI(async_client)
```

#### Methods

- `get_all_bots() -> List[Dict[str, Any]]`: Get all bots
- `create_bot(name: str, account_id: str, market_tag: str, **kwargs) -> Dict[str, Any]`: Create a bot
- `delete_bot(bot_id: str) -> bool`: Delete a bot
- `get_bot_details(bot_id: str) -> Dict[str, Any]`: Get bot details
- `activate_bot(bot_id: str) -> bool`: Activate a bot
- `deactivate_bot(bot_id: str) -> bool`: Deactivate a bot
- `pause_bot(bot_id: str) -> bool`: Pause a bot
- `resume_bot(bot_id: str) -> bool`: Resume a bot
- `edit_bot_parameter(bot_id: str, parameter: str, value: Any) -> bool`: Edit bot parameter
- `get_bot_orders(bot_id: str) -> List[Dict[str, Any]]`: Get bot orders
- `get_bot_positions(bot_id: str) -> List[Dict[str, Any]]`: Get bot positions
- `cancel_bot_order(bot_id: str, order_id: str) -> bool`: Cancel bot order
- `cancel_all_bot_orders(bot_id: str) -> bool`: Cancel all bot orders

### AccountAPI

Account management operations.

```python
from pyHaasAPI_v2.api import AccountAPI

account_api = AccountAPI(async_client)
```

#### Methods

- `get_accounts() -> List[Dict[str, Any]]`: Get all accounts
- `get_account_data(account_id: str) -> Dict[str, Any]`: Get account data
- `get_account_balance(account_id: str) -> float`: Get account balance
- `get_all_account_balances() -> List[Dict[str, Any]]`: Get all account balances
- `get_account_orders(account_id: str) -> List[Dict[str, Any]]`: Get account orders
- `get_margin_settings(account_id: str) -> Dict[str, Any]`: Get margin settings
- `adjust_margin_settings(account_id: str, settings: Dict[str, Any]) -> bool`: Adjust margin settings
- `set_position_mode(account_id: str, mode: str) -> bool`: Set position mode
- `set_margin_mode(account_id: str, mode: str) -> bool`: Set margin mode
- `set_leverage(account_id: str, leverage: int) -> bool`: Set leverage
- `distribute_bots_to_accounts(bot_ids: List[str], account_ids: List[str]) -> bool`: Distribute bots to accounts
- `migrate_bot_to_account(bot_id: str, account_id: str) -> bool`: Migrate bot to account
- `change_bot_account(bot_id: str, account_id: str) -> bool`: Change bot account
- `move_bot(bot_id: str, account_id: str) -> bool`: Move bot between accounts
- `set_bot_account(bot_id: str, account_id: str) -> bool`: Set bot account

### ScriptAPI

Script management operations.

```python
from pyHaasAPI_v2.api import ScriptAPI

script_api = ScriptAPI(async_client)
```

#### Methods

- `get_all_scripts() -> List[Dict[str, Any]]`: Get all scripts
- `get_script_record(script_id: str) -> Dict[str, Any]`: Get script record
- `get_script_item(script_id: str) -> Dict[str, Any]`: Get script item with dependencies
- `get_scripts_by_name(name: str) -> List[Dict[str, Any]]`: Find scripts by name
- `add_script(name: str, source_code: str, description: str = "") -> Dict[str, Any]`: Add a script
- `edit_script(script_id: str, updates: Dict[str, Any]) -> bool`: Edit script
- `edit_script_sourcecode(script_id: str, source_code: str) -> bool`: Edit script source code
- `delete_script(script_id: str) -> bool`: Delete script
- `publish_script(script_id: str) -> bool`: Publish script
- `get_haasscript_commands() -> List[Dict[str, Any]]`: Get HaasScript commands
- `execute_debug_test(script_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]`: Execute debug test
- `execute_quicktest(script_id: str, test_data: Dict[str, Any]) -> Dict[str, Any]`: Execute quick test

### MarketAPI

Market data operations.

```python
from pyHaasAPI_v2.api import MarketAPI

market_api = MarketAPI(async_client)
```

#### Methods

- `get_trade_markets() -> List[Dict[str, Any]]`: Get trading markets
- `get_price_data(market_tag: str) -> Dict[str, Any]`: Get real-time price data
- `get_historical_data(market_tag: str, interval: str, limit: int = 100) -> List[Dict[str, Any]]`: Get historical data
- `get_all_markets() -> List[Dict[str, Any]]`: Get all markets
- `get_all_markets_by_pricesource(pricesource: str) -> List[Dict[str, Any]]`: Get markets by price source
- `get_unique_pricesources() -> List[str]`: Get unique price sources
- `validate_market(market_tag: str) -> bool`: Validate market
- `get_valid_market(market_tag: str) -> Optional[str]`: Get valid market

### BacktestAPI

Backtest operations.

```python
from pyHaasAPI_v2.api import BacktestAPI

backtest_api = BacktestAPI(async_client)
```

#### Methods

- `get_backtest_result(lab_id: str, page: int = 0, page_size: int = 100) -> List[Dict[str, Any]]`: Get backtest results
- `get_backtest_result_page(lab_id: str, page: int, page_size: int = 100) -> Dict[str, Any]`: Get backtest result page
- `get_backtest_runtime(backtest_id: str) -> Dict[str, Any]`: Get backtest runtime data
- `get_full_backtest_runtime_data(backtest_id: str) -> Dict[str, Any]`: Get full backtest runtime data
- `get_backtest_chart(backtest_id: str) -> Dict[str, Any]`: Get backtest chart data
- `get_backtest_log(backtest_id: str) -> Dict[str, Any]`: Get backtest log
- `execute_backtest(lab_id: str, script_id: str, market_tag: str) -> bool`: Execute backtest
- `get_backtest_history(lab_id: str) -> List[Dict[str, Any]]`: Get backtest history
- `edit_backtest_tag(backtest_id: str, tag: str) -> bool`: Edit backtest tag
- `archive_backtest(backtest_id: str) -> bool`: Archive backtest

### OrderAPI

Order management operations.

```python
from pyHaasAPI_v2.api import OrderAPI

order_api = OrderAPI(async_client)
```

#### Methods

- `place_order(bot_id: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]`: Place an order
- `cancel_order(order_id: str) -> bool`: Cancel an order
- `get_order_status(order_id: str) -> Dict[str, Any]`: Get order status
- `get_order_history(bot_id: str, limit: int = 100) -> List[Dict[str, Any]]`: Get order history
- `get_all_orders(account_id: str) -> List[Dict[str, Any]]`: Get all orders for account
- `get_account_orders(account_id: str) -> List[Dict[str, Any]]`: Get account orders
- `get_bot_orders(bot_id: str) -> List[Dict[str, Any]]`: Get bot orders

## Service Layer

### LabService

High-level lab management service.

```python
from pyHaasAPI_v2.services import LabService

lab_service = LabService(lab_api, backtest_api, script_api, account_api)
```

#### Methods

- `get_all_labs() -> List[Dict[str, Any]]`: Get all labs
- `create_lab(name: str, script_id: str, description: str = "") -> Dict[str, Any]`: Create a lab
- `delete_lab(lab_id: str) -> Dict[str, Any]`: Delete a lab
- `execute_lab(lab_id: str) -> Dict[str, Any]`: Execute a lab
- `get_lab_status(lab_id: str) -> Dict[str, Any]`: Get lab status
- `validate_lab(lab_id: str) -> Dict[str, Any]`: Validate lab configuration
- `get_lab_health(lab_id: str) -> Dict[str, Any]`: Get lab health status

### BotService

High-level bot management service.

```python
from pyHaasAPI_v2.services import BotService

bot_service = BotService(bot_api, account_api, backtest_api, market_api, client, auth_manager)
```

#### Methods

- `get_all_bots() -> List[Dict[str, Any]]`: Get all bots
- `create_bot(name: str, account_id: str, market_tag: str, **kwargs) -> Dict[str, Any]`: Create a bot
- `delete_bot(bot_id: str) -> Dict[str, Any]`: Delete a bot
- `activate_bot(bot_id: str) -> Dict[str, Any]`: Activate a bot
- `deactivate_bot(bot_id: str) -> Dict[str, Any]`: Deactivate a bot
- `pause_bot(bot_id: str) -> Dict[str, Any]`: Pause a bot
- `resume_bot(bot_id: str) -> Dict[str, Any]`: Resume a bot
- `create_bots_from_lab(lab_id: str, count: int, activate: bool = False) -> Dict[str, Any]`: Create bots from lab
- `mass_bot_creation(lab_ids: List[str], count_per_lab: int, activate: bool = False) -> Dict[str, Any]`: Mass bot creation
- `get_bot_performance(bot_id: str) -> Dict[str, Any]`: Get bot performance metrics
- `monitor_bot_health(bot_id: str) -> Dict[str, Any]`: Monitor bot health

### AnalysisService

Analysis and reporting service.

```python
from pyHaasAPI_v2.services import AnalysisService

analysis_service = AnalysisService(lab_api, backtest_api, bot_api, client, auth_manager)
```

#### Methods

- `analyze_lab_comprehensive(lab_id: str, top_count: int = 10) -> Dict[str, Any]`: Comprehensive lab analysis
- `analyze_bot(bot_id: str) -> Dict[str, Any]`: Analyze bot performance
- `analyze_wfo(lab_id: str, start_date: str, end_date: str) -> Dict[str, Any]`: Walk Forward Optimization analysis
- `get_performance_metrics() -> Dict[str, Any]`: Get performance metrics
- `generate_bot_recommendations(lab_id: str, criteria: Dict[str, Any]) -> Dict[str, Any]`: Generate bot recommendations
- `compare_labs(lab_ids: List[str]) -> Dict[str, Any]`: Compare multiple labs
- `analyze_risk_metrics(lab_id: str) -> Dict[str, Any]`: Analyze risk metrics

### ReportingService

Report generation service.

```python
from pyHaasAPI_v2.services import ReportingService

reporting_service = ReportingService()
```

#### Methods

- `generate_analysis_report(data: List[Dict], report_type: str, format: str) -> Dict[str, Any]`: Generate analysis report
- `generate_bot_recommendations_report(data: List[Dict], report_type: str, format: str) -> Dict[str, Any]`: Generate bot recommendations report
- `generate_wfo_report(data: Dict, report_type: str, format: str) -> Dict[str, Any]`: Generate WFO report
- `generate_performance_report(data: Dict, report_type: str, format: str) -> Dict[str, Any]`: Generate performance report
- `export_to_csv(data: List[Dict], filename: str) -> str`: Export data to CSV
- `export_to_json(data: List[Dict], filename: str) -> str`: Export data to JSON
- `export_to_excel(data: List[Dict], filename: str) -> str`: Export data to Excel

## Tools

### DataDumper

Export API data to various formats.

```python
from pyHaasAPI_v2.tools import DataDumper

dumper = DataDumper(async_client)
```

#### Methods

- `dump_data(data_type: str, format: str, output_dir: str) -> Dict[str, Any]`: Dump data to file
- `dump_labs(format: str, output_dir: str) -> Dict[str, Any]`: Dump labs data
- `dump_bots(format: str, output_dir: str) -> Dict[str, Any]`: Dump bots data
- `dump_accounts(format: str, output_dir: str) -> Dict[str, Any]`: Dump accounts data
- `dump_scripts(format: str, output_dir: str) -> Dict[str, Any]`: Dump scripts data
- `dump_markets(format: str, output_dir: str) -> Dict[str, Any]`: Dump markets data
- `dump_backtests(lab_id: str, format: str, output_dir: str) -> Dict[str, Any]`: Dump backtests data
- `dump_orders(bot_id: str, format: str, output_dir: str) -> Dict[str, Any]`: Dump orders data

### TestingManager

Test data management.

```python
from pyHaasAPI_v2.tools import TestingManager

testing_manager = TestingManager(async_client)
```

#### Methods

- `create_test_data(data_type: str, count: int) -> Dict[str, Any]`: Create test data
- `cleanup_test_data(data_type: str) -> Dict[str, Any]`: Cleanup test data
- `validate_test_data(data_type: str) -> Dict[str, Any]`: Validate test data
- `isolate_test_data(data_type: str) -> Dict[str, Any]`: Isolate test data
- `create_test_labs(count: int) -> Dict[str, Any]`: Create test labs
- `create_test_bots(count: int) -> Dict[str, Any]`: Create test bots
- `create_test_accounts(count: int) -> Dict[str, Any]`: Create test accounts
- `cleanup_test_labs() -> Dict[str, Any]`: Cleanup test labs
- `cleanup_test_bots() -> Dict[str, Any]`: Cleanup test bots
- `cleanup_test_accounts() -> Dict[str, Any]`: Cleanup test accounts

## CLI

### BaseCLI

Base class for all CLI tools.

```python
from pyHaasAPI_v2.cli import BaseCLI

class MyCLI(BaseCLI):
    async def run(self, args: List[str]) -> int:
        # Implementation
        pass
```

### LabCLI

Lab operations CLI.

```bash
# List labs
python -m pyHaasAPI_v2.cli lab list

# Create lab
python -m pyHaasAPI_v2.cli lab create --name "Test Lab" --script-id script_123

# Analyze lab
python -m pyHaasAPI_v2.cli lab analyze --lab-id lab_123 --top-count 5

# Execute lab
python -m pyHaasAPI_v2.cli lab execute --lab-id lab_123

# Delete lab
python -m pyHaasAPI_v2.cli lab delete --lab-id lab_123
```

### BotCLI

Bot operations CLI.

```bash
# List bots
python -m pyHaasAPI_v2.cli bot list

# Create bots
python -m pyHaasAPI_v2.cli bot create --from-lab lab_123 --count 3 --activate

# Activate bots
python -m pyHaasAPI_v2.cli bot activate --bot-ids bot1,bot2,bot3

# Deactivate bots
python -m pyHaasAPI_v2.cli bot deactivate --all

# Pause bots
python -m pyHaasAPI_v2.cli bot pause --bot-ids bot1,bot2

# Resume bots
python -m pyHaasAPI_v2.cli bot resume --bot-ids bot1,bot2
```

### AnalysisCLI

Analysis operations CLI.

```bash
# Analyze labs
python -m pyHaasAPI_v2.cli analysis labs --generate-reports

# Analyze bots
python -m pyHaasAPI_v2.cli analysis bots --performance-metrics

# Walk Forward Optimization
python -m pyHaasAPI_v2.cli analysis wfo --lab-id lab_123 --start-date 2022-01-01 --end-date 2023-12-31

# Generate reports
python -m pyHaasAPI_v2.cli analysis reports --format csv --output-dir reports/
```

## Data Models

### Common Models

- `LabDetails`: Lab information
- `BotDetails`: Bot information
- `AccountDetails`: Account information
- `ScriptDetails`: Script information
- `MarketDetails`: Market information
- `BacktestDetails`: Backtest information
- `OrderDetails`: Order information

### Service Models

- `LabAnalysisResult`: Lab analysis results
- `BotCreationResult`: Bot creation results
- `AnalysisResult`: Analysis results
- `ReportResult`: Report generation results

### Configuration Models

- `ClientConfig`: Client configuration
- `AuthConfig`: Authentication configuration
- `CacheConfig`: Cache configuration
- `RateLimitConfig`: Rate limiting configuration
- `RetryConfig`: Retry configuration
- `BatchConfig`: Batch processing configuration

## Exceptions

### Exception Hierarchy

```python
from pyHaasAPI_v2.exceptions import (
    HaasAPIError,
    AuthenticationError,
    APIError,
    ValidationError,
    RateLimitError,
    TimeoutError,
    ConnectionError
)
```

### Common Exceptions

- `HaasAPIError`: Base exception for all pyHaasAPI errors
- `AuthenticationError`: Authentication-related errors
- `APIError`: API-related errors
- `ValidationError`: Validation errors
- `RateLimitError`: Rate limiting errors
- `TimeoutError`: Timeout errors
- `ConnectionError`: Connection errors

### Error Handling

```python
from pyHaasAPI_v2.exceptions import HaasAPIError, AuthenticationError

try:
    # API operation
    result = await client.get_labs()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except HaasAPIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Type Safety

### Type Validation

```python
from pyHaasAPI_v2 import TypeValidator, TypeChecker

# Direct validation
validator = TypeValidator()
result = validator.validate_type("test", str)

# Decorator-based validation
checker = TypeChecker()

@checker.check_types
def my_function(value: str) -> str:
    return value
```

### Type Definitions

```python
from pyHaasAPI_v2 import LabID, BotID, AccountID, ScriptID, MarketTag

# Type aliases
lab_id: LabID = "lab_123"
bot_id: BotID = "bot_456"
account_id: AccountID = "account_789"
script_id: ScriptID = "script_101"
market_tag: MarketTag = "BTC_USDT_PERPETUAL"
```

### Type Configuration

```python
from pyHaasAPI_v2 import TypeCheckingConfig, TypeValidationSettings

# Configure type checking
config = TypeCheckingConfig(
    strict_mode=True,
    log_validation_errors=True,
    enable_runtime_validation=True
)

# Configure validation settings
settings = TypeValidationSettings(
    validation_level="strict",
    enable_decorator_validation=True,
    enable_async_validation=True
)
```

---

This API reference provides comprehensive documentation for all pyHaasAPI v2 components. For more detailed examples and usage patterns, see the [Examples](examples.md) document.
