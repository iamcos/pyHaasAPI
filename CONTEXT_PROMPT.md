# Project Context: pyHaasAPI - HaasOnline API Interaction Library

This document provides a comprehensive overview of the `pyHaasAPI` Python library, designed for programmatic interaction with the HaasOnline Trading Bot API. It synthesizes information from the project's documentation, examples, and test suite to outline its structure, core functionalities, usage patterns, and testing methodologies. The goal is to equip an AI model with the necessary context to understand and effectively utilize every server function exposed by this library.

---

## 1. Project Overview

`pyHaasAPI` is a robust Python wrapper that abstracts the complexities of the HaasOnline API, enabling automated trading, backtesting, and bot management.

### 1.1. Core Functionality

The library provides capabilities across several key domains:

*   **Lab Management**: Creation, cloning, updating, and deletion of backtesting labs. This is a central feature, with significant emphasis on proper configuration and parameter handling for backtesting and optimization.
*   **Bot Management**: Creation, activation, pausing, resuming, deactivation, and deletion of live trading bots. Includes monitoring bot status and managing their lifecycle.
*   **Market Data Operations**: Fetching real-time market prices, order books, trade history, and managing market history synchronization. This also covers retrieving chart data and ensuring market history readiness for backtesting.
*   **Account Management**: Listing, filtering, and managing trading accounts and their balances, including simulated accounts.
*   **Script Management**: Listing, retrieving, and managing HaasScripts (trading strategies) on the server.
*   **Backtesting**: Running backtests on labs and retrieving detailed results for analysis and subsequent bot creation.

### 1.2. Key Modules and Components

The project's architecture is modular, with distinct responsibilities:

*   **`pyHaasAPI.api`**: The core module containing the main API client functions for direct interaction with the HaasOnline server. This is where most server functions are exposed.
*   **`pyHaasAPI.model`**: Defines Pydantic models for API requests and responses, ensuring type safety, data validation, and proper serialization/deserialization.
*   **`pyHaasAPI.lab`**: Contains higher-level functions specifically for lab-related operations, often building upon the `api` module.
*   **`pyHaasAPI.market_manager`**: A utility for managing and validating market configurations, including formatting market tags.
*   **`pyHaasAPI.lab_manager`**: A utility for streamlining lab creation and management workflows, often used in examples for complex lab setups.
*   **`config/settings.py`**: Manages project-wide settings, including API host, port, and credentials.
*   **`.env`**: Stores sensitive environment variables (e.g., `API_EMAIL`, `API_PASSWORD`) that are loaded by `config/settings.py`.
*   **`utils/auth/authenticator.py`**: Handles the authentication process, providing an authenticated `executor` object.
*   **`utils/lab_management/parameter_optimizer.py`**: (Used in `examples/lab_full_rundown.py`) Provides functionality for optimizing lab parameters during backtesting.

### 1.3. Common Usage Patterns

Several patterns are consistently observed across the codebase:

*   **Authentication Flow**: All interactions begin with authenticating to the HaasOnline API. This typically involves creating a `RequestsExecutor` and calling its `authenticate()` method.
*   **Resource Discovery**: Before performing operations, scripts often fetch available resources (scripts, accounts, markets) to obtain necessary IDs and ensure valid configurations.
*   **Lab-Centric Workflows**: Many complex operations, especially for backtesting and strategy development, revolve around the creation, configuration, and manipulation of "labs."
*   **Parameter Handling**: Labs and bots have configurable parameters. The library provides mechanisms for updating these, often requiring careful handling of data types and aliases.
*   **Robust Error Handling**: `try-except` blocks are consistently used around API calls to gracefully handle `HaasApiError` (custom exception for API-specific errors) and provide informative messages. Pre-validation of inputs and prerequisites (like market history readiness) is common.
*   **Settings Preservation**: When updating existing labs or bots, there's a strong emphasis on ensuring that critical settings (e.g., `market_tag`, `account_id`) are explicitly preserved and not inadvertently overwritten.
*   **Lifecycle Management**: Both labs and bots follow clear lifecycles (create, activate/start, monitor, pause/cancel, delete), with dedicated functions for each stage.

