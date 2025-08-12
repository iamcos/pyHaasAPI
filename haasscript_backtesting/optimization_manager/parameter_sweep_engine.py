"""
Parameter sweep execution engine for HaasScript backtesting system.

This module handles parameter range generation, validation, and batch backtest execution
with parameter variations. It provides progress tracking for long-running optimization tasks.
"""

import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.optimization_models import (
    SweepConfig, SweepExecution, SweepStatus, ParameterRange
)
from ..models.backtest_models import BacktestConfig, BacktestExecution
from ..models.result_models import ProcessedResults
from ..backtest_manager.backtest_manager import BacktestManager
from ..results_manager.results_manager import ResultsManager


logger = logging.getLogger(__name__)


class ParameterSweepEngine:
    """
    Engine for executing parameter sweeps with batch backtest execution.
    
    Handles parameter range generation, validation, and concurrent execution
    of backtests with different parameter combinations.
    """
    
    def __init__(
        self,
        backtest_manager: BacktestManager,
        results_manager: ResultsManager,
        max_concurrent_executions: int = 5
    ):
        """
        Initialize the parameter sweep engine.
        
        Args:
            backtest_manager: Manager for backtest execution
            results_manager: Manager for result processing
            max_concurrent_executions: Maximum concurrent backtest executions
        """
        self.backtest_manager = backtest_manager
        self.results_manager = results_manager
        self.max_concurrent_executions = max_concurrent_executions
        
        # Active sweep tracking
        self.active_sweeps: Dict[str, SweepExecution] = {}
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        
        # Thread pool for concurrent execution
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_executions)
    
    def validate_parameter_ranges(self, parameter_ranges: List[ParameterRange]) -> List[str]:
        """
        Validate parameter ranges for correctness.
        
        Args:
            parameter_ranges: List of parameter ranges to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        for param_range in parameter_ranges:
            # Check basic range validity
            if param_range.min_value >= param_range.max_value:
                errors.append(f"Parameter '{param_range.name}': min_value must be less than max_value")
            
            if param_range.step <= 0:
                errors.append(f"Parameter '{param_range.name}': step must be positive")
            
            # Check if step size makes sense
            range_size = param_range.max_value - param_range.min_value
            if param_range.step > range_size:
                errors.append(f"Parameter '{param_range.name}': step size larger than range")
            
            # Check for reasonable number of combinations
            total_values = len(param_range.generate_values())
            if total_values > 1000:
                errors.append(
                    f"Parameter '{param_range.name}': generates {total_values} values, "
                    "consider larger step size"
                )
        
        # Check total combinations
        total_combinations = 1
        for param_range in parameter_ranges:
            total_combinations *= param_range.total_combinations
        
        if total_combinations > 10000:
            errors.append(
                f"Total parameter combinations ({total_combinations}) exceeds recommended limit (10000)"
            )
        
        return errors
    
    def create_sweep(self, config: SweepConfig) -> SweepExecution:
        """
        Create a new parameter sweep execution.
        
        Args:
            config: Sweep configuration
            
        Returns:
            SweepExecution object for tracking
            
        Raises:
            ValueError: If parameter ranges are invalid
        """
        # Validate parameter ranges
        validation_errors = self.validate_parameter_ranges(config.parameter_ranges)
        if validation_errors:
            raise ValueError(f"Invalid parameter ranges: {'; '.join(validation_errors)}")
        
        # Create sweep execution
        sweep_id = str(uuid.uuid4())
        sweep_execution = SweepExecution(
            sweep_id=sweep_id,
            config=config,
            status=SweepStatus.PENDING,
            started_at=datetime.now(),
            total_backtests=config.total_combinations
        )
        
        self.active_sweeps[sweep_id] = sweep_execution
        self.progress_callbacks[sweep_id] = []
        
        logger.info(f"Created parameter sweep {sweep_id} with {config.total_combinations} combinations")
        
        return sweep_execution
    
    def add_progress_callback(self, sweep_id: str, callback: Callable[[SweepExecution], None]) -> None:
        """
        Add a progress callback for sweep execution updates.
        
        Args:
            sweep_id: ID of the sweep
            callback: Function to call on progress updates
        """
        if sweep_id in self.progress_callbacks:
            self.progress_callbacks[sweep_id].append(callback)
    
    def _notify_progress(self, sweep_execution: SweepExecution) -> None:
        """Notify all progress callbacks of sweep updates."""
        callbacks = self.progress_callbacks.get(sweep_execution.sweep_id, [])
        for callback in callbacks:
            try:
                callback(sweep_execution)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def execute_sweep(self, sweep_execution: SweepExecution) -> SweepExecution:
        """
        Execute a parameter sweep with batch backtest execution.
        
        Args:
            sweep_execution: Sweep execution to run
            
        Returns:
            Updated sweep execution with results
        """
        try:
            sweep_execution.status = SweepStatus.RUNNING
            self._notify_progress(sweep_execution)
            
            logger.info(f"Starting parameter sweep {sweep_execution.sweep_id}")
            
            # Generate all parameter combinations
            parameter_sets = sweep_execution.config.generate_parameter_sets()
            
            # Execute backtests in batches
            self._execute_batch_backtests(sweep_execution, parameter_sets)
            
            # Mark as completed
            sweep_execution.status = SweepStatus.COMPLETED
            sweep_execution.completed_at = datetime.now()
            
            logger.info(f"Completed parameter sweep {sweep_execution.sweep_id}")
            
        except Exception as e:
            logger.error(f"Error in parameter sweep {sweep_execution.sweep_id}: {e}")
            sweep_execution.status = SweepStatus.FAILED
            raise
        
        finally:
            self._notify_progress(sweep_execution)
        
        return sweep_execution
    
    def _execute_batch_backtests(
        self, 
        sweep_execution: SweepExecution, 
        parameter_sets: List[Dict[str, Any]]
    ) -> None:
        """
        Execute backtests in batches with concurrent execution.
        
        Args:
            sweep_execution: Sweep execution being processed
            parameter_sets: List of parameter combinations to test
        """
        max_concurrent = sweep_execution.config.max_concurrent_executions
        
        # Submit backtests in batches
        futures = []
        for i, parameters in enumerate(parameter_sets):
            # Create backtest config with parameters
            backtest_config = self._create_backtest_config(
                sweep_execution.config.base_config, 
                parameters
            )
            
            # Submit backtest execution
            future = self.executor.submit(
                self._execute_single_backtest,
                sweep_execution,
                backtest_config,
                parameters,
                i
            )
            futures.append(future)
            
            # Limit concurrent executions
            if len(futures) >= max_concurrent:
                self._process_completed_futures(sweep_execution, futures)
                futures = [f for f in futures if not f.done()]
        
        # Process remaining futures
        if futures:
            self._process_completed_futures(sweep_execution, futures)
    
    def _create_backtest_config(
        self, 
        base_config: BacktestConfig, 
        parameters: Dict[str, Any]
    ) -> BacktestConfig:
        """
        Create backtest config with parameter overrides.
        
        Args:
            base_config: Base configuration
            parameters: Parameter overrides
            
        Returns:
            New backtest config with parameters applied
        """
        # Create a copy of base config
        config_dict = {
            'script_id': base_config.script_id,
            'account_id': base_config.account_id,
            'market_tag': base_config.market_tag,
            'start_time': base_config.start_time,
            'end_time': base_config.end_time,
            'interval': base_config.interval,
            'execution_amount': base_config.execution_amount,
            'leverage': base_config.leverage,
            'position_mode': base_config.position_mode,
            'script_parameters': base_config.script_parameters.copy()
        }
        
        # Apply parameter overrides
        config_dict['script_parameters'].update(parameters)
        
        return BacktestConfig(**config_dict)
    
    def _execute_single_backtest(
        self,
        sweep_execution: SweepExecution,
        backtest_config: BacktestConfig,
        parameters: Dict[str, Any],
        index: int
    ) -> Optional[ProcessedResults]:
        """
        Execute a single backtest as part of parameter sweep.
        
        Args:
            sweep_execution: Parent sweep execution
            backtest_config: Configuration for this backtest
            parameters: Parameters used for this backtest
            index: Index of this backtest in the sweep
            
        Returns:
            Processed results if successful, None if failed
        """
        try:
            logger.debug(f"Executing backtest {index} for sweep {sweep_execution.sweep_id}")
            
            # Execute backtest
            backtest_execution = self.backtest_manager.execute_backtest(backtest_config)
            
            # Monitor execution until completion
            while not backtest_execution.status.is_complete:
                backtest_execution = self.backtest_manager.monitor_execution(
                    backtest_execution.backtest_id
                )
                
                # Check for early stopping
                if sweep_execution.config.early_stopping:
                    if self._should_early_stop(sweep_execution):
                        logger.info(f"Early stopping triggered for sweep {sweep_execution.sweep_id}")
                        return None
                
                # Small delay to avoid overwhelming the API
                import time
                time.sleep(1)
            
            # Process results
            if backtest_execution.status.is_complete:
                results = self.results_manager.process_results(backtest_execution.backtest_id)
                
                # Update sweep with results
                sweep_execution.all_results.append(results)
                sweep_execution.update_best_result(results, parameters)
                sweep_execution.completed_backtests += 1
                
                logger.debug(f"Completed backtest {index} for sweep {sweep_execution.sweep_id}")
                return results
            else:
                sweep_execution.failed_backtests += 1
                logger.warning(f"Backtest {index} failed for sweep {sweep_execution.sweep_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error executing backtest {index} for sweep {sweep_execution.sweep_id}: {e}")
            sweep_execution.failed_backtests += 1
            return None
        
        finally:
            self._notify_progress(sweep_execution)
    
    def _process_completed_futures(
        self, 
        sweep_execution: SweepExecution, 
        futures: List
    ) -> None:
        """
        Process completed futures and update progress.
        
        Args:
            sweep_execution: Sweep execution being processed
            futures: List of futures to process
        """
        for future in as_completed(futures):
            try:
                result = future.result()
                # Result processing is handled in _execute_single_backtest
            except Exception as e:
                logger.error(f"Error processing future: {e}")
                sweep_execution.failed_backtests += 1
                self._notify_progress(sweep_execution)
    
    def _should_early_stop(self, sweep_execution: SweepExecution) -> bool:
        """
        Check if early stopping criteria are met.
        
        Args:
            sweep_execution: Sweep execution to check
            
        Returns:
            True if should stop early
        """
        if not sweep_execution.config.early_stopping:
            return False
        
        # Simple early stopping: if we have enough results and no improvement
        min_results = sweep_execution.config.early_stopping_patience
        if len(sweep_execution.all_results) < min_results:
            return False
        
        # Check if recent results show improvement
        recent_results = sweep_execution.all_results[-min_results:]
        metric_name = sweep_execution.config.optimization_metric
        
        recent_scores = [
            getattr(result.execution_metrics, metric_name) 
            for result in recent_results
        ]
        
        # If no improvement in recent results, consider early stopping
        best_recent = max(recent_scores)
        if sweep_execution.best_result:
            best_overall = getattr(sweep_execution.best_result.execution_metrics, metric_name)
            return best_recent <= best_overall
        
        return False
    
    def get_sweep_status(self, sweep_id: str) -> Optional[SweepExecution]:
        """
        Get current status of a parameter sweep.
        
        Args:
            sweep_id: ID of the sweep
            
        Returns:
            Sweep execution status or None if not found
        """
        return self.active_sweeps.get(sweep_id)
    
    def cancel_sweep(self, sweep_id: str) -> bool:
        """
        Cancel a running parameter sweep.
        
        Args:
            sweep_id: ID of the sweep to cancel
            
        Returns:
            True if successfully cancelled
        """
        sweep_execution = self.active_sweeps.get(sweep_id)
        if not sweep_execution:
            return False
        
        if sweep_execution.status == SweepStatus.RUNNING:
            sweep_execution.status = SweepStatus.CANCELLED
            self._notify_progress(sweep_execution)
            logger.info(f"Cancelled parameter sweep {sweep_id}")
            return True
        
        return False
    
    def cleanup_completed_sweeps(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed sweeps to free memory.
        
        Args:
            max_age_hours: Maximum age in hours for keeping completed sweeps
            
        Returns:
            Number of sweeps cleaned up
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        sweep_ids_to_remove = []
        for sweep_id, sweep_execution in self.active_sweeps.items():
            if (sweep_execution.status in [SweepStatus.COMPLETED, SweepStatus.FAILED, SweepStatus.CANCELLED] and
                sweep_execution.completed_at and sweep_execution.completed_at < cutoff_time):
                sweep_ids_to_remove.append(sweep_id)
        
        for sweep_id in sweep_ids_to_remove:
            del self.active_sweeps[sweep_id]
            if sweep_id in self.progress_callbacks:
                del self.progress_callbacks[sweep_id]
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old parameter sweeps")
        return cleaned_count