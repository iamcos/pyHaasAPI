#!/usr/bin/env python3
"""
Test script for Cursor MCP Server

This script tests the Cursor MCP server with server manager integration.
"""

import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_cursor_mcp_server():
    """Test the Cursor MCP server"""
    try:
        print("🔌 Testing Cursor MCP Server with Server Manager")
        print("=" * 60)
        
        # Import the Cursor MCP server
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from cursor_mcp_server import cursor_mcp_server_instance
        
        # Initialize server
        print("📡 Initializing Cursor MCP server...")
        await cursor_mcp_server_instance.initialize()
        print("✅ Server initialized successfully")
        
        # Test server listing
        print("\n📋 Testing server listing...")
        from cursor_mcp_handlers import handle_list_available_servers
        servers_result = await handle_list_available_servers()
        print(f"✅ Available servers: {servers_result[0].text}")
        
        # Test connecting to srv01
        print("\n🔗 Testing connection to srv01...")
        from cursor_mcp_handlers import handle_connect_to_server
        connect_result = await handle_connect_to_server({"server_name": "srv01"})
        print(f"✅ Connection result: {connect_result[0].text}")
        
        # Test listing labs
        print("\n📊 Testing lab listing...")
        from cursor_mcp_handlers import handle_list_labs
        labs_result = await handle_list_labs()
        if labs_result and labs_result[0].text:
            labs_data = json.loads(labs_result[0].text)
            print(f"✅ Found {len(labs_data)} labs")
            
            # Show first few labs
            print("\n📋 Sample labs:")
            for i, lab in enumerate(labs_data[:3]):
                print(f"  {i+1}. {lab.get('name', 'Unknown')} (ID: {lab.get('lab_id', 'Unknown')})")
        else:
            print("⚠️  No labs found or error occurred")
        
        # Test market data
        print("\n📈 Testing market data...")
        from cursor_mcp_handlers import handle_get_markets
        markets_result = await handle_get_markets()
        if markets_result and markets_result[0].text:
            markets_data = json.loads(markets_result[0].text)
            print(f"✅ Found {len(markets_data)} markets")
        else:
            print("⚠️  No markets found")
        
        # Cleanup
        await cursor_mcp_server_instance.cleanup()
        print("\n✅ Cursor MCP server test completed successfully!")
        print("\n🎯 The Cursor MCP server is ready to use!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have the correct credentials in .env file")
        print("2. Check that the server manager can connect to srv01")
        print("3. Verify all dependencies are installed")

if __name__ == "__main__":
    print("🚀 Cursor MCP Server Test")
    print("This will test the Cursor MCP server with server manager integration")
    print()
    
    asyncio.run(test_cursor_mcp_server())