---

## 2. Detailed API Functionality (Server Functions)

This section outlines key server functions available through the `pyHaasAPI.api` module, along with their purpose, important parameters, and concise usage examples. Assume `executor` is an already authenticated `api.RequestsExecutor` instance.

**General Setup for Examples:**
```python
import os
import time
from config import settings
from dotenv import load_dotenv
from pyHaasAPI import api
from pyHaasAPI.model import (
    CreateLabRequest, CloudMarket, StartLabExecutionRequest,
    GetBacktestResultRequest, CreateBotRequest, ScriptItem, Account
)
from pyHaasAPI.exceptions import HaasApiError

# Load environment variables (e.g., API_EMAIL, API_PASSWORD)
load_dotenv()

# Authenticate (simplified for brevity, full auth in examples/lab_full_rundown.py)
try:
    executor = api.RequestsExecutor(
        host=settings.API_HOST,
        port=settings.API_PORT,
        state=api.Guest()
    ).authenticate(
        email=settings.API_EMAIL,
        password=settings.API_PASSWORD
    )
    print("Authentication successful.")
except HaasApiError as e:
    print(f"Authentication failed: {e}")
    exit()

# Helper to get a sample script and account (common in examples)
def get_sample_script_and_account(executor):
    scripts = api.get_all_scripts(executor)
    accounts = api.get_accounts(executor)
    if not scripts:
        print("No scripts found on server.")
        return None, None
    if not accounts:
        print("No accounts found on server.")
        return None, None
    return scripts[0], accounts[0]

# Example usage of helper
sample_script, sample_account = get_sample_script_and_account(executor)
if not sample_script or not sample_account:
    print("Cannot proceed without a sample script and account.")
    exit()
```

---

### 2.1. Authentication & Core Utilities

*   **`api.RequestsExecutor(host, port, state)`**: Constructor for the API client.
    *   `host` (str): HaasOnline API server IP or hostname.
    *   `port` (int): HaasOnline API server port.
    *   `state` (api.Guest): Initial authentication state.
*   **`executor.authenticate(email, password)`**: Authenticates the executor.
    *   `email` (str): User email.
    *   `password` (str): User password.
    *   Returns authenticated `executor` instance.

    ```python
    # See General Setup for example.
    ```

---

### 2.2. Market Data Operations

*   **`api.get_all_markets(executor)`**: Retrieves a list of all available markets.
    *   Returns `List[CloudMarket]`.
    *   *Note*: For performance, prefer `PriceAPI.get_trade_markets(exchange)` for specific exchanges.
    ```python
    try:
        all_markets = api.get_all_markets(executor)
        print(f"Found {len(all_markets)} markets.")
        if all_markets:
            print(f"First market: {all_markets[0].format_market_tag(all_markets[0].price_source)}")
    except HaasApiError as e:
        print(f"Error getting all markets: {e}")
    ```

*   **`api.get_market_price(executor, market_tag)`**: Gets the latest price for a specific market.
    *   `market_tag` (str): Formatted market string (e.g., "BINANCE_BTC_USDT_").
    *   Returns `float`.
    ```python
    market_tag = "BINANCE_BTC_USDT_" # Example
    try:
        price = api.get_market_price(executor, market_tag)
        print(f"Price for {market_tag}: {price}")
    except HaasApiError as e:
        print(f"Error getting market price: {e}")
    ```

*   **`api.get_order_book(executor, market_tag)`**: Retrieves the order book for a market.
    *   `market_tag` (str): Formatted market string.
    *   Returns `dict` (raw API response for order book).
    ```python
    market_tag = "BINANCE_BTC_USDT_"
    try:
        order_book = api.get_order_book(executor, market_tag)
        print(f"Order book for {market_tag}: {order_book.get('Bids')[:2]} (bids), {order_book.get('Asks')[:2]} (asks)")
    except HaasApiError as e:
        print(f"Error getting order book: {e}")
    ```

