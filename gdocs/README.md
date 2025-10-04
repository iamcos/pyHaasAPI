# Google Sheets Integration for pyHaasAPI

This directory contains Google Sheets integration components for publishing pyHaasAPI data.

## Files

- `google_credentials.json` - Google service account credentials (not in git)
- `publish.py` - Simple CLI tool for publishing data to Google Sheets
- `google_credentials_setup.md` - Setup guide for Google Cloud credentials
- `GETTING_STARTED.md` - Quick start guide

## Core Implementation

The main Google Sheets functionality is implemented in:
- `pyHaasAPI/services/google_sheets_service.py` - Core service
- `pyHaasAPI/mcp/cursor_mcp_handlers.py` - MCP handlers
- `pyHaasAPI/mcp/cursor_mcp_server.py` - MCP tools

## Usage

### CLI Tool

```bash
# Publish data to Google Sheets
python gdocs/publish.py --sheet-id "YOUR_SHEET_ID"

# With custom credentials path
python gdocs/publish.py --sheet-id "YOUR_SHEET_ID" --credentials path/to/credentials.json
```

### Python API

```python
from pyHaasAPI.services.google_sheets_service import GoogleSheetsService, MultiServerDataCollector

async def publish_data():
    sheets_service = GoogleSheetsService("gdocs/google_credentials.json", "YOUR_SHEET_ID")
    data_collector = MultiServerDataCollector()
    
    server_configs = {
        "srv01": {"host": "127.0.0.1", "port": 8090},
        "srv02": {"host": "127.0.0.1", "port": 8091},
        "srv03": {"host": "127.0.0.1", "port": 8092}
    }
    
    all_data = await data_collector.collect_all_server_data(server_configs)
    
    for server_name, data in all_data.items():
        await sheets_service.publish_server_data(server_name, data)
    
    await sheets_service.publish_summary(all_data)
```

### MCP Integration

The Google Sheets functionality is available through MCP:

- `publish_to_google_sheets` - Publish data from all servers
- `update_google_sheets_server` - Update data for specific server

## Setup

1. Set up Google Cloud credentials (see `google_credentials_setup.md`)
2. Place `google_credentials.json` in the `gdocs` directory
3. Get your Google Sheets ID from the URL
4. Start SSH tunnels for each server:
   ```bash
   ssh -N -L 8090:127.0.0.1:8090 srv01 &
   ssh -N -L 8091:127.0.0.1:8090 srv02 &
   ssh -N -L 8092:127.0.0.1:8090 srv03 &
   ```
5. Run the publish script

## Data Structure

The service publishes data to separate sheets for each server:
- `srv01` - Server 1 data
- `srv02` - Server 2 data
- `srv03` - Server 3 data
- `Summary` - Cross-server summary

Each server sheet contains:
- Labs with IDs, names, status, markets, scripts
- Bots with performance metrics, ROI, profits, errors
- Accounts with balances and status
- Browser links for direct access
