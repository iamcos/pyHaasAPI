#!/usr/bin/env python3
"""
Minimal CLI for testing the server content revision workflow
"""

import asyncio
import json
import argparse
from pathlib import Path

# Direct imports to avoid the full pyHaasAPI import
from pyHaasAPI.core.logging import get_logger
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.api.lab import LabAPI
from pyHaasAPI.api.bot import BotAPI
from pyHaasAPI.api.account import AccountAPI
from pyHaasAPI.api.backtest import BacktestAPI
from pyHaasAPI.services.server_content_manager import ServerContentManager

class MinimalProjectManagerCLI:
    """Minimal project manager CLI for testing"""
    
    def __init__(self):
        self.logger = get_logger("minimal_cli")
        self.settings = Settings()
        self.server_manager = ServerManager(self.settings)
        self.server_content_managers = {}
        self.server_apis = {}
    
    async def connect_to_server(self, server: str):
        """Connect to a specific server"""
        try:
            self.logger.info(f"Connecting to {server}...")
            
            # Ensure tunnel is available
            await self.server_manager.ensure_tunnel(server)
            await self.server_manager.preflight_check(server)
            
            # Create APIs
            client = AsyncHaasClient(host="127.0.0.1", port=8090)
            auth_manager = AuthenticationManager(client)
            
            apis = {
                "lab_api": LabAPI(client, auth_manager),
                "bot_api": BotAPI(client, auth_manager),
                "account_api": AccountAPI(client, auth_manager),
                "backtest_api": BacktestAPI(client, auth_manager)
            }
            
            # Create server content manager
            server_content_manager = ServerContentManager(
                server=server,
                lab_api=apis["lab_api"],
                bot_api=apis["bot_api"],
                backtest_api=apis["backtest_api"],
                account_api=apis["account_api"],
                cache_dir=Path("unified_cache")
            )
            
            self.server_content_managers[server] = server_content_manager
            self.server_apis[server] = apis
            
            self.logger.info(f"✓ Connected to {server}")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Failed to connect to {server}: {e}")
            return False
    
    async def snapshot(self, servers):
        """Take server snapshot"""
        results = {}
        
        for server in servers:
            try:
                if not await self.connect_to_server(server):
                    continue
                
                self.logger.info(f"Taking snapshot of {server}...")
                snapshot = await self.server_content_managers[server].take_snapshot()
                
                results[server] = {
                    "server": snapshot.server,
                    "timestamp": snapshot.timestamp,
                    "labs_count": len(snapshot.labs),
                    "bots_count": len(snapshot.bots),
                    "coins": list(snapshot.coins),
                    "labs_without_bots": list(snapshot.labs_without_bots),
                    "coins_without_labs": list(snapshot.coins_without_labs)
                }
                
                self.logger.info(f"✓ Snapshot completed for {server}: {len(snapshot.labs)} labs, {len(snapshot.bots)} bots")
                
            except Exception as e:
                self.logger.error(f"✗ Snapshot failed for {server}: {e}")
                results[server] = {"error": str(e)}
        
        return results

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Minimal Project Manager CLI")
    parser.add_argument("command", choices=["snapshot"], help="Command to execute")
    parser.add_argument("--servers", nargs="+", default=["srv03"], help="Servers to process")
    
    args = parser.parse_args()
    
    cli = MinimalProjectManagerCLI()
    
    try:
        if args.command == "snapshot":
            result = await cli.snapshot(args.servers)
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Unknown command: {args.command}")
            return 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))


