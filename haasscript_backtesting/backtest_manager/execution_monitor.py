"""
Real-time execution monitoring and status tracking system.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from ..models import BacktestExecution, ExecutionStatus, ExecutionStatusType
from ..api_client import HaasOnlineClient
from ..api_client.request_models import ExecutionUpdateRequest, ExecutionBacktestsRequest


class MonitoringEventType(Enum):
    """Types of monitoring events."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"
    RESOURCE_THRESHOLD_EXCEEDED = "resource_threshold_exceeded"
    ESTIMATED_TIME_UPDATED = "estimated_time_updated"


@dataclass
class MonitoringEvent:
    """Represents a monitoring event."""
    event_type: MonitoringEventType
    backtest_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


@dataclass
class ProgressMetrics:
    """Progress tracking metrics."""
    current_percentage: float
    estimated_completion: Optional[datetime]
    processing_rate: float  # candles per second
    elapsed_time: timedelta
    remaining_time: Optional[timedelta]
    phase_durations: Dict[str, timedelta] = field(default_factory=dict)
    
    def update_phase_duration(self, phase: str, duration: timedelta):
        """Update duration for a specific phase."""
        self.phase_durations[phase] = duration
    
    def get_average_processing_rate(self) -> float:
        """Calculate average processing rate."""
        if self.elapsed_time.total_seconds() > 0:
            return self.current_percentage / self.elapsed_time.total_seconds()
        return 0.0


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    cpu_percentage: float
    memory_mb: float
    disk_io_mb: float
    network_io_mb: float
    active_connections: int
    peak_memory_mb: float = 0.0
    average_cpu_percentage: float = 0.0
    
    def update_peaks(self):
        """Update peak resource usage."""
        self.peak_memory_mb = max(self.peak_memory_mb, self.memory_mb)


