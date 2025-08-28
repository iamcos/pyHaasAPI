#!/usr/bin/env python3
"""
Lab to Bot Automation - Account Manager
======================================

Consolidated account creation and management system for the Lab to Bot Automation.
Handles account discovery, creation, funding, and cleanup operations.

Features:
- Account discovery and inventory management
- Automated account creation with proper naming
- Currency withdrawal and USDT funding
- Account reservation system for bot creation
- Comprehensive error handling and logging

Requirements:
- HaasOnline API connection
- pyHaasAPI library
- Valid API credentials

Author: AI Assistant
Version: 1.0
"""

import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pyHaasAPI import api
from pyHaasAPI.api import SyncExecutor, Authenticated, HaasApiError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AccountConfig:
    """Configuration for account creation and management"""
    account_suffix: str = "-10k"  # Server adds [Sim] prefix automatically
    initial_balance: float = 10000.0
    required_currency: str = "USDT"
    exchange: str = "BINANCEFUTURES"
    creation_delay: float = 0.1  # Delay between account creations
    max_retries: int = 3

@dataclass
class AccountInfo:
    """Information about a trading account"""
    account_id: str
    name: str
    has_bot: bool = False
    balance_usdt: float = 0.0
    total_balance_usdt: float = 0.0

class AccountManager:
    """
    Consolidated account creation and management system
    """

    def __init__(self, executor: SyncExecutor[Authenticated], config: AccountConfig = None):
        """
        Initialize the Account Manager

        Args:
            executor: Authenticated HaasOnline API executor
            config: Account creation configuration
        """
        self.executor = executor
        self.config = config or AccountConfig()
        self.logger = logger

    def generate_account_names(self, start_letter: str = "A", count: int = 100) -> List[str]:
        """
        Generate account names following the naming convention

        Args:
            start_letter: Starting letter for account names (A, B, C, etc.)
            count: Number of account names to generate

        Returns:
            List of account names
        """
        names = []
        current_letter = start_letter.upper()

        for i in range(count):
            # Generate names like 4AA-10k, 4AB-10k, 4AC-10k, etc.
            second_letter = chr(ord('A') + (i // 26))
            third_letter = chr(ord('A') + (i % 26))

            if second_letter > 'Z':
                # If we exceed Z, we could extend the pattern, but for now let's keep it simple
                second_letter = 'Z'

            account_name = f"4{current_letter}{second_letter}{third_letter}{self.config.account_suffix}"
            names.append(account_name)

        return names

    def get_existing_accounts(self) -> List[AccountInfo]:
        """
        Discover all existing accounts and their status

        Returns:
            List of AccountInfo objects
        """
        try:
            accounts = api.get_accounts(self.executor)
            account_infos = []

            for account in accounts:
                # Get account balance to determine USDT holdings
                try:
                    balance_data = api.get_account_balance(self.executor, account.account_id)

                    usdt_balance = 0.0
                    total_balance_usdt = 0.0

                    if balance_data.get("I"):
                        for wallet in balance_data["I"]:
                            currency = wallet.get("C", "")
                            amount = float(wallet.get("A", 0))

                            if currency == "USDT":
                                usdt_balance = amount
                                total_balance_usdt += amount
                            elif amount > 0:
                                # Convert other currencies to USDT equivalent (simplified)
                                # In a real implementation, you'd use exchange rates
                                total_balance_usdt += amount

                    account_info = AccountInfo(
                        account_id=account.account_id,
                        name=account.name,
                        has_bot=account.has_bot_associated,
                        balance_usdt=usdt_balance,
                        total_balance_usdt=total_balance_usdt
                    )
                    account_infos.append(account_info)

                except Exception as e:
                    self.logger.warning(f"Failed to get balance for account {account.name}: {e}")
                    account_infos.append(AccountInfo(
                        account_id=account.account_id,
                        name=account.name,
                        has_bot=account.has_bot_associated
                    ))

            self.logger.info(f"Discovered {len(account_infos)} existing accounts")
            return account_infos

        except HaasApiError as e:
            self.logger.error(f"Failed to get existing accounts: {e}")
            raise

    def find_free_accounts(self, required_count: int = 10) -> List[AccountInfo]:
        """
        Find accounts that are available for bot creation (no associated bots)

        Args:
            required_count: Number of free accounts needed

        Returns:
            List of free AccountInfo objects
        """
        all_accounts = self.get_existing_accounts()
        free_accounts = [acc for acc in all_accounts if not acc.has_bot]

        if len(free_accounts) >= required_count:
            selected = free_accounts[:required_count]
            self.logger.info(f"Found {len(selected)} free accounts for bot creation")
            return selected
        else:
            self.logger.warning(f"Only found {len(free_accounts)} free accounts, need {required_count}")
            return free_accounts

    def create_account(self, account_name: str) -> Optional[str]:
        """
        Create a new simulated account

        Args:
            account_name: Name for the new account (without [Sim] prefix)

        Returns:
            Account ID if successful, None if failed
        """
        try:
            self.logger.info(f"Creating account: {account_name}")

            response = self.executor._execute_inner(
                endpoint="Account",
                response_type=dict,
                query_params={
                    "channel": "ADD_SIMULATED_ACCOUNT",
                    "name": account_name,
                    "drivercode": self.config.exchange,
                    "drivertype": 2,
                    "interfacekey": self.executor.state.interface_key,
                    "userid": self.executor.state.user_id,
                }
            )

            if response.Success and response.Data:
                account_id = response.Data.get("AID")
                if account_id:
                    self.logger.info(f"Successfully created account {account_name} with ID: {account_id}")
                    return account_id
                else:
                    self.logger.error(f"Account creation succeeded but no AID returned for {account_name}")
                    return None
            else:
                error_msg = response.Error if hasattr(response, 'Error') and response.Error else 'Unknown error'
                self.logger.error(f"Failed to create account {account_name}: {error_msg}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating account {account_name}: {e}")
            return None

    def withdraw_all_currencies(self, account_id: str) -> bool:
        """
        Withdraw all currencies from an account (including USDT)

        Args:
            account_id: ID of the account to withdraw from

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Withdrawing all currencies from account {account_id}")

            # Get current balance
            balance_data = api.get_account_balance(self.executor, account_id)

            if not balance_data.get("I"):
                self.logger.info(f"No currencies to withdraw from account {account_id}")
                return True

            success_count = 0
            total_count = 0

            # Withdraw each currency individually
            for wallet in balance_data["I"]:
                currency = wallet.get("C")
                wallet_id = wallet.get("WT")
                amount = wallet.get("A")

                if currency and wallet_id and amount and amount > 0:
                    total_count += 1
                    try:
                        self.logger.debug(f"Withdrawing {amount} {currency} from account {account_id}")

                        self.executor._execute_inner(
                            endpoint="Account",
                            response_type=bool,
                            query_params={
                                "channel": "WITHDRAWAL_FUNDS",
                                "accountid": account_id,
                                "currency": currency,
                                "walletid": wallet_id,
                                "amount": amount,
                                "interfacekey": self.executor.state.interface_key,
                                "userid": self.executor.state.user_id,
                            }
                        )

                        success_count += 1
                        self.logger.debug(f"Successfully withdrew {amount} {currency}")

                    except Exception as e:
                        self.logger.error(f"Failed to withdraw {currency} from account {account_id}: {e}")

            self.logger.info(f"Withdrew {success_count}/{total_count} currencies from account {account_id}")
            return success_count == total_count

        except Exception as e:
            self.logger.error(f"Error withdrawing currencies from account {account_id}: {e}")
            return False

    def deposit_usdt(self, account_id: str, amount: float) -> bool:
        """
        Deposit USDT to an account

        Args:
            account_id: ID of the account to deposit to
            amount: Amount of USDT to deposit

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Depositing {amount} USDT to account {account_id}")

            success = api.deposit_funds(
                self.executor,
                account_id,
                self.config.required_currency,
                self.config.required_currency,
                amount
            )

            if success:
                self.logger.info(f"Successfully deposited {amount} USDT to account {account_id}")
                return True
            else:
                self.logger.error(f"Failed to deposit {amount} USDT to account {account_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error depositing USDT to account {account_id}: {e}")
            return False

    def create_and_fund_account(self, account_name: str) -> Optional[AccountInfo]:
        """
        Create a new account and fund it with the configured amount

        Args:
            account_name: Name for the new account

        Returns:
            AccountInfo if successful, None if failed
        """
        try:
            # Step 1: Create account
            account_id = self.create_account(account_name)
            if not account_id:
                return None

            # Step 2: Withdraw all currencies
            if not self.withdraw_all_currencies(account_id):
                self.logger.warning(f"Failed to withdraw all currencies from {account_name}, continuing with deposit")

            # Step 3: Deposit USDT
            if not self.deposit_usdt(account_id, self.config.initial_balance):
                self.logger.error(f"Failed to deposit USDT to {account_name}")
                return None

            # Verify final balance
            try:
                balance_data = api.get_account_balance(self.executor, account_id)
                usdt_balance = 0.0

                if balance_data.get("I"):
                    for wallet in balance_data["I"]:
                        if wallet.get("C") == "USDT":
                            usdt_balance = float(wallet.get("A", 0))
                            break

                if abs(usdt_balance - self.config.initial_balance) < 0.01:  # Allow small rounding differences
                    self.logger.info(f"Account {account_name} successfully created and funded with {usdt_balance} USDT")
                    return AccountInfo(
                        account_id=account_id,
                        name=account_name,
                        balance_usdt=usdt_balance,
                        total_balance_usdt=usdt_balance
                    )
                else:
                    self.logger.error(f"Account {account_name} has incorrect balance: {usdt_balance}, expected {self.config.initial_balance}")
                    return None

            except Exception as e:
                self.logger.error(f"Failed to verify balance for account {account_name}: {e}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating and funding account {account_name}: {e}")
            return None

    def create_accounts_batch(self, account_names: List[str]) -> List[AccountInfo]:
        """
        Create and fund multiple accounts

        Args:
            account_names: List of account names to create

        Returns:
            List of successfully created AccountInfo objects
        """
        created_accounts = []

        self.logger.info(f"Starting batch creation of {len(account_names)} accounts")

        for account_name in account_names:
            account_info = self.create_and_fund_account(account_name)
            if account_info:
                created_accounts.append(account_info)

            # Small delay between creations to avoid overwhelming the API
            if self.config.creation_delay > 0:
                time.sleep(self.config.creation_delay)

        self.logger.info(f"Successfully created {len(created_accounts)}/{len(account_names)} accounts")
        return created_accounts

    def reserve_accounts_for_bots(self, bot_count: int) -> List[AccountInfo]:
        """
        Find or create accounts needed for bot creation
        Handles the edge case where ZERO accounts exist in the system

        Args:
            bot_count: Number of bots to create (accounts needed)

        Returns:
            List of AccountInfo objects ready for bot creation
        """
        self.logger.info(f"Reserving {bot_count} accounts for bot creation")

        # First, try to find existing free accounts
        free_accounts = self.find_free_accounts(bot_count)

        # Handle the ZERO accounts scenario
        if len(free_accounts) == 0:
            all_accounts = self.get_existing_accounts()
            if len(all_accounts) == 0:
                self.logger.info("🚨 ZERO accounts found in system - bootstrapping from empty state")
                return self._bootstrap_from_empty_state(bot_count)

        if len(free_accounts) >= bot_count:
            self.logger.info(f"Using {len(free_accounts)} existing free accounts")
            return free_accounts

        # If we need more accounts, create them
        accounts_needed = bot_count - len(free_accounts)
        self.logger.info(f"Need to create {accounts_needed} additional accounts")

        # Generate account names for new accounts
        existing_names = [acc.name for acc in self.get_existing_accounts()]
        new_names = []

        # Start from a letter that doesn't conflict with existing accounts
        start_letter = "A"
        while len(new_names) < accounts_needed:
            candidate_names = self.generate_account_names(start_letter, accounts_needed * 2)
            for name in candidate_names:
                if name not in existing_names and name not in new_names:
                    new_names.append(name)
                    if len(new_names) >= accounts_needed:
                        break
            start_letter = chr(ord(start_letter) + 1)

        # Create the new accounts
        new_accounts = self.create_accounts_batch(new_names[:accounts_needed])

        # Combine existing free accounts with newly created ones
        all_accounts = free_accounts + new_accounts

        if len(all_accounts) >= bot_count:
            selected_accounts = all_accounts[:bot_count]
            self.logger.info(f"Reserved {len(selected_accounts)} accounts for bot creation")
            return selected_accounts
        else:
            self.logger.warning(f"Could only reserve {len(all_accounts)} accounts, needed {bot_count}")
            return all_accounts

    def _bootstrap_from_empty_state(self, bot_count: int) -> List[AccountInfo]:
        """
        Bootstrap account creation for YOUR SPECIFIC HaasOnline setup

        This creates accounts following YOUR exact specifications:
        - Naming: 4AA-10k, 4AB-10k, 4AC-10k, etc. (server adds [Sim] prefix)
        - Balance: Exactly 10,000 USDT per account
        - Exchange: Binance Futures
        - Process: Withdraw all currencies → Deposit 10,000 USDT

        Args:
            bot_count: Number of accounts needed

        Returns:
            List of created AccountInfo objects ready for YOUR bot deployment
        """
        self.logger.info(f"🔄 Bootstrapping YOUR HaasOnline setup - creating {bot_count} accounts")
        self.logger.info(f"   📝 Using YOUR naming convention: 4AA-10k, 4AB-10k, etc.")
        self.logger.info(f"   💰 Using YOUR balance requirement: 10,000 USDT per account")
        self.logger.info(f"   🔄 Using YOUR process: Withdraw all → Deposit 10,000 USDT")

        # Generate initial account names following YOUR specific pattern
        initial_names = self.generate_account_names("A", bot_count)

        # Create accounts using YOUR specific 3-step process
        created_accounts = self.create_accounts_batch(initial_names)

        if len(created_accounts) >= bot_count:
            selected_accounts = created_accounts[:bot_count]
            self.logger.info(f"✅ Bootstrap complete - {len(selected_accounts)} accounts ready for YOUR bots")
            self.logger.info(f"   📊 Accounts created with YOUR specifications:")
            for account in selected_accounts:
                self.logger.info(f"      • [{account.name}] - 10,000 USDT balance")
            return selected_accounts
        else:
            self.logger.warning(f"⚠️  Bootstrap partial - only {len(created_accounts)} accounts created, needed {bot_count}")
            return created_accounts

def main():
    """Example usage of AccountManager"""
    # This would typically be called from the main automation script
    print("Account Manager module loaded successfully")
    print("Use AccountManager class to create and manage trading accounts")

if __name__ == "__main__":
    main()
