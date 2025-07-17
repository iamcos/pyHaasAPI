#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for pyHaasAPI

This server exposes HaasOnline API functionality through the MCP protocol,
allowing AI models to interact with trading bots, labs, and market data.

Usage:
    python mcp_server.py

The server will start on stdin/stdout for MCP communication.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from itertools import product

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.model import (
    CreateLabRequest, StartLabExecutionRequest, AddBotFromLabRequest,
    GetBacktestResultRequest
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MCPRequest:
    """MCP request structure"""
    jsonrpc: str
    id: Union[int, str]
    method: str
    params: Optional[Dict[str, Any]] = None

@dataclass
class MCPResponse:
    """MCP response structure"""
    jsonrpc: str = "2.0"
    id: Optional[Union[int, str]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class HaasOnlineMCPServer:
    """MCP Server for HaasOnline API integration"""
    
    def __init__(self):
        self.authenticated = False
        self.executor = None
        
    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the MCP server"""
        try:
            # Extract connection parameters
            host = params.get("host", "127.0.0.1")
            port = params.get("port", 8090)
            email = params.get("email")
            password = params.get("password")
            
            if not email or not password:
                return {
                    "error": "Email and password are required for initialization"
                }
            
            # Initialize executor and authenticate
            self.executor = api.RequestsExecutor(
                host=host,
                port=port,
                state=api.Guest()
            ).authenticate(email=email, password=password)
            
            self.authenticated = True
            
            return {
                "status": "initialized",
                "message": f"Connected to HaasOnline API at {host}:{port}",
                "user": email
            }
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return {
                "error": f"Initialization failed: {str(e)}"
            }
    
    async def get_scripts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get available trading scripts"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            scripts = api.get_all_scripts(self.executor)
            return {
                "scripts": [
                    {
                        "script_id": script.script_id,
                        "script_name": script.script_name,
                        "description": getattr(script, 'description', ''),
                        "category": getattr(script, 'category', '')
                    }
                    for script in scripts
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get scripts: {e}")
            return {"error": str(e)}
    
    async def get_markets(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get available markets"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            markets = api.get_all_markets(self.executor)
            return {
                "markets": [
                    {
                        "price_source": market.price_source,
                        "primary": market.primary,
                        "secondary": market.secondary,
                        "market_id": getattr(market, 'market_id', '')
                    }
                    for market in markets
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get markets: {e}")
            return {"error": str(e)}
    
    async def get_accounts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get user accounts"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            accounts = api.get_accounts(self.executor)
            return {
                "accounts": [
                    {
                        "account_id": account.account_id,
                        "name": account.name,
                        "type": getattr(account, 'type', ''),
                        "balance": getattr(account, 'balance', 0)
                    }
                    for account in accounts
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return {"error": str(e)}
    
    async def create_lab(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lab for backtesting"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            lab_request = CreateLabRequest(
                script_id=params["script_id"],
                name=params["name"],
                account_id=params["account_id"],
                market=params["market"],
                interval=params.get("interval", 1),
                default_price_data_style=params.get("style", "CandleStick")
            )
            
            lab = api.create_lab(self.executor, lab_request)
            
            return {
                "lab_id": lab.lab_id,
                "name": lab.name,
                "status": "created"
            }
        except Exception as e:
            logger.error(f"Failed to create lab: {e}")
            return {"error": str(e)}
    
    async def get_lab_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get lab details and parameters"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            lab_details = api.get_lab_details(self.executor, params["lab_id"])
            
            return {
                "lab_id": lab_details.lab_id,
                "name": lab_details.name,
                "status": getattr(lab_details, 'status', ''),
                "parameters": lab_details.parameters,
                "config": getattr(lab_details, 'config', {}),
                "settings": getattr(lab_details, 'settings', {})
            }
        except Exception as e:
            logger.error(f"Failed to get lab details: {e}")
            return {"error": str(e)}
    
    async def update_lab_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update lab parameters"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            lab_details = api.get_lab_details(self.executor, params["lab_id"])
            
            # Update parameters
            for param in lab_details.parameters:
                key = param.get('K', '')
                if key in params["parameters"]:
                    param['O'] = [str(params["parameters"][key])]
            
            api.update_lab_details(self.executor, lab_details)
            
            return {
                "lab_id": params["lab_id"],
                "status": "updated",
                "parameters_updated": list(params["parameters"].keys())
            }
        except Exception as e:
            logger.error(f"Failed to update lab parameters: {e}")
            return {"error": str(e)}
    
    async def start_backtest(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a lab backtest"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            execution_request = StartLabExecutionRequest(
                lab_id=params["lab_id"],
                start_unix=params["start_unix"],
                end_unix=params["end_unix"],
                send_email=params.get("send_email", False)
            )
            
            api.start_lab_execution(self.executor, execution_request)
            
            return {
                "lab_id": params["lab_id"],
                "status": "started",
                "start_time": params["start_unix"],
                "end_time": params["end_unix"]
            }
        except Exception as e:
            logger.error(f"Failed to start backtest: {e}")
            return {"error": str(e)}
    
    async def get_backtest_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get backtest results"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            result_request = GetBacktestResultRequest(
                lab_id=params["lab_id"],
                next_page_id=params.get("page_id", 0),
                page_lenght=params.get("page_length", 1000)
            )
            
            results = api.get_backtest_result(self.executor, result_request)
            
            return {
                "lab_id": params["lab_id"],
                "results": [
                    {
                        "backtest_id": item.backtest_id,
                        "roi": item.summary.ReturnOnInvestment if item.summary else 0,
                        "total_trades": item.summary.TotalTrades if item.summary else 0,
                        "win_rate": item.summary.WinRate if item.summary else 0,
                        "parameters": item.parameters if hasattr(item, 'parameters') else {}
                    }
                    for item in results.items
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get backtest results: {e}")
            return {"error": str(e)}
    
    async def create_bot_from_lab(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a bot from lab backtest results"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            bot_request = AddBotFromLabRequest(
                lab_id=params["lab_id"],
                backtest_id=params["backtest_id"],
                bot_name=params["bot_name"],
                account_id=params["account_id"],
                market=params["market"],
                leverage=params.get("leverage", 0)
            )
            
            bot = api.add_bot_from_lab(self.executor, bot_request)
            
            return {
                "bot_id": bot.bot_id,
                "bot_name": bot.bot_name,
                "status": "created"
            }
        except Exception as e:
            logger.error(f"Failed to create bot: {e}")
            return {"error": str(e)}
    
    async def parameter_sweep(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform parameter sweep on a lab"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            lab_id = params["lab_id"]
            sweep_params = params["sweep_parameters"]
            sweep_range = params.get("sweep_range", [0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
            
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Generate parameter combinations
            param_combinations = []
            for values in product(sweep_range, repeat=len(sweep_params)):
                param_dict = dict(zip(sweep_params, values))
                param_combinations.append(param_dict)
            
            # Update lab with first combination and run backtest
            first_combo = param_combinations[0]
            for param in lab_details.parameters:
                key = param.get('K', '')
                if key in first_combo:
                    param['O'] = [str(first_combo[key])]
            
            api.update_lab_details(self.executor, lab_details)
            
            # Start backtest
            now = int(time.time())
            start_unix = now - params.get("backtest_hours", 6) * 3600
            end_unix = now
            
            execution_request = StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=start_unix,
                end_unix=end_unix,
                send_email=False
            )
            
            api.start_lab_execution(self.executor, execution_request)
            
            return {
                "lab_id": lab_id,
                "status": "sweep_started",
                "total_combinations": len(param_combinations),
                "sweep_parameters": sweep_params,
                "backtest_period": f"{params.get('backtest_hours', 6)} hours"
            }
        except Exception as e:
            logger.error(f"Failed to start parameter sweep: {e}")
            return {"error": str(e)}
    
    async def get_bots(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get user's trading bots"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            bots = api.get_bots(self.executor)
            return {
                "bots": [
                    {
                        "bot_id": bot.bot_id,
                        "bot_name": bot.bot_name,
                        "status": getattr(bot, 'status', ''),
                        "market": getattr(bot, 'market', ''),
                        "account_id": getattr(bot, 'account_id', '')
                    }
                    for bot in bots
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get bots: {e}")
            return {"error": str(e)}
    
    async def start_bot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start a trading bot"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            api.start_bot(self.executor, params["bot_id"])
            return {
                "bot_id": params["bot_id"],
                "status": "started"
            }
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            return {"error": str(e)}
    
    async def stop_bot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop a trading bot"""
        if not self.authenticated:
            return {"error": "Not authenticated"}
        
        try:
            api.stop_bot(self.executor, params["bot_id"])
            return {
                "bot_id": params["bot_id"],
                "status": "stopped"
            }
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")
            return {"error": str(e)}

# Global server instance
server = HaasOnlineMCPServer()

async def handle_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP requests"""
    try:
        method = request.method
        params = request.params or {}
        
        # Route to appropriate handler
        if method == "initialize":
            result = await server.initialize(params)
        elif method == "get_scripts":
            result = await server.get_scripts(params)
        elif method == "get_markets":
            result = await server.get_markets(params)
        elif method == "get_accounts":
            result = await server.get_accounts(params)
        elif method == "create_lab":
            result = await server.create_lab(params)
        elif method == "get_lab_details":
            result = await server.get_lab_details(params)
        elif method == "update_lab_parameters":
            result = await server.update_lab_parameters(params)
        elif method == "start_backtest":
            result = await server.start_backtest(params)
        elif method == "get_backtest_results":
            result = await server.get_backtest_results(params)
        elif method == "create_bot_from_lab":
            result = await server.create_bot_from_lab(params)
        elif method == "parameter_sweep":
            result = await server.parameter_sweep(params)
        elif method == "get_bots":
            result = await server.get_bots(params)
        elif method == "start_bot":
            result = await server.start_bot(params)
        elif method == "stop_bot":
            result = await server.stop_bot(params)
        else:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            )
        
        # Check if result contains error
        if "error" in result:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32000,
                    "message": result["error"]
                }
            )
        
        return MCPResponse(
            id=request.id,
            result=result
        )
        
    except Exception as e:
        logger.error(f"Request handling error: {e}")
        return MCPResponse(
            id=request.id,
            error={
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        )

async def main():
    """Main MCP server loop"""
    logger.info("Starting HaasOnline MCP Server...")
    print("[DEBUG] MCP server main() started", file=sys.stderr)
    
    # Send initialization message
    init_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "initialize": {
                        "description": "Initialize the MCP server and authenticate with the HaasOnline API.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "host": {"type": "string", "description": "HaasOnline API host (e.g., '127.0.0.1')."},
                                "port": {"type": "integer", "description": "HaasOnline API port (e.g., 8090)."},
                                "email": {"type": "string", "description": "User email for authentication."},
                                "password": {"type": "string", "description": "User password for authentication."}
                            },
                            "required": ["email", "password"]
                        }
                    },
                    "get_scripts": {
                        "description": "Get available trading scripts from HaasOnline.",
                        "parameters": {"type": "object", "properties": {}}
                    },
                    "get_markets": {
                        "description": "Get available markets from HaasOnline.",
                        "parameters": {"type": "object", "properties": {}}
                    },
                    "get_accounts": {
                        "description": "Get user accounts from HaasOnline.",
                        "parameters": {"type": "object", "properties": {}}
                    },
                    "create_lab": {
                        "description": "Create a new lab for backtesting on HaasOnline.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "script_id": {"type": "string", "description": "ID of the script to use for the lab."},
                                "name": {"type": "string", "description": "Name of the new lab."},
                                "account_id": {"type": "string", "description": "ID of the account to associate with the lab."},
                                "market": {"type": "string", "description": "Market symbol for the lab (e.g., 'BINANCE_BTC_USDT_')."},
                                "interval": {"type": "integer", "description": "Candle interval in minutes (default: 1)."},
                                "style": {"type": "string", "description": "Default price data style (e.g., 'CandleStick', default: 'CandleStick')."}
                            },
                            "required": ["script_id", "name", "account_id", "market"]
                        }
                    },
                    "get_lab_details": {
                        "description": "Get details and parameters of a specific lab.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "lab_id": {"type": "string", "description": "ID of the lab to retrieve details for."}
                            },
                            "required": ["lab_id"]
                        }
                    },
                    "update_lab_parameters": {
                        "description": "Update parameters for a specific lab.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "lab_id": {"type": "string", "description": "ID of the lab to update."},
                                "parameters": {
                                    "type": "object",
                                    "description": "Dictionary of parameter keys and their new values.",
                                    "additionalProperties": {"type": "string"}
                                }
                            },
                            "required": ["lab_id", "parameters"]
                        }
                    },
                    "start_backtest": {
                        "description": "Start a backtest for a specified lab.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "lab_id": {"type": "string", "description": "ID of the lab to start backtest for."},
                                "start_unix": {"type": "integer", "description": "Start timestamp of the backtest in Unix format."},
                                "end_unix": {"type": "integer", "description": "End timestamp of the backtest in Unix format."},
                                "send_email": {"type": "boolean", "description": "Whether to send an email upon completion (default: false)."}
                            },
                            "required": ["lab_id", "start_unix", "end_unix"]
                        }
                    },
                    "get_backtest_results": {
                        "description": "Get backtest results for a specific lab.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "lab_id": {"type": "string", "description": "ID of the lab to get results for."},
                                "page_id": {"type": "integer", "description": "Page number for results (default: 0)."},
                                "page_length": {"type": "integer", "description": "Number of results per page (default: 1000)."}
                            },
                            "required": ["lab_id"]
                        }
                    },
                    "create_bot_from_lab": {
                        "description": "Create a trading bot from lab backtest results.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "lab_id": {"type": "string", "description": "ID of the lab from which to create the bot."},
                                "backtest_id": {"type": "string", "description": "ID of the specific backtest result to use."},
                                "bot_name": {"type": "string", "description": "Name for the new bot."},
                                "account_id": {"type": "string", "description": "ID of the account for the bot."},
                                "market": {"type": "string", "description": "Market symbol for the bot (e.g., 'BINANCE_BTC_USDT_')."},
                                "leverage": {"type": "number", "description": "Leverage for the bot (default: 0)."}
                            },
                            "required": ["lab_id", "backtest_id", "bot_name", "account_id", "market"]
                        }
                    },
                    "parameter_sweep": {
                        "description": "Perform a parameter sweep on a lab, running multiple backtests with varying parameters.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "lab_id": {"type": "string", "description": "ID of the lab to perform the sweep on."},
                                "sweep_parameters": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of parameter keys to sweep."
                                },
                                "sweep_range": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "description": "List of values to test for each sweep parameter (default: [0.5, 1.0, 1.5, 2.0, 2.5, 3.0])."
                                },
                                "backtest_hours": {"type": "integer", "description": "Duration of each backtest in hours (default: 6)."}
                            },
                            "required": ["lab_id", "sweep_parameters"]
                        }
                    },
                    "get_bots": {
                        "description": "Get a list of all trading bots.",
                        "parameters": {"type": "object", "properties": {}}
                    },
                    "start_bot": {
                        "description": "Start a specific trading bot.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "bot_id": {"type": "string", "description": "ID of the bot to start."}
                            },
                            "required": ["bot_id"]
                        }
                    },
                    "stop_bot": {
                        "description": "Stop a specific trading bot.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "bot_id": {"type": "string", "description": "ID of the bot to stop."}
                            },
                            "required": ["bot_id"]
                        }
                    }
                }
            },
            "clientInfo": {
                "name": "haasonline-mcp-server",
                "version": "1.0.0"
            }
        }
    }
    
    print(json.dumps(init_message))
    print("[DEBUG] MCP server sent init message", file=sys.stderr)
    sys.stdout.flush()
    
    # Main request loop
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request_data = json.loads(line.strip())
            request = MCPRequest(**request_data)
            
            response = await handle_request(request)
            response_dict = asdict(response)
            
            # Remove None values
            response_dict = {k: v for k, v in response_dict.items() if v is not None}
            
            print(json.dumps(response_dict))
            sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            error_response = MCPResponse(
                error={
                    "code": -32700,
                    "message": "Parse error"
                }
            )
            print(json.dumps(asdict(error_response)))
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            error_response = MCPResponse(
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
            print(json.dumps(asdict(error_response)))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
