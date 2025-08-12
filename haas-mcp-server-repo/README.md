# HaasOnline MCP Server

A Model Context Protocol (MCP) server that provides access to HaasOnline API functionality.

## Features

- **Complete HaasOnline Integration**: 60+ API endpoints
- **Account Management**: Create and manage trading accounts
- **Lab Operations**: Create, clone, and execute trading labs
- **Market Data**: Access real-time and historical market data
- **Backtest Execution**: Run and analyze trading strategies

## Installation

```bash
pip install haas-mcp-server
```

## Quick Start

1. Set up environment variables:
```bash
export API_HOST=127.0.0.1
export API_PORT=8090
export API_EMAIL=your_email@example.com
export API_PASSWORD=your_password
```

2. Run the server:
```bash
python server.py
```

## Configuration

Configure via `.env` file or environment variables:

```env
API_HOST=127.0.0.1
API_PORT=8090
API_EMAIL=your_email@example.com
API_PASSWORD=your_password
```

## License

MIT License - see LICENSE file for details.

---

**Author: Cosmos**
