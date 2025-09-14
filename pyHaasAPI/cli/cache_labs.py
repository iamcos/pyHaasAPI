#!/usr/bin/env python3
"""
Cache Labs CLI Tool

This tool caches all lab data without creating bots, perfect for data collection
and analysis preparation.
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.api import RequestsExecutor, get_all_labs, get_lab_details
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LabCacheManager:
    """Manages lab data caching operations"""
    
    def __init__(self):
        self.analyzer = None
        self.cache = UnifiedCacheManager()
        self.start_time = time.time()
        
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        try:
            logger.info("🔌 Connecting to HaasOnline API...")
            
            # Initialize analyzer
            self.analyzer = HaasAnalyzer(self.cache)
            
            # Connect
            if not self.analyzer.connect():
                logger.error("❌ Failed to connect to HaasOnline API")
                return False
                
            logger.info("✅ Connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            return False
    
    def get_complete_labs(self) -> List[Any]:
        """Get all complete labs from the server"""
        try:
            logger.info("📋 Fetching all labs from server...")
            all_labs = get_all_labs(self.analyzer.executor)
            
            # Filter for complete labs only
            complete_labs = []
            for lab in all_labs:
                if hasattr(lab, 'status') and lab.status == '3':  # Status 3 = completed
                    complete_labs.append(lab)
                elif hasattr(lab, 'ST') and lab.ST == '3':  # Alternative status field
                    complete_labs.append(lab)
            
            logger.info(f"📊 Found {len(complete_labs)} complete labs out of {len(all_labs)} total labs")
            return complete_labs
            
        except Exception as e:
            logger.error(f"❌ Failed to get labs: {e}")
            return []
    
    def cache_lab_data(self, lab: Any, analyze_count: int = 100, refresh: bool = False) -> Dict[str, Any]:
        """Cache all backtest data for a single lab"""
        try:
            lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            lab_name = getattr(lab, 'name', f'Lab-{lab_id[:8]}')
            
            logger.info(f"🔬 Caching data for lab: {lab_name}")
            
            # Check if we should refresh cache
            if refresh:
                logger.info(f"🔄 Refreshing cache for lab {lab_id}")
                self.cache.refresh_backtest_cache(lab_id)
            
            # Use enhanced fetching for large analyze_count
            if analyze_count >= 1000:
                logger.info(f"🚀 Using enhanced fetching for {analyze_count} backtests...")
                return self._cache_lab_data_enhanced(lab_id, lab_name, analyze_count)
            else:
                # Use standard analyzer for smaller counts
                result = self.analyzer.analyze_lab(lab_id, top_count=analyze_count)
                
                if result and result.top_backtests:
                    logger.info(f"✅ Cached {len(result.top_backtests)} backtests for {lab_name}")
                    return {
                        "lab_id": lab_id,
                        "lab_name": lab_name,
                        "cached_backtests": len(result.top_backtests),
                        "total_backtests": result.total_backtests,
                        "success": True
                    }
                else:
                    logger.warning(f"⚠️ No backtests found for {lab_name}")
                    return {
                        "lab_id": lab_id,
                        "lab_name": lab_name,
                        "cached_backtests": 0,
                        "total_backtests": 0,
                        "success": False
                    }
                
        except Exception as e:
            logger.error(f"❌ Error caching lab {lab_name}: {e}")
            return {
                "lab_id": lab_id,
                "lab_name": lab_name,
                "cached_backtests": 0,
                "total_backtests": 0,
                "success": False,
                "error": str(e)
            }
    
    def _cache_lab_data_enhanced(self, lab_id: str, lab_name: str, analyze_count: int) -> Dict[str, Any]:
        """Enhanced caching that fetches all backtests with runtime data"""
        try:
            from pyHaasAPI.tools.utils import fetch_all_lab_backtests
            import time
            
            logger.info(f"🔍 Fetching all backtests for lab: {lab_id}")
            
            # Fetch all backtests using page size 1000
            backtests = fetch_all_lab_backtests(self.analyzer.executor, lab_id, page_size=1000)
            logger.info(f"📊 Total backtests fetched: {len(backtests)}")
            
            if not backtests:
                logger.warning(f"⚠️ No backtests found for {lab_name}")
                return {
                    "lab_id": lab_id,
                    "lab_name": lab_name,
                    "cached_backtests": 0,
                    "success": False,
                    "error": "No backtests found"
                }
            
            # Fetch runtime data for each backtest
            logger.info(f"🚀 Starting runtime data fetch for {len(backtests)} backtests...")
            
            successful_fetches = 0
            failed_fetches = 0
            
            for i, backtest in enumerate(backtests):
                backtest_id = getattr(backtest, 'backtest_id', None)
                if not backtest_id:
                    logger.warning(f"❌ Backtest {i+1}: No backtest_id found")
                    failed_fetches += 1
                    continue
                    
                try:
                    if (i + 1) % 100 == 0:
                        logger.info(f"📊 Progress: {i+1}/{len(backtests)} backtests processed")
                    
                    # Fetch runtime data
                    runtime_data = self.analyzer.api.get_backtest_runtime(self.analyzer.executor, lab_id, backtest_id)
                    
                    # Cache the runtime data
                    self.cache.cache_backtest_data(lab_id, backtest_id, runtime_data)
                    
                    successful_fetches += 1
                    
                    # Small delay to avoid overwhelming the API
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"❌ Error fetching runtime data for backtest {i+1}: {e}")
                    failed_fetches += 1
                    continue
            
            logger.info(f"📊 FETCH SUMMARY:")
            logger.info(f"✅ Successful fetches: {successful_fetches}")
            logger.info(f"❌ Failed fetches: {failed_fetches}")
            logger.info(f"📊 Total backtests: {len(backtests)}")
            
            return {
                "lab_id": lab_id,
                "lab_name": lab_name,
                "cached_backtests": successful_fetches,
                "success": successful_fetches > 0,
                "successful_fetches": successful_fetches,
                "failed_fetches": failed_fetches
            }
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced caching: {e}")
            return {
                "lab_id": lab_id,
                "lab_name": lab_name,
                "cached_backtests": 0,
                "success": False,
                "error": str(e)
            }
    
    def cache_all_labs(self, lab_ids: List[str] = None, exclude_lab_ids: List[str] = None,
                      analyze_count: int = 100, refresh: bool = False) -> Dict[str, Any]:
        """Cache data for all or specified labs"""
        logger.info("🚀 Starting lab data caching process...")
        self.start_time = time.time()
        
        # Get all complete labs
        all_complete_labs = self.get_complete_labs()
        if not all_complete_labs:
            logger.warning("⚠️ No complete labs found")
            return {
                "total_labs": 0,
                "successful_caches": 0,
                "failed_caches": 0,
                "total_backtests_cached": 0,
                "processing_time": 0.0
            }
        
        # Filter labs based on selection criteria
        complete_labs = self._filter_labs(all_complete_labs, lab_ids, exclude_lab_ids)
        
        if not complete_labs:
            logger.warning("⚠️ No labs match the selection criteria")
            return {
                "total_labs": 0,
                "successful_caches": 0,
                "failed_caches": 0,
                "total_backtests_cached": 0,
                "processing_time": 0.0
            }
        
        logger.info(f"📋 Found {len(complete_labs)} labs to cache")
        
        successful_caches = 0
        failed_caches = 0
        total_backtests_cached = 0
        results = []
        
        # Process each lab
        for i, lab in enumerate(complete_labs):
            logger.info(f"📊 Processing lab {i+1}/{len(complete_labs)}")
            
            result = self.cache_lab_data(lab, analyze_count, refresh)
            results.append(result)
            
            if result["success"]:
                successful_caches += 1
                total_backtests_cached += result["cached_backtests"]
            else:
                failed_caches += 1
        
        # Calculate processing time
        processing_time = time.time() - self.start_time
        
        # Print summary
        self.print_summary({
            "total_labs": len(complete_labs),
            "successful_caches": successful_caches,
            "failed_caches": failed_caches,
            "total_backtests_cached": total_backtests_cached,
            "processing_time": processing_time,
            "results": results
        })
        
        return {
            "total_labs": len(complete_labs),
            "successful_caches": successful_caches,
            "failed_caches": failed_caches,
            "total_backtests_cached": total_backtests_cached,
            "processing_time": processing_time,
            "results": results
        }
    
    def _filter_labs(self, all_labs: List[Any], lab_ids: List[str] = None, exclude_lab_ids: List[str] = None) -> List[Any]:
        """Filter labs based on inclusion/exclusion criteria"""
        filtered_labs = []
        
        for lab in all_labs:
            lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            
            # If specific lab IDs are provided, only include those
            if lab_ids:
                if lab_id in lab_ids:
                    filtered_labs.append(lab)
                continue
            
            # If exclude lab IDs are provided, skip those
            if exclude_lab_ids:
                if lab_id in exclude_lab_ids:
                    continue
            
            # If no filters, include all labs
            filtered_labs.append(lab)
        
        return filtered_labs
    
    def print_summary(self, result: Dict[str, Any]):
        """Print caching summary"""
        logger.info("=" * 60)
        logger.info("📊 LAB CACHING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Labs Processed: {result['total_labs']}")
        logger.info(f"Successful Caches: {result['successful_caches']}")
        logger.info(f"Failed Caches: {result['failed_caches']}")
        logger.info(f"Total Backtests Cached: {result['total_backtests_cached']}")
        logger.info(f"Processing Time: {result['processing_time']:.2f} seconds")
        
        if result['successful_caches'] > 0:
            logger.info("✅ Lab data caching completed successfully!")
            logger.info("💡 You can now run analysis commands on the cached data")
        else:
            logger.warning("⚠️ No labs were cached successfully")


def main(args=None):
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Cache Labs - Cache all lab data for analysis without creating bots',
        epilog='''
Examples:
  # Cache all complete labs
  python -m pyHaasAPI.cli.cache_labs
  
  # Cache specific labs
  python -m pyHaasAPI.cli.cache_labs --lab-ids lab1,lab2,lab3
  
  # Cache all labs except specific ones
  python -m pyHaasAPI.cli.cache_labs --exclude-lab-ids lab1,lab2
  
  # Refresh existing cache
  python -m pyHaasAPI.cli.cache_labs --refresh
  
  # Cache with custom analysis count
  python -m pyHaasAPI.cli.cache_labs --analyze-count 200
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--analyze-count', type=int, default=100,
                       help='Number of backtests to analyze per lab (default: 100)')
    parser.add_argument('--refresh', action='store_true',
                       help='Refresh existing cache data')
    
    # Lab selection options
    lab_group = parser.add_mutually_exclusive_group()
    lab_group.add_argument('--lab-ids', nargs='+', type=str,
                          help='Cache only specific lab IDs')
    lab_group.add_argument('--exclude-lab-ids', nargs='+', type=str,
                          help='Cache all complete labs except these IDs')
    
    args = parser.parse_args(args)
    
    try:
        manager = LabCacheManager()
        
        if not manager.connect():
            sys.exit(1)
        
        # Cache labs with specified criteria
        result = manager.cache_all_labs(
            lab_ids=args.lab_ids,
            exclude_lab_ids=args.exclude_lab_ids,
            analyze_count=args.analyze_count,
            refresh=args.refresh
        )
        
        # Exit with appropriate code
        if result['successful_caches'] > 0:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n❌ Lab caching interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
