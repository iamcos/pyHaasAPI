# pyHaasAPI MCP Server - AI Usage Guide

## Overview

The pyHaasAPI MCP Server provides comprehensive access to all pyHaasAPI functionality for AI agents. This server exposes the entire HaasOnline trading platform through a standardized MCP interface, enabling AI agents to have full control over lab management, bot operations, analysis, and trading.

## Architecture

### Core Components

1. **MCP Server** (`mcp_server.py`) - Main server implementation
2. **Tool Handlers** (`mcp_handlers.py`) - Implementation of all tool functions
3. **API Modules** - Lab, Bot, Account, Script, Market, Backtest, Order APIs
4. **Services** - High-level business logic (LabService, BotService, AnalysisService)
5. **Models** - Data structures and type definitions

### Key Features

- **Complete API Coverage** - All pyHaasAPI functionality exposed as MCP tools
- **Async Support** - Full async/await pattern for performance
- **Type Safety** - Comprehensive type hints and validation
- **Error Handling** - Robust error handling and logging
- **Authentication** - Automatic authentication management
- **Resource Management** - Proper cleanup and connection management

## Available Tools

### 1. Authentication & Connection

#### `connect_to_haas`
Connect to HaasOnline API with authentication.

**Parameters:**
- `host` (string, optional): API host (default: "127.0.0.1")
- `port` (integer, optional): API port (default: 8090)

**Example:**
```json
{
  "host": "127.0.0.1",
  "port": 8090
}
```

### 2. Lab Management

#### `list_labs`
List all available labs.

**Parameters:** None

#### `get_lab_details`
Get detailed information about a specific lab.

**Parameters:**
- `lab_id` (string, required): Lab ID

#### `create_lab`
Create a new lab for backtesting.

**Parameters:**
- `name` (string, required): Lab name
- `script_id` (string, required): Script ID
- `account_id` (string, required): Account ID
- `market` (string, required): Trading market
- `parameters` (object, optional): Lab parameters

#### `start_lab_execution`
Start lab backtesting execution.

**Parameters:**
- `lab_id` (string, required): Lab ID
- `max_iterations` (integer, optional): Maximum iterations (default: 1500)

#### `get_lab_execution_status`
Get the current status of lab execution.

**Parameters:**
- `lab_id` (string, required): Lab ID

### 3. Bot Management

#### `list_bots`
List all trading bots.

**Parameters:** None

#### `get_bot_details`
Get detailed information about a specific bot.

**Parameters:**
- `bot_id` (string, required): Bot ID

#### `create_bot`
Create a new trading bot.

**Parameters:**
- `name` (string, required): Bot name
- `script_id` (string, required): Script ID
- `account_id` (string, required): Account ID
- `market` (string, required): Trading market
- `leverage` (number, optional): Leverage (default: 20.0)
- `trade_amount` (number, optional): Trade amount (default: 2000.0)

#### `activate_bot`
Activate a bot for live trading.

**Parameters:**
- `bot_id` (string, required): Bot ID

#### `deactivate_bot`
Deactivate a bot.

**Parameters:**
- `bot_id` (string, required): Bot ID

### 4. Analysis & Optimization

#### `analyze_lab`
Analyze lab performance and get top backtests.

**Parameters:**
- `lab_id` (string, required): Lab ID
- `top_count` (integer, optional): Number of top results (default: 10)
- `min_win_rate` (number, optional): Minimum win rate (default: 0.3)
- `min_trades` (integer, optional): Minimum trades (default: 5)

#### `create_bots_from_analysis`
Create bots from lab analysis results.

**Parameters:**
- `lab_id` (string, required): Lab ID
- `count` (integer, optional): Number of bots to create (default: 3)
- `activate` (boolean, optional): Activate bots immediately (default: false)

#### `run_wfo_analysis`
Run Walk Forward Optimization analysis.

**Parameters:**
- `lab_id` (string, required): Lab ID
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)
- `training_days` (integer, optional): Training period in days (default: 365)
- `testing_days` (integer, optional): Testing period in days (default: 90)

### 5. Account Management

#### `list_accounts`
List all trading accounts.

