#!/usr/bin/env python3
"""
Simple Local Search Client
"""

import asyncio
import json
import subprocess
import sys

class SimpleLocalClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
        self.markets_cache = []
        self.scripts_cache = []
    
    async def start_server(self):
        """Start MCP server and load data"""
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
        
        # Load data
        await self.load_data()
        print("✅ Data loaded for local search")
    
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
        """Load markets and scripts data"""
        print("📊 Loading data...")
        
        # Load markets (limited for speed)
        markets_response = await self.send_request("get_markets")
        if "result" in markets_response:
            self.markets_cache = markets_response["result"]["markets"][:500]  # Limit to 500
            print(f"✅ Loaded {len(self.markets_cache)} markets")
        
        # Load scripts
        scripts_response = await self.send_request("get_scripts")
        if "result" in scripts_response:
            self.scripts_cache = scripts_response["result"]["scripts"]
            print(f"✅ Loaded {len(self.scripts_cache)} scripts")
    
    def search_markets(self, query: str) -> List[Dict[str, Any]]:
        """Search markets locally"""
        query = query.upper()
        results = []
        
        for market in self.markets_cache:
            if (query in market["primary"] or 
                query in market["secondary"] or 
                query in market["price_source"]):
                results.append(market)
        
        return results[:10]
    
    def search_scripts(self, query: str) -> List[Dict[str, Any]]:
        """Search scripts locally"""
        query = query.lower()
        results = []
        
        for script in self.scripts_cache:
            if query in script["script_name"].lower():
                results.append(script)
        
        return results[:10]
    
    async def interactive_mode(self):
        """Interactive mode"""
        print("\n🔍 Simple Local Search Client")
        print("Commands: 'search btc', 'search scalper', 'quit'")
        
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
                else:
                    print("❓ Try 'search btc' or 'search scalper'")
                    
            except KeyboardInterrupt:
                break
    
    async def cleanup(self):
        """Cleanup"""
        if self.process:
            self.process.terminate()
            self.process.wait()

async def main():
    client = SimpleLocalClient()
    try:
        await client.start_server()
        await client.interactive_mode()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 