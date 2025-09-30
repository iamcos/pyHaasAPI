#!/usr/bin/env python3
"""
Backtest Queue Investigation

This script investigates HaasOnline API backtest queue limits and simultaneous
execution constraints to understand how to properly manage backtest queues.
"""

import asyncio
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


class BacktestQueueInvestigator:
    """Investigate backtest queue limits and constraints"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
        self.queue_tests = {}
    
    async def connect_to_server(self, server_name: str) -> bool:
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
                    'active_backtests': [],
                    'queue_status': {}
                }
                print(f"Successfully connected to {server_name}")
                return True
            else:
                print(f"Failed to connect to {server_name}")
                return False
                
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")
            return False
    
    async def _establish_ssh_tunnel(self, server_name: str):
        """Establish SSH tunnel to server"""
        try:
            print(f"Connecting to {server_name}...")
            
            ssh_cmd = [
                "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
                f"prod@{server_name}"
            ]
            
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            await asyncio.sleep(5)
            
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
    
    def get_running_bots(self, server_name: str) -> List[Dict[str, Any]]:
        """Get all running bots from a server"""
        if server_name not in self.servers:
            return []
        
        try:
            executor = self.servers[server_name]['executor']
            bots = api.get_all_bots(executor)
            
            running_bots = []
            for bot in bots:
                if hasattr(bot, 'model_dump'):
                    bot_data = bot.model_dump()
                elif isinstance(bot, dict):
                    bot_data = bot
                else:
                    bot_data = {
                        'bot_id': getattr(bot, 'bot_id', ''),
                        'bot_name': getattr(bot, 'bot_name', 'Unknown'),
                        'account_id': getattr(bot, 'account_id', ''),
                        'market': getattr(bot, 'market', ''),
                        'script_id': getattr(bot, 'script_id', ''),
                        'is_activated': getattr(bot, 'is_activated', False),
                        'is_paused': getattr(bot, 'is_paused', False)
                    }
                
                # Only include running bots
                if bot_data.get('is_activated', False) and not bot_data.get('is_paused', False):
                    running_bots.append(bot_data)
            
            return running_bots
            
        except Exception as e:
            print(f"Error getting running bots from {server_name}: {e}")
            return []
    
    def create_verification_backtest(self, server_name: str, bot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a verification backtest for a bot"""
        try:
            executor = self.servers[server_name]['executor']
            
            # Extract bot information
            bot_id = bot_data.get('bot_id', '')
            bot_name = bot_data.get('bot_name', 'Unknown')
            script_id = bot_data.get('script_id', '')
            market_tag = bot_data.get('market', '')
            
            if not script_id:
                return {
                    'success': False,
                    'error': 'Bot has no ScriptId',
                    'bot_id': bot_id,
                    'bot_name': bot_name
                }
            
            # Get script record
            from pyHaasAPI.model import GetScriptRecordRequest
            script_request = GetScriptRecordRequest(script_id=script_id)
            script_record = api.get_script_record(executor, script_request)
            
            if not script_record:
                return {
                    'success': False,
                    'error': 'Failed to get script record',
                    'bot_id': bot_id,
                    'bot_name': bot_name
                }
            
            # Build backtest settings from bot data
            settings = api.build_backtest_settings(bot_data, script_record)
            
            # Set time range for verification backtest (1 day)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=1)
            start_unix = int(start_time.timestamp())
            end_unix = int(end_time.timestamp())
            
            # Create backtest request
            from pyHaasAPI.model import ExecuteBacktestRequest
            import uuid
            backtest_id = str(uuid.uuid4())
            
            request = ExecuteBacktestRequest(
                backtest_id=backtest_id,
                script_id=script_id,
                settings=settings,
                start_unix=start_unix,
                end_unix=end_unix
            )
            
            # Execute backtest
            result = api.execute_backtest(executor, request)
            
            if result.get('Success', False):
                return {
                    'success': True,
                    'backtest_id': backtest_id,
                    'bot_id': bot_id,
                    'bot_name': bot_name,
                    'script_id': script_id,
                    'market_tag': market_tag,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_days': 1,
                    'settings': settings,
                    'result': result,
                    'created_at': datetime.now().isoformat(),
                    'server': server_name
                }
            else:
                return {
                    'success': False,
                    'error': result.get('Error', 'Unknown error'),
                    'bot_id': bot_id,
                    'bot_name': bot_name,
                    'result': result
                }
                
        except Exception as e:
            print(f"Error creating verification backtest for bot {bot_data.get('bot_id', 'unknown')}: {e}")
            return {
                'success': False,
                'error': str(e),
                'bot_id': bot_data.get('bot_id', ''),
                'bot_name': bot_data.get('bot_name', 'Unknown')
            }
    
    async def test_queue_limits(self, server_name: str, max_concurrent: int = 15) -> Dict[str, Any]:
        """Test backtest queue limits by creating multiple concurrent backtests"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        try:
            # Get running bots
            running_bots = self.get_running_bots(server_name)
            print(f"Found {len(running_bots)} running bots on {server_name}")
            
            if not running_bots:
                return {'error': 'No running bots found'}
            
            # Limit to max_concurrent for testing
            test_bots = running_bots[:max_concurrent]
            
            queue_test = {
                'server': server_name,
                'total_bots': len(test_bots),
                'max_concurrent': max_concurrent,
                'successful_backtests': 0,
                'failed_backtests': 0,
                'backtests': [],
                'start_time': datetime.now().isoformat()
            }
            
            print(f"Testing queue limits with {len(test_bots)} bots...")
            
            # Create backtests concurrently
            for i, bot in enumerate(test_bots):
                print(f"Creating backtest {i+1}/{len(test_bots)} for bot: {bot.get('bot_name', 'Unknown')}")
                
                backtest_result = self.create_verification_backtest(server_name, bot)
                queue_test['backtests'].append(backtest_result)
                
                if backtest_result.get('success'):
                    queue_test['successful_backtests'] += 1
                    print(f"  ✅ Success: {backtest_result.get('backtest_id', 'N/A')}")
                else:
                    queue_test['failed_backtests'] += 1
                    print(f"  ❌ Failed: {backtest_result.get('error', 'Unknown error')}")
                
                # Small delay between backtests to avoid overwhelming the server
                await asyncio.sleep(1)
            
            queue_test['end_time'] = datetime.now().isoformat()
            queue_test['duration_seconds'] = (datetime.now() - datetime.fromisoformat(queue_test['start_time'])).total_seconds()
            
            # Store results
            self.queue_tests[server_name] = queue_test
            
            return queue_test
            
        except Exception as e:
            print(f"Error testing queue limits on {server_name}: {e}")
            return {'error': str(e)}
    
    def analyze_queue_results(self, server_name: str) -> Dict[str, Any]:
        """Analyze queue test results"""
        if server_name not in self.queue_tests:
            return {'error': 'No queue test results available'}
        
        queue_test = self.queue_tests[server_name]
        
        analysis = {
            'server': server_name,
            'total_bots_tested': queue_test['total_bots'],
            'successful_backtests': queue_test['successful_backtests'],
            'failed_backtests': queue_test['failed_backtests'],
            'success_rate': (queue_test['successful_backtests'] / queue_test['total_bots'] * 100) if queue_test['total_bots'] > 0 else 0,
            'duration_seconds': queue_test.get('duration_seconds', 0),
            'backtests_per_second': queue_test['total_bots'] / queue_test.get('duration_seconds', 1),
            'queue_capacity_estimate': queue_test['successful_backtests'],
            'failed_reasons': {}
        }
        
        # Analyze failure reasons
        for backtest in queue_test['backtests']:
            if not backtest.get('success'):
                error = backtest.get('error', 'Unknown error')
                if error in analysis['failed_reasons']:
                    analysis['failed_reasons'][error] += 1
                else:
                    analysis['failed_reasons'][error] = 1
        
        return analysis
    
    async def cleanup_all(self):
        """Clean up all SSH tunnels"""
        for server_name, process in self.ssh_processes.items():
            print(f"Cleaning up {server_name}...")
            try:
                if process and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception as e:
                print(f"Error cleaning up {server_name}: {e}")


async def test_backtest_queue_investigation():
    """Test backtest queue investigation"""
    print("Testing Backtest Queue Investigation")
    print("=" * 60)
    
    investigator = BacktestQueueInvestigator()
    
    try:
        # Connect to srv03 (has running bots)
        print("Connecting to srv03...")
        if not await investigator.connect_to_server("srv03"):
            print("Failed to connect to srv03")
            return 1
        
        # Test queue limits with 15 concurrent backtests
        print("\nTesting queue limits with 15 concurrent backtests...")
        queue_results = await investigator.test_queue_limits("srv03", max_concurrent=15)
        if 'error' in queue_results:
            print(f"Error testing queue limits: {queue_results['error']}")
            return 1
        
        print(f"\nQueue Test Results:")
        print(f"  Total bots tested: {queue_results['total_bots']}")
        print(f"  Successful backtests: {queue_results['successful_backtests']}")
        print(f"  Failed backtests: {queue_results['failed_backtests']}")
        print(f"  Duration: {queue_results.get('duration_seconds', 0):.2f} seconds")
        
        # Analyze results
        print("\nAnalyzing queue results...")
        analysis = investigator.analyze_queue_results("srv03")
        if 'error' in analysis:
            print(f"Error analyzing results: {analysis['error']}")
            return 1
        
        print(f"\nQueue Analysis:")
        print(f"  Success rate: {analysis['success_rate']:.1f}%")
        print(f"  Backtests per second: {analysis['backtests_per_second']:.2f}")
        print(f"  Queue capacity estimate: {analysis['queue_capacity_estimate']}")
        print(f"  Failed reasons: {analysis['failed_reasons']}")
        
        # Show individual backtest results
        print(f"\nIndividual Backtest Results:")
        for i, backtest in enumerate(queue_results['backtests'][:5]):  # Show first 5
            print(f"  {i+1}. {backtest.get('bot_name', 'Unknown')}")
            print(f"     Success: {backtest.get('success', False)}")
            if backtest.get('success'):
                print(f"     Backtest ID: {backtest.get('backtest_id', 'N/A')}")
            else:
                print(f"     Error: {backtest.get('error', 'Unknown error')}")
        
        print("\nBacktest queue investigation completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await investigator.cleanup_all()


async def main():
    """Main entry point"""
    return await test_backtest_queue_investigation()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

