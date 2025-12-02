#!/usr/bin/env python3
"""
Download CLI - Comprehensive backtest downloading from all servers
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.cli.base import BaseCLI
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings


class DownloadCLI(BaseCLI):
    """CLI for downloading all backtests from all servers"""
    
    def __init__(self):
        super().__init__()
        self.results = {}
        self.total_backtests = 0
        self.total_labs = 0
    
    async def connect(self) -> bool:
        """Override connect to skip tunnel check - we manage tunnels ourselves"""
        # DownloadCLI manages its own connections via ServerManager
        # Don't call parent connect() which checks for tunnel
        return True
        
    async def run(self, args: List[str]) -> int:
        """Run the download CLI"""
        if not args or args[0] == 'help':
            self.print_help()
            return 0
            
        command = args[0]
        
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
            if len(args) < 2:
                print("❌ Server name required. Usage: download backtests-for-labs --server <server_name>")
                return 1
            # Parse server from args
            server = None
            for i, arg in enumerate(args):
                if arg == '--server' and i + 1 < len(args):
                    server = args[i + 1]
                    break
            if not server:
                print("❌ Server name required. Usage: download backtests-for-labs --server <server_name>")
                return 1
            return await self.download_backtests_for_labs(server)
        else:
            print(f"❌ Unknown command: {command}")
            self.print_help()
            return 1
    
    def print_help(self):
        """Print help information"""
        print("📥 Download CLI - Comprehensive Backtest Downloader")
        print()
        print("Usage:")
        print("  download everything                    - Download ALL backtests from ALL servers (srv01, srv02, srv03)")
        print("  download server <server_name>          - Download from specific server (srv01, srv02, or srv03)")
        print("  download lab <lab_id>                  - Download from specific lab")
        print("  download backtests-for-labs --server <name> - Download backtests for labs without bots")
        print("  download help                          - Show this help")
        print()
        print("Examples:")
        print("  download everything")
        print("  download server srv01")
        print("  download server srv02")
        print("  download server srv03")
        print("  download lab 272bbb66-f2b3-4eae-8c32-714747dcb827")
        print()
        print("Note: Uses SSH tunnels managed by ServerManager. Authentication via API_EMAIL and API_PASSWORD from .env")
    
    async def download_everything(self) -> int:
        """Download everything from everywhere - all 3 servers (srv01, srv02, srv03)"""
        print("🚀 DOWNLOADING EVERYTHING FROM EVERYWHERE...")
        print("🎯 Target: EVERY backtest from EVERY lab on EVERY server (srv01, srv02, srv03)")
        
        # Define all servers
        servers = ['srv01', 'srv02', 'srv03']
        
        # Initialize ServerManager
        settings = Settings()
        server_manager = ServerManager(settings)
        
        successful_servers = []
        
        # Process each server sequentially (single-tunnel policy)
        for server_name in servers:
            print(f"\n{'='*60}")
            print(f"🌐 Processing server: {server_name}")
            print(f"{'='*60}")
            
            try:
                # Connect to server using ServerManager
                print(f"🔗 Establishing SSH tunnel to {server_name}...")
                if await server_manager.connect_server(server_name):
                    print(f"✅ Connected to {server_name}")
                    
                    # Preflight check
                    if await server_manager.preflight_check():
                        print(f"✅ Preflight check passed for {server_name}")
                        
                        # Download everything from this server
                        print(f"📥 Downloading EVERYTHING from {server_name}...")
                        server_results = await self._download_everything_from_server_via_manager(server_name, server_manager)
                        self.results[server_name] = server_results
                        self.total_labs += server_results.get('total_labs', 0)
                        self.total_backtests += server_results.get('total_backtests', 0)
                        print(f"✅ {server_name}: {server_results.get('total_labs', 0)} labs, {server_results.get('total_backtests', 0)} backtests")
                        successful_servers.append(server_name)
                    else:
                        print(f"❌ Preflight check failed for {server_name}")
                        self.results[server_name] = {'error': 'Preflight check failed', 'labs': [], 'total_labs': 0, 'total_backtests': 0}
                else:
                    print(f"❌ Failed to connect to {server_name}")
                    self.results[server_name] = {'error': 'Connection failed', 'labs': [], 'total_labs': 0, 'total_backtests': 0}
                
                # Disconnect from current server before moving to next (single-tunnel policy)
                print(f"🔌 Disconnecting from {server_name}...")
                await server_manager.disconnect_server(server_name)
                await asyncio.sleep(2)  # Brief pause between servers
                
            except Exception as e:
                print(f"❌ Error processing {server_name}: {e}")
                import traceback
                traceback.print_exc()
                self.results[server_name] = {'error': str(e), 'labs': [], 'total_labs': 0, 'total_backtests': 0}
                
                # Ensure cleanup
                try:
                    await server_manager.disconnect_server(server_name)
                except Exception:
                    pass
        
        if not successful_servers:
            print("\n❌ No servers were successfully processed!")
            return 1
        
        print(f"\n🎯 Successfully processed {len(successful_servers)} servers: {successful_servers}")
        
        # Save results
        filename = self._save_results()
        print(f"\n💾 Complete database saved to: {filename}")
        
        # Print summary
        self._print_summary()
        
        return 0
    
    async def download_from_server(self, server_name: str) -> int:
        """Download everything from a specific server"""
        print(f"🚀 Downloading everything from {server_name}...")
        
        # Validate server name
        valid_servers = ['srv01', 'srv02', 'srv03']
        if server_name not in valid_servers:
            print(f"❌ Unknown server: {server_name}")
            print(f"Available servers: {', '.join(valid_servers)}")
            return 1
        
        # Initialize ServerManager
        settings = Settings()
        server_manager = ServerManager(settings)
        
        try:
            # Connect to server using ServerManager
            print(f"🔗 Establishing SSH tunnel to {server_name}...")
            if await server_manager.connect_server(server_name):
                print(f"✅ Connected to {server_name}")
                
                # Preflight check
                if await server_manager.preflight_check():
                    print(f"✅ Preflight check passed for {server_name}")
                    
                    # Download everything from this server
                    print(f"📥 Downloading EVERYTHING from {server_name}...")
                    server_results = await self._download_everything_from_server_via_manager(server_name, server_manager)
                    self.results[server_name] = server_results
                    self.total_labs += server_results.get('total_labs', 0)
                    self.total_backtests += server_results.get('total_backtests', 0)
                    print(f"✅ {server_name}: {server_results.get('total_labs', 0)} labs, {server_results.get('total_backtests', 0)} backtests")
                    
                    # Save results
                    filename = self._save_results()
                    print(f"\n💾 Results saved to: {filename}")
                    
                    # Print summary
                    self._print_summary()
                    
                    return 0
                else:
                    print(f"❌ Preflight check failed for {server_name}")
                    return 1
            else:
                print(f"❌ Failed to connect to {server_name}")
                return 1
        except Exception as e:
            print(f"❌ Error downloading from {server_name}: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            # Disconnect from server
            try:
                await server_manager.disconnect_server(server_name)
            except Exception:
                pass
    
    async def download_from_lab(self, lab_id: str) -> int:
        """Download everything from a specific lab"""
        print(f"🚀 Downloading everything from lab {lab_id}...")
        
        try:
            # Connect to srv02 (default)
            config = APIConfig()
            client = AsyncHaasClient(config)
            auth_manager = AuthenticationManager(client, config)
            
            await client.connect()
            await auth_manager.authenticate()
            print("✅ Authenticated")
            
            # Get lab info
            lab_api = LabAPI(client, auth_manager)
            labs = await lab_api.get_labs()
            target_lab = None
            
            for lab in labs:
                if lab.lab_id == lab_id:
                    target_lab = lab
                    break
            
            if not target_lab:
                print(f"❌ Lab {lab_id} not found")
                return 1
            
            print(f"📊 Lab: {target_lab.name}")
            print(f"📈 Expected backtests: {target_lab.completed_backtests}")
            
            # Download all backtests
            backtest_api = BacktestAPI(client, auth_manager)
            backtests = await backtest_api.get_all_backtests_for_lab(lab_id, max_pages=1000)
            
            print(f"✅ Downloaded {len(backtests)} backtests")
            
            # Save results
            lab_data = {
                'lab_id': target_lab.lab_id,
                'lab_name': target_lab.name,
                'script_id': target_lab.script_id,
                'status': target_lab.status,
                'completed_backtests': target_lab.completed_backtests,
                'downloaded_backtests': len(backtests),
                'backtests': []
            }
            
            # Process each backtest
            for bt in backtests:
                bt_data = {
                    'backtest_id': getattr(bt, 'backtest_id', 'N/A'),
                    'realized_profits_usdt': getattr(bt, 'realized_profits_usdt', 0),
                    'starting_balance': getattr(bt, 'starting_balance', 0),
                    'total_trades': getattr(bt, 'total_trades', 0),
                    'win_rate': getattr(bt, 'win_rate', 0),
                    'max_drawdown': getattr(bt, 'max_drawdown', 0),
                    'roi': getattr(bt, 'roi', 0),
                    'roe': getattr(bt, 'roe', 0),
                    'created_at': getattr(bt, 'created_at', 'N/A'),
                    'updated_at': getattr(bt, 'updated_at', 'N/A')
                }
                lab_data['backtests'].append(bt_data)
            
            # Save to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'lab_{lab_id}_backtests_{timestamp}.json'
            
            with open(filename, 'w') as f:
                json.dump(lab_data, f, indent=2, default=str)
            
            print(f"💾 Results saved to: {filename}")
            
            # Show stats
            if backtests:
                rois = [getattr(bt, 'roi', 0) for bt in backtests if hasattr(bt, 'roi')]
                if rois:
                    avg_roi = sum(rois) / len(rois)
                    max_roi = max(rois)
                    min_roi = min(rois)
                    print(f"📈 Stats: Avg ROI={avg_roi:.2f}%, Max ROI={max_roi:.2f}%, Min ROI={min_roi:.2f}%")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
        finally:
            await client.close()
    
    async def _setup_server_connection(self, server: Dict[str, str]) -> bool:
        """Setup connection to a server"""
        try:
            if server['name'] == 'srv02':
                # srv02 tunnel is already running
                return True
            elif server['name'] == 'srv03':
                # Start srv03 tunnel
                print(f"🔗 Starting tunnel for {server['name']}...")
                import subprocess
                tunnel_process = subprocess.Popen(
                    server['tunnel_cmd'].split(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Wait for tunnel to establish
                await asyncio.sleep(5)
                
                # Test connection
                return await self._test_connection(server['port'])
            else:
                return False
        except Exception as e:
            print(f"Tunnel setup failed for {server['name']}: {e}")
            return False
    
    async def _test_connection(self, port: int) -> bool:
        """Test if a port is accessible"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://127.0.0.1:{port}/UserAPI.php?channel=REFRESH_LICENSE', 
                                     timeout=aiohttp.ClientTimeout(total=10)) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _download_everything_from_server_via_manager(self, server_name: str, server_manager: ServerManager) -> Dict[str, Any]:
        """Download everything from a specific server using ServerManager"""
        print(f"🔗 Setting up connection to {server_name}...")
        
        # Create config - using standard localhost ports (8090, 8092) via tunnel
        server_config = APIConfig()
        server_config.host = "127.0.0.1"
        server_config.port = 8090  # Standard port via tunnel
        
        # Setup client for this server
        client = AsyncHaasClient(server_config)
        auth_manager = AuthenticationManager(client, server_config)
        
        try:
            # Connect and authenticate
            await client.connect()
            await auth_manager.authenticate()
            print(f"✅ Authenticated with {server_name}")
            
            # Get ALL labs
            lab_api = LabAPI(client, auth_manager)
            labs = await lab_api.get_labs()
            print(f"📊 Found {len(labs)} labs on {server_name}")
            
            # Filter labs with backtests - handle both dict and object access
            def get_completed_backtests(lab):
                if isinstance(lab, dict):
                    # API returns 'CB' for completed backtests
                    return lab.get('CB', 0) or lab.get('completed_backtests', 0) or lab.get('completedBacktests', 0) or 0
                return getattr(lab, 'completed_backtests', 0) or getattr(lab, 'completedBacktests', 0) or getattr(lab, 'CB', 0) or 0
            
            labs_with_backtests = [lab for lab in labs if get_completed_backtests(lab) > 0]
            print(f"🎯 {len(labs_with_backtests)} labs have backtests on {server_name}")
            
            if not labs_with_backtests:
                print(f"⚠️  No labs with backtests found on {server_name}")
                return {
                    'server': server_name,
                    'total_labs': 0,
                    'total_backtests': 0,
                    'labs': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Download everything for each lab
            backtest_api = BacktestAPI(client, auth_manager)
            server_labs = []
            server_total_backtests = 0
            
            for i, lab in enumerate(labs_with_backtests):
                # Get lab attributes - handle both dict and object
                def get_lab_attr(lab, attr, default=''):
                    if isinstance(lab, dict):
                        # Map common field names to API keys
                        field_map = {
                            'lab_id': 'LID',
                            'name': 'N',
                            'script_id': 'SID',
                            'status': 'S',
                            'scheduled_backtests': 'SB',
                            'completed_backtests': 'CB'
                        }
                        api_key = field_map.get(attr, attr)
                        return lab.get(api_key, lab.get(attr, lab.get(attr.replace('_', ''), default)))
                    return getattr(lab, attr, default)
                
                lab_name = get_lab_attr(lab, 'name', 'Unknown')
                lab_id = get_lab_attr(lab, 'lab_id', '')
                completed_backtests = get_completed_backtests(lab)
                
                print(f"\n📥 Lab {i+1}/{len(labs_with_backtests)}: {lab_name}")
                print(f"   Expected: {completed_backtests} backtests")
                
                try:
                    # Download ALL backtests for this lab - NO LIMITS
                    print(f"   🔄 Downloading ALL backtests (max_pages=1000)...")
                    backtests = await backtest_api.get_all_backtests_for_lab(
                        lab_id, 
                        max_pages=1000  # Massive limit to get everything
                    )
                    
                    print(f"   ✅ Downloaded {len(backtests)} backtests")
                    server_total_backtests += len(backtests)
                    
                    # Process backtest data
                    lab_data = {
                        'lab_id': lab_id,
                        'lab_name': lab_name,
                        'script_id': get_lab_attr(lab, 'script_id', ''),
                        'status': get_lab_attr(lab, 'status', ''),
                        'completed_backtests': completed_backtests,
                        'scheduled_backtests': get_lab_attr(lab, 'scheduled_backtests', 0),
                        'downloaded_backtests': len(backtests),
                        'backtests': []
                    }
                    
                    # Process each backtest with ALL data
                    for bt in backtests:
                        bt_data = {
                            'backtest_id': getattr(bt, 'backtest_id', 'N/A'),
                            'realized_profits_usdt': getattr(bt, 'realized_profits_usdt', 0),
                            'starting_balance': getattr(bt, 'starting_balance', 0),
                            'total_trades': getattr(bt, 'total_trades', 0),
                            'win_rate': getattr(bt, 'win_rate', 0),
                            'max_drawdown': getattr(bt, 'max_drawdown', 0),
                            'roi': getattr(bt, 'roi', 0),
                            'roe': getattr(bt, 'roe', 0),
                            'created_at': getattr(bt, 'created_at', 'N/A'),
                            'updated_at': getattr(bt, 'updated_at', 'N/A'),
                            'profit_factor': getattr(bt, 'profit_factor', 0),
                            'sharpe_ratio': getattr(bt, 'sharpe_ratio', 0),
                            'sortino_ratio': getattr(bt, 'sortino_ratio', 0),
                            'calmar_ratio': getattr(bt, 'calmar_ratio', 0),
                            'max_consecutive_wins': getattr(bt, 'max_consecutive_wins', 0),
                            'max_consecutive_losses': getattr(bt, 'max_consecutive_losses', 0),
                            'average_trade': getattr(bt, 'average_trade', 0),
                            'average_win': getattr(bt, 'average_win', 0),
                            'average_loss': getattr(bt, 'average_loss', 0),
                            'largest_win': getattr(bt, 'largest_win', 0),
                            'largest_loss': getattr(bt, 'largest_loss', 0),
                            'total_fees': getattr(bt, 'total_fees', 0),
                            'net_profit': getattr(bt, 'net_profit', 0),
                            'gross_profit': getattr(bt, 'gross_profit', 0),
                            'gross_loss': getattr(bt, 'gross_loss', 0)
                        }
                        lab_data['backtests'].append(bt_data)
                    
                    server_labs.append(lab_data)
                    
                    # Show comprehensive performance stats
                    if backtests:
                        # Calculate stats
                        rois = [getattr(bt, 'roi', 0) for bt in backtests if hasattr(bt, 'roi')]
                        trades = [getattr(bt, 'total_trades', 0) for bt in backtests if hasattr(bt, 'total_trades')]
                        
                        if rois:
                            avg_roi = sum(rois) / len(rois)
                            max_roi = max(rois)
                            min_roi = min(rois)
                            avg_trades = sum(trades) / len(trades) if trades else 0
                            
                            print(f"   📈 Stats: Avg ROI={avg_roi:.2f}%, Max ROI={max_roi:.2f}%, Min ROI={min_roi:.2f}%")
                            print(f"   📊 Avg Trades: {avg_trades:.1f}")
                
                except Exception as e:
                    print(f"   ❌ Error downloading from lab {lab_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    server_labs.append({
                        'lab_id': lab_id,
                        'lab_name': lab_name,
                        'error': str(e),
                        'backtests': []
                    })
            
            return {
                'server': server_name,
                'total_labs': len(server_labs),
                'total_backtests': server_total_backtests,
                'labs': server_labs,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error with {server_name}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'server': server_name,
                'error': str(e),
                'total_labs': 0,
                'total_backtests': 0,
                'labs': [],
                'timestamp': datetime.now().isoformat()
            }
        finally:
            await client.close()
    
    async def _download_everything_from_server(self, server: Dict[str, str]) -> Dict[str, Any]:
        """Legacy method - kept for compatibility"""
        # This method is deprecated in favor of _download_everything_from_server_via_manager
        # But kept for backward compatibility
        return await self._download_everything_from_server_via_manager(server['name'], None)
    
    def _save_results(self) -> str:
        """Save all results to a comprehensive JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'COMPLETE_BACKTEST_DATABASE_{timestamp}.json'
        
        # Create comprehensive summary
        summary = {
            'download_info': {
                'timestamp': datetime.now().isoformat(),
                'total_servers': len(self.results),
                'total_labs': self.total_labs,
                'total_backtests': self.total_backtests,
                'successful_servers': [s for s, data in self.results.items() if 'error' not in data],
                'failed_servers': [s for s, data in self.results.items() if 'error' in data],
                'description': 'COMPLETE BACKTEST DATABASE - EVERYTHING FROM EVERYWHERE'
            },
            'server_results': self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return filename
    
    def _print_summary(self):
        """Print comprehensive download summary"""
        print(f"\n🎉 COMPLETE DOWNLOAD FINISHED!")
        print(f"📊 COMPREHENSIVE SUMMARY:")
        print(f"   - Servers processed: {len(self.results)}")
        print(f"   - Total labs: {self.total_labs}")
        print(f"   - Total backtests: {self.total_backtests}")
        
        print(f"\n📋 Server Breakdown:")
        for server, data in self.results.items():
            if 'error' in data:
                print(f"   ❌ {server}: ERROR - {data['error']}")
            else:
                print(f"   ✅ {server}: {data['total_labs']} labs, {data['total_backtests']} backtests")
        
        print(f"\n📁 Complete database saved to JSON file")
        print(f"🚀 Ready for bot creation and analysis!")
    
    async def download_backtests_for_labs(self, server: str) -> int:
        """Download ALL backtests for labs without bots and save as individual JSON files"""
        print(f"🚀 Downloading ALL backtests for labs without bots on {server}...")
        
        try:
            # Import required services
            from pyHaasAPI.services.server_content_manager import ServerContentManager
            from pyHaasAPI.api.bot.bot_api import BotAPI
            from pyHaasAPI.api.account.account_api import AccountAPI
            
            # Setup server configuration
            server_configs = {
                'srv01': {'port': 8089, 'tunnel_cmd': 'ssh -N -L 8089:127.0.0.1:8090 -L 8091:127.0.0.1:8092 prod@srv01'},
                'srv02': {'port': 8090, 'tunnel_cmd': None},  # Already running
                'srv03': {'port': 8091, 'tunnel_cmd': 'ssh -N -L 8091:127.0.0.1:8090 -L 8093:127.0.0.1:8092 prod@srv03'},
            }
            
            if server not in server_configs:
                print(f"❌ Unknown server: {server}. Available: srv01, srv02, srv03")
                return 1
            
            config = server_configs[server]
            
            # Setup client for this server
            server_config = APIConfig()
            server_config.host = "127.0.0.1"
            server_config.port = config['port']
            
            # Connect and authenticate
            client = AsyncHaasClient(server_config)
            auth_manager = AuthenticationManager(client, server_config)
            
            await client.connect()
            await auth_manager.authenticate()
            print(f"✅ Connected to {server}")
            
            # Create API instances
            lab_api = LabAPI(client, auth_manager)
            bot_api = BotAPI(client, auth_manager)
            backtest_api = BacktestAPI(client, auth_manager)
            account_api = AccountAPI(client, auth_manager)
            
            # Create ServerContentManager for snapshot only
            manager = ServerContentManager(
                server=server,
                lab_api=lab_api,
                bot_api=bot_api,
                backtest_api=backtest_api,
                account_api=account_api,
                cache_dir="unified_cache"
            )
            
            # Step 1: Snapshot server state
            print(f"📊 Taking snapshot of {server}...")
            snapshot = await manager.snapshot()
            
            print(f"📈 Server snapshot:")
            print(f"   - Total labs: {len(snapshot.labs)}")
            print(f"   - Total bots: {len(snapshot.bots)}")
            print(f"   - Labs without bots: {len(snapshot.labs_without_bots)}")
            
            if not snapshot.labs_without_bots:
                print(f"✅ All labs on {server} already have bots. Nothing to download.")
                return 0
            
            # Step 2: Download ALL backtests for labs without bots
            print(f"📥 Downloading ALL backtests for {len(snapshot.labs_without_bots)} labs without bots...")
            
            # Create backtests directory
            Path("unified_cache/backtests").mkdir(parents=True, exist_ok=True)
            
            # Convert set to list for the API
            lab_ids_without_bots = list(snapshot.labs_without_bots)
            
            # Download results tracking
            download_results = {}
            total_backtests_downloaded = 0
            
            # For each lab without bots, download ALL backtests
            for i, lab_id in enumerate(lab_ids_without_bots, 1):
                lab_name = next((lab.name for lab in snapshot.labs if lab.lab_id == lab_id), lab_id[:8])
                print(f"\n📥 Lab {i}/{len(lab_ids_without_bots)}: {lab_name} ({lab_id[:8]})")
                
                try:
                    # Get ALL backtests for this lab (no page limit)
                    print(f"   🔄 Downloading ALL backtests...")
                    
                    # Add timeout for individual lab downloads
                    import asyncio
                    try:
                        all_backtests = await asyncio.wait_for(
                            backtest_api.get_all_backtests_for_lab(
                                lab_id=lab_id,
                                max_pages=1000  # Download ALL pages
                            ),
                            timeout=60.0  # 60 second timeout per lab
                        )
                    except asyncio.TimeoutError:
                        print(f"   ⏰ Timeout downloading backtests for lab {lab_name} - skipping")
                        download_results[lab_id] = 0
                        continue
                    
                    print(f"   📊 Found {len(all_backtests)} backtests")
                    
                    # Save each backtest as individual JSON file
                    lab_backtests_saved = 0
                    for backtest in all_backtests:
                        filename = f"unified_cache/backtests/{server}_{lab_id}_{backtest.backtest_id}.json"
                        
                        # Extract all backtest data
                        backtest_data = {
                            'lab_id': lab_id,
                            'backtest_id': backtest.backtest_id,
                            'roi': getattr(backtest, 'roi', 0),
                            'roe': getattr(backtest, 'roe', 0),
                            'win_rate': getattr(backtest, 'win_rate', 0),
                            'max_drawdown': getattr(backtest, 'max_drawdown', 0),
                            'total_trades': getattr(backtest, 'total_trades', 0),
                            'realized_profits_usdt': getattr(backtest, 'realized_profits_usdt', 0),
                            'starting_balance': getattr(backtest, 'starting_balance', 0),
                            'created_at': getattr(backtest, 'created_at', 'N/A'),
                            'updated_at': getattr(backtest, 'updated_at', 'N/A'),
                            'status': getattr(backtest, 'status', 'N/A'),
                            'leverage': getattr(backtest, 'leverage', 0),
                            'position_mode': getattr(backtest, 'position_mode', 'N/A'),
                            'margin_mode': getattr(backtest, 'margin_mode', 'N/A')
                        }
                        
                        with open(filename, 'w') as f:
                            json.dump(backtest_data, f, indent=2, default=str)
                        
                        lab_backtests_saved += 1
                    
                    print(f"   ✅ Saved {lab_backtests_saved} backtest files")
                    download_results[lab_id] = lab_backtests_saved
                    total_backtests_downloaded += lab_backtests_saved
                    
                except Exception as e:
                    print(f"   ❌ Error downloading backtests for lab {lab_name}: {e}")
                    download_results[lab_id] = 0
            
            # Step 3: Save snapshot with download results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            snapshot_file = f"unified_cache/snapshots/{server}_{timestamp}.json"
            Path("unified_cache/snapshots").mkdir(parents=True, exist_ok=True)
            
            snapshot_data = {
                'server': server,
                'timestamp': datetime.now().isoformat(),
                'labs': [{'lab_id': lab.lab_id, 'name': lab.name, 'completed_backtests': lab.completed_backtests} for lab in snapshot.labs],
                'bots': [{'bot_id': bot.bot_id, 'bot_name': bot.bot_name} for bot in snapshot.bots],
                'labs_without_bots': list(snapshot.labs_without_bots),
                'download_results': download_results,
                'total_backtests_downloaded': total_backtests_downloaded
            }
            
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2, default=str)
            
            # Summary
            print(f"\n🎉 Download completed for {server}!")
            print(f"📊 Summary:")
            print(f"   - Labs without bots: {len(snapshot.labs_without_bots)}")
            print(f"   - Total backtests downloaded: {total_backtests_downloaded}")
            print(f"   - Individual files created: {total_backtests_downloaded}")
            print(f"   - Snapshot saved: {snapshot_file}")
            
            # Show per-lab results
            print(f"\n📋 Per-lab results:")
            for lab_id, count in download_results.items():
                lab_name = next((lab.name for lab in snapshot.labs if lab.lab_id == lab_id), lab_id[:8])
                print(f"   - {lab_name}: {count} backtests")
            
            # Verify file count
            backtest_files = list(Path("unified_cache/backtests").glob(f"{server}_*"))
            print(f"\n🔍 Verification: Found {len(backtest_files)} backtest files in cache")
            
            # Show file count breakdown by lab
            lab_file_counts = {}
            for file in backtest_files:
                # Extract lab_id from filename: {server}_{lab_id}_{backtest_id}.json
                parts = file.stem.split('_', 2)  # Split into [server, lab_id, backtest_id]
                if len(parts) >= 2:
                    lab_id = parts[1]
                    lab_file_counts[lab_id] = lab_file_counts.get(lab_id, 0) + 1
            
            print(f"📊 File count by lab:")
            for lab_id, count in lab_file_counts.items():
                lab_name = next((lab.name for lab in snapshot.labs if lab.lab_id == lab_id), lab_id[:8])
                print(f"   - {lab_name}: {count} files")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error downloading backtests for {server}: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            await client.close()
