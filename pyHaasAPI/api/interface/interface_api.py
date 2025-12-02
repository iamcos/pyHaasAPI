"""
Interface API module for pyHaasAPI v2

Provides interface functionality including market information and ChatAI bot interactions.
"""

from typing import Optional, Dict, Any

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import APIError
from ...core.logging import get_logger
from ...core.field_utils import safe_get_field, safe_get_success_flag


class InterfaceAPI:
    """
    Interface API for market information and ChatAI interactions
    
    Provides functionality for getting market information and interacting
    with ChatAI bots (Julia, Thomas, Simone, David).
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("interface_api")
    
    async def initialize(self, ct: Any) -> Dict[str, Any]:
        """
        Initialize the interface
        
        Args:
            ct: Connection type or configuration
            
        Returns:
            Dictionary with initialization result
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "Initialize",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "ct": ct
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to initialize interface")
                raise APIError(f"Failed to initialize interface: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to initialize interface: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to initialize interface: {e}")
    
    async def market_info(self, market: str) -> Dict[str, Any]:
        """
        Returns the market information page
        
        Args:
            market: Name of the market, like BINANCE_BTC_USDT_
            
        Returns:
            Dictionary with market information
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "MARKET_INFO",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "market": market
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get market info")
                raise APIError(f"Failed to get market info: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get market info: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get market info: {e}")
    
    async def market_price_info(self, market: str) -> Dict[str, Any]:
        """
        Returns the market price information page
        
        Args:
            market: Name of the market, like BINANCE_BTC_USDT_
            
        Returns:
            Dictionary with market price information
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "MARKET_PRICE_INFO",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "market": market
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get market price info")
                raise APIError(f"Failed to get market price info: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get market price info: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get market price info: {e}")
    
    async def market_ta_info(self, market: str) -> Dict[str, Any]:
        """
        Returns the market price technical analysis page
        
        Args:
            market: Name of the market, like BINANCE_BTC_USDT_
            
        Returns:
            Dictionary with market technical analysis information
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "MARKET_TA_INFO",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "market": market
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get market TA info")
                raise APIError(f"Failed to get market TA info: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to get market TA info: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get market TA info: {e}")
    
    async def ask_julia(self, chat_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a question to ChatAI Bot Julia (support)
        
        Args:
            chat_id: Chat ID
            message: Message to send
            
        Returns:
            Dictionary with response from Julia
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "ASK_JULIA",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "chatid": chat_id,
                    "message": message
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to ask Julia")
                raise APIError(f"Failed to ask Julia: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to ask Julia: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to ask Julia: {e}")
    
    async def ask_thomas(self, chat_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a question to ChatAI Bot Thomas (haasscript)
        
        Args:
            chat_id: Chat ID
            message: Message to send
            
        Returns:
            Dictionary with response from Thomas
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "ASK_THOMAS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "chatid": chat_id,
                    "message": message
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to ask Thomas")
                raise APIError(f"Failed to ask Thomas: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to ask Thomas: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to ask Thomas: {e}")
    
    async def ask_simone(self, chat_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a question to ChatAI Bot Simone (news tracker)
        
        Args:
            chat_id: Chat ID
            message: Message to send
            
        Returns:
            Dictionary with response from Simone
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "ASK_SIMONE",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "chatid": chat_id,
                    "message": message
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to ask Simone")
                raise APIError(f"Failed to ask Simone: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to ask Simone: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to ask Simone: {e}")
    
    async def ask_david(self, chat_id: str, message: str) -> Dict[str, Any]:
        """
        Sends a question to ChatAI Bot David (crypto guru)
        
        Args:
            chat_id: Chat ID
            message: Message to send
            
        Returns:
            Dictionary with response from David
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "ASK_DAVID",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "chatid": chat_id,
                    "message": message
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to ask David")
                raise APIError(f"Failed to ask David: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to ask David: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to ask David: {e}")
    
    async def ask_question(
        self, 
        bot: str, 
        chat_id: str, 
        message_id: str, 
        message: str
    ) -> Dict[str, Any]:
        """
        Sends a question to one of the ChatAI bots
        
        Args:
            bot: Bot identifier
            chat_id: Chat ID
            message_id: Message ID
            message: Message to send
            
        Returns:
            Dictionary with response from the bot
            
        Raises:
            APIError: If API request fails
        """
        try:
            await self.auth_manager.ensure_authenticated()
            
            session = self.auth_manager.session
            if not session:
                raise APIError("Not authenticated")
            
            response = await self.client.post_json(
                "/InterfaceAPI.php",
                data={
                    "channel": "ASK_QUESTION",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "bot": bot,
                    "chatid": chat_id,
                    "messageid": message_id,
                    "message": message
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to ask question")
                raise APIError(f"Failed to ask question: {error_msg}")
            
            return safe_get_field(response, "Data", {})
            
        except Exception as e:
            self.logger.error(f"Failed to ask question: {e}")
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to ask question: {e}")




