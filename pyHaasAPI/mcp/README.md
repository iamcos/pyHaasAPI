# pyHaasAPI MCP Server

This directory contains the MCP (Model Context Protocol) server implementation for pyHaasAPI, designed to work with Cursor IDE and using the existing server manager for SSH tunnel connectivity.

## Files

- **`cursor_mcp_server.py`** - Main Cursor MCP server implementation with 25+ tools
- **`cursor_mcp_handlers.py`** - Comprehensive tool handlers and business logic
- **`test_cursor_mcp.py`** - Test script for the Cursor MCP server
- **`quick_start_guide.md`** - Quick start guide for Cursor integration
- **`MCP_AI_USAGE_GUIDE.md`** - Comprehensive usage documentation
- **`MCP_SERVER_OVERVIEW.md`** - Technical overview and architecture

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install mcp pyHaasAPI
   ```

2. **Configure environment:**
   Create `.env` file with your credentials:
   ```bash
   API_EMAIL=your_email@example.com
   API_PASSWORD=your_password
   ```

3. **Test the server:**
   ```bash
   python pyHaasAPI/mcp/test_cursor_mcp.py
   ```

## Available Tools

The MCP server provides 25+ tools covering:

- **Lab Management** (5 tools) - Create, configure, and execute labs
- **Bot Management** (5 tools) - Create, activate, and manage trading bots
- **Analysis & Optimization** (3 tools) - Comprehensive analysis and WFO
- **Account Management** (3 tools) - Account configuration and balance
- **Market Data** (3 tools) - Real-time and historical market data
- **Script Management** (2 tools) - Trading script management
- **Backtest Management** (3 tools) - Backtest execution and results
- **Order Management** (3 tools) - Order placement and management
- **Reporting & Analytics** (2 tools) - Report generation and metrics
- **Mass Operations** (2 tools) - Batch operations and automation

## Usage

### Claude Desktop Integration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "pyhaasapi": {
      "command": "python",
      "args": ["-m", "pyHaasAPI.mcp.mcp_server"]
    }
  }
}
```

### Programmatic Usage

```python
from pyHaasAPI.mcp import mcp_server_instance

# Initialize server
await mcp_server_instance.initialize()

# Use tools
result = await handle_list_labs()
```

## Documentation

- **`MCP_AI_USAGE_GUIDE.md`** - Complete usage guide with examples
- **`MCP_SERVER_OVERVIEW.md`** - Technical architecture overview

## Features

- ✅ **Complete API Coverage** - All pyHaasAPI functionality exposed
- ✅ **Async Architecture** - Full async/await support
- ✅ **Type Safety** - Comprehensive type hints
- ✅ **Error Handling** - Robust error handling and logging
- ✅ **Authentication** - Automatic session management
- ✅ **Resource Management** - Proper cleanup and connections

## AI Capabilities

With this MCP server, AI agents can:

1. **Autonomous Trading** - Analyze labs and create profitable bots
2. **Market Analysis** - Gather data and identify opportunities
3. **Portfolio Management** - Manage multiple labs and bots
4. **Automation** - Automate complex trading workflows

## Support

For detailed usage instructions, see `MCP_AI_USAGE_GUIDE.md`.

For technical details, see `MCP_SERVER_OVERVIEW.md`.



