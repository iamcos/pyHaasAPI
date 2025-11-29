"""
Market command handlers - Direct calls to MarketAPI
"""

from typing import Any
from ..base import BaseCLI


class MarketCommands:
    """Market command handlers - thin wrappers around MarketAPI"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle market commands"""
        market_api = self.cli.market_api
        
        if not market_api:
            self.cli.logger.error("Market API not initialized")
            return 1
        
        try:
            if action == 'list':
                # Direct API call
                markets = await market_api.get_all_markets()
                self.cli.format_output(markets, args.output_format, args.output_file)
                return 0
                
            elif action == 'price':
                # Direct API call
                if not args.market:
                    self.cli.logger.error("--market is required")
                    return 1
                
                price_data = await market_api.get_price_data(args.market)
                self.cli.format_output([price_data], args.output_format, args.output_file)
                return 0
                
            elif action == 'history':
                # Direct API call
                if not args.market:
                    self.cli.logger.error("--market is required")
                    return 1
                
                days = args.days or 30
                history = await market_api.get_market_history(args.market, days=days)
                self.cli.format_output(history, args.output_format, args.output_file)
                return 0
                
            elif action == 'validate':
                # Direct API call
                if not args.market:
                    self.cli.logger.error("--market is required")
                    return 1
                
                is_valid = await market_api.validate_market(args.market)
                result = [{'market': args.market, 'valid': is_valid}]
                self.cli.format_output(result, args.output_format, args.output_file)
                return 0
                
            elif action == 'sync-history':
                # Use SyncHistoryManager
                if not args.markets:
                    self.cli.logger.error("--markets is required")
                    return 1
                
                sync_history_manager = self.cli.sync_history_manager
                if not sync_history_manager:
                    self.cli.logger.error("SyncHistoryManager not initialized")
                    return 1
                
                markets_list = [m.strip() for m in args.markets.split(',')]
                results = await sync_history_manager.sync_36_months(markets_list)
                
                sync_data = [
                    {
                        'market': market,
                        'status': self.cli.safe_get(result, 'status', 'unknown'),
                        'final_status': self.cli.safe_get(result, 'final_status', 'unknown')
                    }
                    for market, result in results.items()
                ]
                self.cli.format_output(sync_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'sync-status':
                # Check sync status
                if not args.market:
                    self.cli.logger.error("--market is required")
                    return 1
                
                # Use BacktestAPI to check status
                from ...api.backtest.backtest_api import BacktestAPI
                status = await self.cli.backtest_api.get_history_status(args.market)
                status_data = [{'market': args.market, 'status': status}]
                self.cli.format_output(status_data, args.output_format, args.output_file)
                return 0
                
            else:
                self.cli.logger.error(f"Unknown market action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing market command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

