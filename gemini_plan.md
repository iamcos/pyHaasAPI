# Gemini Plan: Refactor `pyHaasAPI/model.py`

## Goal

Refactor `pyHaasAPI/model.py` to replace the incorrect Pydantic models for backtest runtime data with the correct dataclass definitions.

## Current Situation

- The `get_backtest_runtime` API call returns a JSON response that is consistent with the example in `documentation/get_backtest_runtime.txt`.
- The Pydantic models in `pyHaasAPI/model.py` are causing `ValidationError` because they do not match the structure of the API response.
- The file `backtest_runtime_data_processed.py` contains the correct dataclass definitions for the backtest runtime data.
- The `test_single_backtest_retrieval.py` test now successfully extracts the raw API response and can be used to verify the changes.

## Plan

1.  **Modify `pyHaasAPI/model.py`:**
    -   Remove the following Pydantic models from `pyHaasAPI/model.py`:
        -   `ChartColors`
        -   `ChartDetails`
        -   `FeeDetails`
        -   `PerformanceDetails`
        -   `OrderStats`
        -   `PositionStats`
        -   `TradeStats`
        -   `ReportDetails`
        -   `OrderInPosition`
        -   `ManagedPosition`
        -   `FinishedPosition`
        -   `InputFieldDetail`
        -   `BacktestRuntimeData`
        -   `BacktestRuntimeResponse`
        -   `BotRuntimeData`
    -   Append the content of `backtest_runtime_data_processed.py` to the end of `pyHaasAPI/model.py`. This will add the correct dataclass definitions.

2.  **Update `pyHaasAPI/api.py`:**
    -   Search for usages of the old Pydantic models (e.g., `BacktestRuntimeData.model_validate`) and replace them with the new dataclass-based approach. This will likely involve using `dacite.from_dict` to deserialize the response into the new dataclasses.

3.  **Update `pyHaasAPI/backtest_object.py`:**
    -   Update the `BacktestObject` class to use the new dataclasses for `runtime` data.

4.  **Verify Changes:**
    -   Run the `test_single_backtest_retrieval.py` test to ensure that the backtest data is retrieved and parsed correctly without validation errors.
    -   Run the `temp_parse_response.py` script to confirm that the new models can parse the saved JSON response.