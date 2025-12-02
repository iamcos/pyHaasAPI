"""
User API module for pyHaasAPI v2

Provides user management functionality including authentication,
token validation, and device management.
"""

from typing import Optional, Dict, Any

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import APIError
from ...core.logging import get_logger
from ...core.field_utils import safe_get_field, safe_get_success_flag


class UserAPI:
    """
    User API for user management operations
    
    Provides functionality for app login, token checking, logout,
    device approval, and simulation trading configuration.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("user_api")
    
    async def app_login(
        self,
        email: str,
        secret_key: str
    ) -> Dict[str, Any]:
        """
        The 3rd party login
        
        Args:
            email: User email
            secret_key: Secret key for authentication
            
        Returns:
            Dictionary with login result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/UserAPI.php",
                data={
                    "channel": "APP_LOGIN",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "email": email,
                    "secretkey": secret_key
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to login")
                raise APIError(f"Failed to login: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to login: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to login: {e}")
    
    async def check_token(self) -> Dict[str, Any]:
        """
        Checks if the user login is still valid
        
        Returns:
            Dictionary with token validation result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/UserAPI.php",
                data={
                    "channel": "CHECK_TOKEN",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to check token")
                raise APIError(f"Failed to check token: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to check token: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to check token: {e}")
    
    async def logout(self) -> Dict[str, Any]:
        """
        Logout procedure
        
        Returns:
            Dictionary with logout result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/UserAPI.php",
                data={
                    "channel": "LOGOUT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to logout")
                raise APIError(f"Failed to logout: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to logout: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to logout: {e}")
    
    async def is_device_approved(self, device_id: str) -> Dict[str, Any]:
        """
        Checks if a device is approved
        
        Args:
            device_id: Device ID to check
            
        Returns:
            Dictionary with device approval status
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/UserAPI.php",
                data={
                    "channel": "IS_DEVICE_APPROVED",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "deviceid": device_id
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to check device approval")
                raise APIError(f"Failed to check device approval: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to check device approval: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to check device approval: {e}")
    
    async def set_sim_trading_config(self, fill_when_touched: bool) -> Dict[str, Any]:
        """
        Sets the simulation trading configuration
        
        Args:
            fill_when_touched: Whether to fill orders when touched
            
        Returns:
            Dictionary with configuration result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/UserAPI.php",
                data={
                    "channel": "SET_SIM_TRADING_CONFIG",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "fillwhentouched": fill_when_touched
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to set sim trading config")
                raise APIError(f"Failed to set sim trading config: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to set sim trading config: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to set sim trading config: {e}")




