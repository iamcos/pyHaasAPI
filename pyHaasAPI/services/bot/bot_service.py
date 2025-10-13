"""
Bot Service for pyHaasAPI v2

This module provides business logic for bot management, using proven working patterns
from the existing CLI tools and bot creation modules.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...api.bot import BotAPI
from ...api.account import AccountAPI
from ...api.backtest import BacktestAPI
from ...api.market import MarketAPI
from ...core.client import AsyncHaasClient
from ...core.auth import AuthenticationManager
from ...exceptions import BotError, BotNotFoundError, BotCreationError
from ...core.logging import get_logger
from ...models.bot import BotDetails, BotRecord, BotConfiguration, CreateBotRequest
from ...models.backtest import BacktestResult
from ..server_content_manager import ServerContentManager

logger = get_logger("bot_service")


@dataclass
class BotCreationResult:
    """Result of bot creation with comprehensive details"""
    bot_id: str
    bot_name: str
    backtest_id: str
    account_id: str
    market_tag: str
    leverage: float
    margin_mode: str
    position_mode: str
    trade_amount_usdt: float
    creation_timestamp: str
    success: bool
    activated: bool
    error_message: Optional[str] = None


@dataclass
class MassBotCreationResult:
    """Result of mass bot creation operation"""
    total_labs_processed: int
    total_bots_created: int
    total_bots_activated: int
    successful_labs: List[str]
    failed_labs: List[str]
    bot_results: List[BotCreationResult]
    creation_timestamp: str


@dataclass
class BotValidationResult:
    """Result of bot validation"""
    bot_id: str
    is_valid: bool
    validation_errors: List[str]
    recommendations: List[str]
    risk_score: float
    estimated_daily_pnl: Optional[float] = None


class BotService:
    """
    Bot Service with business logic for bot management.

    Provides comprehensive bot functionality including creation, configuration,
    monitoring, and management using proven working patterns from v1.
    """

    def __init__(
        self,
        bot_api: BotAPI,
        account_api: AccountAPI,
        backtest_api: BacktestAPI,
        market_api: MarketAPI,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager,
        server_content_manager: Optional[ServerContentManager] = None
    ):
        self.bot_api = bot_api
        self.account_api = account_api
        self.backtest_api = backtest_api
        self.market_api = market_api
        self.client = client
        self.auth_manager = auth_manager
        self.server_content_manager = server_content_manager
        self.logger = get_logger("bot_service")

    # Duplicate Detection and Bot Creation

    async def check_duplicate_bot(
        self,
        lab_id: str,
        backtest_id: str,
        bot_name: str,
        existing_bots: Optional[List[Any]] = None
    ) -> bool:
        """
        Check if a bot with similar characteristics already exists.
        
        Args:
            lab_id: Lab ID for the bot
            backtest_id: Backtest ID for the bot
            bot_name: Proposed bot name
            existing_bots: Optional list of existing bots to check against
            
        Returns:
            True if duplicate found, False otherwise
        """
        if not self.server_content_manager:
            self.logger.warning("No ServerContentManager provided, skipping duplicate check")
            return False
            
        try:
            # Get existing bots if not provided
            if existing_bots is None:
                existing_bots = await self.bot_api.get_bots()
            
            # Check for duplicate by name
            for bot in existing_bots:
                existing_name = getattr(bot, 'bot_name', None) or getattr(bot, 'name', None)
                if existing_name and existing_name.strip().lower() == bot_name.strip().lower():
                    self.logger.info(f"Duplicate bot found by name: {bot_name}")
                    return True
                
                # Check for duplicate by origin backtest ID in notes
                notes = getattr(bot, 'notes', None) or ""
                if self.server_content_manager._extract_origin_backtest_id(notes) == backtest_id:
                    self.logger.info(f"Duplicate bot found by origin backtest: {backtest_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to check for duplicates: {e}")
            return False

    # Bot Creation from Lab Analysis

    async def create_bot_from_lab_analysis(
        self,
        lab_id: str,
        backtest_id: str,
        account_id: str,
        bot_name: Optional[str] = None,
        trade_amount_usdt: float = 2000.0,
        leverage: float = 20.0,
        activate: bool = False,
        lab_name: Optional[str] = None,
    ) -> BotCreationResult:
        """
        Create a bot from lab analysis using proven working patterns.

        Args:
            lab_id: ID of the lab containing the backtest
            backtest_id: ID of the backtest to use for bot creation
            account_id: Account ID for the bot
            bot_name: Optional custom bot name
            trade_amount_usdt: Trade amount in USDT
            leverage: Leverage for the bot
            activate: Whether to activate the bot immediately

        Returns:
            BotCreationResult with creation details

        Raises:
            BotCreationError: If bot creation fails
        """
        try:
            self.logger.info(f"Creating bot from lab {lab_id}, backtest {backtest_id}")

            # Check for duplicates before proceeding
            if bot_name:
                is_duplicate = await self.check_duplicate_bot(lab_id, backtest_id, bot_name)
                if is_duplicate:
                    self.logger.info(f"Skipping bot creation - duplicate found: {bot_name}")
                    return BotCreationResult(
                        bot_id="",
                        bot_name=bot_name,
                        backtest_id=backtest_id,
                        account_id=account_id,
                        market_tag="",
                        leverage=leverage,
                        margin_mode="",
                        position_mode="",
                        trade_amount_usdt=trade_amount_usdt,
                        creation_timestamp=datetime.now().isoformat(),
                        success=False,
                        activated=False,
                        error_message="Duplicate bot detected"
                    )

            # Get backtest details
            backtest_runtime = await self.backtest_api.get_full_backtest_runtime_data(lab_id, backtest_id)
            
            # Extract performance metrics
            metrics = self._extract_backtest_metrics(backtest_runtime)

            # Generate bot name if not provided (ROE + WR)
            if not bot_name:
                if metrics:
                    script_name = getattr(backtest_runtime, 'ScriptName', 'Unknown')
                    market_tag = getattr(backtest_runtime, 'PriceMarket', 'Unknown')
                    roe = metrics.get('roe_pct', 0.0)
                    wr = metrics.get('winrate_pct', 0.0)
                    bot_name = f"{script_name} - {market_tag} - ROE {roe:.1f}% WR {wr:.1f}%"
                else:
                    bot_name = self._generate_bot_name(backtest_runtime)

            # Create bot from lab backtest
            bot_details = await self.bot_api.create_bot_from_lab(
                lab_id=lab_id,
                backtest_id=backtest_id,
                account_id=account_id,
                bot_name=bot_name,
                trade_amount_usdt=trade_amount_usdt,
                leverage=leverage
            )

            # Configure bot with standard settings
            await self._configure_bot_standard_settings(bot_details.bot_id, leverage)

            # Write provenance/analysis notes
            try:
                gen_idx, pop_idx = self._extract_generation_population(backtest_runtime, backtest_id)
                notes_payload = {
                    "origin": {
                        "lab_id": lab_id,
                        "lab_name": lab_name or "",
                        "backtest_id": backtest_id,
                        "generation_idx": gen_idx,
                        "population_idx": pop_idx,
                        "market": getattr(backtest_runtime, 'PriceMarket', ''),
                        "script_name": getattr(backtest_runtime, 'ScriptName', ''),
                        "creation_ts": datetime.utcnow().isoformat()
                    },
                    "backtest_baseline": {
                        "roe_pct": metrics.get('roe_pct') if metrics else None,
                        "winrate_pct": metrics.get('winrate_pct') if metrics else None,
                        "trades": metrics.get('trades') if metrics else None,
                        "max_drawdown_pct": metrics.get('max_drawdown_pct') if metrics else None,
                        "criteria_passed": True if metrics else False
                    },
                    "longest_backtest": {
                        "status": "queued",
                        "request_ts": datetime.utcnow().isoformat(),
                        "result_ts": None,
                        "roe_pct": None,
                        "winrate_pct": None,
                        "trades": None,
                        "max_drawdown_pct": None,
                        "history_synced_months": None,
                        "period": {"from": None, "to": None}
                    },
                    "account": {
                        "exchange": "BINANCEFUTURES",
                        "account_id": account_id,
                        "position_mode": "HEDGE",
                        "margin_mode": "CROSS",
                        "leverage": leverage,
                        "trade_amount_usdt": trade_amount_usdt
                    }
                }
                await self.bot_api.change_bot_notes(bot_details.bot_id, json_dumps_compact(notes_payload))
            except Exception as e:
                self.logger.warning(f"Failed to set bot notes for {bot_details.bot_id}: {e}")

            # Activate if requested
            activated = False
            if activate:
                try:
                    await self.bot_api.activate_bot(bot_details.bot_id)
                    activated = True
                    self.logger.info(f"✅ Bot activated: {bot_details.bot_id}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Bot created but activation failed: {e}")

            # Enqueue longest backtest for validation
            try:
                await self._enqueue_longest_backtest(bot_details.bot_id, backtest_runtime)
                self.logger.info(f"📊 Longest backtest queued for bot: {bot_details.bot_id}")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to enqueue longest backtest for bot {bot_details.bot_id}: {e}")

            return BotCreationResult(
                bot_id=bot_details.bot_id,
                bot_name=bot_details.bot_name,
                backtest_id=backtest_id,
                account_id=account_id,
                market_tag=backtest_runtime.PriceMarket,
                leverage=leverage,
                margin_mode="CROSS",
                position_mode="HEDGE",
                trade_amount_usdt=trade_amount_usdt,
                creation_timestamp=datetime.now().isoformat(),
                success=True,
                activated=activated
            )

        except Exception as e:
            self.logger.error(f"Failed to create bot from lab analysis: {e}")
            return BotCreationResult(
                bot_id="",
                bot_name=bot_name or "",
                backtest_id=backtest_id,
                account_id=account_id,
                market_tag="",
                leverage=leverage,
                margin_mode="",
                position_mode="",
                trade_amount_usdt=trade_amount_usdt,
                creation_timestamp=datetime.now().isoformat(),
                success=False,
                activated=False,
                error_message=str(e)
            )

    async def create_mass_bots_from_labs(
        self,
        lab_ids: List[str],
        top_count: int = 5,
        min_win_rate: float = 0.6,
        min_trades: int = 10,
        trade_amount_usdt: float = 2000.0,
        leverage: float = 20.0,
        activate: bool = False,
        use_individual_accounts: bool = True
    ) -> MassBotCreationResult:
        """
        Create bots from multiple labs using proven mass creation patterns.

        Args:
            lab_ids: List of lab IDs to process
            top_count: Number of top backtests per lab
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            trade_amount_usdt: Trade amount in USDT
            leverage: Leverage for bots
            activate: Whether to activate bots
            use_individual_accounts: Whether to use individual accounts

        Returns:
            MassBotCreationResult with creation details
        """
        try:
            self.logger.info(f"Creating mass bots from {len(lab_ids)} labs")

            successful_labs = []
            failed_labs = []
            bot_results = []
            total_bots_created = 0
            total_bots_activated = 0

            # Get available accounts
            if use_individual_accounts:
                # Use auto-selection for individual accounts
                used_accounts = set()
            else:
                accounts = await self.account_api.get_accounts()
            if not accounts:
                raise BotCreationError("No accounts available for bot creation")
            account_index = 0

            for lab_id in lab_ids:
                try:
                    self.logger.info(f"Processing lab: {lab_id}")

                    # Get top performing backtests for this lab
                    top_backtests = await self.backtest_api.get_top_performing_backtests(
                        lab_id, top_count, sort_by="roi"
                    )

                    # Filter backtests by criteria
                    qualified_backtests = [
                        bt for bt in top_backtests
                        if bt.win_rate >= min_win_rate and bt.total_trades >= min_trades
                    ]

                    if not qualified_backtests:
                        self.logger.warning(f"No qualified backtests found for lab {lab_id}")
                        failed_labs.append(lab_id)
                        continue

                    # Create bots for qualified backtests
                    for backtest in qualified_backtests:
                        # Select account
                        if use_individual_accounts:
                            # Auto-select available BinanceFutures account
                            available_account = await self.account_api.get_available_binancefutures_account(
                                exclude_accounts=list(used_accounts)
                            )
                            if not available_account:
                                self.logger.warning("No available BinanceFutures accounts for bot creation")
                                failed_labs.append(lab_id)
                                break
                            account_id = available_account.account_id
                            used_accounts.add(account_id)
                        else:
                            account_id = accounts[account_index % len(accounts)].account_id
                            account_index += 1

                        # Create bot
                        bot_result = await self.create_bot_from_lab_analysis(
                            lab_id=lab_id,
                            backtest_id=backtest.backtest_id,
                            account_id=account_id,
                            trade_amount_usdt=trade_amount_usdt,
                            leverage=leverage,
                            activate=activate
                        )

                        bot_results.append(bot_result)
                        
                        if bot_result.success:
                            total_bots_created += 1
                            if bot_result.activated:
                                total_bots_activated += 1

                    successful_labs.append(lab_id)

                except Exception as e:
                    self.logger.error(f"Failed to process lab {lab_id}: {e}")
                    failed_labs.append(lab_id)

            return MassBotCreationResult(
                total_labs_processed=len(lab_ids),
                total_bots_created=total_bots_created,
                total_bots_activated=total_bots_activated,
                successful_labs=successful_labs,
                failed_labs=failed_labs,
                bot_results=bot_results,
                creation_timestamp=datetime.now().isoformat()
            )

        except Exception as e:
            self.logger.error(f"Failed to create mass bots: {e}")
            raise BotCreationError(f"Failed to create mass bots: {e}") from e

    # Bot Configuration and Management

    async def configure_bot_standard_settings(
        self,
        bot_id: str,
        leverage: float = 20.0,
        position_mode: str = "HEDGE",
        margin_mode: str = "CROSS"
    ) -> bool:
        """
        Configure bot with standard trading settings.

        Args:
            bot_id: ID of the bot to configure
            leverage: Leverage setting
            position_mode: Position mode (HEDGE/ONE_WAY)
            margin_mode: Margin mode (CROSS/ISOLATED)

        Returns:
            True if configuration was successful

        Raises:
            BotError: If configuration fails
        """
        try:
            self.logger.info(f"Configuring standard settings for bot {bot_id}")

            # Get bot details
            bot_details = await self.bot_api.get_bot_details(bot_id)
            if not bot_details:
                raise BotNotFoundError(f"Bot {bot_id} not found")

            # Configure leverage
            await self.account_api.set_leverage(
                bot_details.account_id,
                bot_details.market_tag,
                leverage
            )

            # Configure position mode
            position_mode_value = 1 if position_mode == "HEDGE" else 0
            await self.account_api.set_position_mode(
                bot_details.account_id,
                position_mode_value
            )

            # Configure margin mode
            margin_mode_value = 0 if margin_mode == "CROSS" else 1
            await self.account_api.set_margin_mode(
                bot_details.account_id,
                margin_mode_value
            )

            self.logger.info(f"✅ Bot configured successfully: {bot_id}")
            return True

        except BotNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to configure bot: {e}")
            raise BotError(f"Failed to configure bot {bot_id}: {e}") from e

    async def validate_bot_configuration(self, bot_id: str) -> BotValidationResult:
        """
        Validate bot configuration and provide recommendations.

        Args:
            bot_id: ID of the bot to validate

        Returns:
            BotValidationResult with validation details

        Raises:
            BotError: If validation fails
        """
        try:
            self.logger.info(f"Validating bot configuration: {bot_id}")

            # Get bot details
            bot_details = await self.bot_api.get_bot_details(bot_id)
            if not bot_details:
                raise BotNotFoundError(f"Bot {bot_id} not found")

            validation_errors = []
            recommendations = []
            risk_score = 0.0

            # Validate leverage
            if bot_details.leverage > 50:
                validation_errors.append("Leverage too high (>50x)")
                risk_score += 0.3
                recommendations.append("Consider reducing leverage to 20x or less")
            elif bot_details.leverage < 5:
                validation_errors.append("Leverage too low (<5x)")
                recommendations.append("Consider increasing leverage for better capital efficiency")

            # Validate trade amount
            account_balance = await self.account_api.get_account_balance(bot_details.account_id)
            if account_balance:
                balance_usdt = account_balance.get('USDT', 0)
                trade_amount_ratio = bot_details.trade_amount / balance_usdt if balance_usdt > 0 else 0
                
                if trade_amount_ratio > 0.5:
                    validation_errors.append("Trade amount too high relative to account balance")
                    risk_score += 0.4
                    recommendations.append("Consider reducing trade amount to 20% of account balance")
                elif trade_amount_ratio < 0.05:
                    validation_errors.append("Trade amount too low relative to account balance")
                    recommendations.append("Consider increasing trade amount for better returns")

            # Validate position mode
            if bot_details.position_mode != 1:  # HEDGE
                validation_errors.append("Position mode should be HEDGE for risk management")
                risk_score += 0.2
                recommendations.append("Set position mode to HEDGE")

            # Validate margin mode
            if bot_details.margin_mode != 0:  # CROSS
                validation_errors.append("Margin mode should be CROSS for better capital efficiency")
                recommendations.append("Set margin mode to CROSS")

            # Calculate estimated daily PnL (simplified)
            estimated_daily_pnl = None
            if bot_details.trade_amount and bot_details.leverage:
                # Very rough estimate based on typical trading patterns
                estimated_daily_pnl = bot_details.trade_amount * 0.01  # 1% daily return estimate

            return BotValidationResult(
                bot_id=bot_id,
                is_valid=len(validation_errors) == 0,
                validation_errors=validation_errors,
                recommendations=recommendations,
                risk_score=risk_score,
                estimated_daily_pnl=estimated_daily_pnl
            )

        except BotNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate bot configuration: {e}")
            raise BotError(f"Failed to validate bot {bot_id}: {e}") from e

    # Bot Monitoring and Health

    async def get_bot_health_status(self, bot_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health status for a bot.

        Args:
            bot_id: ID of the bot to check

        Returns:
            Dictionary with health status information

        Raises:
            BotError: If health check fails
        """
        try:
            self.logger.info(f"Checking health status for bot {bot_id}")

            # Get bot details
            bot_details = await self.bot_api.get_bot_details(bot_id)
            if not bot_details:
                raise BotNotFoundError(f"Bot {bot_id} not found")

            # Get bot orders and positions
            orders = await self.bot_api.get_bot_orders(bot_id)
            positions = await self.bot_api.get_bot_positions(bot_id)

            # Get account balance
            account_balance = await self.account_api.get_account_balance(bot_details.account_id)

            # Determine health status
            health_status = "healthy"
            issues = []
            warnings = []

            # Check if bot is active
            if not bot_details.is_active:
                health_status = "inactive"
                issues.append("Bot is not active")

            # Check for open orders
            if len(orders) > 10:
                health_status = "warning"
                warnings.append("High number of open orders")

            # Check for positions
            if len(positions) > 0:
                # Check position sizes
                for position in positions:
                    if abs(position.get('size', 0)) > bot_details.trade_amount * 2:
                        health_status = "warning"
                        warnings.append("Large position size detected")

            # Check account balance
            if account_balance:
                balance_usdt = account_balance.get('USDT', 0)
                if balance_usdt < bot_details.trade_amount * 2:
                    health_status = "warning"
                    warnings.append("Low account balance")

            return {
                "bot_id": bot_id,
                "bot_name": bot_details.bot_name,
                "health_status": health_status,
                "is_active": bot_details.is_active,
                "open_orders": len(orders),
                "open_positions": len(positions),
                "account_balance": account_balance,
                "last_updated": datetime.now().isoformat(),
                "issues": issues,
                "warnings": warnings,
                "recommendations": self._get_bot_health_recommendations(health_status, issues, warnings)
            }

        except BotNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get bot health status: {e}")
            raise BotError(f"Failed to get health status for bot {bot_id}: {e}") from e

    def _get_bot_health_recommendations(
        self, 
        health_status: str, 
        issues: List[str], 
        warnings: List[str]
    ) -> List[str]:
        """Get recommendations based on bot health status"""
        recommendations = []

        if health_status == "inactive":
            recommendations.append("Activate the bot to start trading")
        elif health_status == "warning":
            if "High number of open orders" in warnings:
                recommendations.append("Consider canceling some orders to reduce complexity")
            if "Low account balance" in warnings:
                recommendations.append("Add funds to account or reduce trade amount")
            if "Large position size" in warnings:
                recommendations.append("Monitor position sizes and consider reducing trade amount")

        return recommendations

    # Bot Performance and Analytics

    async def get_bot_performance_summary(self, bot_id: str) -> Dict[str, Any]:
        """
        Get comprehensive performance summary for a bot.

        Args:
            bot_id: ID of the bot to analyze

        Returns:
            Dictionary with performance summary

        Raises:
            BotError: If performance analysis fails
        """
        try:
            self.logger.info(f"Getting performance summary for bot {bot_id}")

            # Get bot details
            bot_details = await self.bot_api.get_bot_details(bot_id)
            if not bot_details:
                raise BotNotFoundError(f"Bot {bot_id} not found")

            # Get bot orders and positions
            orders = await self.bot_api.get_bot_orders(bot_id)
            positions = await self.bot_api.get_bot_positions(bot_id)

            # Get account balance
            account_balance = await self.account_api.get_account_balance(bot_details.account_id)

            # Calculate performance metrics
            total_orders = len(orders)
            open_positions = len(positions)
            
            # Calculate PnL from positions (simplified)
            total_pnl = 0.0
            for position in positions:
                total_pnl += position.get('unrealized_pnl', 0)

            return {
                "bot_id": bot_id,
                "bot_name": bot_details.bot_name,
                "market_tag": bot_details.market_tag,
                "leverage": bot_details.leverage,
                "trade_amount": bot_details.trade_amount,
                "is_active": bot_details.is_active,
                "total_orders": total_orders,
                "open_positions": open_positions,
                "total_pnl": total_pnl,
                "account_balance": account_balance,
                "performance_timestamp": datetime.now().isoformat()
            }

        except BotNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get bot performance summary: {e}")
            raise BotError(f"Failed to get performance summary for bot {bot_id}: {e}") from e

    # Utility Methods

    def _generate_bot_name(self, backtest_runtime: Any) -> str:
        """
        Generate a bot name based on backtest runtime data.

        Args:
            backtest_runtime: Backtest runtime data

        Returns:
            Generated bot name
        """
        try:
            # Extract information from backtest runtime
            script_name = getattr(backtest_runtime, 'ScriptName', 'Unknown')
            market_tag = getattr(backtest_runtime, 'PriceMarket', 'Unknown')
            
            # Use metrics when available
            roe = 0.0
            wr = 0.0
            try:
                metrics = self._extract_backtest_metrics(backtest_runtime)
                if metrics:
                    roe = metrics.get('roe_pct') or 0.0
                    wr = metrics.get('winrate_pct') or 0.0
            except Exception:
                pass

            bot_name = f"{script_name} - {market_tag} - ROE {roe:.1f}% WR {wr:.1f}%"
            return bot_name[:100]  # Limit length

        except Exception as e:
            self.logger.warning(f"Failed to generate bot name: {e}")
            return f"Bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def _configure_bot_standard_settings(
        self, 
        bot_id: str, 
        leverage: float
    ) -> None:
        """Configure bot with standard settings (internal method)"""
        try:
            await self.configure_bot_standard_settings(
                bot_id=bot_id,
                leverage=leverage,
                position_mode="HEDGE",
                margin_mode="CROSS"
            )
        except Exception as e:
            self.logger.warning(f"Failed to configure standard settings for bot {bot_id}: {e}")

    def _extract_backtest_metrics(self, backtest_runtime: Any) -> Optional[Dict[str, float]]:
        """Extract ROE, win rate, trades, and max drawdown from backtest runtime Reports.
        Supports both dict-like and attribute-style structures.
        """
        try:
            reports = None
            if hasattr(backtest_runtime, 'Reports'):
                reports = backtest_runtime.Reports
            elif isinstance(backtest_runtime, dict):
                reports = backtest_runtime.get('Reports')
            if not reports:
                return None
            # Take first report entry
            first_key = next(iter(reports.keys()))
            report = reports[first_key]
            # Normalize to dict
            if hasattr(report, 'model_dump'):
                report = report.model_dump(by_alias=True)
            elif hasattr(report, '__dict__'):
                report = report.__dict__
            # Sections: PR (performance), T (trades), P (positions)
            pr = report.get('PR', {}) if isinstance(report, dict) else {}
            t = report.get('T', {}) if isinstance(report, dict) else {}
            p = report.get('P', {}) if isinstance(report, dict) else {}

            # Win rate: prefer PR['WR'] (0..1), else compute from T
            winrate_pct = None
            wr_val = pr.get('WR') if isinstance(pr, dict) else None
            if isinstance(wr_val, (int, float)):
                winrate_pct = float(wr_val) * 100.0 if wr_val <= 1 else float(wr_val)
            # Trades
            trades = None
            if isinstance(pr.get('TR', None), (int, float)):
                trades = float(pr['TR'])
            elif isinstance(t.get('TR', None), (int, float)):
                trades = float(t['TR'])
            # ROE: prefer P['ROE'] or compute from realized profits
            roe_pct = None
            if isinstance(p.get('ROE', None), (int, float)):
                roe_pct = float(p['ROE'])
            elif isinstance(pr.get('ROE', None), (int, float)):
                roe_pct = float(pr['ROE'])
            # Max drawdown
            max_dd = None
            if isinstance(pr.get('MDD', None), (int, float)):
                max_dd = float(pr['MDD'])

            return {
                'roe_pct': roe_pct or 0.0,
                'winrate_pct': winrate_pct or 0.0,
                'trades': trades or 0.0,
                'max_drawdown_pct': max_dd or 0.0,
            }
        except Exception:
            return None

    def _extract_generation_population(self, backtest_runtime: Any, backtest_id: str) -> Tuple[Optional[int], Optional[int]]:
        """Try to extract generation and population indices from backtest data or ID.
        This is heuristic: we look into known fields or encoded IDs if present.
        """
        gen = None
        pop = None
        try:
            # If runtime has obvious fields
            if hasattr(backtest_runtime, 'GenerationIndex'):
                gen = getattr(backtest_runtime, 'GenerationIndex')
            if hasattr(backtest_runtime, 'PopulationIndex'):
                pop = getattr(backtest_runtime, 'PopulationIndex')
            # Fallback: parse backtest_id suffixes if pattern exists (GxxPyy)
            if (gen is None or pop is None) and isinstance(backtest_id, str):
                import re
                m = re.search(r"G(\d+)P(\d+)", backtest_id)
                if m:
                    gen = gen or int(m.group(1))
                    pop = pop or int(m.group(2))
        except Exception:
            pass
        return gen, pop

    async def _enqueue_longest_backtest(self, bot_id: str, backtest_runtime: Any) -> None:
        """
        Enqueue longest backtest for bot validation.
        
        Args:
            bot_id: ID of the bot to backtest
            backtest_runtime: Original backtest runtime data for reference
        """
        try:
            # Get bot details
            bot_details = await self.bot_api.get_bot_details(bot_id)
            if not bot_details:
                self.logger.warning(f"Bot {bot_id} not found for longest backtest")
                return

            # Calculate longest backtest period (e.g., 2 years)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=730)  # 2 years
            
            # Execute longest backtest
            bot_data = {
                'BotId': bot_id,
                'BotName': bot_details.bot_name,
                'ScriptId': bot_details.script_id,
                'MarketTag': bot_details.market_tag,
                'AccountId': bot_details.account_id,
                'Leverage': bot_details.leverage,
                'TradeAmount': bot_details.trade_amount
            }
            
            backtest_result = await self.backtest_api.execute_bot_backtest(
                bot_data=bot_data,
                start_time=start_time,
                end_time=end_time,
                duration_days=730
            )
            
            # Update bot notes with backtest status
            await self._update_bot_notes_with_backtest_status(bot_id, backtest_result)
            
            self.logger.info(f"✅ Longest backtest completed for bot {bot_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to enqueue longest backtest for bot {bot_id}: {e}")
            # Update notes with error status
            await self._update_bot_notes_with_backtest_error(bot_id, str(e))

    async def _update_bot_notes_with_backtest_status(self, bot_id: str, backtest_result: Any) -> None:
        """Update bot notes with longest backtest results"""
        try:
            # Get current notes
            current_notes = await self.bot_api.get_bot_notes(bot_id)
            notes_data = json.loads(current_notes) if current_notes else {}
            
            # Update longest backtest section
            if 'longest_backtest' in notes_data:
                notes_data['longest_backtest'].update({
                    'status': 'completed',
                    'result_ts': datetime.utcnow().isoformat(),
                    'backtest_id': getattr(backtest_result, 'backtest_id', ''),
                    'roe_pct': getattr(backtest_result, 'roe_pct', None),
                    'winrate_pct': getattr(backtest_result, 'winrate_pct', None),
                    'trades': getattr(backtest_result, 'trades', None),
                    'max_drawdown_pct': getattr(backtest_result, 'max_drawdown_pct', None),
                    'period': {
                        'from': getattr(backtest_result, 'start_time', ''),
                        'to': getattr(backtest_result, 'end_time', '')
                    }
                })
                
                # Save updated notes
                await self.bot_api.change_bot_notes(bot_id, json_dumps_compact(notes_data))
                
        except Exception as e:
            self.logger.warning(f"Failed to update bot notes with backtest status: {e}")

    async def _update_bot_notes_with_backtest_error(self, bot_id: str, error_message: str) -> None:
        """Update bot notes with backtest error"""
        try:
            # Get current notes
            current_notes = await self.bot_api.get_bot_notes(bot_id)
            notes_data = json.loads(current_notes) if current_notes else {}
            
            # Update longest backtest section with error
            if 'longest_backtest' in notes_data:
                notes_data['longest_backtest'].update({
                    'status': 'error',
                    'error_message': error_message,
                    'result_ts': datetime.utcnow().isoformat()
                })
                
                # Save updated notes
                await self.bot_api.change_bot_notes(bot_id, json_dumps_compact(notes_data))
                
        except Exception as e:
            self.logger.warning(f"Failed to update bot notes with backtest error: {e}")

    async def check_longest_backtest_progress(self, bot_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Check progress of longest backtests for bots.
        
        Args:
            bot_ids: List of bot IDs to check (if None, checks all bots)
            
        Returns:
            Dictionary with backtest progress information
        """
        try:
            if not bot_ids:
                # Get all bots
                all_bots = await self.bot_api.get_all_bots()
                bot_ids = [bot.bot_id for bot in all_bots]
            
            progress_info = {
                'total_bots': len(bot_ids),
                'completed_backtests': 0,
                'failed_backtests': 0,
                'pending_backtests': 0,
                'bot_details': {}
            }
            
            for bot_id in bot_ids:
                try:
                    # Get bot notes to check backtest status
                    notes = await self.bot_api.get_bot_notes(bot_id)
                    if notes:
                        notes_data = json.loads(notes)
                        longest_backtest = notes_data.get('longest_backtest', {})
                        status = longest_backtest.get('status', 'unknown')
                        
                        if status == 'completed':
                            progress_info['completed_backtests'] += 1
                        elif status == 'error':
                            progress_info['failed_backtests'] += 1
                        elif status == 'queued':
                            progress_info['pending_backtests'] += 1
                        
                        progress_info['bot_details'][bot_id] = {
                            'status': status,
                            'roe_pct': longest_backtest.get('roe_pct'),
                            'winrate_pct': longest_backtest.get('winrate_pct'),
                            'trades': longest_backtest.get('trades'),
                            'error_message': longest_backtest.get('error_message')
                        }
                    else:
                        progress_info['bot_details'][bot_id] = {'status': 'no_notes'}
                        
                except Exception as e:
                    self.logger.warning(f"Failed to check progress for bot {bot_id}: {e}")
                    progress_info['bot_details'][bot_id] = {'status': 'error', 'error': str(e)}
            
            return progress_info
            
        except Exception as e:
            self.logger.error(f"Failed to check longest backtest progress: {e}")
            raise BotError(f"Failed to check backtest progress: {e}") from e

    async def analyze_longest_backtest_results(self, bot_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze longest backtest results and provide recommendations.
        
        Args:
            bot_ids: List of bot IDs to analyze (if None, analyzes all bots)
            
        Returns:
            Dictionary with analysis results and recommendations
        """
        try:
            progress_info = await self.check_longest_backtest_progress(bot_ids)
            
            analysis_results = {
                'total_analyzed': 0,
                'recommendations': {
                    'continue': [],
                    'stop': [],
                    'retest': []
                },
                'bot_analysis': {}
            }
            
            for bot_id, details in progress_info['bot_details'].items():
                if details['status'] != 'completed':
                    continue
                
                analysis_results['total_analyzed'] += 1
                
                # Analyze performance
                roe = details.get('roe_pct', 0)
                winrate = details.get('winrate_pct', 0)
                trades = details.get('trades', 0)
                
                # Decision logic
                decision = 'continue'  # Default
                reason = []
                
                if roe < 0:
                    decision = 'stop'
                    reason.append(f"Negative ROE: {roe:.1f}%")
                elif winrate < 0.4:  # 40%
                    decision = 'stop'
                    reason.append(f"Low win rate: {winrate:.1f}%")
                elif trades < 10:
                    decision = 'retest'
                    reason.append(f"Too few trades: {trades}")
                elif roe < 50:  # 50%
                    decision = 'retest'
                    reason.append(f"Low ROE: {roe:.1f}%")
                
                analysis_results['recommendations'][decision].append({
                    'bot_id': bot_id,
                    'roe_pct': roe,
                    'winrate_pct': winrate,
                    'trades': trades,
                    'reason': reason
                })
                
                analysis_results['bot_analysis'][bot_id] = {
                    'decision': decision,
                    'roe_pct': roe,
                    'winrate_pct': winrate,
                    'trades': trades,
                    'reason': reason
                }
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Failed to analyze longest backtest results: {e}")
            raise BotError(f"Failed to analyze backtest results: {e}") from e


    async def get_all_bots_summary(self) -> Dict[str, Any]:
        """
        Get summary of all bots.

        Returns:
            Dictionary with bot summary information

        Raises:
            BotError: If summary retrieval fails
        """
        try:
            self.logger.info("Getting summary of all bots")

            all_bots = await self.bot_api.get_all_bots()
            
            summary = {
                "total_bots": len(all_bots),
                "active_bots": 0,
                "inactive_bots": 0,
                "bots_by_market": {},
                "bots_by_account": {},
                "summary_timestamp": datetime.now().isoformat()
            }

            for bot in all_bots:
                # Count active/inactive
                if bot.is_active:
                    summary["active_bots"] += 1
                else:
                    summary["inactive_bots"] += 1

                # Count by market
                market = bot.market_tag
                summary["bots_by_market"][market] = summary["bots_by_market"].get(market, 0) + 1

                # Count by account
                account = bot.account_id
                summary["bots_by_account"][account] = summary["bots_by_account"].get(account, 0) + 1

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get bots summary: {e}")
            raise BotError(f"Failed to get bots summary: {e}") from e


def json_dumps_compact(obj: Any) -> str:
    try:
        import json
        return json.dumps(obj, separators=(",", ":"))
    except Exception:
        return "{}"