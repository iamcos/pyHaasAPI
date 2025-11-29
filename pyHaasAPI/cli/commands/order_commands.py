"""
Order command handlers - Direct calls to OrderAPI
"""

from typing import Any
from ..base import BaseCLI


class OrderCommands:
    """Order command handlers - thin wrappers around OrderAPI"""
    
    def __init__(self, cli: BaseCLI):
        self.cli = cli
    
    async def handle(self, action: str, args: Any) -> int:
        """Handle order commands"""
        order_api = self.cli.order_api
        
        if not order_api:
            self.cli.logger.error("Order API not initialized")
            return 1
        
        try:
            if action == 'list':
                # Direct API call
                if args.bot_id:
                    orders = await order_api.get_bot_orders(args.bot_id)
                elif args.account_id:
                    orders = await order_api.get_account_orders(args.account_id)
                else:
                    orders = await order_api.get_all_orders()
                
                self.cli.format_output(orders, args.output_format, args.output_file)
                return 0
                
            elif action == 'place':
                # Direct API call - need account_id and market, not bot_id
                if not args.account_id or not args.market or not args.side or not args.amount:
                    self.cli.logger.error("--account-id, --market, --side, and --amount are required")
                    return 1
                
                from ...models.order import PlaceOrderRequest
                
                request = PlaceOrderRequest(
                    account_id=args.account_id,
                    market=args.market,
                    side=args.side.lower(),  # 'buy' or 'sell'
                    amount=args.amount,
                    price=args.price,
                    bot_id=args.bot_id if hasattr(args, 'bot_id') and args.bot_id else None
                )
                
                order_id = await order_api.place_order_with_request(request)
                result_data = [{'order_id': order_id, 'status': 'placed'}]
                self.cli.format_output(result_data, args.output_format, args.output_file)
                return 0
                
            elif action == 'cancel':
                # Direct API call
                if not args.order_id:
                    self.cli.logger.error("--order-id is required")
                    return 1
                
                from ...models.order import CancelOrderRequest
                
                request = CancelOrderRequest(order_id=args.order_id)
                result = await order_api.cancel_order_with_request(request)
                
                if result.success:
                    self.cli.logger.info(f"Order {args.order_id} cancelled")
                    return 0
                else:
                    self.cli.logger.error(f"Failed to cancel order: {result.error}")
                    return 1
                    
            elif action == 'status':
                # Direct API call
                if not args.order_id:
                    self.cli.logger.error("--order-id is required")
                    return 1
                
                order_details = await order_api.get_order_status(args.order_id)
                self.cli.format_output([order_details], args.output_format, args.output_file)
                return 0
                
            elif action == 'history':
                # Direct API call - use account_id or market filter
                if args.account_id:
                    orders = await order_api.get_account_orders(args.account_id)
                elif args.market:
                    # Filter by market if API supports it
                    all_orders = await order_api.get_all_orders()
                    orders = [o for o in all_orders if self.cli.safe_get(o, 'market', '') == args.market]
                else:
                    orders = await order_api.get_all_orders()
                
                # Apply limit if specified
                if args.top_count:
                    orders = orders[:args.top_count]
                
                self.cli.format_output(orders, args.output_format, args.output_file)
                return 0
                
            else:
                self.cli.logger.error(f"Unknown order action: {action}")
                return 1
                
        except Exception as e:
            self.cli.logger.error(f"Error executing order command: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1



