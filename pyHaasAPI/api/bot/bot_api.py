"""
Bot API module for pyHaasAPI v2

Provides comprehensive bot management functionality including creation,
configuration, control, and monitoring of trading bots.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import BotError, BotNotFoundError, BotCreationError, BotConfigurationError
from ...core.logging import get_logger
from ...core.field_utils import (
    safe_get_field, safe_get_nested_field, safe_get_dict_field,
    safe_get_success_flag, safe_get_status, log_field_mapping_issues
)
from ...models.bot import BotDetails, BotRecord, BotConfiguration


class BotAPI:
    """
    Bot API for managing trading bots
    
    Provides comprehensive bot management functionality including creation,
    configuration, control, and monitoring of trading bots.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("bot_api")
    
    async def create_bot_from_lab(
        self,
        lab_id: str,
        backtest_id: str,
        bot_name: str,
        account_id: str,
        market: str,
        leverage: float = 20.0
    ) -> BotDetails:
        """
        Create a bot from a lab's backtest using v1 patterns
        
        Based on v1 implementation from pyHaasAPI_v1/api.py (lines 1471-1492)
        Uses ADD_BOT_FROM_LABS channel for reliable bot creation
        
        Args:
            lab_id: ID of the lab to create bot from
            backtest_id: ID of the specific backtest to use
            bot_name: Name for the new bot
            account_id: ID of the account to assign the bot to
            market: Market to trade on
            leverage: Leverage to use (default: 20.0)
            
        Returns:
            BotDetails object with created bot information
            
        Raises:
            BotCreationError: If bot creation fails
        """
        try:
            self.logger.info(f"Creating bot from lab {lab_id}, backtest {backtest_id}: {bot_name}")
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotCreationError("Not authenticated")
            
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "ADD_BOT_FROM_LABS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "labid": lab_id,
                    "backtestid": backtest_id,
                    "botname": bot_name,
                    "accountid": account_id,
                    "market": market,
                    "leverage": leverage,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Bot creation failed")
                raise BotCreationError(f"Failed to create bot from lab: {error_msg}")
            
            bot_data = safe_get_field(response, "Data", {})
            if not bot_data:
                raise BotCreationError("No bot data returned from API")
            
            bot_details = BotDetails.model_validate(bot_data)
            self.logger.info(f"Successfully created bot from lab: {bot_details.bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to create bot from lab: {e}")
            if isinstance(e, BotCreationError):
                raise
            else:
                raise BotCreationError(f"Failed to create bot from lab: {e}")

    async def create_bot(
        self,
        bot_name: str,
        script_id: str,
        script_type: int = 0,
        account_id: str = "",
        market: str = "",
        leverage: float = 20.0,
        interval: int = 1,
        chart_style: int = 300,
        **kwargs: Any
    ) -> BotDetails:
        """
        Create a new bot
        
        Args:
            bot_name: Name for the new bot
            script_id: ID of the script to use
            script_type: Type of the script
            account_id: ID of the account to assign the bot to
            market: Market to trade on
            leverage: Leverage to use (default: 20.0)
            interval: Chart interval (default: 1)
            chart_style: Chart style (default: 300)
            
        Returns:
            BotDetails object with created bot information
            
        Raises:
            BotCreationError: If bot creation fails
        """
        try:
            self.logger.info(f"Creating bot: {bot_name}")
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotCreationError("Not authenticated")
            
            # Allow tests to pass 'market_tag' instead of 'market'
            effective_market = safe_get_dict_field(kwargs, "market_tag") or market
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "ADD_BOT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botname": bot_name,
                    "scriptid": script_id,
                    "scripttype": script_type,
                    "accountid": account_id,
                    "market": effective_market,
                    "leverage": leverage,
                    "interval": interval,
                    "chartstyle": chart_style,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Bot creation failed")
                raise BotCreationError(f"Failed to create bot: {error_msg}")
            data = safe_get_field(response, "Data", {})
            bot_details = BotDetails.model_validate(data)
            self.logger.info(f"Successfully created bot: {bot_details.bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to create bot {bot_name}: {e}")
            raise BotCreationError(f"Failed to create bot: {e}") from e
    
    async def create_bot_from_lab(
        self,
        lab_id: str,
        backtest_id: str,
        bot_name: str,
        account_id: str,
        market: str,
        leverage: float = 20.0
    ) -> BotDetails:
        """
        Create a new bot from a lab's backtest
        
        Args:
            lab_id: ID of the lab containing the backtest
            backtest_id: ID of the backtest to use
            bot_name: Name for the new bot
            account_id: ID of the account to assign the bot to
            market: Market to trade on
            leverage: Leverage to use (default: 20.0)
            
        Returns:
            BotDetails object with created bot information
            
        Raises:
            BotCreationError: If bot creation fails
        """
        try:
            self.logger.info(f"Creating bot from lab {lab_id}, backtest {backtest_id}")
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotCreationError("Not authenticated")
            
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "ADD_BOT_FROM_LABS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "labid": lab_id,
                    "backtestid": backtest_id,
                    "botname": bot_name,
                    "accountid": account_id,
                    "market": market,
                    "leverage": leverage,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Bot creation from lab failed")
                raise BotCreationError(f"Failed to create bot from lab: {error_msg}")
            data = safe_get_field(response, "Data", {})
            bot_details = BotDetails.model_validate(data)
            self.logger.info(f"Successfully created bot from lab: {bot_details.bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to create bot from lab {lab_id}: {e}")
            raise BotCreationError(f"Failed to create bot from lab: {e}") from e
    
    async def delete_bot(self, bot_id: str) -> bool:
        """
        Delete a bot
        
        Args:
            bot_id: ID of the bot to delete
            
        Returns:
            True if deletion successful, False otherwise
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If deletion fails
        """
        try:
            self.logger.info(f"Deleting bot: {bot_id}")
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "DELETE_BOT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot_id,
                }
            )
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to delete bot")
                if "not found" in str(error_msg).lower():
                    raise BotNotFoundError(f"Bot not found: {bot_id}")
                raise BotError(message=f"Failed to delete bot: {error_msg}")
            
            self.logger.info(f"Successfully deleted bot: {bot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete bot {bot_id}: {e}")
            raise BotError(message=f"Failed to delete bot: {e}") from e
    
    async def get_all_bots(self) -> List[BotDetails]:
        """
        Get all bots
        
        Based on the most recent v1 implementation from pyHaasAPI/api.py (lines 1501-1506)
        
        Returns:
            List of BotDetails objects
            
        Raises:
            BotError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving all bots")
            
            # Use the correct client method
            response = await self.client.get_json(
                endpoint="/BotAPI.php",
                params={"channel": "GET_BOTS"}
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get bots")
                raise BotError(message=f"Failed to get bots: {error_msg}")
            
            bots_data = safe_get_field(response, "Data", [])
            if not bots_data:
                self.logger.warning("No bot data returned from API")
                return []
            
            # Log field mapping for debugging
            if bots_data:
                log_field_mapping_issues(bots_data[0], "bot data sample")
            
            response = [BotDetails(**bot_data) for bot_data in bots_data]
            
            self.logger.debug(f"Retrieved {len(response)} bots")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve bots: {e}")
            raise BotError(message=f"Failed to retrieve bots: {e}") from e
    
    async def get_bot_details(self, bot_id: str) -> BotDetails:
        """
        Get detailed information about a specific bot
        
        Args:
            bot_id: ID of the bot to get details for
            
        Returns:
            BotDetails object with complete bot information
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving bot details: {bot_id}")
            
            response = await self.client.get_json(
                endpoint="/BotAPI.php",
                params={
                    "channel": "GET_BOT",
                    "botid": bot_id,
                }
            )
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get bot")
                raise BotNotFoundError(f"Bot not found or error: {error_msg}")
            data = safe_get_field(response, "Data", {})
            bot_details = BotDetails.model_validate(data)
            self.logger.debug(f"Retrieved bot details: {bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve bot details {bot_id}: {e}")
            raise BotNotFoundError(f"Bot not found: {bot_id}") from e
    
    async def get_full_bot_runtime_data(self, bot_id: str) -> BotDetails:
        """
        Get detailed runtime information for a specific bot
        
        Args:
            bot_id: ID of the bot
            
        Returns:
            BotDetails object with complete runtime information
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If retrieval fails
        """
        # This is currently the same as get_bot_details
        # In the future, this could be enhanced to include additional runtime data
        return await self.get_bot_details(bot_id)
    
    async def activate_bot(self, bot_id: str, clean_reports: bool = False) -> BotDetails:
        """
        Activate a bot to start trading
        
        Args:
            bot_id: ID of the bot to activate
            clean_reports: Whether to clean previous reports (default: False)
            
        Returns:
            Updated BotDetails object with activation status
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If activation fails
        """
        try:
            self.logger.info(f"Activating bot: {bot_id}")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "ACTIVATE_BOT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot_id,
                    "cleanreports": clean_reports,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to activate bot")
                raise BotError(message=f"Failed to activate bot: {error_msg}")
            data = safe_get_field(response, "Data", {})
            bot_details = BotDetails.model_validate(data) if data else await self.get_bot_details(bot_id)
            
            self.logger.info(f"Successfully activated bot: {bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to activate bot {bot_id}: {e}")
            raise BotError(message=f"Failed to activate bot: {e}") from e
    
    async def deactivate_bot(self, bot_id: str, cancel_orders: bool = False) -> BotDetails:
        """
        Deactivate a bot to stop trading
        
        Args:
            bot_id: ID of the bot to deactivate
            cancel_orders: Whether to cancel open orders (default: False)
            
        Returns:
            Updated BotDetails object with deactivation status
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If deactivation fails
        """
        try:
            self.logger.info(f"Deactivating bot: {bot_id}")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "DEACTIVATE_BOT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot_id,
                    "cancelorders": cancel_orders,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to deactivate bot")
                raise BotError(message=f"Failed to deactivate bot: {error_msg}")
            data = safe_get_field(response, "Data", {})
            bot_details = BotDetails.model_validate(data) if data else await self.get_bot_details(bot_id)
            
            self.logger.info(f"Successfully deactivated bot: {bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate bot {bot_id}: {e}")
            raise BotError(message=f"Failed to deactivate bot: {e}") from e
    
    async def pause_bot(self, bot_id: str) -> BotDetails:
        """
        Pause a bot (temporarily stop trading)
        
        Args:
            bot_id: ID of the bot to pause
            
        Returns:
            Updated BotDetails object with pause status
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If pause fails
        """
        try:
            self.logger.info(f"Pausing bot: {bot_id}")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "PAUSE_BOT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot_id,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to pause bot")
                raise BotError(message=f"Failed to pause bot: {error_msg}")
            data = safe_get_field(response, "Data", {})
            bot_details = BotDetails.model_validate(data) if data else await self.get_bot_details(bot_id)
            
            self.logger.info(f"Successfully paused bot: {bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to pause bot {bot_id}: {e}")
            raise BotError(message=f"Failed to pause bot: {e}") from e
    
    async def resume_bot(self, bot_id: str) -> BotDetails:
        """
        Resume a paused bot
        
        Args:
            bot_id: ID of the bot to resume
            
        Returns:
            Updated BotDetails object with resume status
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If resume fails
        """
        try:
            self.logger.info(f"Resuming bot: {bot_id}")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "RESUME_BOT",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot_id,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to resume bot")
                raise BotError(message=f"Failed to resume bot: {error_msg}")
            data = safe_get_field(response, "Data", {})
            bot_details = BotDetails.model_validate(data) if data else await self.get_bot_details(bot_id)
            
            self.logger.info(f"Successfully resumed bot: {bot_id}")
            return bot_details
            
        except Exception as e:
            self.logger.error(f"Failed to resume bot {bot_id}: {e}")
            raise BotError(message=f"Failed to resume bot: {e}") from e
    
    async def deactivate_all_bots(self) -> List[BotDetails]:
        """
        Deactivate all bots for the authenticated user
        
        Returns:
            List of updated BotDetails objects
            
        Raises:
            BotError: If deactivation fails
        """
        try:
            self.logger.info("Deactivating all bots")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "DEACTIVATE_ALL_BOTS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to deactivate all bots")
                raise BotError(message=f"Failed to deactivate all bots: {error_msg}")
            data = safe_get_field(response, "Data", [])
            bots = [BotDetails.model_validate(bot_data) for bot_data in data]
            self.logger.info(f"Successfully deactivated {len(bots)} bots")
            return bots
            
        except Exception as e:
            self.logger.error(f"Failed to deactivate all bots: {e}")
            raise BotError(message=f"Failed to deactivate all bots: {e}") from e
    
    async def edit_bot_parameter(self, bot: BotDetails) -> BotDetails:
        """
        Edit the parameters and settings of an existing bot
        
        Args:
            bot: BotDetails object with updated settings and parameters
            
        Returns:
            Updated BotDetails object
            
        Raises:
            BotNotFoundError: If bot is not found
            BotConfigurationError: If configuration update fails
        """
        try:
            self.logger.info(f"Editing bot parameters: {bot.bot_id}")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotConfigurationError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "EDIT_SETTINGS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot.bot_id,
                    "scriptid": bot.script_id,
                    "settings": bot.settings.model_dump_json(by_alias=True),
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to edit bot settings")
                raise BotConfigurationError(f"Failed to edit bot parameters: {error_msg}")
            data = safe_get_field(response, "Data", {})
            updated_bot = BotDetails.model_validate(data)
            self.logger.info(f"Successfully updated bot parameters: {bot.bot_id}")
            return updated_bot
            
        except Exception as e:
            self.logger.error(f"Failed to edit bot parameters {bot.bot_id}: {e}")
            raise BotConfigurationError(f"Failed to edit bot parameters: {e}") from e
    
    async def get_bot_orders(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get all open orders for a specific bot
        
        Args:
            bot_id: ID of the bot to get orders for
            
        Returns:
            List of order dictionaries
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving orders for bot: {bot_id}")
            
            response = await self.client.get_json(
                endpoint="/BotAPI.php",
                params={
                    "channel": "GET_BOT_ORDERS",
                    "botid": bot_id,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get bot orders")
                raise BotError(message=f"Failed to get bot orders: {error_msg}")
            orders = safe_get_field(response, "Data", [])
            self.logger.debug(f"Retrieved {len(orders)} orders for bot: {bot_id}")
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve orders for bot {bot_id}: {e}")
            raise BotError(message=f"Failed to retrieve bot orders: {e}") from e
    
    async def get_bot_positions(self, bot_id: str) -> List[Dict[str, Any]]:
        """
        Get all positions for a specific bot
        
        Args:
            bot_id: ID of the bot to get positions for
            
        Returns:
            List of position dictionaries
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving positions for bot: {bot_id}")
            
            response = await self.client.get_json(
                endpoint="/BotAPI.php",
                params={
                    "channel": "GET_BOT_POSITIONS",
                    "botid": bot_id,
                }
            )
            
            if not safe_get_success_flag(response):
                error_msg = safe_get_field(response, "Error", "Failed to get bot positions")
                raise BotError(message=f"Failed to get bot positions: {error_msg}")
            positions = safe_get_field(response, "Data", [])
            self.logger.debug(f"Retrieved {len(positions)} positions for bot: {bot_id}")
            return positions
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve positions for bot {bot_id}: {e}")
            raise BotError(message=f"Failed to retrieve bot positions: {e}") from e

    async def change_bot_notes(self, bot_id: str, notes: str) -> Dict[str, Any]:
        """
        Change bot notes (metadata/provenance) for a specific bot.
        
        Args:
            bot_id: ID of the bot to update
            notes: Plaintext notes (consider JSON string for structured data)
        
        Returns:
            The raw API response (usually success boolean or updated bot payload)
        
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If update fails
        """
        try:
            self.logger.info(f"Updating notes for bot: {bot_id}")
            response = await self.client.post(
                endpoint="/BotAPI.php",
                data={
                    "channel": "CHANGE_BOT_NOTES",
                    "botid": bot_id,
                    "notes": notes,
                }
            )
            self.logger.info(f"Successfully updated notes for bot: {bot_id}")
            return response
        except Exception as e:
            self.logger.error(f"Failed to change notes for bot {bot_id}: {e}")
            raise BotError(message=f"Failed to change bot notes: {e}") from e
    
    async def cancel_bot_order(self, bot_id: str, order_id: str) -> Dict[str, Any]:
        """
        Cancel a specific order for a bot
        
        Args:
            bot_id: ID of the bot
            order_id: ID of the order to cancel
            
        Returns:
            Cancellation result dictionary
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If cancellation fails
        """
        try:
            self.logger.info(f"Cancelling order {order_id} for bot: {bot_id}")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "CANCEL_BOT_ORDER",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot_id,
                    "orderid": order_id,
                }
            )
            
            self.logger.info(f"Successfully cancelled order {order_id} for bot: {bot_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id} for bot {bot_id}: {e}")
            raise BotError(message=f"Failed to cancel bot order: {e}") from e
    
    async def cancel_all_bot_orders(self, bot_id: str) -> Dict[str, Any]:
        """
        Cancel all orders for a specific bot
        
        Args:
            bot_id: ID of the bot to cancel all orders for
            
        Returns:
            Cancellation result dictionary
            
        Raises:
            BotNotFoundError: If bot is not found
            BotError: If cancellation fails
        """
        try:
            self.logger.info(f"Cancelling all orders for bot: {bot_id}")
            
            await self.auth_manager.ensure_authenticated()
            session = self.auth_manager.session
            if not session:
                raise BotError("Not authenticated")
            response = await self.client.post_json(
                endpoint="/BotAPI.php",
                data={
                    "channel": "CANCEL_ALL_BOT_ORDERS",
                    "userid": session.user_id,
                    "interfacekey": session.interface_key,
                    "botid": bot_id,
                }
            )
            
            self.logger.info(f"Successfully cancelled all orders for bot: {bot_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to cancel all orders for bot {bot_id}: {e}")
            raise BotError(message=f"Failed to cancel all bot orders: {e}") from e
    
    # Additional utility methods
    
    async def get_bots_by_status(self, status: str) -> List[BotDetails]:
        """
        Get bots filtered by status
        
        Args:
            status: Bot status to filter by
            
        Returns:
            List of BotDetails objects with the specified status
        """
        all_bots = await self.get_all_bots()
        return [bot for bot in all_bots if bot.status == status]
    
    async def get_bots_by_account(self, account_id: str) -> List[BotDetails]:
        """
        Get bots filtered by account
        
        Args:
            account_id: Account ID to filter by
            
        Returns:
            List of BotDetails objects assigned to the specified account
        """
        all_bots = await self.get_all_bots()
        return [bot for bot in all_bots if bot.account_id == account_id]
    
    async def get_bots_by_market(self, market: str) -> List[BotDetails]:
        """
        Get bots filtered by market
        
        Args:
            market: Market to filter by
            
        Returns:
            List of BotDetails objects trading the specified market
        """
        all_bots = await self.get_all_bots()
        return [bot for bot in all_bots if bot.market == market]
    
    async def get_active_bots(self) -> List[BotDetails]:
        """
        Get all active bots
        
        Returns:
            List of active BotDetails objects
        """
        return await self.get_bots_by_status("active")
    
    async def get_inactive_bots(self) -> List[BotDetails]:
        """
        Get all inactive bots
        
        Returns:
            List of inactive BotDetails objects
        """
        return await self.get_bots_by_status("inactive")
    
    async def get_paused_bots(self) -> List[BotDetails]:
        """
        Get all paused bots
        
        Returns:
            List of paused BotDetails objects
        """
        return await self.get_bots_by_status("paused")
