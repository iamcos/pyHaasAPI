#!/usr/bin/env python3
"""
Cached Strategy Robustness Analysis CLI Tool

This tool analyzes the robustness of trading strategies using cached data:
- Max drawdown analysis for wallet protection
- Time-based performance consistency
- Risk assessment for bot creation
- Works entirely with cached data (no API connection required)
"""

import argparse
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI.analysis.robustness import StrategyRobustnessAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.analysis.models import BacktestAnalysis

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_cached_lab_data(lab_id: str, cache_manager: UnifiedCacheManager) -> list:
    """Load all cached backtest data for a specific lab"""
    
    cache_dir = cache_manager.base_dir / "backtests"
    backtests = []
    
    # Find all cached files for this lab
    pattern = f"{lab_id}_*.json"
    cached_files = list(cache_dir.glob(pattern))
    
    logger.info(f"Found {len(cached_files)} cached backtests for lab {lab_id}")
    
    for file_path in cached_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract backtest ID from filename
            backtest_id = file_path.stem.split('_', 1)[1]
            
            # Create BacktestAnalysis object from cached data
            roi_percentage = data.get('roi_percentage', 0.0)
            calculated_roi_percentage = data.get('calculated_roi_percentage', roi_percentage)
            roi_difference = calculated_roi_percentage - roi_percentage
            
            backtest_analysis = BacktestAnalysis(
                backtest_id=backtest_id,
                lab_id=lab_id,
                generation_idx=data.get('generation_idx'),
                population_idx=data.get('population_idx'),
                market_tag=data.get('market_tag', 'UNKNOWN'),
                script_id=data.get('script_id', ''),
                script_name=data.get('script_name', 'Unknown Script'),
                roi_percentage=roi_percentage,
                calculated_roi_percentage=calculated_roi_percentage,
                roi_difference=roi_difference,
                win_rate=data.get('win_rate', 0.0),
                total_trades=data.get('total_trades', 0),
                max_drawdown=data.get('max_drawdown', 0.0),
                realized_profits_usdt=data.get('realized_profits_usdt', 0.0),
                pc_value=data.get('pc_value', 0.0),
                avg_profit_per_trade=data.get('avg_profit_per_trade', 0.0),
                profit_factor=data.get('profit_factor', 0.0),
                sharpe_ratio=data.get('sharpe_ratio', 0.0),
                starting_balance=data.get('starting_balance', 10000.0),
                final_balance=data.get('final_balance', 10000.0),
                peak_balance=data.get('peak_balance', 10000.0),
                analysis_timestamp=datetime.now().isoformat()
            )
            
            backtests.append(backtest_analysis)
            
        except Exception as e:
            logger.warning(f"Failed to load cached data from {file_path}: {e}")
            continue
    
    return backtests


def get_available_lab_ids(cache_manager: UnifiedCacheManager) -> list:
    """Get list of all lab IDs with cached data"""
    
    cache_dir = cache_manager.base_dir / "backtests"
    lab_ids = set()
    
    for file_path in cache_dir.glob("*.json"):
        try:
            # Extract lab ID from filename (format: labid_backtestid.json)
            lab_id = file_path.stem.split('_')[0]
            lab_ids.add(lab_id)
        except:
            continue
    
    return sorted(list(lab_ids))


def analyze_cached_lab_robustness(lab_id: str, top_count: int = 10, output_file: str = None):
    """Analyze robustness for a specific lab using cached data"""
    
    logger.info(f"Starting cached robustness analysis for lab {lab_id}")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    robustness_analyzer = StrategyRobustnessAnalyzer(cache_manager)
    
    try:
        # Load cached backtest data
        backtests = load_cached_lab_data(lab_id, cache_manager)
        
        if not backtests:
            logger.warning(f"No cached backtests found for lab {lab_id}")
            return False
        
        # Sort by ROI and take top performers
        backtests.sort(key=lambda x: x.roi_percentage, reverse=True)
        top_backtests = backtests[:top_count]
        
        logger.info(f"Analyzing top {len(top_backtests)} backtests from {len(backtests)} total")
        
        # Create a mock lab result object
        class MockLabResult:
            def __init__(self, top_backtests):
                self.top_backtests = top_backtests
        
        lab_result = MockLabResult(top_backtests)
        
        # Analyze robustness for each backtest
        logger.info("Analyzing strategy robustness...")
        robustness_results = robustness_analyzer.analyze_lab_robustness(lab_result)
        
        # Generate report
        report = robustness_analyzer.generate_robustness_report(robustness_results)
        
        # Output results
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            logger.info(f"Robustness report saved to {output_file}")
        else:
            print(report)
        
        # Summary statistics
        scores = [metrics.robustness_score for metrics in robustness_results.values()]
        risk_levels = [metrics.risk_level for metrics in robustness_results.values()]
        
        logger.info(f"Analysis complete!")
        logger.info(f"Average robustness score: {sum(scores) / len(scores):.1f}/100")
        logger.info(f"Risk distribution: {dict(zip(*zip(*[(level, risk_levels.count(level)) for level in set(risk_levels)])))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during cached robustness analysis: {e}")
        return False


