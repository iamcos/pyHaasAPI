#!/usr/bin/env python3
"""
Temporary script to reanalyze all cached backtest data with enhanced features:
- Calculate ROI from trades data
- Enhanced max drawdown display
- Update cache with new analysis fields
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add the current directory to the path so we can import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.analysis.models import BacktestAnalysis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_cached_backtest_data(cache_file_path: Path) -> Dict[str, Any]:
    """Load cached backtest data from JSON file"""
    try:
        with open(cache_file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading cache file {cache_file_path}: {e}")
        return {}


def extract_lab_id_from_filename(filename: str) -> str:
    """Extract lab ID from cache filename (format: labid_backtestid.json)"""
    return filename.split('_')[0]


def reanalyze_backtest_with_enhanced_features(cached_data: Dict[str, Any], lab_id: str) -> BacktestAnalysis:
    """Reanalyze backtest with enhanced features"""
    
    # Create analyzer instance
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    
    # Extract basic info from cached data
    backtest_id = cached_data.get('backtest_id', '')
    generation_idx = cached_data.get('generation_idx')
    population_idx = cached_data.get('population_idx')
    market_tag = cached_data.get('market_tag', '')
    script_id = cached_data.get('script_id', '')
    script_name = cached_data.get('script_name', '')
    
    # Initialize analysis data with existing values
    analysis_data = {
        'roi_percentage': cached_data.get('roi_percentage', 0.0),
        'calculated_roi_percentage': 0.0,  # Will be calculated
        'roi_difference': 0.0,  # Will be calculated
        'win_rate': cached_data.get('win_rate', 0.0),
        'total_trades': cached_data.get('total_trades', 0),
        'max_drawdown': cached_data.get('max_drawdown', 0.0),
        'realized_profits_usdt': cached_data.get('realized_profits_usdt', 0.0),
        'pc_value': cached_data.get('pc_value', 0.0),
        'avg_profit_per_trade': cached_data.get('avg_profit_per_trade', 0.0),
        'profit_factor': cached_data.get('profit_factor', 0.0),
        'sharpe_ratio': cached_data.get('sharpe_ratio', 0.0)
    }
    
    # Calculate ROI from trades data if runtime data is available
    runtime_data = cached_data.get('runtime_data', {})
    if runtime_data:
        # Extract trades to verify we can find them
        trades = analyzer._extract_trades_from_runtime_data(runtime_data)
        logger.info(f"Found {len(trades)} trades in backtest {backtest_id[:8]}")
        
        if trades:
            calculated_roi = analyzer._calculate_roi_from_trades(runtime_data)
            analysis_data['calculated_roi_percentage'] = calculated_roi
            analysis_data['roi_difference'] = abs(analysis_data['roi_percentage'] - calculated_roi)
            
            # Analyze drawdowns
            drawdown_analysis = analyzer._analyze_drawdowns_from_balance_history(runtime_data)
            
            # Enhanced logging
            drawdown_info = ""
            if drawdown_analysis:
                drawdown_info = f", DD Count={drawdown_analysis.drawdown_count}, Lowest={drawdown_analysis.lowest_balance:.1f}"
            
            logger.info(f"Backtest {backtest_id[:8]}: Lab ROI={analysis_data['roi_percentage']:.2f}%, "
                       f"ROE={calculated_roi:.2f}%, Diff={analysis_data['roi_difference']:.2f}%{drawdown_info}")
        else:
            logger.warning(f"No trades found in runtime data for backtest {backtest_id[:8]}")
            analysis_data['calculated_roi_percentage'] = 0.0
            analysis_data['roi_difference'] = 0.0
            drawdown_analysis = None
    else:
        logger.warning(f"No runtime data available for backtest {backtest_id[:8]}")
        analysis_data['calculated_roi_percentage'] = 0.0
        analysis_data['roi_difference'] = 0.0
    
    # Create enhanced analysis object
    enhanced_analysis = BacktestAnalysis(
        backtest_id=backtest_id,
        lab_id=lab_id,
        generation_idx=generation_idx,
        population_idx=population_idx,
        market_tag=market_tag,
        script_id=script_id,
        script_name=script_name,
        roi_percentage=analysis_data['roi_percentage'],
        calculated_roi_percentage=analysis_data['calculated_roi_percentage'],
        roi_difference=analysis_data['roi_difference'],
        win_rate=analysis_data['win_rate'],
        total_trades=analysis_data['total_trades'],
        max_drawdown=analysis_data['max_drawdown'],
        realized_profits_usdt=analysis_data['realized_profits_usdt'],
        pc_value=analysis_data['pc_value'],
        drawdown_analysis=drawdown_analysis,
        avg_profit_per_trade=analysis_data['avg_profit_per_trade'],
        profit_factor=analysis_data['profit_factor'],
        sharpe_ratio=analysis_data['sharpe_ratio'],
        analysis_timestamp=datetime.now().isoformat()
    )
    
    return enhanced_analysis


def update_cache_with_enhanced_data(enhanced_analysis: BacktestAnalysis, cache_file_path: Path):
    """Update cache file with enhanced analysis data"""
    try:
        # Convert analysis to dict
        enhanced_data = {
            'backtest_id': enhanced_analysis.backtest_id,
            'lab_id': enhanced_analysis.lab_id,
            'generation_idx': enhanced_analysis.generation_idx,
            'population_idx': enhanced_analysis.population_idx,
            'market_tag': enhanced_analysis.market_tag,
            'script_id': enhanced_analysis.script_id,
            'script_name': enhanced_analysis.script_name,
            'roi_percentage': enhanced_analysis.roi_percentage,
            'calculated_roi_percentage': enhanced_analysis.calculated_roi_percentage,
            'roi_difference': enhanced_analysis.roi_difference,
            'win_rate': enhanced_analysis.win_rate,
            'total_trades': enhanced_analysis.total_trades,
            'max_drawdown': enhanced_analysis.max_drawdown,
            'realized_profits_usdt': enhanced_analysis.realized_profits_usdt,
            'pc_value': enhanced_analysis.pc_value,
            'avg_profit_per_trade': enhanced_analysis.avg_profit_per_trade,
            'profit_factor': enhanced_analysis.profit_factor,
            'sharpe_ratio': enhanced_analysis.sharpe_ratio,
            'analysis_timestamp': enhanced_analysis.analysis_timestamp,
            'backtest_timestamp': None
        }
        
        # Load original data to preserve runtime_data
        original_data = load_cached_backtest_data(cache_file_path)
        if 'runtime_data' in original_data:
            enhanced_data['runtime_data'] = original_data['runtime_data']
        
        # Write enhanced data back to cache
        with open(cache_file_path, 'w') as f:
            json.dump(enhanced_data, f, indent=2)
        
        logger.info(f"✅ Updated cache for backtest {enhanced_analysis.backtest_id[:8]}")
        
    except Exception as e:
        logger.error(f"❌ Error updating cache for backtest {enhanced_analysis.backtest_id[:8]}: {e}")


def find_backtests_with_good_roi(cache_dir: Path, min_roi: float = 100.0) -> List[Path]:
    """Find backtest cache files with good ROI"""
    good_backtests = []
    
    for cache_file in cache_dir.glob("*.json"):
        try:
            cached_data = load_cached_backtest_data(cache_file)
            roi = cached_data.get('roi_percentage', 0.0)
            
            if roi >= min_roi:
                good_backtests.append(cache_file)
                logger.info(f"Found good backtest: {cache_file.name} - ROI: {roi:.2f}%")
                
        except Exception as e:
            logger.warning(f"Error reading {cache_file.name}: {e}")
    
    return good_backtests


def main():
    """Main function to reanalyze all cached backtests"""
    logger.info("🚀 Starting reanalysis of cached backtest data...")
    
    # Setup paths
    cache_dir = Path("unified_cache/backtests")
    if not cache_dir.exists():
        logger.error(f"Cache directory not found: {cache_dir}")
        return
    
    # Find all cache files
    cache_files = list(cache_dir.glob("*.json"))
    logger.info(f"Found {len(cache_files)} cached backtest files")
    
    if not cache_files:
        logger.warning("No cache files found to reanalyze")
        return
    
    # First, find a backtest with good ROI to test our enhanced analysis
    logger.info("🔍 Looking for backtests with good ROI to test enhanced analysis...")
    good_backtests = find_backtests_with_good_roi(cache_dir, min_roi=50.0)  # Lower threshold for testing
    
    if good_backtests:
        # Test with one good backtest first
        test_file = good_backtests[0]
        logger.info(f"🧪 Testing enhanced analysis with: {test_file.name}")
        
        # Load and reanalyze
        cached_data = load_cached_backtest_data(test_file)
        lab_id = extract_lab_id_from_filename(test_file.name)
        
        enhanced_analysis = reanalyze_backtest_with_enhanced_features(cached_data, lab_id)
        
        # Update cache
        update_cache_with_enhanced_data(enhanced_analysis, test_file)
        
        logger.info(f"✅ Test completed successfully!")
        logger.info(f"   Lab ROI: {enhanced_analysis.roi_percentage:.2f}%")
        logger.info(f"   Calculated ROI: {enhanced_analysis.calculated_roi_percentage:.2f}%")
        logger.info(f"   Win Rate: {enhanced_analysis.win_rate:.1%}")
        logger.info(f"   Max Drawdown: {enhanced_analysis.max_drawdown:.1f}%")
        logger.info(f"   Total Trades: {enhanced_analysis.total_trades}")
        
        # Now process all remaining files
        logger.info("🔄 Processing all remaining cache files...")
        processed_count = 0
        error_count = 0
        
        for cache_file in cache_files:
            if cache_file == test_file:  # Skip the test file
                continue
                
            try:
                cached_data = load_cached_backtest_data(cache_file)
                lab_id = extract_lab_id_from_filename(cache_file.name)
                
                enhanced_analysis = reanalyze_backtest_with_enhanced_features(cached_data, lab_id)
                update_cache_with_enhanced_data(enhanced_analysis, cache_file)
                
                processed_count += 1
                
                if processed_count % 10 == 0:
                    logger.info(f"📊 Processed {processed_count}/{len(cache_files)-1} files...")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {cache_file.name}: {e}")
                error_count += 1
        
        logger.info("🎉 Reanalysis complete!")
        logger.info(f"   ✅ Successfully processed: {processed_count} files")
        logger.info(f"   ❌ Errors: {error_count} files")
        logger.info(f"   📁 Total files: {len(cache_files)}")
        
    else:
        logger.warning("No backtests with good ROI found. Processing all files anyway...")
        
        # Process all files
        processed_count = 0
        error_count = 0
        
        for cache_file in cache_files:
            try:
                cached_data = load_cached_backtest_data(cache_file)
                lab_id = extract_lab_id_from_filename(cache_file.name)
                
                enhanced_analysis = reanalyze_backtest_with_enhanced_features(cached_data, lab_id)
                update_cache_with_enhanced_data(enhanced_analysis, cache_file)
                
                processed_count += 1
                
                if processed_count % 10 == 0:
                    logger.info(f"📊 Processed {processed_count}/{len(cache_files)} files...")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {cache_file.name}: {e}")
                error_count += 1
        
        logger.info("🎉 Reanalysis complete!")
        logger.info(f"   ✅ Successfully processed: {processed_count} files")
        logger.info(f"   ❌ Errors: {error_count} files")


if __name__ == "__main__":
    main()
