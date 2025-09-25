"""
Account API module for pyHaasAPI v2

Provides comprehensive account management functionality including account data retrieval,
balance management, margin settings, and bot account assignments.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import AccountError, AccountNotFoundError, AccountConfigurationError
from ...core.logging import get_logger
from ...models.account import AccountDetails, AccountRecord, AccountBalance


class AccountAPI:
    """
    Account API for managing trading accounts
    
    Provides comprehensive account management functionality including account data retrieval,
    balance management, margin settings, and bot account assignments.
    """
    
    def __init__(self, client: AsyncHaasClient, auth_manager: AuthenticationManager):
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("account_api")
    
    async def get_accounts(self) -> List[AccountDetails]:
        """
        Get all accounts
        
        Based on the most recent v1 implementation from pyHaasAPI/api.py (lines 2127-2146)
        
        Returns:
            List of AccountDetails objects
            
        Raises:
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving all accounts")
            
            # Use the proven v1 implementation pattern
            response = await self.client.execute_request(
                endpoint="Account",
                response_type=List[AccountDetails],
                query_params={"channel": "GET_ACCOUNTS"}
            )
            
            self.logger.debug(f"Retrieved {len(response)} accounts")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve accounts: {e}")
            raise AccountError(f"Failed to retrieve accounts: {e}") from e

    async def get_binancefutures_accounts(self) -> List[AccountDetails]:
        """
        Get all BinanceFutures accounts specifically
        
        Returns:
            List of BinanceFutures AccountDetails objects
            
        Raises:
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving BinanceFutures accounts")
            
            all_accounts = await self.get_accounts()
            binancefutures_accounts = [
                account for account in all_accounts 
                if account.exchange.upper() == "BINANCEFUTURES"
            ]
            
            self.logger.debug(f"Retrieved {len(binancefutures_accounts)} BinanceFutures accounts")
            return binancefutures_accounts
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve BinanceFutures accounts: {e}")
            raise AccountError(f"Failed to retrieve BinanceFutures accounts: {e}") from e

    async def get_available_binancefutures_account(self, exclude_accounts: Optional[List[str]] = None) -> Optional[AccountDetails]:
        """
        Get an available BinanceFutures account for bot assignment.
        
        Selection strategy:
        1. Find accounts with no bots assigned (empty-first)
        2. If all accounts have bots, select the one with least bots
        3. Prefer accounts with sufficient balance
        
        Args:
            exclude_accounts: List of account IDs to exclude from selection
            
        Returns:
            Available AccountDetails or None if no suitable account found
            
        Raises:
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug("Finding available BinanceFutures account")
            
            # Get all BinanceFutures accounts
            binancefutures_accounts = await self.get_binancefutures_accounts()
            if not binancefutures_accounts:
                self.logger.warning("No BinanceFutures accounts found")
                return None
            
            # Filter out excluded accounts
            if exclude_accounts:
                binancefutures_accounts = [
                    acc for acc in binancefutures_accounts 
                    if acc.account_id not in exclude_accounts
                ]
            
            if not binancefutures_accounts:
                self.logger.warning("No BinanceFutures accounts available after exclusions")
                return None
            
            # Get bot assignments for each account
            from ...api.bot import BotAPI
            bot_api = BotAPI(self.client, self.auth_manager)
            all_bots = await bot_api.get_all_bots()
            
            # Count bots per account
            account_bot_counts = {}
            for bot in all_bots:
                account_id = bot.account_id
                account_bot_counts[account_id] = account_bot_counts.get(account_id, 0) + 1
            
            # Sort accounts by bot count (ascending) and then by account_id for consistency
            available_accounts = sorted(
                binancefutures_accounts,
                key=lambda acc: (account_bot_counts.get(acc.account_id, 0), acc.account_id)
            )
            
            selected_account = available_accounts[0]
            bot_count = account_bot_counts.get(selected_account.account_id, 0)
            
            self.logger.info(f"Selected BinanceFutures account {selected_account.account_id} with {bot_count} bots")
            return selected_account
            
        except Exception as e:
            self.logger.error(f"Failed to get available BinanceFutures account: {e}")
            raise AccountError(f"Failed to get available account: {e}") from e
    
    async def get_account_data(self, account_id: str) -> AccountDetails:
        """
        Get account data including exchange information
        
        Args:
            account_id: ID of the account
            
        Returns:
            AccountDetails object with account information
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving account data: {account_id}")
            
            response = await self.client.get(
                endpoint="Account",
                params={
                    "channel": "GET_ACCOUNT_DATA",
                    "accountid": account_id,
                }
            )
            
            # Extract data from the raw response
            data = response.get("Data", {})
            
            # Construct AccountDetails object
            account_data = AccountDetails(
                account_id=account_id,
                exchange=data.get("exchange", ""),
                type=data.get("type", ""),
                wallets=data.get("B", []),
                name=data.get("name", ""),
                status=data.get("status", "active")
            )
            
            self.logger.debug(f"Retrieved account data: {account_id}")
            return account_data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve account data {account_id}: {e}")
            raise AccountNotFoundError(f"Account not found: {account_id}") from e
    
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Get balance information for a specific account
        
        Args:
            account_id: ID of the account to get balance for
            
        Returns:
            Balance information dictionary
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving balance for account: {account_id}")
            
            response = await self.client.get(
                endpoint="Account",
                params={
                    "channel": "GET_BALANCE",
                    "accountid": account_id,
                }
            )
            
            self.logger.debug(f"Retrieved balance for account: {account_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve balance for account {account_id}: {e}")
            raise AccountError(f"Failed to retrieve account balance: {e}") from e
    
    async def get_all_account_balances(self) -> List[Dict[str, Any]]:
        """
        Get balance information for all accounts
        
        Returns:
            List of balance dictionaries for all accounts
            
        Raises:
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug("Retrieving balances for all accounts")
            
            response = await self.client.get(
                endpoint="Account",
                params={
                    "channel": "GET_ALL_BALANCES",
                }
            )
            
            self.logger.debug(f"Retrieved balances for {len(response)} accounts")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve all account balances: {e}")
            raise AccountError(f"Failed to retrieve all account balances: {e}") from e
    
    async def get_account_orders(self, account_id: str) -> Dict[str, Any]:
        """
        Get open orders for an account
        
        Args:
            account_id: ID of the account to get orders for
            
        Returns:
            Dictionary containing orders (with 'I' key for orders)
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving orders for account: {account_id}")
            
            response = await self.client.get(
                endpoint="Account",
                params={
                    "channel": "GET_ORDERS",
                    "accountid": account_id,
                    "userid": self.auth_manager.user_id,
                    "interfacekey": self.auth_manager.interface_key,
                }
            )
            
            self.logger.debug(f"Retrieved orders for account: {account_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve orders for account {account_id}: {e}")
            raise AccountError(f"Failed to retrieve account orders: {e}") from e
    
    async def get_margin_settings(self, account_id: str, market: str) -> Dict[str, Any]:
        """
        Get current margin settings for an account/market
        
        Args:
            account_id: Account ID
            market: Market to get settings for
            
        Returns:
            Dictionary containing margin settings
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug(f"Retrieving margin settings for account {account_id}, market {market}")
            
            response = await self.client.get(
                endpoint="Account",
                params={
                    "channel": "GET_MARGIN_SETTINGS",
                    "accountid": account_id,
                    "market": market,
                }
            )
            
            self.logger.debug(f"Retrieved margin settings for account {account_id}, market {market}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve margin settings for account {account_id}, market {market}: {e}")
            raise AccountError(f"Failed to retrieve margin settings: {e}") from e
    
    async def adjust_margin_settings(
        self,
        account_id: str,
        market: str,
        position_mode: Optional[int] = None,
        margin_mode: Optional[int] = None,
        leverage: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Adjust multiple margin settings at once
        
        Args:
            account_id: Account ID
            market: Market to adjust settings for
            position_mode: Position mode (0=ONE_WAY, 1=HEDGE)
            margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
            leverage: Leverage value
            
        Returns:
            Dictionary containing adjustment result
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountConfigurationError: If configuration fails
        """
        try:
            self.logger.info(f"Adjusting margin settings for account {account_id}, market {market}")
            
            params = {
                "channel": "ADJUST_MARGIN_SETTINGS",
                "accountid": account_id,
                "market": market,
            }
            
            if position_mode is not None:
                params["position_mode"] = position_mode
            if margin_mode is not None:
                params["margin_mode"] = margin_mode
            if leverage is not None:
                params["leverage"] = leverage
            
            response = await self.client.post(
                endpoint="Account",
                data=params
            )
            
            self.logger.info(f"Successfully adjusted margin settings for account {account_id}, market {market}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to adjust margin settings for account {account_id}, market {market}: {e}")
            raise AccountConfigurationError(f"Failed to adjust margin settings: {e}") from e
    
    async def set_position_mode(self, account_id: str, market: str, position_mode: int) -> Dict[str, Any]:
        """
        Set position mode for futures trading (ONE_WAY vs HEDGE)
        
        Args:
            account_id: Account ID
            market: Market to set position mode for
            position_mode: Position mode (0=ONE_WAY, 1=HEDGE)
            
        Returns:
            Dictionary containing result
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountConfigurationError: If configuration fails
        """
        try:
            self.logger.info(f"Setting position mode {position_mode} for account {account_id}, market {market}")
            
            response = await self.client.post(
                endpoint="Account",
                data={
                    "channel": "SET_POSITION_MODE",
                    "accountid": account_id,
                    "market": market,
                    "position_mode": position_mode,
                }
            )
            
            self.logger.info(f"Successfully set position mode {position_mode} for account {account_id}, market {market}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to set position mode for account {account_id}, market {market}: {e}")
            raise AccountConfigurationError(f"Failed to set position mode: {e}") from e
    
    async def set_margin_mode(self, account_id: str, market: str, margin_mode: int) -> Dict[str, Any]:
        """
        Set margin mode for futures trading (CROSS vs ISOLATED)
        
        Args:
            account_id: Account ID
            market: Market to set margin mode for
            margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
            
        Returns:
            Dictionary containing result
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountConfigurationError: If configuration fails
        """
        try:
            self.logger.info(f"Setting margin mode {margin_mode} for account {account_id}, market {market}")
            
            response = await self.client.post(
                endpoint="Account",
                data={
                    "channel": "SET_MARGIN_MODE",
                    "accountid": account_id,
                    "market": market,
                    "margin_mode": margin_mode,
                }
            )
            
            self.logger.info(f"Successfully set margin mode {margin_mode} for account {account_id}, market {market}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to set margin mode for account {account_id}, market {market}: {e}")
            raise AccountConfigurationError(f"Failed to set margin mode: {e}") from e
    
    async def set_leverage(self, account_id: str, market: str, leverage: float) -> Dict[str, Any]:
        """
        Set leverage for futures trading
        
        Args:
            account_id: Account ID
            market: Market to set leverage for
            leverage: Leverage value
            
        Returns:
            Dictionary containing result
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountConfigurationError: If configuration fails
        """
        try:
            self.logger.info(f"Setting leverage {leverage} for account {account_id}, market {market}")
            
            response = await self.client.post(
                endpoint="Account",
                data={
                    "channel": "SET_LEVERAGE",
                    "accountid": account_id,
                    "market": market,
                    "leverage": leverage,
                }
            )
            
            self.logger.info(f"Successfully set leverage {leverage} for account {account_id}, market {market}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to set leverage for account {account_id}, market {market}: {e}")
            raise AccountConfigurationError(f"Failed to set leverage: {e}") from e
    
    async def distribute_bots_to_accounts(
        self,
        bot_ids: List[str],
        account_ids: List[str],
        configure_margin: bool = True,
        position_mode: int = 1,
        margin_mode: int = 0,
        leverage: float = 20.0
    ) -> Dict[str, Any]:
        """
        Distribute multiple bots across different accounts
        
        Args:
            bot_ids: List of bot IDs to distribute
            account_ids: List of account IDs to distribute to
            configure_margin: Whether to configure margin settings
            position_mode: Position mode to set (default: 1=HEDGE)
            margin_mode: Margin mode to set (default: 0=CROSS)
            leverage: Leverage to set (default: 20.0)
            
        Returns:
            Dictionary containing distribution results
            
        Raises:
            AccountError: If distribution fails
        """
        try:
            self.logger.info(f"Distributing {len(bot_ids)} bots across {len(account_ids)} accounts")
            
            response = await self.client.post(
                endpoint="Account",
                data={
                    "channel": "DISTRIBUTE_BOTS_TO_ACCOUNTS",
                    "bot_ids": bot_ids,
                    "account_ids": account_ids,
                    "configure_margin": configure_margin,
                    "position_mode": position_mode,
                    "margin_mode": margin_mode,
                    "leverage": leverage,
                }
            )
            
            self.logger.info(f"Successfully distributed bots across accounts")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to distribute bots to accounts: {e}")
            raise AccountError(f"Failed to distribute bots to accounts: {e}") from e
    
    async def migrate_bot_to_account(
        self,
        bot_id: str,
        new_account_id: str,
        preserve_settings: bool = True,
        position_mode: int = 1,
        margin_mode: int = 0,
        leverage: float = 20.0
    ) -> Dict[str, Any]:
        """
        Migrate a bot to a new account with full configuration
        
        Args:
            bot_id: Bot ID to migrate
            new_account_id: New account ID
            preserve_settings: Whether to preserve bot settings
            position_mode: Position mode to set (default: 1=HEDGE)
            margin_mode: Margin mode to set (default: 0=CROSS)
            leverage: Leverage to set (default: 20.0)
            
        Returns:
            Dictionary containing migration results
            
        Raises:
            AccountError: If migration fails
        """
        try:
            self.logger.info(f"Migrating bot {bot_id} to account {new_account_id}")
            
            response = await self.client.post(
                endpoint="Account",
                data={
                    "channel": "MIGRATE_BOT_TO_ACCOUNT",
                    "bot_id": bot_id,
                    "new_account_id": new_account_id,
                    "preserve_settings": preserve_settings,
                    "position_mode": position_mode,
                    "margin_mode": margin_mode,
                    "leverage": leverage,
                }
            )
            
            self.logger.info(f"Successfully migrated bot {bot_id} to account {new_account_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to migrate bot {bot_id} to account {new_account_id}: {e}")
            raise AccountError(f"Failed to migrate bot to account: {e}") from e
    
    async def change_bot_account(self, bot_id: str, new_account_id: str) -> bool:
        """
        Change a bot's account assignment
        
        Args:
            bot_id: Bot ID to move
            new_account_id: New account ID
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            AccountError: If change fails
        """
        try:
            self.logger.info(f"Changing bot {bot_id} account to {new_account_id}")
            
            response = await self.client.post(
                endpoint="Account",
                data={
                    "channel": "CHANGE_BOT_ACCOUNT",
                    "bot_id": bot_id,
                    "new_account_id": new_account_id,
                }
            )
            
            success = response.get("success", False)
            if success:
                self.logger.info(f"Successfully changed bot {bot_id} account to {new_account_id}")
            else:
                self.logger.warning(f"Failed to change bot {bot_id} account to {new_account_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to change bot {bot_id} account to {new_account_id}: {e}")
            raise AccountError(f"Failed to change bot account: {e}") from e
    
    async def move_bot(self, bot_id: str, new_account_id: str) -> bool:
        """
        Move a bot to a different account (alias for change_bot_account)
        
        Args:
            bot_id: Bot ID to move
            new_account_id: New account ID
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            AccountError: If move fails
        """
        return await self.change_bot_account(bot_id, new_account_id)
    
    async def set_bot_account(self, bot_id: str, account_id: str) -> bool:
        """
        Set a bot's account assignment
        
        Args:
            bot_id: Bot ID to configure
            account_id: Account ID to assign
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            AccountError: If assignment fails
        """
        try:
            self.logger.info(f"Setting bot {bot_id} account to {account_id}")
            
            response = await self.client.post(
                endpoint="Account",
                data={
                    "channel": "SET_BOT_ACCOUNT",
                    "bot_id": bot_id,
                    "account_id": account_id,
                }
            )
            
            success = response.get("success", False)
            if success:
                self.logger.info(f"Successfully set bot {bot_id} account to {account_id}")
            else:
                self.logger.warning(f"Failed to set bot {bot_id} account to {account_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to set bot {bot_id} account to {account_id}: {e}")
            raise AccountError(f"Failed to set bot account: {e}") from e
    
    # Additional utility methods
    
    async def get_accounts_by_type(self, account_type: str) -> List[AccountDetails]:
        """
        Get accounts filtered by type
        
        Args:
            account_type: Account type to filter by
            
        Returns:
            List of AccountDetails objects with the specified type
        """
        all_accounts = await self.get_accounts()
        return [account for account in all_accounts if account.type == account_type]
    
    async def get_accounts_by_exchange(self, exchange: str) -> List[AccountDetails]:
        """
        Get accounts filtered by exchange
        
        Args:
            exchange: Exchange to filter by
            
        Returns:
            List of AccountDetails objects for the specified exchange
        """
        all_accounts = await self.get_accounts()
        return [account for account in all_accounts if account.exchange == exchange]
    
    async def get_active_accounts(self) -> List[AccountDetails]:
        """
        Get all active accounts
        
        Returns:
            List of active AccountDetails objects
        """
        all_accounts = await self.get_accounts()
        return [account for account in all_accounts if account.status == "active"]
    
    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """
        Get comprehensive account summary including data, balance, and settings
        
        Args:
            account_id: Account ID to get summary for
            
        Returns:
            Dictionary containing comprehensive account information
            
        Raises:
            AccountNotFoundError: If account is not found
            AccountError: If retrieval fails
        """
        try:
            self.logger.debug(f"Getting account summary for: {account_id}")
            
            # Get all account information in parallel
            account_data, balance, orders = await asyncio.gather(
                self.get_account_data(account_id),
                self.get_account_balance(account_id),
                self.get_account_orders(account_id),
                return_exceptions=True
            )
            
            summary = {
                "account_data": account_data if not isinstance(account_data, Exception) else None,
                "balance": balance if not isinstance(balance, Exception) else None,
                "orders": orders if not isinstance(orders, Exception) else None,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.debug(f"Retrieved account summary for: {account_id}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to get account summary for {account_id}: {e}")
            raise AccountError(f"Failed to get account summary: {e}") from e