*   **`api.get_last_trades(executor, market_tag)`**: Gets recent trades for a market.
    *   `market_tag` (str): Formatted market string.
    *   Returns `List[dict]` (raw API response for trades).
    ```python
    market_tag = "BINANCE_BTC_USDT_"
    try:
        trades = api.get_last_trades(executor, market_tag)
        print(f"Last trades for {market_tag}: {len(trades)} trades.")
    except HaasApiError as e:
        print(f"Error getting last trades: {e}")
    ```

*   **`api.get_chart(executor, market_tag, interval)`**: Retrieves chart data for a market.
    *   `market_tag` (str): Formatted market string.
    *   `interval` (int): Chart interval in minutes (e.g., 1, 5, 15, 60).
    *   Returns `dict` (raw API response for chart data).
    ```python
    market_tag = "BINANCE_BTC_USDT_"
    try:
        chart_data = api.get_chart(executor, market_tag, 15)
        print(f"Chart data for {market_tag} (15min): {len(chart_data.get('Plots', [])[0].get('PricePlot', {}).get('Candles', []))} candles.")
    except HaasApiError as e:
        print(f"Error getting chart data: {e}")
    ```

*   **`api.set_history_depth(executor, market_tag, months)`**: Sets the history depth for a market.
    *   `market_tag` (str): Formatted market string.
    *   `months` (int): Number of months of history to set.
    *   Returns `bool` indicating success.
    ```python
    market_tag = "BINANCE_BTC_USDT_"
    try:
        success = api.set_history_depth(executor, market_tag, 12)
        print(f"Set history depth for {market_tag} to 12 months: {success}")
    except HaasApiError as e:
        print(f"Error setting history depth: {e}")
    ```

*   **`api.get_history_status(executor, market_tag)`**: Gets the history synchronization status for a market.
    *   `market_tag` (str): Formatted market string.
    *   Returns `dict` (raw API response for history status).
    ```python
    market_tag = "BINANCE_BTC_USDT_"
    try:
        status = api.get_history_status(executor, market_tag)
        print(f"History status for {market_tag}: {status.get('Status')}")
    except HaasApiError as e:
        print(f"Error getting history status: {e}")
    ```

*   **`api.ensure_market_history_ready(executor, market_tag, months)`**: Utility to ensure market history is synced.
    *   `market_tag` (str): Formatted market string.
    *   `months` (int): Desired history depth in months.
    *   Returns `bool` indicating readiness.
    ```python
    market_tag = "BINANCE_BTC_USDT_"
    try:
        ready = api.ensure_market_history_ready(executor, market_tag, 36)
        print(f"Market history for {market_tag} ready: {ready}")
    except HaasApiError as e:
        print(f"Error ensuring market history: {e}")
    ```

---

### 2.3. Lab Management

*   **`api.create_lab(executor, create_lab_request)`**: Creates a new backtesting lab.
    *   `create_lab_request` (CreateLabRequest): Request object with lab details.
    *   Returns `LabDetails` object.
    *   *Best Practice*: Use `CreateLabRequest.with_generated_name()` for proper market tag formatting.
    ```python
    # Assuming sample_script and sample_account are available
    market = CloudMarket(category="SPOT", price_source="BINANCE", primary="BTC", secondary="USDT")
    req = CreateLabRequest.with_generated_name(
        script_id=sample_script.script_id,
        account_id=sample_account.account_id,
        market=market,
        exchange_code="BINANCE",
        interval=1,
        default_price_data_style="CandleStick"
    )
    try:
        new_lab = api.create_lab(executor, req)
        print(f"Lab created: {new_lab.lab_id}, Name: {new_lab.name}")
    except HaasApiError as e:
        print(f"Error creating lab: {e}")
    ```

*   **`api.clone_lab(executor, lab_id, new_name)`**: Clones an existing lab.
    *   `lab_id` (str): ID of the lab to clone.
    *   `new_name` (str): Name for the cloned lab.
    *   Returns `LabDetails` object for the cloned lab.
    ```python
    # Assuming new_lab from previous example
    if 'new_lab' in locals():
        try:
            cloned_lab = api.clone_lab(executor, new_lab.lab_id, "MyClonedLab")
            print(f"Lab cloned: {cloned_lab.lab_id}, Name: {cloned_lab.name}")
        except HaasApiError as e:
            print(f"Error cloning lab: {e}")
    ```

