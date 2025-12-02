"""
Signal API module for pyHaasAPI v2

Provides signal management functionality for webhook signals and signal operations.
"""

from typing import Optional, Dict, Any, List

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import APIError
from ...core.logging import get_logger
from ...core.field_utils import safe_get_field, safe_get_success_flag


class SignalAPI:
    """
    Signal API for signal management operations
    
    Provides functionality for storing, retrieving, and pushing signals
    via webhooks.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("signal_api")
    
    async def store_signal(
        self,
        signal_id: str,
        secret: str,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use this webhook to send signals to the HaasCloud
        
        Args:
            signal_id: Signal ID
            secret: Secret key for authentication
            signal: Signal data dictionary
            
        Returns:
            Dictionary with storage result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/SignalAPI.php",
                data={
                    "channel": "STORE_SIGNAL",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "id": signal_id,
                    "secret": secret,
                    "signal": signal
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to store signal")
                raise APIError(f"Failed to store signal: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to store signal: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to store signal: {e}")
    
    async def my_signals(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all the user's signals
        
        Returns:
            List of signal dictionaries
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/SignalAPI.php",
                data={
                    "channel": "MY_SIGNALS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get signals")
                raise APIError(f"Failed to get signals: {error_msg}")
            
            data = safe_get_field(response, "Data", [])
            return data if isinstance(data, list) else []
            
        except Exception as e:
            self.logger.error(f"Failed to get signals: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get signals: {e}")
    
    async def push_signal(
        self,
        signal_id: str,
        action: str,
        investment_type: str,
        amount: float,
        max_lag: int,
        timestamp: int
    ) -> Dict[str, Any]:
        """
        Push a signal to the system
        
        Args:
            signal_id: Signal ID
            action: Action type
            investment_type: Investment type
            amount: Amount
            max_lag: Maximum lag
            timestamp: Timestamp
            
        Returns:
            Dictionary with push result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/SignalAPI.php",
                data={
                    "channel": "PUSH_SIGNAL",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "id": signal_id,
                    "action": action,
                    "investmenttype": investment_type,
                    "amount": amount,
                    "maxlag": max_lag,
                    "timestamp": timestamp
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to push signal")
                raise APIError(f"Failed to push signal: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to push signal: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to push signal: {e}")




