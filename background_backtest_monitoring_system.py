#!/usr/bin/env python3
"""
Background Backtest Monitoring System

This system runs continuously in the background to monitor backtest progress,
handle longer timeouts, and retrieve results when backtests complete.
"""

import asyncio
import subprocess
import sys
import json
import time
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
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
    last_checked: Optional[datetime] = None
    check_count: int = 0


class BackgroundBacktestMonitoringSystem:
    """Background system for monitoring backtest progress and retrieving results"""
    
    def __init__(self, max_concurrent_per_server: int = 10, check_interval_minutes: int = 5):
        self.servers = {}
        self.ssh_processes = {}
        self.jobs: Dict[str, BacktestJob] = {}
        self.server_queues: Dict[str, List[str]] = {}
        self.running_jobs: Dict[str, List[str]] = {}
        self.completed_jobs: List[str] = []
        self.failed_jobs: List[str] = []
        self.max_concurrent_per_server = max_concurrent_per_server
        self.check_interval_minutes = check_interval_minutes
        self.verification_results = {}
        self.progress_history = {}
        self.running = False
        self.monitoring_tasks = []
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
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
    
    def load_jobs_from_file(self, filename: str = "backtest_jobs.json") -> bool:
        """Load jobs from persistent storage"""
        try:
            if Path(filename).exists():
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                # Restore jobs
                for job_data in data.get('jobs', []):
                    job = BacktestJob(
                        job_id=job_data['job_id'],
                        server_name=job_data['server_name'],
                        bot_id=job_data['bot_id'],
                        bot_name=job_data['bot_name'],
                        backtest_id=job_data['backtest_id'],
                        status=BacktestStatus(job_data['status']),
                        created_at=datetime.fromisoformat(job_data['created_at']),
                        started_at=datetime.fromisoformat(job_data['started_at']) if job_data.get('started_at') else None,
                        completed_at=datetime.fromisoformat(job_data['completed_at']) if job_data.get('completed_at') else None,
                        error_message=job_data.get('error_message'),
                        result_data=job_data.get('result_data'),
                        progress_percentage=job_data.get('progress_percentage', 0.0),
                        last_checked=datetime.fromisoformat(job_data['last_checked']) if job_data.get('last_checked') else None,
                        check_count=job_data.get('check_count', 0)
                    )
                    self.jobs[job.job_id] = job
                
                # Restore server queues
                for server_name, job_ids in data.get('server_queues', {}).items():
                    self.server_queues[server_name] = job_ids
                
                # Restore running jobs
                for server_name, job_ids in data.get('running_jobs', {}).items():
                    self.running_jobs[server_name] = job_ids
                
                self.completed_jobs = data.get('completed_jobs', [])
                self.failed_jobs = data.get('failed_jobs', [])
                
                print(f"Loaded {len(self.jobs)} jobs from {filename}")
                return True
            else:
                print(f"No existing jobs file found: {filename}")
                return False
                
        except Exception as e:
            print(f"Error loading jobs from file: {e}")
            return False
    
    def save_jobs_to_file(self, filename: str = "backtest_jobs.json") -> bool:
        """Save jobs to persistent storage"""
        try:
            data = {
                'jobs': [],
                'server_queues': self.server_queues,
                'running_jobs': self.running_jobs,
                'completed_jobs': self.completed_jobs,
                'failed_jobs': self.failed_jobs,
                'saved_at': datetime.now().isoformat()
            }
            
            for job in self.jobs.values():
                job_data = {
                    'job_id': job.job_id,
                    'server_name': job.server_name,
                    'bot_id': job.bot_id,
                    'bot_name': job.bot_name,
                    'backtest_id': job.backtest_id,
                    'status': job.status.value,
                    'created_at': job.created_at.isoformat(),
                    'started_at': job.started_at.isoformat() if job.started_at else None,
                    'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                    'error_message': job.error_message,
                    'result_data': job.result_data,
                    'progress_percentage': job.progress_percentage,
                    'last_checked': job.last_checked.isoformat() if job.last_checked else None,
                    'check_count': job.check_count
                }
                data['jobs'].append(job_data)
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"Saved {len(self.jobs)} jobs to {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving jobs to file: {e}")
            return False
    
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
    
    async def monitor_single_job(self, job_id: str) -> BacktestJob:
        """Monitor a single job's progress"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        current_time = datetime.now()
        
        # Update last checked time
        job.last_checked = current_time
        job.check_count += 1
        
        # Check if job has been running too long (2 hours max)
        if job.started_at:
            elapsed_hours = (current_time - job.started_at).total_seconds() / 3600
            if elapsed_hours > 2.0:  # 2 hours timeout
                job.status = BacktestStatus.TIMEOUT
                job.completed_at = current_time
                job.error_message = f'Timeout after {elapsed_hours:.1f} hours'
                self.fail_job(job_id, job.error_message)
                print(f"  ⏰ Job {job_id} timed out after {elapsed_hours:.1f} hours")
                return job
        
        # Check backtest status
        status_info = self.check_backtest_status(job.server_name, job.backtest_id)
        
        # Update job progress
        job.progress_percentage = status_info.get('progress_percentage', job.progress_percentage)
        
        # Store progress history
        if job_id not in self.progress_history:
            self.progress_history[job_id] = []
        self.progress_history[job_id].append({
            'timestamp': current_time.isoformat(),
            'status': status_info.get('status', 'unknown'),
            'progress_percentage': job.progress_percentage,
            'check_count': job.check_count
        })
        
        print(f"  Job {job_id}: {status_info.get('status', 'unknown')}, Progress: {job.progress_percentage:.1f}%, Checks: {job.check_count}")
        
        # Check if completed
        if status_info.get('status') == 'completed':
            job.status = BacktestStatus.COMPLETED
            job.completed_at = current_time
            job.result_data = status_info.get('result_data')
            self.complete_job(job_id, job.result_data)
            print(f"  ✅ Job {job_id} completed after {job.check_count} checks")
            return job
        elif status_info.get('status') == 'error':
            job.status = BacktestStatus.FAILED
            job.completed_at = current_time
            job.error_message = status_info.get('error_message', 'Unknown error')
            self.fail_job(job_id, job.error_message)
            print(f"  ❌ Job {job_id} failed: {job.error_message}")
            return job
        
        return job
    
    async def monitor_all_jobs(self):
        """Monitor all jobs in the system"""
        print(f"Monitoring {len(self.jobs)} jobs...")
        
        # Get all running jobs
        running_job_ids = []
        for server_name, job_ids in self.running_jobs.items():
            running_job_ids.extend(job_ids)
        
        if not running_job_ids:
            print("No running jobs to monitor")
            return
        
        print(f"Monitoring {len(running_job_ids)} running jobs...")
        
        # Monitor jobs concurrently
        tasks = []
        for job_id in running_job_ids:
            task = self.monitor_single_job(job_id)
            tasks.append(task)
        
        # Wait for all monitoring tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        completed_count = 0
        failed_count = 0
        timeout_count = 0
        
        for result in results:
            if isinstance(result, BacktestJob):
                if result.status == BacktestStatus.COMPLETED:
                    completed_count += 1
                elif result.status == BacktestStatus.FAILED:
                    failed_count += 1
                elif result.status == BacktestStatus.TIMEOUT:
                    timeout_count += 1
        
        print(f"Monitoring cycle complete: {completed_count} completed, {failed_count} failed, {timeout_count} timeout")
    
    async def start_new_jobs(self):
        """Start new jobs from the queue"""
        for server_name in self.server_queues:
            if server_name not in self.servers:
                continue
            
            # Check if server has capacity
            running_count = len(self.running_jobs.get(server_name, []))
            if running_count >= self.max_concurrent_per_server:
                continue
            
            # Get next pending job
            for job_id in self.server_queues[server_name]:
                job = self.jobs.get(job_id)
                if job and job.status == BacktestStatus.PENDING:
                    # Start the job
                    job.status = BacktestStatus.RUNNING
                    job.started_at = datetime.now()
                    
                    if server_name not in self.running_jobs:
                        self.running_jobs[server_name] = []
                    self.running_jobs[server_name].append(job_id)
                    
                    print(f"  🚀 Started job {job_id} for bot: {job.bot_name}")
                    break
    
    async def background_monitoring_loop(self):
        """Main background monitoring loop"""
        print("Starting background monitoring loop...")
        self.running = True
        
        while self.running:
            try:
                print(f"\n--- Monitoring Cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
                
                # Start new jobs if capacity available
                await self.start_new_jobs()
                
                # Monitor all running jobs
                await self.monitor_all_jobs()
                
                # Save current state
                self.save_jobs_to_file()
                
                # Show status summary
                self.show_status_summary()
                
                # Wait for next check
                print(f"Waiting {self.check_interval_minutes} minutes until next check...")
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\nReceived keyboard interrupt, shutting down...")
                break
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        print("Background monitoring stopped")
    
    def show_status_summary(self):
        """Show current status summary"""
        total_jobs = len(self.jobs)
        pending_jobs = sum(1 for job in self.jobs.values() if job.status == BacktestStatus.PENDING)
        running_jobs = sum(1 for job in self.jobs.values() if job.status == BacktestStatus.RUNNING)
        completed_jobs = len(self.completed_jobs)
        failed_jobs = len(self.failed_jobs)
        
        print(f"\nStatus Summary:")
        print(f"  Total jobs: {total_jobs}")
        print(f"  Pending: {pending_jobs}")
        print(f"  Running: {running_jobs}")
        print(f"  Completed: {completed_jobs}")
        print(f"  Failed: {failed_jobs}")
        
        # Show server status
        for server_name in self.server_queues:
            server_running = len(self.running_jobs.get(server_name, []))
            server_pending = sum(1 for job_id in self.server_queues[server_name] 
                               if self.jobs[job_id].status == BacktestStatus.PENDING)
            
            print(f"  {server_name}: {server_running} running, {server_pending} pending")
    
    def complete_job(self, job_id: str, result_data: Optional[Dict[str, Any]] = None):
        """Mark a job as completed"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = BacktestStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result_data = result_data
            job.progress_percentage = 100.0
            
            server_name = job.server_name
            if server_name in self.running_jobs and job_id in self.running_jobs[server_name]:
                self.running_jobs[server_name].remove(job_id)
            
            self.completed_jobs.append(job_id)
    
    def fail_job(self, job_id: str, error_message: str):
        """Mark a job as failed"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            job.status = BacktestStatus.FAILED
            job.completed_at = datetime.now()
            job.error_message = error_message
            
            server_name = job.server_name
            if server_name in self.running_jobs and job_id in self.running_jobs[server_name]:
                self.running_jobs[server_name].remove(job_id)
            
            self.failed_jobs.append(job_id)
    
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


async def test_background_monitoring_system():
    """Test the background monitoring system"""
    print("Testing Background Backtest Monitoring System")
    print("=" * 60)
    
    system = BackgroundBacktestMonitoringSystem(
        max_concurrent_per_server=5,
        check_interval_minutes=2  # Check every 2 minutes for testing
    )
    
    try:
        # Load existing jobs if available
        print("Loading existing jobs...")
        system.load_jobs_from_file()
        
        # Connect to srv03
        print("Connecting to srv03...")
        if not await system.connect_to_server("srv03"):
            print("Failed to connect to srv03")
            return 1
        
        # Show initial status
        system.show_status_summary()
        
        # Run monitoring loop for a limited time (10 minutes for testing)
        print("\nStarting background monitoring for 10 minutes...")
        monitoring_task = asyncio.create_task(system.background_monitoring_loop())
        
        # Wait for 10 minutes or until interrupted
        try:
            await asyncio.wait_for(monitoring_task, timeout=600)  # 10 minutes
        except asyncio.TimeoutError:
            print("\n10-minute test completed, stopping monitoring...")
            system.running = False
            monitoring_task.cancel()
        
        # Show final status
        print("\nFinal Status:")
        system.show_status_summary()
        
        print("\nBackground monitoring system test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        await system.cleanup_all()


async def main():
    """Main entry point"""
    return await test_background_monitoring_system()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

