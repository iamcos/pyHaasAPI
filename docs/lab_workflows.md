# Lab Workflows and Parameter Management Guide

**Last updated: July 2024**

All major lab workflows are now covered by robust, tested example scripts in the examples/ directory. See examples/README.md for a full index and usage guide. All scripts have been tested and updated to match the latest API as of July 2024.

---

## 1. Supported Workflows

### 1.1. Lab Lifecycle (Recommended)
- Use the full lifecycle pattern for labs: create, clone, update, parameterize, backtest, monitor, and delete.
- **See example:** [examples/lab_lifecycle_example.py](../examples/lab_lifecycle_example.py), [examples/utility_advanced_example.py](../examples/utility_advanced_example.py)

### 1.2. Lab Cloning
- Use `clone_lab()` to create an exact copy of an existing lab, preserving all settings and parameters.
- **See example:** [examples/lab_lifecycle_example.py](../examples/lab_lifecycle_example.py), [examples/fixed_clone_example_lab.py](../examples/fixed_clone_example_lab.py), [examples/simple_clone_example_lab.py](../examples/simple_clone_example_lab.py)

### 1.3. Lab Updating
- Use `update_lab_details()` to change market tag, account ID, or config/parameters after cloning.
- **See example:** [examples/lab_lifecycle_example.py](../examples/lab_lifecycle_example.py), [examples/update_lab_details.py](../examples/update_lab_details.py), [examples/debug_lab_config.py](../examples/debug_lab_config.py)

### 1.4. Parameter Changing
- Update parameters as part of `update_lab_details()` or with dedicated parameter update functions.
- **See example:** [examples/lab_lifecycle_example.py](../examples/lab_lifecycle_example.py), [examples/lab_parameters.py](../examples/lab_parameters.py), [examples/parameter_handling_example.py](../examples/parameter_handling_example.py), [examples/randomize_lab_parameters.py](../examples/randomize_lab_parameters.py)

### 1.5. Bulk Operations
- Use bulk lab creation and management patterns for production-ready workflows across many markets/accounts.
- **See example:** [examples/utility_advanced_example.py](../examples/utility_advanced_example.py), [examples/flexible_lab_workflow.py](../examples/flexible_lab_workflow.py), [examples/integrated_lab_workflow.py](../examples/integrated_lab_workflow.py), [examples/bulk_create_labs_for_pairs.py](../examples/bulk_create_labs_for_pairs.py), [examples/recreate_and_clone_labs.py](../examples/recreate_and_clone_labs.py)

---

## 2. Config/Parameter Mapping Table

| Alias | Field Name        | Meaning         |
|-------|-------------------|----------------|
| MP    | max_population    | Max Population |
| MG    | max_generations   | Max Generations|
| ME    | max_elites        | Max Elites     |
| MR    | mix_rate          | Mix Rate       |
| AR    | adjust_rate       | Adjust Rate    |

**Example Config:**
```json
{"MP":10,"MG":100,"ME":3,"MR":40.0,"AR":25.0}
```

- Always serialize config with `model_dump_json(by_alias=True)`.

---

## 3. Parameter Handling System

- Parameters are organized in groups and support type conversion, hierarchical access, and dictionary conversion.
- Use `ScriptParameters.from_api_response()` to create parameter containers from API data.
- Access parameters by path, group, or as a flat dictionary.
- **See example:** [examples/parameter_handling_example.py](../examples/parameter_handling_example.py), [examples/lab_parameters.py](../examples/lab_parameters.py), [examples/lab_lifecycle_example.py](../examples/lab_lifecycle_example.py)

**Example:**
```python
params = ScriptParameters.from_api_response(api_data)
rsi_length = params.get_parameter("MadHatter RSI.RSI Length")
if rsi_length:
    print(f"RSI Length: {rsi_length.value}")
```

**Parameter Update Structure:**
```json
[
  {"K": "TradeAmount", "O": [10], "I": false, "IS": false},
  {"K": "Interval", "O": [5, 3], "I": true, "IS": true}
]
```
- Always send the full list of parameters you want the lab to have; omitted parameters will be removed.

---

## 4. Best Practices

- **Always use `clone_lab()` for copying labs.**
- **Update market tag and account ID after cloning.**
- **Ensure config parameters are correct before backtesting.**
- **Use bulk functions for large-scale operations.**
- **Validate parameters before submission.**
- **Monitor lab execution and handle errors gracefully.**
- **Delete unused labs to free resources.**
- **Batch parameter updates when possible.**
- **Use appropriate polling intervals for monitoring.**
- **See examples/README.md for robust error handling patterns.**

---

## 5. Troubleshooting

- **404 Errors on UPDATE_LAB_DETAILS:**
  - Use `labid` (not `labId`)
  - Serialize config with `by_alias=True`
  - Use GET method (not POST)
- **Config Parameters Not Applied:**
  - Check field names in `LabConfig`
  - Ensure correct serialization
