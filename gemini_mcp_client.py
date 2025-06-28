#!/usr/bin/env python3
"""
Gemini-powered MCP Client for HaasOnline API

This client uses Google's Gemini API to intelligently interact with the HaasOnline MCP server,
allowing natural language commands to control trading bots, labs, and market data.

Usage:
    python gemini_mcp_client.py

Requirements:
    pip install google-generativeai
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, List
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "your_gemini_api_key"
genai.configure(api_key=GEMINI_API_KEY)

class GeminiMCPClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.conversation_history = []
        
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
    
    def create_system_prompt(self) -> str:
        """Create the system prompt for Gemini"""
        return f"""You are an AI assistant that controls a HaasOnline trading bot system through an MCP (Model Context Protocol) server.

Available MCP methods:
{json.dumps(self.mcp_capabilities, indent=2)}

Your role:
1. Understand user requests in natural language
2. Convert them to appropriate MCP method calls
3. Provide helpful responses about trading operations
4. Suggest trading strategies and parameter optimizations

Current context:
- You have access to HaasOnline API through MCP
- You can create labs, run backtests, and deploy bots
- You can perform parameter sweeps for optimization
- You can manage existing bots (start/stop)

Guidelines:
- Always be helpful and informative
- Suggest best practices for trading
- Explain what you're doing before executing commands
- Provide context about trading strategies
- Be cautious about real money trading (suggest simulation first)

Example interactions:
- "Show me all available scripts" → call get_scripts
- "What markets are available?" → call get_markets
- "Create a scalper bot lab for BTC/USDT" → call create_lab with scalper script
- "Run a parameter sweep on stop loss and take profit" → call parameter_sweep
- "Show me my bots" → call get_bots

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
            
            # Parse Gemini response for MCP commands
            mcp_commands = self.extract_mcp_commands(gemini_response)
            
            if mcp_commands:
                results = []
                for command in mcp_commands:
                    result = await self.send_request(command["method"], command["params"])
                    results.append(result)
                
                # Generate final response with results
                final_response = self.generate_final_response(gemini_response, results)
                return final_response
            else:
                return gemini_response
                
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"
    
    def extract_mcp_commands(self, gemini_response: str) -> List[Dict[str, Any]]:
        """Extract MCP commands from Gemini response"""
        commands = []
        
        # Simple command extraction (can be enhanced with more sophisticated parsing)
        for method in self.mcp_capabilities.keys():
            if method in gemini_response.lower():
                # Basic parameter extraction
                params = {}
                if "script" in method:
                    params = {"script_type": "scalper"}  # Default to scalper
                elif "market" in method:
                    params = {"market_filter": "all"}
                
                commands.append({
                    "method": method,
                    "params": params
                })
        
        return commands
    
    def generate_final_response(self, gemini_response: str, results: List[Dict[str, Any]]) -> str:
        """Generate final response combining Gemini's response with MCP results"""
        response_parts = [gemini_response]
        
        for i, result in enumerate(results):
            if "error" in result:
                response_parts.append(f"\n❌ Command {i+1} failed: {result['error']}")
            else:
                response_parts.append(f"\n✅ Command {i+1} succeeded: {json.dumps(result['result'], indent=2)}")
        
        return "\n".join(response_parts)
    
    async def interactive_mode(self):
        """Run interactive mode for user input"""
        print("\n🤖 Gemini MCP Client - Interactive Mode")
        print("Type 'quit' to exit, 'help' for available commands")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'help':
                    print("\n📚 Available commands:")
                    for method, description in self.mcp_capabilities.items():
                        print(f"  • {method}: {description}")
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
    client = GeminiMCPClient()
    
    try:
        await client.start_server()
        await client.interactive_mode()
    except Exception as e:
        print(f"❌ Client failed with error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
