#!/usr/bin/env python3
"""
Main CLI entry point for pyHaasAPI

This provides a unified command-line interface for all pyHaasAPI operations.
"""

import sys
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import pyHaasAPI
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI import HaasAnalyzer, UnifiedCacheManager
from pyHaasAPI.cli.simple_cli import main as simple_cli_main


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="pyHaasAPI Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete analysis workflow
  python -m pyHaasAPI.cli cache-labs
  python -m pyHaasAPI.cli interactive-analyze
  python -m pyHaasAPI.cli visualize --all-labs
  python -m pyHaasAPI.cli create-bots-from-analysis --top-count 5 --activate
  
  # Quick analysis and bot creation
  python -m pyHaasAPI.cli analyze-cache --save-results
  python -m pyHaasAPI.cli create-bots-from-analysis --top-count 5 --activate
  
  # Traditional workflow
  python -m pyHaasAPI.cli analyze lab-id --create-count 3 --activate
  python -m pyHaasAPI.cli list-labs
  python -m pyHaasAPI.cli complete-workflow lab-id --create-count 2 --verify
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze lab and create bots')
    analyze_parser.add_argument('lab_id', help='Lab ID to analyze')
    analyze_parser.add_argument('--create-count', type=int, help='Number of bots to create')
    analyze_parser.add_argument('--activate', action='store_true', help='Activate bots after creation')
    analyze_parser.add_argument('--verify', action='store_true', help='Verify bot configuration')
    
    # List labs command
    list_parser = subparsers.add_parser('list-labs', help='List all available labs')
    
    # Complete workflow command
    workflow_parser = subparsers.add_parser('complete-workflow', help='Run complete bot management workflow')
    workflow_parser.add_argument('lab_id', help='Lab ID to process')
    workflow_parser.add_argument('--create-count', type=int, default=3, help='Number of bots to create')
    workflow_parser.add_argument('--activate', action='store_true', help='Activate bots after creation')
    workflow_parser.add_argument('--verify', action='store_true', help='Verify bot configuration')
    
    # Robustness analysis command
    robustness_parser = subparsers.add_parser('robustness', help='Analyze strategy robustness with balance reporting')
    robustness_parser.add_argument('--lab-id', type=str, help='Lab ID to analyze (required if not using --all-labs)')
    robustness_parser.add_argument('--all-labs', action='store_true', help='Analyze all available labs')
    robustness_parser.add_argument('--top-count', type=int, default=10, help='Number of top backtests to analyze per lab (default: 10)')
    robustness_parser.add_argument('--output', type=str, help='Output file for the report (default: print to console)')
    robustness_parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    # Cache labs command
    cache_parser = subparsers.add_parser('cache-labs', help='Cache all lab data for analysis without creating bots')
    cache_parser.add_argument('--lab-ids', nargs='+', type=str, help='Cache only specific lab IDs')
    cache_parser.add_argument('--exclude-lab-ids', nargs='+', type=str, help='Cache all complete labs except these IDs')
    cache_parser.add_argument('--analyze-count', type=int, default=100, help='Number of backtests to analyze per lab (default: 100)')
    cache_parser.add_argument('--refresh', action='store_true', help='Refresh existing cache data')
    
    # Analyze from cache command
    analyze_parser = subparsers.add_parser('analyze-cache', help='Analyze cached lab data with detailed results')
    analyze_parser.add_argument('--lab-ids', nargs='+', type=str, help='Analyze only specific lab IDs')
    analyze_parser.add_argument('--top-count', type=int, default=10, help='Number of top backtests to show (default: 10)')
    analyze_parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate', 'profit', 'trades'], default='roe', help='Sort backtests by metric (default: roe)')
    analyze_parser.add_argument('--save-results', action='store_true', help='Save analysis results for later bot creation')
    analyze_parser.add_argument('--generate-lab-reports', action='store_true', help='Generate lab analysis reports with qualifying bots')
    analyze_parser.add_argument('--concise-format', action='store_true', help='Use concise format for lab reports (Strategy, Trading Pair, ROE, WR, Trades, Bots)')
    analyze_parser.add_argument('--comprehensive-summary', action='store_true', help='Generate comprehensive lab summary with all cached labs and real lab names')
    analyze_parser.add_argument('--show-data-distribution', action='store_true', help='Show data distribution analysis to help understand your data')
    analyze_parser.add_argument('--min-roe', type=float, default=0, help='Minimum ROE for qualifying bots (default: 0)')
    analyze_parser.add_argument('--max-roe', type=float, help='Maximum ROE for qualifying bots (no default limit)')
    analyze_parser.add_argument('--min-winrate', type=float, default=30, help='Minimum win rate for qualifying bots (default: 30)')
    analyze_parser.add_argument('--max-winrate', type=float, help='Maximum win rate for qualifying bots (no default limit)')
    analyze_parser.add_argument('--min-trades', type=int, default=5, help='Minimum trades for qualifying bots (default: 5)')
    analyze_parser.add_argument('--max-trades', type=int, help='Maximum trades for qualifying bots (no default limit)')
    analyze_parser.add_argument('--output-format', choices=['json', 'csv', 'markdown'], default='json', help='Output format for lab analysis reports (default: json)')
    
    # Create bots from analysis command
    create_bots_parser = subparsers.add_parser('create-bots-from-analysis', help='Create bots from saved analysis results')
    create_bots_parser.add_argument('--lab-id', type=str, help='Create bots from specific lab analysis result')
    create_bots_parser.add_argument('--top-count', type=int, default=10, help='Number of top backtests to create bots for (default: 10)')
    create_bots_parser.add_argument('--activate', action='store_true', help='Activate created bots for live trading')
    create_bots_parser.add_argument('--target-amount', type=float, default=2000.0, help='Target USDT amount for trade amounts (default: 2000.0)')
    create_bots_parser.add_argument('--validate-backtest', action='store_true', help='Validate backtests before bot creation')
    create_bots_parser.add_argument('--validate-lab', action='store_true', default=True, help='Validate that lab exists on server')
    
    # Interactive analysis command
    interactive_parser = subparsers.add_parser('interactive-analyze', help='Interactive analysis and decision-making for cached data')
    interactive_parser.add_argument('--lab-ids', nargs='+', type=str, help='Analyze only specific lab IDs')
    interactive_parser.add_argument('--top-count', type=int, default=50, help='Number of top backtests to show (default: 50)')
    interactive_parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate', 'profit', 'trades', 'risk', 'stability'], default='roe', help='Sort backtests by metric (default: roe)')
    
    # Visualization command
    viz_parser = subparsers.add_parser('visualize', help='Generate charts and graphs for backtest analysis')
    viz_parser.add_argument('--lab-ids', nargs='+', type=str, help='Generate charts for specific lab IDs')
    viz_parser.add_argument('--backtest-ids', nargs='+', type=str, help='Generate charts for specific backtest IDs')
    viz_parser.add_argument('--all-labs', action='store_true', help='Generate charts for all cached labs')
    viz_parser.add_argument('--output-dir', type=str, help='Output directory for charts (default: cache/charts)')
    viz_parser.add_argument('--top-count', type=int, default=10, help='Number of top backtests to analyze per lab (default: 10)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'analyze':
            simple_cli_main(['analyze', args.lab_id] + 
                          (['--create-count', str(args.create_count)] if args.create_count else []) +
                          (['--activate'] if args.activate else []) +
                          (['--verify'] if args.verify else []))
        elif args.command == 'list-labs':
            simple_cli_main(['list-labs'])
        elif args.command == 'complete-workflow':
            # Import and run the complete workflow
            from pyHaasAPI.examples.complete_bot_management_example import main as workflow_main
            workflow_args = [args.lab_id]
            if args.create_count:
                workflow_args.extend(['--create-count', str(args.create_count)])
            if args.activate:
                workflow_args.append('--activate')
            if args.verify:
                workflow_args.append('--verify')
            workflow_main(workflow_args)
        elif args.command == 'robustness':
            # Import and run the robustness analysis
            from pyHaasAPI.cli.robustness_analyzer import main as robustness_main
            robustness_args = []
            if args.lab_id:
                robustness_args.extend(['--lab-id', args.lab_id])
            if args.all_labs:
                robustness_args.append('--all-labs')
            if args.top_count:
                robustness_args.extend(['--top-count', str(args.top_count)])
            if args.output:
                robustness_args.extend(['--output', args.output])
            if args.verbose:
                robustness_args.append('--verbose')
            robustness_main(robustness_args)
        elif args.command == 'cache-labs':
            # Import and run the cache labs tool
            from pyHaasAPI.cli.cache_labs import main as cache_labs_main
            cache_args = []
            if args.lab_ids:
                cache_args.extend(['--lab-ids'] + args.lab_ids)
            if args.exclude_lab_ids:
                cache_args.extend(['--exclude-lab-ids'] + args.exclude_lab_ids)
            if args.analyze_count:
                cache_args.extend(['--analyze-count', str(args.analyze_count)])
            if args.refresh:
                cache_args.append('--refresh')
            cache_labs_main(cache_args)
        elif args.command == 'analyze-cache':
            # Import and run the analyze from cache tool
            from pyHaasAPI.cli.analyze_from_cache import main as analyze_cache_main
            analyze_args = []
            if args.lab_ids:
                analyze_args.extend(['--lab-ids'] + args.lab_ids)
            if args.top_count:
                analyze_args.extend(['--top-count', str(args.top_count)])
            if args.sort_by:
                analyze_args.extend(['--sort-by', args.sort_by])
            if args.save_results:
                analyze_args.append('--save-results')
            if hasattr(args, 'generate_lab_reports') and args.generate_lab_reports:
                analyze_args.append('--generate-lab-reports')
            if hasattr(args, 'concise_format') and args.concise_format:
                analyze_args.append('--concise-format')
            if hasattr(args, 'comprehensive_summary') and args.comprehensive_summary:
                analyze_args.append('--comprehensive-summary')
            if hasattr(args, 'min_roe'):
                analyze_args.extend(['--min-roe', str(args.min_roe)])
            if hasattr(args, 'max_roe') and args.max_roe is not None:
                analyze_args.extend(['--max-roe', str(args.max_roe)])
            if hasattr(args, 'min_winrate'):
                analyze_args.extend(['--min-winrate', str(args.min_winrate)])
            if hasattr(args, 'max_winrate') and args.max_winrate is not None:
                analyze_args.extend(['--max-winrate', str(args.max_winrate)])
            if hasattr(args, 'min_trades'):
                analyze_args.extend(['--min-trades', str(args.min_trades)])
            if hasattr(args, 'max_trades') and args.max_trades is not None:
                analyze_args.extend(['--max-trades', str(args.max_trades)])
            if hasattr(args, 'output_format'):
                analyze_args.extend(['--output-format', args.output_format])
            analyze_cache_main(analyze_args)
        elif args.command == 'create-bots-from-analysis':
            # Import and run the create bots from analysis tool
            from pyHaasAPI.cli.create_bots_from_analysis import main as create_bots_main
            create_args = []
            if args.lab_id:
                create_args.extend(['--lab-id', args.lab_id])
            if args.top_count:
                create_args.extend(['--top-count', str(args.top_count)])
            if args.activate:
                create_args.append('--activate')
            if args.target_amount:
                create_args.extend(['--target-amount', str(args.target_amount)])
            if args.validate_backtest:
                create_args.append('--validate-backtest')
            if args.validate_lab:
                create_args.append('--validate-lab')
            create_bots_main(create_args)
        elif args.command == 'interactive-analyze':
            # Import and run the interactive analyzer
            from pyHaasAPI.cli.interactive_analyzer import main as interactive_main
            interactive_args = []
            if args.lab_ids:
                interactive_args.extend(['--lab-ids'] + args.lab_ids)
            if args.top_count:
                interactive_args.extend(['--top-count', str(args.top_count)])
            if args.sort_by:
                interactive_args.extend(['--sort-by', args.sort_by])
            interactive_main(interactive_args)
        elif args.command == 'visualize':
            # Import and run the visualization tool
            from pyHaasAPI.cli.visualization_tool import main as viz_main
            viz_args = []
            if args.lab_ids:
                viz_args.extend(['--lab-ids'] + args.lab_ids)
            if args.backtest_ids:
                viz_args.extend(['--backtest-ids'] + args.backtest_ids)
            if args.all_labs:
                viz_args.append('--all-labs')
            if args.output_dir:
                viz_args.extend(['--output-dir', args.output_dir])
            if args.top_count:
                viz_args.extend(['--top-count', str(args.top_count)])
            viz_main(viz_args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
