#!/usr/bin/env python3
"""
Walk Forward Optimization (WFO) CLI Tool

This tool provides command-line interface for performing Walk Forward Optimization
analysis on trading strategies using the pyHaasAPI library.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI_v1.analysis.wfo import WFOAnalyzer, WFOConfig, WFOMode
from pyHaasAPI_v1.analysis.cache import UnifiedCacheManager

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Check for pandas availability
try:
    import pandas as pd
    _has_pandas = True
except ImportError:
    _has_pandas = False
    logger.warning("⚠️ pandas not available - WFO analysis will use basic statistics")


class WFOAnalyzerCLI:
    """CLI interface for WFO analysis"""
    
    def __init__(self):
        self.analyzer = None
        self.cache_manager = UnifiedCacheManager()
    
    def connect(self) -> bool:
        """Connect to HaasOnline API"""
        self.analyzer = WFOAnalyzer(self.cache_manager)
        return self.analyzer.connect()
    
    def analyze_lab_wfo(
        self,
        lab_id: str,
        start_date: str,
        end_date: str,
        training_days: int = 365,
        testing_days: int = 90,
        step_days: int = 30,
        mode: str = "rolling",
        min_trades: int = 10,
        min_win_rate: float = 0.4,
        min_profit_factor: float = 1.1,
        max_drawdown: float = 0.3,
        output_file: str = None,
        dry_run: bool = False
    ) -> bool:
        """Perform WFO analysis on a lab"""
        try:
            # Parse dates
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            # Create WFO configuration
            wfo_mode = WFOMode.ROLLING_WINDOW
            if mode == "fixed":
                wfo_mode = WFOMode.FIXED_WINDOW
            elif mode == "expanding":
                wfo_mode = WFOMode.EXPANDING_WINDOW
            
            config = WFOConfig(
                total_start_date=start_dt,
                total_end_date=end_dt,
                training_duration_days=training_days,
                testing_duration_days=testing_days,
                step_size_days=step_days,
                mode=wfo_mode,
                min_trades=min_trades,
                min_win_rate=min_win_rate,
                min_profit_factor=min_profit_factor,
                max_drawdown_threshold=max_drawdown
            )
            
            logger.info(f"🚀 Starting WFO analysis for lab {lab_id[:8]}")
            logger.info(f"📅 Period: {start_date} to {end_date}")
            logger.info(f"⏱️ Training: {training_days} days, Testing: {testing_days} days")
            logger.info(f"🔄 Mode: {mode}, Step: {step_days} days")
            
            if dry_run:
                logger.info("🔍 DRY RUN - Generating periods only")
                periods = self.analyzer.generate_wfo_periods(config)
                logger.info(f"📊 Would analyze {len(periods)} WFO periods")
                for i, period in enumerate(periods[:3]):  # Show first 3 periods
                    logger.info(f"   Period {i}: {period.training_start.date()} to {period.testing_end.date()}")
                if len(periods) > 3:
                    logger.info(f"   ... and {len(periods) - 3} more periods")
                return True
            
            # Perform WFO analysis
            result = self.analyzer.analyze_lab_wfo(lab_id, config)
            
            # Print summary
            self._print_wfo_summary(result)
            
            # Save report
            if output_file:
                report_path = self.analyzer.save_wfo_report(result, output_file)
                logger.info(f"📊 WFO report saved: {report_path}")
            else:
                report_path = self.analyzer.save_wfo_report(result)
                logger.info(f"�� WFO report saved: {report_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ WFO analysis failed: {e}")
            return False
    
    def _print_wfo_summary(self, result):
        """Print WFO analysis summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 WFO ANALYSIS SUMMARY")
        logger.info("="*60)
        
        logger.info(f"Lab ID: {result.lab_id[:8]}")
        logger.info(f"Total Periods: {result.total_periods}")
        logger.info(f"Successful Periods: {result.successful_periods}")
        logger.info(f"Failed Periods: {result.failed_periods}")
        logger.info(f"Success Rate: {result.successful_periods/result.total_periods*100:.1f}%")
        
        if result.summary_metrics:
            logger.info("\n📈 PERFORMANCE METRICS:")
            logger.info(f"  Average Return: {result.summary_metrics.get('avg_return', 0):.2f}%")
            logger.info(f"  Median Return: {result.summary_metrics.get('median_return', 0):.2f}%")
            logger.info(f"  Return Volatility: {result.summary_metrics.get('std_return', 0):.2f}%")
            logger.info(f"  Average Sharpe: {result.summary_metrics.get('avg_sharpe', 0):.2f}")
            logger.info(f"  Average Drawdown: {result.summary_metrics.get('avg_drawdown', 0):.2f}%")
            logger.info(f"  Max Drawdown: {result.summary_metrics.get('max_drawdown', 0):.2f}%")
            logger.info(f"  Average Stability: {result.summary_metrics.get('avg_stability', 0):.3f}")
            logger.info(f"  Consistency Ratio: {result.summary_metrics.get('consistency_ratio', 0):.1%}")
        
        if result.stability_analysis and not result.stability_analysis.get('insufficient_data'):
            logger.info("\n🔒 STABILITY ANALYSIS:")
            logger.info(f"  Return Volatility: {result.stability_analysis.get('return_volatility', 0):.2f}%")
            logger.info(f"  Return Consistency: {result.stability_analysis.get('return_consistency', 0):.3f}")
            logger.info(f"  Stability Trend: {result.stability_analysis.get('stability_trend', 'unknown')}")
            logger.info(f"  Performance Degradation: {result.stability_analysis.get('performance_degradation', 0):.1%}")
        
        # Show best and worst periods
        successful_results = [r for r in result.results if r.success]
        if successful_results:
            best_period = max(successful_results, key=lambda x: x.out_of_sample_return)
            worst_period = min(successful_results, key=lambda x: x.out_of_sample_return)
            
            logger.info("\n🏆 BEST PERFORMING PERIOD:")
            logger.info(f"  Period {best_period.period.period_id}: {best_period.out_of_sample_return:.2f}% return")
            logger.info(f"  Sharpe: {best_period.out_of_sample_sharpe:.2f}")
            logger.info(f"  Stability: {best_period.stability_score:.3f}")
            
            logger.info("\n📉 WORST PERFORMING PERIOD:")
            logger.info(f"  Period {worst_period.period.period_id}: {worst_period.out_of_sample_return:.2f}% return")
            logger.info(f"  Sharpe: {worst_period.out_of_sample_sharpe:.2f}")
            logger.info(f"  Stability: {worst_period.stability_score:.3f}")
        
        logger.info("="*60)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Walk Forward Optimization (WFO) Analyzer',
        epilog='''
Examples:
  # Basic WFO analysis
  python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31
  
  # Custom training/testing periods
  python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --training-days 180 --testing-days 60
  
  # Fixed window mode with custom step
  python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --mode fixed --step-days 45
  
  # Dry run to see what would be analyzed
  python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --dry-run
  
  # Custom output file
  python -m pyHaasAPI.cli.wfo_analyzer --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31 --output wfo_report.csv
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('--lab-id', required=True, help='Lab ID to analyze')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    
    # WFO configuration
    parser.add_argument('--training-days', type=int, default=365, help='Training period duration in days (default: 365)')
    parser.add_argument('--testing-days', type=int, default=90, help='Testing period duration in days (default: 90)')
    parser.add_argument('--step-days', type=int, default=30, help='Step size in days (default: 30)')
    parser.add_argument('--mode', choices=['rolling', 'fixed', 'expanding'], default='rolling', 
                       help='WFO mode (default: rolling)')
    
    # Performance criteria
    parser.add_argument('--min-trades', type=int, default=10, help='Minimum trades required (default: 10)')
    parser.add_argument('--min-win-rate', type=float, default=0.4, help='Minimum win rate (default: 0.4)')
    parser.add_argument('--min-profit-factor', type=float, default=1.1, help='Minimum profit factor (default: 1.1)')
    parser.add_argument('--max-drawdown', type=float, default=0.3, help='Maximum drawdown threshold (default: 0.3)')
    
    # Output options
    parser.add_argument('--output', help='Output CSV file path')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be analyzed without running')
    
    args = parser.parse_args()
    
    # Validate arguments
    try:
        start_dt = datetime.fromisoformat(args.start_date)
        end_dt = datetime.fromisoformat(args.end_date)
        if start_dt >= end_dt:
            logger.error("❌ Start date must be before end date")
            sys.exit(1)
    except ValueError as e:
        logger.error(f"❌ Invalid date format: {e}")
        sys.exit(1)
    
    # Create CLI instance
    cli = WFOAnalyzerCLI()
    
    # Connect to API
    if not cli.connect():
        logger.error("❌ Failed to connect to HaasOnline API")
        sys.exit(1)
    
    # Perform WFO analysis
    success = cli.analyze_lab_wfo(
        lab_id=args.lab_id,
        start_date=args.start_date,
        end_date=args.end_date,
        training_days=args.training_days,
        testing_days=args.testing_days,
        step_days=args.step_days,
        mode=args.mode,
        min_trades=args.min_trades,
        min_win_rate=args.min_win_rate,
        min_profit_factor=args.min_profit_factor,
        max_drawdown=args.max_drawdown,
        output_file=args.output,
        dry_run=args.dry_run
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
