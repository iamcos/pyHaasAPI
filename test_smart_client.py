#!/usr/bin/env python3
"""
Simple test version of Smart MCP Client
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyD2vkEUotXaNia4xgG7rMVJOOp24gkU8V8"
genai.configure(api_key=GEMINI_API_KEY)

class TestSmartMCPClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Local cache for data
        self.scripts_cache = []
        self.markets_cache = []
        self.accounts_cache = []
    
    async def start_server(self):
        """Start the MCP server as a subprocess"""
        print("🚀 Starting MCP server...")
        self.process = subprocess.Popen(
            [sys.executable, "-u", "mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("✅ MCP server started")
        
        # Read and discard the initial handshake message
        handshake = self.process.stdout.readline()
        print(f"🤝 MCP server handshake: {handshake.strip()}")
        
        # Initialize the server
        print("🔧 Initializing server...")
        await self.send_request("initialize", {
            "host": "127.0.0.1",
            "port": 8090,
            "email": "garrypotterr@gmail.com",
            "password": "IQYTCQJIQYTCQJ"
        })
        print("✅ Server initialized")
        
        # Test basic functionality
        await self.test_basic_functionality()
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        print(f"📤 Sending: {method}")
        
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            print(f"📥 Received response for {method}")
            self.request_id += 1
            return response
        else:
            print("❌ No response received")
            return {"error": "No response"}
    
    async def test_basic_functionality(self):
        """Test basic functionality"""
        print("\n🧪 Testing basic functionality...")
        
        # Test 1: Get scripts (limited)
        print("\n1️⃣ Testing get_scripts...")
        scripts_response = await self.send_request("get_scripts")
        if "result" in scripts_response:
            self.scripts_cache = scripts_response["result"]["scripts"][:10]  # Limit to 10
            print(f"✅ Loaded {len(self.scripts_cache)} scripts")
        
        # Test 2: Get accounts
        print("\n2️⃣ Testing get_accounts...")
        accounts_response = await self.send_request("get_accounts")
        if "result" in accounts_response:
            self.accounts_cache = accounts_response["result"]["accounts"]
            print(f"✅ Loaded {len(self.accounts_cache)} accounts")
        
        # Test 3: Get markets (NO LIMIT)
        print("\n3️⃣ Testing get_markets...")
        markets_response = await self.send_request("get_markets")
        if "result" in markets_response:
            self.markets_cache = markets_response["result"]["markets"]  # No limit
            print(f"✅ Loaded {len(self.markets_cache)} markets")
            sample_markets = [f"{m['primary']}/{m['secondary']} on {m['price_source']}" for m in self.markets_cache[:5]]
            print(f"📝 Sample markets: {sample_markets}")
        
        print("\n✅ Basic functionality test completed!")
        
        # Debug: Print first few entries of each cache
        print("\n🔍 Debug: First few markets:")
        for i, market in enumerate(self.markets_cache[:3]):
            print(f"  {i+1}. {market}")
        
        print("\n🔍 Debug: First few scripts:")
        for i, script in enumerate(self.scripts_cache[:3]):
            print(f"  {i+1}. {script}")
        
        # Show sample data
        if self.scripts_cache:
            print(f"\n📝 Sample script: {self.scripts_cache[0]['script_name']}")
        if self.markets_cache:
            print(f"📈 Sample market: {self.markets_cache[0]['primary']}/{self.markets_cache[0]['secondary']}")
        if self.accounts_cache:
            print(f"💰 Sample account keys: {list(self.accounts_cache[0].keys())}")
            # Try common keys for account name
            acc = self.accounts_cache[0]
            acc_name = acc.get('account_name') or acc.get('name') or acc.get('label') or str(acc)
            print(f"💰 Sample account: {acc_name}")
    
    def search_markets(self, query: str) -> List[Dict[str, Any]]:
        """Search markets locally using the query (supports pairs and fuzzy)"""
        query = query.strip().upper()
        results = []
        # Support pair search like BTC/USDT
        if "/" in query:
            base, quote = query.split("/")
            for market in self.markets_cache:
                if market["primary"].upper() == base and market["secondary"].upper() == quote:
                    results.append(market)
        else:
            for market in self.markets_cache:
                if (query in market["primary"].upper() or 
                    query in market["secondary"].upper() or 
                    query in market["price_source"].upper()):
                    results.append(market)
        return results[:20]  # Show more results, but still limit for display
    
    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """Search scripts locally using the query"""
        query = query.lower()
        results = []
        
        for script in self.scripts_cache:
            if query in script["script_name"].lower():
                results.append(script)
        
        return results[:5]  # Limit results
    
    async def test_local_search(self):
        """Test local search functionality"""
        print("\n🔍 Testing local search...")
        
        # Test market search
        btc_markets = self.search_markets("BTC")
        print(f"🔍 Found {len(btc_markets)} BTC markets:")
        for market in btc_markets:
            print(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")
        
        # Test script search
        scalper_scripts = self.search_scripts("scalper")
        print(f"🤖 Found {len(scalper_scripts)} scalper scripts:")
        for script in scalper_scripts:
            print(f"  • {script['script_name']}")
    
    async def test_gemini_integration(self):
        """Test Gemini integration"""
        print("\n🤖 Testing Gemini integration...")
        
        try:
            context_prompt = """
            You are helping with a legitimate HaasOnline trading bot development and analysis system. 
            
            Context:
            - This is a professional trading bot platform (HaasOnline) used by legitimate traders
            - The user is developing and testing trading strategies in a controlled environment
            - This is for educational and professional trading bot development purposes
            - All trading is done through proper APIs and regulated exchanges
            - The goal is to help users understand market analysis and bot configuration
            
            Available data:
            - 12,243 markets across multiple exchanges (Binance, Coinbase, Kraken, etc.)
            - Various trading scripts including scalpers, RSI, MACD, EMA strategies
            - Backtesting capabilities for strategy validation
            - Parameter optimization tools
            
            Your role:
            - Help users find appropriate markets for their strategies
            - Suggest suitable trading scripts based on their goals
            - Provide guidance on parameter optimization
            - Explain trading concepts and best practices
            - Help with backtesting and analysis
            
            This is legitimate trading bot development, not gambling or illegal trading.
            Please provide helpful, professional advice for trading bot development and market analysis.
            """
            
            user_query = "I want to find BTC markets and scalper scripts for developing a trading bot. What should I look for?"
            
            response = self.model.generate_content(context_prompt + "\n\nUser query: " + user_query)
            print(f"🤖 Gemini response: {response.text[:300]}...")
            print("✅ Gemini integration working!")
        except Exception as e:
            print(f"❌ Gemini integration failed: {e}")
    
    async def interactive_test(self):
        """Simple interactive test"""
        print("\n🎯 Interactive Test Mode")
        print("Type 'search btc' to search BTC markets")
        print("Type 'search scalper' to search scalper scripts")
        print("Type 'ask gemini' to ask Gemini for trading advice")
        print("Type 'quit' to exit")
        
        # Context prompt for Gemini
        gemini_context = """
        You are helping with a legitimate HaasOnline trading bot development and analysis system. 
        
        Context:
        - This is a professional trading bot platform (HaasOnline) used by legitimate traders
        - The user is developing and testing trading strategies in a controlled environment
        - This is for educational and professional trading bot development purposes
        - All trading is done through proper APIs and regulated exchanges
        - The goal is to help users understand market analysis and bot configuration
        
        Available data:
        - 12,243 markets across multiple exchanges (Binance, Coinbase, Kraken, etc.)
        - Various trading scripts including scalpers, RSI, MACD, EMA strategies
        - Backtesting capabilities for strategy validation
        - Parameter optimization tools
        
        Your role:
        - Help users find appropriate markets for their strategies
        - Suggest suitable trading scripts based on their goals
        - Provide guidance on parameter optimization
        - Explain trading concepts and best practices
        - Help with backtesting and analysis
        
        This is legitimate trading bot development, not gambling or illegal trading.
        Please provide helpful, professional advice for trading bot development and market analysis.
        """
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip().lower()
                
                if user_input == 'quit':
                    break
                elif user_input.startswith('search btc'):
                    markets = self.search_markets("BTC")
                    print(f"🔍 Found {len(markets)} BTC markets:")
                    for market in markets:
                        print(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")
                elif user_input.startswith('search scalper'):
                    scripts = self.search_scripts("scalper")
                    print(f"🤖 Found {len(scripts)} scalper scripts:")
                    for script in scripts:
                        print(f"  • {script['script_name']}")
                elif user_input.startswith('ask gemini'):
                    question = input("🤖 What would you like to ask Gemini? ")
                    try:
                        response = self.model.generate_content(gemini_context + "\n\nUser question: " + question)
                        print(f"🤖 Gemini: {response.text}")
                    except Exception as e:
                        print(f"❌ Gemini error: {e}")
                else:
                    print("❓ Unknown command. Try 'search btc', 'search scalper', 'ask gemini', or 'quit'")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    async def cleanup(self):
        """Clean up the server process"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("🛑 MCP server stopped")

async def main():
    client = TestSmartMCPClient()
    
    try:
        await client.start_server()
        await client.test_local_search()
        await client.test_gemini_integration()
        await client.interactive_test()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 