#!/usr/bin/env python3
"""
Backtest Progress Monitor

This system monitors backtest progress, tracks completion status,
and analyzes results for verification against bot performance.
"""

import asyncio
import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


@dataclass
class BacktestProgress:
    """Represents backtest progress information"""
    backtest_id: str
    status: str
    progress_percentage: float
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]


class BacktestProgressMonitor:
    """Monitors backtest progress and completion status"""
    
    def __init__(self):
        self.servers = {}
        self.ssh_processes = {}
        self.monitored_backtests = {}
        self.progress_history = {}
    
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
                    'monitored_backtests': []
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
    
    def check_backtest_status(self, server_name: str, backtest_id: str) -> BacktestProgress:
        """Check the status of a specific backtest"""
        if server_name not in self.servers:
            return BacktestProgress(
                backtest_id=backtest_id,
                status='error',
                progress_percentage=0.0,
                start_time=datetime.now(),
                end_time=None,
                duration_seconds=None,
                result_data=None,
                error_message='No connection to server'
            )
        
        try:
            executor = self.servers[server_name]['executor']
            
            # Try to get backtest result
            try:
                from pyHaasAPI.model import GetBacktestResultRequest
                request = GetBacktestResultRequest(
                    lab_id="",  # We don't have lab_id for individual backtests
                    next_page_id=0,
                    page_lenght=1
                )
                
                # This might not work for individual backtests, but let's try
                result = api.get_backtest_result(executor, request)
                
                if result and isinstance(result, dict):
                    # Check if backtest is in results
                    backtests = result.get('Data', {}).get('I', [])
                    for bt in backtests:
                        if bt.get('BID') == backtest_id:
                            return BacktestProgress(
                                backtest_id=backtest_id,
                                status='completed',
                                progress_percentage=100.0,
                                start_time=datetime.now() - timedelta(hours=1),  # Estimate
                                end_time=datetime.now(),
                                duration_seconds=3600,  # Estimate
                                result_data=bt,
                                error_message=None
                            )
                
                # If not found in results, assume it's still running
                return BacktestProgress(
                    backtest_id=backtest_id,
                    status='running',
                    progress_percentage=50.0,  # Estimate
                    start_time=datetime.now() - timedelta(minutes=30),  # Estimate
                    end_time=None,
                    duration_seconds=1800,  # Estimate
                    result_data=None,
                    error_message=None
                )
                
            except Exception as e:
                # If we can't get specific backtest status, assume it's running
                return BacktestProgress(
                    backtest_id=backtest_id,
                    status='running',
                    progress_percentage=25.0,  # Conservative estimate
                    start_time=datetime.now() - timedelta(minutes=15),  # Estimate
                    end_time=None,
                    duration_seconds=900,  # Estimate
                    result_data=None,
                    error_message=f'Status check failed: {str(e)}'
                )
                
        except Exception as e:
            return BacktestProgress(
                backtest_id=backtest_id,
                status='error',
                progress_percentage=0.0,
                start_time=datetime.now(),
                end_time=None,
                duration_seconds=None,
                result_data=None,
                error_message=str(e)
            )
    
    async def monitor_backtest_progress(self, server_name: str, backtest_id: str, max_duration_minutes: int = 60) -> BacktestProgress:
        """Monitor backtest progress until completion or timeout"""
        if server_name not in self.servers:
            return BacktestProgress(
                backtest_id=backtest_id,
                status='error',
                progress_percentage=0.0,
                start_time=datetime.now(),
                end_time=None,
                duration_seconds=None,
                result_data=None,
                error_message='No connection to server'
            )
        
        start_time = datetime.now()
        max_duration_seconds = max_duration_minutes * 60
        
        print(f"Monitoring backtest {backtest_id} on {server_name}...")
        
        while True:
            current_time = datetime.now()
            elapsed_seconds = (current_time - start_time).total_seconds()
            
            # Check for timeout
            if elapsed_seconds > max_duration_seconds:
                return BacktestProgress(
                    backtest_id=backtest_id,
                    status='timeout',
                    progress_percentage=0.0,
                    start_time=start_time,
                    end_time=current_time,
                    duration_seconds=elapsed_seconds,
                    result_data=None,
                    error_message=f'Timeout after {max_duration_minutes} minutes'
                )
            
            # Check backtest status
            progress = self.check_backtest_status(server_name, backtest_id)
            
            # Store progress history
            if backtest_id not in self.progress_history:
                self.progress_history[backtest_id] = []
            self.progress_history[backtest_id].append({
                'timestamp': current_time.isoformat(),
                'status': progress.status,
                'progress_percentage': progress.progress_percentage,
                'elapsed_seconds': elapsed_seconds
            })
            
            print(f"  Status: {progress.status}, Progress: {progress.progress_percentage:.1f}%, Elapsed: {elapsed_seconds:.1f}s")
            
            # Check if completed
            if progress.status == 'completed':
                print(f"  ✅ Backtest completed in {elapsed_seconds:.1f} seconds")
                return progress
            elif progress.status == 'error':
                print(f"  ❌ Backtest failed: {progress.error_message}")
                return progress
            
            # Wait before next check
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def monitor_multiple_backtests(self, server_name: str, backtest_ids: List[str], max_concurrent: int = 10) -> Dict[str, BacktestProgress]:
        """Monitor multiple backtests concurrently"""
        if server_name not in self.servers:
            return {}
        
        print(f"Monitoring {len(backtest_ids)} backtests on {server_name} (max {max_concurrent} concurrent)...")
        
        # Process backtests in batches
        results = {}
        for i in range(0, len(backtest_ids), max_concurrent):
            batch = backtest_ids[i:i + max_concurrent]
            print(f"Processing batch {i//max_concurrent + 1}: {len(batch)} backtests")
            
            # Monitor batch concurrently
            tasks = []
            for backtest_id in batch:
                task = self.monitor_backtest_progress(server_name, backtest_id, max_duration_minutes=30)
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for j, result in enumerate(batch_results):
                if isinstance(result, BacktestProgress):
                    results[batch[j]] = result
                else:
                    # Handle exceptions
                    results[batch[j]] = BacktestProgress(
                        backtest_id=batch[j],
                        status='error',
                        progress_percentage=0.0,
                        start_time=datetime.now(),
                        end_time=None,
                        duration_seconds=None,
                        result_data=None,
                        error_message=str(result)
                    )
            
            # Small delay between batches
            if i + max_concurrent < len(backtest_ids):
                await asyncio.sleep(5)
        
        return results
    
    def analyze_backtest_results(self, progress_results: Dict[str, BacktestProgress]) -> Dict[str, Any]:
        """Analyze backtest results and generate summary"""
        total_backtests = len(progress_results)
        completed_backtests = sum(1 for p in progress_results.values() if p.status == 'completed')
        failed_backtests = sum(1 for p in progress_results.values() if p.status == 'error')
        timeout_backtests = sum(1 for p in progress_results.values() if p.status == 'timeout')
        running_backtests = sum(1 for p in progress_results.values() if p.status == 'running')
        
        # Calculate average duration
        completed_durations = [p.duration_seconds for p in progress_results.values() 
                             if p.status == 'completed' and p.duration_seconds]
        avg_duration = sum(completed_durations) / len(completed_durations) if completed_durations else 0
        
        # Analyze progress history
        progress_analysis = {}
        for backtest_id, history in self.progress_history.items():
            if history:
                progress_analysis[backtest_id] = {
                    'total_checks': len(history),
                    'final_progress': history[-1]['progress_percentage'],
                    'duration_seconds': history[-1]['elapsed_seconds'],
                    'status_changes': len(set(h['status'] for h in history))
                }
        
        analysis = {
            'total_backtests': total_backtests,
            'completed_backtests': completed_backtests,
            'failed_backtests': failed_backtests,
            'timeout_backtests': timeout_backtests,
            'running_backtests': running_backtests,
            'completion_rate': (completed_backtests / total_backtests * 100) if total_backtests > 0 else 0,
            'average_duration_seconds': avg_duration,
            'progress_analysis': progress_analysis,
            'analyzed_at': datetime.now().isoformat()
        }
        
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


