#!/usr/bin/env python3
"""
Test script to verify MCP server connection and basic functionality
"""

import asyncio
import sys
import os
sys.path.append('.')

from mcp_server.server import HaasMCPServer

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🧪 Testing HaasOnline MCP Server")
    print("=" * 50)
    
    try:
        # Initialize server
        server = HaasMCPServer()
        print(f"✓ Server initialized")
        print(f"✓ API connected: {bool(server.haas_executor)}")
        
        if not server.haas_executor:
            print("❌ Cannot test tools without API connection")
            return
        
        # Test status tool
        print("\n🔍 Testing get_haas_status tool...")
        result = await server._execute_tool("get_haas_status", {})
        print(f"✓ Status result: {result}")
        
        # Test accounts tool
        print("\n👥 Testing get_all_accounts tool...")
        result = await server._execute_tool("get_all_accounts", {})
        print(f"✓ Found {len(result.get('data', []))} accounts")
        
        # Test labs tool
        print("\n🧪 Testing get_all_labs tool...")
        result = await server._execute_tool("get_all_labs", {})
        print(f"✓ Found {len(result.get('data', []))} labs")
        
        # Test markets tool
        print("\n📈 Testing get_all_markets tool...")
        result = await server._execute_tool("get_all_markets", {})
        print(f"✓ Found {len(result.get('data', []))} markets")
        
        print("\n🎉 All tests passed! MCP server is ready for Kiro.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())