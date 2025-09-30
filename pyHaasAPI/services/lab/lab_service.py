"""
Lab Service for pyHaasAPI v2

Provides business logic for lab management operations including creation,
configuration, execution, and monitoring of trading labs.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...api.lab import LabAPI
from ...api.backtest import BacktestAPI
from ...api.script import ScriptAPI
from ...api.account import AccountAPI
from ...models.lab import LabDetails, LabRecord, LabConfig, StartLabExecutionRequest, LabExecutionUpdate
from ...models.common import BaseEntityModel
from ...exceptions import LabError, LabNotFoundError, LabExecutionError, LabConfigurationError
from ...core.logging import get_logger


@dataclass
class LabAnalysisResult:
    """Result of lab analysis operation"""
    lab_id: str
    lab_name: str
    total_backtests: int
    successful_backtests: int
    failed_backtests: int
    average_roi: float
    best_roi: float
    worst_roi: float
    average_win_rate: float
    total_trades: int
    analysis_timestamp: datetime
    recommendations: List[str]


@dataclass
class LabExecutionResult:
    """Result of lab execution operation"""
    lab_id: str
    execution_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    total_generations: int
    completed_generations: int
    total_backtests: int
    completed_backtests: int
    success_rate: float
    execution_time: Optional[timedelta]
    error_message: Optional[str]


@dataclass
class LabValidationResult:
    """Result of lab validation operation"""
    lab_id: str
    is_valid: bool
    validation_errors: List[str]
    validation_warnings: List[str]
    configuration_score: float
    recommendations: List[str]


class LabService:
    """
    Lab Service for managing trading labs
    
    Provides high-level business logic for lab operations including creation,
    configuration, execution, analysis, and monitoring.
    """
    
    def __init__(
        self,
        lab_api: LabAPI,
        backtest_api: BacktestAPI,
        script_api: ScriptAPI,
        account_api: AccountAPI
    ):
        self.lab_api = lab_api
        self.backtest_api = backtest_api
        self.script_api = script_api
        self.account_api = account_api
        self.logger = get_logger("lab_service")
    
    async def create_lab_with_validation(
        self,
        script_id: str,
        name: str,
        account_id: str,
        market: str,
        interval: int = 1,
        trade_amount: float = 100.0,
        leverage: float = 0.0,
        position_mode: int = 0,
        margin_mode: int = 0,
        validate_config: bool = True
    ) -> LabDetails:
        """
        Create a new lab with comprehensive validation
        
        Args:
            script_id: ID of the script to use
            name: Name for the lab
            account_id: ID of the account to use
            market: Market tag (e.g., "BINANCE_BTC_USDT_")
            interval: Data interval in minutes
            trade_amount: Trade amount
            leverage: Leverage value
            position_mode: Position mode (0=ONE_WAY, 1=HEDGE)
            margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
            validate_config: Whether to validate configuration before creation
            
        Returns:
            LabDetails object for the created lab
            
        Raises:
            LabError: If lab creation fails
            LabConfigurationError: If configuration validation fails
        """
        try:
            self.logger.info(f"Creating lab with validation: {name}")
            
            # Validate configuration if requested
            if validate_config:
                validation_result = await self.validate_lab_configuration(
                    script_id, account_id, market, interval, trade_amount, leverage
                )
                if not validation_result.is_valid:
                    raise LabConfigurationError(
                        f"Lab configuration validation failed: {', '.join(validation_result.validation_errors)}"
                    )
            
            # Create the lab
            lab_details = await self.lab_api.create_lab(
                script_id=script_id,
                name=name,
                account_id=account_id,
                market=market,
                interval=interval,
                trade_amount=trade_amount,
                leverage=leverage,
                position_mode=position_mode,
                margin_mode=margin_mode
            )
            
            self.logger.info(f"Lab created successfully: {lab_details.lab_id}")
            return lab_details
            
        except Exception as e:
            self.logger.error(f"Failed to create lab: {e}")
            if isinstance(e, (LabError, LabConfigurationError)):
                raise
            else:
                raise LabError(f"Failed to create lab: {e}")
    
    async def analyze_lab_performance(self, lab_id: str) -> LabAnalysisResult:
        """
        Analyze lab performance and provide recommendations
        
        Args:
            lab_id: ID of the lab to analyze
            
        Returns:
            LabAnalysisResult with analysis data and recommendations
            
        Raises:
            LabNotFoundError: If lab is not found
            LabError: If analysis fails
        """
        try:
            self.logger.info(f"Analyzing lab performance: {lab_id}")
            
            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Get all backtests for the lab
            backtests = await self.backtest_api.get_all_backtests_for_lab(lab_id)
            
            if not backtests:
                return LabAnalysisResult(
                    lab_id=lab_id,
                    lab_name=lab_details.name,
                    total_backtests=0,
                    successful_backtests=0,
                    failed_backtests=0,
                    average_roi=0.0,
                    best_roi=0.0,
                    worst_roi=0.0,
                    average_win_rate=0.0,
                    total_trades=0,
                    analysis_timestamp=datetime.now(),
                    recommendations=["No backtests found for analysis"]
                )
            
            # Analyze backtest performance
            successful_backtests = [bt for bt in backtests if bt.get('Success', False)]
            failed_backtests = [bt for bt in backtests if not bt.get('Success', False)]
            
            if successful_backtests:
                rois = [bt.get('ROI', 0) for bt in successful_backtests]
                win_rates = [bt.get('WinRate', 0) for bt in successful_backtests]
                trades = [bt.get('TotalTrades', 0) for bt in successful_backtests]
                
                average_roi = sum(rois) / len(rois)
                best_roi = max(rois)
                worst_roi = min(rois)
                average_win_rate = sum(win_rates) / len(win_rates)
                total_trades = sum(trades)
            else:
                average_roi = 0.0
                best_roi = 0.0
                worst_roi = 0.0
                average_win_rate = 0.0
                total_trades = 0
            
            # Generate recommendations
            recommendations = self._generate_lab_recommendations(
                average_roi, average_win_rate, len(successful_backtests), len(failed_backtests)
            )
            
            result = LabAnalysisResult(
                lab_id=lab_id,
                lab_name=lab_details.name,
                total_backtests=len(backtests),
                successful_backtests=len(successful_backtests),
                failed_backtests=len(failed_backtests),
                average_roi=average_roi,
                best_roi=best_roi,
                worst_roi=worst_roi,
                average_win_rate=average_win_rate,
                total_trades=total_trades,
                analysis_timestamp=datetime.now(),
                recommendations=recommendations
            )
            
            self.logger.info(f"Lab analysis completed: {lab_id}")
            return result
            
        except LabNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze lab: {e}")
            raise LabError(f"Failed to analyze lab: {e}")
    
    async def execute_lab_with_monitoring(
        self,
        lab_id: str,
        start_unix: int,
        end_unix: int,
        send_email: bool = False,
        monitor_interval: int = 30
    ) -> LabExecutionResult:
        """
        Execute lab with comprehensive monitoring
        
        Args:
            lab_id: ID of the lab to execute
            start_unix: Start time in Unix timestamp
            end_unix: End time in Unix timestamp
            send_email: Whether to send email notification
            monitor_interval: Monitoring interval in seconds
            
        Returns:
            LabExecutionResult with execution details
            
        Raises:
            LabNotFoundError: If lab is not found
            LabExecutionError: If execution fails
        """
        try:
            self.logger.info(f"Starting lab execution with monitoring: {lab_id}")
            
            # Validate lab configuration
            validation_result = await self.validate_lab_configuration_by_id(lab_id)
            if not validation_result.is_valid:
                raise LabExecutionError(
                    lab_id, f"Lab configuration invalid: {', '.join(validation_result.validation_errors)}"
                )
            
            # Start execution
            execution_request = StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=start_unix,
                end_unix=end_unix,
                send_email=send_email
            )
            
            execution_response = await self.lab_api.start_lab_execution(execution_request)
            execution_id = execution_response.get('Data', {}).get('ExecutionId', lab_id)
            
            start_time = datetime.now()
            
            # Monitor execution
            execution_result = await self._monitor_lab_execution(
                lab_id, execution_id, start_time, monitor_interval
            )
            
            self.logger.info(f"Lab execution completed: {lab_id}")
            return execution_result
            
        except LabNotFoundError:
            raise
        except LabExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to execute lab: {e}")
            raise LabExecutionError(lab_id, f"Failed to execute lab: {e}")
    
    async def validate_lab_configuration(
        self,
        script_id: str,
        account_id: str,
        market: str,
        interval: int,
        trade_amount: float,
        leverage: float
    ) -> LabValidationResult:
        """
        Validate lab configuration before creation
        
        Args:
            script_id: Script ID to validate
            account_id: Account ID to validate
            market: Market to validate
            interval: Interval to validate
            trade_amount: Trade amount to validate
            leverage: Leverage to validate
            
        Returns:
            LabValidationResult with validation details
        """
        validation_errors = []
        validation_warnings = []
        recommendations = []
        
        try:
            # Validate script exists
            try:
                script = await self.script_api.get_script_record(script_id)
                if not script:
                    validation_errors.append(f"Script {script_id} not found")
            except Exception:
                validation_errors.append(f"Script {script_id} not accessible")
            
            # Validate account exists
            try:
                account = await self.account_api.get_account_data(account_id)
                if not account:
                    validation_errors.append(f"Account {account_id} not found")
            except Exception:
                validation_errors.append(f"Account {account_id} not accessible")
            
            # Validate market
            try:
                market_valid = await self.backtest_api.validate_market(market)
                if not market_valid:
                    validation_errors.append(f"Market {market} not available")
            except Exception:
                validation_errors.append(f"Market {market} validation failed")
            
            # Validate interval
            if interval <= 0:
                validation_errors.append("Interval must be positive")
            elif interval > 1440:  # 24 hours
                validation_warnings.append("Interval is very large (>24 hours)")
            
            # Validate trade amount
            if trade_amount <= 0:
                validation_errors.append("Trade amount must be positive")
            elif trade_amount < 10:
                validation_warnings.append("Trade amount is very small (<$10)")
            elif trade_amount > 100000:
                validation_warnings.append("Trade amount is very large (>$100k)")
            
            # Validate leverage
            if leverage < 0:
                validation_errors.append("Leverage cannot be negative")
            elif leverage > 100:
                validation_warnings.append("Leverage is very high (>100x)")
            
            # Generate recommendations
            if not validation_errors:
                if leverage == 0:
                    recommendations.append("Consider using leverage for better capital efficiency")
                if interval == 1:
                    recommendations.append("Consider using higher intervals for better signal quality")
                if trade_amount < 100:
                    recommendations.append("Consider increasing trade amount for better risk management")
            
            # Calculate configuration score
            score = 100.0
            score -= len(validation_errors) * 20  # Major issues
            score -= len(validation_warnings) * 5  # Minor issues
            score = max(0.0, score)
            
            return LabValidationResult(
                lab_id="",  # Not created yet
                is_valid=len(validation_errors) == 0,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                configuration_score=score,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"Lab configuration validation failed: {e}")
            return LabValidationResult(
                lab_id="",
                is_valid=False,
                validation_errors=[f"Validation failed: {e}"],
                validation_warnings=[],
                configuration_score=0.0,
                recommendations=[]
            )
    
    async def validate_lab_configuration_by_id(self, lab_id: str) -> LabValidationResult:
        """
        Validate existing lab configuration
        
        Args:
            lab_id: ID of the lab to validate
            
        Returns:
            LabValidationResult with validation details
        """
        try:
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            return await self.validate_lab_configuration(
                script_id=lab_details.script_id,
                account_id=lab_details.settings.account_id,
                market=lab_details.settings.market_tag,
                interval=lab_details.settings.interval,
                trade_amount=lab_details.settings.trade_amount,
                leverage=lab_details.settings.leverage
            )
            
        except LabNotFoundError:
            return LabValidationResult(
                lab_id=lab_id,
                is_valid=False,
                validation_errors=[f"Lab {lab_id} not found"],
                validation_warnings=[],
                configuration_score=0.0,
                recommendations=[]
            )
        except Exception as e:
            self.logger.error(f"Lab configuration validation failed: {e}")
            return LabValidationResult(
                lab_id=lab_id,
                is_valid=False,
                validation_errors=[f"Validation failed: {e}"],
                validation_warnings=[],
                configuration_score=0.0,
                recommendations=[]
            )
    
    async def get_lab_health_status(self, lab_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health status for a lab
        
        Args:
            lab_id: ID of the lab to check
            
        Returns:
            Dictionary with health status information
        """
        try:
            lab_details = await self.lab_api.get_lab_details(lab_id)
            validation_result = await self.validate_lab_configuration_by_id(lab_id)
            analysis_result = await self.analyze_lab_performance(lab_id)
            
            # Calculate overall health score
            health_score = (
                validation_result.configuration_score * 0.4 +
                min(analysis_result.average_roi * 10, 100) * 0.3 +
                min(analysis_result.average_win_rate, 100) * 0.3
            )
            
            return {
                "lab_id": lab_id,
                "lab_name": lab_details.name,
                "status": lab_details.status,
                "health_score": health_score,
                "configuration_valid": validation_result.is_valid,
                "configuration_score": validation_result.configuration_score,
                "performance_score": analysis_result.average_roi,
                "win_rate": analysis_result.average_win_rate,
                "total_backtests": analysis_result.total_backtests,
                "success_rate": (
                    analysis_result.successful_backtests / analysis_result.total_backtests
                    if analysis_result.total_backtests > 0 else 0
                ),
                "last_analysis": analysis_result.analysis_timestamp,
                "recommendations": validation_result.recommendations + analysis_result.recommendations,
                "warnings": validation_result.validation_warnings,
                "errors": validation_result.validation_errors
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get lab health status: {e}")
            return {
                "lab_id": lab_id,
                "health_score": 0.0,
                "error": str(e)
            }
    
    async def _monitor_lab_execution(
        self,
        lab_id: str,
        execution_id: str,
        start_time: datetime,
        monitor_interval: int
    ) -> LabExecutionResult:
        """Monitor lab execution progress"""
        try:
            while True:
                # Get execution status
                status_update = await self.lab_api.get_lab_execution_status(lab_id)
                
                if status_update.is_completed:
                    end_time = datetime.now()
                    execution_time = end_time - start_time
                    
                    return LabExecutionResult(
                        lab_id=lab_id,
                        execution_id=execution_id,
                        status=status_update.status,
                        start_time=start_time,
                        end_time=end_time,
                        total_generations=status_update.total_generations,
                        completed_generations=status_update.current_generation,
                        total_backtests=status_update.total_backtests,
                        completed_backtests=status_update.completed_backtests,
                        success_rate=(
                            status_update.completed_backtests / status_update.total_backtests
                            if status_update.total_backtests > 0 else 0
                        ),
                        execution_time=execution_time,
                        error_message=status_update.error_message
                    )
                
                elif status_update.is_failed:
                    end_time = datetime.now()
                    execution_time = end_time - start_time
                    
                    return LabExecutionResult(
                        lab_id=lab_id,
                        execution_id=execution_id,
                        status=status_update.status,
                        start_time=start_time,
                        end_time=end_time,
                        total_generations=status_update.total_generations,
                        completed_generations=status_update.current_generation,
                        total_backtests=status_update.total_backtests,
                        completed_backtests=status_update.completed_backtests,
                        success_rate=0.0,
                        execution_time=execution_time,
                        error_message=status_update.error_message
                    )
                
                # Wait before next check
                await asyncio.sleep(monitor_interval)
                
        except Exception as e:
            self.logger.error(f"Failed to monitor lab execution: {e}")
            return LabExecutionResult(
                lab_id=lab_id,
                execution_id=execution_id,
                status="ERROR",
                start_time=start_time,
                end_time=datetime.now(),
                total_generations=0,
                completed_generations=0,
                total_backtests=0,
                completed_backtests=0,
                success_rate=0.0,
                execution_time=datetime.now() - start_time,
                error_message=str(e)
            )
    
    def _generate_lab_recommendations(
        self,
        average_roi: float,
        average_win_rate: float,
        successful_backtests: int,
        failed_backtests: int
    ) -> List[str]:
        """Generate recommendations based on lab performance"""
        recommendations = []
        
        if average_roi < 10:
            recommendations.append("Consider optimizing strategy parameters for better ROI")
        elif average_roi > 100:
            recommendations.append("Excellent ROI performance - consider creating bots from this lab")
        
        if average_win_rate < 40:
            recommendations.append("Low win rate - consider improving entry/exit logic")
        elif average_win_rate > 70:
            recommendations.append("High win rate - strategy shows good consistency")
        
        if failed_backtests > successful_backtests:
            recommendations.append("High failure rate - review strategy logic and parameters")
        
        if successful_backtests < 10:
            recommendations.append("Limited backtest data - run more backtests for better analysis")
        
        return recommendations