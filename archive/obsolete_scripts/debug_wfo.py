#!/usr/bin/env python3
"""
Debug WFO analysis to see what's actually happening
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI.analysis.wfo import WFOAnalyzer, WFOConfig, WFOMode, WFOResult, WFOPeriod
from pyHaasAPI.analysis.cache import UnifiedCacheManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DebugWFOAnalyzer(WFOAnalyzer):
    """Debug WFO Analyzer to see what's happening"""
    
    def __init__(self, cache_manager: UnifiedCacheManager):
        super().__init__(cache_manager)
        self.cached_backtests = {}
    
    def load_cached_backtests(self, lab_id: str):
        """Load backtests from cache"""
        cache_dir = Path("unified_cache/backtests")
        backtests = []
        
        # Find all cached files for this lab
        for cache_file in cache_dir.glob(f"{lab_id}_*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    backtests.append(data)
            except Exception as e:
                logger.warning(f"⚠️ Could not load {cache_file}: {e}")
        
        logger.info(f"📁 Loaded {len(backtests)} cached backtests for lab {lab_id[:8]}")
        self.cached_backtests[lab_id] = backtests
        return backtests
    
    def _extract_metric(self, backtest_data, metric_name, default_value):
        """Extract a metric from cached backtest data"""
        metric_mapping = {
            'roi': 'roi_percentage',
            'win_rate': 'win_rate',
            'total_trades': 'total_trades',
            'max_drawdown': 'max_drawdown',
            'profit_factor': 'profit_factor',
            'sharpe_ratio': 'sharpe_ratio',
            'avg_profit_per_trade': 'avg_profit_per_trade'
        }
        
        actual_key = metric_mapping.get(metric_name, metric_name)
        
        try:
            value = backtest_data.get(actual_key, default_value)
            return float(value) if value is not None else default_value
        except (TypeError, ValueError):
            return default_value
    
    def _extract_cached_backtest_metrics(self, backtest_data):
        """Extract metrics from cached backtest data"""
        return {
            'roi': self._extract_metric(backtest_data, 'roi', 0.0),
            'win_rate': self._extract_metric(backtest_data, 'win_rate', 0.0),
            'total_trades': self._extract_metric(backtest_data, 'total_trades', 0),
            'max_drawdown': self._extract_metric(backtest_data, 'max_drawdown', 0.0),
            'profit_factor': self._extract_metric(backtest_data, 'profit_factor', 0.0),
            'sharpe_ratio': self._extract_metric(backtest_data, 'sharpe_ratio', 0.0),
            'avg_profit_per_trade': self._extract_metric(backtest_data, 'avg_profit_per_trade', 0.0)
        }
    
    def _find_best_cached_backtest(self, backtests, config: WFOConfig):
        """Find the best backtest from cached data with debug info"""
        best_backtest = None
        best_score = float('-inf')
        
        logger.info(f"🔍 Analyzing {len(backtests)} backtests for best selection")
        
        for i, backtest in enumerate(backtests[:10]):  # Only check first 10 for debug
            try:
                # Extract metrics from cached data
                roi = self._extract_metric(backtest, 'roi', 0.0)
                win_rate = self._extract_metric(backtest, 'win_rate', 0.0)
                total_trades = self._extract_metric(backtest, 'total_trades', 0)
                max_drawdown = self._extract_metric(backtest, 'max_drawdown', 0.0)
                
                logger.info(f"   Backtest {i}: ROI={roi:.2f}%, WR={win_rate:.2f}, Trades={total_trades}, DD={max_drawdown:.2f}")
                
                # Apply filters
                if total_trades < config.min_trades:
                    logger.info(f"     ❌ Filtered out: trades < {config.min_trades}")
                    continue
                if win_rate < config.min_win_rate:
                    logger.info(f"     ❌ Filtered out: win_rate < {config.min_win_rate}")
                    continue
                if max_drawdown > config.max_drawdown_threshold:
                    logger.info(f"     ❌ Filtered out: drawdown > {config.max_drawdown_threshold}")
                    continue
                
                # Calculate composite score
                score = self._calculate_composite_score(roi, win_rate, total_trades, max_drawdown)
                logger.info(f"     ✅ Score: {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_backtest = backtest
                    logger.info(f"     🏆 New best backtest!")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing backtest {i}: {e}")
                continue
        
        logger.info(f"🏆 Best backtest selected with score: {best_score:.2f}")
        return best_backtest
    
    def _simulate_out_of_sample_performance(self, backtest: Any, period: WFOPeriod, config: WFOConfig) -> Dict[str, float]:
        """Simulate out-of-sample performance with debug info"""
        logger.info("🎲 Simulating out-of-sample performance...")
        
        # This is a simplified simulation
        # In practice, you'd run the strategy on the actual testing period
        
        base_metrics = self._extract_cached_backtest_metrics(backtest)
        logger.info(f"   Base metrics: {base_metrics}")
        
        # Add some randomness to simulate out-of-sample performance
        import random
        random.seed(42)
        
        # Simulate performance degradation
        degradation_factor = random.uniform(0.7, 1.0)
        logger.info(f"   Degradation factor: {degradation_factor:.3f}")
        
        simulated_metrics = {
            'return': base_metrics['roi'] * degradation_factor,
            'win_rate': max(0.0, base_metrics['win_rate'] - random.uniform(0.0, 0.1)),
            'sharpe_ratio': base_metrics['sharpe_ratio'] * degradation_factor,
            'max_drawdown': base_metrics['max_drawdown'] + random.uniform(0.0, base_metrics['max_drawdown'] * 0.05),
            'profit_factor': base_metrics['profit_factor'] * degradation_factor
        }
        
        logger.info(f"   Simulated metrics: {simulated_metrics}")
        return simulated_metrics
    
    def _calculate_stability_score(self, training_metrics: Dict[str, float], testing_metrics: Dict[str, float]) -> float:
        """Calculate stability score with debug info"""
        logger.info("📊 Calculating stability score...")
        logger.info(f"   Training metrics: {training_metrics}")
        logger.info(f"   Testing metrics: {testing_metrics}")
        
        if not training_metrics or not testing_metrics:
            logger.info("   ❌ Empty metrics, returning 0.0")
            return 0.0
        
        # Calculate stability based on performance consistency
        training_return = training_metrics.get('roi', 0.0)
        testing_return = testing_metrics.get('return', 0.0)
        
        if training_return == 0:
            stability = 0.0
        else:
            # Calculate relative performance degradation
            degradation = abs(testing_return - training_return) / abs(training_return)
            stability = max(0.0, 1.0 - degradation)
        
        logger.info(f"   Training return: {training_return:.2f}%")
        logger.info(f"   Testing return: {testing_return:.2f}%")
        logger.info(f"   Calculated stability: {stability:.3f}")
        
        return stability


def debug_wfo_analysis():
    """Debug WFO analysis to see what's happening"""
    logger.info("🔍 Debugging WFO Analysis")
    logger.info("="*50)
    
    # Create cache manager and analyzer
    cache_manager = UnifiedCacheManager()
    analyzer = DebugWFOAnalyzer(cache_manager)
    
    # Test lab ID
    lab_id = "e4616b35-8065-4095-966b-546de68fd493"
    
    # Load cached backtests
    backtests = analyzer.load_cached_backtests(lab_id)
    if not backtests:
        logger.error("❌ No cached backtests found")
        return False
    
    # Show sample of cached data
    logger.info("\n📋 Sample cached backtest data:")
    sample_backtest = backtests[0]
    for key, value in sample_backtest.items():
        logger.info(f"   {key}: {value}")
    
    # Create simple WFO configuration
    config = WFOConfig(
        total_start_date=datetime(2022, 1, 1),
        total_end_date=datetime(2023, 12, 31),
        training_duration_days=60,
        testing_duration_days=30,
        step_size_days=30,
        mode=WFOMode.ROLLING_WINDOW,
        min_trades=2,
        min_win_rate=0.0,
        min_profit_factor=0.5,
        max_drawdown_threshold=1000.0
    )
    
    try:
        # Generate one period
        periods = analyzer.generate_wfo_periods(config)
        logger.info(f"\n📅 Generated {len(periods)} WFO periods")
        
        if periods:
            period = periods[0]
            logger.info(f"🔍 Analyzing first period: {period.period_id}")
            logger.info(f"   Training: {period.training_start.date()} to {period.training_end.date()}")
            logger.info(f"   Testing: {period.testing_start.date()} to {period.testing_end.date()}")
            
            # Find best backtest
            best_backtest = analyzer._find_best_cached_backtest(backtests, config)
            if best_backtest:
                logger.info(f"\n🏆 Best backtest found:")
                logger.info(f"   ID: {best_backtest.get('backtest_id', 'unknown')}")
                logger.info(f"   ROI: {best_backtest.get('roi_percentage', 0):.2f}%")
                logger.info(f"   Win Rate: {best_backtest.get('win_rate', 0):.2f}")
                logger.info(f"   Trades: {best_backtest.get('total_trades', 0)}")
                
                # Extract training metrics
                training_metrics = analyzer._extract_cached_backtest_metrics(best_backtest)
                logger.info(f"\n📊 Training metrics: {training_metrics}")
                
                # Simulate testing
                testing_metrics = analyzer._simulate_out_of_sample_performance(best_backtest, period, config)
                logger.info(f"\n🎲 Testing metrics: {testing_metrics}")
                
                # Calculate stability
                stability = analyzer._calculate_stability_score(training_metrics, testing_metrics)
                logger.info(f"\n📈 Final stability score: {stability:.3f}")
                
            else:
                logger.error("❌ No suitable backtest found")
        
    except Exception as e:
        logger.error(f"❌ Debug analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("\n✅ Debug analysis completed")
    return True


if __name__ == '__main__':
    success = debug_wfo_analysis()
    sys.exit(0 if success else 1)
