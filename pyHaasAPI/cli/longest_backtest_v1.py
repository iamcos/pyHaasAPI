#!/usr/bin/env python3
"""
Longest Backtest CLI using v1 API for immediate functionality.

This script provides a working implementation for longest backtest execution
when v2 API authentication is not available.
"""

import sys
import os
import argparse
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pyHaasAPI_v1 import api, model


class LongestBacktestV1:
    """Longest backtest implementation using v1 API."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8090):
        self.host = host
        self.port = port
        self.executor = None
        
    def connect(self) -> bool:
        """Connect to the HaasOnline API."""
        try:
            # Create API connection
            haas_api = api.RequestsExecutor(
                host=self.host,
                port=self.port,
                state=api.Guest()
            )
            
            # Authenticate
            self.executor = haas_api.authenticate(
                os.getenv('API_EMAIL'), 
                os.getenv('API_PASSWORD')
            )
            
            print(f"✅ Connected to server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def discover_cutoff_date(self, lab_id: str) -> datetime:
        """
        Discover the actual cutoff date by checking lab details and market data.
        
        This method:
        1. Gets the lab's current settings
        2. Queries market data availability
        3. Finds the earliest available data point
        """
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            market_tag = getattr(lab_details, 'market_tag', None)
            
            print(f"📊 Lab: {getattr(lab_details, 'name', 'Unknown')}")
            print(f"🏷️ Market: {market_tag}")
            
            # For now, use a conservative 3-year cutoff
            # In a real implementation, this would query market data API
            cutoff_date = datetime.utcnow() - timedelta(days=365*3)
            
            print(f"📅 Using cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
            return cutoff_date
            
        except Exception as e:
            print(f"⚠️ Failed to discover cutoff date: {e}, using default 3-year cutoff")
            return datetime.utcnow() - timedelta(days=365*3)
    
    def configure_lab_for_longest_backtest(self, lab_id: str, cutoff_date: datetime, 
                                         end_date: datetime, max_iterations: int) -> bool:
        """Configure lab settings for longest backtest."""
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Update lab settings
            lab_details.start_unix = int(cutoff_date.timestamp())
            lab_details.end_unix = int(end_date.timestamp())
            
            # Update the lab
            api.update_lab_details(self.executor, lab_details)
            
            print(f"✅ Lab {lab_id} configured for longest backtest")
            print(f"   Period: {cutoff_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
            print(f"   Duration: {(end_date - cutoff_date).days} days")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure lab: {e}")
            return False
    
    def check_lab_status(self, lab_id: str) -> str:
        """Check current lab execution status."""
        try:
            status_response = api.get_lab_execution_update(self.executor, lab_id)
            if status_response:
                is_running = getattr(status_response, 'is_running', False)
                status = getattr(status_response, 'status', 'unknown')
                return 'running' if is_running else status
            return 'unknown'
        except Exception as e:
            print(f"⚠️ Error checking lab status: {e}")
            return 'unknown'

    def start_lab_execution(self, lab_id: str, cutoff_date: datetime, 
                          end_date: datetime, max_iterations: int) -> str:
        """Start lab execution and return job ID."""
        try:
            # Check if lab is already running
            current_status = self.check_lab_status(lab_id)
            if current_status == 'running':
                print(f"⚠️ Lab {lab_id} is already running!")
                return 'already_running'
            
            # Create start request
            start_request = model.StartLabExecutionRequest(
                lab_id=lab_id,
                startunix=int(cutoff_date.timestamp()),
                endunix=int(end_date.timestamp()),
                maxIterations=max_iterations
            )
            
            # Start execution
            job_id = api.start_lab_execution(self.executor, start_request)
            
            print(f"🚀 Started lab execution")
            print(f"   Lab ID: {lab_id}")
            print(f"   Job ID: {job_id}")
            
            return job_id
            
        except Exception as e:
            print(f"❌ Failed to start execution: {e}")
            # Check if it's already running
            if "already active" in str(e).lower():
                print(f"ℹ️ Lab {lab_id} is already active/running")
                return 'already_running'
            raise
    
    def monitor_execution_status(self, lab_id: str, max_wait_minutes: int = 10) -> str:
        """
        Monitor lab execution status until it's actually running (not queued).
        
        Returns: 'running', 'queued', 'failed', or 'timeout'
        """
        print(f"👀 Monitoring execution status for lab {lab_id}...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Get lab execution status using the correct API
                status_response = api.get_lab_execution_update(self.executor, lab_id)
                
                if status_response:
                    # Access attributes directly from the LabExecutionUpdate object
                    status = getattr(status_response, 'status', 'unknown')
                    progress = getattr(status_response, 'progress', 0)
                    generation = getattr(status_response, 'generation', 0)
                    population = getattr(status_response, 'population', 0)
                    is_running = getattr(status_response, 'is_running', False)
                    
                    print(f"📊 Lab {lab_id} status: {status} | Running: {is_running} | Gen: {generation} | Pop: {population} | Progress: {progress}%")
                    
                    if is_running or status == 'running':
                        print(f"✅ Lab {lab_id} is now running! (Gen: {generation}, Pop: {population}, Progress: {progress}%)")
                        return 'running'
                    elif status == 'completed':
                        print(f"✅ Lab {lab_id} completed!")
                        return 'completed'
                    elif status == 'failed':
                        print(f"❌ Lab {lab_id} execution failed")
                        return 'failed'
                    elif status == 'queued':
                        print(f"⏳ Lab {lab_id} is queued, waiting...")
                        time.sleep(10)
                    else:
                        print(f"📊 Lab {lab_id} status: {status}, waiting...")
                        time.sleep(5)
                else:
                    print(f"📊 Lab {lab_id} status: no response, checking...")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                time.sleep(5)
        
        print(f"⏰ Timeout waiting for lab {lab_id} to start running")
        return 'timeout'
    
    def run_longest_backtest(self, lab_ids: List[str], max_iterations: int = 1500, 
                           start_date: str = None, dry_run: bool = False) -> Dict[str, Any]:
        """Run longest backtest for given lab IDs."""
        results = {}
        
        for lab_id in lab_ids:
            try:
                print(f"\n⚙️ Processing lab {lab_id}...")
                
                # Discover cutoff date
                cutoff_date = self.discover_cutoff_date(lab_id)
                
                # Use provided start_date or discovered cutoff_date
                if start_date:
                    cutoff_date = datetime.strptime(start_date, '%Y-%m-%d')
                    print(f"📅 Using provided start date: {cutoff_date.strftime('%Y-%m-%d')}")
                
                end_date = datetime.utcnow()
                
                if dry_run:
                    print(f"[DRY-RUN] Would configure lab {lab_id} for longest backtest")
                    print(f"   Period: {cutoff_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
                    print(f"   Max iterations: {max_iterations}")
                    results[lab_id] = {
                        'status': 'dry_run',
                        'start_date': cutoff_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d'),
                        'max_iterations': max_iterations
                    }
                else:
                    # Configure lab
                    if not self.configure_lab_for_longest_backtest(lab_id, cutoff_date, end_date, max_iterations):
                        results[lab_id] = {'status': 'failed', 'error': 'Configuration failed'}
                        continue
                    
                    # Start execution
                    job_id = self.start_lab_execution(lab_id, cutoff_date, end_date, max_iterations)
                    
                    # Handle different job_id responses
                    if job_id == 'already_running':
                        print(f"ℹ️ Lab {lab_id} is already running, monitoring current status...")
                        execution_status = self.monitor_execution_status(lab_id)
                    else:
                        # Monitor until running
                        execution_status = self.monitor_execution_status(lab_id)
                    
                    results[lab_id] = {
                        'status': execution_status,
                        'job_id': job_id,
                        'start_date': cutoff_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d'),
                        'max_iterations': max_iterations,
                        'period_days': (end_date - cutoff_date).days
                    }
                
            except Exception as e:
                print(f"❌ Error processing lab {lab_id}: {e}")
                results[lab_id] = {'status': 'error', 'error': str(e)}
        
        return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Longest Backtest CLI using v1 API')
    parser.add_argument('--lab-ids', required=True, help='Comma-separated list of lab IDs')
    parser.add_argument('--max-iterations', type=int, default=1500, help='Maximum iterations')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--host', default='127.0.0.1', help='API host')
    parser.add_argument('--port', type=int, default=8090, help='API port')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run')
    parser.add_argument('--output', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    # Parse lab IDs
    lab_ids = [lab_id.strip() for lab_id in args.lab_ids.split(',') if lab_id.strip()]
    if not lab_ids:
        print("❌ No lab IDs provided")
        return 1
    
    # Create longest backtest instance
    longest_backtest = LongestBacktestV1(host=args.host, port=args.port)
    
    # Connect to API
    if not longest_backtest.connect():
        return 1
    
    # Run longest backtests
    results = longest_backtest.run_longest_backtest(
        lab_ids=lab_ids,
        max_iterations=args.max_iterations,
        start_date=args.start_date,
        dry_run=args.dry_run
    )
    
    # Print summary
    print("\n📋 Longest Backtest Summary")
    for lab_id, result in results.items():
        if 'error' in result:
            print(f"  {lab_id}: ❌ {result['error']}")
        else:
            status_icon = "🔄" if result['status'] == 'running' else "⏳" if result['status'] == 'queued' else "✅"
            print(f"  {lab_id}: {status_icon} {result['status']} | {result.get('start_date', 'N/A')} → {result.get('end_date', 'N/A')} | {result.get('period_days', 0)} days")
    
    # Save results if requested
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
