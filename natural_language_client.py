#!/usr/bin/env python3
"""
Natural Language Client for HaasOnline API

This client understands natural language queries and searches for markets and scripts intelligently.
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

class NaturalLanguageClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Local cache for data
        self.scripts_cache = []
        self.markets_cache = []
        self.accounts_cache = []
        
        # Search keywords mapping
        self.script_keywords = {
            "scalper": ["scalper", "scalp", "quick", "fast", "short", "intraday"],
            "rsi": ["rsi", "relative strength", "oscillator"],
            "macd": ["macd", "moving average convergence"],
            "ema": ["ema", "exponential moving average"],
            "bollinger": ["bollinger", "bands", "bb"],
            "stochastic": ["stochastic", "stoch"],
            "momentum": ["momentum", "mom"],
            "trend": ["trend", "trending", "direction"],
            "arbitrage": ["arbitrage", "arb", "price difference"],
            "grid": ["grid", "grid trading", "martingale"],
            "dca": ["dca", "dollar cost average", "averaging"],
            "swing": ["swing", "swing trading", "medium term"]
        }
    
    async def start_server(self):
        """Start the MCP server and load data"""
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
        
        # Initialize
        await self.send_request("initialize", {
            "host": "127.0.0.1",
            "port": 8090,
            "email": "garrypotterr@gmail.com",
            "password": "IQYTCQJIQYTCQJ"
        })
        
        # Load all data
        await self.load_data()
        print("✅ Data loaded for natural language processing")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send request to MCP server"""
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
    
    async def load_data(self):
        """Load all data for local processing"""
        print("📊 Loading data...")
        
        # Load scripts
        print("  📝 Loading scripts...")
        scripts_response = await self.send_request("get_scripts")
        if "result" in scripts_response:
            self.scripts_cache = scripts_response["result"]["scripts"]
            print(f"    ✅ Loaded {len(self.scripts_cache)} scripts")
            # Print first few script names for debugging
            print(f"    📝 Sample scripts: {[s['script_name'] for s in self.scripts_cache[:5]]}")
        
        # Load accounts
        print("  💰 Loading accounts...")
        accounts_response = await self.send_request("get_accounts")
        if "result" in accounts_response:
            self.accounts_cache = accounts_response["result"]["accounts"]
            print(f"    ✅ Loaded {len(self.accounts_cache)} accounts")
        
        # Load markets
        print("  📈 Loading markets...")
        markets_response = await self.send_request("get_markets")
        if "result" in markets_response:
            self.markets_cache = markets_response["result"]["markets"]
            print(f"    ✅ Loaded {len(self.markets_cache)} markets")
        
        print("✅ All data loaded")
    
    def smart_script_search(self, query: str) -> List[Dict[str, Any]]:
        """Smart script search using multiple strategies"""
        query = query.lower().strip()
        results = []
        
        # Strategy 1: Direct name matching
        for script in self.scripts_cache:
            if query in script["script_name"].lower():
                results.append(script)
        
        # Strategy 2: Keyword mapping
        for category, keywords in self.script_keywords.items():
            if any(keyword in query for keyword in keywords):
                for script in self.scripts_cache:
                    script_name = script["script_name"].lower()
                    if any(keyword in script_name for keyword in keywords):
                        if script not in results:
                            results.append(script)
        
        # Strategy 3: Partial word matching
        if not results:
            query_words = query.split()
            for script in self.scripts_cache:
                script_name = script["script_name"].lower()
                if any(word in script_name for word in query_words):
                    results.append(script)
        
        return results[:10]  # Limit results
    
    def smart_market_search(self, query: str) -> List[Dict[str, Any]]:
        """Smart market search using multiple strategies"""
        query = query.upper().strip()
        results = []
        
        # Strategy 1: Direct pair matching (BTC/USDT)
        if "/" in query:
            base, quote = query.split("/")
            for market in self.markets_cache:
                if market["primary"].upper() == base and market["secondary"].upper() == quote:
                    results.append(market)
        
        # Strategy 2: Currency matching
        else:
            for market in self.markets_cache:
                if (query in market["primary"].upper() or 
                    query in market["secondary"].upper() or 
                    query in market["price_source"].upper()):
                    results.append(market)
        
        return results[:20]  # Limit results
    
    def extract_intent(self, user_input: str) -> Dict[str, Any]:
        """Extract user intent from natural language input"""
        user_input = user_input.lower()
        
        intent = {
            "action": "general_query",
            "markets": [],
            "scripts": [],
            "parameters": {},
            "raw_query": user_input
        }
        
        # Market-related queries
        market_keywords = ["market", "pair", "trading pair", "currency", "btc", "eth", "usdt", "usdc", "binance", "coinbase", "kraken"]
        if any(keyword in user_input for keyword in market_keywords):
            intent["action"] = "search_markets"
            # Extract specific markets mentioned
            if "btc" in user_input and "usdt" in user_input:
                intent["markets"].append("BTC/USDT")
            elif "btc" in user_input:
                intent["markets"].append("BTC")
            elif "eth" in user_input:
                intent["markets"].append("ETH")
        
        # Script-related queries
        script_keywords = ["script", "bot", "strategy", "algorithm", "scalper", "rsi", "macd", "ema", "bollinger", "stochastic"]
        if any(keyword in user_input for keyword in script_keywords):
            intent["action"] = "search_scripts"
            # Extract specific script types mentioned
            if "scalper" in user_input:
                intent["scripts"].append("scalper")
            if "rsi" in user_input:
                intent["scripts"].append("rsi")
            if "macd" in user_input:
                intent["scripts"].append("macd")
        
        # Lab creation queries
        if any(word in user_input for word in ["create", "make", "build", "set up", "new lab"]):
            intent["action"] = "create_lab"
        
        # Backtest queries
        if any(word in user_input for word in ["backtest", "test", "simulate", "historical"]):
            intent["action"] = "backtest"
        
        return intent
    
    async def process_natural_language(self, user_input: str) -> str:
        """Process natural language input and provide intelligent responses"""
        try:
            # Extract intent
            intent = self.extract_intent(user_input)
            
            # Build response
            response_parts = []
            
            # Handle market searches
            if intent["action"] == "search_markets" or "market" in intent["raw_query"]:
                for market_query in intent["markets"]:
                    markets = self.smart_market_search(market_query)
                    if markets:
                        response_parts.append(f"🔍 Found {len(markets)} markets for '{market_query}':")
                        for market in markets[:5]:  # Show first 5
                            response_parts.append(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")
                    else:
                        response_parts.append(f"❌ No markets found for '{market_query}'")
                
                # If no specific markets mentioned, search for common ones
                if not intent["markets"]:
                    btc_markets = self.smart_market_search("BTC")
                    if btc_markets:
                        response_parts.append(f"🔍 Found {len(btc_markets)} BTC markets:")
                        for market in btc_markets[:3]:
                            response_parts.append(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")
            
            # Handle script searches
            if intent["action"] == "search_scripts" or "script" in intent["raw_query"] or "bot" in intent["raw_query"]:
                for script_query in intent["scripts"]:
                    scripts = self.smart_script_search(script_query)
                    if scripts:
                        response_parts.append(f"🤖 Found {len(scripts)} scripts for '{script_query}':")
                        for script in scripts[:5]:  # Show first 5
                            response_parts.append(f"  • {script['script_name']} (ID: {script['script_id'][:8]}...)")
                    else:
                        response_parts.append(f"❌ No scripts found for '{script_query}'")
                
                # If no specific scripts mentioned, search for common ones
                if not intent["scripts"]:
                    scalper_scripts = self.smart_script_search("scalper")
                    if scalper_scripts:
                        response_parts.append(f"🤖 Found {len(scalper_scripts)} scalper scripts:")
                        for script in scalper_scripts[:3]:
                            response_parts.append(f"  • {script['script_name']} (ID: {script['script_id'][:8]}...)")
            
            # Add Gemini AI response for general advice
            if not response_parts or intent["action"] == "general_query":
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
                
                response = self.model.generate_content(context_prompt + "\n\nUser query: " + user_input)
                response_parts.append(f"🤖 AI Advice: {response.text}")
            
            return "\n\n".join(response_parts) if response_parts else "I'm not sure how to help with that. Try asking about markets, scripts, or trading strategies."
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
    
    async def interactive_mode(self):
        """Run interactive natural language mode"""
        print("\n🗣️  Natural Language Client - Interactive Mode")
        print("Ask me anything about markets, scripts, trading strategies, or bot development!")
        print("Examples:")
        print("  • 'Show me BTC markets'")
        print("  • 'Find scalper scripts'")
        print("  • 'What's the best strategy for ETH?'")
        print("  • 'Help me create a lab'")
        print("  • 'How do I optimize parameters?'")
        print("Type 'quit' to exit")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                print("\n🤖 Processing your request...")
                response = await self.process_natural_language(user_input)
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
    client = NaturalLanguageClient()
    
    try:
        await client.start_server()
        await client.interactive_mode()
    except Exception as e:
        print(f"❌ Client failed with error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 