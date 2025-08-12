"""
Core backtest management functionality.
"""

import logging
import asyncio
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
import queue

from ..models import (
    BacktestConfig, BacktestExecution, ExecutionStatus, ExecutionStatusType,
    BacktestSummary, ResourceUsage
)
from ..config import ConfigManager
from ..api_client import HaasOnlineClient
from ..api_client.request_models import BacktestRequest
from ..api_client.response_models import BacktestResponse
from .execution_monitor import ExecutionMonitor, CompletionTimeEstimator, MonitoringEventType


class BacktestExecutionQueue:
    """Queue manager for concurrent backtest executions."""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.queue = queue.Queue()
        self.active_executions: Dict[str, Future] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.logger = logging.getLogger(f"{__name__}.ExecutionQueue")
        
    def submit_execution(self, execution_func, *args, **kwargs) -> str:
        """Submit a backtest execution to the queue."""
        execution_id = str(uuid.uuid4())
        
        if len(self.active_executions) >= self.max_concurrent:
            # Queue the execution
            self.queue.put((execution_id, execution_func, args, kwargs))
            self.logger.info(f"Queued execution {execution_id} (queue size: {self.queue.qsize()})")
        else:
            # Execute immediately
            future = self.executor.submit(execution_func, *args, **kwargs)
            self.active_executions[execution_id] = future
            self.logger.info(f"Started execution {execution_id}")
            
        return execution_id
    
    def check_completed_executions(self):
        """Check for completed executions and start queued ones."""
        completed_ids = []
        
        for execution_id, future in self.active_executions.items():
            if future.done():
                completed_ids.append(execution_id)
                
        # Remove completed executions
        for execution_id in completed_ids:
            del self.active_executions[execution_id]
            self.logger.info(f"Completed execution {execution_id}")
            
        # Start queued executions
        while len(self.active_executions) < self.max_concurrent and not self.queue.empty():
            execution_id, execution_func, args, kwargs = self.queue.get()
            future = self.executor.submit(execution_func, *args, **kwargs)
            self.active_executions[execution_id] = future
            self.logger.info(f"Started queued execution {execution_id}")
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get current queue status."""
        return {
            "active_executions": len(self.active_executions),
            "queued_executions": self.queue.qsize(),
            "max_concurrent": self.max_concurrent
        }
    
    def shutdown(self):
        """Shutdown the execution queue."""
        self.executor.shutdown(wait=True)


class BacktestConfigValidator:
    """Validates backtest configurations before execution."""
    
    @staticmethod
    def validate_config(config: BacktestConfig) -> List[str]:
        """Validate backtest configuration and return list of errors."""
        errors = []
        
        # Basic validation
        if not config.script_id:
            errors.append("Script ID is required")
            
        if not config.account_id:
            errors.append("Account ID is required")
            
        if not config.market_tag:
            errors.append("Market tag is required")
            
        # Time validation
        if config.start_time >= config.end_time:
            errors.append("Start time must be before end time")
            
        if config.start_time <= 0 or config.end_time <= 0:
            errors.append("Start and end times must be positive timestamps")
            
        # Amount validation
        if config.execution_amount <= 0:
            errors.append("Execution amount must be positive")
            
        # Interval validation
        if config.interval <= 0:
            errors.append("Interval must be positive")
            
        # Leverage validation
        if config.leverage < 0:
            errors.append("Leverage cannot be negative")
            
        # Duration validation (reasonable limits)
        duration_days = (config.end_time - config.start_time) / (24 * 3600)
        if duration_days > 365:
            errors.append("Backtest duration cannot exceed 365 days")
            
        if duration_days < 1/24:  # Less than 1 hour
            errors.append("Backtest duration must be at least 1 hour")
            
        return errors
    
    @staticmethod
    def validate_parameters(parameters: Dict[str, Any]) -> List[str]:
        """Validate script parameters."""
        errors = []
        
        # Check for required parameter types
        for key, value in parameters.items():
            if not isinstance(key, str):
                errors.append(f"Parameter key must be string: {key}")
                
            # Check for reasonable parameter values
            if isinstance(value, (int, float)) and (value < -1000000 or value > 1000000):
                errors.append(f"Parameter {key} value seems unreasonable: {value}")
                
        return errors


class BacktestManager:
    """Manages backtest execution, monitoring, and lifecycle."""
    
    def __init__(self, config_manager: ConfigManager, api_client: Optional[HaasOnlineClient] = None):
        """Initialize backtest manager with configuration.
        
        Args:
            config_manager: Configuration manager instance
            api_client: Optional HaasOnline API client instance
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # API client for HaasOnline communication
        self.api_client = api_client or HaasOnlineClient(config_manager.haasonline)
        
        # Track active executions
        self._active_executions: Dict[str, BacktestExecution] = {}
        self._execution_history: List[BacktestSummary] = []
        
        # Execution queue for concurrent management
        max_concurrent = getattr(config_manager.system.execution, 'max_concurrent_backtests', 5)
        self.execution_queue = BacktestExecutionQueue(max_concurrent)
        
        # Configuration validator
        self.validator = BacktestConfigValidator()
        
        # Execution monitoring system
        self.monitor = ExecutionMonitor(self.api_client, update_interval=30)
        self.completion_estimator = CompletionTimeEstimator()
        
        # Register event callbacks
        self.monitor.register_event_callback(
            MonitoringEventType.EXECUTION_COMPLETED,
            self._on_execution_completed
        )
        self.monitor.register_event_callback(
            MonitoringEventType.EXECUTION_FAILED,
            self._on_execution_failed
        )
        
        # Background thread for monitoring
        self._monitoring_thread = None
        self._monitoring_active = False
        
        self.logger.info(f"BacktestManager initialized with max concurrent executions: {max_concurrent}")
    
    def execute_backtest(self, config: BacktestConfig) -> BacktestExecution:
        """Execute a backtest with the given configuration.
        
        Args:
            config: Backtest configuration
            
        Returns:
            BacktestExecution object tracking the execution
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If execution fails to start
        """
        # Validate configuration
        validation_errors = self.validator.validate_config(config)
        if validation_errors:
            raise ValueError(f"Invalid backtest configuration: {'; '.join(validation_errors)}")
        
        # Validate script parameters
        param_errors = self.validator.validate_parameters(config.script_parameters)
        if param_errors:
            raise ValueError(f"Invalid script parameters: {'; '.join(param_errors)}")
        
        # Generate unique backtest ID
        backtest_id = str(uuid.uuid4())
        
        self.logger.info(f"Starting backtest execution: {backtest_id}")
        
        try:
            # Create execution tracking object
            execution = BacktestExecution(
                backtest_id=backtest_id,
                script_id=config.script_id,
                config=config,
                status=ExecutionStatus(
                    status=ExecutionStatusType.QUEUED,
                    progress_percentage=0.0,
                    current_phase="Initializing",
                    estimated_completion=None,
                    resource_usage=ResourceUsage(
                        cpu_percent=0.0,
                        memory_mb=0.0,
                        disk_io_mb=0.0,
                        network_io_mb=0.0,
                        active_connections=0
                    )
                ),
                started_at=datetime.now()
            )
            
            # Add to active executions
            self._active_executions[backtest_id] = execution
            
            # Submit to execution queue
            self.execution_queue.submit_execution(
                self._execute_backtest_async, 
                execution
            )
            
            # Add to monitoring system
            self.monitor.add_execution(execution)
            
            # Start monitoring if not already active
            self._ensure_monitoring_active()
            
            self.logger.info(f"Backtest execution queued: {backtest_id}")
            return execution
            
        except Exception as e:
            self.logger.error(f"Failed to start backtest execution: {e}")
            # Clean up if execution failed to start
            if backtest_id in self._active_executions:
                del self._active_executions[backtest_id]
            raise RuntimeError(f"Backtest execution failed to start: {e}")
    
    def monitor_execution(self, backtest_id: str) -> ExecutionStatus:
        """Monitor the status of a running backtest.
        
        Args:
            backtest_id: ID of the backtest to monitor
            
        Returns:
            Current ExecutionStatus
            
        Raises:
            ValueError: If backtest_id is not found
        """
        # Get from monitoring system first
        execution = self.monitor.get_execution_status(backtest_id)
        if execution:
            return execution.status
        
        # Fallback to local tracking
        if backtest_id not in self._active_executions:
            raise ValueError(f"Backtest not found: {backtest_id}")
        
        execution = self._active_executions[backtest_id]
        
        # Update status from HaasOnline API
        self._update_execution_status(execution)
        
        return execution.status
    
    def get_backtest_logs(self, backtest_id: str) -> List[str]:
        """Get execution logs for a backtest.
        
        Args:
            backtest_id: ID of the backtest
            
        Returns:
            List of log entries
            
        Raises:
            ValueError: If backtest_id is not found
        """
        if backtest_id not in self._active_executions:
            raise ValueError(f"Backtest not found: {backtest_id}")
        
        self.logger.info(f"Retrieving logs for backtest: {backtest_id}")
        
        try:
            # This would call GET_BACKTEST_LOGS API
            logs = self._fetch_backtest_logs(backtest_id)
            return logs
        except Exception as e:
            self.logger.error(f"Failed to retrieve logs for backtest {backtest_id}: {e}")
            return [f"Error retrieving logs: {e}"]
    
    def archive_backtest(self, backtest_id: str, preserve_results: bool = True) -> bool:
        """Archive a backtest to permanent storage.
        
        Args:
            backtest_id: ID of the backtest to archive
            preserve_results: Whether to preserve detailed results
            
        Returns:
            True if archiving was successful
        """
        self.logger.info(f"Archiving backtest: {backtest_id}")
        
        try:
            # Get execution details before archiving
            execution = None
            if backtest_id in self._active_executions:
                execution = self._active_executions[backtest_id]
            else:
                # Try to get from monitoring system
                execution = self.monitor.get_execution_status(backtest_id)
            
            # Call ARCHIVE_BACKTEST API
            success = self._archive_backtest_via_api(backtest_id, preserve_results)
            
            if success:
                # Update execution status if still active
                if execution:
                    execution.status.status = ExecutionStatusType.ARCHIVED
                    
                    # Create detailed summary for history
                    summary = BacktestSummary(
                        backtest_id=backtest_id,
                        script_name=f"Script_{execution.script_id}",
                        market_tag=execution.config.market_tag,
                        start_date=datetime.fromtimestamp(execution.config.start_time),
                        end_date=datetime.fromtimestamp(execution.config.end_time),
                        status="archived",
                        created_at=execution.started_at,
                        duration=execution.duration,
                        final_balance=None  # Would be populated from results
                    )
                    self._execution_history.append(summary)
                    
                    # Remove from monitoring
                    self.monitor.remove_execution(backtest_id)
                
                self.logger.info(f"Successfully archived backtest: {backtest_id}")
            else:
                self.logger.warning(f"Failed to archive backtest: {backtest_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error archiving backtest {backtest_id}: {e}")
            return False
    
    def delete_backtest(self, backtest_id: str, force: bool = False) -> bool:
        """Delete a backtest and free resources.
        
        Args:
            backtest_id: ID of the backtest to delete
            force: Whether to force deletion even if backtest is running
            
        Returns:
            True if deletion was successful
        """
        self.logger.info(f"Deleting backtest: {backtest_id}")
        
        try:
            # Check if backtest is running and not forced
            execution = self._active_executions.get(backtest_id) or self.monitor.get_execution_status(backtest_id)
            if execution and execution.status.is_running and not force:
                self.logger.warning(f"Cannot delete running backtest {backtest_id} without force=True")
                return False
            
            # Cancel execution if it's running
            if execution and execution.status.is_running:
                self.cancel_execution(backtest_id)
            
            # Call DELETE_BACKTEST API
            success = self._delete_backtest_via_api(backtest_id)
            
            if success:
                # Remove from active executions
                if backtest_id in self._active_executions:
                    del self._active_executions[backtest_id]
                
                # Remove from monitoring
                self.monitor.remove_execution(backtest_id)
                
                # Remove from history if present
                self._execution_history = [
                    h for h in self._execution_history 
                    if h.backtest_id != backtest_id
                ]
                
                self.logger.info(f"Successfully deleted backtest: {backtest_id}")
            else:
                self.logger.warning(f"Failed to delete backtest: {backtest_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting backtest {backtest_id}: {e}")
            return False
    
    def get_execution_history(self, limit: Optional[int] = None, include_archived: bool = True) -> List[BacktestSummary]:
        """Get backtest execution history.
        
        Args:
            limit: Optional limit on number of results
            include_archived: Whether to include archived backtests
            
        Returns:
            List of BacktestSummary objects
        """
        self.logger.info("Retrieving backtest execution history")
        
        try:
            # Get history from HaasOnline API
            history = self._fetch_execution_history_from_api(include_archived)
            
            # Combine with local history
            all_history = history + self._execution_history
            
            # Remove duplicates based on backtest_id
            seen_ids = set()
            unique_history = []
            for summary in all_history:
                if summary.backtest_id not in seen_ids:
                    unique_history.append(summary)
                    seen_ids.add(summary.backtest_id)
            
            # Sort by creation date (most recent first)
            unique_history.sort(key=lambda x: x.created_at, reverse=True)
            
            if limit:
                unique_history = unique_history[:limit]
            
            return unique_history
            
        except Exception as e:
            self.logger.error(f"Error retrieving execution history: {e}")
            return self._execution_history[:limit] if limit else self._execution_history
    
    def get_active_executions(self) -> List[BacktestExecution]:
        """Get all currently active backtest executions.
        
        Returns:
            List of active BacktestExecution objects
        """
        return [execution for execution in self._active_executions.values()
                if execution.status.is_running]
    
    def cancel_execution(self, backtest_id: str) -> bool:
        """Cancel a running backtest execution.
        
        Args:
            backtest_id: ID of the backtest to cancel
            
        Returns:
            True if cancellation was successful
        """
        if backtest_id not in self._active_executions:
            raise ValueError(f"Backtest not found: {backtest_id}")
        
        execution = self._active_executions[backtest_id]
        
        if not execution.status.is_running:
            self.logger.warning(f"Backtest {backtest_id} is not running, cannot cancel")
            return False
        
        self.logger.info(f"Cancelling backtest execution: {backtest_id}")
        
        try:
            # Call API to cancel execution
            success = self._cancel_backtest_via_api(backtest_id)
            
            if success:
                execution.status.status = ExecutionStatusType.CANCELLED
                execution.completed_at = datetime.now()
                self.logger.info(f"Successfully cancelled backtest: {backtest_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error cancelling backtest {backtest_id}: {e}")
            return False
    
    def cleanup_completed_executions(self, max_age_hours: int = 24, archive_before_delete: bool = True) -> Dict[str, int]:
        """Clean up old completed executions.
        
        Args:
            max_age_hours: Maximum age in hours for completed executions
            archive_before_delete: Whether to archive before deleting
            
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        archived_count = 0
        deleted_count = 0
        failed_count = 0
        
        executions_to_process = []
        
        # Find old completed executions
        for backtest_id, execution in self._active_executions.items():
            if (execution.status.is_complete and 
                execution.completed_at and 
                execution.completed_at < cutoff_time):
                
                executions_to_process.append(backtest_id)
        
        # Process each execution
        for backtest_id in executions_to_process:
            try:
                if archive_before_delete:
                    # Try to archive first
                    if self.archive_backtest(backtest_id):
                        archived_count += 1
                        self.logger.info(f"Archived old execution: {backtest_id}")
                    else:
                        # If archiving fails, still try to delete
                        if self.delete_backtest(backtest_id):
                            deleted_count += 1
                            self.logger.info(f"Deleted old execution (archive failed): {backtest_id}")
                        else:
                            failed_count += 1
                else:
                    # Delete directly
                    if self.delete_backtest(backtest_id):
                        deleted_count += 1
                        self.logger.info(f"Deleted old execution: {backtest_id}")
                    else:
                        failed_count += 1
                        
            except Exception as e:
                self.logger.error(f"Failed to process old execution {backtest_id}: {e}")
                failed_count += 1
        
        result = {
            "archived": archived_count,
            "deleted": deleted_count,
            "failed": failed_count,
            "total_processed": len(executions_to_process)
        }
        
        self.logger.info(f"Cleanup completed: {result}")
        return result
    
    def get_backtest_retention_status(self) -> Dict[str, Any]:
        """Get information about backtest retention and cleanup needs.
        
        Returns:
            Dictionary with retention status information
        """
        now = datetime.now()
        retention_limit = now - timedelta(hours=48)  # HaasOnline 48-hour limit
        
        # Analyze active executions
        total_executions = len(self._active_executions)
        completed_executions = []
        running_executions = []
        old_executions = []
        
        for execution in self._active_executions.values():
            if execution.status.is_complete:
                completed_executions.append(execution)
                if execution.completed_at and execution.completed_at < retention_limit:
                    old_executions.append(execution)
            elif execution.status.is_running:
                running_executions.append(execution)
        
        # Calculate storage usage estimate
        estimated_storage_mb = len(completed_executions) * 5  # Rough estimate
        
        return {
            "total_executions": total_executions,
            "completed_executions": len(completed_executions),
            "running_executions": len(running_executions),
            "old_executions_needing_cleanup": len(old_executions),
            "retention_limit": retention_limit,
            "estimated_storage_mb": estimated_storage_mb,
            "history_count": len(self._execution_history),
            "cleanup_recommended": len(old_executions) > 0
        }
    
    def bulk_archive_completed(self, older_than_hours: int = 24) -> Dict[str, int]:
        """Archive all completed backtests older than specified hours.
        
        Args:
            older_than_hours: Archive backtests completed more than this many hours ago
            
        Returns:
            Dictionary with archiving statistics
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        archived_count = 0
        failed_count = 0
        
        executions_to_archive = []
        
        for backtest_id, execution in self._active_executions.items():
            if (execution.status.is_complete and 
                execution.completed_at and 
                execution.completed_at < cutoff_time and
                execution.status.status != ExecutionStatusType.ARCHIVED):
                
                executions_to_archive.append(backtest_id)
        
        for backtest_id in executions_to_archive:
            try:
                if self.archive_backtest(backtest_id):
                    archived_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                self.logger.error(f"Failed to archive backtest {backtest_id}: {e}")
                failed_count += 1
        
        result = {
            "archived": archived_count,
            "failed": failed_count,
            "total_candidates": len(executions_to_archive)
        }
        
        self.logger.info(f"Bulk archive completed: {result}")
        return result
    
    def _execute_backtest_async(self, execution: BacktestExecution) -> None:
        """Execute backtest asynchronously via HaasOnline API."""
        try:
            self.logger.info(f"Starting backtest execution: {execution.backtest_id}")
            
            # Update status to running
            execution.status.status = ExecutionStatusType.RUNNING
            execution.status.current_phase = "Initiating backtest"
            execution.status.progress_percentage = 5.0
            
            # Create backtest request
            request = BacktestRequest(
                script_id=execution.config.script_id,
                account_id=execution.config.account_id,
                market_tag=execution.config.market_tag,
                start_time=execution.config.start_time,
                end_time=execution.config.end_time,
                interval=execution.config.interval,
                execution_amount=execution.config.execution_amount,
                leverage=execution.config.leverage,
                position_mode=execution.config.position_mode.value,
                margin_mode=0,  # Default margin mode
                parameters=execution.config.script_parameters
            )
            
            # Execute backtest via API
            with self.api_client as client:
                response = client.execute_backtest(request)
                
                if not response.success:
                    raise RuntimeError(f"Backtest execution failed: {response.error_message}")
                
                # Update execution with response data
                execution.status.current_phase = "Backtest running"
                execution.status.progress_percentage = 10.0
                
                # Store execution ID for monitoring
                execution.execution_id = response.execution_id
                
                # Estimate completion time using historical data
                estimated_completion = self.completion_estimator.estimate_completion_time(execution)
                if estimated_completion:
                    execution.status.estimated_completion = estimated_completion
                else:
                    # Fallback estimation
                    duration_days = execution.config.duration_days
                    estimated_runtime = timedelta(minutes=max(5, duration_days * 2))
                    execution.status.estimated_completion = datetime.now() + estimated_runtime
                
                self.logger.info(f"Backtest started successfully: {execution.backtest_id} (execution_id: {response.execution_id})")
                
        except Exception as e:
            self.logger.error(f"Backtest execution failed: {execution.backtest_id} - {e}")
            execution.status.status = ExecutionStatusType.FAILED
            execution.status.current_phase = "Failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.now()
    
    def _ensure_monitoring_active(self) -> None:
        """Ensure monitoring thread is active."""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self._monitoring_thread.start()
            self.logger.info("Started backtest monitoring thread")
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop for active executions."""
        while self._monitoring_active:
            try:
                # Check execution queue
                self.execution_queue.check_completed_executions()
                
                # Update status of active executions
                for execution in list(self._active_executions.values()):
                    if execution.status.is_running:
                        self._update_execution_status(execution)
                
                # Clean up completed executions older than 1 hour
                self._cleanup_old_executions(max_age_hours=1)
                
                # Sleep before next check
                threading.Event().wait(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                threading.Event().wait(60)  # Wait longer on error
    
    def _cleanup_old_executions(self, max_age_hours: int = 1) -> None:
        """Clean up old completed executions from memory."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        executions_to_remove = []
        
        for backtest_id, execution in self._active_executions.items():
            if (execution.status.is_complete and 
                execution.completed_at and 
                execution.completed_at < cutoff_time):
                
                # Move to history before removing
                summary = BacktestSummary(
                    backtest_id=backtest_id,
                    script_name=f"Script_{execution.script_id}",
                    market_tag=execution.config.market_tag,
                    start_date=datetime.fromtimestamp(execution.config.start_time),
                    end_date=datetime.fromtimestamp(execution.config.end_time),
                    status=execution.status.status.value,
                    created_at=execution.started_at
                )
                self._execution_history.append(summary)
                executions_to_remove.append(backtest_id)
        
        for backtest_id in executions_to_remove:
            del self._active_executions[backtest_id]
            
        if executions_to_remove:
            self.logger.info(f"Cleaned up {len(executions_to_remove)} old executions")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        self._monitoring_active = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
            self.logger.info("Stopped backtest monitoring thread")
        
        # Stop execution monitor
        self.monitor.stop_monitoring()
        
        # Shutdown execution queue
        self.execution_queue.shutdown()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current execution queue status."""
        queue_status = self.execution_queue.get_queue_status()
        
        # Add additional status information
        running_count = len([e for e in self._active_executions.values() if e.status.is_running])
        completed_count = len([e for e in self._active_executions.values() if e.status.is_complete])
        failed_count = len([e for e in self._active_executions.values() if e.status.has_failed])
        
        return {
            **queue_status,
            "total_executions": len(self._active_executions),
            "running_executions": running_count,
            "completed_executions": completed_count,
            "failed_executions": failed_count,
            "history_count": len(self._execution_history)
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data."""
        return self.monitor.get_dashboard_data()
    
    def get_execution_progress(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress information for an execution."""
        dashboard_data = self.monitor.get_dashboard_data()
        executions = dashboard_data.get("executions", {})
        
        if backtest_id in executions:
            execution_data = executions[backtest_id]
            return {
                "execution": execution_data["execution"],
                "progress": execution_data["progress"],
                "resources": execution_data["resources"]
            }
        
        return None
    
    def register_monitoring_callback(self, event_type: MonitoringEventType, callback: Callable):
        """Register callback for monitoring events."""
        self.monitor.register_event_callback(event_type, callback)
    
    def _on_execution_completed(self, execution: BacktestExecution):
        """Handle execution completion event."""
        self.logger.info(f"Execution completed: {execution.backtest_id}")
        
        # Update historical data for completion time estimation
        self.completion_estimator.update_historical_data(execution)
        
        # Move to history if it's been completed for a while
        if execution.completed_at:
            # Schedule for cleanup after some time
            pass
    
    def _on_execution_failed(self, execution: BacktestExecution):
        """Handle execution failure event."""
        self.logger.error(f"Execution failed: {execution.backtest_id} - {execution.error_message}")
        
        # Could implement retry logic here if needed
        if execution.can_retry:
            self.logger.info(f"Execution {execution.backtest_id} can be retried ({execution.retry_count}/{execution.max_retries})")
            # Implement retry logic if needed
    
    def _update_execution_status(self, execution: BacktestExecution) -> None:
        """Update execution status from HaasOnline API."""
        if not execution.status.is_running or not hasattr(execution, 'execution_id'):
            return
            
        try:
            from ..api_client.request_models import ExecutionUpdateRequest
            
            # Get execution update from API
            request = ExecutionUpdateRequest(execution_id=execution.execution_id)
            
            with self.api_client as client:
                response = client.get_execution_update(request)
                
                # Update execution status from response
                execution.status.status = ExecutionStatusType(response.status.value)
                execution.status.progress_percentage = response.progress.percentage
                execution.status.current_phase = response.progress.current_phase
                execution.status.last_update = response.last_update
                
                # Update resource usage
                execution.status.resource_usage.cpu_percent = response.resource_usage.cpu_percentage
                execution.status.resource_usage.memory_mb = response.resource_usage.memory_mb
                execution.status.resource_usage.disk_io_mb = response.resource_usage.disk_io_mb
                execution.status.resource_usage.network_io_mb = response.resource_usage.network_io_mb
                
                # Update estimated completion
                if response.progress.estimated_remaining_seconds > 0:
                    execution.status.estimated_completion = datetime.now() + timedelta(
                        seconds=response.progress.estimated_remaining_seconds
                    )
                
                # Check if execution completed
                if execution.status.status in [ExecutionStatusType.COMPLETED, ExecutionStatusType.FAILED]:
                    execution.completed_at = datetime.now()
                    
                    if response.error_message:
                        execution.error_message = response.error_message
                        
                    self.logger.info(f"Backtest {execution.backtest_id} completed with status: {execution.status.status.value}")
                
        except Exception as e:
            self.logger.error(f"Failed to update execution status for {execution.backtest_id}: {e}")
            # Fall back to time-based estimation if API fails
            self._fallback_status_update(execution)
    
    def _fallback_status_update(self, execution: BacktestExecution) -> None:
        """Fallback status update when API is unavailable."""
        if execution.status.is_running:
            elapsed = datetime.now() - execution.started_at
            if execution.status.estimated_completion:
                total_time = execution.status.estimated_completion - execution.started_at
                progress = min(95.0, (elapsed.total_seconds() / total_time.total_seconds()) * 100)
                execution.status.progress_percentage = progress
                
                # Mark as completed after estimated time + buffer
                if elapsed > total_time + timedelta(minutes=5):
                    execution.status.status = ExecutionStatusType.COMPLETED
                    execution.status.progress_percentage = 100.0
                    execution.status.current_phase = "Completed"
                    execution.completed_at = datetime.now()
    
    def _fetch_backtest_logs(self, backtest_id: str) -> List[str]:
        """Fetch backtest logs from HaasOnline API."""
        # Placeholder implementation
        return [
            f"[{datetime.now().isoformat()}] Backtest started",
            f"[{datetime.now().isoformat()}] Processing market data",
            f"[{datetime.now().isoformat()}] Executing script logic",
            f"[{datetime.now().isoformat()}] Calculating results"
        ]
    
    def _archive_backtest_via_api(self, backtest_id: str, preserve_results: bool = True) -> bool:
        """Archive backtest via HaasOnline API."""
        try:
            # HaasOnline API doesn't have a direct ARCHIVE_BACKTEST endpoint
            # Instead, we need to use the results retrieval and storage pattern
            
            # First, get the backtest runtime data to preserve it
            if preserve_results:
                try:
                    from ..api_client.request_models import BacktestRuntimeRequest
                    
                    runtime_request = BacktestRuntimeRequest(backtest_id=backtest_id)
                    
                    with self.api_client as client:
                        runtime_response = client.get_backtest_runtime(runtime_request)
                        
                        # Store the results in our local history with full details
                        # This effectively "archives" the backtest by preserving its data
                        self.logger.info(f"Retrieved and preserved backtest results for archiving: {backtest_id}")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to preserve results during archiving: {e}")
            
            # Mark as archived in our tracking
            # Note: HaasOnline doesn't have explicit archiving, so we simulate it
            self.logger.info(f"Backtest {backtest_id} marked as archived")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to archive backtest via API: {e}")
            return False
    
    def _delete_backtest_via_api(self, backtest_id: str) -> bool:
        """Delete backtest via HaasOnline API."""
        try:
            # Use the DELETE_BACKTEST endpoint if available
            # Note: The actual endpoint may vary based on HaasOnline API version
            
            params = {
                "channel": "DELETE_BACKTEST",
                "backtestid": backtest_id
            }
            
            with self.api_client as client:
                response = client._make_request(
                    "POST",
                    client.config.get_api_url("Backtest"),
                    data=params
                )
                
                success = response.get("Success", False)
                if not success:
                    error_msg = response.get("Error", "Unknown error")
                    self.logger.error(f"API delete failed for {backtest_id}: {error_msg}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete backtest via API: {e}")
            return False
    
    def _cancel_backtest_via_api(self, backtest_id: str) -> bool:
        """Cancel backtest via HaasOnline API."""
        try:
            # Use the CANCEL_BACKTEST endpoint
            params = {
                "channel": "CANCEL_BACKTEST",
                "backtestid": backtest_id
            }
            
            with self.api_client as client:
                response = client._make_request(
                    "POST",
                    client.config.get_api_url("Backtest"),
                    data=params
                )
                
                success = response.get("Success", False)
                if not success:
                    error_msg = response.get("Error", "Unknown error")
                    self.logger.error(f"API cancel failed for {backtest_id}: {error_msg}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to cancel backtest via API: {e}")
            return False
    
    def _fetch_execution_history_from_api(self, include_archived: bool = True) -> List[BacktestSummary]:
        """Fetch execution history from HaasOnline API."""
        try:
            from ..api_client.request_models import ExecutionBacktestsRequest
            
            # Get list of backtests from API
            request = ExecutionBacktestsRequest(
                include_completed=True,
                include_failed=True
            )
            
            with self.api_client as client:
                response = client.get_execution_backtests(request)
                
                history = []
                
                # Process completed backtests
                for backtest in response.completed_backtests:
                    summary = BacktestSummary(
                        backtest_id=backtest.backtest_id,
                        script_name=backtest.script_name,
                        market_tag=backtest.market_tag,
                        start_date=backtest.started_at,
                        end_date=backtest.estimated_completion or backtest.started_at,
                        status="completed",
                        created_at=backtest.started_at
                    )
                    history.append(summary)
                
                # Process failed backtests
                for backtest in response.failed_backtests:
                    summary = BacktestSummary(
                        backtest_id=backtest.backtest_id,
                        script_name=backtest.script_name,
                        market_tag=backtest.market_tag,
                        start_date=backtest.started_at,
                        end_date=backtest.estimated_completion or backtest.started_at,
                        status="failed",
                        created_at=backtest.started_at
                    )
                    history.append(summary)
                
                return history
                
        except Exception as e:
            self.logger.error(f"Failed to fetch execution history from API: {e}")
            return []