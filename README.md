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

## MCP Server

The library includes an MCP server for AI agent integration:

```bash
python -m pyHaasAPI.mcp.cursor_mcp_server
```
