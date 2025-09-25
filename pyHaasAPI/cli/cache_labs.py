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
                # Check for LabStatus enum with value 3 (COMPLETED)
                if hasattr(lab, 'status') and hasattr(lab.status, 'value') and lab.status.value == 3:
                    complete_labs.append(lab)
                # Fallback: check string comparison for backward compatibility
                elif hasattr(lab, 'status') and str(lab.status) == 'LabStatus.COMPLETED':
                    complete_labs.append(lab)
                # Alternative status field (numeric)
                elif hasattr(lab, 'ST') and lab.ST == 3:
                    complete_labs.append(lab)
            
            logger.info(f"📊 Found {len(complete_labs)} complete labs out of {len(all_labs)} total labs")
            return complete_labs
            
        except Exception as e:
            logger.error(f"❌ Failed to get labs: {e}")
            return []
    
    def cache_lab_data(self, lab: Any, analyze_count: int = 100, refresh: bool = False, concurrent: bool = False, max_workers: int = 5) -> Dict[str, Any]:
        """Cache all backtest data for a single lab"""
        try:
            lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            lab_name = getattr(lab, 'name', f'Lab-{lab_id[:8]}')
            
            logger.info(f"🔬 Caching data for lab: {lab_name}")
            
            # Check if we should refresh cache
            if refresh:
                logger.info(f"🔄 Refreshing cache for lab {lab_id}")
                self.cache.refresh_backtest_cache(lab_id)
            
            # Use enhanced fetching for concurrent mode or large analyze_count
            if concurrent or analyze_count >= 1000:
                logger.info(f"🚀 Using enhanced fetching for {analyze_count} backtests...")
                return self._cache_lab_data_enhanced(lab_id, lab_name, analyze_count, concurrent, max_workers)
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
    
    def _cache_lab_data_enhanced(self, lab_id: str, lab_name: str, analyze_count: int, concurrent: bool = False, max_workers: int = 5) -> Dict[str, Any]:
        """Enhanced caching that fetches backtests and runtime data for top performers only"""
        try:
            from pyHaasAPI.tools.utils import fetch_all_lab_backtests
            import time
            
            logger.info(f"🔍 Fetching backtests for lab: {lab_id}")
            
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
            
            # Sort backtests by ROI to get top performers
            try:
                sorted_backtests = sorted(backtests, 
                                        key=lambda x: getattr(x.summary, 'ReturnOnInvestment', 0) if hasattr(x, 'summary') and x.summary else 0, 
                                        reverse=True)
                logger.info(f"📈 Sorted {len(sorted_backtests)} backtests by ROI")
            except Exception as e:
                logger.warning(f"⚠️ Could not sort by ROI, using original order: {e}")
                sorted_backtests = backtests
            
            # Use the full analyze_count for runtime data fetching
            max_runtime_fetches = min(analyze_count, len(sorted_backtests))
            
            if concurrent:
                logger.info(f"🚀 Concurrent fetching runtime data for top {max_runtime_fetches} backtests (max_workers={max_workers})...")
                return self._fetch_runtime_data_concurrent(lab_id, lab_name, sorted_backtests[:max_runtime_fetches], len(backtests), max_workers)
            else:
                logger.info(f"🚀 Sequential fetching runtime data for top {max_runtime_fetches} backtests...")
                return self._fetch_runtime_data_sequential(lab_id, lab_name, sorted_backtests[:max_runtime_fetches], len(backtests))
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced caching: {e}")
            return {
                "lab_id": lab_id,
                "lab_name": lab_name,
                "cached_backtests": 0,
                "success": False,
                "error": str(e)
            }
    
    def _fetch_runtime_data_sequential(self, lab_id: str, lab_name: str, backtests: list, total_backtests: int) -> Dict[str, Any]:
        """Sequential runtime data fetching (original method)"""
        successful_fetches = 0
        failed_fetches = 0
        
        for i, backtest in enumerate(backtests):
            backtest_id = getattr(backtest, 'backtest_id', None)
            if not backtest_id:
                logger.warning(f"❌ Backtest {i+1}: No backtest_id found")
                failed_fetches += 1
                continue
                
            try:
                if (i + 1) % 10 == 0:
                    logger.info(f"📊 Progress: {i+1}/{len(backtests)} backtests processed")
                
                # Fetch runtime data using the api module
                from pyHaasAPI import api
                runtime_data = api.get_backtest_runtime(self.analyzer.executor, lab_id, backtest_id)
                
                # Cache the runtime data
                self.cache.cache_backtest_data(lab_id, backtest_id, runtime_data)
                
                successful_fetches += 1
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"❌ Error fetching runtime data for backtest {i+1}: {e}")
                failed_fetches += 1
                continue
        
        logger.info(f"📊 SEQUENTIAL FETCH SUMMARY:")
        logger.info(f"✅ Successful runtime fetches: {successful_fetches}")
        logger.info(f"❌ Failed runtime fetches: {failed_fetches}")
        logger.info(f"📊 Total backtests available: {total_backtests}")
        logger.info(f"📊 Runtime data cached for top {len(backtests)} backtests")
        
        return {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "cached_backtests": successful_fetches,
            "total_backtests": total_backtests,
            "success": successful_fetches > 0,
            "successful_fetches": successful_fetches,
            "failed_fetches": failed_fetches,
            "method": "sequential"
        }
    
    def _fetch_runtime_data_concurrent(self, lab_id: str, lab_name: str, backtests: list, total_backtests: int, max_workers: int) -> Dict[str, Any]:
        """Concurrent runtime data fetching using ThreadPoolExecutor"""
        import concurrent.futures
        import threading
        from pyHaasAPI import api
        
        successful_fetches = 0
        failed_fetches = 0
        progress_lock = threading.Lock()
        
        def fetch_single_backtest(backtest_info):
            """Fetch runtime data for a single backtest"""
            nonlocal successful_fetches, failed_fetches
            i, backtest = backtest_info
            backtest_id = getattr(backtest, 'backtest_id', None)
            
            if not backtest_id:
                with progress_lock:
                    failed_fetches += 1
                return False
            
            try:
                # Fetch runtime data using the api module
                runtime_data = api.get_backtest_runtime(self.analyzer.executor, lab_id, backtest_id)
                
                # Cache the runtime data
                self.cache.cache_backtest_data(lab_id, backtest_id, runtime_data)
                
                with progress_lock:
                    successful_fetches += 1
                    if (successful_fetches + failed_fetches) % 10 == 0:
                        logger.info(f"📊 Progress: {successful_fetches + failed_fetches}/{len(backtests)} backtests processed")
                
                return True
                
            except Exception as e:
                with progress_lock:
                    failed_fetches += 1
                logger.warning(f"❌ Error fetching runtime data for backtest {i+1}: {e}")
                return False
        
        # Prepare backtest info for concurrent processing
        backtest_info_list = [(i, backtest) for i, backtest in enumerate(backtests)]
        
        # Use ThreadPoolExecutor for concurrent fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_backtest = {
                executor.submit(fetch_single_backtest, backtest_info): backtest_info 
                for backtest_info in backtest_info_list
            }
            
            # Process completed tasks
            for future in concurrent.futures.as_completed(future_to_backtest):
                try:
                    result = future.result()
                except Exception as e:
                    logger.warning(f"❌ Unexpected error in concurrent fetch: {e}")
                    with progress_lock:
                        failed_fetches += 1
        
        logger.info(f"📊 CONCURRENT FETCH SUMMARY:")
        logger.info(f"✅ Successful runtime fetches: {successful_fetches}")
        logger.info(f"❌ Failed runtime fetches: {failed_fetches}")
        logger.info(f"📊 Total backtests available: {total_backtests}")
        logger.info(f"📊 Runtime data cached for top {len(backtests)} backtests")
        logger.info(f"🚀 Used {max_workers} concurrent workers")
        
        return {
            "lab_id": lab_id,
            "lab_name": lab_name,
            "cached_backtests": successful_fetches,
            "total_backtests": total_backtests,
            "success": successful_fetches > 0,
            "successful_fetches": successful_fetches,
            "failed_fetches": failed_fetches,
            "method": f"concurrent_{max_workers}workers"
        }
    
    def get_unprocessed_labs(self, target_backtests_per_lab: int = 1000) -> List[Any]:
        """Get labs that need processing (not cached or incomplete cache)"""
        try:
            # Get all complete labs from server
            all_complete_labs = self.get_complete_labs()
            if not all_complete_labs:
                logger.warning("⚠️ No complete labs found")
                return []
            
            unprocessed_labs = []
            
            for lab in all_complete_labs:
                lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
                lab_name = getattr(lab, 'name', f'Lab-{lab_id[:8]}')
                
                # Check how many backtests are cached for this lab
                cached_count = self._count_cached_backtests(lab_id)
                
                if cached_count < target_backtests_per_lab:
                    logger.info(f"📋 Lab {lab_name}: {cached_count}/{target_backtests_per_lab} backtests cached - NEEDS PROCESSING")
                    unprocessed_labs.append({
                        'lab': lab,
                        'lab_id': lab_id,
                        'lab_name': lab_name,
                        'cached_count': cached_count,
                        'needed_count': target_backtests_per_lab - cached_count
                    })
                else:
                    logger.info(f"✅ Lab {lab_name}: {cached_count}/{target_backtests_per_lab} backtests cached - COMPLETE")
            
            return unprocessed_labs
            
        except Exception as e:
            logger.error(f"❌ Error getting unprocessed labs: {e}")
            return []
    
    def _count_cached_backtests(self, lab_id: str) -> int:
        """Count how many backtests are cached for a specific lab"""
        try:
            from pathlib import Path
            cache_dir = Path('unified_cache/backtests')
            if not cache_dir.exists():
                return 0
            
            # Count files that start with the lab_id
            cached_files = list(cache_dir.glob(f'{lab_id}_*.json'))
            return len(cached_files)
            
        except Exception as e:
            logger.warning(f"⚠️ Error counting cached backtests for {lab_id}: {e}")
            return 0
    
    def resume_interrupted_caching(self, target_backtests_per_lab: int = 1000, concurrent: bool = True, max_workers: int = 5) -> Dict[str, Any]:
        """Resume interrupted caching with detailed progress tracking and error recovery"""
        logger.info("🔄 Resuming interrupted lab caching process...")
        
        # Get unprocessed labs
        unprocessed_labs = self.get_unprocessed_labs(target_backtests_per_lab)
        
        if not unprocessed_labs:
            logger.info("✅ All labs are already fully cached!")
            return {
                "total_labs": 0,
                "successful_caches": 0,
                "failed_caches": 0,
                "total_backtests_cached": 0,
                "processing_time": 0.0,
                "message": "All labs already cached"
            }
        
        logger.info(f"📋 Found {len(unprocessed_labs)} labs that need completion:")
        for lab_info in unprocessed_labs:
            logger.info(f"   • {lab_info['lab_name']}: {lab_info['cached_count']}/{target_backtests_per_lab} cached (needs {lab_info['needed_count']} more)")
        
        # Process each unprocessed lab with enhanced error handling
        successful_caches = 0
        failed_caches = 0
        total_backtests_cached = 0
        results = []
        
        for i, lab_info in enumerate(unprocessed_labs):
            lab = lab_info['lab']
            lab_id = lab_info['lab_id']
            lab_name = lab_info['lab_name']
            needed_count = lab_info['needed_count']
            current_count = lab_info['cached_count']
            
            logger.info(f"📊 Resuming lab {i+1}/{len(unprocessed_labs)}: {lab_name}")
            logger.info(f"   Current: {current_count}/{target_backtests_per_lab} cached")
            logger.info(f"   Need to cache: {needed_count} more backtests")
            
            # Cache the remaining backtests for this lab
            result = self.cache_lab_data(lab, needed_count, refresh=False, concurrent=concurrent, max_workers=max_workers)
            results.append(result)
            
            if result["success"]:
                successful_caches += 1
                total_backtests_cached += result["cached_backtests"]
                final_count = current_count + result["cached_backtests"]
                logger.info(f"✅ Successfully cached {result['cached_backtests']} more backtests for {lab_name}")
                logger.info(f"   Final count: {final_count}/{target_backtests_per_lab} cached")
            else:
                failed_caches += 1
                logger.error(f"❌ Failed to cache backtests for {lab_name}")
                logger.error(f"   Remaining: {needed_count} backtests still needed")
        
        # Calculate processing time
        processing_time = time.time() - self.start_time
        
        # Print enhanced summary
        self.print_resume_summary({
            "total_labs": len(unprocessed_labs),
            "successful_caches": successful_caches,
            "failed_caches": failed_caches,
            "total_backtests_cached": total_backtests_cached,
            "processing_time": processing_time,
            "results": results,
            "target_per_lab": target_backtests_per_lab
        })
        
        return {
            "total_labs": len(unprocessed_labs),
            "successful_caches": successful_caches,
            "failed_caches": failed_caches,
            "total_backtests_cached": total_backtests_cached,
            "processing_time": processing_time,
            "results": results
        }

    def process_unprocessed_labs(self, target_backtests_per_lab: int = 1000, concurrent: bool = True, max_workers: int = 5) -> Dict[str, Any]:
        """Process all unprocessed labs automatically"""
        logger.info("🔍 Scanning for unprocessed labs...")
        
        # Get unprocessed labs
        unprocessed_labs = self.get_unprocessed_labs(target_backtests_per_lab)
        
        if not unprocessed_labs:
            logger.info("✅ All labs are already fully cached!")
            return {
                "total_labs": 0,
                "successful_caches": 0,
                "failed_caches": 0,
                "total_backtests_cached": 0,
                "processing_time": 0.0,
                "message": "All labs already cached"
            }
        
        logger.info(f"📋 Found {len(unprocessed_labs)} labs that need processing")
        
        # Process each unprocessed lab
        successful_caches = 0
        failed_caches = 0
        total_backtests_cached = 0
        results = []
        
        for i, lab_info in enumerate(unprocessed_labs):
            lab = lab_info['lab']
            lab_id = lab_info['lab_id']
            lab_name = lab_info['lab_name']
            needed_count = lab_info['needed_count']
            
            logger.info(f"📊 Processing lab {i+1}/{len(unprocessed_labs)}: {lab_name}")
            logger.info(f"   Need to cache {needed_count} more backtests")
            
            # Cache the remaining backtests for this lab
            result = self.cache_lab_data(lab, needed_count, refresh=False, concurrent=concurrent, max_workers=max_workers)
            results.append(result)
            
            if result["success"]:
                successful_caches += 1
                total_backtests_cached += result["cached_backtests"]
                logger.info(f"✅ Successfully cached {result['cached_backtests']} backtests for {lab_name}")
            else:
                failed_caches += 1
                logger.error(f"❌ Failed to cache backtests for {lab_name}")
        
        # Calculate processing time
        processing_time = time.time() - self.start_time
        
        # Print summary
        self.print_summary({
            "total_labs": len(unprocessed_labs),
            "successful_caches": successful_caches,
            "failed_caches": failed_caches,
            "total_backtests_cached": total_backtests_cached,
            "processing_time": processing_time,
            "results": results
        })
        
        return {
            "total_labs": len(unprocessed_labs),
            "successful_caches": successful_caches,
            "failed_caches": failed_caches,
            "total_backtests_cached": total_backtests_cached,
            "processing_time": processing_time,
            "results": results
        }

    def cleanup_obsolete_labs(self, current_lab_ids: set, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up cache files for labs that no longer exist on the server"""
        from pathlib import Path
        
        cache_dir = Path('unified_cache/backtests')
        if not cache_dir.exists():
            return {
                'obsolete_labs': [],
                'files_removed': 0,
                'dry_run': dry_run
            }
        
        # Find all cached files and group by lab ID
        cached_files = list(cache_dir.glob('*.json'))
        lab_files = {}
        for file_path in cached_files:
            lab_id = file_path.stem.split('_')[0]
            if lab_id not in lab_files:
                lab_files[lab_id] = []
            lab_files[lab_id].append(file_path)
        
        # Find obsolete labs
        obsolete_labs = []
        for lab_id, files in lab_files.items():
            if lab_id not in current_lab_ids:
                obsolete_labs.append({
                    'lab_id': lab_id,
                    'file_count': len(files),
                    'files': files
                })
        
        # Remove files if not dry run
        files_removed = 0
        if not dry_run:
            for lab_info in obsolete_labs:
                for file_path in lab_info['files']:
                    file_path.unlink()
                    files_removed += 1
        
        return {
            'obsolete_labs': obsolete_labs,
            'files_removed': files_removed,
            'dry_run': dry_run,
            'total_obsolete_files': sum(lab['file_count'] for lab in obsolete_labs)
            }
    
    def cache_all_labs(self, lab_ids: List[str] = None, exclude_lab_ids: List[str] = None,
                      analyze_count: int = 100, refresh: bool = False, concurrent: bool = False, max_workers: int = 5) -> Dict[str, Any]:
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
            
            result = self.cache_lab_data(lab, analyze_count, refresh, concurrent, max_workers)
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
    
    def print_resume_summary(self, result: Dict[str, Any]):
        """Print enhanced resume summary with detailed progress tracking"""
        logger.info("=" * 70)
        logger.info("🔄 RESUME CACHING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total Labs Resumed: {result['total_labs']}")
        logger.info(f"Successful Completions: {result['successful_caches']}")
        logger.info(f"Failed Completions: {result['failed_caches']}")
        logger.info(f"Additional Backtests Cached: {result['total_backtests_cached']}")
        logger.info(f"Resume Processing Time: {result['processing_time']:.2f} seconds")
        logger.info(f"Target per Lab: {result['target_per_lab']} backtests")
        
        # Show detailed results for each lab
        if result['results']:
            logger.info("\n📋 DETAILED RESULTS:")
            for i, lab_result in enumerate(result['results']):
                status = "✅ COMPLETED" if lab_result['success'] else "❌ FAILED"
                logger.info(f"   {i+1}. {lab_result['lab_name']}: {status}")
                if lab_result['success']:
                    logger.info(f"      Cached: {lab_result['cached_backtests']} additional backtests")
                else:
                    logger.info(f"      Error: {lab_result.get('error', 'Unknown error')}")
        
        if result['successful_caches'] > 0:
            logger.info("\n✅ Resume process completed successfully!")
            logger.info("💡 You can now run analysis commands on the cached data")
        elif result['failed_caches'] > 0:
            logger.warning("\n⚠️ Some labs failed to complete. You can run the resume command again.")
            logger.info("💡 Use: python -m pyHaasAPI.cli.cache_labs --resume-interrupted")
        else:
            logger.info("\n✅ All labs were already complete - no resume needed!")


def main(args=None):
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Cache Labs - Cache all lab data for analysis without creating bots',
        epilog='''
Examples:
  # Cache all complete labs
  python -m pyHaasAPI.cli.cache_labs
  
  # Smart mode: only process labs that need caching (RECOMMENDED)
  python -m pyHaasAPI.cli.cache_labs --process-unprocessed --concurrent --max-workers 5
  
  # Resume interrupted caching with detailed progress tracking
  python -m pyHaasAPI.cli.cache_labs --resume-interrupted --concurrent --max-workers 5
  
  # Cache specific labs
  python -m pyHaasAPI.cli.cache_labs --lab-ids lab1,lab2,lab3
  
  # Cache all labs except specific ones
  python -m pyHaasAPI.cli.cache_labs --exclude-lab-ids lab1,lab2
  
  # Refresh existing cache
  python -m pyHaasAPI.cli.cache_labs --refresh
  
  # Cache with custom analysis count and concurrent processing
  python -m pyHaasAPI.cli.cache_labs --analyze-count 1000 --concurrent --max-workers 5
  
  # Clean up obsolete labs (dry run by default)
  python -m pyHaasAPI.cli.cache_labs --dry-run
  python -m pyHaasAPI.cli.cache_labs --force
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--analyze-count', type=int, default=100,
                       help='Number of backtests to analyze per lab (default: 100)')
    parser.add_argument('--refresh', action='store_true',
                       help='Refresh existing cache data')
    parser.add_argument('--concurrent', action='store_true',
                       help='Use concurrent fetching for better performance')
    parser.add_argument('--max-workers', type=int, default=5,
                       help='Maximum number of concurrent workers (default: 5)')
    parser.add_argument('--process-unprocessed', action='store_true',
                       help='Automatically process only unprocessed labs (smart mode)')
    parser.add_argument('--resume-interrupted', action='store_true',
                       help='Resume interrupted caching with detailed progress tracking')
    
    # Cache cleanup options
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be removed without actually removing (for cache cleanup)')
    parser.add_argument('--force', action='store_true',
                       help='Actually remove obsolete cache files (overrides --dry-run)')
    
    # Lab selection options
    lab_group = parser.add_mutually_exclusive_group()
    lab_group.add_argument('--lab-ids', nargs='+', type=str,
                          help='Cache only specific lab IDs')
    lab_group.add_argument('--exclude-lab-ids', nargs='+', type=str,
                          help='Cache all complete labs except these IDs')
    
    args = parser.parse_args(args)
    
    try:
        # Check if this is a cache cleanup operation
        if args.dry_run or args.force:
            # Cache cleanup mode
            print(f"[cache-cleanup] Starting (dry_run={'yes' if args.dry_run and not args.force else 'no'})")
            
            manager = LabCacheManager()
            if not manager.connect():
                sys.exit(1)
            
            # Get current lab IDs from server
            from pyHaasAPI.cli.common import get_complete_labs
            current_labs = get_complete_labs(manager.analyzer.executor)
            current_lab_ids = set()
            for lab in current_labs:
                lab_id = getattr(lab, 'lab_id', None)
                if lab_id:
                    current_lab_ids.add(lab_id)
            
            print(f"[cache-cleanup] Found {len(current_lab_ids)} current labs on server")
            
            # Run cleanup
            dry_run = args.dry_run and not args.force
            result = manager.cleanup_obsolete_labs(current_lab_ids, dry_run=dry_run)
            
            # Print results
            print(f"[cache-cleanup] Found {len(result['obsolete_labs'])} obsolete labs with {result['total_obsolete_files']} files")
            for lab_info in result['obsolete_labs']:
                print(f"  - {lab_info['lab_id']}: {lab_info['file_count']} files")
            
            if dry_run:
                print(f"[cache-cleanup] DRY RUN - No files were actually removed")
                print(f"[cache-cleanup] Use --force to actually remove these files")
            else:
                print(f"[cache-cleanup] Removed {result['files_removed']} files from {len(result['obsolete_labs'])} obsolete labs")
            
            sys.exit(0)
        
        # Normal cache operation
        # Ensure users see something even if logging is muted upstream
        print(
            f"[cache-labs] Starting (analyze_count={args.analyze_count}, "
            f"refresh={'yes' if args.refresh else 'no'}, "
            f"lab_ids={','.join(args.lab_ids) if args.lab_ids else 'ALL'}, "
            f"exclude_lab_ids={','.join(args.exclude_lab_ids) if args.exclude_lab_ids else 'NONE'}, "
            f"process_unprocessed={'yes' if args.process_unprocessed else 'no'})",
            flush=True,
        )
        manager = LabCacheManager()
        
        if not manager.connect():
            sys.exit(1)
        
        # Check which mode to use
        if args.resume_interrupted:
            # Resume mode: detailed progress tracking for interrupted processes
            result = manager.resume_interrupted_caching(
                target_backtests_per_lab=args.analyze_count,
                concurrent=args.concurrent,
                max_workers=args.max_workers
            )
        elif args.process_unprocessed:
            # Smart mode: only process labs that need caching
            result = manager.process_unprocessed_labs(
                target_backtests_per_lab=args.analyze_count,
                concurrent=args.concurrent,
                max_workers=args.max_workers
            )
        else:
            # Normal mode: cache labs with specified criteria
            result = manager.cache_all_labs(
                lab_ids=args.lab_ids,
                exclude_lab_ids=args.exclude_lab_ids,
                analyze_count=args.analyze_count,
                refresh=args.refresh,
                concurrent=args.concurrent,
                max_workers=args.max_workers
            )
        
        # Always print a concise summary to stdout
        print(
            (
                "[cache-labs] Finished: "
                f"labs={result.get('total_labs', 0)}, "
                f"successful={result.get('successful_caches', 0)}, "
                f"failed={result.get('failed_caches', 0)}, "
                f"cached_backtests={result.get('total_backtests_cached', 0)}, "
                f"time={result.get('processing_time', 0.0):.2f}s"
            ),
            flush=True,
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
