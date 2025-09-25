#!/usr/bin/env python3
"""
Lab Monitoring Tool for pyHaasAPI

This tool monitors lab status and backtest counts without downloading new data:
- Check labs without downloading new backtests
- Compare cached vs server backtest counts
- Monitor labs in progress
- Detect labs in run state vs blank/waiting labs
- Selective cache updates for labs with new data
"""

import argparse
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI import api
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LabMonitor:
    """Lab monitoring tool for checking status and backtest counts"""
    
    def __init__(self):
        self.cache_manager = UnifiedCacheManager()
        self.analyzer = None
        self.executor = None
        
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            logger.info("🔌 Connecting to HaasOnline API...")
            
            # Initialize analyzer
            self.analyzer = HaasAnalyzer(self.cache_manager)
            
            # Connect
            if not self.analyzer.connect():
                logger.error("❌ Failed to connect to HaasOnline API")
                return False
            
            self.executor = self.analyzer.executor
            logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_cached_labs(self) -> Dict[str, int]:
        """Get list of cached labs with their backtest counts"""
        cache_dir = self.cache_manager.base_dir / "backtests"
        
        if not cache_dir.exists():
            logger.warning("⚠️ No cache directory found")
            return {}
        
        lab_files = list(cache_dir.glob('*.json'))
        lab_counts = {}
        
        for file_path in lab_files:
            lab_id = file_path.stem.split('_')[0]
            if lab_id not in lab_counts:
                lab_counts[lab_id] = 0
            lab_counts[lab_id] += 1
        
        return lab_counts
    
    def get_server_lab_status(self, lab_id: str) -> Dict[str, Any]:
        """Get lab status from server without downloading backtests"""
        try:
            # Get lab details
            lab_details = api.get_lab_details(self.executor, lab_id)
            
            if not lab_details:
                return {'error': 'Lab not found'}
            
            # Get lab execution status
            execution_status = api.get_lab_execution_update(self.executor, lab_id)
            
            # Get backtest count - use larger page size to get accurate count
            from pyHaasAPI.api import GetBacktestResultRequest
            request = GetBacktestResultRequest(lab_id=lab_id, next_page_id=0, page_lenght=1000)
            backtest_response = api.get_backtest_result(self.executor, request)
            
            return {
                'lab_id': lab_id,
                'lab_name': getattr(lab_details, 'name', 'Unknown'),
                'status': getattr(execution_status, 'status', 'Unknown') if execution_status else 'Unknown',
                'is_running': getattr(execution_status, 'is_running', False) if execution_status else False,
                'total_backtests': getattr(backtest_response, 'total_count', 0) if backtest_response else 0,
                'has_backtests': getattr(backtest_response, 'total_count', 0) > 0 if backtest_response else False,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting server status for lab {lab_id}: {e}")
            return {'error': str(e)}
    
    def get_current_server_labs(self) -> List[str]:
        """Get list of current lab IDs from server"""
        try:
            labs = api.get_all_labs(self.executor)
            lab_ids = []
            
            for lab in labs:
                lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
                if lab_id:
                    lab_ids.append(lab_id)
            
            logger.info(f"📊 Found {len(lab_ids)} labs currently on server")
            return lab_ids
            
        except Exception as e:
            logger.error(f"❌ Error getting server labs: {e}")
            return []
    
    def compare_lab_counts(self, cached_labs: Dict[str, int]) -> List[Dict[str, Any]]:
        """Compare cached vs server backtest counts for labs that exist on server"""
        logger.info("🔍 Comparing cached vs server backtest counts...")
        
        # Get current server labs first
        server_lab_ids = self.get_current_server_labs()
        if not server_lab_ids:
            logger.error("❌ Could not get server labs")
            return []
        
        comparison_results = []
        
        # Only check labs that exist on both server and cache
        labs_to_check = []
        for lab_id in server_lab_ids:
            if lab_id in cached_labs:
                labs_to_check.append((lab_id, cached_labs[lab_id]))
        
        logger.info(f"📊 Checking {len(labs_to_check)} labs that exist on both server and cache")
        
        for i, (lab_id, cached_count) in enumerate(labs_to_check, 1):
            logger.info(f"📊 Checking lab {i}/{len(labs_to_check)}: {lab_id[:8]}")
            
            # Get server status
            server_status = self.get_server_lab_status(lab_id)
            
            if 'error' in server_status:
                logger.warning(f"⚠️ Error for lab {lab_id}: {server_status['error']}")
                continue
            
            server_count = server_status.get('total_backtests', 0)
            difference = server_count - cached_count
            
            result = {
                'lab_id': lab_id,
                'lab_name': server_status.get('lab_name', 'Unknown'),
                'cached_count': cached_count,
                'server_count': server_count,
                'difference': difference,
                'has_new_data': difference > 0,
                'status': server_status.get('status', 'Unknown'),
                'is_running': server_status.get('is_running', False),
                'has_backtests': server_status.get('has_backtests', False)
            }
            
            comparison_results.append(result)
            
            # Log status
            if difference > 0:
                logger.info(f"🆕 {server_status.get('lab_name', 'Unknown')}: {cached_count} → {server_count} (+{difference})")
            elif difference < 0:
                logger.warning(f"⚠️ {server_status.get('lab_name', 'Unknown')}: {cached_count} → {server_count} ({difference})")
            else:
                logger.info(f"✅ {server_status.get('lab_name', 'Unknown')}: {cached_count} (up to date)")
        
        return comparison_results
    
    def monitor_labs_in_progress(self, comparison_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify labs that are currently running or in progress"""
        running_labs = []
        
        for result in comparison_results:
            if result.get('is_running', False):
                running_labs.append(result)
                logger.info(f"🏃 Lab {result['lab_name']} is currently running")
            elif result.get('status') == 'RUNNING':
                running_labs.append(result)
                logger.info(f"🏃 Lab {result['lab_name']} status: RUNNING")
        
        return running_labs
    
    def identify_labs_needing_update(self, comparison_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify labs that have new backtests and need cache updates"""
        labs_needing_update = []
        
        for result in comparison_results:
            if result.get('has_new_data', False):
                labs_needing_update.append(result)
        
        return labs_needing_update
    
    def find_labs_with_many_backtests(self, comparison_results: List[Dict[str, Any]], min_count: int = 250) -> List[Dict[str, Any]]:
        """Find labs with many backtests (active labs)"""
        active_labs = []
        
        for result in comparison_results:
            server_count = result.get('server_count', 0)
            if server_count >= min_count:
                active_labs.append(result)
                logger.info(f"🎯 ACTIVE LAB FOUND: {result['lab_name']} - {server_count} backtests")
        
        return active_labs
    
    def display_monitoring_summary(self, comparison_results: List[Dict[str, Any]], 
                                 running_labs: List[Dict[str, Any]], 
                                 labs_needing_update: List[Dict[str, Any]],
                                 active_labs: List[Dict[str, Any]] = None):
        """Display comprehensive monitoring summary"""
        
        if active_labs is None:
            active_labs = self.find_labs_with_many_backtests(comparison_results)
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 LAB MONITORING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"📅 Check Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📁 Total Labs Checked: {len(comparison_results)}")
        logger.info(f"🏃 Labs Currently Running: {len(running_labs)}")
        logger.info(f"🆕 Labs Needing Cache Update: {len(labs_needing_update)}")
        logger.info(f"🎯 Active Labs (250+ backtests): {len(active_labs)}")
        logger.info("=" * 80)
        
        # Show running labs
        if running_labs:
            logger.info("\n🏃 LABS CURRENTLY RUNNING:")
            logger.info("-" * 60)
            for lab in running_labs:
                logger.info(f"  • {lab['lab_name']} ({lab['lab_id'][:8]})")
                logger.info(f"    Status: {lab['status']}")
                logger.info(f"    Cached: {lab['cached_count']} | Server: {lab['server_count']}")
                logger.info()
        
        # Show labs needing updates
        if labs_needing_update:
            logger.info("\n🆕 LABS NEEDING CACHE UPDATE:")
            logger.info("-" * 60)
            for lab in labs_needing_update:
                logger.info(f"  • {lab['lab_name']} ({lab['lab_id'][:8]})")
                logger.info(f"    Cached: {lab['cached_count']} → Server: {lab['server_count']} (+{lab['difference']})")
                logger.info()
        
        # Show active labs with many backtests
        if active_labs:
            logger.info("\n🎯 ACTIVE LABS WITH MANY BACKTESTS (250+):")
            logger.info("-" * 60)
            for lab in active_labs:
                logger.info(f"  • {lab['lab_name']} ({lab['lab_id'][:8]})")
                logger.info(f"    Server Backtests: {lab['server_count']}")
                logger.info(f"    Cached Backtests: {lab['cached_count']}")
                logger.info(f"    Status: {lab['status']}")
                logger.info(f"    Running: {lab['is_running']}")
                logger.info()
        
        # Show labs with no backtests
        blank_labs = [lab for lab in comparison_results if not lab.get('has_backtests', False)]
        if blank_labs:
            logger.info("\n📋 LABS WITH NO BACKTESTS (BLANK/WAITING):")
            logger.info("-" * 60)
            for lab in blank_labs:
                logger.info(f"  • {lab['lab_name']} ({lab['lab_id'][:8]}) - Status: {lab['status']}")
        
        logger.info("=" * 80)
    
    def save_monitoring_report(self, comparison_results: List[Dict[str, Any]], 
                             running_labs: List[Dict[str, Any]], 
                             labs_needing_update: List[Dict[str, Any]], 
                             output_file: str):
        """Save monitoring report to JSON file"""
        
        report = {
            'metadata': {
                'check_date': datetime.now().isoformat(),
                'total_labs_checked': len(comparison_results),
                'labs_running': len(running_labs),
                'labs_needing_update': len(labs_needing_update)
            },
            'all_labs': comparison_results,
            'running_labs': running_labs,
            'labs_needing_update': labs_needing_update
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"💾 Monitoring report saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Lab Monitoring Tool - Check lab status without downloading data")
    
    # Output options
    parser.add_argument('--output', type=str, help='Save monitoring report to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    # Filtering options
    parser.add_argument('--lab-ids', nargs='+', help='Check specific lab IDs only')
    parser.add_argument('--show-running-only', action='store_true', help='Show only running labs')
    parser.add_argument('--show-updates-only', action='store_true', help='Show only labs needing updates')
    parser.add_argument('--show-active-only', action='store_true', help='Show only active labs with 250+ backtests')
    parser.add_argument('--min-backtests', type=int, default=250, help='Minimum backtests to consider a lab active')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create lab monitor
        monitor = LabMonitor()
        
        # Connect to API
        if not monitor.connect():
            return 1
        
        # Get cached labs
        cached_labs = monitor.get_cached_labs()
        
        if not cached_labs:
            logger.error("❌ No cached labs found")
            return 1
        
        logger.info(f"📁 Found {len(cached_labs)} labs with cached data")
        
        # Filter labs if specified
        if args.lab_ids:
            filtered_cached_labs = {lab_id: count for lab_id, count in cached_labs.items() 
                                  if lab_id in args.lab_ids}
            if not filtered_cached_labs:
                logger.error("❌ No matching labs found in cache")
                return 1
            cached_labs = filtered_cached_labs
            logger.info(f"🎯 Checking {len(cached_labs)} specified labs")
        
        # Compare cached vs server counts
        comparison_results = monitor.compare_lab_counts(cached_labs)
        
        if not comparison_results:
            logger.error("❌ No comparison results generated")
            return 1
        
        # Identify running labs, labs needing updates, and active labs
        running_labs = monitor.monitor_labs_in_progress(comparison_results)
        labs_needing_update = monitor.identify_labs_needing_update(comparison_results)
        active_labs = monitor.find_labs_with_many_backtests(comparison_results, args.min_backtests)
        
        # Apply filters if specified
        if args.show_running_only:
            comparison_results = running_labs
        elif args.show_updates_only:
            comparison_results = labs_needing_update
        elif args.show_active_only:
            comparison_results = active_labs
        
        # Display summary
        monitor.display_monitoring_summary(comparison_results, running_labs, labs_needing_update, active_labs)
        
        # Save report if requested
        if args.output:
            monitor.save_monitoring_report(comparison_results, running_labs, labs_needing_update, args.output)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
