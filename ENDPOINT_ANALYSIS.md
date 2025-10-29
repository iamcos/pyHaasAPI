# API Endpoint Analysis and Standardization

## Root Cause Analysis

### Why the Error Occurred

The v2 branch was getting HTML responses instead of JSON because of **inconsistent endpoint naming patterns**:

1. **Main Branch (Working)**: Uses simple endpoint names like `"HaasScript"`, `"Labs"`, `"Account"`
2. **v2 Branch (Broken)**: Uses PHP file names like `"/HaasScriptAPI.php"`, `"/LabsAPI.php"`

### The Problem

The HaasOnline API has **two different endpoint systems**:

#### ✅ **Working Pattern (Main Branch)**
```python
# Main branch uses simple names
executor.execute(
    endpoint="HaasScript",  # Simple name
    response_type=list[HaasScriptItemWithDependencies],
    query_params={"channel": "GET_ALL_SCRIPT_ITEMS"},
)
```

#### ❌ **Broken Pattern (v2 Branch)**
```python
# v2 uses PHP file names
await self.client.get_json(
    endpoint="/HaasScriptAPI.php",  # PHP file name
    params={
        "channel": "GET_ALL_SCRIPT_ITEMS",
        "userid": self.auth_manager.user_id,
        "interfacekey": self.auth_manager.interface_key,
    }
)
```

## Endpoint Pattern Analysis

### Main Branch Patterns (Working)
- **Scripts**: `"HaasScript"` → Works
- **Labs**: `"Labs"` → Works  
- **Accounts**: `"Account"` → Works
- **Bots**: `"Bot"` → Works
- **Backtests**: `"Backtest"` → Works
- **Prices**: `"Price"` → Works

### v2 Branch Patterns (Mixed)
- **Scripts**: `"/HaasScript"` vs `"/HaasScriptAPI.php"` → Inconsistent
- **Labs**: `"/LabsAPI.php"` → PHP pattern
- **Accounts**: `"/AccountAPI.php"` → PHP pattern
- **Bots**: `"/BotAPI.php"` → PHP pattern
- **Backtests**: `"/BacktestAPI.php"` → PHP pattern
- **Prices**: `"/PriceAPI.php"` → PHP pattern

## Standardization Plan

### 1. **Primary Pattern: Simple Names (Main Branch)**
Use the working pattern from main branch:

```python
# ✅ CORRECT - Use simple endpoint names
executor.execute(
    endpoint="HaasScript",
    response_type=ScriptResponse,
    query_params={"channel": "GET_ALL_SCRIPT_ITEMS"},
)
```

### 2. **Secondary Pattern: PHP Files (When Needed)**
Only use PHP file names when the simple pattern doesn't work:

```python
# ✅ CORRECT - Use PHP files only when necessary
await self.client.get_json(
    endpoint="/LabsAPI.php",
    params={"channel": "CREATE_LAB", ...}
)
```

## Endpoint Mapping

| Function | Main Branch | v2 Branch | Status | Recommendation |
|----------|-------------|-----------|--------|----------------|
| Scripts | `"HaasScript"` | `"/HaasScript"` vs `"/HaasScriptAPI.php"` | ❌ Inconsistent | Use `"HaasScript"` |
| Labs | `"Labs"` | `"/LabsAPI.php"` | ❌ Different | Use `"Labs"` |
| Accounts | `"Account"` | `"/AccountAPI.php"` | ❌ Different | Use `"Account"` |
| Bots | `"Bot"` | `"/BotAPI.php"` | ❌ Different | Use `"Bot"` |
| Backtests | `"Backtest"` | `"/BacktestAPI.php"` | ❌ Different | Use `"Backtest"` |
| Prices | `"Price"` | `"/PriceAPI.php"` | ❌ Different | Use `"Price"` |

## Implementation Strategy

### Phase 1: Fix Script API
```python
# Change from:
endpoint="/HaasScriptAPI.php"

# To:
endpoint="HaasScript"
```

### Phase 2: Standardize All APIs
1. **Lab API**: `"/LabsAPI.php"` → `"Labs"`
2. **Account API**: `"/AccountAPI.php"` → `"Account"`
3. **Bot API**: `"/BotAPI.php"` → `"Bot"`
4. **Backtest API**: `"/BacktestAPI.php"` → `"Backtest"`
5. **Price API**: `"/PriceAPI.php"` → `"Price"`

### Phase 3: Update Client Methods
Ensure all APIs use the same client pattern as main branch:

```python
# Main branch pattern (working)
executor.execute(
    endpoint="HaasScript",
    response_type=ScriptResponse,
    query_params={"channel": "GET_ALL_SCRIPT_ITEMS"},
)
```

## Files to Update

### High Priority
1. `pyHaasAPI/api/script/script_api.py` - Fix script endpoints
2. `pyHaasAPI/api/lab/lab_api.py` - Fix lab endpoints
3. `pyHaasAPI/api/account/account_api.py` - Fix account endpoints
4. `pyHaasAPI/api/bot/bot_api.py` - Fix bot endpoints
5. `pyHaasAPI/api/backtest/backtest_api.py` - Fix backtest endpoints
6. `pyHaasAPI/api/market/market_api.py` - Fix price endpoints

### Medium Priority
1. `pyHaasAPI/api/order/order_api.py` - Fix order endpoints
2. All test files that use endpoints

## Testing Strategy

1. **Test each API individually** after fixing endpoints
2. **Compare responses** between main branch and v2
3. **Verify JSON responses** (not HTML)
4. **Test authentication** with each API

## Expected Results

After standardization:
- ✅ All APIs return JSON responses
- ✅ Consistent endpoint naming across project
- ✅ pshaiBot scripts found successfully
- ✅ All lab operations work correctly
- ✅ Unified API pattern across v1 and v2

## Conclusion

The error occurred because v2 mixed two different endpoint patterns. The solution is to standardize on the **simple endpoint names** pattern from the main branch, which is proven to work correctly with the HaasOnline API.
