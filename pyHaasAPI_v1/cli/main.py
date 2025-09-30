#!/usr/bin/env python3
"""
Enhanced Main CLI entry point for pyHaasAPI

This provides a unified command-line interface for all pyHaasAPI operations.
Now uses the refactored unified tools for better organization and consistency.
"""

import sys
import argparse
from pathlib import Path

# Add the parent directory to the path so we can import pyHaasAPI_v1
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pyHaasAPI_v1 import HaasAnalyzer, UnifiedCacheManager


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="pyHaasAPI Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # NEW UNIFIED INTERFACES (RECOMMENDED):
  # Analysis operations
  python -m pyHaasAPI.cli analysis cache --show-data-distribution --generate-lab-reports
  python -m pyHaasAPI.cli analysis interactive
  python -m pyHaasAPI.cli analysis cache-labs
  python -m pyHaasAPI.cli analysis wfo --lab-id lab123 --start-date 2022-01-01 --end-date 2023-12-31
  
  # Bot management operations
  python -m pyHaasAPI.cli bot create --top-count 5 --activate
  python -m pyHaasAPI.cli bot fix-amounts --method usdt --target-amount 2000
  python -m pyHaasAPI.cli bot cleanup-accounts
  python -m pyHaasAPI.cli bot activate --bot-ids bot1,bot2
  python -m pyHaasAPI.cli bot deactivate --exclude-bot-ids bot3,bot4
  
  # REFACTORED TOOLS (ALSO AVAILABLE):
  python -m pyHaasAPI.cli analyze_from_cache_refactored --generate-lab-reports
  python -m pyHaasAPI.cli mass_bot_creator_refactored --top-count 5 --activate
  python -m pyHaasAPI.cli fix_bot_trade_amounts_refactored --method usdt --target-amount 2000
  python -m pyHaasAPI.cli account_cleanup_refactored
  python -m pyHaasAPI.cli price_tracker_refactored BTC_USDT_PERPETUAL
  
  # LEGACY TOOLS (STILL WORKING):
  python -m pyHaasAPI.cli analyze lab-id --create-count 3 --activate
  python -m pyHaasAPI.cli list-labs
  python -m pyHaasAPI.cli complete-workflow lab-id --create-count 2 --verify
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # NEW UNIFIED COMMANDS (RECOMMENDED)
    # Analysis operations - these will be handled by the unified CLI directly
    subparsers.add_parser('analysis', help='Unified analysis operations (cache, interactive, cache-labs, wfo)')
    
    # Bot management operations - these will be handled by the unified CLI directly  
    subparsers.add_parser('bot', help='Unified bot management operations (create, fix-amounts, cleanup-accounts, activate, deactivate)')
    
    # REFACTORED TOOLS (ALSO AVAILABLE)
    subparsers.add_parser('analyze_from_cache_refactored', help='Refactored cache analysis tool')
    subparsers.add_parser('mass_bot_creator_refactored', help='Refactored mass bot creator')
    subparsers.add_parser('fix_bot_trade_amounts_refactored', help='Refactored bot trade amount fixer')
    subparsers.add_parser('account_cleanup_refactored', help='Refactored account cleanup tool')
    subparsers.add_parser('price_tracker_refactored', help='Refactored price tracker')
    
    # LEGACY COMMANDS (STILL WORKING)
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
    
    # Cache cleanup command
    cleanup_parser = subparsers.add_parser('cache-cleanup', help='Clean up obsolete lab cache files')
    cleanup_parser.add_argument('--dry-run', action='store_true', default=True,
                               help='Show what would be removed without actually removing (default: True)')
    cleanup_parser.add_argument('--force', action='store_true',
                               help='Actually remove obsolete cache files (overrides --dry-run)')
    
    # Analyze from cache command
    analyze_parser = subparsers.add_parser('analyze-cache', help='Analyze cached lab data with detailed results')
    analyze_parser.add_argument('--lab-ids', nargs='+', type=str, help='Analyze only specific lab IDs')
    analyze_parser.add_argument('--top-count', type=int, default=10, help='Number of top backtests to show (default: 10)')
    analyze_parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate', 'profit', 'trades'], default='roe', help='Sort backtests by metric (default: roe)')
    analyze_parser.add_argument('--save-results', action='store_true', help='Save analysis results for later bot creation')
    analyze_parser.add_argument('--generate-lab-reports', action='store_true', help='Generate lab analysis reports with qualifying bots')
    analyze_parser.add_argument('--concise-format', action='store_true', help='Use concise format for lab reports (Strategy, Trading Pair, ROE, WR, Trades, Bots)')
    analyze_parser.add_argument('--comprehensive-summary', action='store_true', help='Generate comprehensive lab summary with all cached labs and real lab names')
    analyze_parser.add_argument('--strategy-grouped-reports', action='store_true', help='Print report grouped by strategy with lab IDs and stats')
    analyze_parser.add_argument('--detailed-lab-reports', action='store_true', help='Print detailed per-lab reports incl. names, stats, ROI ranges, and top bots with UIDs')
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
        # NEW UNIFIED COMMANDS (RECOMMENDED)
        if args.command == 'analysis':
            # Route to unified analysis CLI
            from pyHaasAPI_v1.cli.analysis_cli import main as analysis_cli_main
            # Modify sys.argv to remove the main command and pass to the tool
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'analysis'
            try:
                return analysis_cli_main()
            finally:
                sys.argv = original_argv
        elif args.command == 'bot':
            # Route to unified bot management CLI
            from pyHaasAPI_v1.cli.bot_management_cli import main as bot_mgmt_cli_main
            # Modify sys.argv to remove the main command and pass to the tool
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'bot'
            try:
                return bot_mgmt_cli_main()
            finally:
                sys.argv = original_argv
        
        # REFACTORED TOOLS (ALSO AVAILABLE)
        elif args.command == 'analyze_from_cache_refactored':
            from pyHaasAPI_v1.cli.analyze_from_cache_refactored import main as analyze_cache_refactored_main
            # Modify sys.argv to remove the main command and pass to the tool
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'analyze_from_cache_refactored'
            try:
                return analyze_cache_refactored_main()
            finally:
                sys.argv = original_argv
        elif args.command == 'mass_bot_creator_refactored':
            from pyHaasAPI_v1.cli.mass_bot_creator_refactored import main as mass_bot_creator_refactored_main
            # Modify sys.argv to remove the main command and pass to the tool
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'mass_bot_creator_refactored'
            try:
                return mass_bot_creator_refactored_main()
            finally:
                sys.argv = original_argv
        elif args.command == 'fix_bot_trade_amounts_refactored':
            from pyHaasAPI_v1.cli.fix_bot_trade_amounts_refactored import main as fix_bot_trade_amounts_refactored_main
            # Modify sys.argv to remove the main command and pass to the tool
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'fix_bot_trade_amounts_refactored'
            try:
                return fix_bot_trade_amounts_refactored_main()
            finally:
                sys.argv = original_argv
        elif args.command == 'account_cleanup_refactored':
            from pyHaasAPI_v1.cli.account_cleanup_refactored import main as account_cleanup_refactored_main
            # Modify sys.argv to remove the main command and pass to the tool
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'account_cleanup_refactored'
            try:
                return account_cleanup_refactored_main()
            finally:
                sys.argv = original_argv
        elif args.command == 'price_tracker_refactored':
            from pyHaasAPI_v1.cli.price_tracker_refactored import main as price_tracker_refactored_main
            # Modify sys.argv to remove the main command and pass to the tool
            original_argv = sys.argv[:]
            sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'price_tracker_refactored'
            try:
                return price_tracker_refactored_main()
            finally:
                sys.argv = original_argv
        
        # LEGACY COMMANDS (STILL WORKING)
        elif args.command == 'analyze':
            simple_cli_main(['analyze', args.lab_id] + 
                          (['--create-count', str(args.create_count)] if args.create_count else []) +
                          (['--activate'] if args.activate else []) +
                          (['--verify'] if args.verify else []))
        elif args.command == 'list-labs':
            simple_cli_main(['list-labs'])
        elif args.command == 'complete-workflow':
            # Import and run the complete workflow
            from pyHaasAPI_v1.examples.complete_bot_management_example import main as workflow_main
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
            from pyHaasAPI_v1.cli.robustness_analyzer import main as robustness_main
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
            from pyHaasAPI_v1.cli.cache_labs import main as cache_labs_main
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
        elif args.command == 'cache-cleanup':
            # Import and run the cache cleanup tool
            from pyHaasAPI_v1.cli.cache_labs import main as cache_cleanup_main
            cleanup_args = []
            if args.force:
                cleanup_args.append('--force')
            elif args.dry_run:
                cleanup_args.append('--dry-run')
            cache_cleanup_main(cleanup_args)
        elif args.command == 'analyze-cache':
            # Import and run the analyze from cache tool
            from pyHaasAPI_v1.cli.analyze_from_cache import main as analyze_cache_main
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
            if hasattr(args, 'detailed_lab_reports') and args.detailed_lab_reports:
                analyze_args.append('--detailed-lab-reports')
            if hasattr(args, 'strategy_grouped_reports') and args.strategy_grouped_reports:
                analyze_args.append('--strategy-grouped-reports')
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
            from pyHaasAPI_v1.cli.create_bots_from_analysis import main as create_bots_main
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
            from pyHaasAPI_v1.cli.interactive_analyzer import main as interactive_main
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
            from pyHaasAPI_v1.cli.visualization_tool import main as viz_main
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