def analyze_all_cached_labs_robustness(top_count: int = 5, output_file: str = None):
    """Analyze robustness for all labs with cached data"""
    
    logger.info("Starting cached robustness analysis for all labs")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    robustness_analyzer = StrategyRobustnessAnalyzer(cache_manager)
    
    try:
        # Get all available lab IDs
        lab_ids = get_available_lab_ids(cache_manager)
        logger.info(f"Found {len(lab_ids)} labs with cached data")
        
        all_robustness_results = {}
        lab_summaries = []
        
        for lab_id in lab_ids:
            try:
                logger.info(f"Analyzing lab {lab_id}")
                
                # Load cached backtest data
                backtests = load_cached_lab_data(lab_id, cache_manager)
                
                if not backtests:
                    logger.warning(f"No cached backtests found for lab {lab_id}")
                    continue
                
                # Sort by ROI and take top performers
                backtests.sort(key=lambda x: x.roi_percentage, reverse=True)
                top_backtests = backtests[:top_count]
                
                # Create a mock lab result object
                class MockLabResult:
                    def __init__(self, top_backtests):
                        self.top_backtests = top_backtests
                
                lab_result = MockLabResult(top_backtests)
                
                # Analyze robustness
                robustness_results = robustness_analyzer.analyze_lab_robustness(lab_result)
                all_robustness_results.update(robustness_results)
                
                # Store lab summary
                scores = [metrics.robustness_score for metrics in robustness_results.values()]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                lab_summaries.append({
                    'lab_id': lab_id,
                    'backtest_count': len(robustness_results),
                    'avg_robustness_score': avg_score,
                    'max_score': max(scores) if scores else 0,
                    'min_score': min(scores) if scores else 0
                })
                
            except Exception as e:
                logger.error(f"Error analyzing lab {lab_id}: {e}")
                continue
        
        # Generate comprehensive report
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE CACHED STRATEGY ROBUSTNESS ANALYSIS")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Labs Analyzed: {len(lab_summaries)}")
        report.append(f"Total Backtests Analyzed: {len(all_robustness_results)}")
        report.append("")
        
        # Lab summary
        report.append("LAB SUMMARY:")
        report.append("-" * 40)
        for lab_summary in sorted(lab_summaries, key=lambda x: x['avg_robustness_score'], reverse=True):
            report.append(f"Lab ID: {lab_summary['lab_id']}")
            report.append(f"  Backtests: {lab_summary['backtest_count']}")
            report.append(f"  Avg Robustness: {lab_summary['avg_robustness_score']:.1f}/100")
            report.append(f"  Score Range: {lab_summary['min_score']:.1f} - {lab_summary['max_score']:.1f}")
            report.append("")
        
        # Overall statistics
        all_scores = [metrics.robustness_score for metrics in all_robustness_results.values()]
        all_risk_levels = [metrics.risk_level for metrics in all_robustness_results.values()]
        
        report.append("OVERALL STATISTICS:")
        report.append("-" * 40)
        report.append(f"Average Robustness Score: {sum(all_scores) / len(all_scores):.1f}/100")
        report.append(f"Highest Robustness Score: {max(all_scores):.1f}/100")
        report.append(f"Lowest Robustness Score: {min(all_scores):.1f}/100")
        report.append("")
        
        # Risk level distribution
        risk_distribution = {}
        for risk_level in all_risk_levels:
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        report.append("RISK LEVEL DISTRIBUTION:")
        report.append("-" * 40)
        for risk_level, count in risk_distribution.items():
            percentage = (count / len(all_risk_levels)) * 100
            report.append(f"{risk_level}: {count} backtests ({percentage:.1f}%)")
        report.append("")
        
        # Top performing strategies
        sorted_results = sorted(all_robustness_results.items(), 
                              key=lambda x: x[1].robustness_score, reverse=True)
        
        report.append("TOP 10 MOST ROBUST STRATEGIES:")
        report.append("-" * 40)
        for i, (backtest_id, metrics) in enumerate(sorted_results[:10]):
            report.append(f"{i+1}. Backtest {backtest_id}")
            report.append(f"   Lab ROI: {metrics.overall_roi:.1f}% | Calculated ROI: {metrics.calculated_roi:.1f}%")
            report.append(f"   Win Rate: {metrics.win_rate:.1%} | Max Drawdown: {metrics.drawdown_analysis.max_drawdown_percentage:.1f}%")
            report.append(f"   Balance: Starting={metrics.starting_balance:.0f} USDT | Max DD={metrics.drawdown_analysis.lowest_balance:.0f} USDT | Final={metrics.final_balance:.0f} USDT")
            report.append(f"   Robustness Score: {metrics.robustness_score:.1f}/100")
            report.append(f"   Risk Level: {metrics.risk_level}")
            report.append(f"   Recommendation: {metrics.recommendation}")
            report.append("")
        
        # Output results
        full_report = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(full_report)
            logger.info(f"Comprehensive robustness report saved to {output_file}")
        else:
            print(full_report)
        
        logger.info(f"Comprehensive analysis complete!")
        logger.info(f"Analyzed {len(lab_summaries)} labs with {len(all_robustness_results)} backtests")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during comprehensive cached robustness analysis: {e}")
        return False