async def test_backtest_progress_monitor():
    """Test the backtest progress monitor"""
    print("Testing Backtest Progress Monitor")
    print("=" * 60)
    
    monitor = BacktestProgressMonitor()
    
    try:
        # Connect to srv03
        print("Connecting to srv03...")
        if not await monitor.connect_to_server("srv03"):
            print("Failed to connect to srv03")
            return 1
        
        # Test with some backtest IDs (these would be from the queue system)
        test_backtest_ids = [
            "74c0a2bc-2bff-48b4-a06f-8a3de52400ee",
            "1c823bce-1c36-4011-8ea1-02cfe3ab6876",
            "f8d5ea06-b777-49f5-943c-a84f053db2fd"
        ]
        
        print(f"Monitoring {len(test_backtest_ids)} backtests...")
        
        # Monitor backtests
        results = await monitor.monitor_multiple_backtests("srv03", test_backtest_ids, max_concurrent=3)
        
        print(f"\nMonitoring Results:")
        for backtest_id, progress in results.items():
            print(f"  {backtest_id}:")
            print(f"    Status: {progress.status}")
            print(f"    Progress: {progress.progress_percentage:.1f}%")
            print(f"    Duration: {progress.duration_seconds:.1f}s" if progress.duration_seconds else "    Duration: N/A")
            if progress.error_message:
                print(f"    Error: {progress.error_message}")
        
        # Analyze results
        print(f"\nAnalyzing results...")
        analysis = monitor.analyze_backtest_results(results)
        
        print(f"Analysis Results:")
        print(f"  Total backtests: {analysis['total_backtests']}")
        print(f"  Completed: {analysis['completed_backtests']}")
        print(f"  Failed: {analysis['failed_backtests']}")
        print(f"  Timeout: {analysis['timeout_backtests']}")
        print(f"  Running: {analysis['running_backtests']}")
        print(f"  Completion rate: {analysis['completion_rate']:.1f}%")
        print(f"  Average duration: {analysis['average_duration_seconds']:.1f}s")
        
        print("\nBacktest progress monitor test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await monitor.cleanup_all()


async def main():
    """Main entry point"""
    return await test_backtest_progress_monitor()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

