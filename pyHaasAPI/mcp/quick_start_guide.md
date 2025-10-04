# pyHaasAPI Cursor MCP Server - Quick Start Guide

## How It Works

The Cursor MCP server is designed to work with Cursor IDE and uses the existing pyHaasAPI server manager for SSH tunnel connectivity to multiple servers (srv01, srv02, srv03).

## Setup Steps

### 1. Install Dependencies
```bash
pip install mcp pyHaasAPI
```

### 2. Configure Environment
Create a `.env` file in your project root:
```bash
# .env file
API_EMAIL=your_email@example.com
API_PASSWORD=your_password
```

### 3. Test the Server
```bash
python pyHaasAPI/mcp/test_cursor_mcp.py
```

## Usage in Cursor

The MCP server integrates with Cursor's AI capabilities. You can use it by:

1. **Connect to a server:**
   - "Connect to srv01 using the pyHaasAPI MCP server"

2. **List all labs:**
   - "List all available labs from the current server"

3. **Analyze labs:**
   - "Analyze lab [lab-id] and show me the top 5 backtests"

4. **Create bots:**
   - "Create 3 bots from the best performing lab"

5. **Get market data:**
   - "Show me the current price for BTC_USDT_PERPETUAL"

6. **Mass operations:**
   - "Create bots from all qualifying labs with 60%+ win rate"

## Available Commands

The MCP server provides 25+ tools including:

- **Lab Management**: `list_labs`, `get_lab_details`, `create_lab`, `start_lab_execution`
- **Bot Management**: `list_bots`, `create_bot`, `activate_bot`, `deactivate_bot`
- **Analysis**: `analyze_lab`, `create_bots_from_analysis`, `run_wfo_analysis`
- **Market Data**: `get_markets`, `get_price_data`, `get_historical_data`
- **Account Management**: `list_accounts`, `get_account_balance`, `configure_account`
- **Mass Operations**: `mass_bot_creation`, `analyze_all_labs`

## Testing the Setup

### Test MCP Server Directly
```bash
# Test the server connection
python pyHaasAPI/mcp/test_mcp_server.py
```

### Test with Claude
1. Open Claude Desktop
2. Ask: "Can you connect to the HaasOnline API and list all labs?"
3. Claude should use the MCP server to fetch the data

## Troubleshooting

### Common Issues
1. **SSH Tunnel**: Make sure the SSH tunnel to srv01 is active
2. **Credentials**: Verify your API_EMAIL and API_PASSWORD in .env
3. **Port**: Ensure port 8090 is available and not blocked
4. **Claude Restart**: Restart Claude Desktop after configuration changes

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m pyHaasAPI.mcp.mcp_server
```

## Example Workflow

1. **Start SSH tunnel to srv01**
2. **Configure Claude Desktop with MCP server**
3. **Restart Claude Desktop**
4. **Ask Claude**: "Connect to HaasOnline and list all labs from server 1"
5. **Claude will use the MCP server to fetch and display the labs**

The MCP server acts as a bridge between Claude and the HaasOnline API, providing all the trading functionality through natural language commands.
