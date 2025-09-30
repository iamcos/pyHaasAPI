"""
Testing Data Management for pyHaasAPI v2

This module provides functionality for creating and managing test data
(labs, bots, accounts) for testing workflows as requested by the user.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.logging import get_logger
from ..exceptions import TestingError, LabError, BotError, AccountError
from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.script import ScriptAPI
from ..api.market import MarketAPI
from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager

logger = get_logger("testing_manager")


class TestDataType(Enum):
    """Types of test data to manage"""
    LABS = "labs"
    BOTS = "bots"
    ACCOUNTS = "accounts"
    ALL = "all"


class TestDataScope(Enum):
    """Scope of test data operations"""
    CREATE = "create"
    CLEANUP = "cleanup"
    ISOLATE = "isolate"
    VALIDATE = "validate"


@dataclass
class TestDataConfig:
    """Configuration for test data management"""
    data_type: TestDataType
    scope: TestDataScope
    prefix: str = "TEST_"
    max_items: int = 10
    isolation_enabled: bool = True
    auto_cleanup: bool = True
    cleanup_after_hours: int = 24
    validation_enabled: bool = True


@dataclass
class TestDataResult:
    """Result of test data operation"""
    operation_id: str
    data_type: TestDataType
    scope: TestDataScope
    items_created: List[str]
    items_cleaned: List[str]
    items_validated: List[str]
    operation_timestamp: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class TestLabConfig:
    """Configuration for test lab creation"""
    lab_name: str
    script_id: str
    market_tag: str
    account_id: str
    start_date: str
    end_date: str
    initial_balance: float = 10000.0
    leverage: float = 20.0


@dataclass
class TestBotConfig:
    """Configuration for test bot creation"""
    bot_name: str
    lab_id: str
    backtest_id: str
    account_id: str
    market_tag: str
    trade_amount: float = 1000.0
    leverage: float = 20.0
    position_mode: str = "HEDGE"
    margin_mode: str = "CROSS"


@dataclass
class TestAccountConfig:
    """Configuration for test account creation"""
    account_name: str
    account_type: str = "SIMULATED"
    initial_balance: float = 10000.0
    currency: str = "USDT"


class TestingManager:
    """
    Testing Data Manager for creating and managing test data.

    Provides comprehensive test data management including creation, cleanup,
    isolation, and validation for testing workflows as requested by the user.
    """

    def __init__(
        self,
        lab_api: LabAPI,
        bot_api: BotAPI,
        account_api: AccountAPI,
        script_api: ScriptAPI,
        market_api: MarketAPI,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ):
        self.lab_api = lab_api
        self.bot_api = bot_api
        self.account_api = account_api
        self.script_api = script_api
        self.market_api = market_api
        self.client = client
        self.auth_manager = auth_manager
        self.logger = get_logger("testing_manager")

    # Main Test Data Operations

    async def manage_test_data(self, config: TestDataConfig) -> TestDataResult:
        """
        Manage test data based on configuration.

        Args:
            config: Test data configuration

        Returns:
            TestDataResult with operation details

        Raises:
            TestingError: If test data management fails
        """
        try:
            self.logger.info(f"Managing test data: {config.data_type.value} - {config.scope.value}")

            operation_id = f"test_{config.data_type.value}_{config.scope.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            items_created = []
            items_cleaned = []
            items_validated = []

            if config.scope == TestDataScope.CREATE:
                items_created = await self._create_test_data(config)
            elif config.scope == TestDataScope.CLEANUP:
                items_cleaned = await self._cleanup_test_data(config)
            elif config.scope == TestDataScope.ISOLATE:
                items_created = await self._isolate_test_data(config)
            elif config.scope == TestDataScope.VALIDATE:
                items_validated = await self._validate_test_data(config)

            return TestDataResult(
                operation_id=operation_id,
                data_type=config.data_type,
                scope=config.scope,
                items_created=items_created,
                items_cleaned=items_cleaned,
                items_validated=items_validated,
                operation_timestamp=datetime.now().isoformat(),
                success=True
            )

        except Exception as e:
            self.logger.error(f"Failed to manage test data: {e}")
            return TestDataResult(
                operation_id="",
                data_type=config.data_type,
                scope=config.scope,
                items_created=[],
                items_cleaned=[],
                items_validated=[],
                operation_timestamp=datetime.now().isoformat(),
                success=False,
                error_message=str(e)
            )

    # Test Data Creation

    async def _create_test_data(self, config: TestDataConfig) -> List[str]:
        """Create test data based on configuration"""
        created_items = []

        try:
            if config.data_type in [TestDataType.LABS, TestDataType.ALL]:
                created_items.extend(await self._create_test_labs(config))

            if config.data_type in [TestDataType.BOTS, TestDataType.ALL]:
                created_items.extend(await self._create_test_bots(config))

            if config.data_type in [TestDataType.ACCOUNTS, TestDataType.ALL]:
                created_items.extend(await self._create_test_accounts(config))

            return created_items

        except Exception as e:
            self.logger.error(f"Failed to create test data: {e}")
            raise TestingError(f"Failed to create test data: {e}") from e

    async def _create_test_labs(self, config: TestDataConfig) -> List[str]:
        """Create test labs"""
        created_labs = []

        try:
            # Get available scripts and markets
            scripts = await self.script_api.get_all_scripts()
            markets = await self.market_api.get_trade_markets()
            accounts = await self.account_api.get_all_accounts()

            if not scripts or not markets or not accounts:
                self.logger.warning("Insufficient data to create test labs")
                return created_labs

            # Create test labs
            for i in range(min(config.max_items, 5)):  # Limit to 5 test labs
                try:
                    script = scripts[i % len(scripts)]
                    market = markets[i % len(markets)]
                    account = accounts[i % len(accounts)]

                    lab_name = f"{config.prefix}Lab_{i+1}_{datetime.now().strftime('%H%M%S')}"

                    # Create lab
                    lab = await self.lab_api.create_lab(
                        lab_name=lab_name,
                        script_id=script.script_id,
                        market_tag=market.market_tag,
                        account_id=account.account_id,
                        start_date="2023-01-01",
                        end_date="2023-12-31",
                        initial_balance=10000.0,
                        leverage=20.0
                    )

                    if lab:
                        created_labs.append(lab.lab_id)
                        self.logger.info(f"✅ Created test lab: {lab.lab_id}")

                except Exception as e:
                    self.logger.warning(f"Failed to create test lab {i+1}: {e}")
                    continue

            return created_labs

        except Exception as e:
            self.logger.error(f"Failed to create test labs: {e}")
            raise TestingError(f"Failed to create test labs: {e}") from e

    async def _create_test_bots(self, config: TestDataConfig) -> List[str]:
        """Create test bots"""
        created_bots = []

        try:
            # Get available labs with backtests
            labs = await self.lab_api.get_labs()
            accounts = await self.account_api.get_all_accounts()

            if not labs or not accounts:
                self.logger.warning("Insufficient data to create test bots")
                return created_bots

            # Find labs with backtests
            labs_with_backtests = []
            for lab in labs:
                try:
                    backtests = await self.lab_api.get_backtest_result(lab.lab_id, 0, 1)
                    if backtests and hasattr(backtests, 'items') and backtests.items:
                        labs_with_backtests.append((lab, backtests.items[0]))
                except Exception:
                    continue

            if not labs_with_backtests:
                self.logger.warning("No labs with backtests found for test bot creation")
                return created_bots

            # Create test bots
            for i in range(min(config.max_items, 3)):  # Limit to 3 test bots
                try:
                    lab, backtest = labs_with_backtests[i % len(labs_with_backtests)]
                    account = accounts[i % len(accounts)]

                    bot_name = f"{config.prefix}Bot_{i+1}_{datetime.now().strftime('%H%M%S')}"

                    # Create bot from lab backtest
                    bot = await self.bot_api.create_bot_from_lab(
                        lab_id=lab.lab_id,
                        backtest_id=backtest.backtest_id,
                        account_id=account.account_id,
                        bot_name=bot_name,
                        trade_amount=1000.0,
                        leverage=20.0
                    )

                    if bot:
                        created_bots.append(bot.bot_id)
                        self.logger.info(f"✅ Created test bot: {bot.bot_id}")

                except Exception as e:
                    self.logger.warning(f"Failed to create test bot {i+1}: {e}")
                    continue

            return created_bots

        except Exception as e:
            self.logger.error(f"Failed to create test bots: {e}")
            raise TestingError(f"Failed to create test bots: {e}") from e

    async def _create_test_accounts(self, config: TestDataConfig) -> List[str]:
        """Create test accounts"""
        created_accounts = []

        try:
            # Note: Account creation might not be available in all API versions
            # This is a placeholder for the functionality
            self.logger.info("Test account creation not implemented - accounts are typically managed externally")
            return created_accounts

        except Exception as e:
            self.logger.error(f"Failed to create test accounts: {e}")
            raise TestingError(f"Failed to create test accounts: {e}") from e

    # Test Data Cleanup

    async def _cleanup_test_data(self, config: TestDataConfig) -> List[str]:
        """Cleanup test data based on configuration"""
        cleaned_items = []

        try:
            if config.data_type in [TestDataType.LABS, TestDataType.ALL]:
                cleaned_items.extend(await self._cleanup_test_labs(config))

            if config.data_type in [TestDataType.BOTS, TestDataType.ALL]:
                cleaned_items.extend(await self._cleanup_test_bots(config))

            if config.data_type in [TestDataType.ACCOUNTS, TestDataType.ALL]:
                cleaned_items.extend(await self._cleanup_test_accounts(config))

            return cleaned_items

        except Exception as e:
            self.logger.error(f"Failed to cleanup test data: {e}")
            raise TestingError(f"Failed to cleanup test data: {e}") from e

    async def _cleanup_test_labs(self, config: TestDataConfig) -> List[str]:
        """Cleanup test labs"""
        cleaned_labs = []

        try:
            # Get all labs
            labs = await self.lab_api.get_labs()

            # Find test labs (those with the test prefix)
            test_labs = [lab for lab in labs if lab.lab_name.startswith(config.prefix)]

            # Cleanup test labs
            for lab in test_labs:
                try:
                    # Delete the lab
                    success = await self.lab_api.delete_lab(lab.lab_id)
                    if success:
                        cleaned_labs.append(lab.lab_id)
                        self.logger.info(f"✅ Cleaned up test lab: {lab.lab_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup test lab {lab.lab_id}: {e}")
                    continue

            return cleaned_labs

        except Exception as e:
            self.logger.error(f"Failed to cleanup test labs: {e}")
            raise TestingError(f"Failed to cleanup test labs: {e}") from e

    async def _cleanup_test_bots(self, config: TestDataConfig) -> List[str]:
        """Cleanup test bots"""
        cleaned_bots = []

        try:
            # Get all bots
            bots = await self.bot_api.get_all_bots()

            # Find test bots (those with the test prefix)
            test_bots = [bot for bot in bots if bot.bot_name.startswith(config.prefix)]

            # Cleanup test bots
            for bot in test_bots:
                try:
                    # Delete the bot
                    success = await self.bot_api.delete_bot(bot.bot_id)
                    if success:
                        cleaned_bots.append(bot.bot_id)
                        self.logger.info(f"✅ Cleaned up test bot: {bot.bot_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup test bot {bot.bot_id}: {e}")
                    continue

            return cleaned_bots

        except Exception as e:
            self.logger.error(f"Failed to cleanup test bots: {e}")
            raise TestingError(f"Failed to cleanup test bots: {e}") from e

    async def _cleanup_test_accounts(self, config: TestDataConfig) -> List[str]:
        """Cleanup test accounts"""
        cleaned_accounts = []

        try:
            # Note: Account deletion might not be available in all API versions
            # This is a placeholder for the functionality
            self.logger.info("Test account cleanup not implemented - accounts are typically managed externally")
            return cleaned_accounts

        except Exception as e:
            self.logger.error(f"Failed to cleanup test accounts: {e}")
            raise TestingError(f"Failed to cleanup test accounts: {e}") from e

    # Test Data Isolation

    async def _isolate_test_data(self, config: TestDataConfig) -> List[str]:
        """Isolate test data for testing"""
        isolated_items = []

        try:
            # Get all items
            if config.data_type in [TestDataType.LABS, TestDataType.ALL]:
                labs = await self.lab_api.get_labs()
                test_labs = [lab for lab in labs if lab.lab_name.startswith(config.prefix)]
                isolated_items.extend([lab.lab_id for lab in test_labs])

            if config.data_type in [TestDataType.BOTS, TestDataType.ALL]:
                bots = await self.bot_api.get_all_bots()
                test_bots = [bot for bot in bots if bot.bot_name.startswith(config.prefix)]
                isolated_items.extend([bot.bot_id for bot in test_bots])

            if config.data_type in [TestDataType.ACCOUNTS, TestDataType.ALL]:
                accounts = await self.account_api.get_all_accounts()
                test_accounts = [acc for acc in accounts if acc.account_name.startswith(config.prefix)]
                isolated_items.extend([acc.account_id for acc in test_accounts])

            self.logger.info(f"✅ Isolated {len(isolated_items)} test items")
            return isolated_items

        except Exception as e:
            self.logger.error(f"Failed to isolate test data: {e}")
            raise TestingError(f"Failed to isolate test data: {e}") from e

    # Test Data Validation

    async def _validate_test_data(self, config: TestDataConfig) -> List[str]:
        """Validate test data"""
        validated_items = []

        try:
            if config.data_type in [TestDataType.LABS, TestDataType.ALL]:
                validated_items.extend(await self._validate_test_labs(config))

            if config.data_type in [TestDataType.BOTS, TestDataType.ALL]:
                validated_items.extend(await self._validate_test_bots(config))

            if config.data_type in [TestDataType.ACCOUNTS, TestDataType.ALL]:
                validated_items.extend(await self._validate_test_accounts(config))

            return validated_items

        except Exception as e:
            self.logger.error(f"Failed to validate test data: {e}")
            raise TestingError(f"Failed to validate test data: {e}") from e

    async def _validate_test_labs(self, config: TestDataConfig) -> List[str]:
        """Validate test labs"""
        validated_labs = []

        try:
            # Get all labs
            labs = await self.lab_api.get_labs()

            # Find test labs
            test_labs = [lab for lab in labs if lab.lab_name.startswith(config.prefix)]

            # Validate each test lab
            for lab in test_labs:
                try:
                    # Get lab details
                    details = await self.lab_api.get_lab_details(lab.lab_id)
                    if details:
                        validated_labs.append(lab.lab_id)
                        self.logger.info(f"✅ Validated test lab: {lab.lab_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to validate test lab {lab.lab_id}: {e}")
                    continue

            return validated_labs

        except Exception as e:
            self.logger.error(f"Failed to validate test labs: {e}")
            raise TestingError(f"Failed to validate test labs: {e}") from e

    async def _validate_test_bots(self, config: TestDataConfig) -> List[str]:
        """Validate test bots"""
        validated_bots = []

        try:
            # Get all bots
            bots = await self.bot_api.get_all_bots()

            # Find test bots
            test_bots = [bot for bot in bots if bot.bot_name.startswith(config.prefix)]

            # Validate each test bot
            for bot in test_bots:
                try:
                    # Get bot details
                    details = await self.bot_api.get_bot_details(bot.bot_id)
                    if details:
                        validated_bots.append(bot.bot_id)
                        self.logger.info(f"✅ Validated test bot: {bot.bot_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to validate test bot {bot.bot_id}: {e}")
                    continue

            return validated_bots

        except Exception as e:
            self.logger.error(f"Failed to validate test bots: {e}")
            raise TestingError(f"Failed to validate test bots: {e}") from e

    async def _validate_test_accounts(self, config: TestDataConfig) -> List[str]:
        """Validate test accounts"""
        validated_accounts = []

        try:
            # Get all accounts
            accounts = await self.account_api.get_all_accounts()

            # Find test accounts
            test_accounts = [acc for acc in accounts if acc.account_name.startswith(config.prefix)]

            # Validate each test account
            for account in test_accounts:
                try:
                    # Get account data
                    data = await self.account_api.get_account_data(account.account_id)
                    if data:
                        validated_accounts.append(account.account_id)
                        self.logger.info(f"✅ Validated test account: {account.account_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to validate test account {account.account_id}: {e}")
                    continue

            return validated_accounts

        except Exception as e:
            self.logger.error(f"Failed to validate test accounts: {e}")
            raise TestingError(f"Failed to validate test accounts: {e}") from e

    # Utility Methods

    async def get_test_data_summary(self, prefix: str = "TEST_") -> Dict[str, Any]:
        """
        Get summary of test data.

        Args:
            prefix: Prefix to identify test data

        Returns:
            Dictionary with test data summary
        """
        try:
            summary = {
                "test_labs": 0,
                "test_bots": 0,
                "test_accounts": 0,
                "total_test_items": 0,
                "summary_timestamp": datetime.now().isoformat()
            }

            # Count test labs
            labs = await self.lab_api.get_labs()
            test_labs = [lab for lab in labs if lab.lab_name.startswith(prefix)]
            summary["test_labs"] = len(test_labs)

            # Count test bots
            bots = await self.bot_api.get_all_bots()
            test_bots = [bot for bot in bots if bot.bot_name.startswith(prefix)]
            summary["test_bots"] = len(test_bots)

            # Count test accounts
            accounts = await self.account_api.get_all_accounts()
            test_accounts = [acc for acc in accounts if acc.account_name.startswith(prefix)]
            summary["test_accounts"] = len(test_accounts)

            summary["total_test_items"] = summary["test_labs"] + summary["test_bots"] + summary["test_accounts"]

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get test data summary: {e}")
            return {"error": str(e)}

    async def cleanup_old_test_data(self, prefix: str = "TEST_", hours_old: int = 24) -> int:
        """
        Cleanup old test data.

        Args:
            prefix: Prefix to identify test data
            hours_old: Number of hours after which to delete test data

        Returns:
            Number of items cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_old)
            cleaned_count = 0

            # Cleanup old test labs
            labs = await self.lab_api.get_labs()
            for lab in labs:
                if (lab.lab_name.startswith(prefix) and 
                    hasattr(lab, 'created_at') and 
                    lab.created_at < cutoff_time):
                    try:
                        await self.lab_api.delete_lab(lab.lab_id)
                        cleaned_count += 1
                        self.logger.info(f"Cleaned up old test lab: {lab.lab_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to cleanup old test lab {lab.lab_id}: {e}")

            # Cleanup old test bots
            bots = await self.bot_api.get_all_bots()
            for bot in bots:
                if (bot.bot_name.startswith(prefix) and 
                    hasattr(bot, 'created_at') and 
                    bot.created_at < cutoff_time):
                    try:
                        await self.bot_api.delete_bot(bot.bot_id)
                        cleaned_count += 1
                        self.logger.info(f"Cleaned up old test bot: {bot.bot_id}")
                    except Exception as e:
                        self.logger.warning(f"Failed to cleanup old test bot {bot.bot_id}: {e}")

            return cleaned_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old test data: {e}")
            return 0
