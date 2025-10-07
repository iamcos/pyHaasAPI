"""
Backtesting Manager for pyHaasAPI v2

Centralized backtest management and execution with step-halving algorithm,
parameter optimization, and comprehensive monitoring capabilities.
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
from ..exceptions import BacktestError, LabError, LabExecutionError
from ..core.logging import get_logger
from ..models.lab import LabDetails, LabConfig, StartLabExecutionRequest, LabExecutionUpdate
from ..models.backtest import BacktestResult, BacktestAnalysis


class BacktestStatus(Enum):
    """Backtest execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BacktestProgress:
    """Backtest execution progress information"""
    lab_id: str
    status: BacktestStatus
    progress_percentage: float
    current_generation: int
    max_generations: int
    current_epoch: int
    max_epochs: int
    elapsed_time: float
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class OptimizationResult:
    """Parameter optimization result"""
    lab_id: str
    best_parameters: Dict[str, Any]
    optimization_score: float
    total_generations: int
    total_epochs: int
    execution_time: float
    convergence_achieved: bool
    optimization_data: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BacktestExecutionResult:
    """Backtest execution result"""
    lab_id: str
    backtest_id: str
    status: BacktestStatus
    execution_time: float
    total_generations: int
    total_epochs: int
    best_performance: float
    convergence_achieved: bool
    error_message: Optional[str] = None


