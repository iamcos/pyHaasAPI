#!/usr/bin/env python3
"""
Unified MCP Client for pyHaasAPI

This client framework supports multiple modes:
- Simple (basic search)
- Smart (local cache/index)
- Natural Language (Gemini integration)

Port logic from smart_mcp_client.py, gemini_mcp_client.py, local_search_client.py, simple_local_client.py, and natural_language_client.py into the appropriate sections below.
"""

import asyncio
import json
import subprocess
import sys
import os
from typing import Dict, Any, Optional, List
import socket
import time

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional, but recommended for local development

# Optional: Gemini integration stub
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash')
    else:
        GEMINI_MODEL = None
except ImportError:
    GEMINI_MODEL = None

SERVER_MODE = os.getenv("MCP_SERVER_MODE", "subprocess")  # 'subprocess' or 'external'
SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", 8765))  # For future network mode

DEBUG = os.getenv("MCP_CLIENT_DEBUG", "0") == "1"

class BaseMCPClient:
    def __init__(self, server_cmd: str = "unified_mcp_server.py"):
        self.process = None
        self.request_id = 1
        self.server_cmd = server_cmd
        self.host = os.getenv("API_HOST", "127.0.0.1")
        self.port = int(os.getenv("API_PORT", 8090))
        self.email = os.getenv("API_EMAIL")
        self.password = os.getenv("API_PASSWORD")
        self.server_mode = os.getenv("MCP_SERVER_MODE", "subprocess")
        # Local caches
        self.scripts_cache: List[Dict[str, Any]] = []
        self.markets_cache: List[Dict[str, Any]] = []
        self.accounts_cache: List[Dict[str, Any]] = []
        # Search indexes
        self.market_index = {}
        self.script_index = {}
        # Conversation history for NLP
        self.conversation_history = []

    def is_server_running(self) -> bool:
        # Quick check: try to connect to a known port (future network mode)
        # For now, check for a lock file as a placeholder
        return os.path.exists("/tmp/unified_mcp_server.lock")

    async def start_server(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.server_mode == "external" or self.is_server_running():
                    print("🔗 Connecting to already-running MCP server (external mode or detected lock file)...")
                    self.process = None
                else:
                    print("🚀 Starting MCP server as subprocess...")
                    self.process = subprocess.Popen(
                        [sys.executable, "-u", self.server_cmd],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    handshake = self.process.stdout.readline()
                    print(f"🤝 MCP server handshake: {handshake.strip()}")
                    with open("/tmp/unified_mcp_server.lock", "w") as f:
                        f.write("running")
                if self.process:
                    await self.send_request("initialize", {
                        "host": self.host,
                        "port": self.port,
                        "email": self.email,
                        "password": self.password
                    })
                return
            except BrokenPipeError:
                print(f"❌ Broken pipe: MCP server process may have exited unexpectedly (attempt {attempt+1}/{max_retries}).")
                if self.process:
                    self.process.terminate()
                time.sleep(1)
            except Exception as e:
                print(f"❌ Failed to start or connect to MCP server: {e} (attempt {attempt+1}/{max_retries})")
                if self.process:
                    self.process.terminate()
                time.sleep(1)
        print("❌ Could not connect to MCP server after several attempts. Please restart the client and server.")
        exit(1)

    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        request_json = json.dumps(request) + "\n"
        try:
            if self.process:
                if DEBUG:
                    print(f"[DEBUG] Sending: {request_json.strip()}")
                self.process.stdin.write(request_json)
                self.process.stdin.flush()
                response_line = self.process.stdout.readline()
                if DEBUG:
                    print(f"[DEBUG] Received: {response_line.strip()}")
                if response_line:
                    response = json.loads(response_line.strip())
                    self.request_id += 1
                    return response
                else:
                    print("❌ No response from MCP server. It may have crashed or exited.")
                    return {"error": "No response from MCP server"}
            else:
                print("❌ External server mode not yet implemented.")
                return {"error": "External server mode not implemented"}
        except BrokenPipeError:
            print("❌ Broken pipe: MCP server process may have exited unexpectedly.")
            return {"error": "Broken pipe to MCP server"}
        except Exception as e:
            print(f"❌ Unexpected error communicating with MCP server: {e}")
            return {"error": str(e)}

    async def load_essential_data(self):
        print("📥 Loading essential data from MCP server...")
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
        # Load markets
        markets_response = await self.send_request("get_markets")
        if "result" in markets_response:
            self.markets_cache = markets_response["result"]["markets"]
            print(f"✅ Loaded {len(self.markets_cache)} markets")
        self.build_search_indexes()

    def build_search_indexes(self):
        # Build market index
        for market in self.markets_cache:
            primary = market["primary"].upper()
            secondary = market["secondary"].upper()
            source = market["price_source"].upper()
            for key in [primary, secondary, source]:
                if key not in self.market_index:
                    self.market_index[key] = []
                self.market_index[key].append(market)
        # Build script index
        for script in self.scripts_cache:
            name = script["script_name"].lower()
            for word in name.split():
                if word not in self.script_index:
                    self.script_index[word] = []
                self.script_index[word].append(script)

    def fast_market_search(self, query: str) -> List[Dict[str, Any]]:
        query = query.upper()
        results = []
        if query in self.market_index:
            results.extend(self.market_index[query])
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
        return unique_results[:20]

    def fast_script_search(self, query: str) -> List[Dict[str, Any]]:
        query = query.lower()
        results = []
        if query in self.script_index:
            results.extend(self.script_index[query])
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
        return unique_results[:10]

    async def process_nlp_query(self, user_input: str) -> str:
        if not GEMINI_MODEL:
            return "Gemini NLP is not configured."
        # TODO: Build system prompt and conversation context
        system_prompt = "You are an AI assistant for HaasOnline MCP."
        conversation = [{"role": "user", "parts": [system_prompt]}]
        conversation.extend(self.conversation_history)
        conversation.append({"role": "user", "parts": [user_input]})
        response = GEMINI_MODEL.generate_content(conversation)
        gemini_response = response.text
        self.conversation_history.append({"role": "user", "parts": [user_input]})
        self.conversation_history.append({"role": "model", "parts": [gemini_response]})
        return gemini_response

    # TODO: Add more advanced NLP/MCP command extraction and routing

async def interactive_mode(client: BaseMCPClient, mode: str = "simple"):
    print(f"\n🤖 Unified MCP Client - Interactive Mode (mode: {mode})")
    print("Type 'quit' to exit, 'help' for available commands")
    print("=" * 50)
    await client.load_essential_data()
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            elif user_input.lower() == 'help':
                print("\n📚 Available commands: search market <query>, search script <query>, nlp <query>")
                continue
            if mode == "simple":
                if user_input.startswith("search market"):
                    query = user_input.replace("search market", "").strip()
                    results = client.fast_market_search(query)
                    print(f"\n🔎 Found {len(results)} markets:")
                    for market in results:
                        print(f"  • {market['primary']}/{market['secondary']} on {market['price_source']}")
                elif user_input.startswith("search script"):
                    query = user_input.replace("search script", "").strip()
                    results = client.fast_script_search(query)
                    print(f"\n🔎 Found {len(results)} scripts:")
                    for script in results:
                        print(f"  • {script['script_name']}")
                else:
                    print("❓ Try 'search market <query>' or 'search script <query>'")
            elif mode == "nlp":
                print("\n🤖 Gemini NLP: Processing your request...")
                response = await client.process_nlp_query(user_input)
                print(f"\n🤖 Gemini: {response}")
            # TODO: Add smart mode and more advanced routing
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

# Entrypoint
async def main():
    mode = os.getenv("MCP_CLIENT_MODE", "simple")
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    client = BaseMCPClient()
    await client.start_server()
    await interactive_mode(client, mode=mode)

if __name__ == "__main__":
    asyncio.run(main()) 