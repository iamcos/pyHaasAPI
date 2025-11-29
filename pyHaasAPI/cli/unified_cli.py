"""
Unified CLI for pyHaasAPI v2

Single entry point that routes commands directly to services/APIs.
No business logic - just argument parsing and service calls.
"""

import asyncio
import argparse
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from .base import BaseCLI, CLIConfig
from ..core.logging import get_logger
from ..core.server_manager import ServerManager
from ..config.settings import Settings

logger = get_logger("unified_cli")


class UnifiedCLI(BaseCLI):
    """
    Unified CLI that routes commands directly to services/APIs.
    
    This is a thin layer - all business logic lives in services.
    """
    
    def __init__(self, config: Optional[CLIConfig] = None):
        super().__init__(config)
        self._command_handlers = {}
        self._initialize_handlers()
    
    def _initialize_handlers(self):
        """Initialize command handlers"""
        from .commands import (
            LabCommands, BotCommands, AnalysisCommands, AccountCommands,
            ScriptCommands, MarketCommands, BacktestCommands, OrderCommands,
            DownloadCommands, LongestBacktestCommands, ServerCommands
        )
        
        self._command_handlers = {
            'lab': LabCommands,
            'bot': BotCommands,
            'analysis': AnalysisCommands,
            'account': AccountCommands,
            'script': ScriptCommands,
            'market': MarketCommands,
            'backtest': BacktestCommands,
            'order': OrderCommands,
            'download': DownloadCommands,
            'longest-backtest': LongestBacktestCommands,
            'server': ServerCommands,
        }
    
    async def run(self, args: argparse.Namespace) -> int:
        """Run the unified CLI"""
        try:
            # Connect if not already connected
            if not self.client:
                if not await self.connect():
                    logger.error("Failed to connect to API")
                    return 1
            
            # Get domain and action
            domain = args.domain
            action = args.action
            
            # Route to appropriate handler
            if domain not in self._command_handlers:
                logger.error(f"Unknown domain: {domain}")
                logger.info(f"Available domains: {', '.join(self._command_handlers.keys())}")
                return 1
            
            handler_class = self._command_handlers[domain]
            handler = handler_class(self)
            
            # Execute command
            return await handler.handle(action, args)
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1


def create_parser() -> argparse.ArgumentParser:
    """Create unified argument parser"""
    parser = argparse.ArgumentParser(
        description="pyHaasAPI v2 Unified CLI - Direct service/API access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lab operations
  python -m pyHaasAPI.cli unified_cli lab list
  python -m pyHaasAPI.cli unified_cli lab create --name "Test Lab" --script-id script123
  python -m pyHaasAPI.cli unified_cli lab analyze --lab-id lab123 --top-count 5
  
  # Bot operations
  python -m pyHaasAPI.cli unified_cli bot list
  python -m pyHaasAPI.cli unified_cli bot create --from-lab lab123 --count 3
  python -m pyHaasAPI.cli unified_cli bot activate --bot-ids bot1,bot2,bot3
  
  # Analysis operations
  python -m pyHaasAPI.cli unified_cli analysis labs --min-winrate 55 --zero-drawdown
  python -m pyHaasAPI.cli unified_cli analysis bots --performance-metrics
  
  # Download operations
  python -m pyHaasAPI.cli unified_cli download everything
  python -m pyHaasAPI.cli unified_cli download server --server-name srv02
        """
    )
    
    # Global options
    parser.add_argument('--timeout', type=float, default=30.0, help='Request timeout')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--output-format', choices=['json', 'csv', 'table'], default='table', help='Output format')
    parser.add_argument('--output-file', help='Output file path')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    # Domain and action (required)
    parser.add_argument('domain', choices=[
        'lab', 'bot', 'analysis', 'account', 'script', 'market', 
        'backtest', 'order', 'download', 'longest-backtest', 'server'
    ], help='Domain/entity to operate on')
    
    parser.add_argument('action', help='Action to perform (varies by domain)')
    
    # Common arguments (used by multiple domains)
    parser.add_argument('--lab-id', help='Lab ID')
    parser.add_argument('--lab-ids', help='Comma-separated lab IDs')
    parser.add_argument('--bot-id', help='Bot ID')
    parser.add_argument('--bot-ids', help='Comma-separated bot IDs')
    parser.add_argument('--account-id', help='Account ID')
    parser.add_argument('--exchange', help='Exchange code (e.g., BINANCEFUTURES)')
    parser.add_argument('--script-id', help='Script ID')
    parser.add_argument('--market', help='Market tag')
    parser.add_argument('--backtest-id', help='Backtest ID')
    parser.add_argument('--order-id', help='Order ID')
    parser.add_argument('--side', choices=['buy', 'sell'], help='Order side (buy/sell)')
    parser.add_argument('--amount', type=float, help='Order amount')
    parser.add_argument('--price', type=float, help='Order price')
    
    # Lab-specific arguments
    parser.add_argument('--name', help='Name (for create operations)')
    parser.add_argument('--description', help='Description')
    parser.add_argument('--top-count', type=int, default=10, help='Number of top results')
    parser.add_argument('--generate-reports', action='store_true', help='Generate reports')
    
    # Bot-specific arguments
    parser.add_argument('--from-lab', help='Create bots from lab ID')
    parser.add_argument('--count', type=int, help='Number of bots to create')
    parser.add_argument('--activate', action='store_true', help='Activate after creation')
    parser.add_argument('--status', choices=['active', 'inactive', 'paused'], help='Filter by status')
    
    # Analysis-specific arguments
    parser.add_argument('--min-winrate', type=float, help='Minimum win rate')
    parser.add_argument('--min-trades', type=int, help='Minimum trades')
    parser.add_argument('--zero-drawdown', action='store_true', help='Zero drawdown only')
    parser.add_argument('--sort-by', choices=['roi', 'roe', 'winrate', 'profit', 'trades'], default='roe')
    
    # Download-specific arguments
    parser.add_argument('--server-name', help='Server name (srv01, srv02, srv03)')
    parser.add_argument('--max-pages', type=int, default=1000, help='Max pages to download')
    parser.add_argument('--resume', action='store_true', help='Resume fetching (for fetch-backtests)')
    
    # Longest backtest arguments
    parser.add_argument('--max-iterations', type=int, default=1500, help='Max iterations')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    
    # Market-specific arguments
    parser.add_argument('--days', type=int, help='Number of days for history')
    
    # Lab clone/rename/config arguments
    parser.add_argument('--new-name', help='New name for lab rename')
    parser.add_argument('--coin', help='Coin name (for clone/rename)')
    parser.add_argument('--stage-label', help='Stage label (for clone/rename/orchestrate)')
    parser.add_argument('--script-name', help='Script name (for rename)')
    parser.add_argument('--cutoff-date', help='Cutoff date (for rename)')
    parser.add_argument('--trade-amount', type=float, help='Trade amount in USDT (for config)')
    parser.add_argument('--markets', help='Comma-separated markets (for clone/orchestrate)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD or Unix timestamp)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD or Unix timestamp)')
    parser.add_argument('--source', help='Source code (for script create/edit)')
    parser.add_argument('--count', type=int, help='Count (for various operations)')
    parser.add_argument('--resume', action='store_true', help='Resume operation')
    
    return parser


async def main_async(args: argparse.Namespace) -> int:
    """Main async entry point"""
    try:
        config = CLIConfig(
            timeout=args.timeout,
            log_level=args.log_level
        )
        
        cli = UnifiedCLI(config)
        return await cli.run(args)
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled")
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
    return asyncio.run(main_async(args))


if __name__ == '__main__':
    sys.exit(main())