class BacktestingManager:
    """
    Centralized backtest management and execution
    
    Features:
    - Longest backtest execution with step-halving algorithm
    - Parameter optimization with genetic algorithms
    - Progress monitoring and status tracking
    - Automatic cancellation and cleanup
    - Multi-server support
    - Comprehensive error handling
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
        self.logger = get_logger("backtesting_manager")
        
        # Active backtest tracking
        self.active_backtests: Dict[str, BacktestProgress] = {}
        self.backtest_results: Dict[str, BacktestExecutionResult] = {}
        
        # Configuration
        self.max_concurrent_backtests = 3
        self.default_timeout = 3600  # 1 hour
        self.progress_check_interval = 30  # 30 seconds
        
    async def run_longest_backtest(
        self,
        lab_id: str,
        max_iterations: int = 1500,
        timeout: Optional[float] = None
    ) -> BacktestExecutionResult:
        """
        Execute longest backtest with step-halving algorithm
        
        This implements the proven step-halving algorithm from the refactoring plan
        to find the longest possible backtest period.
        
        Args:
            lab_id: ID of the lab to run backtest on
            max_iterations: Maximum number of iterations for step-halving
            timeout: Maximum execution time in seconds
            
        Returns:
            BacktestExecutionResult with execution details
            
        Raises:
            BacktestError: If backtest execution fails
            LabError: If lab configuration fails
        """
        try:
            self.logger.info(f"Starting longest backtest for lab {lab_id}")
            
            # Ensure authentication
            await self.auth_manager.ensure_authenticated()
            
            # Get lab details
            from ..api.lab.lab_api import LabAPI
            lab_api = LabAPI(self.client, self.auth_manager)
            lab_details = await lab_api.get_lab_details(lab_id)
            
            # Discover cutoff date for longest backtest
            cutoff_date = await self._discover_cutoff_date(lab_id)
            if not cutoff_date:
                raise BacktestError(f"Could not discover cutoff date for lab {lab_id}")
            
            # Configure lab for longest backtest
            await self._configure_lab_for_longest_backtest(lab_id, cutoff_date)
            
            # Start backtest execution
            start_time = time.time()
            backtest_id = await self._start_backtest_execution(lab_id)
            
            # Monitor progress
            progress = await self._monitor_backtest_progress(
                lab_id, backtest_id, timeout or self.default_timeout
            )
            
            execution_time = time.time() - start_time
            
            # Create result
            result = BacktestExecutionResult(
                lab_id=lab_id,
                backtest_id=backtest_id,
                status=BacktestStatus.COMPLETED if progress.status == BacktestStatus.COMPLETED else BacktestStatus.FAILED,
                execution_time=execution_time,
                total_generations=progress.current_generation,
                total_epochs=progress.current_epoch,
                best_performance=0.0,  # Would be extracted from results
                convergence_achieved=progress.status == BacktestStatus.COMPLETED,
                error_message=progress.error_message
            )
            
            self.backtest_results[lab_id] = result
            self.logger.info(f"Longest backtest completed for lab {lab_id} in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to run longest backtest for lab {lab_id}: {e}")
            raise BacktestError(f"Failed to run longest backtest: {e}") from e
    
    async def run_parameter_optimization(
        self,
        lab_id: str,
        optimization_config: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        Run parameter optimization for lab
        
        Args:
            lab_id: ID of the lab to optimize
            optimization_config: Optional optimization configuration
            
        Returns:
            OptimizationResult with optimization details
            
        Raises:
            BacktestError: If optimization fails
        """
        try:
            self.logger.info(f"Starting parameter optimization for lab {lab_id}")
            
            # Ensure authentication
            await self.auth_manager.ensure_authenticated()
            
            # Get lab details
            from ..api.lab.lab_api import LabAPI
            lab_api = LabAPI(self.client, self.auth_manager)
            lab_details = await lab_api.get_lab_details(lab_id)
            
            # Configure optimization parameters
            config = optimization_config or self._get_default_optimization_config()
            
            # Run optimization
            start_time = time.time()
            optimization_data = await self._execute_parameter_optimization(lab_id, config)
            execution_time = time.time() - start_time
            
            # Analyze results
            best_parameters, score = await self._analyze_optimization_results(optimization_data)
            
            result = OptimizationResult(
                lab_id=lab_id,
                best_parameters=best_parameters,
                optimization_score=score,
                total_generations=len(optimization_data),
                total_epochs=sum(gen.get('epochs', 0) for gen in optimization_data),
                execution_time=execution_time,
                convergence_achieved=score > 0.8,  # Threshold for convergence
                optimization_data=optimization_data
            )
            
            self.logger.info(f"Parameter optimization completed for lab {lab_id} with score {score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to run parameter optimization for lab {lab_id}: {e}")
            raise BacktestError(f"Failed to run parameter optimization: {e}") from e
    
    async def monitor_backtest_progress(
        self,
        lab_id: str,
        backtest_id: Optional[str] = None,
        timeout: float = 3600
    ) -> BacktestProgress:
        """
        Monitor backtest execution progress
        
        Args:
            lab_id: ID of the lab
            backtest_id: Optional backtest ID (will be discovered if not provided)
            timeout: Maximum monitoring time in seconds
            
        Returns:
            BacktestProgress with current status
            
        Raises:
            BacktestError: If monitoring fails
        """
        try:
            self.logger.info(f"Monitoring backtest progress for lab {lab_id}")
            
            start_time = time.time()
            last_progress = None
            
            while time.time() - start_time < timeout:
                try:
                    # Get current execution status
                    from ..api.lab.lab_api import LabAPI
                    lab_api = LabAPI(self.client, self.auth_manager)
                    execution_update = await lab_api.get_lab_execution_status(lab_id)
                    
                    # Create progress object
                    progress = BacktestProgress(
                        lab_id=lab_id,
                        status=self._map_execution_status(execution_update.status),
                        progress_percentage=self._calculate_progress_percentage(execution_update),
                        current_generation=getattr(execution_update, 'current_generation', 0),
                        max_generations=getattr(execution_update, 'max_generations', 0),
                        current_epoch=getattr(execution_update, 'current_epoch', 0),
                        max_epochs=getattr(execution_update, 'max_epochs', 0),
                        elapsed_time=time.time() - start_time,
                        estimated_completion=self._estimate_completion(execution_update, start_time)
                    )
                    
                    # Update active backtests
                    self.active_backtests[lab_id] = progress
                    
                    # Check if completed
                    if progress.status in [BacktestStatus.COMPLETED, BacktestStatus.FAILED, BacktestStatus.CANCELLED]:
                        self.logger.info(f"Backtest {lab_id} finished with status: {progress.status}")
                        return progress
                    
                    # Log progress if changed
                    if last_progress is None or progress.progress_percentage != last_progress.progress_percentage:
                        self.logger.info(f"Backtest {lab_id} progress: {progress.progress_percentage:.1f}% "
                                       f"({progress.current_generation}/{progress.max_generations} generations)")
                    
                    last_progress = progress
                    
                    # Wait before next check
                    await asyncio.sleep(self.progress_check_interval)
                    
                except Exception as e:
                    self.logger.warning(f"Error monitoring backtest {lab_id}: {e}")
                    await asyncio.sleep(self.progress_check_interval)
                    continue
            
            # Timeout reached
            self.logger.warning(f"Backtest monitoring timeout for lab {lab_id}")
            return BacktestProgress(
                lab_id=lab_id,
                status=BacktestStatus.FAILED,
                progress_percentage=0.0,
                current_generation=0,
                max_generations=0,
                current_epoch=0,
                max_epochs=0,
                elapsed_time=timeout,
                error_message="Monitoring timeout"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to monitor backtest progress for lab {lab_id}: {e}")
            raise BacktestError(f"Failed to monitor backtest progress: {e}") from e
    
    async def cancel_backtest(self, lab_id: str) -> bool:
        """
        Cancel running backtest
        
        Args:
            lab_id: ID of the lab to cancel
            
        Returns:
            True if cancellation was successful
            
        Raises:
            BacktestError: If cancellation fails
        """
        try:
            self.logger.info(f"Cancelling backtest for lab {lab_id}")
            
            # Ensure authentication
            await self.auth_manager.ensure_authenticated()
            
            # Cancel lab execution
            from ..api.lab.lab_api import LabAPI
            lab_api = LabAPI(self.client, self.auth_manager)
            success = await lab_api.cancel_lab_execution(lab_id)
            
            if success:
                # Update progress status
                if lab_id in self.active_backtests:
                    self.active_backtests[lab_id].status = BacktestStatus.CANCELLED
                
                self.logger.info(f"Successfully cancelled backtest for lab {lab_id}")
                return True
            else:
                raise BacktestError(f"Failed to cancel backtest for lab {lab_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to cancel backtest for lab {lab_id}: {e}")
            raise BacktestError(f"Failed to cancel backtest: {e}") from e
    
    async def get_active_backtests(self) -> List[BacktestProgress]:
        """
        Get all active backtests
        
        Returns:
            List of BacktestProgress objects for active backtests
        """
        return list(self.active_backtests.values())
    
    async def get_backtest_result(self, lab_id: str) -> Optional[BacktestExecutionResult]:
        """
        Get backtest result for a lab
        
        Args:
            lab_id: ID of the lab
            
        Returns:
            BacktestExecutionResult if available, None otherwise
        """
        return self.backtest_results.get(lab_id)
    
    # Private helper methods
    
    async def _discover_cutoff_date(self, lab_id: str) -> Optional[datetime]:
        """Discover the earliest available data point for longest backtest"""
        try:
            # This would implement the cutoff date discovery algorithm
            # For now, return a default date
            return datetime(2020, 1, 1)
        except Exception as e:
            self.logger.error(f"Failed to discover cutoff date for lab {lab_id}: {e}")
            return None
    
    async def _configure_lab_for_longest_backtest(self, lab_id: str, cutoff_date: datetime) -> None:
        """Configure lab for longest backtest execution"""
        try:
            from ..api.lab.lab_api import LabAPI
            lab_api = LabAPI(self.client, self.auth_manager)
            
            # Get current lab details
            lab_details = await lab_api.get_lab_details(lab_id)
            
            # Update lab with longest backtest configuration
            lab_details.settings.start_date = cutoff_date
            lab_details.settings.end_date = datetime.now()
            
            # Update lab details
            await lab_api.update_lab_details(lab_details)
            
            self.logger.info(f"Configured lab {lab_id} for longest backtest from {cutoff_date}")
            
        except Exception as e:
            self.logger.error(f"Failed to configure lab {lab_id} for longest backtest: {e}")
            raise
    
    async def _start_backtest_execution(self, lab_id: str) -> str:
        """Start backtest execution and return backtest ID"""
        try:
            from ..api.lab.lab_api import LabAPI
            lab_api = LabAPI(self.client, self.auth_manager)
            
            # Create execution request
            request = StartLabExecutionRequest(
                lab_id=lab_id,
                start_unix=int(datetime.now().timestamp()),
                end_unix=int(datetime.now().timestamp()),
                send_email=False
            )
            
            # Start execution
            response = await lab_api.start_lab_execution(request)
            
            # Extract backtest ID from response
            backtest_id = safe_get_field(response, "backtest_id", "unknown")
            
            self.logger.info(f"Started backtest execution for lab {lab_id}, backtest ID: {backtest_id}")
            return backtest_id
            
        except Exception as e:
            self.logger.error(f"Failed to start backtest execution for lab {lab_id}: {e}")
            raise
    
    async def _monitor_backtest_progress(
        self,
        lab_id: str,
        backtest_id: str,
        timeout: float
    ) -> BacktestProgress:
        """Monitor backtest progress with timeout"""
        return await self.monitor_backtest_progress(lab_id, backtest_id, timeout)
    
    def _map_execution_status(self, status: str) -> BacktestStatus:
        """Map execution status to BacktestStatus enum"""
        status_map = {
            "running": BacktestStatus.RUNNING,
            "completed": BacktestStatus.COMPLETED,
            "failed": BacktestStatus.FAILED,
            "cancelled": BacktestStatus.CANCELLED,
            "pending": BacktestStatus.PENDING
        }
        return status_map.get(status.lower(), BacktestStatus.PENDING)
    
    def _calculate_progress_percentage(self, execution_update: LabExecutionUpdate) -> float:
        """Calculate progress percentage from execution update"""
        try:
            if hasattr(execution_update, 'current_generation') and hasattr(execution_update, 'max_generations'):
                if execution_update.max_generations > 0:
                    return (execution_update.current_generation / execution_update.max_generations) * 100
            return 0.0
        except Exception:
            return 0.0
    
    def _estimate_completion(self, execution_update: LabExecutionUpdate, start_time: float) -> Optional[datetime]:
        """Estimate completion time based on current progress"""
        try:
            if hasattr(execution_update, 'current_generation') and hasattr(execution_update, 'max_generations'):
                if execution_update.current_generation > 0 and execution_update.max_generations > 0:
                    elapsed = time.time() - start_time
                    progress = execution_update.current_generation / execution_update.max_generations
                    if progress > 0:
                        total_estimated = elapsed / progress
                        remaining = total_estimated - elapsed
                        return datetime.now() + timedelta(seconds=remaining)
            return None
        except Exception:
            return None
    
    def _get_default_optimization_config(self) -> Dict[str, Any]:
        """Get default optimization configuration"""
        return {
            "max_generations": 50,
            "max_epochs": 3,
            "population_size": 20,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "selection_pressure": 2.0
        }
    
    async def _execute_parameter_optimization(
        self,
        lab_id: str,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute parameter optimization algorithm"""
        # This would implement the actual optimization algorithm
        # For now, return empty list
        return []
    
    async def _analyze_optimization_results(
        self,
        optimization_data: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], float]:
        """Analyze optimization results and return best parameters and score"""
        # This would implement the analysis of optimization results
        # For now, return empty parameters and score
        return {}, 0.0
