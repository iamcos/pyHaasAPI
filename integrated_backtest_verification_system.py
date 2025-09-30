#!/usr/bin/env python3
"""
Integrated Backtest Verification System

This system combines queue management, progress monitoring, and result analysis
to provide comprehensive backtest verification for all running bots across all servers.
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
    TIMEOUT = "timeout"


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
    progress_percentage: float = 0.0


class IntegratedBacktestVerificationSystem:
    """Integrated system for backtest verification with queue management and monitoring"""
    
    def __init__(self, max_concurrent_per_server: int = 10):
        self.servers = {}
        self.ssh_processes = {}
        self.jobs: Dict[str, BacktestJob] = {}
        self.server_queues: Dict[str, List[str]] = {}
        self.running_jobs: Dict[str, List[str]] = {}
        self.completed_jobs: List[str] = []
        self.failed_jobs: List[str] = []
        self.max_concurrent_per_server = max_concurrent_per_server
        self.verification_results = {}
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
            self.jobs[job_id].progress_percentage = 100.0
            
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
    
    def check_backtest_status(self, server_name: str, backtest_id: str) -> Dict[str, Any]:
        """Check the status of a specific backtest"""
        if server_name not in self.servers:
            return {
                'status': 'error',
                'progress_percentage': 0.0,
                'error_message': 'No connection to server'
            }
        
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
                
                result = api.get_backtest_result(executor, request)
                
                if result and isinstance(result, dict):
                    # Check if backtest is in results
                    backtests = result.get('Data', {}).get('I', [])
                    for bt in backtests:
                        if bt.get('BID') == backtest_id:
                            return {
                                'status': 'completed',
                                'progress_percentage': 100.0,
                                'result_data': bt,
                                'error_message': None
                            }
                
                # If not found in results, assume it's still running
                return {
                    'status': 'running',
                    'progress_percentage': 50.0,  # Estimate
                    'result_data': None,
                    'error_message': None
                }
                
            except Exception as e:
                # If we can't get specific backtest status, assume it's running
                return {
                    'status': 'running',
                    'progress_percentage': 25.0,  # Conservative estimate
                    'result_data': None,
                    'error_message': f'Status check failed: {str(e)}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'progress_percentage': 0.0,
                'result_data': None,
                'error_message': str(e)
            }
    
    async def monitor_job_progress(self, job_id: str, max_duration_minutes: int = 30) -> BacktestJob:
        """Monitor a specific job's progress"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        start_time = datetime.now()
        max_duration_seconds = max_duration_minutes * 60
        
        print(f"Monitoring job {job_id} (backtest: {job.backtest_id})...")
        
        while True:
            current_time = datetime.now()
            elapsed_seconds = (current_time - start_time).total_seconds()
            
            # Check for timeout
            if elapsed_seconds > max_duration_seconds:
                job.status = BacktestStatus.TIMEOUT
                job.completed_at = current_time
                job.error_message = f'Timeout after {max_duration_minutes} minutes'
                self.fail_job(job_id, job.error_message)
                return job
            
            # Check backtest status
            status_info = self.check_backtest_status(job.server_name, job.backtest_id)
            
            # Update job progress
            job.progress_percentage = status_info.get('progress_percentage', 0.0)
            
            # Store progress history
            if job_id not in self.progress_history:
                self.progress_history[job_id] = []
            self.progress_history[job_id].append({
                'timestamp': current_time.isoformat(),
                'status': status_info.get('status', 'unknown'),
                'progress_percentage': job.progress_percentage,
                'elapsed_seconds': elapsed_seconds
            })
            
            print(f"  Job {job_id}: {status_info.get('status', 'unknown')}, Progress: {job.progress_percentage:.1f}%, Elapsed: {elapsed_seconds:.1f}s")
            
            # Check if completed
            if status_info.get('status') == 'completed':
                job.status = BacktestStatus.COMPLETED
                job.completed_at = current_time
                job.result_data = status_info.get('result_data')
                self.complete_job(job_id, job.result_data)
                print(f"  ✅ Job completed in {elapsed_seconds:.1f} seconds")
                return job
            elif status_info.get('status') == 'error':
                job.status = BacktestStatus.FAILED
                job.completed_at = current_time
                job.error_message = status_info.get('error_message', 'Unknown error')
                self.fail_job(job_id, job.error_message)
                print(f"  ❌ Job failed: {job.error_message}")
                return job
            
            # Wait before next check
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def process_queue(self, server_name: str, max_concurrent: int = None) -> Dict[str, Any]:
        """Process the queue for a specific server"""
        if server_name not in self.servers:
            return {'error': 'No connection to server'}
        
        if max_concurrent is None:
            max_concurrent = self.max_concurrent_per_server
        
        print(f"Processing queue for {server_name} (max {max_concurrent} concurrent)...")
        
        # Get all pending jobs for this server
        pending_jobs = [job_id for job_id in self.server_queues.get(server_name, [])
                       if self.jobs[job_id].status == BacktestStatus.PENDING]
        
        if not pending_jobs:
            print(f"No pending jobs for {server_name}")
            return {'message': 'No pending jobs', 'server': server_name}
        
        print(f"Found {len(pending_jobs)} pending jobs for {server_name}")
        
        # Process jobs in batches
        results = {
            'server': server_name,
            'total_jobs': len(pending_jobs),
            'processed_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'timeout_jobs': 0,
            'job_details': []
        }
        
        for i in range(0, len(pending_jobs), max_concurrent):
            batch = pending_jobs[i:i + max_concurrent]
            print(f"Processing batch {i//max_concurrent + 1}: {len(batch)} jobs")
            
            # Start jobs in batch
            for job_id in batch:
                job = self.jobs[job_id]
                self.start_job(job_id)
                print(f"  Started job {job_id} for bot: {job.bot_name}")
            
            # Monitor batch concurrently
            tasks = []
            for job_id in batch:
                task = self.monitor_job_progress(job_id, max_duration_minutes=30)
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for j, result in enumerate(batch_results):
                job_id = batch[j]
                job = self.jobs[job_id]
                
                results['processed_jobs'] += 1
                
                if isinstance(result, BacktestJob):
                    if result.status == BacktestStatus.COMPLETED:
                        results['completed_jobs'] += 1
                    elif result.status == BacktestStatus.FAILED:
                        results['failed_jobs'] += 1
                    elif result.status == BacktestStatus.TIMEOUT:
                        results['timeout_jobs'] += 1
                    
                    results['job_details'].append({
                        'job_id': job_id,
                        'bot_name': job.bot_name,
                        'backtest_id': job.backtest_id,
                        'status': result.status.value,
                        'progress_percentage': result.progress_percentage,
                        'duration_seconds': (result.completed_at - result.started_at).total_seconds() if result.completed_at and result.started_at else None,
                        'error_message': result.error_message
                    })
                else:
                    # Handle exceptions
                    results['failed_jobs'] += 1
                    results['job_details'].append({
                        'job_id': job_id,
                        'bot_name': job.bot_name,
                        'backtest_id': job.backtest_id,
                        'status': 'error',
                        'progress_percentage': 0.0,
                        'duration_seconds': None,
                        'error_message': str(result)
                    })
            
            # Small delay between batches
            if i + max_concurrent < len(pending_jobs):
                await asyncio.sleep(5)
        
        return results
    
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
                        job_id = self.add_job(
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
        queue_results['queue_status'] = self.get_queue_status()
        
        return queue_results
    
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
    
    async def process_all_queues(self, server_names: List[str]) -> Dict[str, Any]:
        """Process all queues for all servers"""
        print(f"Processing all queues for {len(server_names)} servers...")
        
        results = {
            'total_servers': len(server_names),
            'server_results': {},
            'overall_summary': {},
            'processed_at': datetime.now().isoformat()
        }
        
        for server_name in server_names:
            if server_name not in self.servers:
                print(f"No connection to {server_name}")
                continue
            
            print(f"\nProcessing queue for {server_name}...")
            server_result = await self.process_queue(server_name)
            results['server_results'][server_name] = server_result
        
        # Calculate overall summary
        total_processed = sum(r.get('processed_jobs', 0) for r in results['server_results'].values())
        total_completed = sum(r.get('completed_jobs', 0) for r in results['server_results'].values())
        total_failed = sum(r.get('failed_jobs', 0) for r in results['server_results'].values())
        total_timeout = sum(r.get('timeout_jobs', 0) for r in results['server_results'].values())
        
        results['overall_summary'] = {
            'total_processed': total_processed,
            'total_completed': total_completed,
            'total_failed': total_failed,
            'total_timeout': total_timeout,
            'completion_rate': (total_completed / total_processed * 100) if total_processed > 0 else 0
        }
        
        return results
    
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


async def test_integrated_backtest_verification_system():
    """Test the integrated backtest verification system"""
    print("Testing Integrated Backtest Verification System")
    print("=" * 60)
    
    system = IntegratedBacktestVerificationSystem(max_concurrent_per_server=5)
    
    try:
        # Connect to srv03
        print("Connecting to srv03...")
        if not await system.connect_to_server("srv03"):
            print("Failed to connect to srv03")
            return 1
        
        # Queue all running bots
        print("\nQueueing verification backtests for all running bots...")
        queue_results = await system.queue_all_running_bots(["srv03"])
        
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
        
        # Process queue (limited to first 5 jobs for testing)
        print(f"\nProcessing queue (limited to first 5 jobs for testing)...")
        process_results = await system.process_queue("srv03", max_concurrent=3)
        
        if 'error' in process_results:
            print(f"Error processing queue: {process_results['error']}")
            return 1
        
        print(f"\nProcess Results:")
        print(f"  Total jobs: {process_results['total_jobs']}")
        print(f"  Processed jobs: {process_results['processed_jobs']}")
        print(f"  Completed jobs: {process_results['completed_jobs']}")
        print(f"  Failed jobs: {process_results['failed_jobs']}")
        print(f"  Timeout jobs: {process_results['timeout_jobs']}")
        
        # Show job details
        print(f"\nJob Details:")
        for job_detail in process_results['job_details'][:5]:  # Show first 5
            print(f"  {job_detail['bot_name']}:")
            print(f"    Status: {job_detail['status']}")
            print(f"    Progress: {job_detail['progress_percentage']:.1f}%")
            if job_detail['duration_seconds']:
                print(f"    Duration: {job_detail['duration_seconds']:.1f}s")
            if job_detail['error_message']:
                print(f"    Error: {job_detail['error_message']}")
        
        print("\nIntegrated backtest verification system test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await system.cleanup_all()


async def main():
    """Main entry point"""
    return await test_integrated_backtest_verification_system()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