*   **`api.get_lab_details(executor, lab_id)`**: Retrieves detailed configuration of a lab.
    *   `lab_id` (str): ID of the lab.
    *   Returns `LabDetails` object.
    ```python
    # Assuming new_lab from previous example
    if 'new_lab' in locals():
        try:
            details = api.get_lab_details(executor, new_lab.lab_id)
            print(f"Lab {details.lab_id} status: {details.status}")
            print(f"Market Tag: {details.settings.market_tag}")
        except HaasApiError as e:
            print(f"Error getting lab details: {e}")
    ```

*   **`api.update_lab_details(executor, lab_details)`**: Updates a lab's settings and parameters.
    *   `lab_details` (LabDetails): Modified `LabDetails` object.
    *   Returns updated `LabDetails` object.
    *   *Important*: Ensure critical settings are preserved.
    ```python
    # Assuming new_lab from previous example
    if 'new_lab' in locals():
        try:
            updated_details = api.get_lab_details(executor, new_lab.lab_id)
            updated_details.settings.trade_amount = 150.0 # Example change
            updated_lab_result = api.update_lab_details(executor, updated_details)
            print(f"Lab {updated_lab_result.lab_id} trade amount updated to: {updated_lab_result.settings.trade_amount}")
        except HaasApiError as e:
            print(f"Error updating lab details: {e}")
    ```

*   **`api.start_lab_execution(executor, start_lab_execution_request)`**: Starts a backtest for a lab.
    *   `start_lab_execution_request` (StartLabExecutionRequest): Request object with lab ID and time range.
    *   Returns `LabDetails` object with updated status.
    ```python
    # Assuming new_lab from previous example
    if 'new_lab' in locals():
        start_unix = int(time.time()) - 86400 * 7 # 7 days ago
        end_unix = int(time.time())
        req = StartLabExecutionRequest(
            lab_id=new_lab.lab_id,
            start_unix=start_unix,
            end_unix=end_unix,
            send_email=False
        )
        try:
            started_lab = api.start_lab_execution(executor, req)
            print(f"Lab {started_lab.lab_id} execution started. Status: {started_lab.status}")
        except HaasApiError as e:
            print(f"Error starting lab execution: {e}")
    ```

*   **`api.get_lab_execution_update(executor, lab_id)`**: Monitors the execution status of a running backtest.
    *   `lab_id` (str): ID of the lab.
    *   Returns `LabExecutionUpdate` object.
    ```python
    # Assuming new_lab is running a backtest
    if 'new_lab' in locals():
        print("Monitoring lab execution...")
        for _ in range(3): # Check a few times
            try:
                status_update = api.get_lab_execution_update(executor, new_lab.lab_id)
                print(f"  Current execution status: {status_update.execution_status}")
                if status_update.execution_status == "COMPLETED":
                    break
                time.sleep(5)
            except HaasApiError as e:
                print(f"Error monitoring lab execution: {e}")
                break
    ```

*   **`api.get_backtest_result(executor, get_backtest_result_request)`**: Retrieves backtest results.
    *   `get_backtest_result_request` (GetBacktestResultRequest): Request object with lab ID, page info.
    *   Returns `BacktestResult` object.
    ```python
    # Assuming new_lab has completed a backtest
    if 'new_lab' in locals():
        req = GetBacktestResultRequest(lab_id=new_lab.lab_id, next_page_id=0, page_lenght=10)
        try:
            results = api.get_backtest_result(executor, req)
            print(f"Retrieved {len(results.items)} backtest configurations.")
            if results.items:
                print(f"First result ROI: {getattr(results.items[0].summary, 'ReturnOnInvestment', 'N/A')}%")
        except HaasApiError as e:
            print(f"Error getting backtest results: {e}")
    ```

*   **`api.delete_lab(executor, lab_id)`**: Deletes a lab.
    *   `lab_id` (str): ID of the lab to delete.
    *   Returns `bool` indicating success.
    ```python
    # Assuming new_lab from previous example
    if 'new_lab' in locals():
        try:
            success = api.delete_lab(executor, new_lab.lab_id)
            print(f"Lab {new_lab.lab_id} deleted: {success}")
        except HaasApiError as e:
            print(f"Error deleting lab: {e}")
    ```

