# Lab Management

This section details how to manage labs using the Haaslib library.

## Creating a Lab

To create a new lab, use the `create_lab` function.  This requires a `CreateLabRequest` object specifying the script ID, account ID, market, interval, and other parameters.

```python
from haaslib.api import create_lab
from haaslib.model import CreateLabRequest

# ... (Assuming auth_executor is already initialized) ...

lab = create_lab(auth_executor, CreateLabRequest(
    script_id="YOUR_SCRIPT_ID",  # Replace with actual script ID
    name="My Test Lab",
    account_id="YOUR_ACCOUNT_ID",  # Replace with actual account ID
    market="YOUR_MARKET_TAG",  # e.g., "BINANCE_BTC_USDT_"
    interval=15,
    default_price_data_style="CandleStick"
))

print(f"Lab created with ID: {lab.lab_id}")
```

## Starting Lab Execution

Once a lab is created, start its execution using `start_lab_execution` and a `StartLabExecutionRequest` object specifying the start and end times.

```python
from haaslib.api import start_lab_execution
from haaslib.model import StartLabExecutionRequest
from datetime import datetime

# ... (Assuming lab object is already created) ...

end_time = int(datetime.now().timestamp())
start_time = end_time - (24 * 60 * 60 * 30) # 30 days ago

lab_details = start_lab_execution(auth_executor, StartLabExecutionRequest(
    lab_id=lab.lab_id,
    start_unix=start_time,
    end_unix=end_time,
    send_email=False
))

print(f"Lab execution started: {lab_details}")
```

## Monitoring Lab Status

Use `get_lab_details` to monitor the lab's status.  The function returns a `LabDetails` object containing the current status and other information.

```python
from haaslib.api import get_lab_details

details = get_lab_details(auth_executor, lab.lab_id)
print(f"Lab status: {details.status}")
```

## Getting Backtest Results

After the lab completes, retrieve the backtest results using `get_backtest_result` and a `GetBacktestResultRequest` object.

```python
from haaslib.api import get_backtest_result
from haaslib.model import GetBacktestResultRequest

results = get_backtest_result(auth_executor, GetBacktestResultRequest(
    lab_id=lab.lab_id,
    next_page_id=0,
    page_lenght=100
))

print(f"Backtest results: {results}")
```

## Deleting a Lab

To delete a lab, use the `delete_lab` function.

```python
from haaslib.api import delete_lab

delete_lab(auth_executor, lab.lab_id)
print("Lab deleted successfully")
```

## Handling Errors

The `HaasApiError` exception is raised for API errors.  Implement appropriate error handling in your code.

```python
try:
    # ... your code ...
except HaasApiError as e:
    print(f"API Error: {e}")
```

## Selecting Markets and Accounts

The examples above assume you have already selected a valid market and account.  Refer to the Market Operations and Account Management sections for details on how to do this.  Note that the selection of markets and accounts is crucial for successful lab execution.  The code includes retry logic to handle cases where the selected market is invalid or the lab gets stuck in a queued state.  This retry mechanism ensures robustness and prevents unnecessary failures.
