# API Endpoint Architecture

## Overview

The pyHaasAPI library uses **PHP endpoints** with **channel-based routing** to interact with the HaasOnline Trade Server API. All endpoints follow a consistent pattern but are currently **hardcoded** in each API module.

## Endpoint Structure

### PHP Endpoints

The library uses the following PHP endpoints:

- `/LabsAPI.php` - Lab management operations
- `/BotAPI.php` - Bot management operations  
- `/AccountAPI.php` - Account and order operations
- `/BacktestAPI.php` - Backtest operations
- `/PriceAPI.php` - Market and price data
- `/HaasScriptAPI.php` - Script management
- `/UserAPI.php` - User and authentication operations

### Channel-Based Routing

Each PHP endpoint uses a `channel` query parameter to specify the operation:

```python
# Example: Get all labs
response = await client.post_json(
    endpoint="/LabsAPI.php",
    params={"channel": "GET_LABS"},
    data={"userid": "...", "interfacekey": "..."}
)

# Example: Create bot
response = await client.post_json(
    endpoint="/BotAPI.php",
    data={
        "channel": "ADD_BOT",
        "userid": "...",
        "interfacekey": "...",
        "botname": "...",
        # ... other fields
    }
)
```

## Current Implementation Pattern

### 1. Client Methods

The `AsyncHaasClient` provides several methods for making requests:

```python
# General purpose execution
await client.execute(
    endpoint="/LabsAPI.php",
    method="POST",
    query_params={"channel": "GET_LABS"},
    data={"userid": "...", "interfacekey": "..."}
)

# POST with JSON response
await client.post_json(
    endpoint="/LabsAPI.php",
    params={"channel": "GET_LABS"},  # Query params
    data={"userid": "...", "interfacekey": "..."}  # POST body
)

# GET with JSON response
await client.get_json(
    endpoint="/BotAPI.php",
    params={"channel": "GET_BOTS", "userid": "...", "interfacekey": "..."}
)
```

### 2. Data Format

**Important**: Most endpoints expect **form-urlencoded** data, not JSON:

```python
# The client automatically converts dict to form-urlencoded
data = {
    "channel": "CREATE_LAB",
    "userid": session.user_id,
    "interfacekey": session.interface_key,
    "name": "My Lab",
    "scriptid": "script123"
}
# Sent as: application/x-www-form-urlencoded
```

### 3. Authentication Parameters

Authentication parameters (`userid`, `interfacekey`) are typically included in:
- **POST requests**: In the `data` dict (body)
- **GET requests**: In `params` dict (query string)

Example from `LabAPI.get_labs()`:
```python
post_data = {
    'interfacekey': session.interface_key,
    'userid': session.user_id
}

response = await self.client.post_json(
    endpoint="/LabsAPI.php",
    params={"channel": "GET_LABS"},  # Channel in query params
    data=post_data  # Auth in POST body
)
```

## Common Channel Names

### LabsAPI.php Channels
- `GET_LABS` - Get all labs
- `GET_LAB_DETAILS` - Get lab details
- `CREATE_LAB` - Create new lab
- `DELETE_LAB` - Delete lab
- `UPDATE_LAB_DETAILS` - Update lab configuration
- `CHANGE_LAB_SCRIPT` - Change lab script
- `START_LAB_EXECUTION` - Start lab execution
- `CANCEL_LAB_EXECUTION` - Cancel lab execution
- `GET_BACKTEST_RESULT_PAGE` - Get paginated backtest results

### BotAPI.php Channels
- `GET_BOTS` - Get all bots
- `GET_BOT_DETAILS` - Get bot details
- `ADD_BOT` - Create new bot
- `ADD_BOT_FROM_LABS` - Create bot from lab backtest
- `DELETE_BOT` - Delete bot
- `EDIT_BOT_PARAMETER` - Edit bot parameters
- `ACTIVATE_BOT` - Activate bot
- `DEACTIVATE_BOT` - Deactivate bot
- `PAUSE_BOT` - Pause bot
- `RESUME_BOT` - Resume bot

### AccountAPI.php Channels
- `GET_ACCOUNTS` - Get all accounts
- `GET_ACCOUNT_DETAILS` - Get account details
- `PLACE_ORDER` - Place order
- `CANCEL_ORDER` - Cancel order
- `GET_ORDERS` - Get orders for account
- `GET_ALL_ORDERS` - Get all orders
- `GET_POSITIONS` - Get positions

