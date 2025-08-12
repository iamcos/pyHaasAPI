# HaasOnline MCP Server

This is a Model Context Protocol (MCP) server that provides access to HaasOnline API functionality through Kiro.

## Features

The MCP server exposes the following tools:

### Account Management
- `get_haas_status` - Check API connection status
- `get_all_accounts` - List all user accounts
- `create_simulated_account` - Create new simulated accounts
- `get_account_balance` - Get account balance
- `deposit_funds` - Deposit funds to accounts

### Lab Management
- `get_all_labs` - List all labs
- `create_lab` - Create new labs
- `clone_lab` - Clone existing labs
- `delete_lab` - Delete labs
- `backtest_lab` - Start lab backtests
- `get_backtest_results` - Get backtest results

### Market & Script Management
- `get_all_markets` - List available markets
- `add_script` - Add new trading scripts

## Setup

1. Ensure your `.env` file contains the required HaasOnline API credentials:
   ```
   API_HOST=127.0.0.1
   API_PORT=8090
   API_EMAIL=your_email@example.com
   API_PASSWORD=your_password
   ```

2. Install MCP dependencies:
   ```bash
   pip install mcp python-dotenv
   ```

3. The server is automatically configured in `.kiro/settings/mcp.json`

## Usage

The MCP server runs automatically when Kiro starts. You can use the tools directly in Kiro chat by referencing them or they'll be available through the MCP protocol.

### Example Usage in Kiro

```
Can you check the HaasOnline API status?
```

```
Show me all my trading accounts
```

```
Create a new lab with script ID "abc123" and account ID "def456"
```

## Testing

You can test the MCP server directly:

```bash
cd mcp_server
python test_mcp.py
```

## Troubleshooting

1. **Authentication Issues**: Check your `.env` file credentials
2. **Connection Issues**: Ensure HaasOnline server is running on the specified host/port
3. **MCP Issues**: Check that the `mcp` Python package is installed

## Auto-Approved Tools

The following tools are auto-approved and won't require user confirmation:
- `get_haas_status`
- `get_all_accounts` 
- `get_all_labs`
- `get_all_markets`
- `get_account_balance`

Other tools may require user approval before execution.