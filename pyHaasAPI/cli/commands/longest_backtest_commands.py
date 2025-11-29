"""
Longest backtest command handlers - Direct calls to LongestBacktestService
"""

from typing import Any
from ..base import BaseCLI


class LongestBacktestCommands:
    """Longest backtest command handlers - thin wrappers around LongestBacktestService"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle longest backtest commands"""
        # LongestBacktestService needs to be initialized
        from ...services.longest_backtest_service import LongestBacktestService
        
        longest_service = LongestBacktestService(
            lab_api=self.cli.lab_api,
            market_api=self.cli.market_api,
            backtest_api=self.cli.backtest_api,
            client=self.cli.client,
            auth_manager=self.cli.auth_manager
        )
        
        try:
            if action == 'find':
                # Find longest working period for a lab
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                start_unix, end_unix, period_name, success = await longest_service.find_longest_working_period(args.lab_id)
                
                if success:
                    result = {
                        'lab_id': args.lab_id,
                        'start_unix': start_unix,
                        'end_unix': end_unix,
                        'period_name': period_name,
                        'success': True
                    }
                    self.cli.format_output([result], args.output_format, args.output_file)
                    return 0
                else:
                    self.cli.logger.error(f"Failed to find longest period: {period_name}")
                    return 1
                    
            elif action == 'orchestrate':
                # Orchestrate clone, config, sync, and find cutoff
                if not args.lab_ids:
                    self.cli.logger.error("--lab-ids is required")
                    return 1
                
                if not args.account_id:
                    self.cli.logger.error("--account-id is required")
                    return 1
                
                lab_ids = [lid.strip() for lid in args.lab_ids.split(',')]
                markets = args.markets.split(',') if args.markets else []
                
                results = await longest_service.orchestrate_clone_config_sync_and_find_cutoff(
                    template_lab_id=lab_ids[0],
                    account_id=args.account_id,
                    stage_label=args.stage_label or 'test',
                    markets=markets
                )
                
                self.cli.format_output([results], args.output_format, args.output_file)
                return 0
                
            else:
                self.cli.logger.error(f"Unknown longest-backtest action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing longest-backtest command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1



