#!/usr/bin/env python3
"""
Cursor MCP Server for pyHaasAPI

This MCP server is designed to work with Cursor IDE and uses the existing
pyHaasAPI server manager for SSH tunnel connectivity to multiple servers.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

# MCP imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ListResourcesRequest, ListResourcesResult,
    ReadResourceRequest, ReadResourceResult
)

# pyHaasAPI imports
from ..core.server_manager import ServerManager, ServerConfig
from ..core.data_manager import ComprehensiveDataManager
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager
from ..config.api_config import APIConfig
from ..api import LabAPI, BotAPI, AccountAPI, ScriptAPI, MarketAPI, BacktestAPI, OrderAPI
from ..services import LabService, BotService, AnalysisService, ReportingService
from ..models import *
from ..config.settings import Settings
from ..core.logging import get_logger

# Initialize server
server = Server("pyhaasapi-cursor-mcp-server")
logger = get_logger("cursor_mcp_server")

class CursorPyHaasAPIMCPServer:
    """
    Cursor MCP Server for pyHaasAPI functionality
    
    Uses the existing server manager for SSH tunnel connectivity
    and provides comprehensive access to all pyHaasAPI features.
    """
    
    def __init__(self):
        self.settings = Settings()
        self.server_manager: Optional[ServerManager] = None
        self.data_manager: Optional[ComprehensiveDataManager] = None
        self.logger = logger
        
        # API modules (will be initialized per server)
        self.api_modules: Dict[str, Dict[str, Any]] = {}
        
        # Current active server
        self.active_server: Optional[str] = None
        self.connected = False
        
    async def initialize(self):
        """Initialize the MCP server with server manager"""
        try:
            # Initialize server manager
            self.server_manager = ServerManager(self.settings)
            self.logger.info("Server manager initialized")
            
            # Initialize data manager
            self.data_manager = ComprehensiveDataManager()
            await self.data_manager.initialize()
            self.logger.info("Data manager initialized")
            
            self.connected = True
            logger.info("Cursor MCP Server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cursor MCP server: {e}")
            raise
    
    async def connect_to_server(self, server_name: str) -> bool:
        """Connect to a specific server using the server manager"""
        try:
            if not self.server_manager:
                await self.initialize()
            
            # Connect to server using server manager
            success = await self.server_manager.connect_server(server_name)
            if not success:
                return False
            
            # Get server configuration
            server_config = self.server_manager.servers.get(server_name)
            if not server_config:
                return False
            
            # Create API config bound to mandated tunnel (127.0.0.1:8090)
            api_config = APIConfig(
                host="127.0.0.1",
                port=8090,
                email=self.settings.api.email,
                password=self.settings.api.password,
                timeout=self.settings.api.timeout,
                max_retries=self.settings.api.max_retries,
                retry_delay=self.settings.api.retry_delay,
                retry_backoff_factor=self.settings.api.retry_backoff_factor,
            )
            # Create client and auth manager
            client = AsyncHaasClient(api_config)
            auth_manager = AuthenticationManager(client, api_config)
            
            # Authenticate
            await auth_manager.authenticate()
            
            # Initialize API modules for this server
            self.api_modules[server_name] = {
                "client": client,
                "auth_manager": auth_manager,
                "lab_api": LabAPI(client, auth_manager),
                "bot_api": BotAPI(client, auth_manager),
                "account_api": AccountAPI(client, auth_manager),
                "script_api": ScriptAPI(client, auth_manager),
                "market_api": MarketAPI(client, auth_manager),
                "backtest_api": BacktestAPI(client, auth_manager),
                "order_api": OrderAPI(client, auth_manager),
                "lab_service": LabService(LabAPI(client, auth_manager), BacktestAPI(client, auth_manager), client, auth_manager),
                "bot_service": BotService(BotAPI(client, auth_manager), AccountAPI(client, auth_manager), BacktestAPI(client, auth_manager), MarketAPI(client, auth_manager), client, auth_manager),
                "analysis_service": AnalysisService(LabAPI(client, auth_manager), BacktestAPI(client, auth_manager), BotAPI(client, auth_manager), client, auth_manager),
                "reporting_service": ReportingService(client, auth_manager)
            }
            
            self.active_server = server_name
            logger.info(f"Successfully connected to {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            return False
    
    def get_current_api(self, api_type: str):
        """Get the current API module for the active server"""
        if not self.active_server or self.active_server not in self.api_modules:
            raise Exception(f"No active server connection. Available servers: {list(self.api_modules.keys())}")
        
        return self.api_modules[self.active_server][api_type]
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.server_manager:
            await self.server_manager.disconnect_all()
        if self.data_manager:
            await self.data_manager.cleanup()
        self.connected = False

# Global server instance
cursor_mcp_server_instance = CursorPyHaasAPIMCPServer()

# MCP Tool Definitions
def define_tools() -> List[Tool]:
    """Define all MCP tools for pyHaasAPI functionality"""
    return [
        # Server Management
        Tool(
            name="connect_to_server",
            description="Connect to a specific HaasOnline server (srv01, srv02, srv03)",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "enum": ["srv01", "srv02", "srv03"]}
                },
                "required": ["server_name"]
            }
        ),
        Tool(
            name="list_available_servers",
            description="List all available servers and their status",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_server_status",
            description="Get the status of a specific server",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_name": {"type": "string"}
                },
                "required": ["server_name"]
            }
        ),
        
        # Lab Management
        Tool(
            name="list_labs",
            description="List all available labs from the current server",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_lab_details",
            description="Get detailed information about a specific lab",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"}
                },
                "required": ["lab_id"]
            }
        ),
        Tool(
            name="create_lab",
            description="Create a new lab for backtesting",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "script_id": {"type": "string"},
                    "account_id": {"type": "string"},
                    "market": {"type": "string"},
                    "parameters": {"type": "object"}
                },
                "required": ["name", "script_id", "account_id", "market"]
            }
        ),
        Tool(
            name="start_lab_execution",
            description="Start lab backtesting execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"},
                    "max_iterations": {"type": "integer", "default": 1500}
                },
                "required": ["lab_id"]
            }
        ),
        Tool(
            name="get_lab_execution_status",
            description="Get the current status of lab execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"}
                },
                "required": ["lab_id"]
            }
        ),
        
        # Bot Management
        Tool(
            name="list_bots",
            description="List all trading bots from the current server",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_bot_details",
            description="Get detailed information about a specific bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {"type": "string"}
                },
                "required": ["bot_id"]
            }
        ),
        Tool(
            name="create_bot",
            description="Create a new trading bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "script_id": {"type": "string"},
                    "account_id": {"type": "string"},
                    "market": {"type": "string"},
                    "leverage": {"type": "number", "default": 20.0},
                    "trade_amount": {"type": "number", "default": 2000.0}
                },
                "required": ["name", "script_id", "account_id", "market"]
            }
        ),
        Tool(
            name="activate_bot",
            description="Activate a bot for live trading",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {"type": "string"}
                },
                "required": ["bot_id"]
            }
        ),
        Tool(
            name="deactivate_bot",
            description="Deactivate a bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {"type": "string"}
                },
                "required": ["bot_id"]
            }
        ),
        
        # Analysis & Optimization
        Tool(
            name="analyze_lab",
            description="Analyze lab performance and get top backtests",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"},
                    "top_count": {"type": "integer", "default": 10},
                    "min_win_rate": {"type": "number", "default": 0.3},
                    "min_trades": {"type": "integer", "default": 5}
                },
                "required": ["lab_id"]
            }
        ),
        Tool(
            name="create_bots_from_analysis",
            description="Create bots from lab analysis results",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"},
                    "count": {"type": "integer", "default": 3},
                    "activate": {"type": "boolean", "default": False}
                },
                "required": ["lab_id"]
            }
        ),
        Tool(
            name="run_wfo_analysis",
            description="Run Walk Forward Optimization analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "training_days": {"type": "integer", "default": 365},
                    "testing_days": {"type": "integer", "default": 90}
                },
                "required": ["lab_id", "start_date", "end_date"]
            }
        ),
        
        # Account Management
        Tool(
            name="list_accounts",
            description="List all trading accounts from the current server",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_account_balance",
            description="Get account balance information",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string"}
                },
                "required": ["account_id"]
            }
        ),
        Tool(
            name="configure_account",
            description="Configure account settings (leverage, margin mode, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string"},
                    "leverage": {"type": "number"},
                    "margin_mode": {"type": "string"},
                    "position_mode": {"type": "string"}
                },
                "required": ["account_id"]
            }
        ),
        
        # Market Data
        Tool(
            name="get_markets",
            description="Get available trading markets from the current server",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_price_data",
            description="Get real-time price data for a market",
            inputSchema={
                "type": "object",
                "properties": {
                    "market": {"type": "string"}
                },
                "required": ["market"]
            }
        ),
        Tool(
            name="get_historical_data",
            description="Get historical price data",
            inputSchema={
                "type": "object",
                "properties": {
                    "market": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "interval": {"type": "string", "default": "1h"}
                },
                "required": ["market", "start_date", "end_date"]
            }
        ),
        
        # Script Management
        Tool(
            name="list_scripts",
            description="List all available trading scripts from the current server",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_script_details",
            description="Get detailed information about a script",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {"type": "string"}
                },
                "required": ["script_id"]
            }
        ),
        
        # Backtest Management
        Tool(
            name="get_lab_backtests",
            description="Get all backtests for a lab",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"}
                },
                "required": ["lab_id"]
            }
        ),
        Tool(
            name="get_backtest_results",
            description="Get detailed backtest results",
            inputSchema={
                "type": "object",
                "properties": {
                    "backtest_id": {"type": "string"}
                },
                "required": ["backtest_id"]
            }
        ),
        Tool(
            name="run_longest_backtest",
            description="Run the longest possible backtest for a lab",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"},
                    "max_iterations": {"type": "integer", "default": 1500}
                },
                "required": ["lab_id"]
            }
        ),
        
        # Order Management
        Tool(
            name="get_bot_orders",
            description="Get orders for a specific bot",
            inputSchema={
                "type": "object",
                "properties": {
                    "bot_id": {"type": "string"}
                },
                "required": ["bot_id"]
            }
        ),
        Tool(
            name="place_order",
            description="Place a new order",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_id": {"type": "string"},
                    "market": {"type": "string"},
                    "side": {"type": "string"},
                    "amount": {"type": "number"},
                    "price": {"type": "number"}
                },
                "required": ["account_id", "market", "side", "amount"]
            }
        ),
        Tool(
            name="cancel_order",
            description="Cancel an existing order",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"}
                },
                "required": ["order_id"]
            }
        ),
        
        # Reporting & Analytics
        Tool(
            name="generate_analysis_report",
            description="Generate comprehensive analysis report",
            inputSchema={
                "type": "object",
                "properties": {
                    "lab_id": {"type": "string"},
                    "format": {"type": "string", "default": "json"},
                    "include_charts": {"type": "boolean", "default": False}
                },
                "required": ["lab_id"]
            }
        ),
        Tool(
            name="get_performance_metrics",
            description="Get performance metrics for bots or labs",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_type": {"type": "string", "enum": ["lab", "bot"]},
                    "entity_id": {"type": "string"},
                    "timeframe": {"type": "string", "default": "all"}
                },
                "required": ["entity_type", "entity_id"]
            }
        ),
        
        # Mass Operations
        Tool(
            name="mass_bot_creation",
            description="Create bots from all qualifying labs on the current server",
            inputSchema={
                "type": "object",
                "properties": {
                    "top_count": {"type": "integer", "default": 5},
                    "min_win_rate": {"type": "number", "default": 0.3},
                    "min_trades": {"type": "integer", "default": 5},
                    "activate": {"type": "boolean", "default": False}
                }
            }
        ),
        Tool(
            name="analyze_all_labs",
            description="Analyze all labs on the current server and generate reports",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_win_rate": {"type": "number", "default": 0.3},
                    "min_trades": {"type": "integer", "default": 5},
                    "generate_reports": {"type": "boolean", "default": True}
                }
            }
        ),
        
        # Google Sheets Integration
        Tool(
            name="publish_to_google_sheets",
            description="Publish pyHaasAPI data to Google Sheets for all servers",
            inputSchema={
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "string"},
                    "credentials_path": {"type": "string", "default": "gdocs/google_credentials.json"},
                    "server_configs": {
                        "type": "object",
                        "default": {
                            "srv01": {"host": "127.0.0.1", "port": 8090},
                            "srv02": {"host": "127.0.0.1", "port": 8091},
                            "srv03": {"host": "127.0.0.1", "port": 8092}
                        }
                    }
                },
                "required": ["sheet_id"]
            }
        ),
        Tool(
            name="update_google_sheets_server",
            description="Update Google Sheets with data from a specific server",
            inputSchema={
                "type": "object",
                "properties": {
                    "sheet_id": {"type": "string"},
                    "server_name": {"type": "string"},
                    "credentials_path": {"type": "string", "default": "gdocs/google_credentials.json"}
                },
                "required": ["sheet_id", "server_name"]
            }
        )
    ]

# Register MCP tools
@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools"""
    return define_tools()

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle MCP tool calls"""
    try:
        if not cursor_mcp_server_instance.connected:
            await cursor_mcp_server_instance.initialize()
        
        # Route tool calls to appropriate handlers
        if name == "connect_to_server":
            return await handle_connect_to_server(arguments)
        elif name == "list_available_servers":
            return await handle_list_available_servers()
        elif name == "get_server_status":
            return await handle_get_server_status(arguments)
        elif name == "list_labs":
            return await handle_list_labs()
        elif name == "get_lab_details":
            return await handle_get_lab_details(arguments)
        elif name == "create_lab":
            return await handle_create_lab(arguments)
        elif name == "start_lab_execution":
            return await handle_start_lab_execution(arguments)
        elif name == "get_lab_execution_status":
            return await handle_get_lab_execution_status(arguments)
        elif name == "list_bots":
            return await handle_list_bots()
        elif name == "get_bot_details":
            return await handle_get_bot_details(arguments)
        elif name == "create_bot":
            return await handle_create_bot(arguments)
        elif name == "activate_bot":
            return await handle_activate_bot(arguments)
        elif name == "deactivate_bot":
            return await handle_deactivate_bot(arguments)
        elif name == "analyze_lab":
            return await handle_analyze_lab(arguments)
        elif name == "create_bots_from_analysis":
            return await handle_create_bots_from_analysis(arguments)
        elif name == "run_wfo_analysis":
            return await handle_run_wfo_analysis(arguments)
        elif name == "list_accounts":
            return await handle_list_accounts()
        elif name == "get_account_balance":
            return await handle_get_account_balance(arguments)
        elif name == "configure_account":
            return await handle_configure_account(arguments)
        elif name == "get_markets":
            return await handle_get_markets()
        elif name == "get_price_data":
            return await handle_get_price_data(arguments)
        elif name == "get_historical_data":
            return await handle_get_historical_data(arguments)
        elif name == "list_scripts":
            return await handle_list_scripts()
        elif name == "get_script_details":
            return await handle_get_script_details(arguments)
        elif name == "get_lab_backtests":
            return await handle_get_lab_backtests(arguments)
        elif name == "get_backtest_results":
            return await handle_get_backtest_results(arguments)
        elif name == "run_longest_backtest":
            return await handle_run_longest_backtest(arguments)
        elif name == "get_bot_orders":
            return await handle_get_bot_orders(arguments)
        elif name == "place_order":
            return await handle_place_order(arguments)
        elif name == "cancel_order":
            return await handle_cancel_order(arguments)
        elif name == "generate_analysis_report":
            return await handle_generate_analysis_report(arguments)
        elif name == "get_performance_metrics":
            return await handle_get_performance_metrics(arguments)
        elif name == "mass_bot_creation":
            return await handle_mass_bot_creation(arguments)
        elif name == "analyze_all_labs":
            return await handle_analyze_all_labs(arguments)
        elif name == "publish_to_google_sheets":
            return await handle_publish_to_google_sheets(arguments)
        elif name == "update_google_sheets_server":
            return await handle_update_google_sheets_server(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error in tool call {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

# Tool handlers
async def handle_connect_to_server(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle connect_to_server tool"""
    server_name = arguments["server_name"]
    
    try:
        success = await cursor_mcp_server_instance.connect_to_server(server_name)
        if success:
            return [TextContent(type="text", text=f"Successfully connected to {server_name}")]
        else:
            return [TextContent(type="text", text=f"Failed to connect to {server_name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error connecting to {server_name}: {str(e)}")]

