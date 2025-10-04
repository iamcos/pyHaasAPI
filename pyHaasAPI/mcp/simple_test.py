#!/usr/bin/env python3
"""
Simple test for Cursor MCP Server
"""

import asyncio
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_simple():
    """Simple test of the MCP server components"""
    try:
        print("🔌 Testing Cursor MCP Server Components")
        print("=" * 50)
        
        # Test 1: Check if we can import the modules
        print("📦 Testing imports...")
        
        # Add the parent directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        sys.path.insert(0, parent_dir)
        
        try:
            from pyHaasAPI.mcp.cursor_mcp_server import CursorPyHaasAPIMCPServer
            print("✅ CursorPyHaasAPIMCPServer imported successfully")
        except Exception as e:
            print(f"❌ Failed to import CursorPyHaasAPIMCPServer: {e}")
            return
        
        try:
            from pyHaasAPI.mcp.cursor_mcp_handlers import handle_list_available_servers
            print("✅ MCP handlers imported successfully")
        except Exception as e:
            print(f"❌ Failed to import MCP handlers: {e}")
            return
        
        # Test 2: Check environment variables
        print("\n🔐 Testing environment variables...")
        api_email = os.getenv('API_EMAIL')
        api_password = os.getenv('API_PASSWORD')
        
        if api_email and api_password:
            print(f"✅ API credentials found: {api_email}")
        else:
            print("⚠️  API credentials not found in .env file")
            print("Please create a .env file with:")
            print("API_EMAIL=your_email@example.com")
            print("API_PASSWORD=your_password")
            return
        
        # Test 3: Initialize server
        print("\n📡 Testing server initialization...")
        try:
            server = CursorPyHaasAPIMCPServer()
            await server.initialize()
            print("✅ Server initialized successfully")
            
            # Test server listing
            print("\n📋 Testing server listing...")
            result = await handle_list_available_servers()
            print(f"✅ Server listing result: {result[0].text[:100]}...")
            
            await server.cleanup()
            print("\n✅ All tests passed successfully!")
            print("\n🎯 The Cursor MCP server is ready to use!")
            
        except Exception as e:
            print(f"❌ Server initialization failed: {e}")
            print("\n🔧 This might be due to:")
            print("1. Missing SSH access to servers")
            print("2. Incorrect credentials")
            print("3. Network connectivity issues")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have the correct credentials in .env file")
        print("2. Check that you have SSH access to the servers")
        print("3. Verify all dependencies are installed")

if __name__ == "__main__":
    print("🚀 Simple Cursor MCP Server Test")
    print("This will test the basic components of the Cursor MCP server")
    print()
    
    asyncio.run(test_simple())
