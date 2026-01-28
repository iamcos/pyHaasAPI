#!/usr/bin/env python3
"""
Download CLI - Comprehensive backtest downloading from all servers
Refactored to use ServerManager and stream data to prevent OOM.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.config.settings import settings as global_settings
from pyHaasAPI.core.server_manager import ServerManager, ServerStatus
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.cli.base import BaseCLI
import hashlib
import shutil


class DownloadCLI(BaseCLI):
    """CLI for downloading all backtests from all servers"""
    
    def __init__(self):
        super().__init__()
        self.server_manager = ServerManager(global_settings)
        self.results = {}
        self.total_backtests = 0
        self.total_labs = 0
        
    async def run(self, args: List[str]) -> int:
        """Run the download CLI"""
        if not args or args[0] == 'help':
            self.print_help()
            return 0
            
        command = args[0]
        
        try:
            # Start background monitoring (optional, but good for health checks)
            await self.server_manager.start_monitoring()
            
            if command == 'everything':
                return await self.download_everything()
            elif command == 'server':
                if len(args) < 2:
                    print("❌ Server name required. Usage: download server <server_name>")
                    return 1
                return await self.download_from_server(args[1])
            elif command == 'lab':
                if len(args) < 2:
                    print("❌ Lab ID required. Usage: download lab <lab_id>")
                    return 1
                return await self.download_from_lab(args[1])
            elif command == 'backtests-for-labs':
                server = None
                for i, arg in enumerate(args):
                    if arg == '--server' and i + 1 < len(args):
                        server = args[i + 1]
                        break
                if not server:
                    print("❌ Server name required. Usage: download backtests-for-labs --server <server_name>")
                    return 1
                return await self.download_backtests_for_labs(server)
            elif command == 'scripts':
                return await self.download_scripts()
            else:
                print(f"❌ Unknown command: {command}")
                self.print_help()
                return 1
        finally:
            await self.server_manager.shutdown()
    
    def print_help(self):
        """Print help information"""
        print("📥 Download CLI - Comprehensive Backtest Downloader")
        print("       (Refactored with Safe Connectivity & Streaming)")
        print()
        print("Usage:")
        print("  download everything                    - Download ALL backtests from ALL servers")
        print("  download server <server_name>          - Download from specific server")
        print("  download lab <lab_id>                  - Download from specific lab (active server)")
        print("  download backtests-for-labs --server <name> - Download backtests for labs without bots")
        print("  download scripts                       - Download all HaasScripts from all servers")
        print("  download help                          - Show this help")
    
    async def download_everything(self) -> int:
        """Download everything from everywhere"""
        print("🚀 DOWNLOADING EVERYTHING FROM EVERYWHERE...")
        
        servers = ["srv02", "srv03"] # Define target servers
        
        for server_name in servers:
            try:
                # Use ServerManager to switch/connect
                print(f"\n🌐 Connecting to {server_name}...")
                if await self.server_manager.switch_server(server_name):
                     print(f"✅ Connected to {server_name}")
                     await self._download_everything_from_server(server_name)
                else:
                     print(f"❌ Failed to connect to {server_name}")
            except Exception as e:
                print(f"❌ Error processing {server_name}: {e}")
        
        self._print_summary()
        return 0

    async def download_from_server(self, server_name: str) -> int:
        """Download everything from a specific server"""
        print(f"🚀 Downloading everything from {server_name}...")
        
        if await self.server_manager.switch_server(server_name):
             await self._download_everything_from_server(server_name)
             self._print_summary()
             return 0
        else:
             print(f"❌ Failed to connect to {server_name}")
             return 1

    async def _download_everything_from_server(self, server_name: str):
        """Internal method to download from connected server with streaming"""
        # Get active config for port
        active_config = self.server_manager.get_active_server_config()
        if not active_config:
            print("❌ No active server config found")
            return

        # Setup Client
        api_config = APIConfig()
        api_config.host = "127.0.0.1"
        api_config.port = active_config.local_ports[0] # Use primary port 8090
        
        client = AsyncHaasClient(api_config)
        auth_manager = AuthenticationManager(client, api_config)
        
        try:
            await client.connect()
            await auth_manager.authenticate()
            print(f"✅ Authenticated with API on {server_name}")
            
            lab_api = LabAPI(client, auth_manager)
            backtest_api = BacktestAPI(client, auth_manager)
            
            labs = await lab_api.get_labs()
            labs_with_backtests = [lab for lab in labs if lab.completed_backtests > 0]
            print(f"📊 Found {len(labs)} labs, {len(labs_with_backtests)} with backtests")
            
            # Create output directory
            base_dir = Path("unified_cache")
            base_dir.mkdir(exist_ok=True)
            (base_dir / "backtests").mkdir(exist_ok=True)
            
            server_total = 0
            
            for i, lab in enumerate(labs_with_backtests):
                print(f"\n📥 Processing Lab {i+1}/{len(labs_with_backtests)}: {lab.name} ({lab.lab_id})")
                
                # Fetch backtests (using pagination or high limit)
                # To prevent memory overload, we should fetch and write in batches if API supports it,
                # but get_all_backtests_for_lab fetches all.
                # Ideally, we should modify get_all_backtests_for_lab to be a generator/iterator.
                # For now, we assume a single lab's backtests fit in memory (usually < 10k), 
                # but we MUST NOT accumulate all labs' backtests in a giant list.
                
                try:
                    # Timeout protection per lab
                    backtests = await asyncio.wait_for(
                        backtest_api.get_all_backtests_for_lab(lab.lab_id, max_pages=1000),
                        timeout=120.0
                    )
                    
                    if not backtests:
                        print(f"   ⚠️ No backtests returned despite count {lab.completed_backtests}")
                        continue
                        
                    # Write to disk IMMEDIATELY
                    saved_count = 0
                    for bt in backtests:
                        filename = base_dir / "backtests" / f"{server_name}_{lab.lab_id}_{bt.backtest_id}.json"
                        # Create dict manually or utilize to_dict if available (now it is!)
                        bt_data = bt.to_dict()
                        # Enrich with context
                        bt_data['server'] = server_name
                        bt_data['lab_id'] = lab.lab_id
                        
                        with open(filename, 'w') as f:
                            json.dump(bt_data, f, indent=2, default=str)
                        saved_count += 1
                        
                    print(f"   ✅ Saved {saved_count} backtests to disk")
                    server_total += saved_count
                    
                except asyncio.TimeoutError:
                    print(f"   ⏰ Timeout processing lab {lab.lab_id}")
                except Exception as e:
                    print(f"   ❌ Error processing lab {lab.lab_id}: {e}")

            self.results[server_name] = {'total_backtests': server_total}
            self.total_backtests += server_total
            print(f"🎉 {server_name} Complete: {server_total} backtests saved.")
            
        finally:
            await client.close()

    async def download_from_lab(self, lab_id: str) -> int:
        # Re-implement using current server connection
        # Assume user has connected to correct server or we try current
        config = self.server_manager.get_active_server_config()
        if not config:
            print("❌ No active server connection. Connect to a server first.")
            return 1
            
        print(f"🚀 Downloading from lab {lab_id} on active server...")
        # ... Implementation similar to above, for single lab ...
        # For brevity, reusing the logic logic is best.
        # But here I'll just instantiate client and call APIs.
        api_config = APIConfig()
        api_config.host = "127.0.0.1"
        api_config.port = config.local_ports[0]
        
        client = AsyncHaasClient(api_config)
        auth_manager = AuthenticationManager(client, api_config)
        try:
            await client.connect()
            await auth_manager.authenticate()
            
            backtest_api = BacktestAPI(client, auth_manager)
            backtests = await backtest_api.get_all_backtests_for_lab(lab_id, max_pages=1000)
            
            print(f"✅ Downloaded {len(backtests)} backtests")
            # Save logic...
            filename = f"lab_{lab_id}_backtests.json"
            with open(filename, 'w') as f:
                json.dump([b.to_dict() for b in backtests], f, indent=2, default=str)
            print(f"💾 Saved to {filename}")
            return 0
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
        finally:
            await client.close()

    async def download_backtests_for_labs(self, server_name: str) -> int:
        """Download backtests for labs without bots (legacy/specific logic)"""
        print(f"🚀 Downloading backtests for labs without bots on {server_name}...")
        
        if not await self.server_manager.switch_server(server_name):
             print(f"❌ Failed to connect to {server_name}")
             return 1
             
        # Import Manager - assumed available
        from pyHaasAPI.services.server_content_manager import ServerContentManager
        from pyHaasAPI.api.bot.bot_api import BotAPI
        from pyHaasAPI.api.account.account_api import AccountAPI
        
        config = self.server_manager.get_active_server_config()
        api_config = APIConfig()
        api_config.host = "127.0.0.1"
        api_config.port = config.local_ports[0]
        
        client = AsyncHaasClient(api_config)
        auth_manager = AuthenticationManager(client, api_config)
        
        try:
            await client.connect()
            await auth_manager.authenticate()
            
            lab_api = LabAPI(client, auth_manager)
            bot_api = BotAPI(client, auth_manager)
            backtest_api = BacktestAPI(client, auth_manager)
            account_api = AccountAPI(client, auth_manager)
            
            manager = ServerContentManager(
                server=server_name,
                lab_api=lab_api,
                bot_api=bot_api,
                backtest_api=backtest_api,
                account_api=account_api,
                cache_dir="unified_cache"
            )
            
            snapshot = await manager.snapshot()
            if not snapshot.labs_without_bots:
                print("✅ All labs have bots.")
                return 0
                
            # Download Loop
            base_dir = Path("unified_cache/backtests")
            base_dir.mkdir(parents=True, exist_ok=True)
            
            for i, lab_id in enumerate(snapshot.labs_without_bots, 1):
                print(f"Processing {i}: {lab_id}")
                try:
                     bts = await backtest_api.get_all_backtests_for_lab(lab_id, max_pages=1000)
                     for bt in bts:
                         fpath = base_dir / f"{server_name}_{lab_id}_{bt.backtest_id}.json"
                         data = bt.to_dict()
                         with open(fpath, 'w') as f:
                             json.dump(data, f, indent=2, default=str)
                except Exception as e:
                    print(f"Error on lab {lab_id}: {e}")
            
            return 0
            
        finally:
            await client.close()

    def _print_summary(self):
        print("\n📊 Summary:")
        for k, v in self.results.items():
            print(f"   {k}: {v.get('total_backtests', 0)} backtests")

    async def download_scripts(self, server_names=None, direct_config=None) -> int:
        """
        Download all scripts from all servers
        
        Args:
            server_names: List of specific server names to download from
            direct_config: Dict with 'host', 'port', 'email', 'password' for direct connection
        """
        output_dir = Path("haasScripts")
        output_dir.mkdir(exist_ok=True)
        
        # Case 1: Direct Connection
        if direct_config:
            return await self._download_scripts_direct(direct_config, output_dir)
            
        # Case 2: Standard Server Manager (with optional filtering)
        print("📥 Downloading scripts via Server Manager...")
        
        servers_to_try = ["srv01", "srv02", "srv03"]
        if server_names:
            # Filter servers
            servers_to_try = [s for s in servers_to_try if s in server_names]
            if not servers_to_try:
                print(f"❌ No valid servers found matching: {server_names}")
                return 1
            print(f"🎯 Targeted servers: {servers_to_try}")
        
        total_downloaded = 0
        
        for server_name in servers_to_try:
            print(f"\n🌐 Connecting to {server_name}...")
            try:
                # Attempt to switch/connect to the server
                success = await self.server_manager.switch_server(server_name)
                if not success:
                    print(f"❌ Could not connect to {server_name}, skipping.")
                    continue

                # Wait a bit for the tunnel to stabilize
                await asyncio.sleep(1)

                # Get active config for port
                active_config = self.server_manager.get_active_server_config()
                if not active_config:
                    print(f"❌ No active configuration found for {server_name}")
                    continue

                # Initialize API components
                config = APIConfig()
                config.host = '127.0.0.1'
                config.port = active_config.local_ports[0]
                
                downloaded = await self._download_scripts_from_client(config, server_name, output_dir)
                total_downloaded += downloaded
                    
            except Exception as e:
                print(f"❌ Error connecting to {server_name}: {e}")
        
        print(f"\n🎉 Finished! Total scripts downloaded: {total_downloaded}")
        return 0

    async def _download_scripts_direct(self, config_dict, output_dir):
        """Download scripts using direct connection parameters"""
        host = config_dict.get('host')
        port = config_dict.get('port', 8090)
        email = config_dict.get('email')
        password = config_dict.get('password')
        
        if not host or not email or not password:
            print("❌ Host, email, and password are required for direct connection")
            return 1
            
        print(f"🌐 Connecting directly to {host}:{port}...")
        
        config = APIConfig()
        config.host = host
        config.port = int(port)
        # Disable SSL verification if it's a local IP or if requested (assuming safe for now)
        # config.verify_ssl = False 
        
        # Create auth headers manually if needed, but AuthManager should handle it
        
        try:
            downloaded = await self._download_scripts_from_client(
                config, 
                host, 
                output_dir, 
                auth_creds=(email, password)
            )
            print(f"\n🎉 Finished! Total scripts downloaded: {downloaded}")
            return 0
        except Exception as e:
            print(f"❌ Direct connection failed: {e}")
            return 1

    async def _download_scripts_from_client(self, config, server_name, output_dir, auth_creds=None) -> int:
        """Internal helper to download scripts using a configured client"""
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        
        try:
            # Authenticate
            if auth_creds:
                await auth_manager.authenticate(auth_creds[0], auth_creds[1])
            else:
                await auth_manager.authenticate() # Use env vars
                
            print(f"✅ Authenticated on {server_name}")
            
            script_api = ScriptAPI(client, auth_manager)
            
            # Download scripts
            server_output_dir = output_dir / server_name
            server_output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"🔍 Fetching scripts from {server_name}...")
            scripts = await script_api.get_all_scripts()
            print(f"📊 Found {len(scripts)} scripts on {server_name}")
            
            server_count = 0
            for script in scripts:
                # Clean filename
                script_name = script.name.replace("/", "_").replace("\\", "_")
                if not script_name:
                    script_name = f"unnamed_{script.script_id}"
                
                file_path = server_output_dir / f"{script_name}.hs"
                
                # Get source code
                source_code = script.source_code
                if not source_code:
                    try:
                        full_script = await script_api.get_script_item(script.script_id)
                        source_code = full_script.source_code
                    except Exception as e:
                        print(f"   ⚠️ Failed to fetch source for {script_name}: {e}")
                        continue
                
                if source_code:
                    new_content = source_code.encode("utf-8")
                    new_hash = hashlib.md5(new_content).hexdigest()
                    
                    should_save = True
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            old_content = f.read()
                        old_hash = hashlib.md5(old_content).hexdigest()
                        
                        if old_hash == new_hash:
                            should_save = False
                        else:
                            # Versioning: backup old file
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            backup_path = file_path.with_name(f"{file_path.stem}_{timestamp}{file_path.suffix}")
                            shutil.copy2(file_path, backup_path)
                            print(f"   🔄 Version change detected for {script_name}. Backup created: {backup_path.name}")
                    
                    if should_save:
                        with open(file_path, "wb") as f:
                            f.write(new_content)
                        server_count += 1
                    # else: skip (already up to date)
                else:
                    print(f"   ⚠️ Script {script_name} has no source code")
            
            print(f"✅ Saved {server_count} scripts to {server_name}/")
            return server_count
            
        except Exception as e:
            print(f"❌ Error on {server_name}: {e}")
            # If explicit credentials failed, log it
            if auth_creds: 
                 print("   (Check your email/password)")
            return 0
        finally:
            await client.close()
