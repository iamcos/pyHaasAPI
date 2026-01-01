#!/usr/bin/env python3
"""
Example: List All Bots Across Available Servers

This example demonstrates how to use pyHaasAPI v2 to:
1. Connect to multiple HaasOnline servers
2. List all bots from each server
3. Display bot information in a structured format
4. Handle authentication and connection errors gracefully

Usage:
    python examples/list_all_bots.py
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
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.exceptions import BotError, AuthenticationError, NetworkError


class BotLister:
    """Bot listing utility for HaasOnline servers."""
    
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 8090
        
    async def list_bots(self) -> Dict[str, Any]:
        """List all bots across common servers."""
        print("🚀 pyHaasAPI v2 - List All Bots")
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
            
            # Create bot API
            bot_api = BotAPI(client, auth_manager)
            
            # Get all bots
            print("📋 Fetching bots...")
            bots = await bot_api.get_all_bots()
            print(f"✅ Found {len(bots)} bots")
            
            # Display detailed bot information
            if bots:
                print("\n" + "=" * 60)
                print("🤖 BOT DETAILS")
                print("=" * 60)
                
                for i, bot in enumerate(bots, 1):
                    # bot is a BotDetails model
                    status_emoji = "🟢" if getattr(bot, 'is_active', False) else "🔴"
                    print(f"  {i:2d}. {status_emoji} {bot.name}")
                    print(f"      ID: {bot.bot_id}")
                    print(f"      Script: {getattr(bot, 'script_name', 'Unknown')}")
                    print(f"      Market: {getattr(bot, 'market_tag', 'Unknown')}")
                    print(f"      Account: {getattr(bot, 'account_id', 'Unknown')}")
                    print()
            
            await client.close()
            return {"success": True, "count": len(bots)}
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if 'client' in locals():
                await client.close()
            return {"success": False, "error": str(e)}

async def main():
    """Main function to run the bot listing example."""
    lister = BotLister()
    result = await lister.list_bots()
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    # Run the example
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
