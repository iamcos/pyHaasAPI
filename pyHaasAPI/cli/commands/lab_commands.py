"""
Lab command handlers - Direct calls to LabService/LabAPI
"""

from typing import Any
from ..base import BaseCLI
from ...models.enumerations import map_lab_status_to_string


class LabCommands:
    """Lab command handlers - thin wrappers around LabService/LabAPI"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle lab commands"""
        # Get services (lazy-loaded)
        lab_service = self.cli.lab_service
        lab_api = self.cli.lab_api
        
        if not lab_service or not lab_api:
            self.cli.logger.error("Lab service/API not initialized")
            return 1
        
        try:
            if action == 'list':
                # Direct API call
                labs = await lab_api.get_labs()
                self.cli.format_output(labs, args.output_format, args.output_file)
                return 0
                
            elif action == 'create':
                # Direct API call
                if not args.name or not args.script_id:
                    self.cli.logger.error("--name and --script-id are required")
                    return 1
                
                lab = await lab_api.create_lab(
                    script_id=args.script_id,
                    name=args.name,
                    description=args.description or "" if hasattr(args, 'description') else ""
                )
                self.cli.format_output([lab], args.output_format, args.output_file)
                return 0
                
            elif action == 'delete':
                # Direct API call
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                success = await lab_api.delete_lab(args.lab_id)
                if success:
                    self.cli.logger.info(f"Lab {args.lab_id} deleted")
                    return 0
                else:
                    self.cli.logger.error("Failed to delete lab")
                    return 1
                    
            elif action == 'analyze':
                # Use AnalysisService (not LabService) - it has the analysis logic
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                analysis_service = self.cli.analysis_service
                if not analysis_service:
                    self.cli.logger.error("Analysis service not initialized")
                    return 1
                
                result = await analysis_service.analyze_lab_comprehensive(
                    lab_id=args.lab_id,
                    top_count=args.top_count,
                    min_win_rate=(args.min_winrate / 100.0) if args.min_winrate else 0.3,
                    min_trades=args.min_trades or 5,
                    sort_by=args.sort_by or 'roe'
                )
                
                # Format output using unified format_output
                top_performers_data = [
                    {
                        'lab_id': result.lab_id,
                        'lab_name': result.lab_name,
                        'backtest_id': bt.backtest_id,
                        'roi_percentage': bt.roi_percentage,
                        'win_rate': bt.win_rate,
                        'total_trades': bt.total_trades,
                        'realized_profits_usdt': bt.realized_profits_usdt
                    } for bt in result.top_performers
                ]
                self.cli.format_output(top_performers_data, args.output_format, args.output_file)
                
                return 0
                
            elif action == 'execute':
                # Use LabAPI.start_lab_execution or LabService.execute_lab_with_monitoring
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                # Get lab details first
                lab_details = await lab_api.get_lab_details(args.lab_id)
                if not lab_details:
                    self.cli.logger.error(f"Lab {args.lab_id} not found")
                    return 1
                
                # Use LabService.execute_lab_with_monitoring if available
                from ...models.lab import StartLabExecutionRequest
                from datetime import datetime
                
                # Use current time as default if not provided
                start_unix = int(datetime.now().timestamp()) - (30 * 24 * 3600)  # 30 days ago
                end_unix = int(datetime.now().timestamp())
                
                if hasattr(args, 'start_date') and args.start_date:
                    from datetime import datetime as dt
                    start_unix = int(dt.fromisoformat(args.start_date).timestamp())
                if hasattr(args, 'end_date') and args.end_date:
                    from datetime import datetime as dt
                    end_unix = int(dt.fromisoformat(args.end_date).timestamp())
                
                request = StartLabExecutionRequest(
                    lab_id=args.lab_id,
                    start_unix=start_unix,
                    end_unix=end_unix,
                    send_email=False
                )
                
                try:
                    response = await lab_api.start_lab_execution(request)
                    execution_id = self.cli.safe_get(self.cli.safe_get(response, 'Data', {}), 'ExecutionId', args.lab_id)
                    self.cli.logger.info(f"Lab execution started: {args.lab_id}, execution_id: {execution_id}")
                    result_data = [{'lab_id': args.lab_id, 'execution_id': execution_id, 'status': 'started'}]
                    self.cli.format_output(result_data, args.output_format, args.output_file)
                    return 0
                except Exception as e:
                    self.cli.logger.error(f"Failed to execute lab: {e}")
                    return 1
                    
            elif action == 'status':
                # Use LabAPI.get_lab_details to get status
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                lab_details = await lab_api.get_lab_details(args.lab_id)
                if not lab_details:
                    self.cli.logger.error(f"Lab {args.lab_id} not found")
                    return 1
                
                status_data = {
                    'lab_id': args.lab_id,
                    'name': self.cli.safe_get(lab_details, 'name', ''),
                    'status': self.cli.safe_get(lab_details, 'status', 0),
                    'status_string': map_lab_status_to_string(self.cli.safe_get(lab_details, 'status', 0)) if hasattr(lab_details, 'status') else 'unknown'
                }
                self.cli.format_output([status_data], args.output_format, args.output_file)
                return 0
                    
            elif action == 'clone':
                # Use LabCloneManager
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                if not args.markets:
                    self.cli.logger.error("--markets is required")
                    return 1
                
                if not args.account_id:
                    self.cli.logger.error("--account-id is required")
                    return 1
                
                if not args.stage_label:
                    self.cli.logger.error("--stage-label is required")
                    return 1
                
                lab_clone_manager = self.cli.lab_clone_manager
                if not lab_clone_manager:
                    self.cli.logger.error("LabCloneManager not initialized")
                    return 1
                
                # Parse markets
                markets_list = [m.strip() for m in args.markets.split(',')]
                # Create market dict (coin -> market_tag)
                target_markets = {}
                for market in markets_list:
                    # Extract coin from market tag if possible
                    coin = market.split('_')[1] if '_' in market else market
                    target_markets[coin] = market
                
                cloned_map = await lab_clone_manager.clone_to_markets(
                    template_lab_id=args.lab_id,
                    target_markets=target_markets,
                    account_id=args.account_id,
                    stage_label=args.stage_label
                )
                
                cloned_data = [
                    {'coin': coin, 'lab_id': lab_id}
                    for coin, lab_id in cloned_map.items()
                ]
                self.cli.format_output(cloned_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'rename':
                # Use LabConfigManager
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                if not args.new_name:
                    self.cli.logger.error("--new-name is required")
                    return 1
                
                lab_config_manager = self.cli.lab_config_manager
                if not lab_config_manager:
                    self.cli.logger.error("LabConfigManager not initialized")
                    return 1
                
                # Parse new_name for stage_label, coin, script_name
                # Format: stage_label_coin_script_name or just new_name
                success = await lab_config_manager.rename_lab(
                    lab_id=args.lab_id,
                    stage_label=args.stage_label or 'renamed',
                    coin=args.coin or 'UNKNOWN',
                    script_name=args.script_name or 'UNKNOWN',
                    cutoff_date=args.cutoff_date if hasattr(args, 'cutoff_date') else None
                )
                
                if success:
                    self.cli.logger.info(f"Lab {args.lab_id} renamed")
                    return 0
                else:
                    self.cli.logger.error("Failed to rename lab")
                    return 1
                    
            elif action == 'config':
                # Use LabConfigManager
                if not args.lab_id:
                    self.cli.logger.error("--lab-id is required")
                    return 1
                
                lab_config_manager = self.cli.lab_config_manager
                if not lab_config_manager:
                    self.cli.logger.error("LabConfigManager not initialized")
                    return 1
                
                if hasattr(args, 'trade_amount') and args.trade_amount:
                    success = await lab_config_manager.set_trade_amount_usdt_equivalent(
                        lab_id=args.lab_id,
                        trade_amount_usdt=args.trade_amount
                    )
                    if success:
                        self.cli.logger.info(f"Lab {args.lab_id} trade amount configured")
                        return 0
                    else:
                        self.cli.logger.error("Failed to configure lab")
                        return 1
                else:
                    self.cli.logger.error("--trade-amount is required for config action")
                    return 1
                    
            else:
                self.cli.logger.error(f"Unknown lab action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing lab command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

