#!/usr/bin/env python3
"""
Comprehensive Backtest Verification System

This system manages backtest verification for all running bots across all servers
with intelligent queue management, progress tracking, and result analysis.
"""

import asyncio
import subprocess
import sys
import json
import uuid
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


class BacktestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BacktestJob:
    """Represents a backtest job in the queue"""
    job_id: str
    server_name: str
    bot_id: str
    bot_name: str
    backtest_id: str
    status: BacktestStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


class BacktestQueueManager:
    """Manages backtest queue with intelligent scheduling"""
    
    def __init__(self, max_concurrent_per_server: int = 10):
        self.max_concurrent_per_server = max_concurrent_per_server
        self.jobs: Dict[str, BacktestJob] = {}
        self.server_queues: Dict[str, List[str]] = {}  # server -> list of job_ids
        self.running_jobs: Dict[str, List[str]] = {}   # server -> list of running job_ids
        self.completed_jobs: List[str] = []
        self.failed_jobs: List[str] = []
    
    def add_job(self, server_name: str, bot_id: str, bot_name: str, backtest_id: str) -> str:
        """Add a new backtest job to the queue"""
        job_id = str(uuid.uuid4())
        
        job = BacktestJob(
            job_id=job_id,
            server_name=server_name,
            bot_id=bot_id,
            bot_name=bot_name,
            backtest_id=backtest_id,
            status=BacktestStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.jobs[job_id] = job
        
        # Add to server queue
        if server_name not in self.server_queues:
            self.server_queues[server_name] = []
        self.server_queues[server_name].append(job_id)
        
        return job_id
    
    def get_next_job(self, server_name: str) -> Optional[BacktestJob]:
        """Get the next pending job for a server"""
        if server_name not in self.server_queues:
            return None
        
        # Check if server has capacity
        running_count = len(self.running_jobs.get(server_name, []))
        if running_count >= self.max_concurrent_per_server:
            return None
        
        # Get next pending job
        for job_id in self.server_queues[server_name]:
            job = self.jobs.get(job_id)
            if job and job.status == BacktestStatus.PENDING:
                return job
        
        return None
    
    def start_job(self, job_id: str):
        """Mark a job as running"""
        if job_id in self.jobs:
            self.jobs[job_id].status = BacktestStatus.RUNNING
            self.jobs[job_id].started_at = datetime.now()
            
            server_name = self.jobs[job_id].server_name
            if server_name not in self.running_jobs:
                self.running_jobs[server_name] = []
            self.running_jobs[server_name].append(job_id)
    
    def complete_job(self, job_id: str, result_data: Optional[Dict[str, Any]] = None):
        """Mark a job as completed"""
        if job_id in self.jobs:
            self.jobs[job_id].status = BacktestStatus.COMPLETED
            self.jobs[job_id].completed_at = datetime.now()
            self.jobs[job_id].result_data = result_data
            
            server_name = self.jobs[job_id].server_name
            if server_name in self.running_jobs and job_id in self.running_jobs[server_name]:
                self.running_jobs[server_name].remove(job_id)
            
            self.completed_jobs.append(job_id)
    
    def fail_job(self, job_id: str, error_message: str):
        """Mark a job as failed"""
        if job_id in self.jobs:
            self.jobs[job_id].status = BacktestStatus.FAILED
            self.jobs[job_id].completed_at = datetime.now()
            self.jobs[job_id].error_message = error_message
            
            server_name = self.jobs[job_id].server_name
            if server_name in self.running_jobs and job_id in self.running_jobs[server_name]:
                self.running_jobs[server_name].remove(job_id)
            
            self.failed_jobs.append(job_id)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        total_jobs = len(self.jobs)
        pending_jobs = sum(1 for job in self.jobs.values() if job.status == BacktestStatus.PENDING)
        running_jobs = sum(1 for job in self.jobs.values() if job.status == BacktestStatus.RUNNING)
        completed_jobs = len(self.completed_jobs)
        failed_jobs = len(self.failed_jobs)
        
        server_status = {}
        for server_name in self.server_queues:
            server_jobs = [job_id for job_id in self.server_queues[server_name]]
            server_running = len(self.running_jobs.get(server_name, []))
            server_pending = sum(1 for job_id in server_jobs 
                               if self.jobs[job_id].status == BacktestStatus.PENDING)
            
            server_status[server_name] = {
                'total_jobs': len(server_jobs),
                'running_jobs': server_running,
                'pending_jobs': server_pending,
                'capacity_used': server_running,
                'capacity_available': self.max_concurrent_per_server - server_running
            }
        
        return {
            'total_jobs': total_jobs,
            'pending_jobs': pending_jobs,
            'running_jobs': running_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'server_status': server_status,
            'timestamp': datetime.now().isoformat()
        }


class ComprehensiveBacktestVerificationSystem:
    """Comprehensive backtest verification system for all running bots"""
    
    def __init__(self, max_concurrent_per_server: int = 10):
        self.servers = {}
        self.ssh_processes = {}
        self.queue_manager = BacktestQueueManager(max_concurrent_per_server)
        self.verification_results = {}
        self.progress_tracker = {}
    
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
                    'running_bots': [],
                    'verification_jobs': []
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
    
    async def queue_all_running_bots(self, server_names: List[str]) -> Dict[str, Any]:
        """Queue verification backtests for all running bots across all servers"""
        queue_results = {
            'total_servers': len(server_names),
            'total_bots_queued': 0,
            'server_results': {},
            'queue_status': {},
            'queued_at': datetime.now().isoformat()
        }
        
        for server_name in server_names:
            if server_name not in self.servers:
                print(f"No connection to {server_name}")
                continue
            
            print(f"\nProcessing {server_name}...")
            
            # Get running bots
            running_bots = self.get_running_bots(server_name)
            print(f"Found {len(running_bots)} running bots on {server_name}")
            
            server_result = {
                'server': server_name,
                'running_bots': len(running_bots),
                'queued_bots': 0,
                'failed_queues': 0,
                'bot_details': []
            }
            
            # Queue backtests for each running bot
            for bot in running_bots:
                try:
                    # Create verification backtest
                    backtest_result = self.create_verification_backtest(server_name, bot)
                    
                    if backtest_result.get('success'):
                        # Add to queue
                        job_id = self.queue_manager.add_job(
                            server_name=server_name,
                            bot_id=bot.get('bot_id', ''),
                            bot_name=bot.get('bot_name', 'Unknown'),
                            backtest_id=backtest_result.get('backtest_id', '')
                        )
                        
                        server_result['queued_bots'] += 1
                        server_result['bot_details'].append({
                            'bot_id': bot.get('bot_id', ''),
                            'bot_name': bot.get('bot_name', 'Unknown'),
                            'backtest_id': backtest_result.get('backtest_id', ''),
                            'job_id': job_id,
                            'status': 'queued'
                        })
                        
                        print(f"  ✅ Queued: {bot.get('bot_name', 'Unknown')}")
                    else:
                        server_result['failed_queues'] += 1
                        server_result['bot_details'].append({
                            'bot_id': bot.get('bot_id', ''),
                            'bot_name': bot.get('bot_name', 'Unknown'),
                            'error': backtest_result.get('error', 'Unknown error'),
                            'status': 'failed'
                        })
                        
                        print(f"  ❌ Failed: {bot.get('bot_name', 'Unknown')} - {backtest_result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    print(f"  ❌ Error processing bot {bot.get('bot_id', 'unknown')}: {e}")
                    server_result['failed_queues'] += 1
                    continue
            
            queue_results['server_results'][server_name] = server_result
            queue_results['total_bots_queued'] += server_result['queued_bots']
        
        # Get queue status
        queue_results['queue_status'] = self.queue_manager.get_queue_status()
        
        return queue_results
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return self.queue_manager.get_queue_status()
    
    def get_job_details(self, job_id: str) -> Optional[BacktestJob]:
        """Get details of a specific job"""
        return self.queue_manager.jobs.get(job_id)
    
    def get_server_jobs(self, server_name: str) -> List[BacktestJob]:
        """Get all jobs for a specific server"""
        if server_name not in self.queue_manager.server_queues:
            return []
        
        jobs = []
        for job_id in self.queue_manager.server_queues[server_name]:
            job = self.queue_manager.jobs.get(job_id)
            if job:
                jobs.append(job)
        
        return jobs
    
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


async def test_comprehensive_backtest_verification_system():
    """Test the comprehensive backtest verification system"""
    print("Testing Comprehensive Backtest Verification System")
    print("=" * 60)
    
    system = ComprehensiveBacktestVerificationSystem(max_concurrent_per_server=10)
    
    try:
        # Connect to multiple servers
        servers = ["srv03"]  # Start with srv03 for testing
        
        for server_name in servers:
            print(f"Connecting to {server_name}...")
            if not await system.connect_to_server(server_name):
                print(f"Failed to connect to {server_name}")
                return 1
        
        # Queue all running bots
        print("\nQueueing verification backtests for all running bots...")
        queue_results = await system.queue_all_running_bots(servers)
        
        print(f"\nQueue Results:")
        print(f"  Total servers: {queue_results['total_servers']}")
        print(f"  Total bots queued: {queue_results['total_bots_queued']}")
        
        # Show server results
        for server_name, server_result in queue_results['server_results'].items():
            print(f"\n{server_name}:")
            print(f"  Running bots: {server_result['running_bots']}")
            print(f"  Queued bots: {server_result['queued_bots']}")
            print(f"  Failed queues: {server_result['failed_queues']}")
        
        # Show queue status
        queue_status = queue_results['queue_status']
        print(f"\nQueue Status:")
        print(f"  Total jobs: {queue_status['total_jobs']}")
        print(f"  Pending jobs: {queue_status['pending_jobs']}")
        print(f"  Running jobs: {queue_status['running_jobs']}")
        print(f"  Completed jobs: {queue_status['completed_jobs']}")
        print(f"  Failed jobs: {queue_status['failed_jobs']}")
        
        # Show server status
        for server_name, status in queue_status['server_status'].items():
            print(f"\n{server_name} Status:")
            print(f"  Total jobs: {status['total_jobs']}")
            print(f"  Running jobs: {status['running_jobs']}")
            print(f"  Pending jobs: {status['pending_jobs']}")
            print(f"  Capacity used: {status['capacity_used']}/{system.queue_manager.max_concurrent_per_server}")
            print(f"  Capacity available: {status['capacity_available']}")
        
        print("\nComprehensive backtest verification system test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await system.cleanup_all()


async def main():
    """Main entry point"""
    return await test_comprehensive_backtest_verification_system()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

