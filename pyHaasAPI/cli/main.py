"""
Main CLI entry point for pyHaasAPI v2

This module provides the main command-line interface for all pyHaasAPI v2 operations
using the new async architecture and type-safe components.
"""

import asyncio
import os
import sys
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
from .consolidated_cli import ConsolidatedCLI
from .download_cli import DownloadCLI
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
  
  # Orchestrator operations
  python -m pyHaasAPI.cli orchestrator execute --project-name "MyProject" --base-labs lab1,lab2,lab3
  python -m pyHaasAPI.cli orchestrator validate --project-name "TestProject" --base-labs lab1,lab2
  python -m pyHaasAPI.cli orchestrator status --project-name "MyProject"
        """
    )
    
    # Global options (host/port flags removed; tunnel enforced via ServerManager)
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
        choices=['labs', 'bots', 'wfo', 'performance', 'reports', 'labs-without-bots'],
        help='Analysis action to perform'
    )
    analysis_parser.add_argument('--lab-id', help='Lab ID')
    analysis_parser.add_argument('--bot-id', help='Bot ID')
    analysis_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    analysis_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    analysis_parser.add_argument('--generate-reports', action='store_true', help='Generate reports')
    analysis_parser.add_argument('--performance-metrics', action='store_true', help='Include performance metrics')
    analysis_parser.add_argument('--server', help='Server name (srv01, srv02, srv03)')
    
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

    # Download subcommand
    download_parser = subparsers.add_parser('download', help='Download all backtests from all servers')
    download_parser.add_argument(
        'action',
        choices=['everything', 'server', 'lab', 'backtests-for-labs', 'help'],
        help='Download action to perform'
    )
    download_parser.add_argument('--server-name', help='Server name (for server action)')
    download_parser.add_argument('--lab-id', help='Lab ID (for lab action)')
    
    # Analyze subcommand
    analyze_parser = subparsers.add_parser('analyze', help='Analyze downloaded backtest data')
    analyze_parser.add_argument('json_file', nargs='?', help='Path to JSON database file (defaults to latest)')
    analyze_parser.add_argument('--output', '-o', help='Output CSV file path')

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
    
    # Consolidated CLI subcommand (all-in-one functionality)
    consolidated_parser = subparsers.add_parser('consolidated', help='Consolidated CLI with all functionality')
    consolidated_parser.add_argument('--analyze', action='store_true', help='Analyze labs with zero drawdown requirement')
    consolidated_parser.add_argument('--create-bots', action='store_true', help='Create bots from analysis results')
    consolidated_parser.add_argument('--min-winrate', type=float, default=55.0, help='Minimum win rate percentage (default: 55)')
    consolidated_parser.add_argument('--bots-per-lab', type=int, default=2, help='Number of bots to create per lab (default: 2)')
    consolidated_parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate'], default='roe', help='Sort by metric (default: roe)')
    
    # Orchestrator subcommand (simple trading orchestrator)
    orchestrator_parser = subparsers.add_parser('orchestrator', help='Simple Trading Orchestrator - Multi-server trading orchestration')
    orchestrator_parser.add_argument(
        'action',
        choices=['execute', 'validate', 'status'],
        help='Orchestrator action to perform'
    )
    # Execute arguments
    orchestrator_parser.add_argument('--project-name', type=str, required=True, help='Name of the trading project')
    orchestrator_parser.add_argument('--servers', type=str, default='srv01,srv02,srv03', help='Comma-separated list of servers')
    orchestrator_parser.add_argument('--coins', type=str, default='BTC,ETH,TRX,ADA', help='Comma-separated list of coins')
    orchestrator_parser.add_argument('--base-labs', type=str, required=True, help='Comma-separated list of base lab IDs')
    orchestrator_parser.add_argument('--account-type', type=str, default='BINANCEFUTURES_USDT', help='Account type')
    orchestrator_parser.add_argument('--trade-amount-usdt', type=float, default=2000.0, help='Trade amount in USDT')
    orchestrator_parser.add_argument('--leverage', type=float, default=20.0, help='Leverage')
    orchestrator_parser.add_argument('--max-drawdown-threshold', type=float, default=0.0, help='Maximum drawdown threshold')
    orchestrator_parser.add_argument('--min-win-rate', type=float, default=0.6, help='Minimum win rate')
    orchestrator_parser.add_argument('--min-trades', type=int, default=10, help='Minimum number of trades')
    orchestrator_parser.add_argument('--min-stability-score', type=float, default=70.0, help='Minimum stability score')
    orchestrator_parser.add_argument('--top-bots-per-coin', type=int, default=3, help='Number of top bots per coin')
    orchestrator_parser.add_argument('--activate-bots', action='store_true', help='Activate bots after creation')
    orchestrator_parser.add_argument('--dry-run', action='store_true', help='Dry run - validate configuration without execution')
    orchestrator_parser.add_argument('--output-dir', type=str, default='trading_projects', help='Output directory for project results')
    orchestrator_parser.add_argument('--config-file', type=str, help='Load configuration from JSON file')
    
    return parser


async def main_async(args: argparse.Namespace) -> int:
    """Main async function"""
    try:
        # Create configuration (host/port removed - using mandated tunnel via environment)
        config = CLIConfig(
            timeout=args.timeout,
            log_level=args.log_level,
            strict_mode=args.strict_mode
        )
        
        # Create appropriate CLI instance
        cli_instance = None
        
        # Check for longest-backtest first (before general lab handler)
        if args.command == 'lab' and hasattr(args, 'action') and args.action == 'longest-backtest':
            # Handle longest backtest using unified service
            from pyHaasAPI.services.backtest import BacktestService
            from pyHaasAPI.api.lab.lab_api import LabAPI
            from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
            from pyHaasAPI.core.auth import AuthenticationManager
            from pyHaasAPI.core.server_manager import ServerManager
            from pyHaasAPI.config.settings import Settings
            from pyHaasAPI.core.client import AsyncHaasClient
            from pyHaasAPI.config.api_config import APIConfig
            
            # Preflight: enforce mandated SSH tunnel availability
            sm = ServerManager(Settings())
            ok = await sm.preflight_check()
            if not ok:
                logger.error("Tunnel preflight failed. Start the mandated SSH tunnel: ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv0*")
                return 2
            
            # Create config and client
            client_config = APIConfig()
            client = AsyncHaasClient(client_config)
            
            # Create authentication manager
            auth_manager = AuthenticationManager(client, client_config)
            await auth_manager.authenticate()
            
            # Create API instances
            lab_api = LabAPI(client, auth_manager)
            backtest_api = BacktestAPI(client, auth_manager)
            
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
            
            # Print machine-parseable JSON summary
            import json
            import time
            from datetime import datetime
            
            # Create comprehensive summary with metrics
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_labs": len(lab_ids),
                "successful": sum(
                    1 for r in results.values() 
                    if BaseCLI.safe_get(r, 'status') == 'success'
                ),
                "failed": sum(
                    1 for r in results.values() 
                    if BaseCLI.safe_has(r, 'error')
                ),
                "results": {}
            }
            
            for lab_id, result in results.items():
                if 'error' in result:
                    summary["results"][lab_id] = {
                        "status": "error",
                        "error": result['error'],
                        "earliest_start": None,
                        "end": None,
                        "attempts": [],
                        "total_attempts": 0,
                        "total_elapsed_seconds": 0,
                        "notes": "Error occurred"
                    }
                    print(f"  {lab_id}: ❌ {result['error']}")
                else:
                    # Extract metrics from result using utility method
                    attempts = BaseCLI.safe_get(result, 'attempts', [])
                    earliest_start = BaseCLI.safe_get(result, 'approx_start_date')
                    end_date = BaseCLI.safe_get(result, 'end_date')
                    status = BaseCLI.safe_get(result, 'status', 'unknown')
                    elapsed_seconds = BaseCLI.safe_get(result, 'elapsed_seconds', 0)
                    notes = BaseCLI.safe_get(result, 'notes', '')
                    
                    summary["results"][lab_id] = {
                        "status": status,
                        "earliest_start": earliest_start,
                        "end": end_date,
                        "attempts": attempts,
                        "total_attempts": len(attempts),
                        "total_elapsed_seconds": elapsed_seconds,
                        "notes": notes
                    }
                    
                    result_status = BaseCLI.safe_get(result, 'status', 'unknown')
                    status_icon = "🔄" if result_status == 'running' else "⏳" if result_status == 'queued' else "✅"
                    print(f"  {lab_id}: {status_icon} {result_status} | {earliest_start or 'N/A'} → {end_date or 'N/A'} | {len(attempts)} attempts")
            
            # Print JSON summary to stdout
            print("\n" + "="*50)
            print("JSON SUMMARY:")
            print(json.dumps(summary, indent=2))
            print("="*50)
            
            # Save results if requested
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(summary, f, indent=2)
                print(f"\n💾 Results saved to {args.output}")
            
            return 0
        elif args.command == 'lab':
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
        elif args.command == 'order':
            cli_instance = OrderCLI(config)
        elif args.command == 'download':
            cli_instance = DownloadCLI()
        elif args.command == 'analyze':
            # Handle analyze command
            from .analyze_backtests import BacktestAnalyzer
            import sys
            
            json_file = args.json_file
            if not json_file:
                # Find latest JSON file
                from pathlib import Path
                json_files = sorted(Path('.').glob('COMPLETE_BACKTEST_DATABASE_*.json'), reverse=True)
                if not json_files:
                    logger.error("No backtest database JSON file found!")
                    return 1
                json_file = str(json_files[0])
                logger.info(f"Using latest file: {json_file}")
            
            analyzer = BacktestAnalyzer(json_file)
            analyzer.analyze()
            output_file = analyzer.generate_spreadsheet(args.output)
            
            print(f"\n✅ Analysis complete!")
            print(f"📊 Analyzed {len(analyzer.analysis_results)} labs")
            print(f"📈 Spreadsheet: {output_file}")
            return 0
        elif args.command == 'orchestrator':
            # Handle orchestrator command using SimpleOrchestratorCLI
            from .simple_orchestrator_cli import SimpleOrchestratorCLI
            cli = SimpleOrchestratorCLI()
            return await cli.run(sys.argv[1:])
        elif args.command == 'consolidated':
            # Use the consolidated CLI directly
            cli = ConsolidatedCLI()
            try:
                # Connect to API
                if not await cli.connect():
                    logger.error("Failed to connect to API")
                    return 1
                
                lab_results = {}
                
                # Analyze labs if requested
                if args.analyze:
                    lab_results = await cli.analyze_all_labs(
                        min_winrate=args.min_winrate,
                        sort_by=args.sort_by
                    )
                    
                    if lab_results:
                        cli.print_analysis_report(lab_results)
                    else:
                        logger.warning("No qualifying labs found")
                        return 0
                
                # Create bots if requested
                if args.create_bots:
                    if not lab_results:
                        # Re-analyze if not already done
                        lab_results = await cli.analyze_all_labs(
                            min_winrate=args.min_winrate,
                            sort_by=args.sort_by
                        )
                    
                    if lab_results:
                        created_bots = await cli.create_bots_from_analysis(lab_results, args.bots_per_lab)
                        if created_bots:
                            cli.print_bot_creation_report(created_bots)
                        else:
                            logger.warning("No bots were created")
                    else:
                        logger.warning("No qualifying labs found for bot creation")
                
                return 0
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                return 1
            finally:
                await cli.close()
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
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
        
        # Run the CLI
        async with cli_instance:
            # Pass only the arguments after the command
            # sys.argv can vary depending on options passed before the command
            # Find the command in sys.argv and pass everything after it
            try:
                command_index = sys.argv.index(args.command)
                remaining_args = sys.argv[command_index + 1:]  # Skip command and everything before it
            except ValueError:
                remaining_args = sys.argv[2:]  # Fallback
            
            logger.debug(f"sys.argv: {sys.argv}")
            logger.debug(f"command: {args.command}")
            logger.debug(f"remaining_args: {remaining_args}")
            return await cli_instance.run(remaining_args)
            
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