**Parameters:** None

#### `get_account_balance`
Get account balance information.

**Parameters:**
- `account_id` (string, required): Account ID

#### `configure_account`
Configure account settings.

**Parameters:**
- `account_id` (string, required): Account ID
- `leverage` (number, optional): Leverage setting
- `margin_mode` (string, optional): Margin mode
- `position_mode` (string, optional): Position mode

### 6. Market Data

#### `get_markets`
Get available trading markets.

**Parameters:** None

#### `get_price_data`
Get real-time price data for a market.

**Parameters:**
- `market` (string, required): Market symbol

#### `get_historical_data`
Get historical price data.

**Parameters:**
- `market` (string, required): Market symbol
- `start_date` (string, required): Start date (YYYY-MM-DD)
- `end_date` (string, required): End date (YYYY-MM-DD)
- `interval` (string, optional): Data interval (default: "1h")

### 7. Script Management

#### `list_scripts`
List all available trading scripts.

**Parameters:** None

#### `get_script_details`
Get detailed information about a script.

**Parameters:**
- `script_id` (string, required): Script ID

### 8. Backtest Management

#### `get_lab_backtests`
Get all backtests for a lab.

**Parameters:**
- `lab_id` (string, required): Lab ID

#### `get_backtest_results`
Get detailed backtest results.

**Parameters:**
- `backtest_id` (string, required): Backtest ID

#### `run_longest_backtest`
Run the longest possible backtest for a lab.

**Parameters:**
- `lab_id` (string, required): Lab ID
- `max_iterations` (integer, optional): Maximum iterations (default: 1500)

### 9. Order Management

#### `get_bot_orders`
Get orders for a specific bot.

**Parameters:**
- `bot_id` (string, required): Bot ID

#### `place_order`
Place a new order.

**Parameters:**
- `account_id` (string, required): Account ID
- `market` (string, required): Market symbol
- `side` (string, required): Order side (buy/sell)
- `amount` (number, required): Order amount
- `price` (number, optional): Order price

#### `cancel_order`
Cancel an existing order.

**Parameters:**
- `order_id` (string, required): Order ID

### 10. Reporting & Analytics

#### `generate_analysis_report`
Generate comprehensive analysis report.

**Parameters:**
- `lab_id` (string, required): Lab ID
- `format` (string, optional): Report format (default: "json")
- `include_charts` (boolean, optional): Include charts (default: false)

#### `get_performance_metrics`
Get performance metrics for bots or labs.

**Parameters:**
- `entity_type` (string, required): "lab" or "bot"
- `entity_id` (string, required): Entity ID
- `timeframe` (string, optional): Timeframe (default: "all")

### 11. Mass Operations

#### `mass_bot_creation`
Create bots from all qualifying labs.

**Parameters:**
- `top_count` (integer, optional): Number of top bots per lab (default: 5)
- `min_win_rate` (number, optional): Minimum win rate (default: 0.3)
- `min_trades` (integer, optional): Minimum trades (default: 5)
- `activate` (boolean, optional): Activate bots immediately (default: false)

#### `analyze_all_labs`
Analyze all labs and generate reports.

**Parameters:**
- `min_win_rate` (number, optional): Minimum win rate (default: 0.3)
- `min_trades` (integer, optional): Minimum trades (default: 5)
- `generate_reports` (boolean, optional): Generate reports (default: true)

## Common Usage Patterns

### 1. Complete Lab Analysis Workflow

```json
// 1. Connect to API
{
  "tool": "connect_to_haas",
  "parameters": {
    "host": "127.0.0.1",
    "port": 8090
  }
}

// 2. List available labs
{
  "tool": "list_labs",
  "parameters": {}
}

// 3. Analyze specific lab
{
  "tool": "analyze_lab",
  "parameters": {
    "lab_id": "lab-123",
    "top_count": 10,
    "min_win_rate": 0.4,
    "min_trades": 10
  }
}

// 4. Create bots from analysis
{
  "tool": "create_bots_from_analysis",
  "parameters": {
    "lab_id": "lab-123",
    "count": 3,
    "activate": true
  }
}
```

### 2. Mass Bot Creation Workflow

