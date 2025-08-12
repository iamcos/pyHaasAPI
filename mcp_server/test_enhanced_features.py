#!/usr/bin/env python3
"""
Enhanced test script for the comprehensive HaasOnline MCP Server
Tests all the new features and tools added to the server
"""

import asyncio
import sys
import os
sys.path.append('.')

from mcp_server.server import HaasMCPServer

async def test_enhanced_mcp_server():
    """Test the enhanced MCP server functionality"""
    print("🚀 Testing Enhanced HaasOnline MCP Server")
    print("=" * 60)
    
    try:
        # Initialize server
        server = HaasMCPServer()
        print(f"✓ Server initialized")
        print(f"✓ API connected: {bool(server.haas_executor)}")
        
        if not server.haas_executor:
            print("❌ Cannot test tools without API connection")
            return
        
        # Test basic status
        print("\n🔍 Testing basic status...")
        result = await server._execute_tool("get_haas_status", {})
        print(f"✓ Status: {result['status']}")
        
        # Test account management
        print("\n👥 Testing account management...")
        accounts_result = await server._execute_tool("get_all_accounts", {})
        accounts = accounts_result.get('data', [])
        print(f"✓ Found {len(accounts)} accounts")
        
        if accounts:
            account_id = accounts[0].get('AID')
            if account_id:
                balance_result = await server._execute_tool("get_account_balance", {"account_id": account_id})
                print(f"✓ Account balance retrieved")
                
                account_data_result = await server._execute_tool("get_account_data", {"account_id": account_id})
                print(f"✓ Account data retrieved")
        
        # Test lab management
        print("\n🧪 Testing lab management...")
        labs_result = await server._execute_tool("get_all_labs", {})
        labs = labs_result.get('data', [])
        print(f"✓ Found {len(labs)} labs")
        
        if labs:
            # Handle both dict and pydantic model formats
            lab = labs[0]
            lab_id = getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            if hasattr(lab, 'model_dump'):
                lab_dict = lab.model_dump()
                lab_id = lab_dict.get('lab_id') or lab_dict.get('LID')
            
            if lab_id:
                lab_details_result = await server._execute_tool("get_lab_details", {"lab_id": lab_id})
                print(f"✓ Lab details retrieved for lab {lab_id}")
                
                # Test parameter range optimization
                try:
                    param_result = await server._execute_tool("update_lab_parameter_ranges", {
                        "lab_id": lab_id, 
                        "randomize": True
                    })
                    print(f"✓ Parameter ranges updated for lab {lab_id}")
                except Exception as e:
                    print(f"⚠ Parameter range update failed: {e}")
        
        # Test bot management
        print("\n🤖 Testing bot management...")
        bots_result = await server._execute_tool("get_all_bots", {})
        bots = bots_result.get('data', [])
        print(f"✓ Found {len(bots)} bots")
        
        if bots:
            # Handle both dict and pydantic model formats
            bot = bots[0]
            bot_id = getattr(bot, 'bot_id', None) or getattr(bot, 'BID', None)
            if hasattr(bot, 'model_dump'):
                bot_dict = bot.model_dump()
                bot_id = bot_dict.get('bot_id') or bot_dict.get('BID')
            
            if bot_id:
                bot_details_result = await server._execute_tool("get_bot_details", {"bot_id": bot_id})
                print(f"✓ Bot details retrieved for bot {bot_id}")
        
        # Test script management
        print("\n📜 Testing script management...")
        scripts_result = await server._execute_tool("get_all_scripts", {})
        scripts = scripts_result.get('data', [])
        print(f"✓ Found {len(scripts)} scripts")
        
        if scripts:
            # Handle both dict and pydantic model formats
            script = scripts[0]
            script_id = None
            if isinstance(script, dict):
                script_id = script.get('script_id') or script.get('SID') or script.get('I')
            else:
                script_id = getattr(script, 'script_id', None) or getattr(script, 'SID', None) or getattr(script, 'I', None)
                if hasattr(script, 'model_dump'):
                    script_dict = script.model_dump()
                    script_id = script_dict.get('script_id') or script_dict.get('SID') or script_dict.get('I')
            
            if script_id:
                script_details_result = await server._execute_tool("get_script_details", {"script_id": script_id})
                print(f"✓ Script details retrieved for script {script_id}")
        
        # Test market data
        print("\n📈 Testing market data...")
        markets_result = await server._execute_tool("get_all_markets", {})
        markets = markets_result.get('data', [])
        print(f"✓ Found {len(markets)} markets")
        
        if markets:
            # Try to get market data for a common market
            test_markets = ["BINANCE_BTC_USDT", "BINANCE_ETH_USDT"]
            for market in test_markets:
                try:
                    price_result = await server._execute_tool("get_market_price", {"market": market})
                    print(f"✓ Price retrieved for {market}")
                    
                    orderbook_result = await server._execute_tool("get_order_book", {"market": market, "depth": 5})
                    print(f"✓ Order book retrieved for {market}")
                    break
                except Exception as e:
                    print(f"⚠ Market data failed for {market}: {e}")
        
        # Test history intelligence (if available)
        print("\n🧠 Testing history intelligence...")
        try:
            history_result = await server._execute_tool("get_history_summary", {})
            if history_result.get('success'):
                print(f"✓ History intelligence available")
                
                if labs:
                    # Handle both dict and pydantic model formats
                    lab = labs[0]
                    lab_id = getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
                    if hasattr(lab, 'model_dump'):
                        lab_dict = lab.model_dump()
                        lab_id = lab_dict.get('lab_id') or lab_dict.get('LID')
                    
                    if lab_id:
                        cutoff_result = await server._execute_tool("discover_cutoff_date", {"lab_id": lab_id})
                        print(f"✓ Cutoff discovery tested for lab {lab_id}")
            else:
                print(f"⚠ History intelligence not available: {history_result.get('error')}")
        except Exception as e:
            print(f"⚠ History intelligence test failed: {e}")
        
        print("\n🎉 Enhanced MCP server testing complete!")
        tool_count = await server._get_tool_list()
        print(f"📊 Total tools available: {tool_count}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def server_get_tool_list(server):
    """Helper to get tool list count"""
    try:
        tools = await server.server.list_tools()
        return len(tools) if hasattr(tools, '__len__') else 0
    except:
        return 0

# Monkey patch the helper method
HaasMCPServer._get_tool_list = server_get_tool_list

if __name__ == "__main__":
    asyncio.run(test_enhanced_mcp_server())