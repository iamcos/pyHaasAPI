#!/usr/bin/env python3
"""
HTTP Bridge for MCP Server
Wraps the stdio MCP server with an HTTP interface for web frontend integration.
"""

import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-http-bridge")

app = FastAPI(title="HaasOnline MCP HTTP Bridge", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCPRequest(BaseModel):
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str

class MCPBridge:
    def __init__(self):
        self.mcp_process = None
        self.request_id = 0
    
    async def start_mcp_server(self):
        """Start the MCP server process"""
        try:
            # Start the MCP server as a subprocess
            self.mcp_process = await asyncio.create_subprocess_exec(
                sys.executable, "server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="."
            )
            logger.info("MCP server process started")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        if not self.mcp_process:
            await self.start_mcp_server()
        
        self.request_id += 1
        
        # Format request according to MCP protocol
        if method == "tools/call":
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "tools/call",
                "params": params or {}
            }
        else:
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method,
                "params": params or {}
            }
        
        try:
            # Send request to MCP server
            request_json = json.dumps(request) + "\n"
            self.mcp_process.stdin.write(request_json.encode())
            await self.mcp_process.stdin.drain()
            
            # Read response
            response_line = await self.mcp_process.stdout.readline()
            if not response_line:
                raise Exception("No response from MCP server")
            
            response = json.loads(response_line.decode().strip())
            
            if "error" in response:
                raise Exception(response["error"]["message"])
            
            return response.get("result", {})
        
        except Exception as e:
            logger.error(f"MCP request failed: {e}")
            raise
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.mcp_process:
            self.mcp_process.terminate()
            await self.mcp_process.wait()

# Global bridge instance
bridge = MCPBridge()

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP bridge on startup"""
    try:
        await bridge.start_mcp_server()
        logger.info("MCP HTTP Bridge started successfully")
    except Exception as e:
        logger.error(f"Failed to start MCP bridge: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    await bridge.stop()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return MCPResponse(
        success=True,
        data={
            "status": "healthy",
            "services": {
                "mcp": bridge.mcp_process is not None,
                "haas": True  # Will be determined by actual MCP call
            },
            "timestamp": "2025-01-13T00:00:00Z"
        },
        timestamp="2025-01-13T00:00:00Z"
    )

# HaasOnline API endpoints
@app.get("/api/haas/status")
async def get_haas_status():
    try:
        result = await bridge.send_request("tools/call", {
            "name": "get_haas_status",
            "arguments": {}
        })
        return MCPResponse(
            success=True,
            data=result,
            timestamp="2025-01-13T00:00:00Z"
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/accounts")
async def get_all_accounts():
    try:
        result = await bridge.send_request("tools/call", {
            "name": "get_all_accounts",
            "arguments": {}
        })
        return MCPResponse(
            success=True,
            data=result,
            timestamp="2025-01-13T00:00:00Z"
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/labs")
async def get_all_labs():
    try:
        result = await bridge.send_request("tools/call", {
            "name": "get_all_labs",
            "arguments": {}
        })
        return MCPResponse(
            success=True,
            data=result,
            timestamp="2025-01-13T00:00:00Z"
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/bots")
async def get_all_bots():
    try:
        result = await bridge.send_request("tools/call", {
            "name": "get_all_bots",
            "arguments": {}
        })
        return MCPResponse(
            success=True,
            data=result,
            timestamp="2025-01-13T00:00:00Z"
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

@app.get("/api/markets")
async def get_all_markets():
    try:
        result = await bridge.send_request("tools/call", {
            "name": "get_all_markets",
            "arguments": {}
        })
        return MCPResponse(
            success=True,
            data=result,
            timestamp="2025-01-13T00:00:00Z"
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

# Generic tool call endpoint
@app.post("/api/tools/call")
async def call_tool(request: MCPRequest):
    try:
        result = await bridge.send_request("tools/call", {
            "name": request.method,
            "arguments": request.params or {}
        })
        return MCPResponse(
            success=True,
            data=result,
            timestamp="2025-01-13T00:00:00Z"
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=str(e),
            timestamp="2025-01-13T00:00:00Z"
        )

if __name__ == "__main__":
    uvicorn.run(
        "http_bridge:app",
        host="127.0.0.1",
        port=3001,
        reload=False,
        log_level="info"
    )