"""
Bot Verification Manager for pyHaasAPI v2

Bot validation and verification with comprehensive configuration checks,
performance analysis, and account assignment validation.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .client import AsyncHaasClient
from .auth import AuthenticationManager
from .server_manager import ServerManager
from .field_utils import safe_get_field, safe_get_success_flag, log_field_mapping_issues
from ..exceptions import BotError, BotConfigurationError, AccountError
from ..core.logging import get_logger
from ..models.bot import BotDetails, BotConfiguration
from ..models.account import AccountDetails


class VerificationStatus(Enum):
    """Bot verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    WARNING = "warning"


class VerificationLevel(Enum):
    """Verification level"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


@dataclass
class VerificationResult:
    """Bot verification result"""
    bot_id: str
    status: VerificationStatus
    level: VerificationLevel
    verification_time: float
    checks_performed: List[str]
    issues_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    configuration_valid: bool = False
    account_assignment_valid: bool = False
    performance_acceptable: bool = False


@dataclass
class ValidationResult:
    """Bot parameter validation result"""
    bot_id: str
    parameters_valid: bool
    validation_time: float
    invalid_parameters: List[str] = field(default_factory=list)
    parameter_warnings: List[str] = field(default_factory=list)
    parameter_recommendations: List[str] = field(default_factory=list)


@dataclass
class PerformanceReport:
    """Bot performance report"""
    bot_id: str
    analysis_time: float
    total_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    performance_score: float
    risk_level: str
    performance_trend: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AssignmentResult:
    """Bot account assignment result"""
    bot_id: str
    account_id: str
    assignment_valid: bool
    assignment_time: float
    account_available: bool
    account_configured: bool
    margin_settings_valid: bool
    leverage_appropriate: bool
    issues_found: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class BotVerificationManager:
    """
    Bot verification and validation manager
    
    Features:
    - Comprehensive bot configuration validation
    - Parameter validation and optimization
    - Performance analysis and reporting
    - Account assignment verification
    - Risk assessment and recommendations
    - Multi-level verification (basic, standard, comprehensive)
    """
    
    def __init__(
        self,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager,
        server_manager: ServerManager
    ):
        self.client = client
        self.auth_manager = auth_manager
        self.server_manager = server_manager
        self.logger = get_logger("bot_verification_manager")
        
        # Verification tracking
        self.verification_results: Dict[str, VerificationResult] = {}
        self.performance_reports: Dict[str, PerformanceReport] = {}
        
        # Configuration
        self.default_verification_level = VerificationLevel.STANDARD
        self.performance_thresholds = {
            "min_win_rate": 0.3,
            "min_profit_factor": 1.2,
            "max_drawdown": 0.5,
            "min_sharpe_ratio": 0.5
        }
    
    async def verify_bot_configuration(
        self,
        bot_id: str,
        level: VerificationLevel = None
    ) -> VerificationResult:
        """
        Verify bot configuration is valid
        
        Args:
            bot_id: ID of the bot to verify
            level: Verification level (basic, standard, comprehensive)
            
        Returns:
            VerificationResult with verification details
            
        Raises:
            BotError: If verification fails
        """
        try:
            verification_level = level or self.default_verification_level
            self.logger.info(f"Verifying bot configuration for {bot_id} (level: {verification_level.value})")
            
            start_time = time.time()
            checks_performed = []
            issues_found = []
            warnings = []
            recommendations = []
            
            # Ensure authentication
            await self.auth_manager.ensure_authenticated()
            
            # Get bot details
            from ..api.bot.bot_api import BotAPI
            bot_api = BotAPI(self.client, self.auth_manager)
            bot_details = await bot_api.get_bot_details(bot_id)
            
            # Basic verification checks
            checks_performed.append("bot_exists")
            if not bot_details:
                issues_found.append("Bot not found")
                return self._create_verification_result(
                    bot_id, VerificationStatus.FAILED, verification_level,
                    time.time() - start_time, checks_performed, issues_found
                )
            
            # Configuration validation
            config_valid = await self._validate_bot_configuration(bot_details)
            checks_performed.append("configuration_validation")
            if not config_valid:
                issues_found.append("Invalid bot configuration")
            
            # Account assignment validation
            account_valid = await self._validate_account_assignment(bot_details)
            checks_performed.append("account_assignment")
            if not account_valid:
                issues_found.append("Invalid account assignment")
            
            # Standard verification checks
            if verification_level in [VerificationLevel.STANDARD, VerificationLevel.COMPREHENSIVE]:
                # Parameter validation
                param_valid = await self._validate_bot_parameters(bot_details)
                checks_performed.append("parameter_validation")
                if not param_valid:
                    warnings.append("Parameter validation issues detected")
                
                # Market validation
                market_valid = await self._validate_market_configuration(bot_details)
                checks_performed.append("market_validation")
                if not market_valid:
                    warnings.append("Market configuration issues detected")
            
            # Comprehensive verification checks
            if verification_level == VerificationLevel.COMPREHENSIVE:
                # Performance analysis
                performance_acceptable = await self._analyze_bot_performance(bot_details)
                checks_performed.append("performance_analysis")
                if not performance_acceptable:
                    warnings.append("Performance analysis indicates potential issues")
                
                # Risk assessment
                risk_assessment = await self._assess_bot_risk(bot_details)
                checks_performed.append("risk_assessment")
                if risk_assessment.get("high_risk", False):
                    warnings.append("High risk detected in bot configuration")
                    recommendations.append("Consider reducing leverage or trade amount")
            
            # Determine overall status
            status = VerificationStatus.VERIFIED
            if issues_found:
                status = VerificationStatus.FAILED
            elif warnings:
                status = VerificationStatus.WARNING
            
            # Generate recommendations
            if not issues_found and not warnings:
                recommendations.append("Bot configuration is optimal")
            elif not issues_found:
                recommendations.append("Address warnings to improve bot performance")
            else:
                recommendations.append("Fix critical issues before activating bot")
            
            result = VerificationResult(
                bot_id=bot_id,
                status=status,
                level=verification_level,
                verification_time=time.time() - start_time,
                checks_performed=checks_performed,
                issues_found=issues_found,
                warnings=warnings,
                recommendations=recommendations,
                configuration_valid=config_valid,
                account_assignment_valid=account_valid,
                performance_acceptable=performance_acceptable if verification_level == VerificationLevel.COMPREHENSIVE else True
            )
            
            self.verification_results[bot_id] = result
            self.logger.info(f"Bot verification completed for {bot_id}: {status.value}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to verify bot configuration for {bot_id}: {e}")
            raise BotError(f"Failed to verify bot configuration: {e}") from e
    
    async def validate_bot_parameters(self, bot_id: str) -> ValidationResult:
        """
        Validate bot parameters
        
        Args:
            bot_id: ID of the bot to validate
            
        Returns:
            ValidationResult with validation details
            
        Raises:
            BotError: If validation fails
        """
        try:
            self.logger.info(f"Validating bot parameters for {bot_id}")
            
            start_time = time.time()
            invalid_parameters = []
            parameter_warnings = []
            parameter_recommendations = []
            
            # Get bot details
            from ..api.bot.bot_api import BotAPI
            bot_api = BotAPI(self.client, self.auth_manager)
            bot_details = await bot_api.get_bot_details(bot_id)
            
            # Validate required parameters
            if not bot_details.script_id:
                invalid_parameters.append("script_id")
            
            if not bot_details.settings.market_tag:
                invalid_parameters.append("market_tag")
            
            if not bot_details.settings.account_id:
                invalid_parameters.append("account_id")
            
            # Validate parameter ranges
            if bot_details.settings.leverage <= 0:
                invalid_parameters.append("leverage")
            elif bot_details.settings.leverage > 100:
                parameter_warnings.append("leverage")
                parameter_recommendations.append("Consider reducing leverage for risk management")
            
            if bot_details.settings.trade_amount <= 0:
                invalid_parameters.append("trade_amount")
            elif bot_details.settings.trade_amount > 10000:
                parameter_warnings.append("trade_amount")
                parameter_recommendations.append("Consider reducing trade amount for risk management")
            
            # Validate position and margin modes
            if bot_details.settings.position_mode not in [0, 1]:
                invalid_parameters.append("position_mode")
            
            if bot_details.settings.margin_mode not in [0, 1]:
                invalid_parameters.append("margin_mode")
            
            parameters_valid = len(invalid_parameters) == 0
            
            result = ValidationResult(
                bot_id=bot_id,
                parameters_valid=parameters_valid,
                validation_time=time.time() - start_time,
                invalid_parameters=invalid_parameters,
                parameter_warnings=parameter_warnings,
                parameter_recommendations=parameter_recommendations
            )
            
            self.logger.info(f"Bot parameter validation completed for {bot_id}: {'valid' if parameters_valid else 'invalid'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate bot parameters for {bot_id}: {e}")
            raise BotError(f"Failed to validate bot parameters: {e}") from e
    
    async def check_bot_performance(self, bot_id: str) -> PerformanceReport:
        """
        Check bot performance metrics
        
        Args:
            bot_id: ID of the bot to analyze
            
        Returns:
            PerformanceReport with performance analysis
            
        Raises:
            BotError: If performance analysis fails
        """
        try:
            self.logger.info(f"Analyzing bot performance for {bot_id}")
            
            start_time = time.time()
            
            # Get bot runtime data
            from ..api.bot.bot_api import BotAPI
            bot_api = BotAPI(self.client, self.auth_manager)
            bot_details = await bot_api.get_full_bot_runtime_data(bot_id)
            
            # Extract performance metrics
            total_trades = getattr(bot_details, 'total_trades', 0)
            win_rate = getattr(bot_details, 'win_rate', 0.0)
            profit_factor = getattr(bot_details, 'profit_factor', 0.0)
            max_drawdown = getattr(bot_details, 'max_drawdown', 0.0)
            sharpe_ratio = getattr(bot_details, 'sharpe_ratio', 0.0)
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(
                win_rate, profit_factor, max_drawdown, sharpe_ratio
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(max_drawdown, leverage=getattr(bot_details.settings, 'leverage', 1.0))
            
            # Determine performance trend
            performance_trend = self._determine_performance_trend(performance_score)
            
            # Generate recommendations
            recommendations = self._generate_performance_recommendations(
                win_rate, profit_factor, max_drawdown, sharpe_ratio
            )
            
            result = PerformanceReport(
                bot_id=bot_id,
                analysis_time=time.time() - start_time,
                total_trades=total_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                performance_score=performance_score,
                risk_level=risk_level,
                performance_trend=performance_trend,
                recommendations=recommendations
            )
            
            self.performance_reports[bot_id] = result
            self.logger.info(f"Bot performance analysis completed for {bot_id}: score {performance_score:.3f}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze bot performance for {bot_id}: {e}")
            raise BotError(f"Failed to analyze bot performance: {e}") from e
    
    async def verify_account_assignment(self, bot_id: str) -> AssignmentResult:
        """
        Verify bot account assignment
        
        Args:
            bot_id: ID of the bot to verify
            
        Returns:
            AssignmentResult with assignment details
            
        Raises:
            BotError: If verification fails
        """
        try:
            self.logger.info(f"Verifying account assignment for bot {bot_id}")
            
            start_time = time.time()
            issues_found = []
            recommendations = []
            
            # Get bot details
            from ..api.bot.bot_api import BotAPI
            bot_api = BotAPI(self.client, self.auth_manager)
            bot_details = await bot_api.get_bot_details(bot_id)
            
            account_id = bot_details.settings.account_id
            if not account_id:
                issues_found.append("No account assigned to bot")
                return AssignmentResult(
                    bot_id=bot_id,
                    account_id="",
                    assignment_valid=False,
                    assignment_time=time.time() - start_time,
                    account_available=False,
                    account_configured=False,
                    margin_settings_valid=False,
                    leverage_appropriate=False,
                    issues_found=issues_found,
                    recommendations=recommendations
                )
            
            # Check account availability
            from ..api.account.account_api import AccountAPI
            account_api = AccountAPI(self.client, self.auth_manager)
            try:
                account_data = await account_api.get_account_data(account_id)
                account_available = True
                account_configured = True
            except Exception:
                account_available = False
                account_configured = False
                issues_found.append(f"Account {account_id} not available or not configured")
            
            # Check margin settings
            margin_settings_valid = True
            if account_available:
                try:
                    margin_settings = await account_api.get_margin_settings(
                        account_id, bot_details.settings.market_tag
                    )
                    # Validate margin settings
                    if not margin_settings:
                        margin_settings_valid = False
                        issues_found.append("Margin settings not configured for account")
                except Exception:
                    margin_settings_valid = False
                    issues_found.append("Failed to retrieve margin settings")
            
            # Check leverage appropriateness
            leverage_appropriate = True
            if bot_details.settings.leverage > 50:
                leverage_appropriate = False
                issues_found.append("Leverage too high for risk management")
                recommendations.append("Consider reducing leverage to 20x or less")
            
            assignment_valid = (
                account_available and 
                account_configured and 
                margin_settings_valid and 
                leverage_appropriate
            )
            
            if assignment_valid:
                recommendations.append("Account assignment is optimal")
            else:
                recommendations.append("Fix account assignment issues before activating bot")
            
            result = AssignmentResult(
                bot_id=bot_id,
                account_id=account_id,
                assignment_valid=assignment_valid,
                assignment_time=time.time() - start_time,
                account_available=account_available,
                account_configured=account_configured,
                margin_settings_valid=margin_settings_valid,
                leverage_appropriate=leverage_appropriate,
                issues_found=issues_found,
                recommendations=recommendations
            )
            
            self.logger.info(f"Account assignment verification completed for bot {bot_id}: {'valid' if assignment_valid else 'invalid'}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to verify account assignment for bot {bot_id}: {e}")
            raise BotError(f"Failed to verify account assignment: {e}") from e
    
    # Private helper methods
    
    async def _validate_bot_configuration(self, bot_details: BotDetails) -> bool:
        """Validate bot configuration"""
        try:
            # Check required fields
            if not bot_details.script_id:
                return False
            if not bot_details.settings.market_tag:
                return False
            if not bot_details.settings.account_id:
                return False
            
            # Check parameter ranges
            if bot_details.settings.leverage <= 0:
                return False
            if bot_details.settings.trade_amount <= 0:
                return False
            
            return True
        except Exception:
            return False
    
    async def _validate_account_assignment(self, bot_details: BotDetails) -> bool:
        """Validate account assignment"""
        try:
            # Check if account is assigned
            if not bot_details.settings.account_id:
                return False
            
            # Check if account exists and is available
            from ..api.account.account_api import AccountAPI
            account_api = AccountAPI(self.client, self.auth_manager)
            await account_api.get_account_data(bot_details.settings.account_id)
            
            return True
        except Exception:
            return False
    
    async def _validate_bot_parameters(self, bot_details: BotDetails) -> bool:
        """Validate bot parameters"""
        try:
            # Validate parameter ranges
            if bot_details.settings.leverage > 100:
                return False
            if bot_details.settings.trade_amount > 10000:
                return False
            
            return True
        except Exception:
            return False
    
    async def _validate_market_configuration(self, bot_details: BotDetails) -> bool:
        """Validate market configuration"""
        try:
            # Check if market tag is valid
            if not bot_details.settings.market_tag:
                return False
            
            # Check if market is available
            from ..api.market.market_api import MarketAPI
            market_api = MarketAPI(self.client, self.auth_manager)
            await market_api.get_valid_market(bot_details.settings.market_tag)
            
            return True
        except Exception:
            return False
    
    async def _analyze_bot_performance(self, bot_details: BotDetails) -> bool:
        """Analyze bot performance"""
        try:
            # Get performance metrics
            performance_report = await self.check_bot_performance(bot_details.bot_id)
            
            # Check against thresholds
            return (
                performance_report.win_rate >= self.performance_thresholds["min_win_rate"] and
                performance_report.profit_factor >= self.performance_thresholds["min_profit_factor"] and
                performance_report.max_drawdown <= self.performance_thresholds["max_drawdown"] and
                performance_report.sharpe_ratio >= self.performance_thresholds["min_sharpe_ratio"]
            )
        except Exception:
            return False
    
    async def _assess_bot_risk(self, bot_details: BotDetails) -> Dict[str, Any]:
        """Assess bot risk level"""
        try:
            risk_factors = []
            high_risk = False
            
            # Check leverage risk
            if bot_details.settings.leverage > 50:
                risk_factors.append("high_leverage")
                high_risk = True
            
            # Check trade amount risk
            if bot_details.settings.trade_amount > 5000:
                risk_factors.append("high_trade_amount")
                high_risk = True
            
            return {
                "high_risk": high_risk,
                "risk_factors": risk_factors
            }
        except Exception:
            return {"high_risk": True, "risk_factors": ["assessment_failed"]}
    
    def _calculate_performance_score(
        self,
        win_rate: float,
        profit_factor: float,
        max_drawdown: float,
        sharpe_ratio: float
    ) -> float:
        """Calculate overall performance score"""
        try:
            # Normalize metrics to 0-1 scale
            win_rate_score = min(win_rate, 1.0)
            profit_factor_score = min(profit_factor / 2.0, 1.0)  # 2.0 is excellent
            drawdown_score = max(0, 1.0 - max_drawdown)  # Lower drawdown is better
            sharpe_score = min(sharpe_ratio / 2.0, 1.0)  # 2.0 is excellent
            
            # Weighted average
            score = (
                win_rate_score * 0.3 +
                profit_factor_score * 0.3 +
                drawdown_score * 0.2 +
                sharpe_score * 0.2
            )
            
            return max(0.0, min(1.0, score))
        except Exception:
            return 0.0
    
    def _determine_risk_level(self, max_drawdown: float, leverage: float) -> str:
        """Determine risk level based on drawdown and leverage"""
        try:
            if max_drawdown > 0.5 or leverage > 50:
                return "high"
            elif max_drawdown > 0.3 or leverage > 20:
                return "medium"
            else:
                return "low"
        except Exception:
            return "unknown"
    
    def _determine_performance_trend(self, performance_score: float) -> str:
        """Determine performance trend"""
        try:
            if performance_score >= 0.8:
                return "excellent"
            elif performance_score >= 0.6:
                return "good"
            elif performance_score >= 0.4:
                return "average"
            else:
                return "poor"
        except Exception:
            return "unknown"
    
    def _generate_performance_recommendations(
        self,
        win_rate: float,
        profit_factor: float,
        max_drawdown: float,
        sharpe_ratio: float
    ) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        if win_rate < 0.3:
            recommendations.append("Consider improving strategy to increase win rate")
        
        if profit_factor < 1.2:
            recommendations.append("Consider optimizing strategy for better profit factor")
        
        if max_drawdown > 0.3:
            recommendations.append("Consider reducing risk to lower drawdown")
        
        if sharpe_ratio < 0.5:
            recommendations.append("Consider improving risk-adjusted returns")
        
        if not recommendations:
            recommendations.append("Performance metrics are within acceptable ranges")
        
        return recommendations
    
    def _create_verification_result(
        self,
        bot_id: str,
        status: VerificationStatus,
        level: VerificationLevel,
        verification_time: float,
        checks_performed: List[str],
        issues_found: List[str]
    ) -> VerificationResult:
        """Create verification result"""
        return VerificationResult(
            bot_id=bot_id,
            status=status,
            level=level,
            verification_time=verification_time,
            checks_performed=checks_performed,
            issues_found=issues_found,
            configuration_valid=status == VerificationStatus.VERIFIED,
            account_assignment_valid=status == VerificationStatus.VERIFIED,
            performance_acceptable=status == VerificationStatus.VERIFIED
        )
