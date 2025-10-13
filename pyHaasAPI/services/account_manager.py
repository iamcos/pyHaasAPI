"""
Account Manager Service for pyHaasAPI v2

Provides production-tested account management algorithms from v1:
- Round-robin account assignment
- Balance management and validation
- On-demand simulated account creation
- Sequential naming schema ([Sim] 4AA-10k, 4AB-10k, etc.)

Based on:
- pyHaasAPI_v1/cli/base.py:BaseBotCLI.get_next_account
- pyHaasAPI_v1/cli/account_cleanup.py
- pyHaasAPI_v1/accounts/management.py:AccountManager
"""

import asyncio
import logging
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
from pathlib import Path

from ..api.account import AccountAPI
from ..models.account import AccountRecord
from ..exceptions import AccountError
from ..core.logging import get_logger


@dataclass
class AccountAssignmentState:
    """Tracks account assignment state for round-robin"""
    server: str
    assigned_accounts: Dict[str, int]  # account_id -> bot_count
    last_assigned_index: int = 0
    total_accounts: int = 0


class AccountManager:
    """
    Manages account assignment, creation, and balance tracking.
    
    Features:
    - Round-robin assignment (distributes bots evenly across accounts)
    - On-demand account creation with sequential naming
    - Balance validation and tracking
    - Exchange-specific filtering
    """
    
    def __init__(
        self,
        account_api: AccountAPI,
        server: str,
        initial_balance: float = 10000.0,
        min_balance: float = 1000.0
    ):
        """
        Initialize AccountManager.
        
        Args:
            account_api: AccountAPI instance for account operations
            server: Server identifier (e.g., "srv03")
            initial_balance: Starting balance for new accounts (default: 10000 USDT)
            min_balance: Minimum required balance (default: 1000 USDT)
        """
        self.account_api = account_api
        self.server = server
        self.initial_balance = initial_balance
        self.min_balance = min_balance
        self.logger = get_logger(f"account_manager_{server}")
        
        # Track assignment state
        self.assignment_state = AccountAssignmentState(
            server=server,
            assigned_accounts={}
        )
        
        # Track created accounts to avoid duplicates
        self.created_account_names: Set[str] = set()
    
    def _generate_sequential_name(self, index: int) -> str:
        """
        Generate sequential account name following v1 schema.
        
        Pattern: [Sim] 4AA-10k, [Sim] 4AB-10k, ..., [Sim] 4ZZ-10k
        
        Args:
            index: Sequential index (0-675 for AA-ZZ)
            
        Returns:
            Formatted account name
        """
        # Convert index to two-letter code (AA-ZZ)
        first_letter = chr(65 + (index // 26))  # A-Z
        second_letter = chr(65 + (index % 26))   # A-Z
        
        return f"[Sim] 4{first_letter}{second_letter}-10k"
    
    def _find_next_available_name(self, existing_names: Set[str]) -> str:
        """
        Find the next available account name in the sequence.
        
        Args:
            existing_names: Set of existing account names
            
        Returns:
            Next available account name
        """
        for index in range(676):  # 26*26 = 676 possible combinations
            name = self._generate_sequential_name(index)
            if name not in existing_names and name not in self.created_account_names:
                return name
        
        # Fallback if all 676 slots are taken
        self.logger.warning("All 676 sequential account names used, using timestamp-based name")
        from datetime import datetime
        return f"[Sim] 4XX-{datetime.now().strftime('%H%M%S')}"
    
    async def get_or_create_account(
        self,
        exchange: str = "BINANCEFUTURES",
        min_balance: Optional[float] = None
    ) -> AccountRecord:
        """
        Get an existing account or create a new one if needed.
        
        Prioritizes existing accounts with sufficient balance before creating new ones.
        
        Args:
            exchange: Exchange code (default: "BINANCEFUTURES")
            min_balance: Minimum required balance (default: self.min_balance)
            
        Returns:
            AccountRecord ready for bot assignment
            
        Raises:
            AccountError: If account retrieval/creation fails
        """
        min_bal = min_balance or self.min_balance
        
        try:
            # First, try to find an existing account
            accounts = await self.account_api.get_accounts()
            exchange_accounts = [
                acc for acc in accounts
                if acc.exchange.upper() == exchange.upper()
            ]
            
            # Filter by simulated status
            simulated_accounts = [
                acc for acc in exchange_accounts
                if acc.is_simulated
            ]
            
            if simulated_accounts:
                self.logger.info(f"Found {len(simulated_accounts)} existing simulated {exchange} accounts")
                # Return the first one (we'll handle assignment in assign_account_round_robin)
                return simulated_accounts[0]
            
            # No existing accounts, create a new one
            self.logger.info(f"No existing {exchange} accounts found, creating new account")
            
            # Get existing names to find next available
            existing_names = {acc.name for acc in accounts}
            new_name = self._find_next_available_name(existing_names)
            
            # Create account
            new_account = await self.account_api.create_simulated_account(
                name=new_name,
                exchange=exchange,
                initial_balance=self.initial_balance,
                position_mode=1  # HEDGE mode
            )
            
            if not new_account:
                raise AccountError(message="Failed to create new account")
            
            # Track the created account
            self.created_account_names.add(new_name)
            self.logger.info(f"✅ Created new account: {new_name}")
            
            return new_account
            
        except Exception as e:
            self.logger.error(f"Failed to get or create account: {e}")
            raise AccountError(message=f"Failed to get or create account: {str(e)}")
    
    async def assign_account_round_robin(
        self,
        exchange: str = "BINANCEFUTURES",
        exclude_accounts: Optional[List[str]] = None
    ) -> AccountRecord:
        """
        Assign an account using round-robin strategy.
        
        Based on v1: cli/base.py:BaseBotCLI.get_next_account
        
        Distributes bots evenly across all available accounts.
        Creates new accounts on-demand if needed.
        
        Args:
            exchange: Exchange code (default: "BINANCEFUTURES")
            exclude_accounts: List of account IDs to exclude
            
        Returns:
            AccountRecord for bot assignment
            
        Raises:
            AccountError: If no suitable account can be assigned
        """
        try:
            # Get all accounts for this exchange
            all_accounts = await self.account_api.get_accounts()
            exchange_accounts = [
                acc for acc in all_accounts
                if acc.exchange.upper() == exchange.upper() and acc.is_simulated
            ]
            
            # Filter out excluded accounts
            if exclude_accounts:
                exchange_accounts = [
                    acc for acc in exchange_accounts
                    if acc.account_id not in exclude_accounts
                ]
            
            # If no accounts available, create one
            if not exchange_accounts:
                self.logger.info("No accounts available for assignment, creating new account")
                return await self.get_or_create_account(exchange=exchange)
            
            # Update assignment state
            self.assignment_state.total_accounts = len(exchange_accounts)
            
            # Round-robin selection
            next_index = self.assignment_state.last_assigned_index % len(exchange_accounts)
            selected_account = exchange_accounts[next_index]
            
            # Update state
            self.assignment_state.last_assigned_index = (next_index + 1) % len(exchange_accounts)
            self.assignment_state.assigned_accounts[selected_account.account_id] = \
                self.assignment_state.assigned_accounts.get(selected_account.account_id, 0) + 1
            
            self.logger.info(
                f"Assigned account {selected_account.name} "
                f"(total assignments: {self.assignment_state.assigned_accounts[selected_account.account_id]})"
            )
            
            return selected_account
            
        except Exception as e:
            self.logger.error(f"Failed to assign account: {e}")
            raise AccountError(message=f"Failed to assign account: {str(e)}")
    
    async def ensure_sufficient_accounts(
        self,
        required_count: int,
        exchange: str = "BINANCEFUTURES"
    ) -> List[AccountRecord]:
        """
        Ensure that at least N accounts exist for the given exchange.
        
        Creates additional accounts if needed.
        
        Args:
            required_count: Minimum number of accounts required
            exchange: Exchange code (default: "BINANCEFUTURES")
            
        Returns:
            List of available AccountRecord objects
            
        Raises:
            AccountError: If account creation fails
        """
        try:
            # Get existing accounts
            all_accounts = await self.account_api.get_accounts()
            exchange_accounts = [
                acc for acc in all_accounts
                if acc.exchange.upper() == exchange.upper() and acc.is_simulated
            ]
            
            existing_count = len(exchange_accounts)
            self.logger.info(f"Found {existing_count} existing {exchange} accounts")
            
            if existing_count >= required_count:
                self.logger.info(f"Sufficient accounts available ({existing_count} >= {required_count})")
                return exchange_accounts
            
            # Need to create more accounts
            accounts_to_create = required_count - existing_count
            self.logger.info(f"Creating {accounts_to_create} additional accounts...")
            
            # Get existing names
            existing_names = {acc.name for acc in all_accounts}
            
            # Create new accounts
            new_accounts = []
            for i in range(accounts_to_create):
                new_name = self._find_next_available_name(existing_names)
                existing_names.add(new_name)  # Avoid duplicates in this batch
                
                new_account = await self.account_api.create_simulated_account(
                    name=new_name,
                    exchange=exchange,
                    initial_balance=self.initial_balance,
                    position_mode=1  # HEDGE mode
                )
                
                if new_account:
                    new_accounts.append(new_account)
                    self.created_account_names.add(new_name)
                    self.logger.info(f"✅ Created account {i+1}/{accounts_to_create}: {new_name}")
                else:
                    self.logger.error(f"Failed to create account {i+1}/{accounts_to_create}")
            
            # Return all available accounts
            all_available = exchange_accounts + new_accounts
            self.logger.info(f"Total {exchange} accounts available: {len(all_available)}")
            
            return all_available
            
        except Exception as e:
            self.logger.error(f"Failed to ensure sufficient accounts: {e}")
            raise AccountError(message=f"Failed to ensure sufficient accounts: {str(e)}")
    
    def get_assignment_statistics(self) -> Dict[str, any]:
        """
        Get current assignment statistics.
        
        Returns:
            Dictionary with assignment stats
        """
        return {
            "server": self.server,
            "total_accounts": self.assignment_state.total_accounts,
            "assigned_accounts": len(self.assignment_state.assigned_accounts),
            "assignment_counts": dict(self.assignment_state.assigned_accounts),
            "created_accounts": len(self.created_account_names),
            "created_account_names": list(self.created_account_names)
        }