---

### 2.4. Bot Management

*   **`api.add_bot(executor, create_bot_request)`**: Creates a new trading bot.
    *   `create_bot_request` (CreateBotRequest): Request object with bot details.
    *   Returns `Bot` object.
    ```python
    # Assuming sample_script and sample_account are available
    market_tag = "BINANCE_BTC_USDT_" # Example
    req = CreateBotRequest(
        bot_name="MyNewBot",
        script=sample_script,
        account_id=sample_account.account_id,
        market=market_tag
    )
    try:
        new_bot = api.add_bot(executor, req)
        print(f"Bot created: {new_bot.bot_id}, Name: {new_bot.bot_name}")
    except HaasApiError as e:
        print(f"Error creating bot: {e}")
    ```

*   **`api.activate_bot(executor, bot_id, cleanreports=False)`**: Activates a bot.
    *   `bot_id` (str): ID of the bot.
    *   `cleanreports` (bool): Whether to clean reports.
    *   Returns `Bot` object.
    ```python
    # Assuming new_bot from previous example
    if 'new_bot' in locals():
        try:
            activated_bot = api.activate_bot(executor, new_bot.bot_id)
            print(f"Bot {activated_bot.bot_id} activated.")
        except HaasApiError as e:
            print(f"Error activating bot: {e}")
    ```

*   **`api.pause_bot(executor, bot_id)`**: Pauses a running bot.
    *   `bot_id` (str): ID of the bot.
    *   Returns `Bot` object.
    ```python
    # Assuming new_bot is active
    if 'new_bot' in locals():
        try:
            paused_bot = api.pause_bot(executor, new_bot.bot_id)
            print(f"Bot {paused_bot.bot_id} paused.")
        except HaasApiError as e:
            print(f"Error pausing bot: {e}")
    ```

*   **`api.resume_bot(executor, bot_id)`**: Resumes a paused bot.
    *   `bot_id` (str): ID of the bot.
    *   Returns `Bot` object.
    ```python
    # Assuming new_bot is paused
    if 'new_bot' in locals():
        try:
            resumed_bot = api.resume_bot(executor, new_bot.bot_id)
            print(f"Bot {resumed_bot.bot_id} resumed.")
        except HaasApiError as e:
            print(f"Error resuming bot: {e}")
    ```

*   **`api.deactivate_bot(executor, bot_id, cancelorders=False)`**: Deactivates a bot.
    *   `bot_id` (str): ID of the bot.
    *   `cancelorders` (bool): Whether to cancel open orders.
    *   Returns `Bot` object.
    ```python
    # Assuming new_bot is active
    if 'new_bot' in locals():
        try:
            deactivated_bot = api.deactivate_bot(executor, new_bot.bot_id)
            print(f"Bot {deactivated_bot.bot_id} deactivated.")
        except HaasApiError as e:
            print(f"Error deactivating bot: {e}")
    ```

*   **`api.delete_bot(executor, bot_id)`**: Deletes a bot.
    *   `bot_id` (str): ID of the bot.
    *   Returns `bool` indicating success.
    ```python
    # Assuming new_bot from previous example
    if 'new_bot' in locals():
        try:
            success = api.delete_bot(executor, new_bot.bot_id)
            print(f"Bot {new_bot.bot_id} deleted: {success}")
        except HaasApiError as e:
            print(f"Error deleting bot: {e}")
    ```

*   **`api.get_bot(executor, bot_id)`**: Retrieves details of a specific bot.
    *   `bot_id` (str): ID of the bot.
    *   Returns `Bot` object.
    ```python
    # Assuming a bot_id exists (e.g., from a previously created bot)
    some_bot_id = "..." # Replace with a real bot ID if testing
    try:
        bot_details = api.get_bot(executor, some_bot_id)
        print(f"Bot details for {some_bot_id}: Name={bot_details.bot_name}, Activated={bot_details.is_activated}")
    except HaasApiError as e:
        print(f"Error getting bot details: {e}")
    ```

