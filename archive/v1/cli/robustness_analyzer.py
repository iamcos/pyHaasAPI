#!/usr/bin/env python3
"""
Strategy Robustness Analysis CLI Tool

This tool analyzes the robustness of trading strategies including:
- Max drawdown analysis for wallet protection
- Time-based performance consistency
- Risk assessment for bot creation
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyHaasAPI_v1.analysis.robustness import StrategyRobustnessAnalyzer
from pyHaasAPI_v1.analysis.analyzer import HaasAnalyzer
from pyHaasAPI_v1.analysis.cache import UnifiedCacheManager
from pyHaasAPI_v1 import api

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_lab_robustness(lab_id: str, top_count: int = 10, output_file: str = None):
    """Analyze robustness for a specific lab"""
    
    logger.info(f"Starting robustness analysis for lab {lab_id}")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    robustness_analyzer = StrategyRobustnessAnalyzer(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        logger.error("Failed to connect to HaasOnline API")
        return False
    
    try:
        # Analyze the lab
        logger.info(f"Analyzing lab {lab_id}...")
        lab_result = analyzer.analyze_lab(lab_id, top_count=top_count)
        
        if not lab_result.top_backtests:
            logger.warning(f"No backtests found for lab {lab_id}")
            return False
        
        logger.info(f"Found {len(lab_result.top_backtests)} backtests to analyze")
        
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
        logger.error(f"Error during robustness analysis: {e}")
        return False


def analyze_all_labs_robustness(top_count: int = 5, output_file: str = None):
    """Analyze robustness for all available labs"""
    
    logger.info("Starting robustness analysis for all labs")
    
    # Initialize components
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    robustness_analyzer = StrategyRobustnessAnalyzer(cache_manager)
    
    # Connect to API
    if not analyzer.connect():
        logger.error("Failed to connect to HaasOnline API")
        return False
    
    try:
        # Get all labs
        labs = api.get_all_labs(analyzer.executor)
        logger.info(f"Found {len(labs)} labs to analyze")
        
        all_robustness_results = {}
        lab_summaries = []
        
        for lab in labs:
            try:
                logger.info(f"Analyzing lab {lab.lab_id}: {lab.name}")
                
                # Analyze the lab
                lab_result = analyzer.analyze_lab(lab.lab_id, top_count=top_count)
                
                if not lab_result.top_backtests:
                    logger.warning(f"No backtests found for lab {lab.lab_id}")
                    continue
                
                # Analyze robustness
                robustness_results = robustness_analyzer.analyze_lab_robustness(lab_result)
                all_robustness_results.update(robustness_results)
                
                # Store lab summary
                scores = [metrics.robustness_score for metrics in robustness_results.values()]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                lab_summaries.append({
                    'lab_id': lab.lab_id,
                    'lab_name': lab.name,
                    'backtest_count': len(robustness_results),
                    'avg_robustness_score': avg_score,
                    'max_score': max(scores) if scores else 0,
                    'min_score': min(scores) if scores else 0
                })
                
            except Exception as e:
                logger.error(f"Error analyzing lab {lab.lab_id}: {e}")
                continue
        
        # Generate comprehensive report
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE STRATEGY ROBUSTNESS ANALYSIS")
        report.append("=" * 80)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Labs Analyzed: {len(lab_summaries)}")
        report.append(f"Total Backtests Analyzed: {len(all_robustness_results)}")
        report.append("")
        
        # Lab summary
        report.append("LAB SUMMARY:")
        report.append("-" * 40)
        for lab_summary in sorted(lab_summaries, key=lambda x: x['avg_robustness_score'], reverse=True):
            report.append(f"Lab: {lab_summary['lab_name']}")
            report.append(f"  ID: {lab_summary['lab_id']}")
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
        logger.error(f"Error during comprehensive robustness analysis: {e}")
        return False


def main(args=None):
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Strategy Robustness Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze specific lab
  python -m pyHaasAPI.cli.robustness_analyzer --lab-id lab123 --top-count 10
  
  # Analyze all labs
  python -m pyHaasAPI.cli.robustness_analyzer --all-labs --top-count 5
  
  # Save report to file
  python -m pyHaasAPI.cli.robustness_analyzer --lab-id lab123 --output robustness_report.txt
        """
    )
    
    parser.add_argument(
        '--lab-id',
        type=str,
        help='Lab ID to analyze (required if not using --all-labs)'
    )
    
    parser.add_argument(
        '--all-labs',
        action='store_true',
        help='Analyze all available labs'
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
    
    # Validate arguments
    if not args.lab_id and not args.all_labs:
        parser.error("Either --lab-id or --all-labs must be specified")
    
    if args.lab_id and args.all_labs:
        parser.error("Cannot specify both --lab-id and --all-labs")
    
    # Run analysis
    try:
        if args.all_labs:
            success = analyze_all_labs_robustness(
                top_count=args.top_count,
                output_file=args.output
            )
        else:
            success = analyze_lab_robustness(
                lab_id=args.lab_id,
                top_count=args.top_count,
                output_file=args.output
            )
        
        if success:
            logger.info("Robustness analysis completed successfully")
            sys.exit(0)
        else:
            logger.error("Robustness analysis failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()





