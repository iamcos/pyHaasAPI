#!/usr/bin/env python3
"""
Smart MCP Client for HaasOnline API

This client intelligently processes data locally and only calls MCP methods when needed,
providing fast market search and better user experience.

Usage:
    python smart_mcp_client.py
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "your_gemini_api_key"
genai.configure(api_key=GEMINI_API_KEY)

class SmartMCPClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.conversation_history = []
        
        # Local cache for data
        self.scripts_cache = []
        self.markets_cache = []
        self.accounts_cache = []
        self.labs_cache = []
        self.bots_cache = []
        
        # MCP server capabilities
        self.mcp_capabilities = {
            "initialize": "Initialize connection to HaasOnline API",
            "get_scripts": "Get all available trading scripts",
            "get_markets": "Get all available markets", 
            "get_accounts": "Get user accounts",
            "create_lab": "Create a new lab for backtesting",
            "get_lab_details": "Get lab details and parameters",
            "update_lab_parameters": "Update lab parameters",
            "start_backtest": "Start a lab backtest",
            "get_backtest_results": "Get backtest results",
            "create_bot_from_lab": "Create a bot from lab backtest results",
            "parameter_sweep": "Perform parameter sweep on a lab",
            "get_bots": "Get user's trading bots",
            "start_bot": "Start a trading bot",
            "stop_bot": "Stop a trading bot"
        }
    
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
        
        # Initialize the server
        await self.send_request("initialize", {
            "host": "127.0.0.1",
            "port": 8090,
            "email": "your_email@example.com",
            "password": "your_password"
        })
        print("✅ MCP server initialized")
        
        # Pre-load essential data
        await self.load_essential_data()
    
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
    
    async def load_essential_data(self):
        """Pre-load essential data for fast local processing"""
        print("📊 Loading essential data...")
        
        # Load scripts
        scripts_response = await self.send_request("get_scripts")
        if "result" in scripts_response:
            self.scripts_cache = scripts_response["result"]["scripts"]
            print(f"✅ Loaded {len(self.scripts_cache)} scripts")
        
        # Load accounts
        accounts_response = await self.send_request("get_accounts")
        if "result" in accounts_response:
            self.accounts_cache = accounts_response["result"]["accounts"]
            print(f"✅ Loaded {len(self.accounts_cache)} accounts")
        
        # Load markets (but limit to first 1000 for speed)
        markets_response = await self.send_request("get_markets")
        if "result" in markets_response:
            self.markets_cache = markets_response["result"]["markets"][:1000]  # Limit for speed
            print(f"✅ Loaded {len(self.markets_cache)} markets (limited for speed)")
        
        print("✅ Essential data loaded")
    
    def search_markets(self, query: str) -> List[Dict[str, Any]]:
        """Search markets locally using the query"""
        query = query.upper()
        results = []
        
        for market in self.markets_cache:
            if (query in market["primary"] or 
                query in market["secondary"] or 
                query in market["price_source"]):
                results.append(market)
        
        return results[:20]  # Limit results
    
    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """Search scripts locally using the query"""
        query = query.lower()
        results = []
        
        for script in self.scripts_cache:
            if query in script["script_name"].lower():
                results.append(script)
        
        return results[:10]  # Limit results
    
    def create_system_prompt(self) -> str:
        """Create the system prompt for Gemini"""
        return f"""You are an AI assistant that controls a HaasOnline trading bot system through an MCP (Model Context Protocol) server.

Available MCP methods:
{json.dumps(self.mcp_capabilities, indent=2)}

Your role:
1. Understand user requests in natural language
2. Provide helpful responses about trading operations
3. Suggest trading strategies and parameter optimizations
4. Use local data when possible to avoid slow API calls

Current context:
- You have access to HaasOnline API through MCP
- Local data is available for fast queries (scripts, markets, accounts)
- You can create labs, run backtests, and deploy bots
- You can perform parameter sweeps for optimization
- You can manage existing bots (start/stop)

Guidelines:
- Always be helpful and informative
- Suggest best practices for trading
- Use local search when possible (markets, scripts)
- Only call MCP methods when you have the required parameters
- Be cautious about real money trading (suggest simulation first)
- Provide specific, actionable advice

Example interactions:
- "Show me BTC markets" → search local markets for BTC
- "Find scalper scripts" → search local scripts for scalper
- "Create a lab for BTC/USDT with scalper" → call create_lab with specific parameters
- "Show me my bots" → call get_bots
- "Run a parameter sweep" → call parameter_sweep with lab_id

