"""
Portfolio API module for pyHaasAPI v2

Provides portfolio management functionality including currency conversion,
balance mutations, and tick data retrieval.
"""

from typing import Optional, List, Dict, Any

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import APIError
from ...core.logging import get_logger
from ...core.field_utils import safe_get_field, safe_get_success_flag


class PortfolioAPI:
    """
    Portfolio API for portfolio management operations
    
    Provides functionality for currency conversion, balance mutations,
    and tick data retrieval.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("portfolio_api")
    
    async def convert(
        self,
        price_source: str,
        from_currency: str,
        to_currency: str,
        amount: float,
        timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Returns the wallet and total balance after currency conversion
        
        Args:
            price_source: Name of the pricesource, like BINANCE
            from_currency: Source currency
            to_currency: Target currency
            amount: Amount to convert
            timestamp: Optional timestamp for historical conversion
            
        Returns:
            Dictionary with conversion result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            data = {
                "channel": "CONVERT",
                "userid": session.user_id,
                "interfacekey": session.interface_key,
                "pricesource": price_source,
                "fromcurrency": from_currency,
                "tocurrency": to_currency,
                "amount": amount
            }
            
            if timestamp is not None:
                data["timestamp"] = timestamp
            
            response = await self.client.post_json(
                "/PortfolioAPI.php",
                data=data
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to convert currency")
                raise APIError(f"Failed to convert currency: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to convert currency: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to convert currency: {e}")
    
    async def get_balance_mutations(
        self,
        account_ids: Optional[List[str]] = None,
        next_page_id: int = 0,
        page_length: int = 100
    ) -> Dict[str, Any]:
        """
        Returns the balance mutation per user
        
        Args:
            account_ids: Optional list of account IDs to filter
            next_page_id: Page ID for pagination (0 for first page)
            page_length: Number of results per page
            
        Returns:
            Dictionary with paginated balance mutations
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            data = {
                "channel": "GET_BALANCE_MUTATIONS",
                "userid": session.user_id,
                "interfacekey": session.interface_key,
                "nextpageid": next_page_id,
                "pagelength": page_length
            }
            
            if account_ids:
                data["accountids"] = account_ids
            
            response = await self.client.post_json(
                "/PortfolioAPI.php",
                data=data
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get balance mutations")
                raise APIError(f"Failed to get balance mutations: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get balance mutations: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get balance mutations: {e}")
    
    async def get_ticks(self) -> Dict[str, Any]:
        """
        Returns the tick data
        
        Returns:
            Dictionary with tick data
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/PortfolioAPI.php",
                data={
                    "channel": "GET_TICKS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get ticks")
                raise APIError(f"Failed to get ticks: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get ticks: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get ticks: {e}")
    
    async def get_range(
        self,
        market: str,
        start_unix: int,
        end_unix: int
    ) -> Dict[str, Any]:
        """
        Returns the range data for a market
        
        Args:
            market: Name of the market, like BINANCE_BTC_USDT_
            start_unix: Start Unix timestamp
            end_unix: End Unix timestamp
            
        Returns:
            Dictionary with range data
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/PortfolioAPI.php",
                data={
                    "channel": "GET_RANGE",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "market": market,
                    "startunix": start_unix,
                    "endunix": end_unix
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get range")
                raise APIError(f"Failed to get range: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get range: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get range: {e}")




