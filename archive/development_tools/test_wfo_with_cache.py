#!/usr/bin/env python3
"""
Test WFO functionality using cached data
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Optional imports for advanced analysis
try:
    import numpy as np
    _has_numpy = True
except ImportError:
    _has_numpy = False
    # Create dummy numpy for basic operations
    class np:
        @staticmethod
        def random():
            import random
            return type('random', (), {
                'uniform': lambda a, b: random.uniform(a, b),
                'seed': lambda x: random.seed(x)
            })()

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from pyHaasAPI.analysis.wfo import WFOAnalyzer, WFOConfig, WFOMode, WFOResult, WFOResult
from pyHaasAPI.analysis.cache import UnifiedCacheManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CachedWFOAnalyzer(WFOAnalyzer):
    """WFO Analyzer that works with cached data"""
    
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
    
    def analyze_wfo_period(self, lab_id: str, period, config: WFOConfig) -> WFOResult:
        """Analyze a single WFO period using cached data"""
        try:
            logger.info(f"🔍 Analyzing WFO period {period.period_id}")
            logger.info(f"   Training: {period.training_start.date()} to {period.training_end.date()}")
            logger.info(f"   Testing: {period.testing_start.date()} to {period.testing_end.date()}")
            
            # Get cached backtests for this lab
            if lab_id not in self.cached_backtests:
                self.load_cached_backtests(lab_id)
            
            backtests = self.cached_backtests[lab_id]
            if not backtests:
                raise ValueError("No cached backtests found")
            
            # For this test, we'll use all backtests as "training" data
            # In a real implementation, you'd filter by actual dates
            training_backtests = backtests
            
            if len(training_backtests) < config.min_training_periods:
                raise ValueError(f"Insufficient training data: {len(training_backtests)} < {config.min_training_periods}")
            
            # Find best backtest in training period
            best_backtest = self._find_best_cached_backtest(training_backtests, config)
            if not best_backtest:
                raise ValueError("No suitable backtest found in training period")
            
            # Extract training metrics
            training_metrics = self._extract_cached_backtest_metrics(best_backtest)
            
            # Simulate out-of-sample testing
            testing_metrics = self._simulate_out_of_sample_performance(best_backtest, period, config)
            
            # Calculate stability score
            stability_score = self._calculate_stability_score(training_metrics, testing_metrics)
            
            return WFOResult(
                period=period,
                best_backtest_id=best_backtest.get('backtest_id', 'unknown'),
                best_parameters=self._extract_cached_parameters(best_backtest),
                training_metrics=training_metrics,
                testing_metrics=testing_metrics,
                out_of_sample_return=testing_metrics.get('return', 0.0),
                out_of_sample_sharpe=testing_metrics.get('sharpe_ratio', 0.0),
                out_of_sample_max_drawdown=testing_metrics.get('max_drawdown', 0.0),
                stability_score=stability_score,
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ Error analyzing WFO period {period.period_id}: {e}")
            return WFOResult(
                period=period,
                best_backtest_id="",
                best_parameters={},
                training_metrics={},
                testing_metrics={},
                out_of_sample_return=0.0,
                out_of_sample_sharpe=0.0,
                out_of_sample_max_drawdown=0.0,
                stability_score=0.0,
                success=False,
                error_message=str(e)
            )
    
    def _find_best_cached_backtest(self, backtests, config: WFOConfig):
        """Find the best backtest from cached data"""
        best_backtest = None
        best_score = float('-inf')
        
        for backtest in backtests:
            try:
                # Extract metrics from cached data
                # The structure might be different, so we'll be flexible
                roi = self._extract_metric(backtest, 'roi', 0.0)
                win_rate = self._extract_metric(backtest, 'win_rate', 0.0)
                total_trades = self._extract_metric(backtest, 'total_trades', 0)
                max_drawdown = self._extract_metric(backtest, 'max_drawdown', 0.0)
                
                # Apply filters
                if total_trades < config.min_trades:
                    continue
                if win_rate < config.min_win_rate:
                    continue
                if max_drawdown > config.max_drawdown_threshold:
                    continue
                
                # Calculate composite score
                score = self._calculate_composite_score(roi, win_rate, total_trades, max_drawdown)
                
                if score > best_score:
                    best_score = score
                    best_backtest = backtest
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing cached backtest: {e}")
                continue
        
        return best_backtest
    
    def _extract_metric(self, backtest_data, metric_name, default_value):
        """Extract a metric from cached backtest data"""
        # Map metric names to the actual keys in cached data
        metric_mapping = {
            'roi': 'roi_percentage',
            'win_rate': 'win_rate',
            'total_trades': 'total_trades',
            'max_drawdown': 'max_drawdown',
            'profit_factor': 'profit_factor',
            'sharpe_ratio': 'sharpe_ratio',
            'avg_profit_per_trade': 'avg_profit_per_trade'
        }
        
        # Get the actual key name
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
    
    def _extract_cached_parameters(self, backtest_data):
        """Extract parameters from cached backtest data"""
        return {
            'backtest_id': backtest_data.get('backtest_id', 'unknown'),
            'generation_idx': backtest_data.get('generation_idx', 0),
            'population_idx': backtest_data.get('population_idx', 0)
        }


def test_wfo_with_cache():
    """Test WFO analysis using cached data"""
    logger.info("🚀 Testing WFO analysis with cached data")
    
    # Create cache manager and analyzer
    cache_manager = UnifiedCacheManager()
    analyzer = CachedWFOAnalyzer(cache_manager)
    
    # Test lab ID (we know we have cached data for this one)
    lab_id = "e4616b35-8065-4095-966b-546de68fd493"
    
    # Load cached backtests
    backtests = analyzer.load_cached_backtests(lab_id)
    if not backtests:
        logger.error("❌ No cached backtests found")
        return False
    
    # Create WFO configuration
    config = WFOConfig(
        total_start_date=datetime(2022, 1, 1),
        total_end_date=datetime(2023, 12, 31),
        training_duration_days=60,   # 2 months training
        testing_duration_days=30,    # 1 month testing
        step_size_days=30,           # 1 month step
        mode=WFOMode.ROLLING_WINDOW,
        min_trades=2,  # Lower threshold for testing
        min_win_rate=0.0,  # Very low threshold
        min_profit_factor=0.5,  # Lower threshold
        max_drawdown_threshold=1000.0  # Much higher threshold
    )
    
    try:
        # Generate periods
        logger.info(f"🔧 Config: training={config.training_duration_days} days, testing={config.testing_duration_days} days, step={config.step_size_days} days")
        periods = analyzer.generate_wfo_periods(config)
        logger.info(f"📅 Generated {len(periods)} WFO periods")
        
        if periods:
            logger.info(f"   First period: {periods[0].training_start.date()} to {periods[0].testing_end.date()}")
            logger.info(f"   Last period: {periods[-1].training_start.date()} to {periods[-1].testing_end.date()}")
        
        # Analyze first few periods (for testing)
        test_periods = periods[:3]  # Test first 3 periods
        results = []
        
        for period in test_periods:
            result = analyzer.analyze_wfo_period(lab_id, period, config)
            results.append(result)
        
        # Calculate summary metrics
        summary_metrics = analyzer._calculate_summary_metrics(results)
        
        # Print results
        logger.info("\n" + "="*60)
        logger.info("📊 WFO ANALYSIS RESULTS (CACHED DATA)")
        logger.info("="*60)
        
        logger.info(f"Lab ID: {lab_id[:8]}")
        logger.info(f"Total Periods Analyzed: {len(results)}")
        logger.info(f"Successful Periods: {sum(1 for r in results if r.success)}")
        logger.info(f"Failed Periods: {sum(1 for r in results if not r.success)}")
        
        if summary_metrics:
            logger.info(f"\n📈 PERFORMANCE METRICS:")
            logger.info(f"  Average Return: {summary_metrics.get('avg_return', 0):.2f}%")
            logger.info(f"  Average Sharpe: {summary_metrics.get('avg_sharpe', 0):.2f}")
            logger.info(f"  Average Drawdown: {summary_metrics.get('avg_drawdown', 0):.2f}%")
            logger.info(f"  Average Stability: {summary_metrics.get('avg_stability', 0):.3f}")
            logger.info(f"  Success Rate: {summary_metrics.get('success_rate', 0):.1%}")
        
        # Show individual period results
        logger.info(f"\n📋 INDIVIDUAL PERIOD RESULTS:")
        for result in results:
            if result.success:
                logger.info(f"  Period {result.period.period_id}: {result.out_of_sample_return:.2f}% return, Sharpe: {result.out_of_sample_sharpe:.2f}, Stability: {result.stability_score:.3f}")
            else:
                logger.info(f"  Period {result.period.period_id}: FAILED - {result.error_message}")
        
        logger.info("="*60)
        logger.info("✅ WFO analysis with cached data completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ WFO analysis failed: {e}")
        return False


if __name__ == '__main__':
    success = test_wfo_with_cache()
    sys.exit(0 if success else 1)
