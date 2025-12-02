"""
Custom API module for pyHaasAPI v2

Provides custom command functionality.
"""

from typing import List, Dict, Any

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import APIError
from ...core.logging import get_logger
from ...core.field_utils import safe_get_field, safe_get_success_flag


class CustomAPI:
    """
    Custom API for custom command operations
    
    Provides functionality for retrieving default commands.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("custom_api")
    
    async def get_default_commands(self) -> List[Dict[str, Any]]:
        """
        Gets all the default commands
        
        Returns:
            List of default command dictionaries
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/CustomAPI.php",
                data={
                    "channel": "GET_DEFAULT_COMMANDS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get default commands")
                raise APIError(f"Failed to get default commands: {error_msg}")
            
            data = safe_get_field(response, "Data", [])
            return data if isinstance(data, list) else []
            
        except Exception as e:
            self.logger.error(f"Failed to get default commands: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get default commands: {e}")




