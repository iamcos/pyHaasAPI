#!/usr/bin/env python3
"""
Simple API Bridge for HaasOnline
Direct HTTP API that connects to HaasOnline without MCP complexity
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("haas-api-bridge")

app = FastAPI(title="HaasOnline API Bridge", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

# Global API client
haas_executor = None

def initialize_haas_api():
    """Initialize HaasOnline API connection"""
    global haas_executor
    
    try:
        # Import pyHaasAPI
        from pyHaasAPI import api
        
        api_host = os.getenv("API_HOST", "127.0.0.1")
        api_port = int(os.getenv("API_PORT", 8090))
        
        # Try local credentials first, then fall back to regular credentials
        api_email = os.getenv("API_EMAIL_LOCAL") or os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD_LOCAL") or os.getenv("API_PASSWORD")

        if not api_email or not api_password:
            logger.error("No API credentials found in environment")
            return False

        logger.info(f"Connecting to HaasOnline API: {api_host}:{api_port} with email: {api_email}")

        haas_executor = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        ).authenticate(
            email=api_email,
            password=api_password
        )
        
        logger.info("Successfully connected to HaasOnline API")
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect to HaasOnline API: {e}")
        haas_executor = None
        return False

@app.on_event("startup")
async def startup_event():
    """Initialize the API bridge on startup"""
    success = initialize_haas_api()
    if success:
        logger.info("HaasOnline API Bridge started successfully")
    else:
        logger.error("Failed to start HaasOnline API Bridge")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return APIResponse(
        success=True,
        data={
            "status": "healthy" if haas_executor else "unhealthy",
            "services": {
                "mcp": True,
                "haas": haas_executor is not None
            },
            "timestamp": "2025-01-13T00:00:00Z"
        },
        timestamp="2025-01-13T00:00:00Z"
    )

@app.get("/api/haas/status")
async def get_haas_status():
    try:
        if not haas_executor:
            return APIResponse(
                success=False,
                error="HaasOnline API not connected",
                timestamp="2025-01-13T00:00:00Z"
            )
        
        # Simple status check
        result = {
            "connected": True,
            "version": "1.0.0"
        }
        
        return APIResponse(
            success=True,
            data=result,
            timestamp="2025-01-13T00:00:00Z"
        )
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/accounts")
async def get_all_accounts():
    try:
        if not haas_executor:
            return APIResponse(
                success=False,
                error="HaasOnline API not connected",
                timestamp="2025-01-13T00:00:00Z"
            )
        
        # Get accounts from HaasOnline using the correct API method
        from pyHaasAPI.api import get_all_account_balances
        logger.info("Fetching account balances...")
        accounts_data = get_all_account_balances(haas_executor)
        logger.info(f"Accounts data type: {type(accounts_data)}, data: {accounts_data}")
        
        # Convert to our format
        accounts = []
        if accounts_data and isinstance(accounts_data, list):
            for account_info in accounts_data:
                accounts.append({
                    "id": account_info.get("accountId", ""),
                    "name": account_info.get("accountName", f"Account {account_info.get('accountId', '')}"),
                    "type": "simulated" if account_info.get("isSimulated", True) else "live",
                    "balance": float(account_info.get("balance", 0)),
                    "equity": float(account_info.get("equity", 0)),
                    "margin": float(account_info.get("margin", 0)),
                    "freeMargin": float(account_info.get("freeMargin", 0)),
                    "marginLevel": float(account_info.get("marginLevel", 0)),
                    "currency": account_info.get("currency", "USD")
                })
        
        return APIResponse(
            success=True,
            data=accounts,
            timestamp="2025-01-13T00:00:00Z"
        )
        
    except Exception as e:
        logger.error(f"Get accounts failed: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/labs")
async def get_all_labs():
    try:
        if not haas_executor:
            return APIResponse(
                success=False,
                error="HaasOnline API not connected",
                timestamp="2025-01-13T00:00:00Z"
            )
        
        # Get labs from HaasOnline using the correct API method
        from pyHaasAPI.api import get_all_labs
        labs_data = get_all_labs(haas_executor)
        
        # Convert to our format
        labs = []
        if labs_data and isinstance(labs_data, list):
            for lab_info in labs_data:
                labs.append({
                    "id": lab_info.get("labId", ""),
                    "name": lab_info.get("name", f"Lab {lab_info.get('labId', '')}"),
                    "scriptId": lab_info.get("scriptId", ""),
                    "accountId": lab_info.get("accountId", ""),
                    "parameters": lab_info.get("parameters", {}),
                    "status": lab_info.get("status", "idle"),
                    "createdAt": lab_info.get("createdAt", "2025-01-13T00:00:00Z")
                })
        
        return APIResponse(
            success=True,
            data=labs,
            timestamp="2025-01-13T00:00:00Z"
        )
        
    except Exception as e:
        logger.error(f"Get labs failed: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/bots")
async def get_all_bots():
    try:
        if not haas_executor:
            return APIResponse(
                success=False,
                error="HaasOnline API not connected",
                timestamp="2025-01-13T00:00:00Z"
            )
        
        # Get bots from HaasOnline using the correct API method
        from pyHaasAPI.api import get_all_bots
        bots_data = get_all_bots(haas_executor)
        
        # Convert to our format
        bots = []
        if bots_data and isinstance(bots_data, list):
            for bot_info in bots_data:
                # Extract performance data from bot statistics
                stats = bot_info.get("statistics", {})
                bots.append({
                    "id": bot_info.get("botId", ""),
                    "name": bot_info.get("name", f"Bot {bot_info.get('botId', '')}"),
                    "labId": bot_info.get("labId", ""),
                    "accountId": bot_info.get("accountId", ""),
                    "status": "active" if bot_info.get("isActive", False) else "inactive",
                    "performance": {
                        "totalReturn": float(stats.get("totalReturn", 0)),
                        "sharpeRatio": float(stats.get("sharpeRatio", 0)),
                        "maxDrawdown": float(stats.get("maxDrawdown", 0)),
                        "winRate": float(stats.get("winRate", 0)),
                        "profitFactor": float(stats.get("profitFactor", 0)),
                        "totalTrades": int(stats.get("totalTrades", 0)),
                        "avgTradeReturn": float(stats.get("avgTradeReturn", 0)),
                        "volatility": float(stats.get("volatility", 0)),
                        "calmarRatio": float(stats.get("calmarRatio", 0)),
                        "sortinoRatio": float(stats.get("sortinoRatio", 0))
                    },
                    "createdAt": bot_info.get("createdAt", "2025-01-13T00:00:00Z")
                })
        
        return APIResponse(
            success=True,
            data=bots,
            timestamp="2025-01-13T00:00:00Z"
        )
        
    except Exception as e:
        logger.error(f"Get bots failed: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/markets")
async def get_all_markets():
    try:
        if not haas_executor:
            return APIResponse(
                success=False,
                error="HaasOnline API not connected",
                timestamp="2025-01-13T00:00:00Z"
            )
        
        # Get markets from HaasOnline using the correct API method
        from pyHaasAPI.api import get_all_markets
        markets_data = get_all_markets(haas_executor)
        
        # Convert to our format
        markets = []
        if markets_data and isinstance(markets_data, list):
            for market_info in markets_data:
                markets.append({
                    "id": f"{market_info.get('price_source', '')}_{market_info.get('primary', '')}_{market_info.get('secondary', '')}",
                    "symbol": f"{market_info.get('primary', '')}/{market_info.get('secondary', '')}",
                    "baseAsset": market_info.get("primary", ""),
                    "quoteAsset": market_info.get("secondary", ""),
                    "exchange": market_info.get("price_source", ""),
                    "price": 0,  # Would need separate price call
                    "volume24h": 0,  # Would need separate volume call
                    "change24h": 0,  # Would need separate change call
                    "changePercent24h": 0,
                    "high24h": 0,
                    "low24h": 0,
                    "category": {
                        "primary": "crypto",
                        "tags": []
                    },
                    "status": "active",
                    "lastUpdated": "2025-01-13T00:00:00Z"
                })
        
        return APIResponse(
            success=True,
            data=markets,
            timestamp="2025-01-13T00:00:00Z"
        )
        
    except Exception as e:
        logger.error(f"Get markets failed: {e}")
        return APIResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

if __name__ == "__main__":
    uvicorn.run(
        "simple_api_bridge:app",
        host="127.0.0.1",
        port=3002,
        reload=False,
        log_level="info"
    )