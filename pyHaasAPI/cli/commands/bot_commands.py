"""
Bot command handlers - Direct calls to BotService/BotAPI
"""

from typing import Any
from ..base import BaseCLI


class BotCommands:
    """Bot command handlers - thin wrappers around BotService/BotAPI"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle bot commands"""
        bot_service = self.cli.bot_service
        bot_api = self.cli.bot_api
        
        if not bot_service or not bot_api:
            self.cli.logger.error("Bot service/API not initialized")
            return 1
        
        try:
            if action == 'list':
                # Direct API call - BotAPI.get_all_bots() returns List[BotDetails]
                bots = await bot_api.get_all_bots()
                
                # Filter by status if specified - use BotAPI helper methods
                if args.status:
                    if args.status == 'active':
                        bots = await bot_api.get_active_bots()
                    elif args.status == 'inactive':
                        bots = await bot_api.get_inactive_bots()
                    elif args.status == 'paused':
                        bots = await bot_api.get_paused_bots()
                    # Otherwise use all bots
                
                self.cli.format_output(bots, args.output_format, args.output_file)
                return 0
                
            elif action == 'create':
                # Use BotService.create_bot_from_lab_analysis
                if not args.from_lab:
                    self.cli.logger.error("--from-lab is required for bot creation")
                    return 1
                
                if not args.backtest_id:
                    self.cli.logger.error("--backtest-id is required for bot creation")
                    return 1
                
                if not args.account_id:
                    self.cli.logger.error("--account-id is required for bot creation")
                    return 1
                
                # Get lab details for lab_name
                lab_api = self.cli.lab_api
                lab_details = await lab_api.get_lab_details(args.from_lab)
                lab_name = self.cli.safe_get(lab_details, 'name', f'Lab {args.from_lab}')
                
                # Create bot using BotService
                bot_result = await bot_service.create_bot_from_lab_analysis(
                    lab_id=args.from_lab,
                    backtest_id=args.backtest_id,
                    account_id=args.account_id,
                    bot_name=args.name if hasattr(args, 'name') and args.name else None,
                    trade_amount_usdt=args.trade_amount if hasattr(args, 'trade_amount') and args.trade_amount else 2000.0,
                    leverage=20.0,
                    activate=args.activate if hasattr(args, 'activate') else False,
                    lab_name=lab_name
                )
                
                result_data = [{
                    'bot_id': bot_result.bot_id,
                    'bot_name': bot_result.bot_name,
                    'lab_id': args.from_lab,
                    'backtest_id': args.backtest_id,
                    'account_id': args.account_id,
                    'status': 'created'
                }]
                self.cli.format_output(result_data, args.output_format, args.output_file)
                return 0
                    
            elif action == 'delete':
                # Direct API call
                if not args.bot_id:
                    self.cli.logger.error("--bot-id is required")
                    return 1
                
                success = await bot_api.delete_bot(args.bot_id)
                if success:
                    self.cli.logger.info(f"Bot {args.bot_id} deleted")
                    return 0
                else:
                    self.cli.logger.error("Failed to delete bot")
                    return 1
                    
            elif action == 'activate':
                # Direct API call (BotAPI has activate_bot singular, loop for multiple)
                bot_ids = []
                if args.bot_ids:
                    bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
                elif args.bot_id:
                    bot_ids = [args.bot_id]
                else:
                    self.cli.logger.error("--bot-id or --bot-ids is required")
                    return 1
                
                activated = []
                for bot_id in bot_ids:
                    try:
                        bot = await bot_api.activate_bot(bot_id)
                        activated.append(bot)
                    except Exception as e:
                        self.cli.logger.error(f"Failed to activate bot {bot_id}: {e}")
                
                if activated:
                    self.cli.logger.info(f"Activated {len(activated)} bots")
                    self.cli.format_output(activated, args.output_format, args.output_file)
                    return 0
                else:
                    self.cli.logger.error("Failed to activate any bots")
                    return 1
                    
            elif action == 'deactivate':
                # Direct API call (BotAPI has deactivate_bot singular, loop for multiple)
                bot_ids = []
                if args.bot_ids:
                    bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
                elif args.bot_id:
                    bot_ids = [args.bot_id]
                else:
                    self.cli.logger.error("--bot-id or --bot-ids is required")
                    return 1
                
                deactivated = []
                for bot_id in bot_ids:
                    try:
                        bot = await bot_api.deactivate_bot(bot_id)
                        deactivated.append(bot)
                    except Exception as e:
                        self.cli.logger.error(f"Failed to deactivate bot {bot_id}: {e}")
                
                if deactivated:
                    self.cli.logger.info(f"Deactivated {len(deactivated)} bots")
                    self.cli.format_output(deactivated, args.output_format, args.output_file)
                    return 0
                else:
                    self.cli.logger.error("Failed to deactivate any bots")
                    return 1
                    
            elif action == 'pause':
                # Direct API call (BotAPI has pause_bot singular, loop for multiple)
                bot_ids = []
                if args.bot_ids:
                    bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
                elif args.bot_id:
                    bot_ids = [args.bot_id]
                else:
                    self.cli.logger.error("--bot-id or --bot-ids is required")
                    return 1
                
                paused = []
                for bot_id in bot_ids:
                    try:
                        bot = await bot_api.pause_bot(bot_id)
                        paused.append(bot)
                    except Exception as e:
                        self.cli.logger.error(f"Failed to pause bot {bot_id}: {e}")
                
                if paused:
                    self.cli.logger.info(f"Paused {len(paused)} bots")
                    self.cli.format_output(paused, args.output_format, args.output_file)
                    return 0
                else:
                    self.cli.logger.error("Failed to pause any bots")
                    return 1
                    
            elif action == 'resume':
                # Direct API call (BotAPI has resume_bot singular, loop for multiple)
                bot_ids = []
                if args.bot_ids:
                    bot_ids = [bid.strip() for bid in args.bot_ids.split(',')]
                elif args.bot_id:
                    bot_ids = [args.bot_id]
                else:
                    self.cli.logger.error("--bot-id or --bot-ids is required")
                    return 1
                
                resumed = []
                for bot_id in bot_ids:
                    try:
                        bot = await bot_api.resume_bot(bot_id)
                        resumed.append(bot)
                    except Exception as e:
                        self.cli.logger.error(f"Failed to resume bot {bot_id}: {e}")
                
                if resumed:
                    self.cli.logger.info(f"Resumed {len(resumed)} bots")
                    self.cli.format_output(resumed, args.output_format, args.output_file)
                    return 0
                else:
                    self.cli.logger.error("Failed to resume any bots")
                    return 1
                    
            else:
                self.cli.logger.error(f"Unknown bot action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing bot command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1

