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
        self.servers = {
            "srv01": {"host": "127.0.0.1", "port": 8090},
            "srv02": {"host": "127.0.0.1", "port": 8091}, 
            "srv03": {"host": "127.0.0.1", "port": 8092}
        }
        self.results = {}
    
    async def analyze_server(self, server_name: str, config: APIConfig) -> Dict[str, Any]:
        """Analyze a specific server for labs and bots."""
        print(f"\n🔍 Analyzing {server_name}...")
        
        try:
            # Create client and auth manager
            client = AsyncHaasClient(config)
            auth_manager = AuthenticationManager(client, config)
            
            # Authenticate
            print(f"   Authenticating with {server_name}...")
            session = await auth_manager.authenticate()
            print(f"   ✅ Authentication successful: {session.user_id}")
            
            # Create APIs
            lab_api = LabAPI(client, auth_manager)
            bot_api = BotAPI(client, auth_manager)
            
            # Get labs
            print(f"   📋 Fetching labs from {server_name}...")
            labs = await lab_api.get_labs()
            print(f"   ✅ Found {len(labs)} labs")
            
            # Get bots
            print(f"   🤖 Fetching bots from {server_name}...")
            bots = await bot_api.get_all_bots()
            print(f"   ✅ Found {len(bots)} bots")
            
            # Analyze data
            active_bots = [bot for bot in bots if bot.is_active]
            inactive_bots = [bot for bot in bots if not bot.is_active]
            
            # Get unique markets and scripts
            markets = set()
            scripts = set()
            
            for lab in labs:
                if hasattr(lab, 'market_tag') and lab.market_tag:
                    markets.add(lab.market_tag)
                if hasattr(lab, 'script_name') and lab.script_name:
                    scripts.add(lab.script_name)
            
            for bot in bots:
                if hasattr(bot, 'market_tag') and bot.market_tag:
                    markets.add(bot.market_tag)
                if hasattr(bot, 'script_name') and bot.script_name:
                    scripts.add(bot.script_name)
            
            return {
                "server": server_name,
                "success": True,
                "user_id": session.user_id,
                "labs": {
                    "total": len(labs),
                    "labs": labs
                },
                "bots": {
                    "total": len(bots),
                    "active": len(active_bots),
                    "inactive": len(inactive_bots),
                    "bots": bots
                },
                "markets": {
                    "count": len(markets),
                    "list": list(markets)
                },
                "scripts": {
                    "count": len(scripts),
                    "list": list(scripts)
                }
            }
            
        except AuthenticationError as e:
            print(f"   ❌ Authentication failed for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Authentication failed: {e}"
            }
        except NetworkError as e:
            print(f"   ❌ Network error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Network error: {e}"
            }
        except Exception as e:
            print(f"   ❌ Unexpected error for {server_name}: {e}")
            return {
                "server": server_name,
                "success": False,
                "error": f"Unexpected error: {e}"
            }
    
    async def generate_overview(self) -> Dict[str, Any]:
        """Generate comprehensive overview of all servers."""
        print("🚀 pyHaasAPI v2 - Comprehensive Server Overview")
        print("=" * 60)
        
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
        total_labs = 0
        total_bots = 0
        total_active_bots = 0
        all_markets = set()
        all_scripts = set()
        
        # Analyze each server
        for server_name, server_config in self.servers.items():
            config = APIConfig(
                email=email,
                password=password,
                host=server_config["host"],
                port=server_config["port"],
                timeout=30.0
            )
            
            result = await self.analyze_server(server_name, config)
            results[server_name] = result
            
            if result["success"]:
                total_labs += result["labs"]["total"]
                total_bots += result["bots"]["total"]
                total_active_bots += result["bots"]["active"]
                all_markets.update(result["markets"]["list"])
                all_scripts.update(result["scripts"]["list"])
        
        # Display comprehensive summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE SUMMARY")
        print("=" * 60)
        
        successful_servers = 0
        for server_name, result in results.items():
            if result["success"]:
                successful_servers += 1
                print(f"✅ {server_name}:")
                print(f"   🧪 Labs: {result['labs']['total']}")
                print(f"   🤖 Bots: {result['bots']['total']} ({result['bots']['active']} active)")
                print(f"   📈 Markets: {result['markets']['count']}")
                print(f"   📜 Scripts: {result['scripts']['count']}")
                print(f"   👤 User: {result['user_id']}")
            else:
                print(f"❌ {server_name}: Failed - {result['error']}")
        
        print(f"\n🎯 GLOBAL TOTALS:")
        print(f"   🌐 Servers: {successful_servers}/{len(self.servers)} connected")
        print(f"   🧪 Total Labs: {total_labs}")
        print(f"   🤖 Total Bots: {total_bots} ({total_active_bots} active)")
        print(f"   📈 Unique Markets: {len(all_markets)}")
        print(f"   📜 Unique Scripts: {len(all_scripts)}")
        
        # Display detailed information
        if successful_servers > 0:
            print("\n" + "=" * 60)
            print("📋 DETAILED BREAKDOWN")
            print("=" * 60)
            
            # Markets breakdown
            if all_markets:
                print(f"\n📈 MARKETS ({len(all_markets)} total):")
                for market in sorted(all_markets):
                    print(f"   • {market}")
            
            # Scripts breakdown
            if all_scripts:
                print(f"\n📜 SCRIPTS ({len(all_scripts)} total):")
                for script in sorted(all_scripts):
                    print(f"   • {script}")
            
            # Server-specific details
            for server_name, result in results.items():
                if result["success"]:
                    print(f"\n📡 {server_name.upper()} DETAILS:")
                    print("-" * 40)
                    
                    # Labs
                    if result["labs"]["labs"]:
                        print(f"🧪 LABS ({result['labs']['total']}):")
                        for i, lab in enumerate(result["labs"]["labs"][:5], 1):  # Show first 5
                            print(f"   {i}. {lab.name} ({lab.market_tag})")
                        if result["labs"]["total"] > 5:
                            print(f"   ... and {result['labs']['total'] - 5} more")
                    
                    # Bots
                    if result["bots"]["bots"]:
                        print(f"🤖 BOTS ({result['bots']['total']}):")
                        active_bots = [bot for bot in result["bots"]["bots"] if bot.is_active]
                        inactive_bots = [bot for bot in result["bots"]["bots"] if not bot.is_active]
                        
                        if active_bots:
                            print(f"   🟢 Active ({len(active_bots)}):")
                            for i, bot in enumerate(active_bots[:3], 1):  # Show first 3
                                print(f"      {i}. {bot.name} ({bot.market_tag})")
                            if len(active_bots) > 3:
                                print(f"      ... and {len(active_bots) - 3} more")
                        
                        if inactive_bots:
                            print(f"   🔴 Inactive ({len(inactive_bots)}):")
                            for i, bot in enumerate(inactive_bots[:3], 1):  # Show first 3
                                print(f"      {i}. {bot.name} ({bot.market_tag})")
                            if len(inactive_bots) > 3:
                                print(f"      ... and {len(inactive_bots) - 3} more")
        
        return {
            "total_servers": len(self.servers),
            "successful_servers": successful_servers,
            "total_labs": total_labs,
            "total_bots": total_bots,
            "total_active_bots": total_active_bots,
            "unique_markets": len(all_markets),
            "unique_scripts": len(all_scripts),
            "results": results
        }


async def main():
    """Main function to run the comprehensive overview example."""
    overview = ServerOverview()
    
    try:
        results = await overview.generate_overview()
        
        if "error" in results:
            print(f"\n❌ Example failed: {results['error']}")
            return 1
        
        print(f"\n✅ Comprehensive overview completed successfully!")
        print(f"   Connected to {results['successful_servers']}/{results['total_servers']} servers")
        print(f"   Found {results['total_labs']} labs and {results['total_bots']} bots")
        print(f"   Active bots: {results['total_active_bots']}")
        print(f"   Unique markets: {results['unique_markets']}")
        print(f"   Unique scripts: {results['unique_scripts']}")
        
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
