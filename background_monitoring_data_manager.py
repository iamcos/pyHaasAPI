#!/usr/bin/env python3
"""
Background Monitoring Data Manager

This script implements background monitoring and data refresh for all servers
with automatic reconnection and health monitoring.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


class BackgroundMonitoringDataManager:
    """Data manager with background monitoring capabilities"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
        self.monitoring_task = None
        self.refresh_interval = 300  # 5 minutes
        self.health_check_interval = 60  # 1 minute
        self.running = False
    
    async def connect_to_server(self, server_name):
        """Connect to a specific server"""
        try:
            # Establish SSH tunnel
            ssh_process = await self._establish_ssh_tunnel(server_name)
            if not ssh_process:
                return False
            
            self.ssh_processes[server_name] = ssh_process
            
            # Get credentials
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            
            if not email or not password:
                print("API_EMAIL and API_PASSWORD environment variables are required")
                return False
            
            # Initialize analyzer and connect
            cache = UnifiedCacheManager()
            analyzer = HaasAnalyzer(cache)
            success = analyzer.connect(
                host='127.0.0.1',
                port=8090,
                email=email,
                password=password
            )
            
            if success:
                self.servers[server_name] = {
                    'analyzer': analyzer,
                    'executor': analyzer.executor,
                    'cache': cache,
                    'labs': [],
                    'bots': [],
                    'accounts': [],
                    'backtests': {},
                    'last_update': None,
                    'connection_status': 'connected',
                    'error_count': 0
                }
                print(f"Successfully connected to {server_name}")
                return True
            else:
                print(f"Failed to connect to {server_name}")
                return False
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _establish_ssh_tunnel(self, server_name):
        """Establish SSH tunnel to server"""
        try:
            print(f"Connecting to {server_name}...")
            
            # SSH command for tunnel
            ssh_cmd = [
                "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
                f"prod@{server_name}"
            ]
            
            # Start SSH process
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # Wait a moment for tunnel to establish
            await asyncio.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"SSH tunnel established to {server_name} (PID: {process.pid})")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"SSH tunnel failed for {server_name}: {stderr.decode()}")
                return None
                
        except Exception as e:
            print(f"Failed to establish SSH tunnel to {server_name}: {e}")
            return None
    
    async def fetch_server_data(self, server_name):
        """Fetch all data from a specific server"""
        if server_name not in self.servers:
            print(f"No connection to {server_name}")
            return False
        
        try:
            server_data = self.servers[server_name]
            executor = server_data['executor']
            
            print(f"Fetching data from {server_name}...")
            
            # Fetch labs
            labs = api.get_all_labs(executor)
            server_data['labs'] = labs
            
            # Fetch bots
            bots = api.get_all_bots(executor)
            server_data['bots'] = bots
            
            # Fetch accounts
            accounts = api.get_all_accounts(executor)
            server_data['accounts'] = accounts
            
            # Fetch backtests for each lab (limit to first 2 labs for monitoring)
            total_backtests = 0
            for lab in labs[:2]:
                lab_id = lab.lab_id
                try:
                    from pyHaasAPI.model import GetBacktestResultRequest
                    request = GetBacktestResultRequest(
                        lab_id=lab_id,
                        next_page_id=0,
                        page_lenght=20  # Limit for monitoring
                    )
                    backtest_results = api.get_backtest_result(executor, request)
                    
                    if backtest_results and hasattr(backtest_results, '__iter__'):
                        result_list = list(backtest_results)
                        
                        # Find the "items" tuple
                        for result_tuple in result_list:
                            if result_tuple[0] == "items":
                                lab_backtests = result_tuple[1]
                                server_data['backtests'][lab_id] = lab_backtests
                                total_backtests += len(lab_backtests)
                                break
                        else:
                            print(f"    No backtests found for lab {lab_id}")
                    else:
                        print(f"    No backtest results for lab {lab_id}")
                        
                except Exception as e:
                    print(f"    Failed to fetch backtests for lab {lab_id}: {e}")
                    continue
            
            # Update timestamp and reset error count
            server_data['last_update'] = datetime.now()
            server_data['error_count'] = 0
            server_data['connection_status'] = 'connected'
            
            print(f"  Updated {server_name}: {len(labs)} labs, {len(bots)} bots, {len(accounts)} accounts, {total_backtests} backtests")
            return True
            
        except Exception as e:
            print(f"Failed to fetch data from {server_name}: {e}")
            server_data['error_count'] += 1
            server_data['connection_status'] = 'error'
            return False
    
    async def health_check(self):
        """Perform health check on all servers"""
        print(f"\nHealth Check - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 50)
        
        for server_name, server_data in self.servers.items():
            status = server_data['connection_status']
            last_update = server_data['last_update']
            error_count = server_data['error_count']
            
            if last_update:
                time_since_update = datetime.now() - last_update
                print(f"{server_name}: {status} (last update: {time_since_update.total_seconds():.0f}s ago, errors: {error_count})")
            else:
                print(f"{server_name}: {status} (no updates yet, errors: {error_count})")
            
            # Check if server needs reconnection
            if error_count > 3 or status == 'error':
                print(f"  Reconnecting to {server_name}...")
                await self._reconnect_server(server_name)
    
    async def _reconnect_server(self, server_name):
        """Reconnect to a server"""
        try:
            # Clean up existing connection
            if server_name in self.ssh_processes:
                await self._cleanup_ssh_tunnel(self.ssh_processes[server_name])
                del self.ssh_processes[server_name]
            
            if server_name in self.servers:
                del self.servers[server_name]
            
            # Reconnect
            await asyncio.sleep(2)  # Brief delay before reconnection
            success = await self.connect_to_server(server_name)
            
            if success:
                print(f"  Successfully reconnected to {server_name}")
                # Fetch data immediately after reconnection
                await self.fetch_server_data(server_name)
            else:
                print(f"  Failed to reconnect to {server_name}")
                
        except Exception as e:
            print(f"  Error reconnecting to {server_name}: {e}")
    
    async def background_monitoring(self):
        """Background monitoring task"""
        print("Starting background monitoring...")
        self.running = True
        
        while self.running:
            try:
                # Health check
                await self.health_check()
                
                # Refresh data for all connected servers
                for server_name in list(self.servers.keys()):
                    if self.servers[server_name]['connection_status'] == 'connected':
                        await self.fetch_server_data(server_name)
                
                # Wait for next cycle
                await asyncio.sleep(self.refresh_interval)
                
            except Exception as e:
                print(f"Error in background monitoring: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def start_monitoring(self, servers=None):
        """Start background monitoring for specified servers"""
        if servers is None:
            servers = ["srv01", "srv02", "srv03"]
        
        print(f"Starting background monitoring for servers: {servers}")
        
        # Connect to all servers
        for server in servers:
            await self.connect_to_server(server)
        
        # Start background monitoring task
        self.monitoring_task = asyncio.create_task(self.background_monitoring())
        
        return len(self.servers)
    
    async def stop_monitoring(self):
        """Stop background monitoring"""
        print("Stopping background monitoring...")
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all connections
        await self.cleanup_all()
    
    def get_status_summary(self):
        """Get status summary for all servers"""
        summary = {}
        for server_name, server_data in self.servers.items():
            summary[server_name] = {
                'status': server_data['connection_status'],
                'labs': len(server_data['labs']),
                'bots': len(server_data['bots']),
                'accounts': len(server_data['accounts']),
                'backtests': sum(len(bt) for bt in server_data['backtests'].values()),
                'last_update': server_data['last_update'].isoformat() if server_data['last_update'] else None,
                'error_count': server_data['error_count']
            }
        return summary
    
    async def _cleanup_ssh_tunnel(self, process):
        """Clean up SSH tunnel"""
        try:
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        except Exception as e:
            print(f"Error cleaning up SSH tunnel: {e}")
    
    async def cleanup_all(self):
        """Clean up all SSH tunnels"""
        for server_name, process in self.ssh_processes.items():
            print(f"Cleaning up {server_name}...")
            await self._cleanup_ssh_tunnel(process)


async def test_background_monitoring():
    """Test the background monitoring data manager"""
    print("Testing Background Monitoring Data Manager")
    print("=" * 60)
    
    data_manager = BackgroundMonitoringDataManager()
    
    try:
        # Start monitoring for srv01 only (for testing)
        connected_count = await data_manager.start_monitoring(["srv01"])
        print(f"Connected to {connected_count} servers")
        
        if connected_count == 0:
            print("No servers connected. Exiting.")
            return 1
        
        # Let it run for a few cycles
        print("\nRunning background monitoring for 2 cycles...")
        await asyncio.sleep(10)  # Let it run for 10 seconds
        
        # Show status
        print("\nStatus Summary:")
        summary = data_manager.get_status_summary()
        for server_name, status in summary.items():
            print(f"\n{server_name.upper()}:")
            print(f"  Status: {status['status']}")
            print(f"  Labs: {status['labs']}")
            print(f"  Bots: {status['bots']}")
            print(f"  Accounts: {status['accounts']}")
            print(f"  Backtests: {status['backtests']}")
            print(f"  Last Update: {status['last_update']}")
            print(f"  Error Count: {status['error_count']}")
        
        print("\nBackground monitoring test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Stop monitoring and cleanup
        await data_manager.stop_monitoring()


async def main():
    """Main entry point"""
    return await test_background_monitoring()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

