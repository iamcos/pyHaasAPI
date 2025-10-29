"""
Order API for pyHaasAPI v2

This module provides comprehensive order management functionality including
placing, canceling, and monitoring orders across accounts and bots.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import OrderError, OrderNotFoundError, OrderExecutionError
from ...core.logging import get_logger
from ...models.order import (
    Order, OrderDetails, OrderStatus, OrderType, OrderSide, TimeInForce,
    PlaceOrderRequest, CancelOrderRequest, OrderHistoryRequest
)
from ...models.common import PaginatedResponse

logger = get_logger("order_api")


class OrderAPI:
    """
    Order API for managing trading orders.

    Provides comprehensive order functionality including placement,
    cancellation, monitoring, and history tracking.
    """

    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("order_api")

    async def place_order(
        self,
        account_id: str,
        market: str,
        side: str,
        price: float,
        amount: float,
        order_type: int = 0,
        tif: int = 0,
        source: str = "Manual"
    ) -> str:
        """
        Place an order.

        Args:
            account_id: Account ID
            market: Market identifier
            side: Order side ("buy" or "sell")
            price: Order price
            amount: Order amount
            order_type: Order type (0=limit, 1=market)
            tif: Time in force (0=GTC, 1=IOC, 2=FOK)
            source: Order source

        Returns:
            Order ID if successful

        Raises:
            OrderExecutionError: If the order placement fails
        """
        try:
            self.logger.info(f"Placing {side} order for {amount} {market} at {price}")
            
            response = await self.client.execute(
                endpoint="Account",
                query_params={
                    "channel": "PLACE_ORDER",
                    "accountid": account_id,
                    "market": market,
                    "side": side,
                    "price": price,
                    "amount": amount,
                    "ordertype": order_type,
                    "tif": tif,
                    "source": source,
                }
            )
            
            if isinstance(response, str):
                self.logger.info(f"✅ Order placed successfully: {response}")
                return response
            else:
                raise OrderExecutionError(f"Unexpected response format: {response}")
                
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            raise OrderExecutionError(f"Failed to place order: {e}") from e

    async def place_order_with_request(
        self, 
        request: PlaceOrderRequest
    ) -> str:
        """
        Place an order using a structured request object.

        Args:
            request: PlaceOrderRequest with all order parameters

        Returns:
            Order ID if successful

        Raises:
            OrderExecutionError: If the order placement fails
        """
        try:
            return await self.place_order(
                account_id=request.account_id,
                market=request.market,
                side=request.side,
                price=request.price,
                amount=request.amount,
                order_type=request.order_type,
                tif=request.tif,
                source=request.source
            )
            
        except OrderExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to place order with request: {e}")
            raise OrderExecutionError(f"Failed to place order: {e}") from e

    async def cancel_order(
        self, 
        account_id: str, 
        order_id: str
    ) -> bool:
        """
        Cancel a specific order.

        Args:
            account_id: Account ID
            order_id: Order ID to cancel

        Returns:
            True if successful, False otherwise

        Raises:
            OrderError: If the order cancellation fails
        """
        try:
            self.logger.info(f"Canceling order {order_id} for account {account_id}")
            
            response = await self.client.execute(
                endpoint="Account",
                query_params={
                    "channel": "CANCEL_ORDER",
                    "accountid": account_id,
                    "orderid": order_id,
                }
            )
            
            success = bool(response)
            if success:
                self.logger.info(f"✅ Order {order_id} canceled successfully")
            else:
                self.logger.warning(f"⚠️ Order {order_id} cancellation returned false")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            raise OrderError(f"Failed to cancel order {order_id}: {e}") from e

    async def cancel_order_with_request(
        self, 
        request: CancelOrderRequest
    ) -> bool:
        """
        Cancel an order using a structured request object.

        Args:
            request: CancelOrderRequest with order details

        Returns:
            True if successful, False otherwise

        Raises:
            OrderError: If the order cancellation fails
        """
        try:
            return await self.cancel_order(
                account_id=request.account_id,
                order_id=request.order_id
            )
            
        except OrderError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to cancel order with request: {e}")
            raise OrderError(f"Failed to cancel order: {e}") from e

    async def get_order_status(
        self, 
        account_id: str, 
        order_id: str
    ) -> OrderStatus:
        """
        Get the status of a specific order.

        Args:
            account_id: Account ID
            order_id: Order ID to check

        Returns:
            OrderStatus with current order information

        Raises:
            OrderNotFoundError: If the order is not found
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting status for order {order_id}")
            
            # Get all orders for the account and find the specific one
            orders = await self.get_account_orders(account_id)
            
            for order_data in orders:
                if order_data.get('OrderId') == order_id:
                    return OrderStatus.model_validate(order_data)
            
            raise OrderNotFoundError(f"Order {order_id} not found")
            
        except OrderNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get order status: {e}")
            raise OrderError(f"Failed to get status for order {order_id}: {e}") from e

    async def get_order_history(
        self, 
        request: OrderHistoryRequest
    ) -> List[Order]:
        """
        Get order history with filtering options.

        Args:
            request: OrderHistoryRequest with filtering parameters

        Returns:
            List of Order objects matching the criteria

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info("Getting order history")
            
            # This would typically call a dedicated history endpoint
            # For now, we'll use the existing orders endpoint with filtering
            all_orders = await self.get_all_orders()
            
            # Filter orders based on request criteria
            filtered_orders = []
            for order_data in all_orders:
                order = Order.model_validate(order_data)
                
                # Apply filters
                if request.account_id and order.account_id != request.account_id:
                    continue
                if request.market and order.market != request.market:
                    continue
                if request.side and order.side != request.side:
                    continue
                if request.start_date and order.timestamp < request.start_date:
                    continue
                if request.end_date and order.timestamp > request.end_date:
                    continue
                
                filtered_orders.append(order)
            
            # Sort by timestamp (newest first)
            filtered_orders.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            if request.limit:
                filtered_orders = filtered_orders[:request.limit]
            
            self.logger.info(f"Retrieved {len(filtered_orders)} orders from history")
            return filtered_orders
            
        except Exception as e:
            self.logger.error(f"Failed to get order history: {e}")
            raise OrderError(f"Failed to get order history: {e}") from e

    async def get_all_orders(self) -> List[Dict[str, Any]]:
        """
        Get all orders across all accounts.

        Returns:
            List of order dictionaries

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info("Getting all orders across all accounts")
            
            response = await self.client.get_json(
                endpoint="Account",
                params={
                    "channel": "GET_ALL_ORDERS",
                }
            )
            
            orders = response if isinstance(response, list) else []
            self.logger.info(f"Retrieved {len(orders)} orders")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get all orders: {e}")
            raise OrderError(f"Failed to get all orders: {e}") from e

    async def get_account_orders(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get open orders for a specific account.

        Args:
            account_id: Account ID

        Returns:
            List of order dictionaries

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting orders for account {account_id}")
            
            response = await self.client.get_json(
                endpoint="Account",
                params={
                    "channel": "GET_ORDERS",
                    "accountid": account_id,
                }
            )
            
            # Extract orders from response (typically under 'I' key)
            orders = []
            if isinstance(response, dict) and 'I' in response:
                orders = response['I'] if isinstance(response['I'], list) else []
            elif isinstance(response, list):
                orders = response
            
            self.logger.info(f"Retrieved {len(orders)} orders for account {account_id}")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get account orders: {e}")
            raise OrderError(f"Failed to get orders for account {account_id}: {e}") from e

    async def get_account_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """
        Get open positions for a specific account.

        Args:
            account_id: Account ID

        Returns:
            List of position dictionaries

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting positions for account {account_id}")
            
            response = await self.client.get_json(
                endpoint="Account",
                params={
                    "channel": "GET_POSITIONS",
                    "accountid": account_id,
                }
            )
            
            # Extract positions from response (typically under 'I' key)
            positions = []
            if isinstance(response, dict) and 'I' in response:
                positions = response['I'] if isinstance(response['I'], list) else []
            elif isinstance(response, list):
                positions = response
            
            self.logger.info(f"Retrieved {len(positions)} positions for account {account_id}")
            return positions
            
        except Exception as e:
            self.logger.error(f"Failed to get account positions: {e}")
            raise OrderError(f"Failed to get positions for account {account_id}: {e}") from e

    # Bot-specific order operations

    async def get_bot_orders(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get all open orders for a specific bot.

        Args:
            bot_id: ID of the bot to get orders for

        Returns:
            List of order dictionaries

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting orders for bot {bot_id}")
            
            response = await self.client.execute(
                endpoint="Bot",
                query_params={
                    "channel": "GET_BOT_ORDERS",
                    "botid": bot_id,
                }
            )
            
            orders = response if isinstance(response, list) else []
            self.logger.info(f"Retrieved {len(orders)} orders for bot {bot_id}")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get bot orders: {e}")
            raise OrderError(f"Failed to get orders for bot {bot_id}: {e}") from e

    async def get_bot_positions(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get all positions for a specific bot.

        Args:
            bot_id: ID of the bot to get positions for

        Returns:
            List of position dictionaries

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting positions for bot {bot_id}")
            
            response = await self.client.execute(
                endpoint="Bot",
                query_params={
                    "channel": "GET_BOT_POSITIONS",
                    "botid": bot_id,
                }
            )
            
            positions = response if isinstance(response, list) else []
            self.logger.info(f"Retrieved {len(positions)} positions for bot {bot_id}")
            return positions
            
        except Exception as e:
            self.logger.error(f"Failed to get bot positions: {e}")
            raise OrderError(f"Failed to get positions for bot {bot_id}: {e}") from e

    async def cancel_bot_order(self, bot_id: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel a specific order for a bot.

        Args:
            bot_id: ID of the bot
            order_id: ID of the order to cancel

        Returns:
            Cancellation result dictionary

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Canceling order {order_id} for bot {bot_id}")
            
            response = await self.client.execute(
                endpoint="Bot",
                query_params={
                    "channel": "CANCEL_BOT_ORDER",
                    "botid": bot_id,
                    "orderid": order_id,
                }
            )
            
            self.logger.info(f"✅ Order {order_id} canceled for bot {bot_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to cancel bot order: {e}")
            raise OrderError(f"Failed to cancel order {order_id} for bot {bot_id}: {e}") from e

    async def cancel_all_bot_orders(self, bot_id: str) -> Dict[str, Any]:
        """
        Cancel all orders for a specific bot.

        Args:
            bot_id: ID of the bot

        Returns:
            Cancellation result dictionary

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Canceling all orders for bot {bot_id}")
            
            response = await self.client.execute(
                endpoint="Bot",
                query_params={
                    "channel": "CANCEL_ALL_BOT_ORDERS",
                    "botid": bot_id,
                }
            )
            
            self.logger.info(f"✅ All orders canceled for bot {bot_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to cancel all bot orders: {e}")
            raise OrderError(f"Failed to cancel all orders for bot {bot_id}: {e}") from e

    # Utility methods for order management

    async def get_orders_by_market(
        self, 
        market: str, 
        account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all orders for a specific market.

        Args:
            market: Market identifier
            account_id: Optional account ID to filter by

        Returns:
            List of order dictionaries for the market

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting orders for market {market}")
            
            if account_id:
                orders = await self.get_account_orders(account_id)
            else:
                orders = await self.get_all_orders()
            
            # Filter by market
            market_orders = [
                order for order in orders 
                if order.get('Market') == market or order.get('market') == market
            ]
            
            self.logger.info(f"Retrieved {len(market_orders)} orders for market {market}")
            return market_orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders by market: {e}")
            raise OrderError(f"Failed to get orders for market {market}: {e}") from e

    async def get_orders_by_status(
        self, 
        status: str, 
        account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all orders with a specific status.

        Args:
            status: Order status to filter by
            account_id: Optional account ID to filter by

        Returns:
            List of order dictionaries with the specified status

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting orders with status {status}")
            
            if account_id:
                orders = await self.get_account_orders(account_id)
            else:
                orders = await self.get_all_orders()
            
            # Filter by status
            status_orders = [
                order for order in orders 
                if order.get('Status') == status or order.get('status') == status
            ]
            
            self.logger.info(f"Retrieved {len(status_orders)} orders with status {status}")
            return status_orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders by status: {e}")
            raise OrderError(f"Failed to get orders with status {status}: {e}") from e

    async def cancel_orders_by_market(
        self, 
        market: str, 
        account_id: str
    ) -> List[bool]:
        """
        Cancel all orders for a specific market and account.

        Args:
            market: Market identifier
            account_id: Account ID

        Returns:
            List of boolean results for each cancellation

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Canceling all orders for market {market} in account {account_id}")
            
            # Get orders for the market
            orders = await self.get_orders_by_market(market, account_id)
            
            # Cancel each order
            results = []
            for order in orders:
                order_id = order.get('OrderId') or order.get('orderId')
                if order_id:
                    try:
                        result = await self.cancel_order(account_id, order_id)
                        results.append(result)
                    except Exception as e:
                        self.logger.warning(f"Failed to cancel order {order_id}: {e}")
                        results.append(False)
            
            successful_cancellations = sum(results)
            self.logger.info(f"Canceled {successful_cancellations}/{len(orders)} orders for market {market}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to cancel orders by market: {e}")
            raise OrderError(f"Failed to cancel orders for market {market}: {e}") from e

    async def get_order_summary(self, account_id: str) -> Dict[str, Any]:
        """
        Get a summary of orders for an account.

        Args:
            account_id: Account ID

        Returns:
            Dictionary with order summary statistics

        Raises:
            OrderError: If the API request fails
        """
        try:
            self.logger.info(f"Getting order summary for account {account_id}")
            
            orders = await self.get_account_orders(account_id)
            positions = await self.get_account_positions(account_id)
            
            # Calculate summary statistics
            total_orders = len(orders)
            total_positions = len(positions)
            
            # Count orders by status
            status_counts = {}
            for order in orders:
                status = order.get('Status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count orders by market
            market_counts = {}
            for order in orders:
                market = order.get('Market', 'Unknown')
                market_counts[market] = market_counts.get(market, 0) + 1
            
            summary = {
                'account_id': account_id,
                'total_orders': total_orders,
                'total_positions': total_positions,
                'orders_by_status': status_counts,
                'orders_by_market': market_counts,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Generated order summary for account {account_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get order summary: {e}")
            raise OrderError(f"Failed to get order summary for account {account_id}: {e}") from e
