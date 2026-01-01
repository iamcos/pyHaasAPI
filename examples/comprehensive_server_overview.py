#!/usr/bin/env python3
"""
Example: Comprehensive Server Overview

This example demonstrates how to use pyHaasAPI v2 to:
1. Connect to multiple HaasOnline servers
2. List all labs and bots from each server
3. Display comprehensive server statistics
4. Show performance metrics and status information
5. Handle authentication and connection errors gracefully

Usage:
    python examples/comprehensive_server_overview.py
"""

import asyncio
import sys
import os
from typing import List, Dict, Any
from datetime import datetime

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.exceptions import LabError, BotError, AuthenticationError, NetworkError


class ServerOverview:
    """Comprehensive server overview utility."""
    
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 8090
        
    async def generate_overview(self) -> Dict[str, Any]:
        """Generate comprehensive overview of the server."""
        print("🚀 pyHaasAPI v2 - Comprehensive Server Overview")
        print("=" * 60)
        
        # Load environment variables
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("❌ Error: API_EMAIL and API_PASSWORD environment variables must be set")
            return {"error": "Missing credentials"}
        
        try:
            # Create configuration
            config = APIConfig(
                email=email,
                password=password,
                host=self.host,
                port=self.port,
                timeout=30.0
            )
            
            # Create client and auth manager
            client = AsyncHaasClient(config)
            auth_manager = AuthenticationManager(client, config)
            
            # Authenticate
            print(f"🔗 Connecting to Haas API at {self.host}:{self.port}...")
            await auth_manager.authenticate()
            print(f"✅ Authentication successful")
            
            # Create APIs
            lab_api = LabAPI(client, auth_manager)
            bot_api = BotAPI(client, auth_manager)
            
            # Get data
            print("📋 Fetching labs...")
            labs = await lab_api.get_labs()
            print("🤖 Fetching bots...")
            bots = await bot_api.get_all_bots()
            
            # Analyze
            active_bots = [b for b in bots if getattr(b, 'is_active', False)]
            
            markets = set()
            scripts = set()
            
            for lab in labs:
                # lab is LabRecord
                if getattr(lab, 'market_tag', None):
                    markets.add(lab.market_tag)
                if getattr(lab, 'script_name', None):
                    scripts.add(lab.script_name)
                    
            for bot in bots:
                # bot is BotDetails
                if getattr(bot, 'market_tag', None):
                    markets.add(bot.market_tag)
                if getattr(bot, 'script_name', None):
                    scripts.add(bot.script_name)
            
            # Display results
            print("\n" + "=" * 60)
            print("📊 SERVER SUMMARY")
            print("=" * 60)
            print(f"🧪 Total Labs: {len(labs)}")
            print(f"🤖 Total Bots: {len(bots)} ({len(active_bots)} active)")
            print(f"📈 Unique Markets: {len(markets)}")
            print(f"📜 Unique Scripts: {len(scripts)}")
            
            if markets:
                print("\n📈 MARKETS:")
                for m in sorted(list(markets)):
                    print(f"   • {m}")
                    
            if scripts:
                print("\n📜 SCRIPTS:")
                for s in sorted(list(scripts)):
                    print(f"   • {s}")
            
            await client.close()
            return {"success": True}
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if 'client' in locals():
                await client.close()
            return {"success": False, "error": str(e)}

async def main():
    """Main function to run the comprehensive overview example."""
    overview = ServerOverview()
    result = await overview.generate_overview()
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    # Run the example
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