class ExecutionStatusDashboard:
    """Real-time dashboard for execution status."""
    
    def __init__(self):
        self.executions: Dict[str, BacktestExecution] = {}
        self.progress_metrics: Dict[str, ProgressMetrics] = {}
        self.resource_metrics: Dict[str, ResourceMetrics] = {}
        self.event_history: List[MonitoringEvent] = []
        self.logger = logging.getLogger(f"{__name__}.Dashboard")
    
    def add_execution(self, execution: BacktestExecution):
        """Add execution to dashboard."""
        self.executions[execution.backtest_id] = execution
        
        # Initialize metrics
        self.progress_metrics[execution.backtest_id] = ProgressMetrics(
            current_percentage=0.0,
            estimated_completion=execution.status.estimated_completion,
            processing_rate=0.0,
            elapsed_time=timedelta(0),
            remaining_time=None
        )
        
        self.resource_metrics[execution.backtest_id] = ResourceMetrics(
            cpu_percentage=0.0,
            memory_mb=0.0,
            disk_io_mb=0.0,
            network_io_mb=0.0,
            active_connections=0
        )
        
        self._add_event(MonitoringEvent(
            event_type=MonitoringEventType.EXECUTION_STARTED,
            backtest_id=execution.backtest_id,
            message=f"Execution started for script {execution.script_id}"
        ))
    
    def update_execution(self, execution: BacktestExecution):
        """Update execution status in dashboard."""
        if execution.backtest_id not in self.executions:
            self.add_execution(execution)
            return
        
        old_execution = self.executions[execution.backtest_id]
        self.executions[execution.backtest_id] = execution
        
        # Update progress metrics
        progress = self.progress_metrics[execution.backtest_id]
        progress.current_percentage = execution.status.progress_percentage
        progress.estimated_completion = execution.status.estimated_completion
        progress.elapsed_time = datetime.now() - execution.started_at
        
        # Calculate remaining time
        if execution.status.estimated_completion:
            progress.remaining_time = execution.status.estimated_completion - datetime.now()
        
        # Update resource metrics
        resources = self.resource_metrics[execution.backtest_id]
        resources.cpu_percentage = execution.status.resource_usage.cpu_percent
        resources.memory_mb = execution.status.resource_usage.memory_mb
        resources.disk_io_mb = execution.status.resource_usage.disk_io_mb
        resources.network_io_mb = execution.status.resource_usage.network_io_mb
        resources.active_connections = execution.status.resource_usage.active_connections
        resources.update_peaks()
        
        # Generate events for status changes
        if old_execution.status.status != execution.status.status:
            if execution.status.status == ExecutionStatusType.COMPLETED:
                self._add_event(MonitoringEvent(
                    event_type=MonitoringEventType.EXECUTION_COMPLETED,
                    backtest_id=execution.backtest_id,
                    message=f"Execution completed successfully"
                ))
            elif execution.status.status == ExecutionStatusType.FAILED:
                self._add_event(MonitoringEvent(
                    event_type=MonitoringEventType.EXECUTION_FAILED,
                    backtest_id=execution.backtest_id,
                    message=f"Execution failed: {execution.error_message}",
                    data={"error": execution.error_message}
                ))
        
        # Generate progress events
        if abs(old_execution.status.progress_percentage - execution.status.progress_percentage) >= 10:
            self._add_event(MonitoringEvent(
                event_type=MonitoringEventType.EXECUTION_PROGRESS,
                backtest_id=execution.backtest_id,
                message=f"Progress: {execution.status.progress_percentage:.1f}%",
                data={"progress": execution.status.progress_percentage}
            ))
    
    def remove_execution(self, backtest_id: str):
        """Remove execution from dashboard."""
        if backtest_id in self.executions:
            del self.executions[backtest_id]
            del self.progress_metrics[backtest_id]
            del self.resource_metrics[backtest_id]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data."""
        return {
            "executions": {
                backtest_id: {
                    "execution": execution,
                    "progress": self.progress_metrics[backtest_id],
                    "resources": self.resource_metrics[backtest_id]
                }
                for backtest_id, execution in self.executions.items()
            },
            "summary": {
                "total_executions": len(self.executions),
                "running": len([e for e in self.executions.values() if e.status.is_running]),
                "completed": len([e for e in self.executions.values() if e.status.is_complete]),
                "failed": len([e for e in self.executions.values() if e.status.has_failed])
            },
            "recent_events": self.event_history[-10:]  # Last 10 events
        }
    
    def _add_event(self, event: MonitoringEvent):
        """Add event to history."""
        self.event_history.append(event)
        
        # Keep only last 1000 events
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-1000:]
        
        self.logger.info(f"Event: {event.event_type.value} - {event.message}")


class ExecutionMonitor:
    """Real-time execution monitoring system."""
    
    def __init__(self, api_client: HaasOnlineClient, update_interval: int = 30):
        """Initialize execution monitor.
        
        Args:
            api_client: HaasOnline API client
            update_interval: Update interval in seconds
        """
        self.api_client = api_client
        self.update_interval = update_interval
        self.logger = logging.getLogger(__name__)
        
        # Dashboard for real-time status
        self.dashboard = ExecutionStatusDashboard()
        
        # Event callbacks
        self.event_callbacks: Dict[MonitoringEventType, List[Callable]] = {
            event_type: [] for event_type in MonitoringEventType
        }
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._executions_to_monitor: Dict[str, BacktestExecution] = {}
        self._lock = threading.Lock()
        
        # Performance tracking
        self._last_update_time = datetime.now()
        self._update_count = 0
        self._error_count = 0
    
    def add_execution(self, execution: BacktestExecution):
        """Add execution to monitoring."""
        with self._lock:
            self._executions_to_monitor[execution.backtest_id] = execution
            self.dashboard.add_execution(execution)
        
        self.logger.info(f"Added execution to monitoring: {execution.backtest_id}")
        
        # Start monitoring if not already active
        if not self._monitoring_active:
            self.start_monitoring()
    
    def remove_execution(self, backtest_id: str):
        """Remove execution from monitoring."""
        with self._lock:
            if backtest_id in self._executions_to_monitor:
                del self._executions_to_monitor[backtest_id]
                self.dashboard.remove_execution(backtest_id)
        
        self.logger.info(f"Removed execution from monitoring: {backtest_id}")
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitoring_thread.start()
        self.logger.info("Started execution monitoring")
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self._monitoring_active = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=10)
        self.logger.info("Stopped execution monitoring")
    
    def register_event_callback(self, event_type: MonitoringEventType, callback: Callable):
        """Register callback for monitoring events."""
        self.event_callbacks[event_type].append(callback)
    
    def get_execution_status(self, backtest_id: str) -> Optional[BacktestExecution]:
        """Get current status of an execution."""
        with self._lock:
            return self._executions_to_monitor.get(backtest_id)
    
    def get_all_executions(self) -> Dict[str, BacktestExecution]:
        """Get all monitored executions."""
        with self._lock:
            return self._executions_to_monitor.copy()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data with monitoring statistics."""
        dashboard_data = self.dashboard.get_dashboard_data()
        
        # Add monitoring statistics
        dashboard_data["monitoring_stats"] = {
            "active": self._monitoring_active,
            "update_interval": self.update_interval,
            "last_update": self._last_update_time,
            "update_count": self._update_count,
            "error_count": self._error_count,
            "monitored_executions": len(self._executions_to_monitor)
        }
        
        return dashboard_data
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                start_time = time.time()
                
                # Update all monitored executions
                self._update_all_executions()
                
                # Update performance metrics
                self._update_count += 1
                self._last_update_time = datetime.now()
                
                # Calculate sleep time to maintain interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Monitoring update took {elapsed:.2f}s, longer than interval {self.update_interval}s")
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self._error_count += 1
                time.sleep(min(60, self.update_interval * 2))  # Back off on error
    
    def _update_all_executions(self):
        """Update status for all monitored executions."""
        with self._lock:
            executions_to_update = list(self._executions_to_monitor.values())
        
        for execution in executions_to_update:
            try:
                if execution.status.is_running and hasattr(execution, 'execution_id'):
                    self._update_single_execution(execution)
            except Exception as e:
                self.logger.error(f"Failed to update execution {execution.backtest_id}: {e}")
    
    def _update_single_execution(self, execution: BacktestExecution):
        """Update status for a single execution."""
        try:
            request = ExecutionUpdateRequest(execution_id=execution.execution_id)
            
            with self.api_client as client:
                response = client.get_execution_update(request)
                
                # Update execution status
                old_status = execution.status.status
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
                
                # Mark as completed if status changed
                if execution.status.status in [ExecutionStatusType.COMPLETED, ExecutionStatusType.FAILED]:
                    execution.completed_at = datetime.now()
                    
                    if response.error_message:
                        execution.error_message = response.error_message
                
                # Update dashboard
                self.dashboard.update_execution(execution)
                
                # Trigger callbacks for status changes
                if old_status != execution.status.status:
                    self._trigger_status_change_callbacks(execution, old_status)
                
        except Exception as e:
            self.logger.error(f"Failed to update execution {execution.backtest_id}: {e}")
            raise
    
    def _trigger_status_change_callbacks(self, execution: BacktestExecution, old_status: ExecutionStatusType):
        """Trigger callbacks for status changes."""
        event_type = None
        
        if execution.status.status == ExecutionStatusType.COMPLETED:
            event_type = MonitoringEventType.EXECUTION_COMPLETED
        elif execution.status.status == ExecutionStatusType.FAILED:
            event_type = MonitoringEventType.EXECUTION_FAILED
        elif execution.status.status == ExecutionStatusType.CANCELLED:
            event_type = MonitoringEventType.EXECUTION_CANCELLED
        
        if event_type and event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(execution)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")


