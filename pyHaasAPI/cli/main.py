"""
Main CLI entry point for pyHaasAPI v2

This module provides the main command-line interface for all pyHaasAPI v2 operations
using the new async architecture and type-safe components.
"""

import asyncio
import sys
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base import BaseCLI, CLIConfig
from .lab_cli import LabCLI
from .bot_cli import BotCLI
from .analysis_cli import AnalysisCLI
from .account_cli import AccountCLI
from .script_cli import ScriptCLI
from .market_cli import MarketCLI
from .backtest_cli import BacktestCLI
from .order_cli import OrderCLI
from .backtest_workflow_cli import BacktestWorkflowCLI
# Google Sheets integration moved to gdocs/ folder
# from .google_sheets_integration import GoogleSheetsIntegration
from ..core.logging import get_logger
import subprocess
import shlex

logger = get_logger("main_cli")


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        description="pyHaasAPI v2 Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lab operations
  python -m pyHaasAPI_v2.cli lab list
  python -m pyHaasAPI_v2.cli lab create --name "Test Lab" --script-id script123
  python -m pyHaasAPI_v2.cli lab analyze --lab-id lab123 --top-count 5
  
  # Bot operations
  python -m pyHaasAPI_v2.cli bot list
  python -m pyHaasAPI_v2.cli bot create --from-lab lab123 --count 3
  python -m pyHaasAPI_v2.cli bot activate --bot-ids bot1,bot2,bot3
  
  # Analysis operations
  python -m pyHaasAPI_v2.cli analysis labs --generate-reports
  python -m pyHaasAPI_v2.cli analysis bots --performance-metrics
  python -m pyHaasAPI_v2.cli analysis wfo --lab-id lab123 --start-date 2022-01-01
  
  # Account operations
  python -m pyHaasAPI_v2.cli account list
  python -m pyHaasAPI_v2.cli account balance --account-id acc123
  python -m pyHaasAPI_v2.cli account settings --account-id acc123 --leverage 20
  
  # Script operations
  python -m pyHaasAPI_v2.cli script list
  python -m pyHaasAPI_v2.cli script create --name "Test Script" --source "print('hello')"
  python -m pyHaasAPI_v2.cli script test --script-id script123
  
  # Market operations
  python -m pyHaasAPI_v2.cli market list
  python -m pyHaasAPI_v2.cli market price --market BTC_USDT_PERPETUAL
  python -m pyHaasAPI_v2.cli market history --market BTC_USDT_PERPETUAL --days 30
  
  # Backtest operations
  python -m pyHaasAPI_v2.cli backtest list --lab-id lab123
  python -m pyHaasAPI_v2.cli backtest run --lab-id lab123 --script-id script123
  python -m pyHaasAPI_v2.cli backtest results --backtest-id bt123
  
  # Order operations
  python -m pyHaasAPI_v2.cli order list --bot-id bot123
  python -m pyHaasAPI_v2.cli order place --bot-id bot123 --side buy --amount 1000
  python -m pyHaasAPI_v2.cli order cancel --order-id order123
        """
    )
    
    # Global options
    parser.add_argument(
        '--host', 
        default='127.0.0.1',
        help='API host (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=8090,
        help='API port (default: 8090)'
    )
    parser.add_argument(
        '--timeout', 
        type=float, 
        default=30.0,
        help='Request timeout in seconds (default: 30.0)'
    )
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Log level (default: INFO)'
    )
    parser.add_argument(
        '--strict-mode', 
        action='store_true',
        help='Enable strict mode for type checking'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Perform a dry run without making changes'
    )
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true',
        help='Enable verbose output'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        required=True
    )
    
    # Lab subcommand
    lab_parser = subparsers.add_parser('lab', help='Lab operations')
    lab_parser.add_argument(
        'action',
        choices=['list', 'create', 'delete', 'analyze', 'execute', 'status', 'longest-backtest'],
        help='Lab action to perform'
    )
    lab_parser.add_argument('--lab-id', help='Lab ID')
    lab_parser.add_argument('--name', help='Lab name')
    lab_parser.add_argument('--script-id', help='Script ID')
    lab_parser.add_argument('--top-count', type=int, help='Number of top results')
    lab_parser.add_argument('--generate-reports', action='store_true', help='Generate analysis reports')
    # Longest backtest specific arguments
    lab_parser.add_argument('--lab-ids', help='Comma-separated list of lab IDs for longest backtest')
    lab_parser.add_argument('--max-iterations', type=int, default=1500, help='Maximum iterations for longest backtest')
    lab_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD) for longest backtest')
    lab_parser.add_argument('--dry-run', action='store_true', help='Perform dry run for longest backtest')
    lab_parser.add_argument('--output', help='Save longest backtest results to JSON file')
    
    # Bot subcommand
    bot_parser = subparsers.add_parser('bot', help='Bot operations')
    bot_parser.add_argument(
        'action',
        choices=['list', 'create', 'delete', 'activate', 'deactivate', 'pause', 'resume'],
        help='Bot action to perform'
    )
    bot_parser.add_argument('--bot-id', help='Bot ID')
    bot_parser.add_argument('--bot-ids', help='Comma-separated bot IDs')
    bot_parser.add_argument('--from-lab', help='Create bots from lab ID')
    bot_parser.add_argument('--count', type=int, help='Number of bots to create')
    bot_parser.add_argument('--activate', action='store_true', help='Activate bots after creation')
    
    # Analysis subcommand
    analysis_parser = subparsers.add_parser('analysis', help='Analysis operations')
    analysis_parser.add_argument(
        'action',
        choices=['labs', 'bots', 'wfo', 'performance', 'reports'],
        help='Analysis action to perform'
    )
    analysis_parser.add_argument('--lab-id', help='Lab ID')
    analysis_parser.add_argument('--bot-id', help='Bot ID')
    analysis_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    analysis_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    analysis_parser.add_argument('--generate-reports', action='store_true', help='Generate reports')
    analysis_parser.add_argument('--performance-metrics', action='store_true', help='Include performance metrics')
    
    # Account subcommand
    account_parser = subparsers.add_parser('account', help='Account operations')
    account_parser.add_argument(
        'action',
        choices=['list', 'balance', 'settings', 'orders', 'positions'],
        help='Account action to perform'
    )
    account_parser.add_argument('--account-id', help='Account ID')
    account_parser.add_argument('--leverage', type=int, help='Leverage setting')
    account_parser.add_argument('--margin-mode', choices=['cross', 'isolated'], help='Margin mode')
    account_parser.add_argument('--position-mode', choices=['hedge', 'one_way'], help='Position mode')
    
    # Script subcommand
    script_parser = subparsers.add_parser('script', help='Script operations')
    script_parser.add_argument(
        'action',
        choices=['list', 'create', 'edit', 'delete', 'test', 'publish'],
        help='Script action to perform'
    )
    script_parser.add_argument('--script-id', help='Script ID')
    script_parser.add_argument('--name', help='Script name')
    script_parser.add_argument('--source', help='Script source code')
    script_parser.add_argument('--description', help='Script description')
    
    # Market subcommand
    market_parser = subparsers.add_parser('market', help='Market operations')
    market_parser.add_argument(
        'action',
        choices=['list', 'price', 'history', 'validate'],
        help='Market action to perform'
    )
    market_parser.add_argument('--market', help='Market tag')
    market_parser.add_argument('--days', type=int, help='Number of days for history')
    market_parser.add_argument('--interval', help='Data interval')
    
    # Backtest subcommand
    backtest_parser = subparsers.add_parser('backtest', help='Backtest operations')
    backtest_parser.add_argument(
        'action',
        choices=['list', 'run', 'results', 'chart', 'log'],
        help='Backtest action to perform'
    )
    backtest_parser.add_argument('--backtest-id', help='Backtest ID')
    backtest_parser.add_argument('--lab-id', help='Lab ID')
    backtest_parser.add_argument('--script-id', help='Script ID')
    backtest_parser.add_argument('--market', help='Market tag')
    
    # Backtest Workflow subcommand
    backtest_workflow_parser = subparsers.add_parser('backtest-workflow', help='Longest backtest workflow management')
    backtest_workflow_parser.add_argument(
        'action',
        choices=['check-progress', 'analyze-results', 'execute-decisions', 'longest'],
        help='Workflow action to perform'
    )
    backtest_workflow_parser.add_argument('--bot-ids', help='Comma-separated list of bot IDs')
    backtest_workflow_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    backtest_workflow_parser.add_argument('--output', '-o', help='Save results to JSON file')
    backtest_workflow_parser.add_argument('--execute-stop', action='store_true', help='Execute stop decisions')
    backtest_workflow_parser.add_argument('--execute-retest', action='store_true', help='Execute retest decisions')
    # longest options
    backtest_workflow_parser.add_argument('--lab-ids', help='Comma-separated list of lab IDs (for longest)')
    backtest_workflow_parser.add_argument('--max-iterations', type=int, help='Max iterations (for longest)')
    backtest_workflow_parser.add_argument('--start-date', help='Explicit start date YYYY-MM-DD (for longest)')

    # Order subcommand
    order_parser = subparsers.add_parser('order', help='Order operations')
    order_parser.add_argument(
        'action',
        choices=['list', 'place', 'cancel', 'status', 'history'],
        help='Order action to perform'
    )
    order_parser.add_argument('--order-id', help='Order ID')
    order_parser.add_argument('--bot-id', help='Bot ID')
    order_parser.add_argument('--side', choices=['buy', 'sell'], help='Order side')
    order_parser.add_argument('--amount', type=float, help='Order amount')
    order_parser.add_argument('--price', type=float, help='Order price')

    # Utils subcommand (direct runners for helper tools)
    utils_parser = subparsers.add_parser('utils', help='Utility tools')
    utils_parser.add_argument(
        'action',
        choices=['cache-filtered', 'detailed-analysis'],
        help='Utility action to perform'
    )
    # cache-filtered options
    utils_parser.add_argument('--min-roe', type=float, default=0.0)
    utils_parser.add_argument('--max-roe', type=float, default=10000.0)
    utils_parser.add_argument('--min-winrate', type=float, default=0.0)
    utils_parser.add_argument('--min-trades', type=int, default=5)
    utils_parser.add_argument('--top-count', type=int, default=10)
    # detailed-analysis options
    utils_parser.add_argument('--lab-id', help='Lab ID for detailed analysis')
    
    return parser


async def main_async(args: argparse.Namespace) -> int:
    """Main async function"""
    try:
        # Create configuration
        config = CLIConfig(
            host=args.host,
            port=args.port,
            timeout=args.timeout,
            log_level=args.log_level,
            strict_mode=args.strict_mode
        )
        
        # Create appropriate CLI instance
        cli_instance = None
        
        if args.command == 'lab':
            cli_instance = LabCLI(config)
        elif args.command == 'bot':
            cli_instance = BotCLI(config)
        elif args.command == 'analysis':
            cli_instance = AnalysisCLI(config)
        elif args.command == 'account':
            cli_instance = AccountCLI(config)
        elif args.command == 'script':
            cli_instance = ScriptCLI(config)
        elif args.command == 'market':
            cli_instance = MarketCLI(config)
        elif args.command == 'backtest':
            cli_instance = BacktestCLI(config)
        elif args.command == 'backtest-workflow':
            cli_instance = BacktestWorkflowCLI(config)
            # Pass host/port from global args to the workflow CLI
            if hasattr(args, 'host'):
                cli_instance.config.host = args.host
            if hasattr(args, 'port'):
                cli_instance.config.port = args.port
        elif args.command == 'order':
            cli_instance = OrderCLI(config)
        elif args.command == 'utils':
            # Run utility scripts directly to avoid heavy wiring
            if args.action == 'cache-filtered':
                cmd = (
                    f"{shlex.quote(sys.executable)} "
                    f"{shlex.quote(str(Path(__file__).parent / 'cache_analysis_filtered.py'))} "
                    f"--min-roe {args.min_roe} --max-roe {args.max_roe} "
                    f"--min-winrate {args.min_winrate} --min-trades {args.min_trades} "
                    f"--top-count {args.top_count}"
                )
                logger.info(f"Running: {cmd}")
                proc = await asyncio.create_subprocess_shell(cmd)
                await proc.communicate()
                return proc.returncode or 0
            elif args.action == 'detailed-analysis':
                if not args.lab_id:
                    logger.error("--lab-id is required for detailed-analysis")
                    return 2
                cmd = (
                    f"{shlex.quote(sys.executable)} "
                    f"{shlex.quote(str(Path(__file__).parent / 'detailed_analysis.py'))} "
                    f"--lab-id {shlex.quote(args.lab_id)} --top-count {args.top_count}"
                )
                logger.info(f"Running: {cmd}")
                proc = await asyncio.create_subprocess_shell(cmd)
                await proc.communicate()
                return proc.returncode or 0
            else:
                logger.error(f"Unknown utils action: {args.action}")
                return 1
        elif args.command == 'lab' and args.action == 'longest-backtest':
            # Handle longest backtest using unified service
            from ..services.backtest import BacktestService
            from ..api.lab.lab_api import LabAPI
            from ..api.backtest.backtest_api import BacktestAPI
            from ..core.auth import AuthenticationManager
            
            # Create authentication manager
            auth_manager = AuthenticationManager(
                email=os.getenv('API_EMAIL'),
                password=os.getenv('API_PASSWORD')
            )
            await auth_manager.authenticate()
            
            # Create API instances
            lab_api = LabAPI(auth_manager, config)
            backtest_api = BacktestAPI(auth_manager, config)
            
            # Create backtest service
            backtest_service = BacktestService(lab_api, backtest_api)
            
            # Parse lab IDs
            lab_ids = [lab_id.strip() for lab_id in (args.lab_ids or '').split(',') if lab_id.strip()]
            if not lab_ids:
                logger.error("No lab IDs provided. Use --lab-ids id1,id2")
                return 1
            
            # Run comprehensive longest backtest
            results = await backtest_service.run_comprehensive_longest_backtest(
                lab_ids=lab_ids,
                max_iterations=args.max_iterations,
                start_date=args.start_date,
                dry_run=args.dry_run
            )
            
            # Print summary
            print("\n📋 Longest Backtest Summary")
            for lab_id, result in results.items():
                if 'error' in result:
                    print(f"  {lab_id}: ❌ {result['error']}")
                else:
                    status_icon = "🔄" if result['status'] == 'running' else "⏳" if result['status'] == 'queued' else "✅"
                    print(f"  {lab_id}: {status_icon} {result['status']} | {result.get('start_date', 'N/A')} → {result.get('end_date', 'N/A')} | {result.get('period_days', 0)} days")
            
            # Save results if requested
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Results saved to {args.output}")
            
            return 0
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
        
        # Run the CLI
        async with cli_instance:
            return await cli_instance.run(sys.argv[1:])
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Run async main function
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())