async def handle_list_available_servers() -> List[TextContent]:
    """Handle list_available_servers tool"""
    try:
        if not cursor_mcp_server_instance.server_manager:
            return [TextContent(type="text", text="Server manager not initialized")]
        
        servers_info = []
        for server_name, status in cursor_mcp_server_instance.server_manager.servers.items():
            servers_info.append({
                "name": server_name,
                "status": status.status.value,
                "connected": status.status.value == "connected",
                "last_error": status.last_error
            })
        
        return [TextContent(type="text", text=json.dumps(servers_info, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing servers: {str(e)}")]

async def handle_get_server_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle get_server_status tool"""
    server_name = arguments["server_name"]
    
    try:
        if not cursor_mcp_server_instance.server_manager:
            return [TextContent(type="text", text="Server manager not initialized")]
        
        if server_name not in cursor_mcp_server_instance.server_manager.servers:
            return [TextContent(type="text", text=f"Server {server_name} not found")]
        
        status = cursor_mcp_server_instance.server_manager.servers[server_name]
        status_info = {
            "name": server_name,
            "status": status.status.value,
            "connected": status.status.value == "connected",
            "last_error": status.last_error,
            "reconnect_attempts": status.reconnect_attempts
        }
        
        return [TextContent(type="text", text=json.dumps(status_info, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error getting server status: {str(e)}")]

# Import handlers
from .cursor_mcp_handlers import *

if __name__ == "__main__":
    # Run the MCP server
    asyncio.run(stdio_server(server))