*   **`api.get_all_bots(executor)`**: Retrieves a list of all bots.
    *   Returns `List[Bot]`.
    ```python
    try:
        all_bots = api.get_all_bots(executor)
        print(f"Found {len(all_bots)} bots.")
    except HaasApiError as e:
        print(f"Error getting all bots: {e}")
    ```

---

### 2.5. Account Management

*   **`api.get_accounts(executor)`**: Retrieves a list of all trading accounts.
    *   Returns `List[Account]`.
    ```python
    try:
        accounts = api.get_accounts(executor)
        print(f"Found {len(accounts)} accounts.")
        if accounts:
            print(f"First account: {accounts[0].name} (ID: {accounts[0].account_id})")
    except HaasApiError as e:
        print(f"Error getting accounts: {e}")
    ```

*   **`api.get_account_balance(executor, account_id)`**: Gets the balance for a specific account.
    *   `account_id` (str): ID of the account.
    *   Returns `dict` (raw API response for balance).
    ```python
    # Assuming sample_account is available
    if sample_account:
        try:
            balance = api.get_account_balance(executor, sample_account.account_id)
            print(f"Balance for {sample_account.name}: {balance}")
        except HaasApiError as e:
            print(f"Error getting account balance: {e}")
    ```

*   **`api.rename_account(executor, account_id, new_name)`**: Renames an account.
    *   `account_id` (str): ID of the account.
    *   `new_name` (str): New name for the account.
    *   Returns `bool` indicating success.
    ```python
    # Assuming sample_account is available
    if sample_account:
        original_name = sample_account.name
        new_account_name = f"{original_name}_Renamed"
        try:
            success = api.rename_account(executor, sample_account.account_id, new_account_name)
            print(f"Account renamed to {new_account_name}: {success}")
            # Rename back
            api.rename_account(executor, sample_account.account_id, original_name)
        except HaasApiError as e:
            print(f"Error renaming account: {e}")
    ```

---

### 2.6. Script Management

*   **`api.get_all_scripts(executor)`**: Retrieves a list of all HaasScripts.
    *   Returns `List[ScriptItem]`.
    ```python
    try:
        scripts = api.get_all_scripts(executor)
        print(f"Found {len(scripts)} scripts.")
        if scripts:
            print(f"First script: {scripts[0].script_name} (ID: {scripts[0].script_id})")
    except HaasApiError as e:
        print(f"Error getting all scripts: {e}")
    ```

*   **`api.get_script_item(executor, script_id)`**: Retrieves details of a specific script.
    *   `script_id` (str): ID of the script.
    *   Returns `ScriptItem` object.
    ```python
    # Assuming sample_script is available
    if sample_script:
        try:
            script_details = api.get_script_item(executor, sample_script.script_id)
            print(f"Script details for {sample_script.script_name}: {script_details.script_type}")
        except HaasApiError as e:
            print(f"Error getting script item: {e}")
    ```

---

## 3. Testing Methodology

The project employs a structured testing approach to ensure the reliability and correctness of the `pyHaasAPI` library:

*   **Test Organization**: Tests are categorized into `unit`, `integration`, and `performance` directories, with additional top-level files for quick checks. This separation allows for focused testing at different levels of granularity.
*   **Consistent Authentication**: Test scripts consistently use a standardized method (fixtures or helper functions) to authenticate with the API. Credentials are securely loaded from `.env` via `config/settings.py`, promoting reusability and security.
*   **Test Data Management**: Fixtures are extensively used (especially with `pytest`) to set up and tear down test data, such as ensuring the presence of accounts or providing specific account IDs. This approach helps in isolating tests and maintaining a clean testing environment.
*   **`pytest` Framework**: The `pytest` framework is utilized for writing and running tests, leveraging its powerful assertion capabilities and fixture management.
*   **Robust Error Handling in Tests**: Test cases often include `try-except` blocks or checks for `None` values to gracefully handle expected API errors. This demonstrates a commitment to building a resilient client that can handle various server responses.
*   **Progress Tracking**: The `TEST_FIX_PROGRESS.cursor` file indicates a diligent effort to standardize and track the completion of test suite updates. This highlights a focus on test quality, maintainability, and ensuring comprehensive coverage.
*   **Real-World Scenario Focus**: Integration tests are designed to cover end-to-end workflows, such as renaming an account and then reverting the change. This ensures that the library functions correctly in practical, real-world scenarios.

