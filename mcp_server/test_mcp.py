#!/usr/bin/env python3
"""
Test script for HaasOnline MCP Server
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

async def test_mcp_server():
    """Test the MCP server by calling it directly"""
    
    # Test message to list tools
    test_message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        # Start the MCP server process
        process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="."
        )
        
        # Send the test message
        input_data = json.dumps(test_message) + "\n"
        stdout, stderr = process.communicate(input=input_data, timeout=10)
        
        print("STDOUT:")
        print(stdout)
        print("\nSTDERR:")
        print(stderr)
        print(f"\nReturn code: {process.returncode}")
        
    except subprocess.TimeoutExpired:
        print("Process timed out")
        process.kill()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())