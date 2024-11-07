# API Reference

This section provides a detailed reference for the Haaslib API functions.

## Authentication

```python
from haaslib.api import RequestsExecutor, Guest

# Create guest executor
executor = RequestsExecutor(
    host="127.0.0.1",
    port=8090,
    state=Guest()
)

# Authenticate
auth_executor = executor.authenticate(
    email="your_email@example.com",
    password="your_password"
)
```

## Scripts

### `get_all_scripts(executor: SyncExecutor[Authenticated]) -> list[HaasScriptItemWithDependencies]`

Retrieves information about all script items for an authenticated user.

### `get_scripts_by_name(executor: SyncExecutor[Authenticated], name_pattern: str, case_sensitive: bool = False) -> list[HaasScriptItemWithDependencies]`

Retrieves scripts that match the given name pattern.


## Accounts

### `get_accounts(executor: SyncExecutor[Authenticated]) -> list[UserAccount]`

Retrieves information about user accounts for an authenticated user.

### `get_account_data(executor: SyncExecutor[Authenticated], account_id: str) -> AccountData`

Get detailed information about an account including its exchange


## Labs

### `create_lab(executor: SyncExecutor[Authenticated], req: CreateLabRequest) -> LabDetails`

Creates a new lab.

### `start_lab_execution(executor: SyncExecutor[Authenticated], request: StartLabExecutionRequest) -> LabDetails`

Starts lab execution with specified parameters.

### `get_lab_details(executor: SyncExecutor[Authenticated], lab_id: str) -> LabDetails`

Gets details for a specific lab.

### `update_lab_details(executor: SyncExecutor[Authenticated], lab_id: str, config: LabConfig, settings: LabSettings, name: str, lab_type: str) -> LabDetails`

Updates lab details.

### `cancel_lab_execution(executor: SyncExecutor[Authenticated], lab_id: str) -> None`

Cancels a running lab execution.

### `get_lab_execution_update(executor: SyncExecutor[Authenticated], lab_id: str) -> LabExecutionUpdate`

Gets the current execution status of a lab.

### `get_backtest_result(executor: SyncExecutor[Authenticated], req: GetBacktestResultRequest) -> PaginatedResponse[LabBacktestResult]`

Retrieves the backtest result for a specific lab.

### `get_all_labs(executor: SyncExecutor[Authenticated]) -> list[LabRecord]`

Gets all labs for the authenticated user.

### `delete_lab(executor: SyncExecutor[Authenticated], lab_id: str)`

Removes a lab with the given ID.


## Bots

### `add_bot(executor: SyncExecutor[Authenticated], req: CreateBotRequest) -> HaasBot`

Creates a new bot.

### `add_bot_from_lab(executor: SyncExecutor[Authenticated], req: AddBotFromLabRequest) -> HaasBot`

Creates a new bot from a given lab's backtest.

### `delete_bot(executor: SyncExecutor[Authenticated], bot_id: str)`

Deletes a bot with the given ID.

### `get_all_bots(executor: SyncExecutor[Authenticated]) -> list[HaasBot]`

Gets all bots for the authenticated user.


## Error Handling

The `HaasApiError` exception is raised for API errors. Implement appropriate error handling in your code.

```python
try:
    # ... your code ...
except HaasApiError as e:
    print(f"API Error: {e}")
