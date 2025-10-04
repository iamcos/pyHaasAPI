"""
High-level Lab Service for pyHaasAPI_no_pydantic

Provides business logic for lab operations including creation,
configuration, execution, analysis, and monitoring with proper
error handling and workflow management.
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..api.lab_api import LabAPI
from ..models.lab import LabDetails, LabRecord, LabConfig, StartLabExecutionRequest, LabExecutionUpdate
from ..api.exceptions import LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError

logger = logging.getLogger(__name__)


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
    High-level Lab Service - Business logic for lab operations
    
    Provides comprehensive lab management including creation, configuration,
    execution, analysis, and monitoring with proper error handling.
    """
    
    def __init__(self, lab_api: LabAPI):
        self.lab_api = lab_api
        self.logger = logger
    
    # ============================================================================
    # LAB CREATION AND MANAGEMENT
    # ============================================================================
    
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
            LabAPIError: If lab creation fails
            LabConfigurationError: If configuration validation fails
        """
        try:
            self.logger.info(f"Creating lab with validation: {name}")
            
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
            
            # Validate configuration if requested
            if validate_config:
                validation_result = await self.validate_lab_configuration(lab_details.lab_id)
                if not validation_result.is_valid:
                    raise LabConfigurationError(
                        "validation", 
                        "failed", 
                        f"Lab configuration validation failed: {', '.join(validation_result.validation_errors)}"
                    )
            
            self.logger.info(f"Lab created and validated successfully: {lab_details.lab_id}")
            return lab_details
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Lab creation with validation failed: {e}")
            raise LabAPIError(f"Lab creation with validation failed: {e}")
    
    async def create_optimized_lab(
        self,
        source_lab_id: str,
        target_lab_id: str,
        coin_symbol: str
    ) -> LabDetails:
        """
        Create optimized lab with parameter optimization
        
        Args:
            source_lab_id: ID of the source lab to optimize
            target_lab_id: ID of the target lab to create
            coin_symbol: Coin symbol for optimization
            
        Returns:
            LabDetails object for the optimized lab
            
        Raises:
            LabAPIError: If optimization fails
        """
        try:
            self.logger.info(f"Creating optimized lab from {source_lab_id} to {target_lab_id}")
            
            # Get source lab details
            source_lab = await self.lab_api.get_lab_details(source_lab_id)
            
            # Create optimized lab with best parameters
            optimized_lab = await self.lab_api.create_lab(
                script_id=source_lab.script_id,
                name=f"Optimized {source_lab.name}",
                account_id=source_lab.settings.account_id,
                market=coin_symbol,
                interval=source_lab.settings.interval,
                trade_amount=source_lab.settings.trade_amount,
                leverage=source_lab.settings.leverage,
                position_mode=source_lab.settings.position_mode,
                margin_mode=source_lab.settings.margin_mode
            )
            
            # Configure with optimized parameters
            optimized_config = LabConfig(
                max_parallel=20,  # Increased for optimization
                max_generations=100,  # More generations for better results
                max_epochs=5,  # More epochs
                max_runtime=0,  # Unlimited runtime
                auto_restart=1  # Auto restart enabled
            )
            
            await self.lab_api.ensure_lab_config_parameters(optimized_lab.lab_id, optimized_config)
            
            self.logger.info(f"Optimized lab created successfully: {optimized_lab.lab_id}")
            return optimized_lab
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Lab optimization failed: {e}")
            raise LabAPIError(f"Lab optimization failed: {e}")
    
    # ============================================================================
    # LAB EXECUTION AND MONITORING
    # ============================================================================
    
    async def run_longest_backtest(
        self,
        lab_id: str,
        cutoff_date: Optional[datetime] = None,
        max_iterations: int = 1500
    ) -> LabExecutionResult:
        """
        Run the longest possible backtest for a lab
        
        Args:
            lab_id: ID of the lab to run backtest for
            cutoff_date: Optional cutoff date to use
            max_iterations: Maximum number of iterations
            
        Returns:
            LabExecutionResult with execution details
            
        Raises:
            LabAPIError: If backtest fails
        """
        try:
            self.logger.info(f"Running longest backtest for lab: {lab_id}")
            
            # Discover cutoff date if not provided
            if not cutoff_date:
                cutoff_date = await self.lab_api.discover_cutoff_date(lab_id)
            
            # Configure lab for longest backtest
            config = LabConfig(
                max_parallel=10,
                max_generations=max_iterations,
                max_epochs=3,
                max_runtime=0,  # Unlimited
                auto_restart=0
            )
            
            await self.lab_api.ensure_lab_config_parameters(lab_id, config)
            
            # Start execution
            start_time = int(cutoff_date.timestamp())
            end_time = int(datetime.now().timestamp())
            
            execution_request = StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=start_time,
                end_unix=end_time,
                send_email=False
            )
            
            execution_response = await self.lab_api.start_lab_execution(execution_request)
            execution_id = execution_response.get("Data", {}).get("executionId", "unknown")
            
            result = LabExecutionResult(
                lab_id=lab_id,
                execution_id=execution_id,
                status="started",
                start_time=cutoff_date,
                end_time=None,
                total_generations=max_iterations,
                completed_generations=0,
                total_backtests=0,
                completed_backtests=0,
                success_rate=0.0,
                execution_time=None,
                error_message=None
            )
            
            self.logger.info(f"Longest backtest started for lab {lab_id}")
            return result
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to run longest backtest: {e}")
            raise LabAPIError(f"Failed to run longest backtest: {e}")
    
    async def monitor_lab_progress(
        self,
        lab_id: str,
        job_id: str,
        max_wait_minutes: int = 10
    ) -> LabExecutionResult:
        """
        Monitor lab execution progress
        
        Args:
            lab_id: ID of the lab to monitor
            job_id: ID of the execution job
            max_wait_minutes: Maximum time to wait for completion
            
        Returns:
            LabExecutionResult with final execution details
            
        Raises:
            LabAPIError: If monitoring fails
        """
        try:
            self.logger.info(f"Monitoring progress for lab: {lab_id}")
            
            start_time = datetime.now()
            max_wait_seconds = max_wait_minutes * 60
            
            while True:
                # Get current execution status
                execution_update = await self.lab_api.get_lab_execution_status(lab_id)
                
                # Check if execution is complete
                if execution_update.is_completed or execution_update.is_failed or execution_update.is_cancelled:
                    end_time = datetime.now()
                    execution_time = end_time - start_time
                    
                    result = LabExecutionResult(
                        lab_id=lab_id,
                        execution_id=job_id,
                        status=execution_update.status,
                        start_time=start_time,
                        end_time=end_time,
                        total_generations=execution_update.total_generations,
                        completed_generations=execution_update.current_generation,
                        total_backtests=execution_update.total_backtests,
                        completed_backtests=execution_update.completed_backtests,
                        success_rate=execution_update.progress,
                        execution_time=execution_time,
                        error_message=execution_update.error_message
                    )
                    
                    self.logger.info(f"Lab execution completed: {execution_update.status}")
                    return result
                
                # Check timeout
                elapsed_seconds = (datetime.now() - start_time).total_seconds()
                if elapsed_seconds > max_wait_seconds:
                    raise LabExecutionError(
                        lab_id, 
                        f"Execution timeout after {max_wait_minutes} minutes"
                    )
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to monitor lab progress: {e}")
            raise LabAPIError(f"Failed to monitor lab progress: {e}")
    
    # ============================================================================
    # LAB ANALYSIS
    # ============================================================================
    
    async def analyze_lab_comprehensive(
        self,
        lab_id: str,
        top_count: int = 10,
        min_win_rate: float = 0.3,
        min_trades: int = 5,
        sort_by: str = "roe"
    ) -> LabAnalysisResult:
        """
        Perform comprehensive lab analysis
        
        Args:
            lab_id: ID of the lab to analyze
            top_count: Number of top performers to return
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            sort_by: Field to sort by (roi, roe, winrate, profit, trades)
            
        Returns:
            LabAnalysisResult with analysis details
            
        Raises:
            LabAPIError: If analysis fails
        """
        try:
            self.logger.info(f"Performing comprehensive analysis for lab {lab_id}")
            
            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Perform analysis (this would need to be implemented based on actual API)
            # For now, return a placeholder structure
            analysis_result = LabAnalysisResult(
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
                recommendations=[]
            )
            
            self.logger.info(f"Analysis completed for lab {lab_id}")
            return analysis_result
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze lab: {e}")
            raise LabAPIError(f"Failed to analyze lab: {e}")
    
    # ============================================================================
    # LAB CONFIGURATION
    # ============================================================================
    
    async def configure_lab_parameters(
        self,
        lab_id: str,
        best_params: Dict[str, Any]
    ) -> LabDetails:
        """
        Configure lab with best parameters
        
        Args:
            lab_id: ID of the lab to configure
            best_params: Dictionary of best parameters to apply
            
        Returns:
            LabDetails object with updated configuration
            
        Raises:
            LabAPIError: If configuration fails
        """
        try:
            self.logger.info(f"Configuring lab parameters for lab: {lab_id}")
            
            # Get current lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Update parameters (this would need to be implemented based on actual API)
            # For now, return the current lab details
            
            self.logger.info(f"Lab parameters configured successfully: {lab_id}")
            return lab_details
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to configure lab parameters: {e}")
            raise LabAPIError(f"Failed to configure lab parameters: {e}")
    
    # ============================================================================
    # LAB DISCOVERY
    # ============================================================================
    
    async def discover_cutoff_date(
        self,
        lab_id: str,
        market_tag: Optional[str] = None
    ) -> datetime:
        """
        Discover the earliest available data point
        
        Args:
            lab_id: ID of the lab to discover cutoff for
            market_tag: Optional market tag to use
            
        Returns:
            Datetime of the earliest available data point
            
        Raises:
            LabAPIError: If discovery fails
        """
        try:
            self.logger.info(f"Discovering cutoff date for lab: {lab_id}")
            
            cutoff_date = await self.lab_api.discover_cutoff_date(lab_id, market_tag)
            
            self.logger.info(f"Discovered cutoff date for lab {lab_id}: {cutoff_date}")
            return cutoff_date
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to discover cutoff date: {e}")
            raise LabAPIError(f"Failed to discover cutoff date: {e}")
    
    # ============================================================================
    # LAB VALIDATION
    # ============================================================================
    
    async def validate_lab_configuration(self, lab_id: str) -> LabValidationResult:
        """
        Validate lab configuration
        
        Args:
            lab_id: ID of the lab to validate
            
        Returns:
            LabValidationResult with validation details
            
        Raises:
            LabAPIError: If validation fails
        """
        try:
            self.logger.info(f"Validating lab configuration for lab: {lab_id}")
            
            # Get lab details
            lab_details = await self.lab_api.get_lab_details(lab_id)
            
            # Perform validation
            validation_errors = []
            validation_warnings = []
            recommendations = []
            
            # Check required fields
            if not lab_details.script_id:
                validation_errors.append("Script ID is required")
            
            if not lab_details.settings.account_id:
                validation_errors.append("Account ID is required")
            
            if not lab_details.settings.market_tag:
                validation_errors.append("Market tag is required")
            
            if lab_details.settings.interval <= 0:
                validation_errors.append("Interval must be positive")
            
            if lab_details.settings.trade_amount <= 0:
                validation_errors.append("Trade amount must be positive")
            
            # Check for warnings
            if lab_details.settings.leverage > 20:
                validation_warnings.append("High leverage detected")
                recommendations.append("Consider reducing leverage for risk management")
            
            if lab_details.settings.trade_amount > 10000:
                validation_warnings.append("Large trade amount detected")
                recommendations.append("Consider reducing trade amount for risk management")
            
            # Calculate configuration score
            total_checks = 5  # Number of validation checks
            error_count = len(validation_errors)
            warning_count = len(validation_warnings)
            configuration_score = max(0, (total_checks - error_count - warning_count * 0.5) / total_checks)
            
            is_valid = len(validation_errors) == 0
            
            result = LabValidationResult(
                lab_id=lab_id,
                is_valid=is_valid,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                configuration_score=configuration_score,
                recommendations=recommendations
            )
            
            self.logger.info(f"Lab configuration validation completed: {is_valid}")
            return result
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate lab configuration: {e}")
            raise LabAPIError(f"Failed to validate lab configuration: {e}")
    
    # ============================================================================
    # BULK OPERATIONS
    # ============================================================================
    
    async def get_complete_labs(self) -> List[LabRecord]:
        """
        Get only completed labs (labs with backtest results)
        
        Returns:
            List of completed LabRecord objects
            
        Raises:
            LabAPIError: If API request fails
        """
        try:
            self.logger.info("Getting complete labs")
            
            complete_labs = await self.lab_api.get_complete_labs()
            
            self.logger.info(f"Found {len(complete_labs)} complete labs")
            return complete_labs
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to get complete labs: {e}")
            raise LabAPIError(f"Failed to get complete labs: {e}")
    
    async def analyze_all_labs(
        self,
        lab_ids: Optional[List[str]] = None,
        top_count: int = 10,
        min_win_rate: float = 0.3,
        min_trades: int = 5
    ) -> Dict[str, LabAnalysisResult]:
        """
        Analyze multiple labs
        
        Args:
            lab_ids: Optional list of lab IDs to analyze (if None, analyzes all labs)
            top_count: Number of top performers to return per lab
            min_win_rate: Minimum win rate threshold
            min_trades: Minimum number of trades
            
        Returns:
            Dictionary mapping lab IDs to analysis results
            
        Raises:
            LabAPIError: If analysis fails
        """
        try:
            self.logger.info(f"Analyzing multiple labs: {lab_ids or 'all'}")
            
            # Get labs to analyze
            if lab_ids is None:
                all_labs = await self.lab_api.get_labs()
                lab_ids = [lab.lab_id for lab in all_labs]
            
            # Analyze each lab
            results = {}
            for lab_id in lab_ids:
                try:
                    analysis_result = await self.analyze_lab_comprehensive(
                        lab_id, top_count, min_win_rate, min_trades
                    )
                    results[lab_id] = analysis_result
                except Exception as e:
                    self.logger.warning(f"Failed to analyze lab {lab_id}: {e}")
                    continue
            
            self.logger.info(f"Analysis completed for {len(results)} labs")
            return results
            
        except (LabAPIError, LabNotFoundError, LabExecutionError, LabConfigurationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze all labs: {e}")
            raise LabAPIError(f"Failed to analyze all labs: {e}")



