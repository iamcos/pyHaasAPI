#!/usr/bin/env python3
"""
Comprehensive Backtest Verification CLI

This CLI provides a complete interface for managing backtest verification
across all servers with queue management, progress monitoring, and result analysis.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from integrated_backtest_verification_system import IntegratedBacktestVerificationSystem
from background_backtest_monitoring_system import BackgroundBacktestMonitoringSystem
from backtest_result_analysis_system import BacktestResultAnalysisSystem


class ComprehensiveBacktestVerificationCLI:
    """Comprehensive CLI for backtest verification system"""
    
    def __init__(self):
        self.integrated_system = None
        self.background_system = None
        self.analysis_system = None
    
    async def setup_systems(self, max_concurrent_per_server: int = 10):
        """Setup all verification systems"""
        self.integrated_system = IntegratedBacktestVerificationSystem(max_concurrent_per_server)
        self.background_system = BackgroundBacktestMonitoringSystem(max_concurrent_per_server)
        self.analysis_system = BacktestResultAnalysisSystem()
    
    async def connect_to_servers(self, server_names: List[str]) -> bool:
        """Connect to all specified servers"""
        print(f"Connecting to {len(server_names)} servers...")
        
        success_count = 0
        for server_name in server_names:
            print(f"Connecting to {server_name}...")
            
            # Connect integrated system
            if await self.integrated_system.connect_to_server(server_name):
                success_count += 1
                print(f"  ✅ Integrated system connected to {server_name}")
            else:
                print(f"  ❌ Failed to connect integrated system to {server_name}")
            
            # Connect background system
            if await self.background_system.connect_to_server(server_name):
                print(f"  ✅ Background system connected to {server_name}")
            else:
                print(f"  ❌ Failed to connect background system to {server_name}")
            
            # Connect analysis system
            if await self.analysis_system.connect_to_server(server_name):
                print(f"  ✅ Analysis system connected to {server_name}")
            else:
                print(f"  ❌ Failed to connect analysis system to {server_name}")
        
        return success_count > 0
    
    async def queue_all_bots(self, server_names: List[str]) -> dict:
        """Queue verification backtests for all running bots"""
        print("Queueing verification backtests for all running bots...")
        
        # Use integrated system to queue all bots
        queue_results = await self.integrated_system.queue_all_running_bots(server_names)
        
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
        
        return queue_results
    
    async def start_background_monitoring(self, check_interval_minutes: int = 5) -> None:
        """Start background monitoring system"""
        print(f"Starting background monitoring (check interval: {check_interval_minutes} minutes)...")
        
        # Load existing jobs
        self.background_system.load_jobs_from_file()
        
        # Start monitoring loop
        await self.background_system.background_monitoring_loop()
    
    async def process_completed_backtests(self, server_names: List[str]) -> dict:
        """Process completed backtests and generate verification reports"""
        print("Processing completed backtests...")
        
        # Load completed jobs
        completed_job_ids = []
        if Path("backtest_jobs.json").exists():
            with open("backtest_jobs.json", 'r') as f:
                jobs_data = json.load(f)
            completed_job_ids = jobs_data.get('completed_jobs', [])
        
        if not completed_job_ids:
            print("No completed backtests found")
            return {}
        
        print(f"Found {len(completed_job_ids)} completed backtests")
        
        # Process backtests for each server
        all_verification_reports = {}
        for server_name in server_names:
            if server_name in self.analysis_system.servers:
                print(f"Processing completed backtests on {server_name}...")
                server_reports = await self.analysis_system.process_completed_backtests(server_name, completed_job_ids)
                all_verification_reports.update(server_reports)
        
        if all_verification_reports:
            # Save verification reports
            self.analysis_system.save_verification_reports(all_verification_reports)
            
            # Show summary
            print(f"\nVerification Summary:")
            pass_count = sum(1 for r in all_verification_reports.values() if r.verification_status == "PASS")
            warning_count = sum(1 for r in all_verification_reports.values() if r.verification_status == "WARNING")
            fail_count = sum(1 for r in all_verification_reports.values() if r.verification_status == "FAIL")
            avg_score = sum(r.verification_score for r in all_verification_reports.values()) / len(all_verification_reports)
            
            print(f"  Total reports: {len(all_verification_reports)}")
            print(f"  Pass: {pass_count}")
            print(f"  Warning: {warning_count}")
            print(f"  Fail: {fail_count}")
            print(f"  Average score: {avg_score:.2f}")
            
            # Show individual reports
            print(f"\nIndividual Reports:")
            for job_id, report in all_verification_reports.items():
                print(f"  {report.bot_name}:")
                print(f"    Status: {report.verification_status}")
                print(f"    Score: {report.verification_score:.2f}")
                print(f"    Bot PnL: {report.bot_total_pnl:.2f}")
                print(f"    Backtest PnL: {report.backtest_net_profit:.2f}")
                print(f"    Difference: {report.pnl_difference_percentage:.1f}%")
                if report.issues:
                    print(f"    Issues: {', '.join(report.issues)}")
        
        return all_verification_reports
    
    def show_status(self) -> None:
        """Show current system status"""
        print("Current System Status:")
        print("=" * 50)
        
        # Check if jobs file exists
        if Path("backtest_jobs.json").exists():
            with open("backtest_jobs.json", 'r') as f:
                jobs_data = json.load(f)
            
            total_jobs = len(jobs_data.get('jobs', []))
            completed_jobs = len(jobs_data.get('completed_jobs', []))
            failed_jobs = len(jobs_data.get('failed_jobs', []))
            
            print(f"Total jobs: {total_jobs}")
            print(f"Completed jobs: {completed_jobs}")
            print(f"Failed jobs: {failed_jobs}")
            
            # Show server status
            for server_name, job_ids in jobs_data.get('server_queues', {}).items():
                server_jobs = [job for job in jobs_data.get('jobs', []) if job['job_id'] in job_ids]
                running_jobs = [job for job in server_jobs if job['status'] == 'running']
                pending_jobs = [job for job in server_jobs if job['status'] == 'pending']
                
                print(f"\n{server_name}:")
                print(f"  Total jobs: {len(server_jobs)}")
                print(f"  Running jobs: {len(running_jobs)}")
                print(f"  Pending jobs: {len(pending_jobs)}")
        else:
            print("No jobs file found")
        
        # Check if verification reports exist
        if Path("verification_reports.json").exists():
            with open("verification_reports.json", 'r') as f:
                reports_data = json.load(f)
            
            summary = reports_data.get('summary', {})
            print(f"\nVerification Reports:")
            print(f"  Total reports: {summary.get('total_reports', 0)}")
            print(f"  Pass: {summary.get('pass_count', 0)}")
            print(f"  Warning: {summary.get('warning_count', 0)}")
            print(f"  Fail: {summary.get('fail_count', 0)}")
            print(f"  Average score: {summary.get('average_score', 0):.2f}")
        else:
            print("\nNo verification reports found")
    
    async def cleanup_all(self):
        """Clean up all systems"""
        if self.integrated_system:
            await self.integrated_system.cleanup_all()
        if self.background_system:
            await self.background_system.cleanup_all()
        if self.analysis_system:
            await self.analysis_system.cleanup_all()


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive Backtest Verification CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Queue command
    queue_parser = subparsers.add_parser('queue', help='Queue verification backtests for all running bots')
    queue_parser.add_argument('--servers', nargs='+', default=['srv03'], help='Server names to connect to')
    queue_parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent backtests per server')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Start background monitoring system')
    monitor_parser.add_argument('--servers', nargs='+', default=['srv03'], help='Server names to connect to')
    monitor_parser.add_argument('--check-interval', type=int, default=5, help='Check interval in minutes')
    monitor_parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent backtests per server')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process completed backtests and generate reports')
    process_parser.add_argument('--servers', nargs='+', default=['srv03'], help='Server names to connect to')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current system status')
    
    # Full workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Run complete verification workflow')
    workflow_parser.add_argument('--servers', nargs='+', default=['srv03'], help='Server names to connect to')
    workflow_parser.add_argument('--max-concurrent', type=int, default=10, help='Max concurrent backtests per server')
    workflow_parser.add_argument('--check-interval', type=int, default=5, help='Check interval in minutes')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = ComprehensiveBacktestVerificationCLI()
    
    try:
        if args.command == 'queue':
            await cli.setup_systems(args.max_concurrent)
            if await cli.connect_to_servers(args.servers):
                await cli.queue_all_bots(args.servers)
            else:
                print("Failed to connect to any servers")
                return 1
        
        elif args.command == 'monitor':
            await cli.setup_systems(args.max_concurrent)
            if await cli.connect_to_servers(args.servers):
                await cli.start_background_monitoring(args.check_interval)
            else:
                print("Failed to connect to any servers")
                return 1
        
        elif args.command == 'process':
            await cli.setup_systems()
            if await cli.connect_to_servers(args.servers):
                await cli.process_completed_backtests(args.servers)
            else:
                print("Failed to connect to any servers")
                return 1
        
        elif args.command == 'status':
            cli.show_status()
        
        elif args.command == 'workflow':
            await cli.setup_systems(args.max_concurrent)
            if await cli.connect_to_servers(args.servers):
                print("Step 1: Queueing all running bots...")
                await cli.queue_all_bots(args.servers)
                
                print("\nStep 2: Starting background monitoring...")
                # Note: This would run indefinitely in a real scenario
                # For testing, we'll just show the status
                cli.show_status()
                
                print("\nStep 3: Processing completed backtests...")
                await cli.process_completed_backtests(args.servers)
            else:
                print("Failed to connect to any servers")
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        await cli.cleanup_all()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