```json
// 1. Analyze all labs
{
  "tool": "analyze_all_labs",
  "parameters": {
    "min_win_rate": 0.5,
    "min_trades": 20,
    "generate_reports": true
  }
}

// 2. Create bots from all qualifying labs
{
  "tool": "mass_bot_creation",
  "parameters": {
    "top_count": 5,
    "min_win_rate": 0.5,
    "min_trades": 20,
    "activate": true
  }
}
```

### 3. Market Analysis Workflow

```json
// 1. Get available markets
{
  "tool": "get_markets",
  "parameters": {}
}

// 2. Get price data for specific market
{
  "tool": "get_price_data",
  "parameters": {
    "market": "BTC_USDT_PERPETUAL"
  }
}

// 3. Get historical data
{
  "tool": "get_historical_data",
  "parameters": {
    "market": "BTC_USDT_PERPETUAL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "interval": "1h"
  }
}
```

### 4. Bot Management Workflow

```json
// 1. List all bots
{
  "tool": "list_bots",
  "parameters": {}
}

// 2. Get bot details
{
  "tool": "get_bot_details",
  "parameters": {
    "bot_id": "bot-123"
  }
}

// 3. Activate bot
{
  "tool": "activate_bot",
  "parameters": {
    "bot_id": "bot-123"
  }
}

// 4. Get bot orders
{
  "tool": "get_bot_orders",
  "parameters": {
    "bot_id": "bot-123"
  }
}
```

## Error Handling

All tools return structured responses with error information:

```json
{
  "type": "text",
  "text": "Error: Connection failed - Invalid credentials"
}
```

Common error scenarios:
- **Authentication errors**: Invalid credentials or expired sessions
- **Network errors**: Connection timeouts or server unavailable
- **Validation errors**: Invalid parameters or missing required fields
- **Business logic errors**: Insufficient funds, invalid market, etc.

## Performance Considerations

1. **Connection Management**: The server maintains persistent connections to avoid re-authentication
2. **Async Operations**: All operations are async for better performance
3. **Rate Limiting**: Built-in rate limiting to respect API limits
4. **Caching**: Intelligent caching for frequently accessed data
5. **Batch Operations**: Support for batch operations where possible

## Security

1. **Authentication**: Secure credential management with automatic session handling
2. **Input Validation**: Comprehensive input validation and sanitization
3. **Error Handling**: Secure error messages that don't expose sensitive information
4. **Resource Cleanup**: Proper cleanup of resources and connections

## Development

### Running the MCP Server

```bash
# Install dependencies
pip install mcp pyHaasAPI

# Run the server
python -m pyHaasAPI.mcp_server
```

### Configuration

The server uses environment variables for configuration:

```bash
export API_EMAIL="your_email@example.com"
export API_PASSWORD="your_password"
export API_HOST="127.0.0.1"
export API_PORT="8090"
```

### Testing

```bash
# Test individual tools
python -c "
import asyncio
from pyHaasAPI.mcp_server import mcp_server_instance
asyncio.run(mcp_server_instance.initialize())
"
```

## Integration Examples

### With Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "pyhaasapi": {
      "command": "python",
      "args": ["-m", "pyHaasAPI.mcp_server"],
      "env": {
        "API_EMAIL": "your_email@example.com",
        "API_PASSWORD": "your_password"
      }
    }
  }
}
```

### With Other MCP Clients

The server follows the MCP protocol and can be used with any MCP-compatible client.

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure SSH tunnel is established and API is accessible
2. **Authentication Failed**: Check credentials and ensure account is active
3. **Tool Not Found**: Verify tool name and parameters
4. **Timeout Errors**: Check network connectivity and server status

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For issues and questions:
1. Check the pyHaasAPI documentation
2. Review error messages and logs
3. Verify network connectivity
4. Check authentication credentials

## Future Enhancements

1. **Real-time Updates**: WebSocket support for real-time data
2. **Advanced Analytics**: More sophisticated analysis tools
3. **Portfolio Management**: Portfolio-level operations
4. **Risk Management**: Advanced risk assessment tools
5. **Automation**: Automated trading strategies
