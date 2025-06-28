#!/usr/bin/env python3
"""
Simple test client for the HaasOnline MCP Server
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

class MCPTestClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
    
    async def start_server(self):
        """Start the MCP server as a subprocess"""
        self.process = subprocess.Popen(
            [sys.executable, "-u", "mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("🚀 Started MCP server")
        # Read and discard the initial handshake message
        handshake = self.process.stdout.readline()
        print(f"🤝 MCP server handshake: {handshake.strip()}")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        print(f"📤 Sending: {request_json.strip()}")
        
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"📥 Received: {json.dumps(response, indent=2)}")
            self.request_id += 1
            return response
        else:
            print("❌ No response received")
            return {"error": "No response"}
    
    async def test_basic_functionality(self):
        """Test basic MCP server functionality"""
        print("\n🧪 Testing MCP Server Functionality\n")
        
        # Test 1: Initialize
        print("1️⃣ Testing initialization...")
        init_response = await self.send_request("initialize", {
            "host": "127.0.0.1",
            "port": 8090,
            "email": "your_email@example.com",
            "password": "your_password"
        })
        
        if "error" in init_response:
            print(f"❌ Initialization failed: {init_response['error']}")
            return False
        
        print("✅ Initialization successful")
        
        # Test 2: Get scripts
        print("\n2️⃣ Testing get_scripts...")
        scripts_response = await self.send_request("get_scripts")
        if "error" in scripts_response:
            print(f"❌ Get scripts failed: {scripts_response['error']}")
        else:
            print(f"✅ Found {len(scripts_response['result']['scripts'])} scripts")
        
        # Test 3: Get markets
        print("\n3️⃣ Testing get_markets...")
        markets_response = await self.send_request("get_markets")
        if "error" in markets_response:
            print(f"❌ Get markets failed: {markets_response['error']}")
        else:
            print(f"✅ Found {len(markets_response['result']['markets'])} markets")
        
        # Test 4: Get accounts
        print("\n4️⃣ Testing get_accounts...")
        accounts_response = await self.send_request("get_accounts")
        if "error" in accounts_response:
            print(f"❌ Get accounts failed: {accounts_response['error']}")
        else:
            print(f"✅ Found {len(accounts_response['result']['accounts'])} accounts")
        
        return True
    
    async def cleanup(self):
        """Clean up the server process"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("🛑 MCP server stopped")

async def main():
    client = MCPTestClient()
    
    try:
        await client.start_server()
        success = await client.test_basic_functionality()
        
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