def main(args=None):
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Cached Strategy Robustness Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze specific lab using cached data
  python -m pyHaasAPI.cli.cached_robustness_analyzer --lab-id 058c6c5a-549a-4828-9169-a79b0a317229 --top-count 10
  
  # Analyze all labs with cached data
  python -m pyHaasAPI.cli.cached_robustness_analyzer --all-labs --top-count 5
  
  # Save report to file
  python -m pyHaasAPI.cli.cached_robustness_analyzer --lab-id 058c6c5a-549a-4828-9169-a79b0a317229 --output robustness_report.txt
  
  # List available labs
  python -m pyHaasAPI.cli.cached_robustness_analyzer --list-labs
        """
    )
    
    parser.add_argument(
        '--lab-id',
        type=str,
        help='Lab ID to analyze (required if not using --all-labs or --list-labs)'
    )
    
    parser.add_argument(
        '--all-labs',
        action='store_true',
        help='Analyze all available labs with cached data'
    )
    
    parser.add_argument(
        '--list-labs',
        action='store_true',
        help='List all available lab IDs with cached data'
    )
    
    parser.add_argument(
        '--top-count',
        type=int,
        default=10,
        help='Number of top backtests to analyze per lab (default: 10)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for the report (default: print to console)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args(args)
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle list labs command
    if args.list_labs:
        cache_manager = UnifiedCacheManager()
        lab_ids = get_available_lab_ids(cache_manager)
        print(f"Available labs with cached data ({len(lab_ids)}):")
        for lab_id in lab_ids:
            print(f"  {lab_id}")
        return
    
    # Validate arguments
    if not args.lab_id and not args.all_labs:
        parser.error("Either --lab-id, --all-labs, or --list-labs must be specified")
    
    if args.lab_id and args.all_labs:
        parser.error("Cannot specify both --lab-id and --all-labs")
    
    # Run analysis
    try:
        if args.all_labs:
            success = analyze_all_cached_labs_robustness(
                top_count=args.top_count,
                output_file=args.output
            )
        else:
            success = analyze_cached_lab_robustness(
                lab_id=args.lab_id,
                top_count=args.top_count,
                output_file=args.output
            )
        
        if success:
            logger.info("Cached robustness analysis completed successfully")
            sys.exit(0)
        else:
            logger.error("Cached robustness analysis failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