### BacktestAPI.php Channels
- `GET_HISTORY_STATUS` - Get market history sync status
- `EXECUTE_BACKTEST` - Execute a backtest
- `GET_BACKTEST_RESULT` - Get backtest result

### PriceAPI.php Channels
- `MARKETLIST` - Get market list
- `TRADE_MARKETS` - Get trade markets
- `GET_PRICE_DATA` - Get price data

### HaasScriptAPI.php Channels
- `GET_ALL_SCRIPT_ITEMS` - Get all scripts
- `GET_SCRIPT_DETAILS` - Get script details
- `CREATE_SCRIPT` - Create script
- `EDIT_SCRIPT` - Edit script
- `DELETE_SCRIPT` - Delete script

## Current Limitations

### 1. No Centralization

Endpoints and channels are **hardcoded** in each API module:

```python
# In LabAPI
response = await self.client.post_json(
    endpoint="/LabsAPI.php",  # Hardcoded
    params={"channel": "GET_LABS"},  # Hardcoded
    ...
)

# In BotAPI  
response = await self.client.post_json(
    endpoint="/BotAPI.php",  # Hardcoded
    data={"channel": "ADD_BOT"},  # Hardcoded
    ...
)
```

### 2. No Type Safety

Channel names are strings with no validation:
- Typos are only caught at runtime
- No IDE autocomplete
- No centralized documentation

### 3. Inconsistent Patterns

Some APIs put channel in query params, others in POST body:
```python
# Pattern 1: Channel in query params
params={"channel": "GET_LABS"}
data={"userid": "...", "interfacekey": "..."}

# Pattern 2: Channel in POST body
data={"channel": "ADD_BOT", "userid": "...", "interfacekey": "..."}
```

## Recommended Improvements

### 1. Centralize Endpoints

Create an endpoints configuration:

```python
# pyHaasAPI/core/endpoints.py
class Endpoints:
    LABS = "/LabsAPI.php"
    BOTS = "/BotAPI.php"
    ACCOUNTS = "/AccountAPI.php"
    BACKTESTS = "/BacktestAPI.php"
    PRICES = "/PriceAPI.php"
    SCRIPTS = "/HaasScriptAPI.php"
    USERS = "/UserAPI.php"
```

### 2. Centralize Channels

Create channel constants:

```python
# pyHaasAPI/core/channels.py
class LabChannels:
    GET_LABS = "GET_LABS"
    GET_LAB_DETAILS = "GET_LAB_DETAILS"
    CREATE_LAB = "CREATE_LAB"
    DELETE_LAB = "DELETE_LAB"
    # ...

class BotChannels:
    GET_BOTS = "GET_BOTS"
    ADD_BOT = "ADD_BOT"
    ADD_BOT_FROM_LABS = "ADD_BOT_FROM_LABS"
    # ...
```

### 3. Standardize Channel Placement

Decide on a consistent pattern:
- **Recommendation**: Always put `channel` in query params for clarity
- Keep auth params in POST body for POST requests
- Keep auth params in query params for GET requests

### 4. Add Type Safety

Use enums or TypedDict for channels:

```python
from enum import Enum

class LabChannel(str, Enum):
    GET_LABS = "GET_LABS"
    GET_LAB_DETAILS = "GET_LAB_DETAILS"
    CREATE_LAB = "CREATE_LAB"
    # ...
```

## Examples

### Current Pattern (LabAPI)

```python
async def get_labs(self) -> List[LabRecord]:
    session = self.auth_manager.session
    post_data = {
        'interfacekey': session.interface_key,
        'userid': session.user_id
    }
    
    response = await self.client.post_json(
        endpoint="/LabsAPI.php",
        params={"channel": "GET_LABS"},
        data=post_data
    )
    # ...
```

### Current Pattern (BotAPI)

```python
async def create_bot(self, bot_name: str, ...) -> BotDetails:
    session = self.auth_manager.session
    response = await self.client.post_json(
        endpoint="/BotAPI.php",
        data={
            "channel": "ADD_BOT",  # Channel in body
            "userid": session.user_id,
            "interfacekey": session.interface_key,
            "botname": bot_name,
            # ...
        }
    )
    # ...
```

## Summary

- **Endpoints**: PHP files (`/LabsAPI.php`, `/BotAPI.php`, etc.)
- **Routing**: Channel-based via query parameter or POST body
- **Data Format**: Form-urlencoded (not JSON)
- **Auth**: Included in request (body for POST, query for GET)
- **Status**: Hardcoded, not centralized
- **Recommendation**: Centralize endpoints and channels for maintainability

