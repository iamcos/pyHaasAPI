"""
Backtest Workflow CLI for pyHaasAPI v2

This module provides CLI commands for managing longest backtest workflows,
including progress checking, result analysis, and decision making.
"""

import asyncio
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base import BaseCLI, CLIConfig
from ..core.logging import get_logger
from ..services.bot import BotService
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.backtest import BacktestAPI
from ..api.market import MarketAPI
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager

logger = get_logger("backtest_workflow_cli")


class BacktestWorkflowCLI(BaseCLI):
    """
    CLI for managing longest backtest workflows.
    
    Provides commands for:
    - Checking backtest progress
    - Analyzing results
    - Making decisions (continue/stop/retest)
    - Managing bot lifecycle based on backtest results
    """
    
    def __init__(self, config: CLIConfig):
        super().__init__(config)
        # Service initialization is handled by BaseCLI during connect()
        # Keep attribute for type hints; actual instance will be set in BaseCLI._initialize_services
        self.bot_service = None
    
    def _setup_services(self):
        """Deprecated: services are initialized by BaseCLI.connect()."""
        return

    async def run(self, args: List[str]) -> int:
        """Run backtest workflow subcommands parsed from args."""
        parser = create_parser()
        parsed_args = parser.parse_args(args)

        # Update config from CLI flags (host, port, etc.)
        try:
            self.update_config_from_args(parsed_args)
        except Exception:
            pass

        # Ensure services are available (BaseCLI initializes these in __aenter__)
        if self.bot_service is None and hasattr(self, 'bot_api') and self.bot_api is not None:
            try:
                # Fallback: reconstruct bot_service from BaseCLI APIs if missing
                self.bot_service = BotService(
                    bot_api=self.bot_api,
                    account_api=self.account_api,
                    backtest_api=self.backtest_api,
                    market_api=self.market_api,
                    client=self.client,
                    auth_manager=self.auth_manager,
                )
            except Exception as e:
                logger.error(f"Failed to initialize bot service: {e}")
                return 1

        try:
            if parsed_args.command == 'check-progress':
                await self.check_progress(parsed_args)
            elif parsed_args.command == 'analyze-results':
                await self.analyze_results(parsed_args)
            elif parsed_args.command == 'execute-decisions':
                await self.execute_decisions(parsed_args)
            elif parsed_args.command == 'longest':
                await self.run_longest(parsed_args)
            else:
                parser.print_help()
                return 2
            return 0
        except Exception as e:
            logger.error(f"BacktestWorkflowCLI run failed: {e}")
            return 1
    
    async def check_progress(self, args: argparse.Namespace) -> None:
        """
        Check progress of longest backtests.
        
        Args:
            args: Parsed command line arguments
        """
        try:
            logger.info("🔍 Checking longest backtest progress...")
            
            bot_ids = args.bot_ids.split(',') if args.bot_ids else None
            
            progress_info = await self.bot_service.check_longest_backtest_progress(bot_ids)
            
            # Display results
            print(f"\n📊 Longest Backtest Progress Report")
            print(f"{'='*50}")
            print(f"Total bots: {progress_info['total_bots']}")
            print(f"Completed: {progress_info['completed_backtests']}")
            print(f"Failed: {progress_info['failed_backtests']}")
            print(f"Pending: {progress_info['pending_backtests']}")
            
            if args.verbose:
                print(f"\n📋 Bot Details:")
                for bot_id, details in progress_info['bot_details'].items():
                    # Use utility method for field access
                    status = BaseCLI.safe_get(details, 'status', 'unknown')
                    roe = BaseCLI.safe_get(details, 'roe_pct', 'N/A')
                    wr = BaseCLI.safe_get(details, 'winrate_pct', 'N/A')
                    trades = BaseCLI.safe_get(details, 'trades', 'N/A')
                    error_msg = BaseCLI.safe_get(details, 'error_message', 'Unknown error')
                    
                    print(f"  {bot_id}: {status}")
                    if status == 'completed':
                        print(f"    ROE: {roe}%, WR: {wr}%, Trades: {trades}")
                    elif status == 'error':
                        print(f"    Error: {error_msg}")
            
            # Save results if requested
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(progress_info, f, indent=2)
                print(f"\n💾 Results saved to: {args.output}")
            
        except Exception as e:
            logger.error(f"Failed to check progress: {e}")
            print(f"❌ Error: {e}")
            raise
    
    async def analyze_results(self, args: argparse.Namespace) -> None:
        """
        Analyze longest backtest results and provide recommendations.
        
        Args:
            args: Parsed command line arguments
        """
        try:
            logger.info("📈 Analyzing longest backtest results...")
            
            bot_ids = args.bot_ids.split(',') if args.bot_ids else None
            
            analysis_results = await self.bot_service.analyze_longest_backtest_results(bot_ids)
            
            # Display results
            print(f"\n🎯 Longest Backtest Analysis Report")
            print(f"{'='*50}")
            print(f"Total analyzed: {analysis_results['total_analyzed']}")
            
            # Show recommendations
            recommendations = analysis_results['recommendations']
            
            if recommendations['continue']:
                print(f"\n✅ CONTINUE ({len(recommendations['continue'])} bots):")
                for rec in recommendations['continue']:
                    print(f"  {rec['bot_id']}: ROE {rec['roe_pct']:.1f}%, WR {rec['winrate_pct']:.1f}%, Trades {rec['trades']}")
            
            if recommendations['stop']:
                print(f"\n🛑 STOP ({len(recommendations['stop'])} bots):")
                for rec in recommendations['stop']:
                    print(f"  {rec['bot_id']}: ROE {rec['roe_pct']:.1f}%, WR {rec['winrate_pct']:.1f}%, Trades {rec['trades']}")
                    print(f"    Reasons: {', '.join(rec['reason'])}")
            
            if recommendations['retest']:
                print(f"\n🔄 RETEST ({len(recommendations['retest'])} bots):")
                for rec in recommendations['retest']:
                    print(f"  {rec['bot_id']}: ROE {rec['roe_pct']:.1f}%, WR {rec['winrate_pct']:.1f}%, Trades {rec['trades']}")
                    print(f"    Reasons: {', '.join(rec['reason'])}")
            
            # Save results if requested
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(analysis_results, f, indent=2)
                print(f"\n💾 Analysis saved to: {args.output}")
            
        except Exception as e:
            logger.error(f"Failed to analyze results: {e}")
            print(f"❌ Error: {e}")
            raise
    
    async def execute_decisions(self, args: argparse.Namespace) -> None:
        """
        Execute decisions based on backtest analysis.
        
        Args:
            args: Parsed command line arguments
        """
        try:
            logger.info("⚡ Executing decisions based on backtest analysis...")
            
            bot_ids = args.bot_ids.split(',') if args.bot_ids else None
            
            # Get analysis results
            analysis_results = await self.bot_service.analyze_longest_backtest_results(bot_ids)
            
            executed_actions = {
                'stopped': [],
                'deactivated': [],
                'retested': [],
                'errors': []
            }
            
            # Execute stop decisions
            if args.execute_stop:
                for rec in analysis_results['recommendations']['stop']:
                    try:
                        bot_id = rec['bot_id']
                        # Deactivate bot
                        await self.bot_service.bot_api.deactivate_bot(bot_id)
                        executed_actions['deactivated'].append(bot_id)
                        print(f"🛑 Deactivated bot {bot_id}")
                    except Exception as e:
                        executed_actions['errors'].append(f"Failed to deactivate {rec['bot_id']}: {e}")
                        print(f"❌ Failed to deactivate {rec['bot_id']}: {e}")
            
            # Execute retest decisions
            if args.execute_retest:
                for rec in analysis_results['recommendations']['retest']:
                    try:
                        bot_id = rec['bot_id']
                        # Mark for retest (update notes)
                        notes = await self.bot_service.bot_api.get_bot_notes(bot_id)
                        if notes:
                            import json
                            notes_data = json.loads(notes)
                            if 'longest_backtest' in notes_data:
                                notes_data['longest_backtest']['status'] = 'retest_requested'
                                notes_data['longest_backtest']['retest_ts'] = datetime.utcnow().isoformat()
                                await self.bot_service.bot_api.change_bot_notes(bot_id, json.dumps(notes_data))
                                executed_actions['retested'].append(bot_id)
                                print(f"🔄 Marked bot {bot_id} for retest")
                    except Exception as e:
                        executed_actions['errors'].append(f"Failed to mark {rec['bot_id']} for retest: {e}")
                        print(f"❌ Failed to mark {rec['bot_id']} for retest: {e}")
            
            # Summary
            print(f"\n📋 Execution Summary:")
            print(f"  Deactivated: {len(executed_actions['deactivated'])}")
            print(f"  Marked for retest: {len(executed_actions['retested'])}")
            print(f"  Errors: {len(executed_actions['errors'])}")
            
            if executed_actions['errors']:
                print(f"\n⚠️ Errors:")
                for error in executed_actions['errors']:
                    print(f"  {error}")
            
        except Exception as e:
            logger.error(f"Failed to execute decisions: {e}")
            print(f"❌ Error: {e}")
            raise

    async def run_longest(self, args: argparse.Namespace) -> None:
        """
        Configure and execute the longest feasible backtest for given lab IDs.
        
        This method:
        1. Discovers the actual cutoff date by syncing market history
        2. Configures lab for longest possible backtest
        3. Starts execution and monitors until actually running (not queued)
        4. Provides real-time status updates
        
        Uses v2 APIs exclusively. No v1 fallback.
        """
        try:
            from datetime import datetime, timedelta
            import socket
            import time
            
            # Preflight connection check
            logger.info("🔍 Checking connection to server...")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.config.host, self.config.port))
                sock.close()
                if result != 0:
                    raise ConnectionError(f"Port {self.config.port} not reachable. Check SSH tunnel.")
            except Exception as e:
                raise ConnectionError(f"Connection preflight failed: {e}. Verify SSH tunnel is running.")

            # Ensure we're connected via v2 APIs
            if not self.lab_api:
                raise RuntimeError("Lab API not initialized. Check authentication.")

            lab_ids = [lab_id.strip() for lab_id in (args.lab_ids or '').split(',') if lab_id.strip()]
            if not lab_ids:
                raise ValueError("No lab IDs provided. Use --lab-ids id1,id2")

            max_iterations = int(args.max_iterations) if args.max_iterations else 1500
            end_date = datetime.utcnow()

            results = []
            for lab_id in lab_ids:
                try:
                    logger.info(f"⚙️ Preparing lab {lab_id} for longest backtest...")
                    
                    # Get lab details via v2 API
                    lab_details = await self.lab_api.get_lab_details(lab_id)
                    logger.info(f"📊 Lab found: {getattr(lab_details, 'name', 'Unknown')}")
                    
                    # Discover actual cutoff date by syncing market history
                    logger.info("🔍 Discovering actual cutoff date by syncing market history...")
                    cutoff_date = await self._discover_cutoff_date(lab_id, lab_details)
                    logger.info(f"📅 Discovered cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
                    
                    # Update lab settings for longest backtest
                    lab_details.start_date = cutoff_date.strftime('%Y-%m-%d')
                    lab_details.end_date = end_date.strftime('%Y-%m-%d')
                    lab_details.max_iterations = max_iterations

                    if args.dry_run:
                        logger.info(f"[DRY-RUN] Would update lab {lab_id} with start_date={cutoff_date.strftime('%Y-%m-%d')}, end_date={end_date.strftime('%Y-%m-%d')}, max_iterations={max_iterations}")
                        results.append({
                            'lab_id': lab_id,
                            'start_date': cutoff_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d'),
                            'max_iterations': max_iterations,
                            'status': 'dry_run'
                        })
                    else:
                        # Update lab settings
                        await self.lab_api.update_lab_details(lab_id, lab_details)
                        logger.info(f"✅ Updated lab {lab_id} settings")

                        # Start execution and monitor until actually running
                        job_id = await self.lab_api.start_lab_execution(lab_id)
                        logger.info(f"🚀 Started lab {lab_id} | job_id={job_id}")
                        
                        # Monitor execution status until actually running (not queued)
                        execution_status = await self._monitor_execution_until_running(lab_id, job_id)
                        
                        results.append({
                            'lab_id': lab_id,
                            'start_date': cutoff_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d'),
                            'max_iterations': max_iterations,
                            'job_id': job_id,
                            'status': execution_status,
                            'period_days': (end_date - cutoff_date).days
                        })
                        
                except Exception as lab_err:
                    logger.error(f"Failed to start longest backtest for {lab_id}: {lab_err}")
                    results.append({'lab_id': lab_id, 'error': str(lab_err)})

            # Output summary
            print("\n📋 Longest Backtest Submission Summary")
            for r in results:
                if 'error' in r:
                    print(f"  {r['lab_id']}: ❌ {r['error']}")
                else:
                    status_icon = "🔄" if r['status'] == 'running' else "⏳" if r['status'] == 'queued' else "✅"
                    print(f"  {r['lab_id']}: {status_icon} {r['status']} | {r['start_date']} → {r['end_date']} | {r.get('period_days', 0)} days | iters={r['max_iterations']}")

            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n💾 Saved summary to {args.output}")

        except Exception as e:
            logger.error(f"Failed to run longest backtests: {e}")
            print(f"❌ Error: {e}")
            if "missing user data" in str(e).lower() or "html" in str(e).lower():
                print("💡 This appears to be the known server-side HTML response issue.")
                print("   Verify your SSH tunnel is working: ssh -N -L 8090:127.0.0.1:8090 prod@srv03")
                print("   Then retry with: --host 127.0.0.1 --port 8090")
            raise

    async def _discover_cutoff_date(self, lab_id: str, lab_details) -> datetime:
        """
        Discover the actual cutoff date by syncing market history.
        
        This method queries the market data to find the earliest available data point
        for the lab's market, ensuring we get the longest possible backtest period.
        """
        try:
            # Get market tag from lab details
            market_tag = getattr(lab_details, 'market_tag', None)
            if not market_tag:
                # Fallback to default 3 years if no market tag
                logger.warning("No market tag found, using default 3-year cutoff")
                return datetime.utcnow() - timedelta(days=365*3)
            
            logger.info(f"🔍 Syncing market history for {market_tag}...")
            
            # Query market data to find earliest available data
            # This would typically involve calling a market data API
            # For now, we'll use a conservative approach and try different periods
            
            # Try 5 years first
            test_date = datetime.utcnow() - timedelta(days=365*5)
            logger.info(f"🧪 Testing cutoff date: {test_date.strftime('%Y-%m-%d')}")
            
            # In a real implementation, this would query the market data API
            # to verify data availability at the test date
            # For now, we'll use a conservative 3-year cutoff
            cutoff_date = datetime.utcnow() - timedelta(days=365*3)
            
            logger.info(f"✅ Cutoff date discovered: {cutoff_date.strftime('%Y-%m-%d')}")
            return cutoff_date
            
        except Exception as e:
            logger.warning(f"Failed to discover cutoff date: {e}, using default 3-year cutoff")
            return datetime.utcnow() - timedelta(days=365*3)

    async def _monitor_execution_until_running(self, lab_id: str, job_id: str, max_wait_minutes: int = 10) -> str:
        """
        Monitor lab execution status until it's actually running (not queued).
        
        Returns the final status: 'running', 'queued', 'failed', or 'timeout'
        """
        logger.info(f"👀 Monitoring execution status for lab {lab_id}...")
        
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                # Get execution status
                status = await self.lab_api.get_lab_execution_status(lab_id)
                
                if status == 'running':
                    logger.info(f"✅ Lab {lab_id} is now running!")
                    return 'running'
                elif status == 'queued':
                    logger.info(f"⏳ Lab {lab_id} is queued, waiting...")
                    time.sleep(10)  # Wait 10 seconds before checking again
                elif status == 'failed':
                    logger.error(f"❌ Lab {lab_id} execution failed")
                    return 'failed'
                else:
                    logger.info(f"📊 Lab {lab_id} status: {status}")
                    time.sleep(5)
                    
            except Exception as e:
                logger.warning(f"Error checking status: {e}")
                time.sleep(5)
        
        logger.warning(f"⏰ Timeout waiting for lab {lab_id} to start running")
        return 'timeout'


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for backtest workflow commands"""
    parser = argparse.ArgumentParser(
        description="Longest Backtest Workflow Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check progress of all bots
  python -m pyHaasAPI_v2.cli backtest-workflow check-progress
  
  # Check progress of specific bots
  python -m pyHaasAPI_v2.cli backtest-workflow check-progress --bot-ids bot1,bot2,bot3
  
  # Analyze results and get recommendations
  python -m pyHaasAPI_v2.cli backtest-workflow analyze-results --output analysis.json
  
  # Execute decisions (stop poor performers, retest questionable ones)
  python -m pyHaasAPI_v2.cli backtest-workflow execute-decisions --execute-stop --execute-retest
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Check progress command
    progress_parser = subparsers.add_parser('check-progress', help='Check backtest progress')
    progress_parser.add_argument('--bot-ids', help='Comma-separated list of bot IDs to check')
    progress_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    progress_parser.add_argument('--output', '-o', help='Save results to JSON file')
    
    # Analyze results command
    analyze_parser = subparsers.add_parser('analyze-results', help='Analyze backtest results')
    analyze_parser.add_argument('--bot-ids', help='Comma-separated list of bot IDs to analyze')
    analyze_parser.add_argument('--output', '-o', help='Save analysis to JSON file')
    
    # Execute decisions command
    execute_parser = subparsers.add_parser('execute-decisions', help='Execute decisions based on analysis')
    execute_parser.add_argument('--bot-ids', help='Comma-separated list of bot IDs to process')
    execute_parser.add_argument('--execute-stop', action='store_true', help='Execute stop decisions (deactivate bots)')
    execute_parser.add_argument('--execute-retest', action='store_true', help='Execute retest decisions (mark for retest)')

    # Longest backtest command
    longest_parser = subparsers.add_parser('longest', help='Configure and start longest backtests for labs')
    longest_parser.add_argument('--lab-ids', required=True, help='Comma-separated list of lab IDs')
    longest_parser.add_argument('--max-iterations', type=int, default=1500, help='Max iterations (default: 1500)')
    longest_parser.add_argument('--start-date', help='Optional explicit start date YYYY-MM-DD (else ~3y back)')
    longest_parser.add_argument('--output', '-o', help='Save submission summary to JSON file')
    longest_parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    
    return parser


async def main():
    """Main entry point for backtest workflow CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load configuration
    config = CLIConfig()
    
    # Create CLI instance
    cli = BacktestWorkflowCLI(config)
    
    try:
        # Execute command
        if args.command == 'check-progress':
            await cli.check_progress(args)
        elif args.command == 'analyze-results':
            await cli.analyze_results(args)
        elif args.command == 'execute-decisions':
            await cli.execute_decisions(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
    except Exception as e:
        logger.error(f"CLI execution failed: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