class CompletionTimeEstimator:
    """Estimates completion time for backtest executions."""
    
    def __init__(self):
        self.historical_data: Dict[str, List[float]] = {}  # script_id -> [duration_per_day]
        self.logger = logging.getLogger(f"{__name__}.Estimator")
    
    def estimate_completion_time(self, execution: BacktestExecution) -> Optional[datetime]:
        """Estimate completion time for an execution."""
        try:
            # Get historical data for this script
            script_id = execution.script_id
            duration_days = execution.config.duration_days
            
            if script_id in self.historical_data and self.historical_data[script_id]:
                # Use historical average
                avg_duration_per_day = sum(self.historical_data[script_id]) / len(self.historical_data[script_id])
                estimated_total_minutes = avg_duration_per_day * duration_days
            else:
                # Use default estimation
                estimated_total_minutes = self._default_estimation(duration_days)
            
            return execution.started_at + timedelta(minutes=estimated_total_minutes)
            
        except Exception as e:
            self.logger.error(f"Error estimating completion time: {e}")
            return None
    
    def update_historical_data(self, execution: BacktestExecution):
        """Update historical data with completed execution."""
        if not execution.completed_at or not execution.status.is_complete:
            return
        
        try:
            script_id = execution.script_id
            duration_days = execution.config.duration_days
            actual_duration = execution.completed_at - execution.started_at
            duration_per_day = actual_duration.total_seconds() / 60 / duration_days  # minutes per day
            
            if script_id not in self.historical_data:
                self.historical_data[script_id] = []
            
            self.historical_data[script_id].append(duration_per_day)
            
            # Keep only last 10 data points
            if len(self.historical_data[script_id]) > 10:
                self.historical_data[script_id] = self.historical_data[script_id][-10:]
            
            self.logger.info(f"Updated historical data for script {script_id}: {duration_per_day:.2f} min/day")
            
        except Exception as e:
            self.logger.error(f"Error updating historical data: {e}")
    
    def _default_estimation(self, duration_days: int) -> float:
        """Default estimation when no historical data is available."""
        # Base estimation: 2 minutes per day + overhead
        base_minutes = duration_days * 2
        overhead_minutes = min(10, duration_days * 0.5)  # Up to 10 minutes overhead
        return base_minutes + overhead_minutes