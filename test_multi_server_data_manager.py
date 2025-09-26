#!/usr/bin/env python3
"""
Test Multi-Server Data Manager

This script tests the data manager with multiple servers (srv01, srv02, srv03)
to verify multi-server capabilities.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


async def establish_ssh_tunnel(server_name):
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


async def cleanup_ssh_tunnel(process):
    """Clean up SSH tunnel"""
    try:
        if process and process.poll() is None:
            print("Cleaning up SSH tunnel...")
            process.terminate()
            process.wait(timeout=5)
            print("SSH tunnel cleaned up")
    except Exception as e:
        print(f"Error cleaning up SSH tunnel: {e}")


class MultiServerDataManager:
    """Multi-server data manager for testing"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
    
    async def connect_to_server(self, server_name):
        """Connect to a specific server"""
        try:
            # Establish SSH tunnel
            ssh_process = await establish_ssh_tunnel(server_name)
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
                    'backtests': {}
                }
                print(f"Successfully connected to {server_name}")
                return True
            else:
                print(f"Failed to connect to {server_name}")
                return False
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            return False
    
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
            print(f"  Fetched {len(labs)} labs")
            
            # Fetch bots
            bots = api.get_all_bots(executor)
            server_data['bots'] = bots
            print(f"  Fetched {len(bots)} bots")
            
            # Fetch accounts
            accounts = api.get_all_accounts(executor)
            server_data['accounts'] = accounts
            print(f"  Fetched {len(accounts)} accounts")
            
            # Fetch backtests for each lab (limit to first 3 labs for testing)
            total_backtests = 0
            for lab in labs[:3]:
                lab_id = lab.lab_id
                try:
                    from pyHaasAPI.model import GetBacktestResultRequest
                    request = GetBacktestResultRequest(
                        lab_id=lab_id,
                        next_page_id=0,
                        page_lenght=50  # Limit for testing
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
                                print(f"    Fetched {len(lab_backtests)} backtests for lab {lab_id}")
                                break
                        else:
                            print(f"    No backtests found for lab {lab_id}")
                    else:
                        print(f"    No backtest results for lab {lab_id}")
                        
                except Exception as e:
                    print(f"    Failed to fetch backtests for lab {lab_id}: {e}")
                    continue
            
            print(f"  Total backtests fetched: {total_backtests}")
            return True
            
        except Exception as e:
            print(f"Failed to fetch data from {server_name}: {e}")
            return False
    
    def get_server_summary(self, server_name):
        """Get summary for a specific server"""
        if server_name not in self.servers:
            return None
        
        server_data = self.servers[server_name]
        return {
            'labs': len(server_data['labs']),
            'bots': len(server_data['bots']),
            'accounts': len(server_data['accounts']),
            'backtests': sum(len(bt) for bt in server_data['backtests'].values())
        }
    
    def get_all_summaries(self):
        """Get summaries for all servers"""
        summaries = {}
        for server_name in self.servers:
            summaries[server_name] = self.get_server_summary(server_name)
        return summaries
    
    async def cleanup_all(self):
        """Clean up all SSH tunnels"""
        for server_name, process in self.ssh_processes.items():
            print(f"Cleaning up {server_name}...")
            await cleanup_ssh_tunnel(process)


async def test_multi_server_data_manager():
    """Test the multi-server data manager"""
    print("Testing Multi-Server Data Manager")
    print("=" * 60)
    
    data_manager = MultiServerDataManager()
    
    try:
        # Test servers
        servers_to_test = ["srv01", "srv02", "srv03"]
        connected_servers = []
        
        # Step 1: Connect to servers
        print("Connecting to servers...")
        for server in servers_to_test:
            print(f"\nConnecting to {server}...")
            if await data_manager.connect_to_server(server):
                connected_servers.append(server)
                print(f"Successfully connected to {server}")
            else:
                print(f"Failed to connect to {server}")
        
        print(f"\nConnected to {len(connected_servers)} servers: {connected_servers}")
        
        if not connected_servers:
            print("No servers connected. Exiting.")
            return 1
        
        # Step 2: Fetch data from each server
        print("\nFetching data from servers...")
        for server in connected_servers:
            print(f"\nFetching data from {server}...")
            await data_manager.fetch_server_data(server)
        
        # Step 3: Show summaries
        print("\nServer Summaries:")
        print("=" * 40)
        summaries = data_manager.get_all_summaries()
        
        for server_name, summary in summaries.items():
            if summary:
                print(f"\n{server_name.upper()}:")
                print(f"  Labs: {summary['labs']}")
                print(f"  Bots: {summary['bots']}")
                print(f"  Accounts: {summary['accounts']}")
                print(f"  Backtests: {summary['backtests']}")
            else:
                print(f"\n{server_name.upper()}: No data")
        
        # Step 4: Show total across all servers
        total_labs = sum(s['labs'] for s in summaries.values() if s)
        total_bots = sum(s['bots'] for s in summaries.values() if s)
        total_accounts = sum(s['accounts'] for s in summaries.values() if s)
        total_backtests = sum(s['backtests'] for s in summaries.values() if s)
        
        print(f"\nTOTAL ACROSS ALL SERVERS:")
        print(f"  Labs: {total_labs}")
        print(f"  Bots: {total_bots}")
        print(f"  Accounts: {total_accounts}")
        print(f"  Backtests: {total_backtests}")
        
        print("\nMulti-server data manager test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up all SSH tunnels
        await data_manager.cleanup_all()


async def main():
    """Main entry point"""
    return await test_multi_server_data_manager()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

