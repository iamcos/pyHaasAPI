#!/usr/bin/env python3
"""
Local Search Client for HaasOnline API

This client focuses on local processing of markets and scripts data,
providing fast search capabilities without heavy API calls.

Usage:
    python local_search_client.py
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

class LocalSearchClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Local cache for data
        self.scripts_cache = []
        self.markets_cache = []
        self.accounts_cache = []
        
        # Search indexes for fast lookup
        self.market_index = {}
        self.script_index = {}
    
    async def start_server(self):
        """Start the MCP server and load data once"""
        print("🚀 Starting MCP server...")
        self.process = subprocess.Popen(
            [sys.executable, "-u", "mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Read handshake
        handshake = self.process.stdout.readline()
        print("✅ MCP server started")
        
        # Initialize once
        await self.send_request("initialize", {
            "host": "127.0.0.1",
            "port": 8090,
            "email": "garrypotterr@gmail.com",
            "password": "IQYTCQJIQYTCQJ"
        })
        
        # Load all data once
        await self.load_all_data()
        
        # Build search indexes
        self.build_search_indexes()
        
        print("✅ Local search client ready!")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        if response_line:
            response = json.loads(response_line.strip())
            self.request_id += 1
            return response
        else:
            return {"error": "No response"}
    
    async def load_all_data(self):
        """Load all data once for local processing"""
        print("📊 Loading data for local processing...")
        
        # Load scripts
        print("  📝 Loading scripts...")
        scripts_response = await self.send_request("get_scripts")
        if "result" in scripts_response:
            self.scripts_cache = scripts_response["result"]["scripts"]
            print(f"    ✅ Loaded {len(self.scripts_cache)} scripts")
        
        # Load accounts
        print("  💰 Loading accounts...")
        accounts_response = await self.send_request("get_accounts")
        if "result" in accounts_response:
            self.accounts_cache = accounts_response["result"]["accounts"]
            print(f"    ✅ Loaded {len(self.accounts_cache)} accounts")
        
        # Load markets (all of them for comprehensive search)
        print("  📈 Loading markets...")
        markets_response = await self.send_request("get_markets")
        if "result" in markets_response:
            self.markets_cache = markets_response["result"]["markets"]
            print(f"    ✅ Loaded {len(self.markets_cache)} markets")
        
        print("✅ All data loaded for local processing")
    
    def build_search_indexes(self):
        """Build fast search indexes"""
        print("🔍 Building search indexes...")
        
        # Build market index
        for market in self.markets_cache:
            primary = market["primary"].upper()
            secondary = market["secondary"].upper()
            source = market["price_source"].upper()
            
            # Index by primary currency
            if primary not in self.market_index:
                self.market_index[primary] = []
            self.market_index[primary].append(market)
            
            # Index by secondary currency
            if secondary not in self.market_index:
                self.market_index[secondary] = []
            self.market_index[secondary].append(market)
            
            # Index by exchange
            if source not in self.market_index:
                self.market_index[source] = []
            self.market_index[source].append(market)
        
        # Build script index
        for script in self.scripts_cache:
            name = script["script_name"].lower()
            words = name.split()
            
            for word in words:
                if word not in self.script_index:
                    self.script_index[word] = []
                self.script_index[word].append(script)
        
        print(f"✅ Built indexes: {len(self.market_index)} market keys, {len(self.script_index)} script keys")
    
    def fast_market_search(self, query: str) -> List[Dict[str, Any]]:
        """Fast market search using indexes"""
        query = query.upper()
        results = []
        
        # Direct index lookup
        if query in self.market_index:
            results.extend(self.market_index[query])
        
        # Partial matches
        for key, markets in self.market_index.items():
            if query in key and key not in results:
                results.extend(markets)
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for market in results:
            market_id = f"{market['primary']}_{market['secondary']}_{market['price_source']}"
            if market_id not in seen:
                seen.add(market_id)
                unique_results.append(market)
        
        return unique_results[:20]  # Limit results
    
    def fast_script_search(self, query: str) -> List[Dict[str, Any]]:
        """Fast script search using indexes"""
        query = query.lower()
        results = []
        
        # Direct index lookup
        if query in self.script_index:
            results.extend(self.script_index[query])
        
        # Partial matches
        for key, scripts in self.script_index.items():
            if query in key and key not in results:
                results.extend(scripts)
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for script in results:
            if script["script_id"] not in seen:
                seen.add(script["script_id"])
                unique_results.append(script)
        
        return unique_results[:10]  # Limit results
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Get summary of available markets"""
        exchanges = {}
        currencies = {}
        
        for market in self.markets_cache:
            # Count by exchange
            source = market["price_source"]
            exchanges[source] = exchanges.get(source, 0) + 1
            
            # Count by primary currency
            primary = market["primary"]
            currencies[primary] = currencies.get(primary, 0) + 1
        
        return {
            "total_markets": len(self.markets_cache),
            "exchanges": dict(sorted(exchanges.items(), key=lambda x: x[1], reverse=True)[:10]),
            "top_currencies": dict(sorted(currencies.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def get_script_summary(self) -> Dict[str, Any]:
        """Get summary of available scripts"""
        script_types = {}
        
        for script in self.scripts_cache:
            name = script["script_name"].lower()
            
            # Categorize scripts
            if "scalper" in name:
                script_types["scalper"] = script_types.get("scalper", 0) + 1
            elif "rsi" in name:
                script_types["rsi"] = script_types.get("rsi", 0) + 1
            elif "macd" in name:
                script_types["macd"] = script_types.get("macd", 0) + 1
            elif "ema" in name:
                script_types["ema"] = script_types.get("ema", 0) + 1
            else:
                script_types["other"] = script_types.get("other", 0) + 1
        
        return {
            "total_scripts": len(self.scripts_cache),
            "script_types": script_types
        }
    
    async def process_user_query(self, query: str) -> str:
        """Process user query using local search and Gemini"""
        try:
            # First, do local searches
            local_results = {}
            
            # Market search
            market_keywords = ["market", "btc", "eth", "usdt", "usdc", "eur", "binance", "kraken", "coinbase"]
            for keyword in market_keywords:
                if keyword.lower() in query.lower():
                    markets = self.fast_market_search(keyword)
                    if markets:
                        local_results["markets"] = markets
                        break
            
            # Script search
            script_keywords = ["script", "bot", "scalper", "rsi", "macd", "ema", "strategy"]
            for keyword in script_keywords:
                if keyword.lower() in query.lower():
                    scripts = self.fast_script_search(keyword)
                    if scripts:
                        local_results["scripts"] = scripts
                        break
            
            # Get Gemini response
            context = f"""
            You are helping with a HaasOnline trading bot system. 
            
            Available data:
            - {len(self.markets_cache)} markets across multiple exchanges
            - {len(self.scripts_cache)} trading scripts
            - {len(self.accounts_cache)} trading accounts
            
            User query: {query}
            
            Local search results: {json.dumps(local_results, indent=2)}
            
            Provide helpful advice about trading strategies, market selection, and bot configuration.
            Be specific and actionable.
            """
            
            response = self.model.generate_content(context)
            gemini_response = response.text
            
            # Combine results
            final_response = [gemini_response]
            
            if local_results:
                final_response.append("\n🔍 Local Search Results:")
                
                if "markets" in local_results:
                    final_response.append(f"\n📈 Found {len(local_results['markets'])} markets:")
                    for market in local_results["markets"][:5]:
                        final_response.append(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")
                
                if "scripts" in local_results:
                    final_response.append(f"\n🤖 Found {len(local_results['scripts'])} scripts:")
                    for script in local_results["scripts"][:5]:
                        final_response.append(f"  • {script['script_name']}")
            
            return "\n".join(final_response)
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
    
    async def interactive_mode(self):
        """Run interactive mode"""
        print("\n🔍 Local Search Client - Interactive Mode")
        print("Type 'quit' to exit, 'help' for commands, 'summary' for data overview")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print("\n📚 Available commands:")
                    print("  • 'summary' - Show data overview")
                    print("  • 'search btc' - Search BTC markets")
                    print("  • 'search scalper' - Search scalper scripts")
                    print("  • 'find eth markets' - Find ETH markets")
                    print("  • Any trading question - Get AI advice")
                    continue
                elif user_input.lower() == 'summary':
                    market_summary = self.get_market_summary()
                    script_summary = self.get_script_summary()
                    
                    print(f"\n📊 Data Summary:")
                    print(f"  📈 Markets: {market_summary['total_markets']} total")
                    print(f"  🤖 Scripts: {script_summary['total_scripts']} total")
                    print(f"  💰 Accounts: {len(self.accounts_cache)} total")
                    
                    print(f"\n🏢 Top Exchanges:")
                    for exchange, count in list(market_summary['exchanges'].items())[:5]:
                        print(f"  • {exchange}: {count} markets")
                    
                    print(f"\n💰 Top Currencies:")
                    for currency, count in list(market_summary['top_currencies'].items())[:5]:
                        print(f"  • {currency}: {count} pairs")
                    
                    print(f"\n🤖 Script Types:")
                    for script_type, count in script_summary['script_types'].items():
                        print(f"  • {script_type}: {count} scripts")
                    continue
                
                print("\n🤖 Processing your query...")
                response = await self.process_user_query(user_input)
                print(f"\n🤖 Response: {response}")
                
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
    client = LocalSearchClient()
    
    try:
        await client.start_server()
        await client.interactive_mode()
    except Exception as e:
        print(f"❌ Client failed with error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 