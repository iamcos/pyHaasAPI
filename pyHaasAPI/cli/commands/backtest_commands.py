"""
Backtest command handlers - Direct calls to BacktestAPI/BacktestService
"""

from typing import Any
from ..base import BaseCLI


class BacktestCommands:
    """Backtest command handlers - thin wrappers around BacktestAPI/BacktestService"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle backtest commands"""
        backtest_api = self.cli.backtest_api
        
        if not backtest_api:
            self.cli.logger.error("Backtest API not initialized")
            return 1
        
        try:
            if action == 'list':
                # Direct API call
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                backtests = await backtest_api.get_all_backtests_for_lab(args.lab_id)
                self.cli.format_output(backtests, args.output_format, args.output_file)
                return 0
                
            elif action == 'run':
                # Use BacktestService if available, otherwise API
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                # Direct API call to start backtest
                result = await backtest_api.start_backtest(args.lab_id)
                result_data = [{'lab_id': args.lab_id, 'job_id': result}]
                self.cli.format_output(result_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'results':
                # Direct API call
                if not args.backtest_id:
                    self.cli.logger.error("--backtest-id is required")
                    return 1
                
                result = await backtest_api.get_backtest_result(args.backtest_id)
                self.cli.format_output([result], args.output_format, args.output_file)
                return 0
                
            elif action == 'chart':
                # Direct API call
                if not args.backtest_id:
                    self.cli.logger.error("--backtest-id is required")
                    return 1
                
                chart_data = await backtest_api.get_backtest_chart(args.backtest_id)
                self.cli.format_output([chart_data], args.output_format, args.output_file)
                return 0
                
            elif action == 'log':
                # Direct API call
                if not args.backtest_id:
                    self.cli.logger.error("--backtest-id is required")
                    return 1
                
                log_data = await backtest_api.get_backtest_log(args.backtest_id)
                self.cli.format_output([log_data], args.output_format, args.output_file)
                return 0
                
            elif action == 'longest':
                # Use BacktestingManager
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                backtesting_manager = self.cli.backtesting_manager
                if not backtesting_manager:
                    self.cli.logger.error("BacktestingManager not initialized")
                    return 1
                
                result = await backtesting_manager.run_longest_backtest(
                    lab_id=args.lab_id,
                    max_iterations=args.max_iterations if hasattr(args, 'max_iterations') else 1500,
                    timeout=args.timeout if hasattr(args, 'timeout') else None
                )
                
                result_data = [{
                    'lab_id': result.lab_id,
                    'backtest_id': result.backtest_id,
                    'status': result.status.value if hasattr(result.status, 'value') else str(result.status),
                    'execution_time': result.execution_time,
                    'total_generations': result.total_generations,
                    'convergence_achieved': result.convergence_achieved
                }]
                self.cli.format_output(result_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'monitor':
                # Monitor backtest progress
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                backtesting_manager = self.cli.backtesting_manager
                if not backtesting_manager:
                    self.cli.logger.error("BacktestingManager not initialized")
                    return 1
                
                # Get progress from active backtests
                if args.lab_id in backtesting_manager.active_backtests:
                    progress = backtesting_manager.active_backtests[args.lab_id]
                    progress_data = [{
                        'lab_id': args.lab_id,
                        'status': progress.status.value if hasattr(progress.status, 'value') else str(progress.status),
                        'current_generation': progress.current_generation,
                        'current_epoch': progress.current_epoch,
                        'progress_percent': progress.progress_percent
                    }]
                    self.cli.format_output(progress_data, args.output_format, args.output_file)
                    return 0
                else:
                    self.cli.logger.warning(f"No active backtest found for lab {args.lab_id}")
                    return 1
                    
            elif action == 'cancel':
                # Cancel backtest
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                backtesting_manager = self.cli.backtesting_manager
                if not backtesting_manager:
                    self.cli.logger.error("BacktestingManager not initialized")
                    return 1
                
                success = await backtesting_manager.cancel_backtest(args.lab_id)
                if success:
                    self.cli.logger.info(f"Backtest for lab {args.lab_id} cancelled")
                    return 0
                else:
                    self.cli.logger.error("Failed to cancel backtest")
                    return 1
                    
            else:
                self.cli.logger.error(f"Unknown backtest action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing backtest command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