- **Backtest Start Failures:**
  - Ensure lab is in CREATED status
  - Check parameter format for `START_LAB_EXECUTION`
  - Verify lab has valid market tag and account ID
- **Parameter Update Issues:**
  - Use plain dicts/lists, not Pydantic objects
  - Include all required fields (`K`, `O`, `I`, `IS`)
- **See examples/lab_lifecycle_example.py and utility_advanced_example.py for robust error handling.**

---

## 6. API Operations Reference

- `create_lab()`: Create new lab instance
- `clone_lab()`: Clone existing lab (recommended)
- `delete_lab()`: Remove lab
- `get_lab_details()`: Retrieve lab configuration
- `update_lab_details()`: Modify lab settings/parameters
- `get_all_labs()`: List all labs
- `start_lab_execution()`: Begin backtest
- `cancel_lab_execution()`: Stop running backtest
- `get_lab_execution_update()`: Check execution status
- `get_backtest_result()`: Retrieve test results
- `bulk_clone_and_backtest_labs()`: Bulk workflow for many markets

---

## 7. Example Code Snippets

**Clone and Backtest a Lab:**
```python
result = api.clone_and_backtest_lab(
    executor=executor,
    source_lab_id="example_lab_id",
    new_lab_name="BTC_USDT_Backtest",
    market_tag="BINANCE_BTC_USDT_",
    account_id="account_id",
    start_unix=1744009200,
    end_unix=1752994800,
    config=LabConfig(max_population=10, max_generations=100, max_elites=3, mix_rate=40.0, adjust_rate=25.0)
)
```

**Bulk Workflow:**
```python
market_configs = [
    {"name": "BTC_USDT_Backtest", "market_tag": "BINANCE_BTC_USDT_", "account_id": "account1"},
    {"name": "ETH_USDT_Backtest", "market_tag": "BINANCE_ETH_USDT_", "account_id": "account1"},
]
results = api.bulk_clone_and_backtest_labs(
    executor=executor,
    source_lab_id="example_lab_id",
    market_configs=market_configs,
    start_unix=1744009200,
    end_unix=1752994800
)
```

---

## History Sync Management

Market history synchronization ("Price History Status" in the interface, "History Sync" in the menu) ensures that backtests and labs have access to sufficient historical data. Always check and set history depth before running backtests on new markets.

### 1. Check History Status for All Markets
```python
history_status = api.get_history_status(auth_executor)
for market, info in history_status.items():
    print(f"Market: {market}, Status: {info}")
```

### 2. Set History Depth for a Single Market
```python
success = api.set_history_depth(auth_executor, market="BINANCE_BTC_USDT_", months=12)
print(f"Set history depth: {success}")
```

### 3. Bulk Set History Depth for All Markets
```python
history_status = api.get_history_status(auth_executor)
for market in history_status.keys():
    api.set_history_depth(auth_executor, market, months=12)
```

**See also:**
- [examples/utility_advanced_example.py](../examples/utility_advanced_example.py)
- [examples/lab_lifecycle_example.py](../examples/lab_lifecycle_example.py)
- [examples/bulk_set_history_depth.py](../examples/bulk_set_history_depth.py)
- [examples/simple_history_status.py](../examples/simple_history_status.py)
- [examples/debug_history_status.py](../examples/debug_history_status.py)
- [examples/get_history_status.py](../examples/get_history_status.py)
- [examples/test_set_history_depth.py](../examples/test_set_history_depth.py)

---

## 8. References
- `examples/README.md` - Example script index and usage
- `docs/BULK_LAB_CREATION_TUTORIAL.md` - End-user tutorial
- `pyHaasAPI/api.py` - API source 

---

## 9. Robust Lab Start Workflow (Sync, Set History, Start)

For reliable backtesting, always follow this robust workflow:

1. **Clone or select a lab** for your target market/account.
2. **Trigger a chart data fetch** (registers the market for sync):
   ```python
   api.get_chart(executor, market_tag)
   ```
3. **Wait for market sync**: Poll `api.get_history_status()` until the market status is `synched`.
4. **Set history depth** (e.g., 36 months):
   ```python
   api.set_history_depth(executor, market_tag, months=36)
   ```
5. **Wait for full sync**: Again, poll until the market is fully synced for the requested depth.
6. **Start the backtest** using the robust POST logic (see below).

**See example:** [examples/start_random_lab.py](../examples/start_random_lab.py), [utils/lab_management/lab_sync_and_backtest.py](../utils/lab_management/lab_sync_and_backtest.py)

---

## 10. API Endpoint Header Handling Rule

- **Only use browser-matching headers and robust POST logic for endpoints that are known to require it** (e.g., `START_LAB_EXECUTION`).
- For all other endpoints, use the default executor logic unless issues are observed.
- Document any exceptions or changes to this rule in this file.

**See implementation:**
- [pyHaasAPI/api.py](../pyHaasAPI/api.py) (`start_lab_execution`)
- [rules.cursor](../rules.cursor)

--- 