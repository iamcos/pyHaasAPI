"""
Trading API module for pyHaasAPI v2

Provides trading functionality including order placement, cancellation,
margin calculations, and order management.
"""

from typing import Optional, Dict, Any

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import APIError
from ...core.logging import get_logger
from ...core.field_utils import safe_get_field, safe_get_success_flag


class TradingAPI:
    """
    Trading API for trading operations
    
    Provides functionality for placing orders, canceling orders,
    calculating margins, and managing orders.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("trading_api")
    
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Places an order
        
        Args:
            order: Order data dictionary
            
        Returns:
            Dictionary with order placement result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/TradingAPI.php",
                data={
                    "channel": "PLACE_ORDER",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "order": order
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to place order")
                raise APIError(f"Failed to place order: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to place order: {e}")
    
    async def cancel_order(
        self,
        account_id: str,
        order_id: str
    ) -> Dict[str, Any]:
        """
        Cancels an open order
        
        Args:
            account_id: Account ID
            order_id: Order ID to cancel
            
        Returns:
            Dictionary with cancellation result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/TradingAPI.php",
                data={
                    "channel": "CANCEL_ORDER",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "accountid": account_id,
                    "orderid": order_id
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to cancel order")
                raise APIError(f"Failed to cancel order: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to cancel order: {e}")
    
    async def used_margin(
        self,
        driver_name: str,
        driver_type: int,
        market: str,
        leverage: float,
        price: float,
        amount: float
    ) -> Dict[str, Any]:
        """
        Returns what the used margin is
        
        Args:
            driver_name: Driver name
            driver_type: Driver type
            market: Name of the market, like BINANCE_BTC_USDT_
            leverage: Leverage value
            price: Price
            amount: Amount
            
        Returns:
            Dictionary with used margin calculation
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/TradingAPI.php",
                data={
                    "channel": "USED_MARGIN",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "drivername": driver_name,
                    "drivertype": driver_type,
                    "market": market,
                    "leverage": leverage,
                    "price": price,
                    "amount": amount
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to calculate used margin")
                raise APIError(f"Failed to calculate used margin: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to calculate used margin: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to calculate used margin: {e}")
    
    async def max_amount(
        self,
        account_id: str,
        market: str,
        price: float,
        used_amount: float,
        amount_percentage: float,
        is_buy: bool
    ) -> Dict[str, Any]:
        """
        Calculates the maximum trade amount, price and margin
        
        Args:
            account_id: Account ID
            market: Name of the market, like BINANCE_BTC_USDT_
            price: Price
            used_amount: Used amount
            amount_percentage: Amount percentage
            is_buy: Whether this is a buy order
            
        Returns:
            Dictionary with maximum amount calculation
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/TradingAPI.php",
                data={
                    "channel": "MAX_AMOUNT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "accountid": account_id,
                    "market": market,
                    "price": price,
                    "usedamount": used_amount,
                    "amountpercentage": amount_percentage,
                    "isbuy": is_buy
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to calculate max amount")
                raise APIError(f"Failed to calculate max amount: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to calculate max amount: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to calculate max amount: {e}")
    
    async def cancel_all_open_orders(
        self,
        account_id: Optional[str] = None,
        market: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancels all open orders, accountid and market are optional
        
        Args:
            account_id: Optional account ID to filter
            market: Optional market to filter (Name of the market, like BINANCE_BTC_USDT_)
            
        Returns:
            Dictionary with cancellation result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            data = {
                "channel": "CANCEL_ALL_OPEN_ORDERS",
                "userid": session.user_id,
                "interfacekey": session.interface_key
            }
            
            if account_id:
                data["accountid"] = account_id
            if market:
                data["market"] = market
            
            response = await self.client.post_json(
                "/TradingAPI.php",
                data=data
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to cancel all open orders")
                raise APIError(f"Failed to cancel all open orders: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to cancel all open orders: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to cancel all open orders: {e}")




