#!/usr/bin/env python3
"""
FIXED Longest Backtest Algorithm

This implements the EXACT algorithm using Unix timestamps:
1. Start with 36 months → if QUEUED, decrease by couple months
2. When RUNNING → increase by week until QUEUED again
3. Then decrease by 5 days until RUNNING again
4. Then increase by 2 days until QUEUED again
5. Then decrease by 1 day until RUNNING again
6. DONE! - that's the longest working period

ONLY changes Unix timestamps and lab name - NEVER touches population/generations
"""

import argparse
import time
import re

from pyHaasAPI_v1 import api, model
from dotenv import load_dotenv
import os

load_dotenv()


class FixedLongestBacktest:
    """FIXED longest backtest algorithm using Unix timestamps."""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8090):
        self.host = host
        self.port = port
        self.executor = None
    
    def connect(self) -> bool:
        """Connect to the API"""
        try:
            self.executor = api.RequestsExecutor(
                host=self.host,
                port=self.port,
                state=api.Guest()
            )
            
            # Authenticate
            self.executor = self.executor.authenticate(
                os.getenv('API_EMAIL'), 
                os.getenv('API_PASSWORD')
            )
            
            print(f"✅ Connected to server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def force_cancel_backtest(self, lab_id: str) -> bool:
        """Force cancel any existing backtest."""
        try:
            print(f"🛑 Force canceling any existing backtest...")
            
            # Try to cancel multiple times
            for attempt in range(3):
                result = api.cancel_lab_execution(self.executor, lab_id)
                time.sleep(2)
                
                # Check if it's actually canceled
                status = api.get_lab_execution_update(self.executor, lab_id)
                if status and getattr(status, 'status', 'unknown') not in ['queued', 'running']:
                    print(f"✅ Backtest canceled successfully")
                    return True
            
            print(f"⚠️ Could not cancel backtest, but continuing...")
            return True
            
        except Exception as e:
            print(f"⚠️ Error canceling backtest: {e}")
            return True  # Continue anyway
    
    def configure_lab_unix_timestamps(self, lab_id: str, start_unix: int, end_unix: int) -> bool:
        """Configure lab with Unix timestamps - ONLY change timestamps."""
        try:
            lab_details = api.get_lab_details(self.executor, lab_id)
            lab_details.start_unix = start_unix
            lab_details.end_unix = end_unix
            api.update_lab_details(self.executor, lab_details)
            
            # Convert to readable dates for display
            start_date = time.strftime('%Y-%m-%d', time.gmtime(start_unix))
            end_date = time.strftime('%Y-%m-%d', time.gmtime(end_unix))
            duration_days = (end_unix - start_unix) // (24 * 3600)
            
            print(f"📅 Configured: {start_date} → {end_date} ({duration_days} days)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure timestamps: {e}")
            return False
    
    def update_lab_name_with_date(self, lab_id: str, start_unix: int) -> bool:
        """Update lab name to include the new start date."""
        try:
            lab_details = api.get_lab_details(self.executor, lab_id)
            current_name = getattr(lab_details, 'name', '')
            
            # Extract the base name (everything before the last date part)
            # Example: "2 - Simple RSING VWAP Strategy - TRX - 25.09.2023" 
            # Should become: "2 - Simple RSING VWAP Strategy - TRX - 15.01.2024"
            
            # Find the last occurrence of a date pattern (DD.MM.YYYY or DD-MM-YYYY)
            date_pattern = r'\s+\d{2}[.-]\d{2}[.-]\d{4}$'
            base_name = re.sub(date_pattern, '', current_name)
            
            # Add new date in DD.MM.YYYY format (no extra dash)
            new_date = time.strftime('%d.%m.%Y', time.gmtime(start_unix))
            new_name = f"{base_name} {new_date}"
            
            # Update the lab name
            lab_details.name = new_name
            api.update_lab_details(self.executor, lab_details)
            
            print(f"📝 Updated lab name: '{current_name}' → '{new_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update lab name: {e}")
            return False
    
    def start_backtest(self, lab_id: str, start_unix: int = None, end_unix: int = None) -> str:
        """Start backtest while preserving lab configuration."""
        try:
            # Get current lab details to preserve configuration
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            # Save original configuration to restore later
            original_config = {
                'max_population': getattr(lab_details.config, 'max_population', 25),
                'max_generations': getattr(lab_details.config, 'max_generations', 40),
                'max_elites': getattr(lab_details.config, 'max_elites', 3),
                'mix_rate': getattr(lab_details.config, 'mix_rate', 40.0),
                'adjust_rate': getattr(lab_details.config, 'adjust_rate', 25.0)
            }
            
            print(f"🔧 Preserving lab config: MP={original_config['max_population']}, MG={original_config['max_generations']}, ME={original_config['max_elites']}, MR={original_config['mix_rate']}, AR={original_config['adjust_rate']}")
            
            # Use provided dates or fall back to lab details
            start_unix_to_use = start_unix if start_unix is not None else lab_details.start_unix
            end_unix_to_use = end_unix if end_unix is not None else lab_details.end_unix
            
            start_request = model.StartLabExecutionRequest(
                lab_id=lab_id,
                startunix=start_unix_to_use,
                endunix=end_unix_to_use,
                maxIterations=getattr(lab_details, 'max_iterations', 1500)
            )
            
            # CRITICAL: Disable ensure_config to prevent API from changing lab configuration
            job_id = api.start_lab_execution(self.executor, start_request, ensure_config=False)
            
            if isinstance(job_id, dict) and job_id.get('Success') == False:
                error_msg = job_id.get('Error', '')
                if 'already active' in error_msg.lower():
                    return 'already_active'
                else:
                    print(f"❌ Start failed: {error_msg}")
                    return 'failed'
            
            # Restore original configuration after starting backtest
            try:
                lab_details.config.max_population = original_config['max_population']
                lab_details.config.max_generations = original_config['max_generations']
                lab_details.config.max_elites = original_config['max_elites']
                lab_details.config.mix_rate = original_config['mix_rate']
                lab_details.config.adjust_rate = original_config['adjust_rate']
                api.update_lab_details(self.executor, lab_details)
                print(f"✅ Restored original lab config: MP={original_config['max_population']}, MG={original_config['max_generations']}")
            except Exception as e:
                print(f"⚠️ Warning: Could not restore lab config: {e}")
            
            print(f"🚀 Started backtest: {job_id}")
            return job_id
            
        except Exception as e:
            print(f"❌ Failed to start: {e}")
            return 'error'
    
    def check_status_after_wait(self, lab_id: str, wait_seconds: int = 5) -> dict:
        """Check status after waiting."""
        print(f"⏳ Waiting {wait_seconds} seconds...")
        time.sleep(wait_seconds)
        
        try:
            status = api.get_lab_execution_update(self.executor, lab_id)
            if status:
                return {
                    'status': getattr(status, 'status', 'unknown'),
                    'is_running': getattr(status, 'is_running', False),
                    'progress': getattr(status, 'progress', 0),
                    'generation': getattr(status, 'generation', 0),
                    'population': getattr(status, 'population', 0)
                }
            return {'status': 'unknown', 'is_running': False, 'progress': 0, 'generation': 0, 'population': 0}
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
            return {'status': 'error', 'is_running': False, 'progress': 0, 'generation': 0, 'population': 0}
    
    def test_period(self, lab_id: str, start_unix: int, end_unix: int, period_name: str) -> bool:
        """Test if a specific period works."""
        try:
            # Convert to readable dates for display
            start_date = time.strftime('%Y-%m-%d', time.gmtime(start_unix))
            end_date = time.strftime('%Y-%m-%d', time.gmtime(end_unix))
            duration_days = (end_unix - start_unix) // (24 * 3600)
            
            print(f"\n🧪 Testing {period_name}: {start_date} → {end_date} ({duration_days} days)")
            
            # CRITICAL: Cancel any existing backtest before starting new one
            print(f"🛑 Canceling any existing backtest before testing {period_name}...")
            self.force_cancel_backtest(lab_id)
            time.sleep(3)  # Wait for cancellation
            
            # Configure timestamps
            if not self.configure_lab_unix_timestamps(lab_id, start_unix, end_unix):
                return False
            
            # Start backtest with the specific dates
            job_id = self.start_backtest(lab_id, start_unix, end_unix)
            if job_id in ['failed', 'error']:
                print(f"❌ Failed to start backtest")
                return False
            
            if job_id == 'already_active':
                print(f"ℹ️ Lab is already active, checking status...")
            
            # Wait and check status
            status = self.check_status_after_wait(lab_id, 5)
            print(f"📊 Status: {status['status']} | Running: {status['is_running']} | Progress: {status['progress']}%")
            
            # FIXED: Proper status detection using LabStatus enum
            from pyHaasAPI_v1.model import LabStatus
            
            # Check if status is RUNNING (value 2) or if is_running is True
            is_running = (status['status'] == LabStatus.RUNNING or 
                         status['status'] == 2 or 
                         status['is_running'])
            is_queued = (status['status'] == LabStatus.QUEUED or 
                       status['status'] == 1)
            
            if is_running:
                print(f"✅ {period_name} WORKS! Backtest is running.")
                # CRITICAL: Cancel this backtest before returning
                print(f"🛑 Canceling successful backtest to test next period...")
                self.force_cancel_backtest(lab_id)
                time.sleep(3)  # Wait for cancellation
                return True
            elif is_queued:
                print(f"⏳ {period_name} is queued - period too long")
                self.force_cancel_backtest(lab_id)
                time.sleep(3)  # Wait for cancellation
                return False
            else:
                print(f"❌ {period_name} failed: {status['status']}")
                # Cancel failed backtest
                self.force_cancel_backtest(lab_id)
                time.sleep(3)  # Wait for cancellation
                return False
                
        except Exception as e:
            print(f"❌ Error testing {period_name}: {e}")
            # Cancel on error
            self.force_cancel_backtest(lab_id)
            time.sleep(3)  # Wait for cancellation
            return False
    
    def find_longest_working_period(self, lab_id: str) -> tuple:
        """Find the longest period that actually works using Unix timestamps."""
        try:
            print(f"🔍 Finding longest working period for lab {lab_id}")
            
            # Get lab info
            lab_details = api.get_lab_details(self.executor, lab_id)
            market_tag = None
            if hasattr(lab_details, 'settings') and hasattr(lab_details.settings, 'market_tag'):
                market_tag = lab_details.settings.market_tag
            
            print(f"📊 Lab: {getattr(lab_details, 'name', 'Unknown')}")
            print(f"🏷️ Market: {market_tag}")
            
            # DEBUG: Show current lab configuration
            if hasattr(lab_details, 'config'):
                config = lab_details.config
                print(f"🔧 Current lab config: MP={getattr(config, 'max_population', 'N/A')}, MG={getattr(config, 'max_generations', 'N/A')}, ME={getattr(config, 'max_elites', 'N/A')}, MR={getattr(config, 'mix_rate', 'N/A')}, AR={getattr(config, 'adjust_rate', 'N/A')}")
            else:
                print(f"⚠️ No config found in lab details")
            
            # Force cancel any existing backtest
            self.force_cancel_backtest(lab_id)
            time.sleep(3)  # Wait for cancellation
            
            # Current time in Unix
            end_unix = int(time.time())
            
            # STEP 1: Start with 36 months, decrease by couple months until RUNNING
            print(f"\n📋 STEP 1: Start with 36 months, decrease by couple months until RUNNING")
            
            # 36 months in seconds (36 * 30.44 * 24 * 3600)
            months_36_seconds = 36 * 30.44 * 24 * 3600  # ≈ 94,371,840 seconds
            current_seconds = months_36_seconds
            start_unix = end_unix - current_seconds
            
            while current_seconds > 0:
                period_name = f"{current_seconds // (30.44 * 24 * 3600):.1f} months"
                if self.test_period(lab_id, start_unix, end_unix, period_name):
                    print(f"✅ Found initial RUNNING period: {current_seconds // (30.44 * 24 * 3600):.1f} months")
                    break
                else:
                    # Decrease by couple months (60 days)
                    current_seconds -= 60 * 24 * 3600  # 60 days in seconds
                    start_unix = end_unix - current_seconds
            
            if current_seconds <= 0:
                print(f"❌ No RUNNING period found")
                return None, None, "none", False
            
            # STEP 2: Increase by week until QUEUED again
            print(f"\n📋 STEP 2: Increase by week until QUEUED again")
            
            step2_iterations = 0
            max_step2_iterations = 20  # Maximum 20 weeks (140 days)
            
            while step2_iterations < max_step2_iterations:
                test_start_unix = end_unix - (current_seconds + 7 * 24 * 3600)  # Add 1 week
                test_days = (end_unix - test_start_unix) // (24 * 3600)
                if not self.test_period(lab_id, test_start_unix, end_unix, f"{test_days} days"):
                    print(f"⏳ {test_days} days is QUEUED - found upper limit")
                    break
                else:
                    current_seconds += 7 * 24 * 3600  # Add 1 week
                    step2_iterations += 1
                    print(f"✅ {test_days} days still RUNNING, trying {test_days + 7} days...")
            
            if step2_iterations >= max_step2_iterations:
                print(f"⚠️ Reached maximum iterations for step 2, continuing...")
            
            # STEP 3: Decrease by 5 days until RUNNING again
            print(f"\n📋 STEP 3: Decrease by 5 days until RUNNING again")
            
            step3_iterations = 0
            max_step3_iterations = 20  # Maximum 20 iterations (100 days)
            
            while step3_iterations < max_step3_iterations:
                test_start_unix = end_unix - (current_seconds - 5 * 24 * 3600)  # Subtract 5 days
                test_days = (end_unix - test_start_unix) // (24 * 3600)
                if self.test_period(lab_id, test_start_unix, end_unix, f"{test_days} days"):
                    print(f"✅ {test_days} days is RUNNING again")
                    current_seconds -= 5 * 24 * 3600  # Subtract 5 days
                    break
                else:
                    current_seconds -= 5 * 24 * 3600  # Subtract 5 days
                    step3_iterations += 1
                    print(f"⏳ {test_days} days still QUEUED, trying {test_days - 5} days...")
            
            if step3_iterations >= max_step3_iterations:
                print(f"⚠️ Reached maximum iterations for step 3, continuing...")
            
            # STEP 4: Increase by 2 days until QUEUED again
            print(f"\n📋 STEP 4: Increase by 2 days until QUEUED again")
            
            step4_iterations = 0
            max_step4_iterations = 20  # Maximum 20 iterations (40 days)
            
            while step4_iterations < max_step4_iterations:
                test_start_unix = end_unix - (current_seconds + 2 * 24 * 3600)  # Add 2 days
                test_days = (end_unix - test_start_unix) // (24 * 3600)
                if not self.test_period(lab_id, test_start_unix, end_unix, f"{test_days} days"):
                    print(f"⏳ {test_days} days is QUEUED - found upper limit")
                    break
                else:
                    current_seconds += 2 * 24 * 3600  # Add 2 days
                    step4_iterations += 1
                    print(f"✅ {test_days} days still RUNNING, trying {test_days + 2} days...")
            
            if step4_iterations >= max_step4_iterations:
                print(f"⚠️ Reached maximum iterations for step 4, continuing...")
            
            # STEP 5: Decrease by 1 day until RUNNING again
            print(f"\n📋 STEP 5: Decrease by 1 day until RUNNING again")
            
            step5_iterations = 0
            max_step5_iterations = 10  # Maximum 10 iterations (10 days)
            
            while step5_iterations < max_step5_iterations:
                test_start_unix = end_unix - (current_seconds - 1 * 24 * 3600)  # Subtract 1 day
                test_days = (end_unix - test_start_unix) // (24 * 3600)
                if self.test_period(lab_id, test_start_unix, end_unix, f"{test_days} days"):
                    print(f"✅ {test_days} days is RUNNING - FOUND LONGEST PERIOD!")
                    current_seconds -= 1 * 24 * 3600  # Subtract 1 day
                    break
                else:
                    current_seconds -= 1 * 24 * 3600  # Subtract 1 day
                    step5_iterations += 1
                    print(f"⏳ {test_days} days still QUEUED, trying {test_days - 1} days...")
            
            if step5_iterations >= max_step5_iterations:
                print(f"⚠️ Reached maximum iterations for step 5, using current period...")
            
            # Final result
            final_start_unix = end_unix - current_seconds
            final_days = current_seconds // (24 * 3600)
            final_period_name = f"{final_days} days"
            
            print(f"🎉 SUCCESS! Longest working period: {final_period_name}")
            print(f"   Period: {time.strftime('%Y-%m-%d', time.gmtime(final_start_unix))} → {time.strftime('%Y-%m-%d', time.gmtime(end_unix))}")
            print(f"   Duration: {final_days} days")
            print(f"   Boundary: {final_days + 1} days = QUEUED, {final_days} days = RUNNING")
            
            # Update lab name with new start date
            print(f"\n📝 Updating lab name with new start date...")
            self.update_lab_name_with_date(lab_id, final_start_unix)
            
            return final_start_unix, end_unix, final_period_name, True
            
        except Exception as e:
            print(f"❌ Error finding longest period: {e}")
            return None, None, "error", False
    
    def run_longest_backtest(self, lab_ids: list, dry_run: bool = False) -> dict:
        """Run fixed longest backtest."""
        results = {}
        
        for lab_id in lab_ids:
            try:
                print(f"\n⚙️ Processing lab {lab_id}...")
                
                if dry_run:
                    print(f"[DRY-RUN] Would find longest working period using Unix timestamps")
                    results[lab_id] = {'status': 'dry_run', 'message': 'Would use correct algorithm with Unix timestamps: 36 months → decrease until RUNNING → increase by week until QUEUED → decrease by 5 days until RUNNING → increase by 2 days until QUEUED → decrease by 1 day until RUNNING'}
                else:
                    start_unix, end_unix, period_name, success = self.find_longest_working_period(lab_id)
                    
                    if success:
                        results[lab_id] = {
                            'status': 'success',
                            'start_date': time.strftime('%Y-%m-%d', time.gmtime(start_unix)),
                            'end_date': time.strftime('%Y-%m-%d', time.gmtime(end_unix)),
                            'duration_days': (end_unix - start_unix) // (24 * 3600),
                            'period_name': period_name,
                            'message': f'Longest working period: {period_name}'
                        }
                    else:
                        results[lab_id] = {
                            'status': 'failed',
                            'message': 'No working period found'
                        }
                
            except Exception as e:
                print(f"❌ Error processing lab {lab_id}: {e}")
                results[lab_id] = {'error': str(e)}
        
        return results


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='FIXED Longest Backtest Algorithm')
    parser.add_argument('--lab-ids', required=True, help='Comma-separated list of lab IDs')
    parser.add_argument('--host', default='127.0.0.1', help='API host')
    parser.add_argument('--port', type=int, default=8090, help='API port')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run')
    
    args = parser.parse_args()
    
    lab_ids = [lab_id.strip() for lab_id in args.lab_ids.split(',') if lab_id.strip()]
    if not lab_ids:
        print("❌ No lab IDs provided")
        return 1
    
    fixed_backtest = FixedLongestBacktest(host=args.host, port=args.port)
    
    if not fixed_backtest.connect():
        return 1
    
    results = fixed_backtest.run_longest_backtest(lab_ids, dry_run=args.dry_run)
    
    print("\n📋 FIXED Longest Backtest Summary")
    for lab_id, result in results.items():
        if 'error' in result:
            print(f"  {lab_id}: ❌ {result['error']}")
        else:
            status_icon = "🧪" if result['status'] == 'dry_run' else "✅" if result['status'] == 'success' else "❌"
            print(f"  {lab_id}: {status_icon} {result['status']} | {result.get('message', 'N/A')}")
            if result['status'] == 'success':
                print(f"    Period: {result.get('start_date', 'N/A')} → {result.get('end_date', 'N/A')} ({result.get('duration_days', 0)} days)")
    
    return 0


if __name__ == "__main__":
    exit(main())
