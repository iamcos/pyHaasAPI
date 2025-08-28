#!/usr/bin/env python3
"""
MCP Server for HaasOnline API Integration
This implements the Model Context Protocol to expose HaasOnline API functionality.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env'))

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel
    )
    import mcp.types as types
except ImportError:
    print("MCP library not found. Please install it with: pip install mcp")
    sys.exit(1)

# Import pyHaasAPI components
try:
    from pyHaasAPI import api
    from pyHaasAPI.model import CreateLabRequest, CloudMarket, UserAccount, AccountData, LabDetails
    from pyHaasAPI.exceptions import HaasApiError
    from pyHaasAPI.enhanced_execution import get_enhanced_executor
    from pyHaasAPI.history_intelligence import get_history_service
except ImportError as e:
    print(f"pyHaasAPI not found: {e}")
    api = None
    CreateLabRequest = None
    CloudMarket = None
    HaasApiError = Exception
    get_enhanced_executor = None
    get_history_service = None

# Import our enhanced authentication manager
try:
    from auth_manager import get_auth_manager, get_authenticated_executor
except ImportError as e:
    print(f"Auth manager not found: {e}")
    get_auth_manager = None
    get_authenticated_executor = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("haas-mcp-server")

class HaasMCPServer:
    def __init__(self):
        self.server = Server("haas-api-server")
        self.haas_executor = None
        self._initialize_haas_api()
        self._register_handlers()
    
    def _serialize_object(self, obj):
        """Convert complex objects to JSON-serializable dictionaries"""
        if hasattr(obj, '__dict__'):
            # For objects with __dict__, convert to dictionary
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):  # Skip private attributes
                    try:
                        json.dumps(value)  # Test if value is JSON serializable
                        result[key] = value
                    except (TypeError, ValueError):
                        result[key] = str(value)  # Convert to string if not serializable
            return result
        elif hasattr(obj, '_asdict'):
            # For namedtuples
            return obj._asdict()
        else:
            # For other objects, try to extract common attributes
            result = {}
            common_attrs = ['id', 'name', 'script_id', 'account_id', 'lab_id', 'bot_id', 'market', 'status', 'created', 'modified']
            for attr in common_attrs:
                if hasattr(obj, attr):
                    value = getattr(obj, attr)
                    try:
                        json.dumps(value)
                        result[attr] = value
                    except (TypeError, ValueError):
                        result[attr] = str(value)
            return result if result else str(obj)

    def _initialize_haas_api(self):
        """Initialize HaasOnline API connection using enhanced authentication manager"""
        if api is None:
            logger.error("pyHaasAPI not available")
            self.haas_executor = None
            return

        # Check if auth manager is available
        if not get_auth_manager or not get_authenticated_executor:
            logger.warning("Auth manager not available, falling back to basic authentication")
            self._fallback_authentication()
            return

        try:
            logger.info("Initializing HaasOnline API connection with enhanced authentication...")
            
            # Use the authentication manager to get a working executor
            auth_manager = get_auth_manager()
            auth_result = auth_manager.authenticate()
            
            if auth_result.success:
                self.haas_executor = auth_result.executor
                self.auth_manager = auth_manager
                
                logger.info(f"✅ Successfully authenticated with {auth_result.credential_set.name} credentials")
                logger.info(f"Connected to: {auth_result.server_info.get('host')}:{auth_result.server_info.get('port')}")
                logger.info(f"Account: {auth_result.server_info.get('account_name', 'Unknown')}")
                
                return
            else:
                logger.error(f"❌ Authentication failed: {auth_result.error_message}")
                self.haas_executor = None
                
        except Exception as e:
            logger.error(f"Exception during enhanced authentication: {e}")
            self.haas_executor = None

    def _fallback_authentication(self):
        """Fallback authentication method (original implementation)"""
        try:
            api_host = os.getenv("API_HOST", "127.0.0.1")
            api_port = int(os.getenv("API_PORT", 8090))
            
            # Try local credentials first, then fall back to regular credentials
            api_email = os.getenv("API_EMAIL_LOCAL") or os.getenv("API_EMAIL")
            api_password = os.getenv("API_PASSWORD_LOCAL") or os.getenv("API_PASSWORD")

            if not api_email or not api_password:
                logger.error("No API credentials found in environment")
                self.haas_executor = None
                return

            logger.info(f"Authenticating with HaasOnline API: {api_host}:{api_port} using email: {api_email}")

            self.haas_executor = api.RequestsExecutor(
                host=api_host,
                port=api_port,
                state=api.Guest()
            ).authenticate(
                email=api_email,
                password=api_password
            )
            logger.info("Successfully authenticated with HaasOnline API")
        except Exception as e:
            logger.error(f"Failed to authenticate with HaasOnline API: {e}")
            # Try with regular credentials if local failed
            if os.getenv("API_EMAIL_LOCAL"):
                try:
                    logger.info("Retrying with regular credentials...")
                    api_email = os.getenv("API_EMAIL")
                    api_password = os.getenv("API_PASSWORD")
                    if api_email and api_password:
                        self.haas_executor = api.RequestsExecutor(
                            host=api_host,
                            port=api_port,
                            state=api.Guest()
                        ).authenticate(
                            email=api_email,
                            password=api_password
                        )
                        logger.info("Successfully authenticated with regular credentials")
                    else:
                        self.haas_executor = None
                except Exception as e2:
                    logger.error(f"Failed with regular credentials too: {e2}")
                    self.haas_executor = None
            else:
                self.haas_executor = None
    
    def _register_handlers(self):
        """Register all MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_haas_status",
                    description="Check the status of the HaasOnline API connection",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_auth_status",
                    description="Get detailed authentication status and credential information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="refresh_authentication",
                    description="Force refresh of authentication using all available credential sets",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_all_accounts",
                    description="Get all user accounts from HaasOnline",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="create_simulated_account",
                    description="Create a new simulated account in HaasOnline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_name": {"type": "string", "description": "Name for the new account"},
                            "driver_code": {"type": "string", "description": "Driver code (e.g., BINANCE)"},
                            "driver_type": {"type": "integer", "description": "Driver type (usually 0)"}
                        },
                        "required": ["account_name", "driver_code", "driver_type"]
                    }
                ),
                Tool(
                    name="get_all_labs",
                    description="Get all labs from HaasOnline",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="create_lab",
                    description="Create a new lab in HaasOnline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to use"},
                            "account_id": {"type": "string", "description": "ID of the account to use"},
                            "market_category": {"type": "string", "default": "SPOT", "description": "Market category"},
                            "market_price_source": {"type": "string", "default": "BINANCE", "description": "Price source"},
                            "market_primary": {"type": "string", "default": "BTC", "description": "Primary currency"},
                            "market_secondary": {"type": "string", "default": "USDT", "description": "Secondary currency"},
                            "exchange_code": {"type": "string", "default": "BINANCE", "description": "Exchange code"},
                            "interval": {"type": "integer", "default": 1, "description": "Interval"},
                            "default_price_data_style": {"type": "string", "default": "CandleStick", "description": "Price data style"}
                        },
                        "required": ["script_id", "account_id"]
                    }
                ),
                Tool(
                    name="clone_lab",
                    description="Clone an existing lab",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab to clone"},
                            "new_name": {"type": "string", "description": "Name for the cloned lab (optional)"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="delete_lab",
                    description="Delete a lab by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab to delete"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="backtest_lab",
                    description="Start a backtest for a lab",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab to backtest"},
                            "start_unix": {"type": "integer", "description": "Start time as Unix timestamp"},
                            "end_unix": {"type": "integer", "description": "End time as Unix timestamp"},
                            "send_email": {"type": "boolean", "default": False, "description": "Send email when complete"}
                        },
                        "required": ["lab_id", "start_unix", "end_unix"]
                    }
                ),
                Tool(
                    name="get_backtest_results",
                    description="Get backtest results for a lab",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab"},
                            "next_page_id": {"type": "integer", "default": -1, "description": "Next page ID"},
                            "page_length": {"type": "integer", "default": 100, "description": "Page length"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="get_all_markets",
                    description="Get all available markets",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="add_script",
                    description="Add a new script to HaasOnline",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_name": {"type": "string", "description": "Name of the script"},
                            "script_content": {"type": "string", "description": "Content of the script"},
                            "description": {"type": "string", "default": "", "description": "Script description"},
                            "script_type": {"type": "integer", "default": 0, "description": "Script type"}
                        },
                        "required": ["script_name", "script_content"]
                    }
                ),
                Tool(
                    name="deposit_funds",
                    description="Deposit funds to an account",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"},
                            "currency": {"type": "string", "description": "Currency code"},
                            "wallet_id": {"type": "string", "description": "Wallet ID"},
                            "amount": {"type": "number", "description": "Amount to deposit"}
                        },
                        "required": ["account_id", "currency", "wallet_id", "amount"]
                    }
                ),
                Tool(
                    name="withdraw_funds",
                    description="Withdraw funds from an account",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"},
                            "currency": {"type": "string", "description": "Currency code"},
                            "wallet_id": {"type": "string", "description": "Wallet ID"},
                            "amount": {"type": "number", "description": "Amount to withdraw"}
                        },
                        "required": ["account_id", "currency", "wallet_id", "amount"]
                    }
                ),
                Tool(
                    name="get_account_balance",
                    description="Get account balance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"}
                        },
                        "required": ["account_id"]
                    }
                ),
                Tool(
                    name="discover_cutoff_date",
                    description="Discover the cutoff date for a lab's market (earliest date with historical data)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID to discover cutoff for"},
                            "force_rediscover": {"type": "boolean", "default": False, "description": "Force rediscovery even if already known"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="validate_backtest_period",
                    description="Validate if a backtest period is valid for a lab's market",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID to validate period for"},
                            "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DDTHH:MM:SS)"},
                            "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DDTHH:MM:SS)"}
                        },
                        "required": ["lab_id", "start_date", "end_date"]
                    }
                ),
                Tool(
                    name="execute_backtest_intelligent",
                    description="Execute backtest with automatic history intelligence validation and adjustment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID to execute backtest for"},
                            "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DDTHH:MM:SS)"},
                            "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DDTHH:MM:SS)"},
                            "send_email": {"type": "boolean", "default": False, "description": "Send email notification when complete"},
                            "auto_adjust": {"type": "boolean", "default": True, "description": "Automatically adjust periods if needed"}
                        },
                        "required": ["lab_id", "start_date", "end_date"]
                    }
                ),
                Tool(
                    name="get_history_summary",
                    description="Get summary of all known cutoff dates and history intelligence data",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="bulk_discover_cutoffs",
                    description="Discover cutoff dates for multiple labs in bulk",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_ids": {"type": "array", "items": {"type": "string"}, "description": "List of lab IDs to discover cutoffs for"}
                        },
                        "required": ["lab_ids"]
                    }
                ),
                # Lab Management Tools
                Tool(
                    name="get_lab_details",
                    description="Get detailed information about a specific lab",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab to get details for"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="update_lab_details",
                    description="Update lab details and settings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab to update"},
                            "name": {"type": "string", "description": "New name for the lab (optional)"},
                            "settings": {"type": "object", "description": "Lab settings to update (optional)"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="change_lab_script",
                    description="Change the script associated with a lab",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab"},
                            "script_id": {"type": "string", "description": "ID of the new script"}
                        },
                        "required": ["lab_id", "script_id"]
                    }
                ),
                Tool(
                    name="cancel_lab_execution",
                    description="Cancel a running lab execution/backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab to cancel"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="get_lab_execution_update",
                    description="Get execution status update for a lab",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="update_lab_parameter_ranges",
                    description="Set optimal parameter ranges for a lab to improve backtesting",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab to optimize"},
                            "randomize": {"type": "boolean", "default": True, "description": "Whether to randomize parameter ranges"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                # Bot Management Tools
                Tool(
                    name="get_all_bots",
                    description="Get all trading bots",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_bot_details",
                    description="Get detailed information about a specific bot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "ID of the bot"}
                        },
                        "required": ["bot_id"]
                    }
                ),
                Tool(
                    name="create_bot_from_lab",
                    description="Create a trading bot from a lab's backtest results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "ID of the lab"},
                            "backtest_id": {"type": "string", "description": "ID of the backtest"},
                            "bot_name": {"type": "string", "description": "Name for the new bot"},
                            "account_id": {"type": "string", "description": "Account ID for the bot"},
                            "market": {"type": "string", "description": "Market for the bot"},
                            "leverage": {"type": "integer", "default": 0, "description": "Leverage setting"}
                        },
                        "required": ["lab_id", "backtest_id", "bot_name", "account_id", "market"]
                    }
                ),
                Tool(
                    name="activate_bot",
                    description="Activate a bot to start trading",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "ID of the bot to activate"},
                            "clean_reports": {"type": "boolean", "default": False, "description": "Clean previous reports"}
                        },
                        "required": ["bot_id"]
                    }
                ),
                Tool(
                    name="deactivate_bot",
                    description="Deactivate a bot to stop trading",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "ID of the bot to deactivate"},
                            "cancel_orders": {"type": "boolean", "default": False, "description": "Cancel open orders"}
                        },
                        "required": ["bot_id"]
                    }
                ),
                Tool(
                    name="pause_bot",
                    description="Pause a bot temporarily",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "ID of the bot to pause"}
                        },
                        "required": ["bot_id"]
                    }
                ),
                Tool(
                    name="resume_bot",
                    description="Resume a paused bot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "ID of the bot to resume"}
                        },
                        "required": ["bot_id"]
                    }
                ),
                Tool(
                    name="delete_bot",
                    description="Delete a trading bot",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "bot_id": {"type": "string", "description": "ID of the bot to delete"}
                        },
                        "required": ["bot_id"]
                    }
                ),
                Tool(
                    name="deactivate_all_bots",
                    description="Deactivate all trading bots",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                # Script Management Tools
                Tool(
                    name="get_all_scripts",
                    description="Get all available scripts",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_script_details",
                    description="Get detailed information about a specific script",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script"}
                        },
                        "required": ["script_id"]
                    }
                ),
                Tool(
                    name="edit_script",
                    description="Edit an existing script",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to edit"},
                            "script_name": {"type": "string", "description": "New name for the script (optional)"},
                            "script_content": {"type": "string", "description": "New content for the script (optional)"},
                            "description": {"type": "string", "description": "New description (optional)"}
                        },
                        "required": ["script_id"]
                    }
                ),
                Tool(
                    name="delete_script",
                    description="Delete a script",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to delete"}
                        },
                        "required": ["script_id"]
                    }
                ),
                Tool(
                    name="get_scripts_by_name",
                    description="Search for scripts by name pattern",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name_pattern": {"type": "string", "description": "Name pattern to search for"}
                        },
                        "required": ["name_pattern"]
                    }
                ),
                Tool(
                    name="save_script",
                    description="Save a HaasScript's source code to the server and get validation results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to save"},
                            "source_code": {"type": "string", "description": "The HaasScript source code to save"},
                            "settings": {
                                "type": "object", 
                                "description": "Optional script settings (account, market, etc.)",
                                "properties": {
                                    "accountId": {"type": "string", "description": "Account ID"},
                                    "marketTag": {"type": "string", "description": "Market tag (e.g., BINANCE_BTC_USDT_)"},
                                    "leverage": {"type": "integer", "description": "Leverage setting"},
                                    "positionMode": {"type": "integer", "description": "Position mode"},
                                    "marginMode": {"type": "integer", "description": "Margin mode"},
                                    "tradeAmount": {"type": "number", "description": "Trade amount"},
                                    "orderTemplate": {"type": "integer", "description": "Order template"},
                                    "chartStyle": {"type": "integer", "description": "Chart style"},
                                    "interval": {"type": "integer", "description": "Interval"},
                                    "scriptParameters": {"type": "object", "description": "Script parameters"},
                                    "botName": {"type": "string", "description": "Bot name"},
                                    "botId": {"type": "string", "description": "Bot ID"}
                                }
                            }
                        },
                        "required": ["script_id", "source_code"]
                    }
                ),
                Tool(
                    name="validate_script",
                    description="Validate a HaasScript by saving it and getting validation feedback",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to validate"},
                            "source_code": {"type": "string", "description": "The HaasScript source code to validate"},
                            "settings": {
                                "type": "object", 
                                "description": "Optional script settings (account, market, etc.)",
                                "properties": {
                                    "accountId": {"type": "string", "description": "Account ID"},
                                    "marketTag": {"type": "string", "description": "Market tag (e.g., BINANCE_BTC_USDT_)"},
                                    "leverage": {"type": "integer", "description": "Leverage setting"},
                                    "positionMode": {"type": "integer", "description": "Position mode"},
                                    "marginMode": {"type": "integer", "description": "Margin mode"},
                                    "tradeAmount": {"type": "number", "description": "Trade amount"},
                                    "orderTemplate": {"type": "integer", "description": "Order template"},
                                    "chartStyle": {"type": "integer", "description": "Chart style"},
                                    "interval": {"type": "integer", "description": "Interval"},
                                    "scriptParameters": {"type": "object", "description": "Script parameters"},
                                    "botName": {"type": "string", "description": "Bot name"},
                                    "botId": {"type": "string", "description": "Bot ID"}
                                }
                            }
                        },
                        "required": ["script_id", "source_code"]
                    }
                ),
                Tool(
                    name="compile_script",
                    description="[DEPRECATED] Compile/validate a HaasScript (use save_script instead)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to compile"},
                            "source_code": {"type": "string", "description": "The HaasScript source code to compile"},
                            "settings": {
                                "type": "object", 
                                "description": "Optional script settings (account, market, etc.)",
                                "properties": {
                                    "accountId": {"type": "string", "description": "Account ID"},
                                    "marketTag": {"type": "string", "description": "Market tag (e.g., BINANCE_BTC_USDT_)"},
                                    "leverage": {"type": "integer", "description": "Leverage setting"},
                                    "positionMode": {"type": "integer", "description": "Position mode"},
                                    "marginMode": {"type": "integer", "description": "Margin mode"},
                                    "tradeAmount": {"type": "number", "description": "Trade amount"},
                                    "orderTemplate": {"type": "integer", "description": "Order template"},
                                    "chartStyle": {"type": "integer", "description": "Chart style"},
                                    "interval": {"type": "integer", "description": "Interval"},
                                    "scriptParameters": {"type": "object", "description": "Script parameters"},
                                    "botName": {"type": "string", "description": "Bot name"},
                                    "botId": {"type": "string", "description": "Bot ID"}
                                }
                            }
                        },
                        "required": ["script_id", "source_code"]
                    }
                ),
                # Market Data Tools
                Tool(
                    name="get_market_price",
                    description="Get current price for a specific market",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "market": {"type": "string", "description": "Market identifier (e.g., 'BINANCE_BTC_USDT')"}
                        },
                        "required": ["market"]
                    }
                ),
                Tool(
                    name="get_order_book",
                    description="Get order book for a specific market",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "market": {"type": "string", "description": "Market identifier"},
                            "depth": {"type": "integer", "default": 20, "description": "Order book depth"}
                        },
                        "required": ["market"]
                    }
                ),
                Tool(
                    name="get_market_snapshot",
                    description="Get market snapshot with price, volume, and metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "market": {"type": "string", "description": "Market identifier"}
                        },
                        "required": ["market"]
                    }
                ),
                Tool(
                    name="get_last_trades",
                    description="Get recent trades for a specific market",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "market": {"type": "string", "description": "Market identifier"},
                            "limit": {"type": "integer", "default": 100, "description": "Number of trades to retrieve"}
                        },
                        "required": ["market"]
                    }
                ),
                # Account Management Tools (Extended)
                Tool(
                    name="get_account_data",
                    description="Get detailed account data including exchange information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"}
                        },
                        "required": ["account_id"]
                    }
                ),
                Tool(
                    name="get_all_account_balances",
                    description="Get balance information for all accounts",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_account_orders",
                    description="Get open orders for an account",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"}
                        },
                        "required": ["account_id"]
                    }
                ),
                Tool(
                    name="get_account_positions",
                    description="Get open positions for an account",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"}
                        },
                        "required": ["account_id"]
                    }
                ),
                Tool(
                    name="get_account_trades",
                    description="Get trade history for an account",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"}
                        },
                        "required": ["account_id"]
                    }
                ),
                Tool(
                    name="rename_account",
                    description="Rename an account",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "string", "description": "Account ID"},
                            "new_name": {"type": "string", "description": "New name for the account"}
                        },
                        "required": ["account_id", "new_name"]
                    }
                ),
                # Backtest Analysis Tools
                Tool(
                    name="get_backtest_runtime",
                    description="Get detailed runtime information for a specific backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID"},
                            "backtest_id": {"type": "string", "description": "Backtest ID"}
                        },
                        "required": ["lab_id", "backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_chart",
                    description="Get chart data for a specific backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID"},
                            "backtest_id": {"type": "string", "description": "Backtest ID"}
                        },
                        "required": ["lab_id", "backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_log",
                    description="Get execution log for a specific backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID"},
                            "backtest_id": {"type": "string", "description": "Backtest ID"}
                        },
                        "required": ["lab_id", "backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_execution_update",
                    description="Get real-time execution status update for a specific backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID"},
                            "backtest_id": {"type": "string", "description": "Backtest ID"}
                        },
                        "required": ["lab_id", "backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_chart_partition",
                    description="Get chart data partition for a specific backtest (useful for large datasets)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID"},
                            "backtest_id": {"type": "string", "description": "Backtest ID"},
                            "partition_index": {"type": "integer", "default": 0, "description": "Index of the partition to retrieve"}
                        },
                        "required": ["lab_id", "backtest_id"]
                    }
                ),
                Tool(
                    name="cancel_backtest",
                    description="Cancel a running backtest execution",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_id": {"type": "string", "description": "Service ID (e.g., LocalService-ENT)"},
                            "backtest_id": {"type": "string", "description": "Backtest ID to cancel"}
                        },
                        "required": ["service_id", "backtest_id"]
                    }
                ),
                Tool(
                    name="execute_backtest",
                    description="Execute a backtest with specified parameters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to backtest"},
                            "start_date": {"type": "string", "description": "Start date for backtest"},
                            "end_date": {"type": "string", "description": "End date for backtest"},
                            "additional_params": {"type": "object", "description": "Additional backtest parameters"}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="share_script",
                    description="Share/publish a HaasScript to make it available to other users",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to share"},
                            "script_name": {"type": "string", "description": "Display name for the shared script"},
                            "script_description": {"type": "string", "default": "", "description": "Description of what the script does"},
                            "status": {"type": "integer", "default": 0, "description": "Sharing status (0 = public)"},
                            "allowed_users": {"type": "string", "default": "", "description": "Comma-separated list of allowed user IDs"}
                        },
                        "required": ["script_id", "script_name"]
                    }
                ),
                # New Script Manipulation Tools
                Tool(
                    name="edit_script_sourcecode",
                    description="Edit and save HaasScript source code with real-time validation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to edit"},
                            "source_code": {"type": "string", "description": "New source code for the script"}
                        },
                        "required": ["script_id", "source_code"]
                    }
                ),
                Tool(
                    name="check_script_execution_status",
                    description="Check if a script is currently executing/compiling",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to check"}
                        },
                        "required": ["script_id"]
                    }
                ),
                # New Backtest Management Tools
                Tool(
                    name="execute_quicktest",
                    description="Execute a quick test/validation of a script",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to test"},
                            "account_id": {"type": "string", "description": "Account ID for the test"},
                            "market_tag": {"type": "string", "description": "Market tag (e.g., BINANCE_BTC_USDT_)"}
                        },
                        "required": ["script_id", "account_id", "market_tag"]
                    }
                ),
                Tool(
                    name="execute_backtest_advanced",
                    description="Execute a full backtest with advanced options",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "ID of the script to backtest"},
                            "account_id": {"type": "string", "description": "Account ID for the backtest"},
                            "market_tag": {"type": "string", "description": "Market tag (e.g., BINANCE_BTC_USDT_)"},
                            "start_unix": {"type": "integer", "description": "Start time as Unix timestamp"},
                            "end_unix": {"type": "integer", "description": "End time as Unix timestamp"},
                            "send_email": {"type": "boolean", "default": False, "description": "Send email when complete"},
                            "additional_params": {"type": "object", "description": "Additional backtest parameters"}
                        },
                        "required": ["script_id", "account_id", "market_tag", "start_unix", "end_unix"]
                    }
                ),
                Tool(
                    name="get_execution_update",
                    description="Get real-time execution status update for any running process",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "process_id": {"type": "string", "description": "Process/execution ID to check"}
                        },
                        "required": ["process_id"]
                    }
                ),
                Tool(
                    name="get_backtest_runtime",
                    description="Get runtime information for a completed backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_logs",
                    description="Get execution logs for a backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_chart_partition_advanced",
                    description="Get chart data partition with indicator data for backtests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"},
                            "partition_index": {"type": "integer", "default": 0, "description": "Partition index"},
                            "include_market_data": {"type": "boolean", "default": False, "description": "Include market data (large)"},
                            "indicators_only": {"type": "boolean", "default": True, "description": "Return only indicator data"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="archive_backtest",
                    description="Archive a backtest to preserve it beyond 48 hours",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID to archive"},
                            "archive_result": {"type": "boolean", "default": True, "description": "Archive the result"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_positions",
                    description="Get position data for a backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"},
                            "next_page_id": {"type": "integer", "default": 0, "description": "Next page ID for pagination"},
                            "page_length": {"type": "integer", "default": 50, "description": "Number of positions per page"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_info",
                    description="Get comprehensive information about a backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_history",
                    description="Get backtest history for a script or all backtests",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to filter backtests (optional)"},
                            "limit": {"type": "integer", "default": 50, "description": "Maximum number of backtests to return"},
                            "offset": {"type": "integer", "default": 0, "description": "Offset for pagination"}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_backtest_object",
                    description="Get a comprehensive backtest object with all data (runtime, positions, info) but excluding heavy chart data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"},
                            "include_chart_data": {"type": "boolean", "default": False, "description": "Include heavy chart partition data"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="test_concurrent_backtests",
                    description="Test running multiple concurrent backtests to determine limits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to test with (default: a46d0d561ebe4e48bd7a1500ea6e1d60)"},
                            "account_id": {"type": "string", "description": "Account ID for testing"},
                            "market_tag": {"type": "string", "default": "BINANCE_BTC_USDT_", "description": "Market tag for testing"},
                            "concurrent_count": {"type": "integer", "default": 3, "description": "Number of concurrent backtests to attempt"}
                        },
                        "required": ["account_id"]
                    }
                ),
                # Enhanced Execution Tools
                Tool(
                    name="execute_backtest_with_intelligence",
                    description="Execute backtest with integrated history intelligence and automatic validation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID to execute backtest for"},
                            "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DDTHH:MM:SS)"},
                            "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DDTHH:MM:SS)"},
                            "send_email": {"type": "boolean", "default": False, "description": "Send email notification when complete"},
                            "auto_adjust": {"type": "boolean", "default": True, "description": "Automatically adjust periods if needed"}
                        },
                        "required": ["lab_id", "start_date", "end_date"]
                    }
                ),
                # Parameter Optimization Tools
                Tool(
                    name="optimize_lab_parameters_mixed",
                    description="Optimize lab parameters using mixed strategy (strategic values + intelligent ranges)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID to optimize"},
                            "max_combinations": {"type": "integer", "default": 50000, "description": "Maximum allowed parameter combinations"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                Tool(
                    name="optimize_lab_parameters_traditional",
                    description="Optimize lab parameters using traditional linear ranges (Min/Max/Step)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "lab_id": {"type": "string", "description": "Lab ID to optimize"},
                            "max_combinations": {"type": "integer", "default": 10000, "description": "Maximum allowed parameter combinations"}
                        },
                        "required": ["lab_id"]
                    }
                ),
                # Account Management Tools
                Tool(
                    name="create_test_accounts",
                    description="Create multiple test accounts with standardized naming",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "count": {"type": "integer", "default": 2, "description": "Number of test accounts to create"}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="find_test_accounts",
                    description="Find all test accounts in the system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_account_statistics",
                    description="Get comprehensive account statistics and breakdown",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                # Market Discovery Tools
                Tool(
                    name="discover_markets",
                    description="Discover and classify markets for a specific exchange",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "exchange": {"type": "string", "description": "Exchange name (e.g., BINANCEFUTURES)"},
                            "market_types": {"type": "array", "items": {"type": "string"}, "description": "Market types to discover (spot, perpetual, quarterly, monthly)"}
                        },
                        "required": ["exchange"]
                    }
                ),
                Tool(
                    name="discover_perpetual_markets",
                    description="Discover perpetual trading markets for a specific exchange",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "exchange": {"type": "string", "description": "Exchange name"}
                        },
                        "required": ["exchange"]
                    }
                ),
                Tool(
                    name="find_markets_by_asset",
                    description="Find all markets for a specific base asset across exchanges",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "base_asset": {"type": "string", "description": "Base asset symbol (e.g., BTC)"},
                            "exchanges": {"type": "array", "items": {"type": "string"}, "description": "List of exchanges to search"}
                        },
                        "required": ["base_asset"]
                    }
                ),
                Tool(
                    name="find_markets_by_symbol",
                    description="Find all markets for a specific trading symbol across exchanges",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading symbol (e.g., BTC/USDT)"},
                            "exchanges": {"type": "array", "items": {"type": "string"}, "description": "List of exchanges to search"}
                        },
                        "required": ["symbol"]
                    }
                ),
                # Lab Cloning Tools
                Tool(
                    name="clone_lab_for_assets",
                    description="Clone a lab for specific assets across exchanges",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "base_lab_id": {"type": "string", "description": "Base lab ID to clone from"},
                            "base_assets": {"type": "array", "items": {"type": "string"}, "description": "List of base assets (e.g., [BTC, ETH])"},
                            "account_id": {"type": "string", "description": "Account ID to use"},
                            "exchanges": {"type": "array", "items": {"type": "string"}, "description": "List of exchanges to use"},
                            "market_types": {"type": "array", "items": {"type": "string"}, "description": "Market types to include"}
                        },
                        "required": ["base_lab_id", "base_assets", "account_id"]
                    }
                ),
                Tool(
                    name="clone_lab_for_perpetual_markets",
                    description="Clone a lab for perpetual markets with default asset selection",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "base_lab_id": {"type": "string", "description": "Base lab ID to clone from"},
                            "account_id": {"type": "string", "description": "Account ID to use"},
                            "base_assets": {"type": "array", "items": {"type": "string"}, "description": "List of base assets (defaults to BTC, ETH, BNB, ADA, SOL)"},
                            "exchanges": {"type": "array", "items": {"type": "string"}, "description": "List of exchanges to use"}
                        },
                        "required": ["base_lab_id", "account_id"]
                    }
                ),
                # Script Management Tools (Extended)
                Tool(
                    name="get_haasscript_commands",
                    description="Get all available HaasScript commands and their descriptions",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_script_record",
                    description="Get complete script record including compile logs and all fields",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to retrieve"}
                        },
                        "required": ["script_id"]
                    }
                ),
                Tool(
                    name="edit_script_sourcecode",
                    description="Update script source code and settings (mimics WebEditor save)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to edit"},
                            "sourcecode": {"type": "string", "description": "New source code for the script"},
                            "settings": {"type": "object", "description": "Script settings dictionary"}
                        },
                        "required": ["script_id", "sourcecode", "settings"]
                    }
                ),
                Tool(
                    name="publish_script",
                    description="Publish a script to make it public",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to publish"}
                        },
                        "required": ["script_id"]
                    }
                ),
                Tool(
                    name="get_all_script_folders",
                    description="Get all script folders for organization",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="create_script_folder",
                    description="Create a new script folder for organization",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "foldername": {"type": "string", "description": "Name of the folder"},
                            "parentid": {"type": "integer", "default": -1, "description": "Parent folder ID (-1 for root)"}
                        },
                        "required": ["foldername"]
                    }
                ),
                Tool(
                    name="move_script_to_folder",
                    description="Move a script to a different folder",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to move"},
                            "folder_id": {"type": "integer", "description": "Target folder ID"}
                        },
                        "required": ["script_id", "folder_id"]
                    }
                ),
                # New Backtest Management Tools
                Tool(
                    name="get_backtest_history",
                    description="Get list of all backtests",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_backtest_profit_chart",
                    description="Get profit chart data for a backtest",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"},
                            "interval": {"type": "integer", "default": 1, "description": "Chart interval"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="get_backtest_object",
                    description="Get unified backtest object with all data (lazy loading for heavy data)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "backtest_id": {"type": "string", "description": "Backtest ID"},
                            "include_chart_partition": {"type": "boolean", "default": False, "description": "Include heavy chart partition data"},
                            "summary_only": {"type": "boolean", "default": True, "description": "Return summary only (faster)"}
                        },
                        "required": ["backtest_id"]
                    }
                ),
                Tool(
                    name="test_concurrent_backtests",
                    description="Test concurrent backtest execution limits",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script_id": {"type": "string", "description": "Script ID to test with"},
                            "account_id": {"type": "string", "description": "Account ID for testing"},
                            "market_tag": {"type": "string", "description": "Market tag for testing"},
                            "max_concurrent": {"type": "integer", "default": 10, "description": "Maximum concurrent backtests to test"}
                        },
                        "required": ["script_id", "account_id", "market_tag"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls"""
            if not self.haas_executor:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "HaasOnline API not authenticated. Check your credentials.",
                        "success": False
                    })
                )]

            try:
                result = await self._execute_tool(name, arguments)
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "success": False
                    })
                )]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool"""
        
        if name == "get_haas_status":
            return {
                "status": "authenticated" if self.haas_executor else "unauthenticated",
                "haas_api_connected": bool(self.haas_executor),
                "success": True
            }
        
        elif name == "get_auth_status":
            # Get detailed authentication status
            if hasattr(self, 'auth_manager') and self.auth_manager:
                status = self.auth_manager.get_authentication_status()
                return {"success": True, "data": status}
            else:
                return {
                    "success": True,
                    "data": {
                        "authenticated": bool(self.haas_executor),
                        "credential_sets_available": 0,
                        "current_session": None,
                        "credential_sets": [],
                        "note": "Enhanced authentication manager not available"
                    }
                }
        
        elif name == "refresh_authentication":
            # Force refresh authentication
            if hasattr(self, 'auth_manager') and self.auth_manager:
                try:
                    auth_result = self.auth_manager.refresh_authentication()
                    if auth_result.success:
                        self.haas_executor = auth_result.executor
                        return {
                            "success": True,
                            "message": f"Authentication refreshed successfully with {auth_result.credential_set.name} credentials",
                            "server_info": auth_result.server_info
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Authentication refresh failed: {auth_result.error_message}"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Exception during authentication refresh: {str(e)}"
                    }
            else:
                # Fall back to original authentication method
                try:
                    self._initialize_haas_api()
                    return {
                        "success": bool(self.haas_executor),
                        "message": "Basic authentication attempted",
                        "note": "Enhanced authentication manager not available"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Authentication failed: {str(e)}"
                    }
        
        elif name == "get_all_accounts":
            # Get all accounts by making a direct HTTP request
            try:
                import requests
                import json
                
                # Make direct HTTP request to bypass pydantic validation
                url = f"http://{os.getenv('API_HOST', '127.0.0.1')}:{os.getenv('API_PORT', 8090)}/AccountAPI.php"
                params = {
                    "channel": "GET_ACCOUNTS",
                    "userid": getattr(self.haas_executor.state, 'user_id', None),
                    "interfacekey": getattr(self.haas_executor.state, 'interface_key', None),
                }
                
                response = requests.get(url, params=params)
                response_data = response.json()
                
                if response_data.get("Success"):
                    accounts_data = response_data.get("Data", [])
                    return {"success": True, "data": accounts_data}
                else:
                    return {"success": False, "error": response_data.get("Error", "Unknown error"), "data": []}
            except Exception as e:
                logger.error(f"Error getting accounts: {e}")
                return {"success": False, "error": str(e), "data": []}
        
        elif name == "create_simulated_account":
            response = self.haas_executor._execute_inner(
                endpoint="Account",
                response_type=dict,
                query_params={
                    "channel": "ADD_SIMULATED_ACCOUNT",
                    "name": arguments["account_name"],
                    "drivercode": arguments["driver_code"],
                    "drivertype": arguments["driver_type"],
                    "interfacekey": self.haas_executor.state.interface_key,
                    "userid": self.haas_executor.state.user_id,
                }
            )
            return {
                "success": response.Success,
                "data": response.Data if response.Success else None,
                "error": response.Error if not response.Success else None
            }
        
        elif name == "get_all_labs":
            labs = api.get_all_labs(self.haas_executor)
            # Convert lab objects to dictionaries for JSON serialization
            labs_data = [self._serialize_object(lab) for lab in labs]
            return {"success": True, "data": labs_data}
        
        elif name == "create_lab":
            market = CloudMarket(
                C=arguments.get("market_category", "SPOT"),
                PS=arguments.get("market_price_source", "BINANCE"),
                P=arguments.get("market_primary", "BTC"),
                S=arguments.get("market_secondary", "USDT")
            )
            req = CreateLabRequest.with_generated_name(
                script_id=arguments["script_id"],
                account_id=arguments["account_id"],
                market=market,
                exchange_code=arguments.get("exchange_code", "BINANCE"),
                interval=arguments.get("interval", 1),
                default_price_data_style=arguments.get("default_price_data_style", "CandleStick")
            )
            lab = api.create_lab(self.haas_executor, req)
            return {
                "success": True,
                "data": {
                    "lab_id": lab.lab_id,
                    "lab_name": lab.name,
                    "message": "Lab created successfully"
                }
            }
        
        elif name == "clone_lab":
            cloned_lab = api.clone_lab(
                self.haas_executor, 
                arguments["lab_id"], 
                arguments.get("new_name")
            )
            return {
                "success": True,
                "data": {
                    "lab_id": cloned_lab.lab_id,
                    "lab_name": cloned_lab.name,
                    "message": "Lab cloned successfully"
                }
            }
        
        elif name == "delete_lab":
            success = api.delete_lab(self.haas_executor, arguments["lab_id"])
            return {
                "success": success,
                "message": f"Lab {arguments['lab_id']} deleted successfully" if success else "Failed to delete lab"
            }
        
        elif name == "backtest_lab":
            req = api.StartLabExecutionRequest(
                lab_id=arguments["lab_id"],
                start_unix=arguments["start_unix"],
                end_unix=arguments["end_unix"],
                send_email=arguments.get("send_email", False)
            )
            result = api.start_lab_execution(self.haas_executor, req)
            return {
                "success": True,
                "data": result,
                "message": "Backtest started successfully"
            }
        
        elif name == "get_backtest_results":
            req = api.GetBacktestResultRequest(
                lab_id=arguments["lab_id"],
                next_page_id=arguments.get("next_page_id", -1),
                page_lenght=arguments.get("page_length", 100)
            )
            results = api.get_backtest_result(self.haas_executor, req)
            return {"success": True, "data": results}
        
        elif name == "get_all_markets":
            markets = api.get_all_markets(self.haas_executor)
            return {"success": True, "data": markets}
        
        elif name == "add_script":
            script = api.add_script(
                self.haas_executor,
                arguments["script_name"],
                arguments["script_content"],
                arguments.get("description", ""),
                arguments.get("script_type", 0)
            )
            return {
                "success": True,
                "data": {
                    "script_id": script.script_id,
                    "script_name": script.script_name,
                    "message": "Script added successfully"
                }
            }
        
        elif name == "deposit_funds":
            success = api.deposit_funds(
                self.haas_executor,
                arguments["account_id"],
                arguments["currency"],
                arguments["wallet_id"],
                arguments["amount"]
            )
            return {
                "success": success,
                "message": "Funds deposited successfully" if success else "Failed to deposit funds"
            }
        
        elif name == "withdraw_funds":
            success = api.withdraw_funds(
                self.haas_executor,
                arguments["account_id"],
                arguments["currency"],
                arguments["wallet_id"],
                arguments["amount"]
            )
            return {
                "success": success,
                "message": "Funds withdrawn successfully" if success else "Failed to withdraw funds"
            }

        elif name == "get_account_balance":
            balance = api.get_account_balance(self.haas_executor, arguments["account_id"])
            return {"success": True, "data": balance}
        
        elif name == "discover_cutoff_date":
            if not get_enhanced_executor:
                return {"success": False, "error": "History intelligence not available"}
            
            executor = get_enhanced_executor(self.haas_executor)
            result = executor.discover_cutoff_for_lab(arguments["lab_id"])
            return result
        
        elif name == "validate_backtest_period":
            if not get_enhanced_executor:
                return {"success": False, "error": "History intelligence not available"}
            
            executor = get_enhanced_executor(self.haas_executor)
            result = executor.validate_lab_backtest_period(
                arguments["lab_id"],
                arguments["start_date"],
                arguments["end_date"]
            )
            return result
        
        elif name == "execute_backtest_intelligent":
            if not get_enhanced_executor:
                return {"success": False, "error": "History intelligence not available"}
            
            executor = get_enhanced_executor(self.haas_executor)
            result = executor.execute_backtest_with_intelligence(
                arguments["lab_id"],
                arguments["start_date"],
                arguments["end_date"],
                arguments.get("send_email", False),
                arguments.get("auto_adjust", True)
            )
            
            # Convert EnhancedExecutionResult to dictionary
            return {
                "success": result.success,
                "lab_id": result.lab_id,
                "market_tag": result.market_tag,
                "original_start_date": result.original_start_date.isoformat(),
                "actual_start_date": result.actual_start_date.isoformat(),
                "end_date": result.end_date.isoformat(),
                "execution_started": result.execution_started,
                "history_intelligence_used": result.history_intelligence_used,
                "cutoff_date": result.cutoff_date.isoformat() if result.cutoff_date else None,
                "adjustments_made": result.adjustments_made,
                "execution_time": result.execution_time,
                "error_message": result.error_message
            }
        
        elif name == "get_history_summary":
            if not get_enhanced_executor:
                return {"success": False, "error": "History intelligence not available"}
            
            executor = get_enhanced_executor(self.haas_executor)
            result = executor.get_history_summary()
            return result
        
        elif name == "bulk_discover_cutoffs":
            if not get_enhanced_executor:
                return {"success": False, "error": "History intelligence not available"}
            
            executor = get_enhanced_executor(self.haas_executor)
            result = executor.bulk_discover_cutoffs(arguments["lab_ids"])
            return result
        
        # Lab Management Tools
        elif name == "get_lab_details":
            lab_details = api.get_lab_details(self.haas_executor, arguments["lab_id"])
            return {"success": True, "data": lab_details}
        
        elif name == "update_lab_details":
            lab_details = api.get_lab_details(self.haas_executor, arguments["lab_id"])
            if arguments.get("name"):
                lab_details.name = arguments["name"]
            # Update other settings if provided
            updated_lab = api.update_lab_details(self.haas_executor, lab_details)
            return {"success": True, "data": updated_lab, "message": "Lab details updated successfully"}
        
        elif name == "change_lab_script":
            updated_lab = api.change_lab_script(self.haas_executor, arguments["lab_id"], arguments["script_id"])
            return {"success": True, "data": updated_lab, "message": "Lab script changed successfully"}
        
        elif name == "cancel_lab_execution":
            success = api.cancel_lab_execution(self.haas_executor, arguments["lab_id"])
            return {"success": success, "message": "Lab execution cancelled" if success else "Failed to cancel lab execution"}
        
        elif name == "get_lab_execution_update":
            update = api.get_lab_execution_update(self.haas_executor, arguments["lab_id"])
            return {"success": True, "data": update}
        
        elif name == "update_lab_parameter_ranges":
            from pyHaasAPI.lab import update_lab_parameter_ranges
            updated_lab = update_lab_parameter_ranges(
                self.haas_executor, 
                arguments["lab_id"], 
                arguments.get("randomize", True)
            )
            return {"success": True, "data": updated_lab, "message": "Lab parameter ranges updated successfully"}
        
        # Bot Management Tools
        elif name == "get_all_bots":
            bots = api.get_all_bots(self.haas_executor)
            return {"success": True, "data": bots}
        
        elif name == "get_bot_details":
            bot = api.get_bot(self.haas_executor, arguments["bot_id"])
            return {"success": True, "data": bot}
        
        elif name == "create_bot_from_lab":
            req = api.AddBotFromLabRequest(
                lab_id=arguments["lab_id"],
                backtest_id=arguments["backtest_id"],
                bot_name=arguments["bot_name"],
                account_id=arguments["account_id"],
                market=arguments["market"],
                leverage=arguments.get("leverage", 0)
            )
            bot = api.add_bot_from_lab(self.haas_executor, req)
            return {"success": True, "data": bot, "message": "Bot created from lab successfully"}
        
        elif name == "activate_bot":
            bot = api.activate_bot(self.haas_executor, arguments["bot_id"], arguments.get("clean_reports", False))
            return {"success": True, "data": bot, "message": "Bot activated successfully"}
        
        elif name == "deactivate_bot":
            bot = api.deactivate_bot(self.haas_executor, arguments["bot_id"], arguments.get("cancel_orders", False))
            return {"success": True, "data": bot, "message": "Bot deactivated successfully"}
        
        elif name == "pause_bot":
            bot = api.pause_bot(self.haas_executor, arguments["bot_id"])
            return {"success": True, "data": bot, "message": "Bot paused successfully"}
        
        elif name == "resume_bot":
            bot = api.resume_bot(self.haas_executor, arguments["bot_id"])
            return {"success": True, "data": bot, "message": "Bot resumed successfully"}
        
        elif name == "delete_bot":
            success = api.delete_bot(self.haas_executor, arguments["bot_id"])
            return {"success": bool(success), "message": "Bot deleted successfully" if success else "Failed to delete bot"}
        
        elif name == "deactivate_all_bots":
            bots = api.deactivate_all_bots(self.haas_executor)
            return {"success": True, "data": bots, "message": f"Deactivated {len(bots)} bots"}
        
        # Script Management Tools
        elif name == "get_all_scripts":
            scripts = api.get_all_scripts(self.haas_executor)
            # Convert script objects to dictionaries for JSON serialization
            scripts_data = [self._serialize_object(script) for script in scripts]
            return {"success": True, "data": scripts_data}
        
        elif name == "get_script_details":
            script = api.get_script_item(self.haas_executor, arguments["script_id"])
            return {"success": True, "data": script}
        
        elif name == "edit_script":
            script = api.edit_script(
                self.haas_executor,
                arguments["script_id"],
                arguments.get("script_name"),
                arguments.get("script_content"),
                arguments.get("description", "")
            )
            return {"success": True, "data": script, "message": "Script edited successfully"}
        
        elif name == "delete_script":
            success = api.delete_script(self.haas_executor, arguments["script_id"])
            return {"success": success, "message": "Script deleted successfully" if success else "Failed to delete script"}
        
        elif name == "get_scripts_by_name":
            scripts = api.get_scripts_by_name(self.haas_executor, arguments["name_pattern"])
            return {"success": True, "data": scripts}
        
        elif name in ["save_script", "validate_script", "compile_script"]:
            # All these tools do the same thing - save script with validation
            result = api.save_script_with_validation(
                self.haas_executor,
                arguments["script_id"],
                arguments["source_code"],
                arguments.get("settings")
            )
            
            # Determine the appropriate message based on which tool was called
            if name == "save_script":
                success_msg = "Script saved successfully"
                error_msg = f"Script save failed: {result.get('Error', 'Unknown error')}"
            elif name == "validate_script":
                success_msg = "Script validated successfully"
                error_msg = f"Script validation failed: {result.get('Error', 'Unknown error')}"
            else:  # compile_script (deprecated)
                success_msg = "Script compiled successfully"
                error_msg = f"Script compilation failed: {result.get('Error', 'Unknown error')}"
            
            is_valid = result.get("Data", {}).get("IV", False)
            has_errors = len(result.get("Data", {}).get("LCE", [])) > 0
            
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "validation_logs": result.get("Data", {}).get("CL", []),
                "validation_errors": result.get("Data", {}).get("LCE", []),
                "syntax_errors": result.get("Data", {}).get("VCE", []),
                "is_valid": is_valid,
                "has_errors": has_errors,
                "message": success_msg if result.get("Success", False) and is_valid else error_msg
            }
        
        # Market Data Tools
        elif name == "get_market_price":
            price = api.get_market_price(self.haas_executor, arguments["market"])
            return {"success": True, "data": price}
        
        elif name == "get_order_book":
            orderbook = api.get_order_book(self.haas_executor, arguments["market"], arguments.get("depth", 20))
            return {"success": True, "data": orderbook}
        
        elif name == "get_market_snapshot":
            snapshot = api.get_market_snapshot(self.haas_executor, arguments["market"])
            return {"success": True, "data": snapshot}
        
        elif name == "get_last_trades":
            trades = api.get_last_trades(self.haas_executor, arguments["market"], arguments.get("limit", 100))
            return {"success": True, "data": trades}
        
        # Account Management Tools (Extended)
        elif name == "get_account_data":
            account_data = api.get_account_data(self.haas_executor, arguments["account_id"])
            return {"success": True, "data": account_data}
        
        elif name == "get_all_account_balances":
            balances = api.get_all_account_balances(self.haas_executor)
            return {"success": True, "data": balances}
        
        elif name == "get_account_orders":
            orders = api.get_account_orders(self.haas_executor, arguments["account_id"])
            return {"success": True, "data": orders}
        
        elif name == "get_account_positions":
            positions = api.get_account_positions(self.haas_executor, arguments["account_id"])
            return {"success": True, "data": positions}
        
        elif name == "get_account_trades":
            trades = api.get_account_trades(self.haas_executor, arguments["account_id"])
            return {"success": True, "data": trades}
        
        elif name == "rename_account":
            success = api.rename_account(self.haas_executor, arguments["account_id"], arguments["new_name"])
            return {"success": success, "message": "Account renamed successfully" if success else "Failed to rename account"}
        
        # Backtest Analysis Tools
        elif name == "get_backtest_runtime":
            runtime = api.get_backtest_runtime(self.haas_executor, arguments["lab_id"], arguments["backtest_id"])
            return {"success": True, "data": runtime}
        
        elif name == "get_backtest_chart":
            chart = api.get_backtest_chart(self.haas_executor, arguments["lab_id"], arguments["backtest_id"])
            return {"success": True, "data": chart}
        
        elif name == "get_backtest_log":
            log = api.get_backtest_log(self.haas_executor, arguments["lab_id"], arguments["backtest_id"])
            return {"success": True, "data": log}
        
        elif name == "get_backtest_execution_update":
            update = api.get_backtest_execution_update(self.haas_executor, arguments["lab_id"], arguments["backtest_id"])
            return {"success": True, "data": update}
        
        elif name == "get_backtest_chart_partition":
            partition = api.get_backtest_chart_partition(
                self.haas_executor, 
                arguments["lab_id"], 
                arguments["backtest_id"],
                arguments.get("partition_index", 0)
            )
            return {"success": True, "data": partition}
        
        elif name == "cancel_backtest":
            success = api.cancel_backtest(
                self.haas_executor,
                arguments["service_id"],
                arguments["backtest_id"]
            )
            return {
                "success": success,
                "data": {"cancelled": success},
                "message": "Backtest cancelled successfully" if success else "Failed to cancel backtest"
            }
        
        elif name == "execute_backtest":
            # Pass all arguments except the tool name to the execute_backtest function
            backtest_args = {k: v for k, v in arguments.items()}
            result = api.execute_backtest(self.haas_executor, **backtest_args)
            return {
                "success": result.get("Success", False),
                "data": result,
                "message": "Backtest execution started successfully" if result.get("Success", False) else f"Failed to start backtest: {result.get('Error', 'Unknown error')}"
            }
        
        elif name == "share_script":
            shared_id = api.share_script(
                self.haas_executor,
                arguments["script_id"],
                arguments["script_name"],
                arguments.get("script_description", ""),
                arguments.get("status", 0),
                arguments.get("allowed_users", "")
            )
            return {
                "success": bool(shared_id),
                "data": {"shared_script_id": shared_id},
                "message": f"Script shared successfully with ID: {shared_id}" if shared_id else "Failed to share script"
            }
        
        # Enhanced Execution Tools
        elif name == "execute_backtest_with_intelligence":
            from pyHaasAPI.enhanced_execution import execute_backtest_with_intelligence
            result = execute_backtest_with_intelligence(
                self.haas_executor,
                arguments["lab_id"],
                arguments["start_date"],
                arguments["end_date"],
                arguments.get("send_email", False),
                arguments.get("auto_adjust", True)
            )
            return {
                "success": result.success,
                "data": {
                    "lab_id": result.lab_id,
                    "market_tag": result.market_tag,
                    "original_start_date": result.original_start_date.isoformat(),
                    "actual_start_date": result.actual_start_date.isoformat(),
                    "end_date": result.end_date.isoformat(),
                    "execution_started": result.execution_started,
                    "history_intelligence_used": result.history_intelligence_used,
                    "cutoff_date": result.cutoff_date.isoformat() if result.cutoff_date else None,
                    "adjustments_made": result.adjustments_made,
                    "execution_time": result.execution_time,
                    "error_message": result.error_message
                }
            }
        
        # Parameter Optimization Tools
        elif name == "optimize_lab_parameters_mixed":
            from pyHaasAPI.optimization import optimize_lab_parameters_mixed
            result = optimize_lab_parameters_mixed(
                self.haas_executor,
                arguments["lab_id"],
                arguments.get("max_combinations", 50000)
            )
            return {
                "success": result.success,
                "data": {
                    "lab_id": result.lab_id,
                    "total_parameters": result.total_parameters,
                    "optimized_parameters": result.optimized_parameters,
                    "total_combinations": result.total_combinations,
                    "strategy_used": result.strategy_used.value,
                    "parameter_details": result.parameter_details,
                    "error_message": result.error_message
                }
            }
        
        elif name == "optimize_lab_parameters_traditional":
            from pyHaasAPI.optimization import optimize_lab_parameters_traditional
            result = optimize_lab_parameters_traditional(
                self.haas_executor,
                arguments["lab_id"],
                arguments.get("max_combinations", 10000)
            )
            return {
                "success": result.success,
                "data": {
                    "lab_id": result.lab_id,
                    "total_parameters": result.total_parameters,
                    "optimized_parameters": result.optimized_parameters,
                    "total_combinations": result.total_combinations,
                    "strategy_used": result.strategy_used.value,
                    "parameter_details": result.parameter_details,
                    "error_message": result.error_message
                }
            }
        
        # Account Management Tools
        elif name == "create_test_accounts":
            from pyHaasAPI.accounts.management import AccountManager
            manager = AccountManager(self.haas_executor)
            accounts = manager.create_test_accounts(arguments.get("count", 2))
            return {
                "success": True,
                "data": {
                    "created_accounts": len(accounts),
                    "accounts": [acc.to_dict() for acc in accounts]
                }
            }
        
        elif name == "find_test_accounts":
            from pyHaasAPI.accounts.management import AccountManager
            manager = AccountManager(self.haas_executor)
            accounts = manager.find_test_accounts()
            return {
                "success": True,
                "data": {
                    "test_accounts_found": len(accounts),
                    "accounts": [acc.to_dict() for acc in accounts]
                }
            }
        
        elif name == "get_account_statistics":
            from pyHaasAPI.accounts.management import AccountManager
            manager = AccountManager(self.haas_executor)
            stats = manager.get_account_statistics()
            return {"success": True, "data": stats}
        
        # Market Discovery Tools
        elif name == "discover_markets":
            from pyHaasAPI.markets.discovery import MarketDiscovery
            discovery = MarketDiscovery(self.haas_executor)
            market_types = arguments.get("market_types")
            if market_types:
                from pyHaasAPI.markets.discovery import MarketType
                market_types = [MarketType(mt) for mt in market_types]
            markets = discovery.discover_markets(arguments["exchange"], market_types)
            return {
                "success": True,
                "data": {
                    "exchange": arguments["exchange"],
                    "markets_found": len(markets),
                    "markets": [market.to_dict() for market in markets]
                }
            }
        
        elif name == "discover_perpetual_markets":
            from pyHaasAPI.markets.discovery import discover_perpetual_markets
            markets = discover_perpetual_markets(arguments["exchange"], self.haas_executor)
            return {
                "success": True,
                "data": {
                    "exchange": arguments["exchange"],
                    "perpetual_markets_found": len(markets),
                    "markets": [market.to_dict() for market in markets]
                }
            }
        
        elif name == "find_markets_by_asset":
            from pyHaasAPI.markets.discovery import find_asset_markets
            markets = find_asset_markets(
                arguments["base_asset"],
                arguments.get("exchanges"),
                self.haas_executor
            )
            return {
                "success": True,
                "data": {
                    "base_asset": arguments["base_asset"],
                    "markets_found": len(markets),
                    "markets": [market.to_dict() for market in markets]
                }
            }
        
        elif name == "find_markets_by_symbol":
            from pyHaasAPI.markets.discovery import MarketDiscovery
            discovery = MarketDiscovery(self.haas_executor)
            markets = discovery.find_markets_by_symbol(
                arguments["symbol"],
                arguments.get("exchanges")
            )
            return {
                "success": True,
                "data": {
                    "symbol": arguments["symbol"],
                    "markets_found": len(markets),
                    "markets": [market.to_dict() for market in markets]
                }
            }
        
        # Lab Cloning Tools
        elif name == "clone_lab_for_assets":
            from pyHaasAPI.labs.cloning import LabCloner
            cloner = LabCloner(self.haas_executor)
            results = cloner.clone_lab_for_assets(
                arguments["base_lab_id"],
                arguments["base_assets"],
                arguments["account_id"],
                arguments.get("exchanges"),
                arguments.get("market_types")
            )
            return {
                "success": True,
                "data": {
                    "total_clones": len(results),
                    "successful_clones": len([r for r in results if r.success]),
                    "failed_clones": len([r for r in results if not r.success]),
                    "results": [
                        {
                            "success": r.success,
                            "new_lab_id": r.new_lab_id,
                            "market_tag": r.market_tag,
                            "error_message": r.error_message,
                            "execution_time": r.execution_time
                        }
                        for r in results
                    ]
                }
            }
        
        elif name == "clone_lab_for_perpetual_markets":
            from pyHaasAPI.labs.cloning import LabCloner
            cloner = LabCloner(self.haas_executor)
            results = cloner.clone_lab_for_perpetual_markets(
                arguments["base_lab_id"],
                arguments["account_id"],
                arguments.get("base_assets"),
                arguments.get("exchanges")
            )
            return {
                "success": True,
                "data": {
                    "total_clones": len(results),
                    "successful_clones": len([r for r in results if r.success]),
                    "failed_clones": len([r for r in results if not r.success]),
                    "results": [
                        {
                            "success": r.success,
                            "new_lab_id": r.new_lab_id,
                            "market_tag": r.market_tag,
                            "error_message": r.error_message,
                            "execution_time": r.execution_time
                        }
                        for r in results
                    ]
                }
            }
        
        # Script Management Tools (Extended)
        elif name == "get_haasscript_commands":
            commands = api.get_haasscript_commands(self.haas_executor)
            return {"success": True, "data": commands}
        
        elif name == "get_script_record":
            record = api.get_script_record(self.haas_executor, arguments["script_id"])
            return {"success": True, "data": record.model_dump() if hasattr(record, 'model_dump') else record}
        
        elif name == "edit_script_sourcecode":
            result = api.edit_script_sourcecode(
                self.haas_executor,
                arguments["script_id"],
                arguments["sourcecode"],
                arguments["settings"]
            )
            return {"success": True, "data": result}
        
        elif name == "publish_script":
            result = api.publish_script(self.haas_executor, arguments["script_id"])
            return {"success": result, "data": {"published": result}}
        
        elif name == "get_all_script_folders":
            folders = api.get_all_script_folders(self.haas_executor)
            return {"success": True, "data": [folder.model_dump() if hasattr(folder, 'model_dump') else folder for folder in folders]}
        
        elif name == "create_script_folder":
            folder = api.create_script_folder(
                self.haas_executor,
                arguments["foldername"],
                arguments.get("parentid", -1)
            )
            return {"success": True, "data": folder.model_dump() if hasattr(folder, 'model_dump') else folder}
        
        elif name == "move_script_to_folder":
            result = api.move_script_to_folder(
                self.haas_executor,
                arguments["script_id"],
                arguments["folder_id"]
            )
            return {"success": result, "data": {"moved": result}}
        
        # New Script Manipulation Handlers
        elif name == "edit_script_sourcecode":
            # Edit and save script source code with validation
            result = api.edit_script_sourcecode(
                self.haas_executor,
                arguments["script_id"],
                arguments["source_code"]
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "validation_errors": result.get("Data", {}).get("CompilationErrors", [])
            }
        
        elif name == "check_script_execution_status":
            # Check if script is executing
            result = api.is_script_execution(
                self.haas_executor,
                arguments["script_id"]
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "is_executing": result.get("Data", {}).get("S", 0) == 3  # Status 3 = executing
            }
        
        # New Backtest Management Handlers
        elif name == "execute_quicktest":
            # Execute quick test
            result = api.execute_quicktest(
                self.haas_executor,
                arguments["script_id"],
                arguments["account_id"],
                arguments["market_tag"]
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", "")
            }
        
        elif name == "execute_backtest_advanced":
            # Execute full backtest with advanced options
            result = api.execute_backtest(
                self.haas_executor,
                arguments["script_id"],
                arguments["account_id"],
                arguments["market_tag"],
                arguments["start_unix"],
                arguments["end_unix"],
                arguments.get("send_email", False),
                arguments.get("additional_params", {})
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "backtest_id": result.get("Data", {}).get("BID", "")
            }
        
        elif name == "get_execution_update":
            # Get execution status update
            result = api.get_execution_update(
                self.haas_executor,
                arguments["process_id"]
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", "")
            }
        
        elif name == "get_backtest_runtime":
            # Get backtest runtime information
            result = api.get_backtest_runtime(
                self.haas_executor,
                arguments["backtest_id"]
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", "")
            }
        
        elif name == "get_backtest_logs":
            # Get backtest execution logs
            result = api.get_backtest_logs(
                self.haas_executor,
                arguments["backtest_id"]
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "logs": result.get("Data", {}).get("Logs", [])
            }
        
        elif name == "get_backtest_chart_partition_advanced":
            # Get chart partition with indicator data
            result = api.get_backtest_chart_partition(
                self.haas_executor,
                arguments["backtest_id"],
                arguments.get("partition_index", 0),
                arguments.get("include_market_data", False),
                arguments.get("indicators_only", True)
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "chart_data": result.get("Data", {})
            }
        
        elif name == "archive_backtest":
            # Archive backtest to preserve beyond 48 hours
            result = api.archive_backtest(
                self.haas_executor,
                arguments["backtest_id"],
                arguments.get("archive_result", True)
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "archived": result.get("Data", False)
            }
        
        elif name == "get_backtest_positions":
            # Get backtest position data
            result = api.get_backtest_positions(
                self.haas_executor,
                arguments["backtest_id"],
                arguments.get("next_page_id", 0),
                arguments.get("page_length", 50)
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "positions": result.get("Data", {}).get("I", []),
                "next_page": result.get("Data", {}).get("NP", -1)
            }
        
        elif name == "get_backtest_info":
            # Get comprehensive backtest information
            result = api.get_backtest_info(
                self.haas_executor,
                arguments["backtest_id"]
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", ""),
                "backtest_info": result.get("Data", {})
            }
        
        # New Backtest Management Handlers
        elif name == "get_backtest_history":
            # Get list of all backtests
            result = api.get_backtest_history(self.haas_executor)
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", []),
                "error": result.get("Error", "")
            }
        
        elif name == "get_backtest_profit_chart":
            # Get profit chart data
            result = api.get_backtest_profit_chart(
                self.haas_executor,
                arguments["backtest_id"],
                arguments.get("interval", 1)
            )
            return {
                "success": result.get("Success", False),
                "data": result.get("Data", {}),
                "error": result.get("Error", "")
            }
        
        elif name == "get_backtest_object":
            # Get unified backtest object
            try:
                from pyHaasAPI.backtest_object import BacktestObject
                
                backtest_obj = BacktestObject(self.haas_executor, arguments["backtest_id"])
                
                if arguments.get("summary_only", True):
                    data = backtest_obj.get_summary()
                else:
                    data = backtest_obj.get_full_data(
                        include_chart_partition=arguments.get("include_chart_partition", False)
                    )
                
                return {
                    "success": True,
                    "data": data,
                    "error": ""
                }
            except Exception as e:
                return {
                    "success": False,
                    "data": {},
                    "error": str(e)
                }
        
        elif name == "test_concurrent_backtests":
            # Test concurrent backtest limits
            try:
                import time
                import asyncio
                from concurrent.futures import ThreadPoolExecutor
                
                script_id = arguments["script_id"]
                account_id = arguments["account_id"]
                market_tag = arguments["market_tag"]
                max_concurrent = arguments.get("max_concurrent", 10)
                
                # Use a short time period for testing
                end_time = int(time.time())
                start_time = end_time - (60 * 60)  # 1 hour ago
                
                def start_backtest(test_id):
                    try:
                        result = api.execute_backtest(
                            self.haas_executor,
                            script_id,
                            account_id,
                            market_tag,
                            start_time,
                            end_time,
                            send_email=False
                        )
                        return {
                            "test_id": test_id,
                            "success": result.get("Success", False),
                            "backtest_id": result.get("Data", {}).get("BID", ""),
                            "error": result.get("Error", "")
                        }
                    except Exception as e:
                        return {
                            "test_id": test_id,
                            "success": False,
                            "backtest_id": "",
                            "error": str(e)
                        }
                
                # Test concurrent execution
                results = []
                with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                    futures = [executor.submit(start_backtest, i) for i in range(max_concurrent)]
                    for future in futures:
                        results.append(future.result())
                
                successful_starts = sum(1 for r in results if r["success"])
                
                return {
                    "success": True,
                    "data": {
                        "total_attempts": max_concurrent,
                        "successful_starts": successful_starts,
                        "concurrent_limit_reached": successful_starts < max_concurrent,
                        "results": results
                    },
                    "error": ""
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "data": {},
                    "error": str(e)
                }
        
        else:
            raise ValueError(f"Unknown tool: {name}")

# Create a global instance of HaasMCPServer
haas_mcp_server_instance = HaasMCPServer()

# Expose the underlying MCP Server instance as the ASGI application
# Uvicorn will call this directly
app = haas_mcp_server_instance.server

# The main function is no longer needed for uvicorn, but keep it for direct execution if desired
async def main():
    """Main entry point for direct execution (e.g., python -m mcp_server.server)"""
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await haas_mcp_server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="haas-api-server",
                server_version="1.0.0",
                capabilities=haas_mcp_server_instance.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())