#!/usr/bin/env python3
"""
Walk Forward Optimization (WFO) Example

This example demonstrates how to use the WFO functionality in pyHaasAPI
to perform comprehensive Walk Forward Optimization analysis on trading strategies.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyHaasAPI_v1.analysis.wfo import WFOAnalyzer, WFOConfig, WFOMode
from pyHaasAPI_v1.analysis.cache import UnifiedCacheManager


def example_basic_wfo():
    """Basic WFO analysis example"""
    print("🚀 Basic WFO Analysis Example")
    print("="*50)
    
    # Create cache manager and analyzer
    cache_manager = UnifiedCacheManager()
    analyzer = WFOAnalyzer(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        print("❌ Failed to connect to HaasOnline API")
        return False
    
    # Define WFO configuration
    config = WFOConfig(
        total_start_date=datetime(2022, 1, 1),
        total_end_date=datetime(2023, 12, 31),
        training_duration_days=365,  # 1 year training
        testing_duration_days=90,    # 3 months testing
        step_size_days=30,           # 1 month step
        mode=WFOMode.ROLLING_WINDOW,
        min_trades=10,
        min_win_rate=0.4,
        min_profit_factor=1.1,
        max_drawdown_threshold=0.3
    )
    
    # Example lab ID (replace with actual lab ID)
    lab_id = "e4616b35-8065-4095-966b-546de68fd493"
    
    try:
        # Perform WFO analysis
        print(f"🔍 Analyzing lab {lab_id[:8]} with WFO...")
        result = analyzer.analyze_lab_wfo(lab_id, config)
        
        # Print results
        print_wfo_results(result)
        
        # Save report
        report_path = analyzer.save_wfo_report(result)
        print(f"📊 Report saved: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ WFO analysis failed: {e}")
        return False


def example_custom_wfo():
    """Custom WFO configuration example"""
    print("\n🔧 Custom WFO Configuration Example")
    print("="*50)
    
    # Create analyzer
    cache_manager = UnifiedCacheManager()
    analyzer = WFOAnalyzer(cache_manager)
    
    if not analyzer.connect():
        print("❌ Failed to connect to HaasOnline API")
        return False
    
    # Custom configuration for shorter periods
    config = WFOConfig(
        total_start_date=datetime(2023, 1, 1),
        total_end_date=datetime(2023, 12, 31),
        training_duration_days=180,  # 6 months training
        testing_duration_days=60,    # 2 months testing
        step_size_days=15,           # 2 weeks step
        mode=WFOMode.EXPANDING_WINDOW,
        min_trades=5,
        min_win_rate=0.35,
        min_profit_factor=1.05,
        max_drawdown_threshold=0.25
    )
    
    lab_id = "e4616b35-8065-4095-966b-546de68fd493"
    
    try:
        print(f"🔍 Analyzing lab {lab_id[:8]} with custom WFO settings...")
        result = analyzer.analyze_lab_wfo(lab_id, config)
        
        print_wfo_results(result)
        return True
        
    except Exception as e:
        print(f"❌ Custom WFO analysis failed: {e}")
        return False


def example_wfo_periods():
    """Example showing how to generate WFO periods"""
    print("\n📅 WFO Periods Generation Example")
    print("="*50)
    
    # Create analyzer
    analyzer = WFOAnalyzer()
    
    # Define configuration
    config = WFOConfig(
        total_start_date=datetime(2022, 1, 1),
        total_end_date=datetime(2023, 12, 31),
        training_duration_days=365,
        testing_duration_days=90,
        step_size_days=30,
        mode=WFOMode.ROLLING_WINDOW
    )
    
    # Generate periods
    periods = analyzer.generate_wfo_periods(config)
    
    print(f"📊 Generated {len(periods)} WFO periods:")
    for i, period in enumerate(periods[:5]):  # Show first 5 periods
        print(f"  Period {i}:")
        print(f"    Training: {period.training_start.date()} to {period.training_end.date()}")
        print(f"    Testing:  {period.testing_start.date()} to {period.testing_end.date()}")
    
    if len(periods) > 5:
        print(f"  ... and {len(periods) - 5} more periods")
    
    return True


def print_wfo_results(result):
    """Print WFO analysis results in a formatted way"""
    print(f"\n📊 WFO ANALYSIS RESULTS")
    print("="*60)
    print(f"Lab ID: {result.lab_id[:8]}")
    print(f"Total Periods: {result.total_periods}")
    print(f"Successful Periods: {result.successful_periods}")
    print(f"Failed Periods: {result.failed_periods}")
    print(f"Success Rate: {result.successful_periods/result.total_periods*100:.1f}%")
    
    if result.summary_metrics:
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"  Average Return: {result.summary_metrics.get('avg_return', 0):.2f}%")
        print(f"  Median Return: {result.summary_metrics.get('median_return', 0):.2f}%")
        print(f"  Return Volatility: {result.summary_metrics.get('std_return', 0):.2f}%")
        print(f"  Average Sharpe: {result.summary_metrics.get('avg_sharpe', 0):.2f}")
        print(f"  Average Drawdown: {result.summary_metrics.get('avg_drawdown', 0):.2f}%")
        print(f"  Max Drawdown: {result.summary_metrics.get('max_drawdown', 0):.2f}%")
        print(f"  Average Stability: {result.summary_metrics.get('avg_stability', 0):.3f}")
        print(f"  Consistency Ratio: {result.summary_metrics.get('consistency_ratio', 0):.1%}")
    
    if result.stability_analysis and not result.stability_analysis.get('insufficient_data'):
        print(f"\n🔒 STABILITY ANALYSIS:")
        print(f"  Return Volatility: {result.stability_analysis.get('return_volatility', 0):.2f}%")
        print(f"  Return Consistency: {result.stability_analysis.get('return_consistency', 0):.3f}")
        print(f"  Stability Trend: {result.stability_analysis.get('stability_trend', 'unknown')}")
        print(f"  Performance Degradation: {result.stability_analysis.get('performance_degradation', 0):.1%}")
    
    # Show best and worst periods
    successful_results = [r for r in result.results if r.success]
    if successful_results:
        best_period = max(successful_results, key=lambda x: x.out_of_sample_return)
        worst_period = min(successful_results, key=lambda x: x.out_of_sample_return)
        
        print(f"\n🏆 BEST PERFORMING PERIOD:")
        print(f"  Period {best_period.period.period_id}: {best_period.out_of_sample_return:.2f}% return")
        print(f"  Sharpe: {best_period.out_of_sample_sharpe:.2f}")
        print(f"  Stability: {best_period.stability_score:.3f}")
        
        print(f"\n📉 WORST PERFORMING PERIOD:")
        print(f"  Period {worst_period.period.period_id}: {worst_period.out_of_sample_return:.2f}% return")
        print(f"  Sharpe: {worst_period.out_of_sample_sharpe:.2f}")
        print(f"  Stability: {worst_period.stability_score:.3f}")


def main():
    """Main example function"""
    print("🎯 pyHaasAPI Walk Forward Optimization Examples")
    print("="*60)
    
    # Run examples
    examples = [
        ("Basic WFO Analysis", example_basic_wfo),
        ("Custom WFO Configuration", example_custom_wfo),
        ("WFO Periods Generation", example_wfo_periods),
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            success = example_func()
            if success:
                print(f"✅ {name} completed successfully")
            else:
                print(f"❌ {name} failed")
        except Exception as e:
            print(f"❌ {name} failed with error: {e}")
    
    print(f"\n{'='*60}")
    print("🎉 WFO Examples completed!")


if __name__ == '__main__':
    main()
