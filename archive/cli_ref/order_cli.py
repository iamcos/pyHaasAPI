"""
Order CLI module using v2 APIs and centralized managers.
Provides order management functionality.
"""

import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pyHaasAPI.cli_ref.base import EnhancedBaseCLI
from pyHaasAPI.core.logging import get_logger


class OrderCLI(EnhancedBaseCLI):
    """Order management CLI using v2 APIs and centralized managers"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger("order_cli")

    async def list_orders(self, account_id: str = None) -> Dict[str, Any]:
        """List orders for an account or all accounts"""
        try:
            if account_id:
                self.logger.info(f"Listing orders for account {account_id}")
            else:
                self.logger.info("Listing all orders")
            
            if not self.order_api:
                return {"error": "Order API not available"}
            
            if account_id:
                orders = await self.order_api.list_account_orders(account_id)
            else:
                orders = await self.order_api.list_all_orders()
            
            return {
                "success": True,
                "orders": orders,
                "count": len(orders) if orders else 0,
                "account_id": account_id
            }
            
        except Exception as e:
            self.logger.error(f"Error listing orders: {e}")
            return {"error": str(e)}

    async def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get order details"""
        try:
            self.logger.info(f"Getting order details for {order_id}")
            
            if not self.order_api:
                return {"error": "Order API not available"}
            
            order = await self.order_api.get_order_details(order_id)
            
            if order:
                return {
                    "success": True,
                    "order": order
                }
            else:
                return {
                    "success": False,
                    "error": f"Order {order_id} not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error getting order details: {e}")
            return {"error": str(e)}

    async def create_order(self, account_id: str, market_id: str, side: str, 
                          amount: float, price: float = None, order_type: str = "limit") -> Dict[str, Any]:
        """Create a new order"""
        try:
            self.logger.info(f"Creating {side} order for {amount} {market_id} at {price}")
            
            if not self.order_api:
                return {"error": "Order API not available"}
            
            order = await self.order_api.create_order(
                account_id=account_id,
                market_id=market_id,
                side=side,
                amount=amount,
                price=price,
                order_type=order_type
            )
            
            if order:
                return {
                    "success": True,
                    "order": order,
                    "message": f"Order created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create order"
                }
                
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return {"error": str(e)}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            self.logger.info(f"Cancelling order {order_id}")
            
            if not self.order_api:
                return {"error": "Order API not available"}
            
            success = await self.order_api.cancel_order(order_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Order {order_id} cancelled successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to cancel order {order_id}"
                }
                
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return {"error": str(e)}

    def print_orders_report(self, orders_data: Dict[str, Any]):
        """Print orders report"""
        try:
            if "error" in orders_data:
                print(f"❌ Error: {orders_data['error']}")
                return
            
            orders = orders_data.get("orders", [])
            count = orders_data.get("count", 0)
            account_id = orders_data.get("account_id")
            
            print("\n" + "="*80)
            print("📋 ORDERS REPORT")
            print("="*80)
            if account_id:
                print(f"🏦 Account ID: {account_id}")
            print(f"📊 Total Orders: {count}")
            print("-"*80)
            
            if orders:
                for order in orders:
                    order_id = getattr(order, 'id', 'Unknown')
                    market_id = getattr(order, 'market_id', 'Unknown')
                    side = getattr(order, 'side', 'Unknown')
                    amount = getattr(order, 'amount', 0)
                    price = getattr(order, 'price', 0)
                    status = getattr(order, 'status', 'Unknown')
                    
                    print(f"📋 {side.upper()} {amount} {market_id}")
                    print(f"   ID: {order_id}")
                    print(f"   Price: {price}")
                    print(f"   Status: {status}")
                    print()
            else:
                print("No orders found")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing orders report: {e}")
            print(f"❌ Error generating report: {e}")

    def print_order_details_report(self, order_data: Dict[str, Any]):
        """Print order details report"""
        try:
            if "error" in order_data:
                print(f"❌ Error: {order_data['error']}")
                return
            
            if not order_data.get("success", False):
                print(f"❌ {order_data.get('error', 'Unknown error')}")
                return
            
            order = order_data.get("order")
            if not order:
                print("❌ No order data available")
                return
            
            print("\n" + "="*80)
            print("📋 ORDER DETAILS")
            print("="*80)
            
            # Basic info
            order_id = getattr(order, 'id', 'Unknown')
            market_id = getattr(order, 'market_id', 'Unknown')
            side = getattr(order, 'side', 'Unknown')
            amount = getattr(order, 'amount', 0)
            price = getattr(order, 'price', 0)
            status = getattr(order, 'status', 'Unknown')
            
            print(f"📋 {side.upper()} {amount} {market_id}")
            print(f"   ID: {order_id}")
            print(f"   Price: {price}")
            print(f"   Status: {status}")
            
            # Additional details
            if hasattr(order, 'filled_amount'):
                print(f"   Filled Amount: {order.filled_amount}")
            if hasattr(order, 'remaining_amount'):
                print(f"   Remaining Amount: {order.remaining_amount}")
            if hasattr(order, 'created_at'):
                print(f"   Created: {order.created_at}")
            if hasattr(order, 'updated_at'):
                print(f"   Updated: {order.updated_at}")
            
            print("="*80)
            
        except Exception as e:
            self.logger.error(f"Error printing order details report: {e}")
            print(f"❌ Error generating report: {e}")


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Order Management CLI")
    parser.add_argument("--list", action="store_true", help="List all orders")
    parser.add_argument("--list-account", type=str, help="List orders for specific account")
    parser.add_argument("--details", type=str, help="Get order details by ID")
    parser.add_argument("--create", action="store_true", help="Create a new order")
    parser.add_argument("--cancel", type=str, help="Cancel order by ID")
    
    # Order creation arguments
    parser.add_argument("--account-id", type=str, help="Account ID for order creation")
    parser.add_argument("--market-id", type=str, help="Market ID for order creation")
    parser.add_argument("--side", type=str, choices=["buy", "sell"], help="Order side (buy/sell)")
    parser.add_argument("--amount", type=float, help="Order amount")
    parser.add_argument("--price", type=float, help="Order price (for limit orders)")
    parser.add_argument("--order-type", type=str, default="limit", choices=["limit", "market"], help="Order type")
    
    args = parser.parse_args()
    
    cli = OrderCLI()
    
    # Connect
    if not await cli.connect():
        print("❌ Failed to connect to APIs")
        return
    
    try:
        if args.list:
            # List all orders
            orders_data = await cli.list_orders()
            cli.print_orders_report(orders_data)
            
        elif args.list_account:
            # List orders for specific account
            orders_data = await cli.list_orders(args.list_account)
            cli.print_orders_report(orders_data)
            
        elif args.details:
            # Get order details
            order_data = await cli.get_order_details(args.details)
            cli.print_order_details_report(order_data)
            
        elif args.create:
            # Create new order
            if not all([args.account_id, args.market_id, args.side, args.amount]):
                print("❌ Missing required arguments for order creation")
                print("Required: --account-id, --market-id, --side, --amount")
                return
            
            order_data = await cli.create_order(
                account_id=args.account_id,
                market_id=args.market_id,
                side=args.side,
                amount=args.amount,
                price=args.price,
                order_type=args.order_type
            )
            
            if order_data.get("success"):
                print(f"✅ {order_data['message']}")
            else:
                print(f"❌ {order_data.get('error', 'Unknown error')}")
                
        elif args.cancel:
            # Cancel order
            cancel_data = await cli.cancel_order(args.cancel)
            if cancel_data.get("success"):
                print(f"✅ {cancel_data['message']}")
            else:
                print(f"❌ {cancel_data.get('error', 'Unknown error')}")
                
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())