Remember: Always prioritize safety and suggest simulation mode for testing."""
    
    async def process_user_request(self, user_input: str) -> str:
        """Process user input using Gemini and execute MCP commands"""
        try:
            # Create conversation context
            system_prompt = self.create_system_prompt()
            
            # Add conversation history
            conversation = [{"role": "user", "parts": [system_prompt]}]
            conversation.extend(self.conversation_history)
            conversation.append({"role": "user", "parts": [user_input]})
            
            # Get Gemini response
            response = self.model.generate_content(conversation)
            gemini_response = response.text
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "parts": [user_input]})
            self.conversation_history.append({"role": "model", "parts": [gemini_response]})
            
            # Process local searches first
            local_results = self.process_local_searches(user_input)
            
            # Only call MCP methods when we have specific parameters
            mcp_commands = self.extract_specific_mcp_commands(user_input, gemini_response)
            
            if mcp_commands:
                results = []
                for command in mcp_commands:
                    result = await self.send_request(command["method"], command["params"])
                    results.append(result)
                
                # Generate final response with results
                final_response = self.generate_final_response(gemini_response, local_results, results)
                return final_response
            else:
                # Just return Gemini response with local results
                return self.generate_final_response(gemini_response, local_results, [])
                
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"
    
    def process_local_searches(self, user_input: str) -> Dict[str, Any]:
        """Process local searches for markets and scripts"""
        results = {}
        
        # Search for markets
        market_keywords = ["market", "btc", "eth", "usdt", "usdc", "eur", "binance", "kraken"]
        for keyword in market_keywords:
            if keyword.lower() in user_input.lower():
                markets = self.search_markets(keyword)
                if markets:
                    results["markets"] = markets
                    break
        
        # Search for scripts
        script_keywords = ["script", "bot", "scalper", "rsi", "macd", "ema"]
        for keyword in script_keywords:
            if keyword.lower() in user_input.lower():
                scripts = self.search_scripts(keyword)
                if scripts:
                    results["scripts"] = scripts
                    break
        
        return results
    
    def extract_specific_mcp_commands(self, user_input: str, gemini_response: str) -> List[Dict[str, Any]]:
        """Extract specific MCP commands only when we have required parameters"""
        commands = []
        
        # Only call methods that don't require specific IDs
        safe_methods = ["get_bots", "get_lab_details"]  # These require IDs we might have
        
        # For create_lab, we need script_id and market info
        if "create lab" in user_input.lower() or "create a lab" in user_input.lower():
            # Find scalper script
            scalper_scripts = self.search_scripts("scalper")
            if scalper_scripts:
                script_id = scalper_scripts[0]["script_id"]
                
                # Find BTC/USDT market
                btc_markets = self.search_markets("BTC")
                usdt_markets = [m for m in btc_markets if "USDT" in m["secondary"]]
                
                if usdt_markets and self.accounts_cache:
                    market = usdt_markets[0]
                    account = self.accounts_cache[0]
                    
                    commands.append({
                        "method": "create_lab",
                        "params": {
                            "script_id": script_id,
                            "name": f"Smart_Lab_{int(time.time())}",
                            "account_id": account["account_id"],
                            "market": f"{market['price_source']}_{market['primary']}_{market['secondary']}_",
                            "interval": 1,
                            "style": "CandleStick"
                        }
                    })
        
        return commands
    
    def generate_final_response(self, gemini_response: str, local_results: Dict[str, Any], mcp_results: List[Dict[str, Any]]) -> str:
        """Generate final response combining all results"""
        response_parts = [gemini_response]
        
        # Add local search results
        if local_results:
            response_parts.append("\n🔍 Local Search Results:")
            
            if "markets" in local_results:
                response_parts.append(f"\n📈 Found {len(local_results['markets'])} markets:")
                for market in local_results["markets"][:5]:  # Show first 5
                    response_parts.append(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")
            
            if "scripts" in local_results:
                response_parts.append(f"\n🤖 Found {len(local_results['scripts'])} scripts:")
                for script in local_results["scripts"][:5]:  # Show first 5
                    response_parts.append(f"  • {script['script_name']} (ID: {script['script_id'][:8]}...)")
        
        # Add MCP results
        for i, result in enumerate(mcp_results):
            if "error" in result:
                response_parts.append(f"\n❌ Command {i+1} failed: {result['error']}")
            else:
                response_parts.append(f"\n✅ Command {i+1} succeeded: {json.dumps(result['result'], indent=2)}")
        
        return "\n".join(response_parts)
    
    async def interactive_mode(self):
        """Run interactive mode for user input"""
        print("\n🤖 Smart MCP Client - Interactive Mode")
        print("Type 'quit' to exit, 'help' for available commands")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print("\n📚 Available commands:")
                    print("  • Search markets: 'Show me BTC markets'")
                    print("  • Search scripts: 'Find scalper scripts'")
                    print("  • Create lab: 'Create a lab for BTC/USDT'")
                    print("  • Show bots: 'Show my bots'")
                    print("  • General questions about trading")
                    continue
                
                print("\n🤖 Gemini: Processing your request...")
                response = await self.process_user_request(user_input)
                print(f"\n🤖 Gemini: {response}")
                
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
    client = SmartMCPClient()
    
    try:
        await client.start_server()
        await client.interactive_mode()
    except Exception as e:
        print(f"❌ Client failed with error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 