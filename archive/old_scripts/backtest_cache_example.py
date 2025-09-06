#!/usr/bin/env python3
"""
Backtest Cache Example Script

This script demonstrates how to work with the backtest caching system,
including how to access cached data, process it, and create custom analytics.
"""

import os
import json
import csv
import pickle
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestCacheManager:
    """Manages backtest cache operations and data access"""
    
    def __init__(self, cache_root: str = "cache"):
        self.cache_root = Path(cache_root)
        self.backtest_cache_dir = Path("backtest_cache")
        
    def get_latest_lab_cache(self, lab_id: Optional[str] = None) -> Optional[Path]:
        """Get the most recent cache directory for a lab"""
        if not self.cache_root.exists():
            logger.warning(f"Cache root directory does not exist: {self.cache_root}")
            return None
            
        # Find all lab cache directories
        lab_dirs = []
        for item in self.cache_root.iterdir():
            if item.is_dir() and item.name.startswith("lab_backtests_"):
                if lab_id is None or lab_id in item.name:
                    lab_dirs.append(item)
        
        if not lab_dirs:
            logger.warning(f"No lab cache directories found in {self.cache_root}")
            return None
            
        # Return the most recent one
        latest_dir = sorted(lab_dirs)[-1]
        logger.info(f"Found latest cache directory: {latest_dir}")
        return latest_dir
    
    def load_backtests_list(self, cache_dir: Path) -> List[Dict[str, Any]]:
        """Load the complete backtests list from cache"""
        list_file = cache_dir / "backtests_list.json"
        if not list_file.exists():
            logger.error(f"Backtests list file not found: {list_file}")
            return []
            
        try:
            with open(list_file, 'r') as f:
                backtests = json.load(f)
            logger.info(f"Loaded {len(backtests)} backtests from cache")
            return backtests
        except Exception as e:
            logger.error(f"Error loading backtests list: {e}")
            return []
    
    def load_backtest_details(self, cache_dir: Path, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Load detailed data for a specific backtest"""
        detail_file = cache_dir / "backtest_details" / f"{backtest_id}.json"
        if not detail_file.exists():
            logger.warning(f"Backtest detail file not found: {detail_file}")
            return None
            
        try:
            with open(detail_file, 'r') as f:
                backtest_data = json.load(f)
            logger.info(f"Loaded backtest details for {backtest_id}")
            return backtest_data
        except Exception as e:
            logger.error(f"Error loading backtest details for {backtest_id}: {e}")
            return None
    
    def load_analytics_csv(self, cache_dir: Path) -> List[Dict[str, Any]]:
        """Load analytics data from CSV"""
        csv_file = cache_dir / "backtests_analytics.csv"
        if not csv_file.exists():
            logger.warning(f"Analytics CSV file not found: {csv_file}")
            return []
            
        try:
            analytics = []
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert string values to appropriate types
                    analytics.append(self._convert_csv_row_types(row))
            logger.info(f"Loaded {len(analytics)} analytics records from CSV")
            return analytics
        except Exception as e:
            logger.error(f"Error loading analytics CSV: {e}")
            return []
    
    def _convert_csv_row_types(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Convert CSV string values to appropriate Python types"""
        converted = {}
        for key, value in row.items():
            if value == '':
                converted[key] = None
            elif key in ['roi_percentage', 'win_rate', 'max_drawdown', 'fees_usdt', 
                        'pc_value', 'realized_profits_usdt']:
                try:
                    converted[key] = float(value) if value else 0.0
                except ValueError:
                    converted[key] = 0.0
            elif key in ['total_trades', 'winning_trades', 'losing_trades', 'orders', 'positions']:
                try:
                    converted[key] = int(value) if value else 0
                except ValueError:
                    converted[key] = 0
            elif key == 'beats_buy_hold':
                converted[key] = value.lower() == 'true'
            else:
                converted[key] = value
        return converted
    
    def get_pickle_cache_info(self) -> Dict[str, Any]:
        """Get information about pickle cache files"""
        if not self.backtest_cache_dir.exists():
            return {"error": "Backtest cache directory not found"}
            
        cache_info = {
            "cache_dir": str(self.backtest_cache_dir),
            "files": [],
            "total_size": 0
        }
        
        for file_path in self.backtest_cache_dir.iterdir():
            if file_path.is_file():
                file_info = {
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                cache_info["files"].append(file_info)
                cache_info["total_size"] += file_info["size"]
        
        return cache_info

class BacktestAnalyzer:
    """Advanced backtest analysis and reporting"""
    
    def __init__(self, cache_manager: BacktestCacheManager):
        self.cache_manager = cache_manager
    
    def generate_performance_summary(self, analytics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive performance summary"""
        if not analytics:
            return {"error": "No analytics data provided"}
        
        # Calculate summary statistics
        total_backtests = len(analytics)
        profitable_backtests = len([a for a in analytics if a.get('roi_percentage', 0) > 0])
        beating_buy_hold = len([a for a in analytics if a.get('beats_buy_hold', False)])
        
        # Performance metrics
        roi_values = [a.get('roi_percentage', 0) for a in analytics]
        win_rates = [a.get('win_rate', 0) for a in analytics if a.get('win_rate') is not None]
        trade_counts = [a.get('total_trades', 0) for a in analytics]
        
        summary = {
            "total_backtests": total_backtests,
            "profitable_backtests": profitable_backtests,
            "profitable_percentage": (profitable_backtests / total_backtests * 100) if total_backtests > 0 else 0,
            "beating_buy_hold": beating_buy_hold,
            "beating_buy_hold_percentage": (beating_buy_hold / total_backtests * 100) if total_backtests > 0 else 0,
            "roi_statistics": {
                "mean": sum(roi_values) / len(roi_values) if roi_values else 0,
                "median": sorted(roi_values)[len(roi_values)//2] if roi_values else 0,
                "min": min(roi_values) if roi_values else 0,
                "max": max(roi_values) if roi_values else 0,
                "std_dev": self._calculate_std_dev(roi_values) if roi_values else 0
            },
            "win_rate_statistics": {
                "mean": sum(win_rates) / len(win_rates) if win_rates else 0,
                "median": sorted(win_rates)[len(win_rates)//2] if win_rates else 0,
                "min": min(win_rates) if win_rates else 0,
                "max": max(win_rates) if win_rates else 0
            },
            "trade_statistics": {
                "total_trades": sum(trade_counts),
                "mean_trades_per_backtest": sum(trade_counts) / len(trade_counts) if trade_counts else 0,
                "max_trades": max(trade_counts) if trade_counts else 0,
                "min_trades": min(trade_counts) if trade_counts else 0
            }
        }
        
        return summary
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def find_top_performers(self, analytics: List[Dict[str, Any]], 
                          metric: str = 'roi_percentage', top_n: int = 10) -> List[Dict[str, Any]]:
        """Find top performing backtests by specified metric"""
        if not analytics:
            return []
        
        # Sort by metric (descending)
        sorted_analytics = sorted(analytics, key=lambda x: x.get(metric, 0), reverse=True)
        
        # Return top N with ranking
        top_performers = []
        for i, analysis in enumerate(sorted_analytics[:top_n]):
            performer = analysis.copy()
            performer['rank'] = i + 1
            top_performers.append(performer)
        
        return top_performers
    
    def analyze_script_performance(self, analytics: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by script"""
        script_stats = {}
        
        for analysis in analytics:
            script_name = analysis.get('script_name', 'Unknown')
            if script_name not in script_stats:
                script_stats[script_name] = {
                    'count': 0,
                    'total_roi': 0,
                    'total_trades': 0,
                    'profitable_count': 0,
                    'beating_buy_hold_count': 0
                }
            
            stats = script_stats[script_name]
            stats['count'] += 1
            stats['total_roi'] += analysis.get('roi_percentage', 0)
            stats['total_trades'] += analysis.get('total_trades', 0)
            
            if analysis.get('roi_percentage', 0) > 0:
                stats['profitable_count'] += 1
            
            if analysis.get('beats_buy_hold', False):
                stats['beating_buy_hold_count'] += 1
        
        # Calculate averages and percentages
        for script_name, stats in script_stats.items():
            stats['avg_roi'] = stats['total_roi'] / stats['count'] if stats['count'] > 0 else 0
            stats['avg_trades'] = stats['total_trades'] / stats['count'] if stats['count'] > 0 else 0
            stats['profitable_percentage'] = (stats['profitable_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
            stats['beating_buy_hold_percentage'] = (stats['beating_buy_hold_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
        
        return script_stats

def main():
    """Main function demonstrating cache usage"""
    logger.info("Starting Backtest Cache Example")
    
    # Initialize cache manager
    cache_manager = BacktestCacheManager()
    
    # Get cache information
    logger.info("=== Cache Information ===")
    pickle_info = cache_manager.get_pickle_cache_info()
    logger.info(f"Pickle cache info: {json.dumps(pickle_info, indent=2)}")
    
    # Find latest lab cache
    latest_cache = cache_manager.get_latest_lab_cache()
    if not latest_cache:
        logger.error("No cache found. Please run fetch_lab_backtests.py first.")
        return
    
    logger.info(f"Using cache directory: {latest_cache}")
    
    # Load analytics data
    analytics = cache_manager.load_analytics_csv(latest_cache)
    if not analytics:
        logger.error("No analytics data found in cache")
        return
    
    # Initialize analyzer
    analyzer = BacktestAnalyzer(cache_manager)
    
    # Generate performance summary
    logger.info("=== Performance Summary ===")
    summary = analyzer.generate_performance_summary(analytics)
    logger.info(f"Performance summary: {json.dumps(summary, indent=2)}")
    
    # Find top performers
    logger.info("=== Top 5 Performers by ROI ===")
    top_performers = analyzer.find_top_performers(analytics, 'roi_percentage', 5)
    for performer in top_performers:
        logger.info(f"Rank {performer['rank']}: {performer.get('script_name', 'Unknown')} - "
                   f"ROI: {performer.get('roi_percentage', 0):.2f}%, "
                   f"Trades: {performer.get('total_trades', 0)}")
    
    # Analyze script performance
    logger.info("=== Script Performance Analysis ===")
    script_stats = analyzer.analyze_script_performance(analytics)
    for script_name, stats in script_stats.items():
        logger.info(f"Script: {script_name}")
        logger.info(f"  Count: {stats['count']}, Avg ROI: {stats['avg_roi']:.2f}%, "
                   f"Profitable: {stats['profitable_percentage']:.1f}%")
    
    # Example: Load specific backtest details
    if analytics:
        first_backtest_id = analytics[0].get('backtest_id')
        if first_backtest_id:
            logger.info(f"=== Loading Details for Backtest: {first_backtest_id} ===")
            details = cache_manager.load_backtest_details(latest_cache, first_backtest_id)
            if details:
                runtime = details.get('runtime', {})
                reports = runtime.get('Reports', {})
                logger.info(f"Backtest has {len(reports)} reports")
                
                # Show first report summary
                if reports:
                    first_report_key = list(reports.keys())[0]
                    first_report = reports[first_report_key]
                    logger.info(f"First report ({first_report_key}):")
                    if 'PR' in first_report:
                        pr_data = first_report['PR']
                        logger.info(f"  ROI: {pr_data.get('ROI', 'N/A')}%")
                        logger.info(f"  Profit: {pr_data.get('RP', 'N/A')} USDT")
                        logger.info(f"  Max Drawdown: {pr_data.get('RM', 'N/A')}%")
    
    logger.info("=== Cache Example Complete ===")

if __name__ == "__main__":
    main()
