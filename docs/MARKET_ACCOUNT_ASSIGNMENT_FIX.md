# Market and Account Assignment Fix

## Problem Summary

Previously, labs were being created with incorrect or empty market tags and account IDs, causing them to be queued with wrong market information. This was happening because:

1. **HTTP Method Mismatch**: The API was using GET requests for lab updates when POST with form-encoded data was required
2. **Data Format Issues**: Complex objects weren't being properly JSON-encoded for the API
3. **Indentation Errors**: Syntax errors in the codebase prevented proper execution

## Root Cause Analysis

The issue was in the `_execute_inner` method in `pyHaasAPI/api.py`. The HaasOnline API requires:

- **POST requests** with `application/x-www-form-urlencoded` content type for lab updates
- **JSON-encoded strings** for complex fields like `settings`, `config`, and `parameters`
- **Proper indentation** and syntax in the Python code

## Changes Made

### 1. Fixed HTTP Method and Data Format (`pyHaasAPI/api.py`)

**Before:**
```python
# All requests used GET with query parameters
resp = requests.get(url, params=query_params)
```

**After:**
```python
# PATCH: Use POST with form-encoded data for UPDATE_LAB_DETAILS
if query_params and query_params.get("channel") == "UPDATE_LAB_DETAILS":
    # Ensure all values are JSON-encoded strings
    form_data = {}
    for k, v in query_params.items():
        if isinstance(v, (str, int, float, bool, type(None))):
            form_data[k] = str(v) if not isinstance(v, str) else v
        else:
            form_data[k] = json.dumps(v, default=self._custom_encoder(by_alias=True))
    resp = requests.post(url, data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
else:
    resp = requests.get(url, params=query_params)
```

### 2. Fixed Indentation Errors

**Fixed in `pyHaasAPI/api.py`:**
```python
# Line 279: Fixed indentation after else:
else:
    resp = requests.get(url, params=query_params)  # Now properly indented
```

**Fixed in `pyHaasAPI/lab.py`:**
```python
# Added missing try/except block
try:
    # Parameter optimization logic
    # ...
    return final_lab
except Exception as e:
    log.error(f"❌ Error during lab parameter update: {e}")
    return lab_details
```

### 3. Enhanced Lab Creation Pattern

The working pattern uses `CreateLabRequest.with_generated_name()` which properly formats market tags:

```python
# Market tag format: "BINANCE_BTC_USDT_"
market_tag = f"{exchange_code.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"

req = CreateLabRequest.with_generated_name(
    script_id=script_id,
    account_id=account_id,
    market=cloud_market,
    exchange_code=exchange_code,
    interval=interval,
    default_price_data_style="CandleStick"
)
```

## Verification

The fix was verified using `examples/lab_full_rundown.py` which demonstrates:

✅ **Correct Market Assignment**: `Market Tag: 'BINANCE_BTC_USDT_'`
✅ **Correct Account Assignment**: `Account ID: '4ba07e12-0e45-48d4-9826-be139680957c'`
✅ **Settings Preservation**: All critical settings maintained throughout workflow
✅ **Successful Backtesting**: Labs complete backtests with correct configuration

## Files Affected

### Core API Files
- `pyHaasAPI/api.py` - Fixed HTTP method and indentation
- `pyHaasAPI/lab.py` - Fixed syntax errors and parameter handling

### Example Files
- `examples/lab_full_rundown.py` - Working example (fixed main function call)
- `examples/bulk_create_labs_for_pairs.py` - Uses same pattern

### Documentation
- `docs/lab_management.md` - Updated with correct patterns
- `docs/MARKET_ACCOUNT_ASSIGNMENT_FIX.md` - This document

## Best Practices

### For Lab Creation
1. **Use `CreateLabRequest.with_generated_name()`** for proper market tag formatting
2. **Match accounts to markets by exchange code**
3. **Validate settings after creation**

### For Lab Updates
1. **Use POST with form-encoded data** for UPDATE_LAB_DETAILS
2. **JSON-encode complex objects** (settings, config, parameters)
3. **Preserve critical settings** during parameter optimization

### For Error Handling
1. **Check market tag and account ID** after lab creation
2. **Verify settings preservation** throughout workflow
3. **Handle API errors gracefully** with proper logging

## Testing

To verify the fix works:

```bash
# Run the working example
python -m examples.lab_full_rundown

# Expected output includes:
# ✅ Market tag is set
# ✅ Account ID is set
# ✅ All settings preserved throughout the process
```

## Impact

This fix resolves the core issue where labs were being queued with wrong market information, enabling:

- ✅ Proper lab creation with correct market/account assignment
- ✅ Successful backtesting with valid configuration
- ✅ Reliable bulk lab creation workflows
- ✅ Consistent parameter optimization without losing settings

## Related Issues

- **Memory ID 3654712**: Parameter definitions and valid ranges should be implemented in the API layer
- **Bulk Lab Creation**: Now works correctly with proper market/account assignment
- **Lab Cloning**: Preserves settings correctly during cloning operations 