---

## 4. Project Structure (Relevant Directories)

*   **`pyHaasAPI/`**: The core library source code.
    *   `api.py`: Main API client functions.
    *   `model.py`: Pydantic data models.
    *   `lab.py`: Lab-specific functions.
    *   `exceptions.py`: Custom exception definitions.
*   **`examples/`**: Contains runnable scripts demonstrating various functionalities and workflows. These are excellent references for practical usage.
*   **`docs/`**: Project documentation, including detailed guides on lab workflows, market fetching, and API reference.
*   **`tests/`**: Comprehensive test suite (`unit/`, `integration/`, `performance/`) ensuring code quality and functionality.
*   **`config/`**: Configuration files, primarily `settings.py` for loading environment variables.
*   **`utils/`**: Utility scripts and helper modules, such as `auth/authenticator.py` and `lab_management/parameter_optimizer.py`.
*   **`.env`**: (User-managed) Environment variable file for sensitive credentials.
*   **`.cursor` files**: Internal documentation and progress trackers (e.g., `rules.cursor`, `RUNNING_TESTS.cursor`, `TEST_FIX_PROGRESS.cursor`).

---

## 5. Important Conventions and Best Practices

*   **Authentication**: Always authenticate using `executor.authenticate()` at the start of any script that interacts with the API. Credentials should be loaded from `.env` via `config/settings.py`.
*   **Market Naming**: All market tags must use the format: `<EXCHANGE>_<BASE>_<QUOTE>_` (e.g., `BINANCE_BTC_USDT_`). This is enforced and critical for API compatibility.
*   **Efficient Market Fetching**: **CRITICAL**: Always use `PriceAPI.get_trade_markets(exchange)` for fetching markets from specific exchanges. Avoid `api.get_all_markets()` as it is slow and unreliable.
*   **Error Handling**: Wrap all API calls in `try-except HaasApiError` blocks to handle failures gracefully and provide informative feedback.
*   **Settings Preservation**: When updating labs or bots, retrieve the current settings first, modify only the necessary fields, and then send the updated object back to ensure other critical settings are not lost.
*   **Lab Lifecycle**: Follow the recommended lab lifecycle (create, clone, update, backtest, delete) for robust automation.
*   **History Synchronization**: Before running backtests, ensure market history is ready using `api.ensure_market_history_ready()` or by manually setting history depth.
*   **Parameter Handling**: Be mindful of parameter types and structures, especially when dealing with `LabParameter` objects and their `K`, `T`, `O`, `I`, `IS` keys.
*   **API Endpoint Naming**: API endpoint names often end with `API` (e.g., `LabsAPI`) internally, which is important for constructing URLs.

---

## 6. Development Plan (Gemini Trading System)

This section outlines the strategic development phases for the broader Gemini Trading System, which will leverage `pyHaasAPI`.

### Phase 1: Foundational Layer (In Progress)
*   [x] Implement core API interaction logic (`pyHaasAPI` itself).
*   [ ] Develop a robust data collection and storage mechanism.
*   [ ] Create a basic command-line interface (CLI) for manual interaction.
*   [ ] Implement basic logging and error handling.

### Phase 2: Manual Trading & Analysis
*   [ ] Implement manual trade execution through the CLI.
*   [ ] Add features for viewing market data and charts.
*   [ ] Develop tools for analyzing historical data.

### Phase 3: Semi-Automated Trading
*   [ ] Implement a strategy definition framework.
*   [ ] Add support for backtesting strategies.
*   [ ] Create a system for deploying and monitoring strategies.

### Phase 4: Fully Autonomous Trading
*   [ ] Develop an AI-driven decision-making engine.
*   [ ] Implement risk management and performance monitoring.
*   [ ] Create a user-friendly dashboard for monitoring the system.

---
