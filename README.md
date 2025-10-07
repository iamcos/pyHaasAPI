# pyHaasAPI

A comprehensive Python library for interacting with the HaasOnline trading platform.

## Features

- Complete API coverage for lab management, bot operations, and trading
- Async/await support throughout
- Comprehensive type safety
- MCP server integration for AI agents
- CLI tools for automation

## Installation

```bash
pip install -e .
```

## Usage

```python
from pyHaasAPI import AsyncHaasClient, AuthenticationManager

# Create client and authenticate
client = AsyncHaasClient(host="127.0.0.1", port=8090)
auth_manager = AuthenticationManager(email="your_email", password="your_password")
await auth_manager.authenticate()

# Use the client
labs = await client.get_labs()
```

## Endpoints and Connectivity (PHP routes only)

Use a single SSH tunnel to srv03 and point the client to 127.0.0.1:8090.

```bash
ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv03
```

Only the PHP JSON endpoints are supported (avoid frontend paths):

- Accounts: `/AccountAPI.php?channel=GET_ACCOUNTS`
- Markets: `/PriceAPI.php?channel=MARKETLIST`, `/PriceAPI.php?channel=TRADE_MARKETS&pricesource=...`
- Scripts: `/HaasScriptAPI.php?channel=GET_ALL_SCRIPT_ITEMS&userid=<...>&interfacekey=<...>`
- Orders: `/AccountAPI.php?channel=GET_ORDERS&accountid=<...>`, `/AccountAPI.php?channel=GET_ALL_ORDERS`
- Backtests: `/BacktestAPI.php?channel=GET_HISTORY_STATUS`, `/LabsAPI.php?channel=GET_BACKTEST_RESULT_PAGE&labid=<...>`
- Labs: `/LabsAPI.php?channel=GET_LAB_DETAILS`, `/LabsAPI.php?channel=CREATE_LAB`, `/LabsAPI.php?channel=DELETE_LAB`

Troubleshooting:
- If you see HTML instead of JSON, the request hit a frontend route. Use the PHP endpoints above exclusively.
- Ensure the tunnel is active before running any CLI/tests.

## CI Smoke Gate

A GitHub Actions workflow (`.github/workflows/smoke.yml`) runs a fast smoke suite on every PR:

- Starts the SSH tunnel to srv03
- Runs read-only smoke tests for Accounts, Markets, Scripts, Orders, and Backtests
- Blocks merges if the smoke suite fails

Required repository secrets:

- `SSH_PRIVATE_KEY`, `SRV03_HOST`, `SRV03_USER`
- `API_EMAIL`, `API_PASSWORD`

## MCP Server

The library includes an MCP server for AI agent integration:

```bash
python -m pyHaasAPI.mcp.cursor_mcp_server
```
