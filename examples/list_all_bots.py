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
    """Bot listing utility for multiple servers."""
    
    def __init__(self):
        self.servers = {
            "srv01": {"host": "127.0.0.1", "port": 8090},
            "srv02": {"host": "127.0.0.1", "port": 8091}, 
            "srv03": {"host": "127.0.0.1", "port": 8092}
        }
        self.results = {}
    
    async def list_bots_for_server(self, server_name: str, config: APIConfig) -> Dict[str, Any]:
        """List all bots for a specific server."""
        print(f"\n🔍 Connecting to {server_name}...")
        
        try:
            # Create client and auth manager
            client = AsyncHaasClient(config)
            auth_manager = AuthenticationManager(client, config)
            
            # Authenticate
            print(f"   Authenticating with {server_name}...")
            session = await auth_manager.authenticate()
            print(f"   ✅ Authentication successful: {session.user_id}")
            
            # Create bot API
            bot_api = BotAPI(client, auth_manager)
            
            # Get all bots
            print(f"   📋 Fetching bots from {server_name}...")
            bots = await bot_api.get_all_bots()
            
            print(f"   ✅ Found {len(bots)} bots on {server_name}")
            
            return {
                "server": server_name,
                "success": True,
                "bot_count": len(bots),
                "bots": bots,
                "user_id": session.user_id
            }
            
        except AuthenticationError as e:
            print(f"   ❌ Authentication failed for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Authentication failed: {e}",
                "bot_count": 0,
                "bots": []
            }
        except NetworkError as e:
            print(f"   ❌ Network error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Network error: {e}",
                "bot_count": 0,
                "bots": []
            }
        except BotError as e:
            print(f"   ❌ Bot API error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Bot API error: {e}",
                "bot_count": 0,
                "bots": []
            }
        except Exception as e:
            print(f"   ❌ Unexpected error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Unexpected error: {e}",
                "bot_count": 0,
                "bots": []
            }
    
    async def list_all_bots(self) -> Dict[str, Any]:
        """List all bots across all available servers."""
        print("🚀 pyHaasAPI v2 - List All Bots Example")
        print("=" * 50)
        
        # Load environment variables
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("❌ Error: API_EMAIL and API_PASSWORD environment variables must be set")
            print("   Please create a .env file with your credentials:")
            print("   API_EMAIL=your_email@example.com")
            print("   API_PASSWORD=your_password")
            return {"error": "Missing credentials"}
        
        results = {}
        total_bots = 0
        
        # Try each server
        for server_name, server_config in self.servers.items():
            config = APIConfig(
                email=email,
                password=password,
                host=server_config["host"],
                port=server_config["port"],
                timeout=30.0
            )
            
            result = await self.list_bots_for_server(server_name, config)
            results[server_name] = result
            
            if result["success"]:
                total_bots += result["bot_count"]
        
        # Display summary
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        
        successful_servers = 0
        for server_name, result in results.items():
            if result["success"]:
                successful_servers += 1
                print(f"✅ {server_name}: {result['bot_count']} bots (User: {result.get('user_id', 'Unknown')})")
            else:
                print(f"❌ {server_name}: Failed - {result['error']}")
        
        print(f"\n🎯 Total: {successful_servers}/{len(self.servers)} servers connected")
        print(f"🤖 Total bots found: {total_bots}")
        
        # Display detailed bot information
        if total_bots > 0:
            print("\n" + "=" * 50)
            print("🤖 BOT DETAILS")
            print("=" * 50)
            
            for server_name, result in results.items():
                if result["success"] and result["bots"]:
                    print(f"\n📡 {server_name.upper()} ({result['bot_count']} bots):")
                    print("-" * 30)
                    
                    for i, bot in enumerate(result["bots"], 1):
                        status_emoji = "🟢" if bot.is_active else "🔴"
                        print(f"  {i:2d}. {status_emoji} {bot.name}")
                        print(f"      ID: {bot.bot_id}")
                        print(f"      Script: {bot.script_name}")
                        print(f"      Market: {bot.market_tag}")
                        print(f"      Account: {bot.account_id}")
                        print(f"      Status: {'Active' if bot.is_active else 'Inactive'}")
                        if hasattr(bot, 'created_at') and bot.created_at:
                            print(f"      Created: {bot.created_at}")
                        print()
        
        return {
            "total_servers": len(self.servers),
            "successful_servers": successful_servers,
            "total_bots": total_bots,
            "results": results
        }


async def main():
    """Main function to run the bot listing example."""
    lister = BotLister()
    
    try:
        results = await lister.list_all_bots()
        
        if "error" in results:
            print(f"\n❌ Example failed: {results['error']}")
            return 1
        
        print(f"\n✅ Example completed successfully!")
        print(f"   Connected to {results['successful_servers']}/{results['total_servers']} servers")
        print(f"   Found {results['total_bots']} total bots")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Example interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Example failed with unexpected error: {e}")
        return 1


if __name__ == "__main__":
    # Run the example
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
