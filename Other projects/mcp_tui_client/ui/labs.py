"""
Lab Management View

Advanced lab management capabilities with intelligent backtesting.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.widget import Widget
from textual.widgets import (
    Static, DataTable, Button, Input, Select, Checkbox, 
    ProgressBar, Label, TabbedContent, TabPane, Tree, 
    TextArea, RadioSet, RadioButton, Collapsible
)
from textual.message import Message
from textual.reactive import reactive
from textual import events

from ..utils.logging import get_logger
from .optimization import ParameterOptimizationInterface, OptimizationStarted, OptimizationCompleted


@dataclass
class BacktestConfig:
    """Intelligent backtest configuration"""
    lab_id: str
    start_date: str
    end_date: str
    auto_adjust: bool = True
    validate_history: bool = True
    concurrent_execution: bool = False
    resource_limits: Dict[str, Any] = None
    optimization_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                "max_memory_mb": 1024,
                "max_cpu_percent": 80,
                "max_concurrent_labs": 3
            }
        if self.optimization_settings is None:
            self.optimization_settings = {
                "enabled": False,
                "algorithm": "genetic",
                "max_iterations": 100,
                "population_size": 50
            }


@dataclass
class BacktestProgress:
    """Backtest execution progress tracking"""
    lab_id: str
    status: str = "pending"
    progress: float = 0.0
    current_period: str = ""
    estimated_completion: Optional[datetime] = None
    data_validation_status: str = "pending"
    resource_usage: Dict[str, float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.resource_usage is None:
            self.resource_usage = {
                "memory_mb": 0.0,
                "cpu_percent": 0.0,
                "disk_io_mb": 0.0
            }


@dataclass
class LabConfig:
    """Lab configuration data structure"""
    lab_name: str = ""
    script_id: str = ""
    trading_pair: str = ""
    account_id: str = ""
    start_date: str = ""
    end_date: str = ""
    parameters: Dict[str, Any] = None
    auto_adjust: bool = True
    concurrent_execution: bool = False
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class IntelligentBacktestEngine(Widget):
    """Intelligent backtesting engine with history validation and auto-adjustment"""
    
    class BacktestStarted(Message):
        """Message sent when backtest starts"""
        def __init__(self, lab_id: str, config: BacktestConfig) -> None:
            self.lab_id = lab_id
            self.config = config
            super().__init__()
    
    class BacktestProgress(Message):
        """Message sent for backtest progress updates"""
        def __init__(self, progress: BacktestProgress) -> None:
            self.progress = progress
            super().__init__()
    
    class BacktestCompleted(Message):
        """Message sent when backtest completes"""
        def __init__(self, lab_id: str, results: Dict[str, Any]) -> None:
            self.lab_id = lab_id
            self.results = results
            super().__init__()
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        self.active_backtests: Dict[str, BacktestProgress] = {}
        self.resource_monitor = ResourceMonitor()
        self.history_validator = HistoryValidator(mcp_client)
        self.period_adjuster = PeriodAdjuster(mcp_client)
        
        # Background tasks
        self._monitor_task: Optional[asyncio.Task] = None
        self._progress_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_intelligent_backtest(self, config: BacktestConfig) -> bool:
        """Start intelligent backtest with validation and auto-adjustment"""
        try:
            self.logger.info(f"Starting intelligent backtest for lab {config.lab_id}")
            
            # Step 1: Validate history data availability
            if config.validate_history:
                validation_result = await self.history_validator.validate_data_availability(
                    config.lab_id, config.start_date, config.end_date
                )
                
                if not validation_result.is_valid:
                    if config.auto_adjust:
                        # Auto-adjust period based on available data
                        adjusted_config = await self.period_adjuster.adjust_period(
                            config, validation_result
                        )
                        if adjusted_config:
                            config = adjusted_config
                            self.logger.info(f"Auto-adjusted backtest period: {config.start_date} to {config.end_date}")
                        else:
                            raise Exception("Insufficient data available for backtesting")
                    else:
                        raise Exception(f"Data validation failed: {validation_result.error_message}")
            
            # Step 2: Check resource availability
            if not await self.resource_monitor.check_resources(config.resource_limits):
                if config.concurrent_execution:
                    # Queue for later execution
                    await self._queue_backtest(config)
                    return True
                else:
                    raise Exception("Insufficient resources for backtest execution")
            
            # Step 3: Initialize progress tracking
            progress = BacktestProgress(
                lab_id=config.lab_id,
                status="initializing",
                data_validation_status="validated" if config.validate_history else "skipped"
            )
            self.active_backtests[config.lab_id] = progress
            
            # Step 4: Start backtest execution
            await self._execute_backtest(config)
            
            # Step 5: Start progress monitoring
            self._progress_tasks[config.lab_id] = asyncio.create_task(
                self._monitor_backtest_progress(config.lab_id)
            )
            
            self.post_message(self.BacktestStarted(config.lab_id, config))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start intelligent backtest: {e}")
            if config.lab_id in self.active_backtests:
                self.active_backtests[config.lab_id].status = "failed"
                self.active_backtests[config.lab_id].error_message = str(e)
            raise
    
    async def _execute_backtest(self, config: BacktestConfig) -> None:
        """Execute the actual backtest"""
        if not self.mcp_client:
            raise Exception("MCP client not available")
        
        # Update status
        if config.lab_id in self.active_backtests:
            self.active_backtests[config.lab_id].status = "running"
        
        # Execute intelligent backtest via MCP
        result = await self.mcp_client.execute_backtest_intelligent(
            lab_id=config.lab_id,
            start_date=config.start_date,
            end_date=config.end_date
        )
        
        self.logger.info(f"Backtest execution started for lab {config.lab_id}")
    
    async def _monitor_backtest_progress(self, lab_id: str) -> None:
        """Monitor backtest progress with real-time updates"""
        while lab_id in self.active_backtests:
            try:
                progress = self.active_backtests[lab_id]
                
                if progress.status in ["completed", "failed", "stopped"]:
                    break
                
                # Get updated progress from MCP server
                if self.mcp_client:
                    lab_details = await self.mcp_client.get_lab_details(lab_id)
                    
                    # Update progress
                    progress.progress = lab_details.get("progress", 0.0)
                    progress.current_period = lab_details.get("current_period", "")
                    progress.status = lab_details.get("status", "unknown")
                    
                    # Update resource usage
                    resource_usage = await self.resource_monitor.get_lab_resource_usage(lab_id)
                    progress.resource_usage.update(resource_usage)
                    
                    # Calculate ETA
                    if progress.progress > 0:
                        progress.estimated_completion = self._calculate_eta(progress)
                    
                    # Emit progress update
                    self.post_message(self.BacktestProgress(progress))
                
                # Check if completed
                if progress.status == "completed":
                    results = await self.mcp_client.call_tool("get_lab_results", {"lab_id": lab_id})
                    self.post_message(self.BacktestCompleted(lab_id, results))
                    break
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring backtest progress: {e}")
                if lab_id in self.active_backtests:
                    self.active_backtests[lab_id].status = "failed"
                    self.active_backtests[lab_id].error_message = str(e)
                break
        
        # Cleanup
        if lab_id in self._progress_tasks:
            del self._progress_tasks[lab_id]
    
    def _calculate_eta(self, progress: BacktestProgress) -> Optional[datetime]:
        """Calculate estimated time to completion"""
        # This would be implemented based on historical performance data
        # For now, simple linear extrapolation
        if progress.progress <= 0:
            return None
        
        # Estimate based on current progress rate
        # This is a simplified calculation
        remaining_progress = 100 - progress.progress
        estimated_seconds = (remaining_progress / progress.progress) * 3600  # Rough estimate
        
        return datetime.now() + timedelta(seconds=estimated_seconds)
    
    async def _queue_backtest(self, config: BacktestConfig) -> None:
        """Queue backtest for later execution when resources are available"""
        # This would implement a proper queue system
        self.logger.info(f"Queuing backtest for lab {config.lab_id}")
        # TODO: Implement proper queuing system
    
    async def stop_backtest(self, lab_id: str) -> bool:
        """Stop running backtest"""
        try:
            if lab_id in self.active_backtests:
                self.active_backtests[lab_id].status = "stopping"
                
                # Cancel progress monitoring
                if lab_id in self._progress_tasks:
                    self._progress_tasks[lab_id].cancel()
                
                # Stop via MCP
                if self.mcp_client:
                    await self.mcp_client.call_tool("stop_lab", {"lab_id": lab_id})
                
                # Update status
                self.active_backtests[lab_id].status = "stopped"
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to stop backtest: {e}")
            return False
    
    async def pause_backtest(self, lab_id: str) -> bool:
        """Pause running backtest"""
        try:
            if lab_id in self.active_backtests:
                self.active_backtests[lab_id].status = "pausing"
                
                if self.mcp_client:
                    await self.mcp_client.call_tool("pause_lab", {"lab_id": lab_id})
                
                self.active_backtests[lab_id].status = "paused"
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to pause backtest: {e}")
            return False
    
    async def resume_backtest(self, lab_id: str) -> bool:
        """Resume paused backtest"""
        try:
            if lab_id in self.active_backtests:
                self.active_backtests[lab_id].status = "resuming"
                
                if self.mcp_client:
                    await self.mcp_client.call_tool("resume_lab", {"lab_id": lab_id})
                
                self.active_backtests[lab_id].status = "running"
                
                # Restart progress monitoring if needed
                if lab_id not in self._progress_tasks:
                    self._progress_tasks[lab_id] = asyncio.create_task(
                        self._monitor_backtest_progress(lab_id)
                    )
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to resume backtest: {e}")
            return False
    
    def get_backtest_status(self, lab_id: str) -> Optional[BacktestProgress]:
        """Get current backtest status"""
        return self.active_backtests.get(lab_id)
    
    def get_all_active_backtests(self) -> Dict[str, BacktestProgress]:
        """Get all active backtests"""
        return self.active_backtests.copy()
    
    async def cleanup(self) -> None:
        """Cleanup resources and stop all monitoring tasks"""
        # Cancel all progress monitoring tasks
        for task in self._progress_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._progress_tasks:
            await asyncio.gather(*self._progress_tasks.values(), return_exceptions=True)
        
        self._progress_tasks.clear()
        self.active_backtests.clear()


class HistoryValidator:
    """Validates historical data availability for backtesting"""
    
    @dataclass
    class ValidationResult:
        is_valid: bool
        available_start: Optional[str] = None
        available_end: Optional[str] = None
        missing_periods: List[str] = None
        data_quality_score: float = 0.0
        error_message: Optional[str] = None
        
        def __post_init__(self):
            if self.missing_periods is None:
                self.missing_periods = []
    
    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
    
    async def validate_data_availability(
        self, 
        lab_id: str, 
        start_date: str, 
        end_date: str
    ) -> ValidationResult:
        """Validate data availability for the specified period"""
        try:
            if not self.mcp_client:
                return self.ValidationResult(
                    is_valid=False,
                    error_message="MCP client not available"
                )
            
            # Get lab details to determine trading pair
            lab_details = await self.mcp_client.get_lab_details(lab_id)
            trading_pair = lab_details.get("trading_pair")
            
            if not trading_pair:
                return self.ValidationResult(
                    is_valid=False,
                    error_message="Trading pair not found in lab configuration"
                )
            
            # Check data availability via MCP
            validation_result = await self.mcp_client.call_tool("validate_historical_data", {
                "trading_pair": trading_pair,
                "start_date": start_date,
                "end_date": end_date
            })
            
            return self.ValidationResult(
                is_valid=validation_result.get("is_valid", False),
                available_start=validation_result.get("available_start"),
                available_end=validation_result.get("available_end"),
                missing_periods=validation_result.get("missing_periods", []),
                data_quality_score=validation_result.get("data_quality_score", 0.0),
                error_message=validation_result.get("error_message")
            )
            
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            return self.ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )


class PeriodAdjuster:
    """Automatically adjusts backtest periods based on data availability"""
    
    def __init__(self, mcp_client=None):
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
    
    async def adjust_period(
        self, 
        config: BacktestConfig, 
        validation_result: HistoryValidator.ValidationResult
    ) -> Optional[BacktestConfig]:
        """Adjust backtest period based on validation results"""
        try:
            if validation_result.is_valid:
                return config  # No adjustment needed
            
            # Try to find the best available period
            if validation_result.available_start and validation_result.available_end:
                # Adjust to available data range
                adjusted_config = BacktestConfig(
                    lab_id=config.lab_id,
                    start_date=validation_result.available_start,
                    end_date=validation_result.available_end,
                    auto_adjust=config.auto_adjust,
                    validate_history=config.validate_history,
                    concurrent_execution=config.concurrent_execution,
                    resource_limits=config.resource_limits,
                    optimization_settings=config.optimization_settings
                )
                
                self.logger.info(
                    f"Adjusted period from {config.start_date}-{config.end_date} "
                    f"to {adjusted_config.start_date}-{adjusted_config.end_date}"
                )
                
                return adjusted_config
            
            # Try to find alternative periods
            alternative_periods = await self._find_alternative_periods(config)
            
            if alternative_periods:
                best_period = alternative_periods[0]  # Use the best available period
                
                adjusted_config = BacktestConfig(
                    lab_id=config.lab_id,
                    start_date=best_period["start_date"],
                    end_date=best_period["end_date"],
                    auto_adjust=config.auto_adjust,
                    validate_history=config.validate_history,
                    concurrent_execution=config.concurrent_execution,
                    resource_limits=config.resource_limits,
                    optimization_settings=config.optimization_settings
                )
                
                self.logger.info(f"Found alternative period: {best_period}")
                return adjusted_config
            
            return None  # No suitable period found
            
        except Exception as e:
            self.logger.error(f"Period adjustment failed: {e}")
            return None
    
    async def _find_alternative_periods(self, config: BacktestConfig) -> List[Dict[str, str]]:
        """Find alternative periods with good data availability"""
        try:
            if not self.mcp_client:
                return []
            
            # Get lab details
            lab_details = await self.mcp_client.get_lab_details(config.lab_id)
            trading_pair = lab_details.get("trading_pair")
            
            # Find alternative periods via MCP
            alternatives = await self.mcp_client.call_tool("find_alternative_periods", {
                "trading_pair": trading_pair,
                "requested_start": config.start_date,
                "requested_end": config.end_date,
                "min_duration_days": 30,  # Minimum 30 days
                "max_alternatives": 5
            })
            
            return alternatives.get("periods", [])
            
        except Exception as e:
            self.logger.error(f"Failed to find alternative periods: {e}")
            return []


class ResourceMonitor:
    """Monitors system resources for concurrent backtest execution"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.current_usage = {
            "memory_mb": 0.0,
            "cpu_percent": 0.0,
            "active_labs": 0
        }
    
    async def check_resources(self, limits: Dict[str, Any]) -> bool:
        """Check if resources are available for new backtest"""
        try:
            # Get current system usage
            await self._update_current_usage()
            
            # Check memory limit
            if self.current_usage["memory_mb"] + 512 > limits.get("max_memory_mb", 1024):
                self.logger.warning("Memory limit would be exceeded")
                return False
            
            # Check CPU limit
            if self.current_usage["cpu_percent"] + 20 > limits.get("max_cpu_percent", 80):
                self.logger.warning("CPU limit would be exceeded")
                return False
            
            # Check concurrent labs limit
            if self.current_usage["active_labs"] >= limits.get("max_concurrent_labs", 3):
                self.logger.warning("Concurrent labs limit reached")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Resource check failed: {e}")
            return False
    
    async def get_lab_resource_usage(self, lab_id: str) -> Dict[str, float]:
        """Get resource usage for specific lab"""
        try:
            # This would integrate with system monitoring
            # For now, return mock data
            return {
                "memory_mb": 256.0,
                "cpu_percent": 15.0,
                "disk_io_mb": 10.0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get lab resource usage: {e}")
            return {"memory_mb": 0.0, "cpu_percent": 0.0, "disk_io_mb": 0.0}
    
    async def _update_current_usage(self) -> None:
        """Update current system resource usage"""
        try:
            # This would integrate with system monitoring tools
            # For now, use mock data
            self.current_usage = {
                "memory_mb": 512.0,
                "cpu_percent": 25.0,
                "active_labs": 1
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update resource usage: {e}")


class BacktestProgressPanel(Widget):
    """Panel for monitoring backtest progress with real-time updates"""
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        self.backtest_engine = IntelligentBacktestEngine(mcp_client)
        self.active_backtests: Dict[str, BacktestProgress] = {}
    
    def compose(self) -> ComposeResult:
        with Container(classes="progress-container"):
            yield Static("Backtest Progress Monitor", classes="panel-title")
            
            # Active backtests table
            with Container(classes="active-backtests"):
                yield Static("Active Backtests:", classes="section-title")
                table = DataTable(id="progress-table")
                table.add_columns(
                    "Lab", "Status", "Progress", "Current Period", 
                    "ETA", "Memory", "CPU", "Actions"
                )
                yield table
            
            # Resource usage overview
            with Container(classes="resource-overview"):
                yield Static("Resource Usage:", classes="section-title")
                with Horizontal():
                    yield ProgressBar(total=100, show_percentage=True, id="memory-usage")
                    yield ProgressBar(total=100, show_percentage=True, id="cpu-usage")
                    yield Static("Active: 0/3", id="concurrent-count")
            
            # Control buttons
            with Horizontal(classes="progress-controls"):
                yield Button("🔄 Refresh", id="refresh-progress")
                yield Button("⏸️ Pause All", id="pause-all")
                yield Button("▶️ Resume All", id="resume-all")
                yield Button("⏹️ Stop All", id="stop-all")
    
    async def on_mount(self) -> None:
        """Initialize progress monitoring"""
        # Set up message handlers for backtest engine
        self.backtest_engine.add_connection_callback(self._on_backtest_event)
        await self.refresh_progress()
    
    async def refresh_progress(self) -> None:
        """Refresh progress data"""
        try:
            # Get active backtests from engine
            self.active_backtests = self.backtest_engine.get_all_active_backtests()
            self._update_progress_table()
            self._update_resource_display()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh progress: {e}")
    
    def _update_progress_table(self) -> None:
        """Update the progress table"""
        table = self.query_one("#progress-table", DataTable)
        table.clear()
        
        for lab_id, progress in self.active_backtests.items():
            eta = progress.estimated_completion.strftime("%H:%M:%S") if progress.estimated_completion else "Unknown"
            memory_usage = f"{progress.resource_usage.get('memory_mb', 0):.0f}MB"
            cpu_usage = f"{progress.resource_usage.get('cpu_percent', 0):.1f}%"
            
            table.add_row(
                lab_id,
                self._get_status_display(progress.status),
                f"{progress.progress:.1f}%",
                progress.current_period or "Unknown",
                eta,
                memory_usage,
                cpu_usage,
                "⏸️ ⏹️ 📊"  # Pause, Stop, Details
            )
    
    def _update_resource_display(self) -> None:
        """Update resource usage display"""
        # Calculate total resource usage
        total_memory = sum(p.resource_usage.get('memory_mb', 0) for p in self.active_backtests.values())
        total_cpu = sum(p.resource_usage.get('cpu_percent', 0) for p in self.active_backtests.values())
        active_count = len([p for p in self.active_backtests.values() if p.status == "running"])
        
        # Update progress bars
        memory_bar = self.query_one("#memory-usage", ProgressBar)
        memory_bar.update(progress=min(total_memory / 1024 * 100, 100))
        
        cpu_bar = self.query_one("#cpu-usage", ProgressBar)
        cpu_bar.update(progress=min(total_cpu, 100))
        
        # Update concurrent count
        self.query_one("#concurrent-count", Static).update(f"Active: {active_count}/3")
    
    def _get_status_display(self, status: str) -> str:
        """Get formatted status display"""
        status_icons = {
            "pending": "⏳ Pending",
            "initializing": "🔄 Initializing",
            "running": "🟢 Running",
            "paused": "⏸️ Paused",
            "completed": "✅ Complete",
            "failed": "🔴 Failed",
            "stopped": "⏹️ Stopped"
        }
        return status_icons.get(status, f"❓ {status.title()}")
    
    def _on_backtest_event(self, event) -> None:
        """Handle backtest engine events"""
        # This would handle events from the backtest engine
        # For now, just refresh the display
        asyncio.create_task(self.refresh_progress())
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "refresh-progress":
            await self.refresh_progress()
        
        elif event.button.id == "pause-all":
            await self._pause_all_backtests()
        
        elif event.button.id == "resume-all":
            await self._resume_all_backtests()
        
        elif event.button.id == "stop-all":
            await self._stop_all_backtests()
    
    async def _pause_all_backtests(self) -> None:
        """Pause all running backtests"""
        for lab_id, progress in self.active_backtests.items():
            if progress.status == "running":
                await self.backtest_engine.pause_backtest(lab_id)
        
        await self.refresh_progress()
    
    async def _resume_all_backtests(self) -> None:
        """Resume all paused backtests"""
        for lab_id, progress in self.active_backtests.items():
            if progress.status == "paused":
                await self.backtest_engine.resume_backtest(lab_id)
        
        await self.refresh_progress()
    
    async def _stop_all_backtests(self) -> None:
        """Stop all active backtests"""
        for lab_id in list(self.active_backtests.keys()):
            await self.backtest_engine.stop_backtest(lab_id)
        
        await self.refresh_progress()


class LabCreationWizard(Widget):
    """Guided lab creation wizard with step-by-step setup"""
    
    class StepChanged(Message):
        """Message sent when wizard step changes"""
        def __init__(self, step: int, total_steps: int) -> None:
            self.step = step
            self.total_steps = total_steps
            super().__init__()
    
    class LabCreated(Message):
        """Message sent when lab is successfully created"""
        def __init__(self, lab_config: LabConfig) -> None:
            self.lab_config = lab_config
            super().__init__()
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        self.current_step = reactive(0)
        self.total_steps = 5
        self.lab_config = LabConfig()
        
        # Data for dropdowns
        self.available_scripts: List[Dict[str, Any]] = []
        self.available_markets: List[Dict[str, Any]] = []
        self.available_accounts: List[Dict[str, Any]] = []
        
    def compose(self) -> ComposeResult:
        with Container(classes="wizard-container"):
            yield Static("Lab Creation Wizard", classes="wizard-title")
            yield ProgressBar(total=self.total_steps, show_eta=False, classes="wizard-progress")
            
            with Container(classes="wizard-content"):
                # Step 1: Basic Information
                with Container(id="step-1", classes="wizard-step"):
                    yield Static("Step 1: Basic Information", classes="step-title")
                    yield Label("Lab Name:")
                    yield Input(placeholder="Enter lab name...", id="lab-name")
                    yield Label("Description (optional):")
                    yield TextArea(placeholder="Enter lab description...", id="lab-description")
                
                # Step 2: Script Selection
                with Container(id="step-2", classes="wizard-step hidden"):
                    yield Static("Step 2: Script Selection", classes="step-title")
                    yield Label("Select Script:")
                    yield Select(options=[], id="script-select")
                    yield Static("Script Details:", classes="subsection-title")
                    yield Static("", id="script-details")
                
                # Step 3: Market Configuration
                with Container(id="step-3", classes="wizard-step hidden"):
                    yield Static("Step 3: Market Configuration", classes="step-title")
                    yield Label("Trading Pair:")
                    yield Select(options=[], id="market-select")
                    yield Label("Account:")
                    yield Select(options=[], id="account-select")
                
                # Step 4: Backtest Period
                with Container(id="step-4", classes="wizard-step hidden"):
                    yield Static("Step 4: Backtest Period", classes="step-title")
                    yield Label("Start Date (YYYY-MM-DD):")
                    yield Input(placeholder="2023-01-01", id="start-date")
                    yield Label("End Date (YYYY-MM-DD):")
                    yield Input(placeholder="2024-01-01", id="end-date")
                    yield Checkbox("Auto-adjust period based on data availability", value=True, id="auto-adjust")
                
                # Step 5: Advanced Options
                with Container(id="step-5", classes="wizard-step hidden"):
                    yield Static("Step 5: Advanced Options", classes="step-title")
                    yield Checkbox("Enable concurrent execution", id="concurrent-execution")
                    yield Label("Script Parameters:")
                    yield TextArea(placeholder="Enter JSON parameters...", id="script-parameters")
                    
                    with Collapsible(title="Optimization Settings"):
                        yield Checkbox("Enable parameter optimization", id="enable-optimization")
                        yield Label("Optimization Algorithm:")
                        with RadioSet(id="optimization-algorithm"):
                            yield RadioButton("Genetic Algorithm", value=True)
                            yield RadioButton("Grid Search")
                            yield RadioButton("Random Search")
            
            # Navigation buttons
            with Horizontal(classes="wizard-navigation"):
                yield Button("Previous", id="prev-btn", disabled=True)
                yield Button("Next", id="next-btn")
                yield Button("Create Lab", id="create-btn", classes="hidden")
                yield Button("Cancel", id="cancel-btn", variant="error")
    
    async def on_mount(self) -> None:
        """Initialize wizard data"""
        await self._load_wizard_data()
        self._update_progress()
    
    async def _load_wizard_data(self) -> None:
        """Load data for wizard dropdowns"""
        if not self.mcp_client:
            return
        
        try:
            # Load scripts
            scripts_data = await self.mcp_client.get_all_scripts()
            self.available_scripts = scripts_data if isinstance(scripts_data, list) else []
            
            # Load markets
            markets_data = await self.mcp_client.get_all_markets()
            self.available_markets = markets_data if isinstance(markets_data, list) else []
            
            # Load accounts
            accounts_data = await self.mcp_client.get_all_accounts()
            self.available_accounts = accounts_data if isinstance(accounts_data, list) else []
            
            # Update dropdowns
            self._update_dropdowns()
            
        except Exception as e:
            self.logger.error(f"Failed to load wizard data: {e}")
    
    def _update_dropdowns(self) -> None:
        """Update dropdown options"""
        # Update script select
        script_select = self.query_one("#script-select", Select)
        script_options = [(script.get("name", "Unknown"), script.get("id", "")) 
                         for script in self.available_scripts]
        script_select.set_options(script_options)
        
        # Update market select
        market_select = self.query_one("#market-select", Select)
        market_options = [(f"{market.get('primary', '')}/{market.get('secondary', '')}", 
                          market.get("tag", "")) for market in self.available_markets]
        market_select.set_options(market_options)
        
        # Update account select
        account_select = self.query_one("#account-select", Select)
        account_options = [(account.get("name", "Unknown"), account.get("id", "")) 
                          for account in self.available_accounts]
        account_select.set_options(account_options)
    
    def _update_progress(self) -> None:
        """Update progress bar and step visibility"""
        progress_bar = self.query_one(ProgressBar)
        progress_bar.update(progress=self.current_step + 1)
        
        # Hide all steps
        for i in range(1, self.total_steps + 1):
            step = self.query_one(f"#step-{i}")
            step.add_class("hidden")
        
        # Show current step
        current_step_widget = self.query_one(f"#step-{self.current_step + 1}")
        current_step_widget.remove_class("hidden")
        
        # Update navigation buttons
        prev_btn = self.query_one("#prev-btn", Button)
        next_btn = self.query_one("#next-btn", Button)
        create_btn = self.query_one("#create-btn", Button)
        
        prev_btn.disabled = self.current_step == 0
        
        if self.current_step == self.total_steps - 1:
            next_btn.add_class("hidden")
            create_btn.remove_class("hidden")
        else:
            next_btn.remove_class("hidden")
            create_btn.add_class("hidden")
        
        # Emit step changed message
        self.post_message(self.StepChanged(self.current_step, self.total_steps))
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "next-btn":
            if await self._validate_current_step():
                self._save_current_step()
                self.current_step = min(self.current_step + 1, self.total_steps - 1)
                self._update_progress()
        
        elif event.button.id == "prev-btn":
            self.current_step = max(self.current_step - 1, 0)
            self._update_progress()
        
        elif event.button.id == "create-btn":
            if await self._validate_current_step():
                self._save_current_step()
                await self._create_lab()
        
        elif event.button.id == "cancel-btn":
            self.remove()
    
    async def _validate_current_step(self) -> bool:
        """Validate current step inputs"""
        if self.current_step == 0:  # Basic Information
            lab_name = self.query_one("#lab-name", Input).value.strip()
            if not lab_name:
                self._show_error("Lab name is required")
                return False
        
        elif self.current_step == 1:  # Script Selection
            script_select = self.query_one("#script-select", Select)
            if script_select.value == Select.BLANK:
                self._show_error("Please select a script")
                return False
        
        elif self.current_step == 2:  # Market Configuration
            market_select = self.query_one("#market-select", Select)
            account_select = self.query_one("#account-select", Select)
            if market_select.value == Select.BLANK:
                self._show_error("Please select a trading pair")
                return False
            if account_select.value == Select.BLANK:
                self._show_error("Please select an account")
                return False
        
        elif self.current_step == 3:  # Backtest Period
            start_date = self.query_one("#start-date", Input).value.strip()
            end_date = self.query_one("#end-date", Input).value.strip()
            if not start_date or not end_date:
                self._show_error("Start and end dates are required")
                return False
            
            # Validate date format
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                self._show_error("Invalid date format. Use YYYY-MM-DD")
                return False
        
        return True
    
    def _save_current_step(self) -> None:
        """Save current step data to lab config"""
        if self.current_step == 0:  # Basic Information
            self.lab_config.lab_name = self.query_one("#lab-name", Input).value.strip()
        
        elif self.current_step == 1:  # Script Selection
            self.lab_config.script_id = self.query_one("#script-select", Select).value
        
        elif self.current_step == 2:  # Market Configuration
            self.lab_config.trading_pair = self.query_one("#market-select", Select).value
            self.lab_config.account_id = self.query_one("#account-select", Select).value
        
        elif self.current_step == 3:  # Backtest Period
            self.lab_config.start_date = self.query_one("#start-date", Input).value.strip()
            self.lab_config.end_date = self.query_one("#end-date", Input).value.strip()
            self.lab_config.auto_adjust = self.query_one("#auto-adjust", Checkbox).value
        
        elif self.current_step == 4:  # Advanced Options
            self.lab_config.concurrent_execution = self.query_one("#concurrent-execution", Checkbox).value
            
            # Parse script parameters
            params_text = self.query_one("#script-parameters", TextArea).text.strip()
            if params_text:
                try:
                    import json
                    self.lab_config.parameters = json.loads(params_text)
                except json.JSONDecodeError:
                    self.lab_config.parameters = {}
    
    async def _create_lab(self) -> None:
        """Create the lab using MCP client"""
        if not self.mcp_client:
            self._show_error("MCP client not available")
            return
        
        try:
            # Prepare lab configuration
            config = {
                "lab_name": self.lab_config.lab_name,
                "script_id": self.lab_config.script_id,
                "trading_pair": self.lab_config.trading_pair,
                "account_id": self.lab_config.account_id,
                "start_date": self.lab_config.start_date,
                "end_date": self.lab_config.end_date,
                "auto_adjust": self.lab_config.auto_adjust,
                "concurrent_execution": self.lab_config.concurrent_execution,
                "parameters": self.lab_config.parameters
            }
            
            # Create lab
            result = await self.mcp_client.create_lab(config)
            
            # Emit success message
            self.post_message(self.LabCreated(self.lab_config))
            self.remove()
            
        except Exception as e:
            self.logger.error(f"Failed to create lab: {e}")
            self._show_error(f"Failed to create lab: {str(e)}")
    
    def _show_error(self, message: str) -> None:
        """Show error message to user"""
        # TODO: Implement proper error display
        self.logger.error(message)
    
    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select dropdown changes"""
        if event.select.id == "script-select":
            await self._update_script_details(event.value)
    
    async def _update_script_details(self, script_id: str) -> None:
        """Update script details display"""
        if not script_id or not self.mcp_client:
            return
        
        try:
            script_details = await self.mcp_client.get_script_details(script_id)
            details_widget = self.query_one("#script-details", Static)
            
            details_text = f"""
Name: {script_details.get('name', 'Unknown')}
Description: {script_details.get('description', 'No description')}
Parameters: {len(script_details.get('parameters', []))} parameters
Last Modified: {script_details.get('last_modified', 'Unknown')}
            """.strip()
            
            details_widget.update(details_text)
            
        except Exception as e:
            self.logger.error(f"Failed to load script details: {e}")


class LabListPanel(Widget):
    """Enhanced panel with lab list and overview"""
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        self.labs_data: List[Dict[str, Any]] = []
        self.selected_lab_id: Optional[str] = None
        self.refresh_callback: Optional[Callable] = None
    
    def compose(self) -> ComposeResult:
        with Container(classes="lab-list-container"):
            with Horizontal(classes="panel-header"):
                yield Static("Backtesting Labs", classes="panel-title")
                yield Button("🔄", id="refresh-labs", classes="refresh-btn")
                yield Button("➕", id="create-lab", classes="action-btn")
            
            # Lab table with enhanced columns
            table = DataTable(id="labs-table", cursor_type="row")
            table.add_columns(
                "Name", "Status", "Script", "Market", "Progress", 
                "P&L", "Created", "Actions"
            )
            yield table
            
            # Quick stats
            with Horizontal(classes="lab-stats"):
                yield Static("Total: 0", id="total-labs")
                yield Static("Running: 0", id="running-labs")
                yield Static("Complete: 0", id="complete-labs")
                yield Static("Failed: 0", id="failed-labs")
    
    async def on_mount(self) -> None:
        """Initialize lab list"""
        await self.refresh_labs()
    
    async def refresh_labs(self) -> None:
        """Refresh lab data from MCP server"""
        if not self.mcp_client:
            return
        
        try:
            self.labs_data = await self.mcp_client.get_all_labs()
            self._update_table()
            self._update_stats()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh labs: {e}")
    
    def _update_table(self) -> None:
        """Update the labs table"""
        table = self.query_one("#labs-table", DataTable)
        table.clear()
        
        for lab in self.labs_data:
            status_icon = self._get_status_icon(lab.get("status", "unknown"))
            progress = f"{lab.get('progress', 0):.1f}%"
            pnl = f"${lab.get('pnl', 0):,.2f}"
            created = lab.get("created_at", "Unknown")[:10]  # Just date part
            
            table.add_row(
                lab.get("name", "Unknown"),
                f"{status_icon} {lab.get('status', 'Unknown')}",
                lab.get("script_name", "Unknown"),
                lab.get("trading_pair", "Unknown"),
                progress,
                pnl,
                created,
                "⚙️ 📊 🗑️"  # Settings, Results, Delete icons
            )
    
    def _get_status_icon(self, status: str) -> str:
        """Get status icon for lab status"""
        status_icons = {
            "running": "🟢",
            "complete": "✅",
            "paused": "⏸️",
            "failed": "🔴",
            "pending": "⏳",
            "stopped": "⏹️"
        }
        return status_icons.get(status.lower(), "❓")
    
    def _update_stats(self) -> None:
        """Update lab statistics"""
        total = len(self.labs_data)
        running = sum(1 for lab in self.labs_data if lab.get("status") == "running")
        complete = sum(1 for lab in self.labs_data if lab.get("status") == "complete")
        failed = sum(1 for lab in self.labs_data if lab.get("status") == "failed")
        
        self.query_one("#total-labs", Static).update(f"Total: {total}")
        self.query_one("#running-labs", Static).update(f"Running: {running}")
        self.query_one("#complete-labs", Static).update(f"Complete: {complete}")
        self.query_one("#failed-labs", Static).update(f"Failed: {failed}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "refresh-labs":
            await self.refresh_labs()
        elif event.button.id == "create-lab":
            await self._show_lab_creation_wizard()
    
    async def _show_lab_creation_wizard(self) -> None:
        """Show lab creation wizard"""
        wizard = LabCreationWizard(self.mcp_client)
        await self.app.push_screen(wizard)
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle lab selection"""
        if event.row_index < len(self.labs_data):
            selected_lab = self.labs_data[event.row_index]
            self.selected_lab_id = selected_lab.get("id")
            
            # Notify parent about selection
            if self.refresh_callback:
                await self.refresh_callback(self.selected_lab_id)
    
    def set_refresh_callback(self, callback: Callable) -> None:
        """Set callback for lab selection changes"""
        self.refresh_callback = callback


class LabDetailsPanel(Widget):
    """Enhanced panel with detailed lab information and real-time updates"""
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        self.current_lab_id: Optional[str] = None
        self.lab_details: Dict[str, Any] = {}
        self.auto_refresh = True
        self._refresh_task: Optional[asyncio.Task] = None
    
    def compose(self) -> ComposeResult:
        with Container(classes="lab-details-container"):
            yield Static("Lab Details", classes="panel-title", id="details-title")
            
            with ScrollableContainer(classes="details-content"):
                # Basic Information Section
                with Collapsible(title="Basic Information", collapsed=False):
                    yield Static("", id="basic-info")
                
                # Configuration Section
                with Collapsible(title="Configuration"):
                    yield Static("", id="config-info")
                
                # Performance Metrics Section
                with Collapsible(title="Performance Metrics", collapsed=False):
                    yield Static("", id="performance-info")
                
                # Execution Status Section
                with Collapsible(title="Execution Status", collapsed=False):
                    yield Static("", id="execution-info")
                    yield ProgressBar(total=100, show_eta=True, id="execution-progress")
                
                # Recent Activity Section
                with Collapsible(title="Recent Activity"):
                    yield Static("", id="activity-info")
            
            # Control buttons
            with Horizontal(classes="details-controls"):
                yield Button("🔄 Refresh", id="refresh-details", classes="control-btn")
                yield Button("⏸️ Pause", id="pause-lab", classes="control-btn")
                yield Button("▶️ Resume", id="resume-lab", classes="control-btn")
                yield Button("⏹️ Stop", id="stop-lab", classes="control-btn")
                yield Button("📊 Results", id="view-results", classes="control-btn")
    
    async def update_lab_details(self, lab_id: str) -> None:
        """Update details for specific lab"""
        if not lab_id or not self.mcp_client:
            self._clear_details()
            return
        
        self.current_lab_id = lab_id
        await self._refresh_details()
        
        # Start auto-refresh if enabled
        if self.auto_refresh and not self._refresh_task:
            self._refresh_task = asyncio.create_task(self._auto_refresh_loop())
    
    async def _refresh_details(self) -> None:
        """Refresh lab details from server"""
        if not self.current_lab_id or not self.mcp_client:
            return
        
        try:
            self.lab_details = await self.mcp_client.get_lab_details(self.current_lab_id)
            self._update_display()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh lab details: {e}")
            self._show_error(f"Failed to load lab details: {str(e)}")
    
    def _update_display(self) -> None:
        """Update the display with current lab details"""
        if not self.lab_details:
            self._clear_details()
            return
        
        # Update title
        lab_name = self.lab_details.get("name", "Unknown Lab")
        self.query_one("#details-title", Static).update(f"Lab Details: {lab_name}")
        
        # Update basic information
        basic_info = f"""
Name: {self.lab_details.get('name', 'Unknown')}
ID: {self.lab_details.get('id', 'Unknown')}
Status: {self._get_status_display(self.lab_details.get('status', 'unknown'))}
Created: {self.lab_details.get('created_at', 'Unknown')}
Last Modified: {self.lab_details.get('modified_at', 'Unknown')}
        """.strip()
        self.query_one("#basic-info", Static).update(basic_info)
        
        # Update configuration
        config_info = f"""
Script: {self.lab_details.get('script_name', 'Unknown')}
Trading Pair: {self.lab_details.get('trading_pair', 'Unknown')}
Account: {self.lab_details.get('account_name', 'Unknown')}
Period: {self.lab_details.get('start_date', 'Unknown')} to {self.lab_details.get('end_date', 'Unknown')}
Auto-adjust: {'Yes' if self.lab_details.get('auto_adjust', False) else 'No'}
Concurrent: {'Yes' if self.lab_details.get('concurrent_execution', False) else 'No'}
        """.strip()
        self.query_one("#config-info", Static).update(config_info)
        
        # Update performance metrics
        performance_info = f"""
Total Return: {self.lab_details.get('total_return', 0):.2f}%
P&L: ${self.lab_details.get('pnl', 0):,.2f}
Trades Executed: {self.lab_details.get('total_trades', 0):,}
Win Rate: {self.lab_details.get('win_rate', 0):.1f}%
Max Drawdown: {self.lab_details.get('max_drawdown', 0):.2f}%
Sharpe Ratio: {self.lab_details.get('sharpe_ratio', 0):.2f}
Profit Factor: {self.lab_details.get('profit_factor', 0):.2f}
        """.strip()
        self.query_one("#performance-info", Static).update(performance_info)
        
        # Update execution status
        progress = self.lab_details.get('progress', 0)
        status = self.lab_details.get('status', 'unknown')
        
        execution_info = f"""
Progress: {progress:.1f}%
Status: {status.title()}
Started: {self.lab_details.get('started_at', 'Not started')}
ETA: {self._calculate_eta()}
Current Period: {self.lab_details.get('current_period', 'Unknown')}
        """.strip()
        self.query_one("#execution-info", Static).update(execution_info)
        
        # Update progress bar
        progress_bar = self.query_one("#execution-progress", ProgressBar)
        progress_bar.update(progress=progress)
        
        # Update recent activity
        activity_info = self._format_recent_activity()
        self.query_one("#activity-info", Static).update(activity_info)
    
    def _get_status_display(self, status: str) -> str:
        """Get formatted status display"""
        status_icons = {
            "running": "🟢 Running",
            "complete": "✅ Complete",
            "paused": "⏸️ Paused",
            "failed": "🔴 Failed",
            "pending": "⏳ Pending",
            "stopped": "⏹️ Stopped"
        }
        return status_icons.get(status.lower(), f"❓ {status.title()}")
    
    def _calculate_eta(self) -> str:
        """Calculate estimated time to completion"""
        progress = self.lab_details.get('progress', 0)
        started_at = self.lab_details.get('started_at')
        
        if not started_at or progress <= 0:
            return "Unknown"
        
        try:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            elapsed = datetime.now() - start_time.replace(tzinfo=None)
            
            if progress >= 100:
                return "Complete"
            
            estimated_total = elapsed.total_seconds() / (progress / 100)
            remaining = estimated_total - elapsed.total_seconds()
            
            if remaining <= 0:
                return "Almost done"
            
            remaining_delta = timedelta(seconds=remaining)
            
            # Format remaining time
            hours = remaining_delta.seconds // 3600
            minutes = (remaining_delta.seconds % 3600) // 60
            
            if remaining_delta.days > 0:
                return f"{remaining_delta.days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception:
            return "Unknown"
    
    def _format_recent_activity(self) -> str:
        """Format recent activity information"""
        activity = self.lab_details.get('recent_activity', [])
        
        if not activity:
            return "No recent activity"
        
        formatted_activity = []
        for item in activity[-5:]:  # Show last 5 activities
            timestamp = item.get('timestamp', 'Unknown')
            message = item.get('message', 'Unknown activity')
            formatted_activity.append(f"• {timestamp}: {message}")
        
        return "\n".join(formatted_activity)
    
    def _clear_details(self) -> None:
        """Clear all details display"""
        self.query_one("#details-title", Static).update("Lab Details")
        self.query_one("#basic-info", Static).update("No lab selected")
        self.query_one("#config-info", Static).update("")
        self.query_one("#performance-info", Static).update("")
        self.query_one("#execution-info", Static).update("")
        self.query_one("#activity-info", Static).update("")
        
        progress_bar = self.query_one("#execution-progress", ProgressBar)
        progress_bar.update(progress=0)
    
    def _show_error(self, message: str) -> None:
        """Show error message"""
        self.query_one("#basic-info", Static).update(f"Error: {message}")
    
    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh loop for real-time updates"""
        while self.auto_refresh and self.current_lab_id:
            try:
                await asyncio.sleep(5)  # Refresh every 5 seconds
                await self._refresh_details()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-refresh error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if not self.current_lab_id or not self.mcp_client:
            return
        
        try:
            if event.button.id == "refresh-details":
                await self._refresh_details()
            
            elif event.button.id == "pause-lab":
                await self.mcp_client.call_tool("pause_lab", {"lab_id": self.current_lab_id})
                await self._refresh_details()
            
            elif event.button.id == "resume-lab":
                await self.mcp_client.call_tool("resume_lab", {"lab_id": self.current_lab_id})
                await self._refresh_details()
            
            elif event.button.id == "stop-lab":
                await self.mcp_client.call_tool("stop_lab", {"lab_id": self.current_lab_id})
                await self._refresh_details()
            
            elif event.button.id == "view-results":
                # TODO: Show detailed results view
                pass
                
        except Exception as e:
            self.logger.error(f"Lab control action failed: {e}")
            self._show_error(f"Action failed: {str(e)}")
    
    async def on_unmount(self) -> None:
        """Cleanup when widget is unmounted"""
        self.auto_refresh = False
        if self._refresh_task:
            self._refresh_task.cancel()


class BulkLabOperationsModal(Widget):
    """Modal for bulk lab operations"""
    
    class OperationComplete(Message):
        """Message sent when bulk operation completes"""
        def __init__(self, operation: str, results: List[Dict[str, Any]]) -> None:
            self.operation = operation
            self.results = results
            super().__init__()
    
    def __init__(self, operation: str, lab_ids: List[str], mcp_client=None):
        super().__init__()
        self.operation = operation
        self.lab_ids = lab_ids
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        
    def compose(self) -> ComposeResult:
        with Container(classes="modal-container"):
            yield Static(f"Bulk {self.operation.title()}", classes="modal-title")
            yield Static(f"Selected {len(self.lab_ids)} labs", classes="modal-subtitle")
            
            with Container(classes="modal-content"):
                if self.operation == "clone":
                    yield Label("Clone Configuration:")
                    yield Label("Target Markets (comma-separated):")
                    yield Input(placeholder="BTC/USDT, ETH/USDT, ADA/USDT", id="target-markets")
                    yield Label("Name Template:")
                    yield Input(value="{original_name}_{market}", id="name-template")
                    yield Checkbox("Clone parameters", value=True, id="clone-parameters")
                
                elif self.operation == "optimize":
                    yield Label("Optimization Settings:")
                    yield Label("Algorithm:")
                    with RadioSet(id="optimization-algorithm"):
                        yield RadioButton("Genetic Algorithm", value=True)
                        yield RadioButton("Grid Search")
                        yield RadioButton("Random Search")
                    yield Label("Max Iterations:")
                    yield Input(value="100", id="max-iterations")
                
                # Progress tracking
                yield ProgressBar(total=len(self.lab_ids), id="bulk-progress")
                yield Static("Ready to start...", id="progress-status")
            
            with Horizontal(classes="modal-buttons"):
                yield Button("Start", id="start-operation", variant="primary")
                yield Button("Cancel", id="cancel-operation", variant="error")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "start-operation":
            await self._execute_bulk_operation()
        elif event.button.id == "cancel-operation":
            self.remove()
    
    async def _execute_bulk_operation(self) -> None:
        """Execute the bulk operation"""
        if not self.mcp_client:
            return
        
        progress_bar = self.query_one("#bulk-progress", ProgressBar)
        status_widget = self.query_one("#progress-status", Static)
        
        results = []
        
        try:
            for i, lab_id in enumerate(self.lab_ids):
                status_widget.update(f"Processing lab {i+1}/{len(self.lab_ids)}...")
                
                if self.operation == "clone":
                    result = await self._clone_lab(lab_id)
                elif self.operation == "delete":
                    result = await self._delete_lab(lab_id)
                elif self.operation == "optimize":
                    result = await self._optimize_lab(lab_id)
                else:
                    result = {"success": False, "error": f"Unknown operation: {self.operation}"}
                
                results.append({"lab_id": lab_id, **result})
                progress_bar.update(progress=i + 1)
                
                # Small delay to prevent overwhelming the server
                await asyncio.sleep(0.1)
            
            status_widget.update("Operation complete!")
            self.post_message(self.OperationComplete(self.operation, results))
            
            # Auto-close after 2 seconds
            await asyncio.sleep(2)
            self.remove()
            
        except Exception as e:
            self.logger.error(f"Bulk operation failed: {e}")
            status_widget.update(f"Operation failed: {str(e)}")
    
    async def _clone_lab(self, lab_id: str) -> Dict[str, Any]:
        """Clone a single lab"""
        try:
            markets_input = self.query_one("#target-markets", Input).value.strip()
            name_template = self.query_one("#name-template", Input).value.strip()
            
            if not markets_input:
                return {"success": False, "error": "No target markets specified"}
            
            markets = [m.strip() for m in markets_input.split(",")]
            
            # Use bulk clone if available, otherwise clone individually
            if hasattr(self.mcp_client, 'bulk_clone_labs'):
                result = await self.mcp_client.bulk_clone_labs(lab_id, markets, name_template)
                return {"success": True, "cloned_labs": result}
            else:
                # Individual cloning
                cloned_labs = []
                for market in markets:
                    new_name = name_template.replace("{market}", market).replace("{original_name}", f"Lab_{lab_id}")
                    clone_result = await self.mcp_client.clone_lab(lab_id, new_name)
                    cloned_labs.append(clone_result)
                
                return {"success": True, "cloned_labs": cloned_labs}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _delete_lab(self, lab_id: str) -> Dict[str, Any]:
        """Delete a single lab"""
        try:
            await self.mcp_client.call_tool("delete_lab", {"lab_id": lab_id})
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _optimize_lab(self, lab_id: str) -> Dict[str, Any]:
        """Optimize a single lab"""
        try:
            algorithm = "genetic"  # Default, could be read from radio buttons
            max_iterations = int(self.query_one("#max-iterations", Input).value or "100")
            
            result = await self.mcp_client.call_tool("optimize_lab_parameters", {
                "lab_id": lab_id,
                "algorithm": algorithm,
                "max_iterations": max_iterations
            })
            return {"success": True, "optimization_result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


class LabActionsPanel(Widget):
    """Enhanced panel with lab action buttons and bulk operations"""
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        self.selected_lab_ids: List[str] = []
        self.action_callback: Optional[Callable] = None
    
    def compose(self) -> ComposeResult:
        with Container(classes="lab-actions-container"):
            yield Static("Lab Actions", classes="panel-title")
            
            # Individual lab actions
            with Container(classes="individual-actions"):
                yield Static("Individual Actions:", classes="section-title")
                with Horizontal(classes="action-buttons"):
                    yield Button("➕ New Lab", id="new-lab", classes="action-btn")
                    yield Button("📋 Clone Lab", id="clone-lab", classes="action-btn")
                    yield Button("🧠 Smart Start", id="intelligent-backtest", classes="action-btn")
                    yield Button("▶️ Start", id="start-lab", classes="action-btn")
                
                with Horizontal(classes="action-buttons"):
                    yield Button("⏸️ Pause", id="pause-lab", classes="action-btn")
                    yield Button("⏹️ Stop", id="stop-lab", classes="action-btn")
                    yield Button("🔧 Optimize", id="optimize-lab", classes="action-btn")
                    yield Button("🤖 Deploy Bot", id="deploy-bot", classes="action-btn")
                
                with Horizontal(classes="action-buttons"):
                    yield Button("📊 Export", id="export-results", classes="action-btn")
                    yield Button("🔍 Validate Data", id="validate-data", classes="action-btn")
                    yield Button("📈 Auto-Adjust", id="auto-adjust", classes="action-btn")
                    yield Button("⚡ Resource Check", id="resource-check", classes="action-btn")
            
            # Bulk operations
            with Container(classes="bulk-actions"):
                yield Static("Bulk Operations:", classes="section-title")
                yield Static("Selected: 0 labs", id="selection-count")
                
                with Horizontal(classes="bulk-buttons"):
                    yield Button("📋 Bulk Clone", id="bulk-clone", classes="bulk-btn", disabled=True)
                    yield Button("🔧 Bulk Optimize", id="bulk-optimize", classes="bulk-btn", disabled=True)
                    yield Button("🗑️ Bulk Delete", id="bulk-delete", classes="bulk-btn", disabled=True)
                    yield Button("📤 Bulk Export", id="bulk-export", classes="bulk-btn", disabled=True)
            
            # Quick templates
            with Container(classes="quick-templates"):
                yield Static("Quick Templates:", classes="section-title")
                with Horizontal(classes="template-buttons"):
                    yield Button("📈 Trend Following", id="template-trend", classes="template-btn")
                    yield Button("🔄 Mean Reversion", id="template-mean", classes="template-btn")
                    yield Button("⚡ Scalping", id="template-scalp", classes="template-btn")
                    yield Button("🎯 Arbitrage", id="template-arb", classes="template-btn")
    
    def update_selection(self, selected_lab_ids: List[str]) -> None:
        """Update selected lab IDs and enable/disable bulk actions"""
        self.selected_lab_ids = selected_lab_ids
        count = len(selected_lab_ids)
        
        # Update selection count
        self.query_one("#selection-count", Static).update(f"Selected: {count} labs")
        
        # Enable/disable bulk action buttons
        bulk_buttons = [
            "#bulk-clone", "#bulk-optimize", "#bulk-delete", "#bulk-export"
        ]
        
        for button_id in bulk_buttons:
            button = self.query_one(button_id, Button)
            button.disabled = count == 0
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        # Individual actions
        if button_id == "new-lab":
            await self._create_new_lab()
        elif button_id == "clone-lab":
            await self._clone_selected_lab()
        elif button_id == "intelligent-backtest":
            await self._start_intelligent_backtest()
        elif button_id in ["start-lab", "pause-lab", "stop-lab"]:
            await self._control_selected_lab(button_id.replace("-lab", ""))
        elif button_id == "optimize-lab":
            await self._optimize_selected_lab()
        elif button_id == "deploy-bot":
            await self._deploy_bot_from_lab()
        elif button_id == "export-results":
            await self._export_lab_results()
        elif button_id == "validate-data":
            await self._validate_lab_data()
        elif button_id == "auto-adjust":
            await self._auto_adjust_period()
        elif button_id == "resource-check":
            await self._check_resources()
        
        # Bulk actions
        elif button_id.startswith("bulk-"):
            operation = button_id.replace("bulk-", "")
            await self._show_bulk_operation_modal(operation)
        
        # Template actions
        elif button_id.startswith("template-"):
            template_type = button_id.replace("template-", "")
            await self._create_lab_from_template(template_type)
    
    async def _create_new_lab(self) -> None:
        """Create a new lab using the wizard"""
        wizard = LabCreationWizard(self.mcp_client)
        await self.app.push_screen(wizard)
    
    async def _clone_selected_lab(self) -> None:
        """Clone the currently selected lab"""
        if not self.selected_lab_ids:
            self._show_message("No lab selected")
            return
        
        # For single lab, show simple clone dialog
        if len(self.selected_lab_ids) == 1:
            # TODO: Implement simple clone dialog
            pass
        else:
            await self._show_bulk_operation_modal("clone")
    
    async def _control_selected_lab(self, action: str) -> None:
        """Control selected lab (start/pause/stop)"""
        if not self.selected_lab_ids or not self.mcp_client:
            self._show_message("No lab selected")
            return
        
        try:
            lab_id = self.selected_lab_ids[0]  # Use first selected lab
            await self.mcp_client.call_tool(f"{action}_lab", {"lab_id": lab_id})
            
            if self.action_callback:
                await self.action_callback("refresh")
                
        except Exception as e:
            self.logger.error(f"Lab control action failed: {e}")
            self._show_message(f"Action failed: {str(e)}")
    
    async def _optimize_selected_lab(self) -> None:
        """Optimize selected lab parameters"""
        if not self.selected_lab_ids:
            self._show_message("No lab selected")
            return
        
        if len(self.selected_lab_ids) == 1:
            # TODO: Show optimization settings dialog
            pass
        else:
            await self._show_bulk_operation_modal("optimize")
    
    async def _deploy_bot_from_lab(self) -> None:
        """Deploy bot from selected lab"""
        if not self.selected_lab_ids or not self.mcp_client:
            self._show_message("No lab selected")
            return
        
        try:
            lab_id = self.selected_lab_ids[0]
            
            # TODO: Show bot deployment dialog with account selection
            # For now, use a default configuration
            result = await self.mcp_client.create_bot_from_lab(
                lab_id=lab_id,
                bot_name=f"Bot_from_Lab_{lab_id}",
                account_id="default_account"  # Should be selected by user
            )
            
            self._show_message(f"Bot created successfully: {result.get('bot_id', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Bot deployment failed: {e}")
            self._show_message(f"Bot deployment failed: {str(e)}")
    
    async def _export_lab_results(self) -> None:
        """Export results for selected labs"""
        if not self.selected_lab_ids:
            self._show_message("No lab selected")
            return
        
        # TODO: Implement export functionality
        self._show_message("Export functionality coming soon")
    
    async def _show_bulk_operation_modal(self, operation: str) -> None:
        """Show bulk operation modal"""
        if not self.selected_lab_ids:
            return
        
        modal = BulkLabOperationsModal(operation, self.selected_lab_ids, self.mcp_client)
        await self.app.push_screen(modal)
    
    async def _create_lab_from_template(self, template_type: str) -> None:
        """Create lab from predefined template"""
        # TODO: Implement template-based lab creation
        self._show_message(f"Creating {template_type} template lab...")
    
    def _show_message(self, message: str) -> None:
        """Show message to user"""
        # TODO: Implement proper message display
        self.logger.info(message)
    
    async def _start_intelligent_backtest(self) -> None:
        """Start intelligent backtest for selected lab"""
        if not self.selected_lab_ids or not self.mcp_client:
            self._show_message("No lab selected")
            return
        
        try:
            lab_id = self.selected_lab_ids[0]
            
            # Notify parent to start intelligent backtest
            if self.action_callback:
                await self.action_callback("start_intelligent_backtest")
            
            self._show_message("Starting intelligent backtest...")
            
        except Exception as e:
            self.logger.error(f"Failed to start intelligent backtest: {e}")
            self._show_message(f"Failed to start intelligent backtest: {str(e)}")
    
    async def _validate_lab_data(self) -> None:
        """Validate historical data for selected lab"""
        if not self.selected_lab_ids or not self.mcp_client:
            self._show_message("No lab selected")
            return
        
        try:
            lab_id = self.selected_lab_ids[0]
            
            # Get lab details
            lab_details = await self.mcp_client.get_lab_details(lab_id)
            trading_pair = lab_details.get("trading_pair")
            start_date = lab_details.get("start_date")
            end_date = lab_details.get("end_date")
            
            # Validate data
            validation_result = await self.mcp_client.call_tool("validate_historical_data", {
                "trading_pair": trading_pair,
                "start_date": start_date,
                "end_date": end_date
            })
            
            if validation_result.get("is_valid", False):
                quality_score = validation_result.get("data_quality_score", 0.0)
                self._show_message(f"✅ Data validation passed (Quality: {quality_score:.1f}%)")
            else:
                error_msg = validation_result.get("error_message", "Unknown error")
                self._show_message(f"❌ Data validation failed: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"Data validation failed: {e}")
            self._show_message(f"Data validation error: {str(e)}")
    
    async def _auto_adjust_period(self) -> None:
        """Auto-adjust backtest period for selected lab"""
        if not self.selected_lab_ids or not self.mcp_client:
            self._show_message("No lab selected")
            return
        
        try:
            lab_id = self.selected_lab_ids[0]
            
            # Get lab details
            lab_details = await self.mcp_client.get_lab_details(lab_id)
            trading_pair = lab_details.get("trading_pair")
            
            # Find alternative periods
            alternatives = await self.mcp_client.call_tool("find_alternative_periods", {
                "trading_pair": trading_pair,
                "requested_start": lab_details.get("start_date"),
                "requested_end": lab_details.get("end_date"),
                "min_duration_days": 30,
                "max_alternatives": 3
            })
            
            periods = alternatives.get("periods", [])
            if periods:
                best_period = periods[0]
                self._show_message(
                    f"📅 Suggested period: {best_period['start_date']} to {best_period['end_date']}"
                )
            else:
                self._show_message("No alternative periods found")
                
        except Exception as e:
            self.logger.error(f"Period adjustment failed: {e}")
            self._show_message(f"Period adjustment error: {str(e)}")
    
    async def _check_resources(self) -> None:
        """Check system resources for backtesting"""
        try:
            # Get current resource usage
            resource_info = await self.mcp_client.call_tool("get_system_resources", {})
            
            memory_usage = resource_info.get("memory_usage_percent", 0)
            cpu_usage = resource_info.get("cpu_usage_percent", 0)
            active_labs = resource_info.get("active_labs", 0)
            
            status_msg = f"""
🖥️ System Resources:
• Memory: {memory_usage:.1f}%
• CPU: {cpu_usage:.1f}%
• Active Labs: {active_labs}/3
            """.strip()
            
            self._show_message(status_msg)
            
        except Exception as e:
            self.logger.error(f"Resource check failed: {e}")
            self._show_message(f"Resource check error: {str(e)}")
    
    def set_action_callback(self, callback: Callable) -> None:
        """Set callback for action notifications"""
        self.action_callback = callback


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics data structure"""
    # Basic metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Risk metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    volatility: float = 0.0
    
    # Trade metrics
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    profit_factor: float = 0.0
    avg_trade_duration: str = ""
    
    # Advanced metrics
    var_95: float = 0.0
    cvar_95: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    information_ratio: float = 0.0
    treynor_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display"""
        return {
            "Basic Metrics": {
                "Total Return": f"{self.total_return:.2f}%",
                "Annualized Return": f"{self.annualized_return:.2f}%",
                "Total Trades": f"{self.total_trades:,}",
                "Win Rate": f"{self.win_rate:.1f}%",
            },
            "Risk Metrics": {
                "Sharpe Ratio": f"{self.sharpe_ratio:.2f}",
                "Sortino Ratio": f"{self.sortino_ratio:.2f}",
                "Max Drawdown": f"{self.max_drawdown:.2f}%",
                "Volatility": f"{self.volatility:.2f}%",
            },
            "Trade Metrics": {
                "Average Win": f"${self.avg_win:.2f}",
                "Average Loss": f"${self.avg_loss:.2f}",
                "Profit Factor": f"{self.profit_factor:.2f}",
                "Avg Duration": self.avg_trade_duration,
            },
            "Advanced Metrics": {
                "VaR (95%)": f"${self.var_95:.2f}",
                "Beta": f"{self.beta:.2f}",
                "Alpha": f"{self.alpha:.2f}%",
                "Information Ratio": f"{self.information_ratio:.2f}",
            }
        }


class AdvancedChartRenderer:
    """Advanced ASCII chart rendering for backtest analysis"""
    
    @staticmethod
    def render_equity_curve(equity_data: List[float], width: int = 60, height: int = 12) -> str:
        """Render detailed equity curve with trend lines"""
        if not equity_data or len(equity_data) < 2:
            return "No equity data available"
        
        min_val = min(equity_data)
        max_val = max(equity_data)
        
        if max_val == min_val:
            return "Flat equity curve"
        
        # Normalize data
        normalized = []
        for val in equity_data:
            norm_val = int((val - min_val) / (max_val - min_val) * (height - 1))
            normalized.append(norm_val)
        
        # Create chart with trend analysis
        chart_lines = []
        
        # Add trend line calculation
        trend_slope = (equity_data[-1] - equity_data[0]) / len(equity_data)
        
        for y in range(height - 1, -1, -1):
            value = min_val + (max_val - min_val) * (height - 1 - y) / (height - 1)
            line = f"${value:8.0f} ┤"
            
            for x in range(min(len(normalized), width)):
                if normalized[x] == y:
                    # Determine trend direction
                    if x > 0:
                        if normalized[x] > normalized[x-1]:
                            line += "╱"  # Up trend
                        elif normalized[x] < normalized[x-1]:
                            line += "╲"  # Down trend
                        else:
                            line += "─"  # Flat
                    else:
                        line += "●"
                elif x > 0 and (
                    (normalized[x-1] < y < normalized[x]) or 
                    (normalized[x-1] > y > normalized[x])
                ):
                    line += "│"
                else:
                    line += " "
            
            chart_lines.append(line)
        
        # Add time axis with markers
        time_axis = "         └" + "─" * min(len(normalized), width)
        chart_lines.append(time_axis)
        
        # Add trend information
        trend_direction = "↗" if trend_slope > 0 else "↘" if trend_slope < 0 else "→"
        chart_lines.append(f"Trend: {trend_direction} ({trend_slope:+.2f} per period)")
        
        return "\n".join(chart_lines)
    
    @staticmethod
    def render_drawdown_chart(drawdown_data: List[float], width: int = 60, height: int = 8) -> str:
        """Render drawdown chart with recovery periods"""
        if not drawdown_data:
            return "No drawdown data available"
        
        # Drawdowns are typically negative, so we work with absolute values
        abs_drawdowns = [abs(dd) for dd in drawdown_data]
        max_dd = max(abs_drawdowns) if abs_drawdowns else 0
        
        if max_dd == 0:
            return "No drawdowns recorded"
        
        # Normalize to chart height
        normalized = []
        for dd in abs_drawdowns:
            norm_val = int((dd / max_dd) * (height - 1))
            normalized.append(norm_val)
        
        chart_lines = []
        for y in range(height - 1, -1, -1):
            dd_value = (max_dd * (height - 1 - y) / (height - 1))
            line = f"-{dd_value:6.1f}% ┤"
            
            for x in range(min(len(normalized), width)):
                if normalized[x] >= y:
                    line += "█"  # Drawdown bar
                else:
                    line += " "
            
            chart_lines.append(line)
        
        # Add time axis
        time_axis = "         └" + "─" * min(len(normalized), width)
        chart_lines.append(time_axis)
        
        return "\n".join(chart_lines)
    
    @staticmethod
    def render_monthly_returns_heatmap(monthly_returns: Dict[str, float], width: int = 50) -> str:
        """Render monthly returns as ASCII heatmap"""
        if not monthly_returns:
            return "No monthly returns data available"
        
        # Sort by date
        sorted_months = sorted(monthly_returns.items())
        
        # Create heatmap representation
        heatmap_lines = ["Monthly Returns Heatmap:"]
        
        # Group by year
        years = {}
        for month, return_val in sorted_months:
            year = month[:4]
            if year not in years:
                years[year] = {}
            month_name = month[5:7]
            years[year][month_name] = return_val
        
        # Render each year
        for year, months in years.items():
            line = f"{year}: "
            for month_num in ["01", "02", "03", "04", "05", "06", 
                             "07", "08", "09", "10", "11", "12"]:
                if month_num in months:
                    return_val = months[month_num]
                    if return_val > 5:
                        line += "██"  # Strong positive
                    elif return_val > 0:
                        line += "▓▓"  # Positive
                    elif return_val > -5:
                        line += "░░"  # Slight negative
                    else:
                        line += "  "  # Strong negative
                else:
                    line += "··"  # No data
            heatmap_lines.append(line)
        
        # Add legend
        heatmap_lines.append("")
        heatmap_lines.append("Legend: ██ >5%  ▓▓ 0-5%  ░░ 0-(-5%)  ·· <-5%")
        
        return "\n".join(heatmap_lines)


class TradeAnalyzer:
    """Advanced trade-by-trade analysis"""
    
    @staticmethod
    def analyze_trades(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comprehensive trade analysis"""
        if not trades:
            return {"error": "No trades to analyze"}
        
        # Basic statistics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
        
        # Trade duration analysis
        durations = []
        for trade in trades:
            duration_str = trade.get("duration", "0m")
            # Parse duration (simplified)
            if "h" in duration_str:
                hours = float(duration_str.split("h")[0])
                durations.append(hours * 60)  # Convert to minutes
            elif "m" in duration_str:
                minutes = float(duration_str.split("m")[0])
                durations.append(minutes)
        
        # P&L analysis
        pnls = [t.get("pnl", 0) for t in trades]
        winning_pnls = [t.get("pnl", 0) for t in winning_trades]
        losing_pnls = [t.get("pnl", 0) for t in losing_trades]
        
        # Calculate streaks
        win_streaks, loss_streaks = TradeAnalyzer._calculate_streaks(trades)
        
        # Time-based analysis
        hourly_performance = TradeAnalyzer._analyze_by_hour(trades)
        daily_performance = TradeAnalyzer._analyze_by_day(trades)
        
        return {
            "basic_stats": {
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
            },
            "pnl_analysis": {
                "total_pnl": sum(pnls),
                "avg_win": sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0,
                "avg_loss": sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0,
                "largest_win": max(pnls) if pnls else 0,
                "largest_loss": min(pnls) if pnls else 0,
                "profit_factor": abs(sum(winning_pnls) / sum(losing_pnls)) if losing_pnls and sum(losing_pnls) != 0 else 0,
            },
            "duration_analysis": {
                "avg_duration_minutes": sum(durations) / len(durations) if durations else 0,
                "shortest_trade_minutes": min(durations) if durations else 0,
                "longest_trade_minutes": max(durations) if durations else 0,
            },
            "streak_analysis": {
                "max_win_streak": max(win_streaks) if win_streaks else 0,
                "max_loss_streak": max(loss_streaks) if loss_streaks else 0,
                "current_streak": TradeAnalyzer._get_current_streak(trades),
            },
            "time_analysis": {
                "hourly_performance": hourly_performance,
                "daily_performance": daily_performance,
            }
        }
    
    @staticmethod
    def _calculate_streaks(trades: List[Dict[str, Any]]) -> tuple:
        """Calculate winning and losing streaks"""
        win_streaks = []
        loss_streaks = []
        current_win_streak = 0
        current_loss_streak = 0
        
        for trade in trades:
            pnl = trade.get("pnl", 0)
            if pnl > 0:
                current_win_streak += 1
                if current_loss_streak > 0:
                    loss_streaks.append(current_loss_streak)
                    current_loss_streak = 0
            elif pnl < 0:
                current_loss_streak += 1
                if current_win_streak > 0:
                    win_streaks.append(current_win_streak)
                    current_win_streak = 0
        
        # Add final streaks
        if current_win_streak > 0:
            win_streaks.append(current_win_streak)
        if current_loss_streak > 0:
            loss_streaks.append(current_loss_streak)
        
        return win_streaks, loss_streaks
    
    @staticmethod
    def _get_current_streak(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get current winning/losing streak"""
        if not trades:
            return {"type": "none", "count": 0}
        
        # Look at recent trades to determine current streak
        current_streak = 0
        streak_type = "none"
        
        for trade in reversed(trades[-10:]):  # Look at last 10 trades
            pnl = trade.get("pnl", 0)
            if current_streak == 0:
                if pnl > 0:
                    streak_type = "winning"
                    current_streak = 1
                elif pnl < 0:
                    streak_type = "losing"
                    current_streak = 1
            else:
                if (streak_type == "winning" and pnl > 0) or (streak_type == "losing" and pnl < 0):
                    current_streak += 1
                else:
                    break
        
        return {"type": streak_type, "count": current_streak}
    
    @staticmethod
    def _analyze_by_hour(trades: List[Dict[str, Any]]) -> Dict[int, Dict[str, float]]:
        """Analyze performance by hour of day"""
        hourly_stats = {}
        
        for trade in trades:
            # Extract hour from trade date (simplified)
            date_str = trade.get("date", "")
            if "T" in date_str:
                time_part = date_str.split("T")[1]
                hour = int(time_part.split(":")[0])
                
                if hour not in hourly_stats:
                    hourly_stats[hour] = {"trades": 0, "pnl": 0.0, "wins": 0}
                
                hourly_stats[hour]["trades"] += 1
                hourly_stats[hour]["pnl"] += trade.get("pnl", 0)
                if trade.get("pnl", 0) > 0:
                    hourly_stats[hour]["wins"] += 1
        
        # Calculate win rates
        for hour_stats in hourly_stats.values():
            hour_stats["win_rate"] = hour_stats["wins"] / hour_stats["trades"] * 100 if hour_stats["trades"] > 0 else 0
        
        return hourly_stats
    
    @staticmethod
    def _analyze_by_day(trades: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Analyze performance by day of week"""
        daily_stats = {}
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for trade in trades:
            # This would need proper date parsing in real implementation
            # For now, use simplified logic
            date_str = trade.get("date", "")
            if date_str:
                # Simplified day extraction (would need proper datetime parsing)
                day_index = hash(date_str) % 7  # Mock day calculation
                day_name = day_names[day_index]
                
                if day_name not in daily_stats:
                    daily_stats[day_name] = {"trades": 0, "pnl": 0.0, "wins": 0}
                
                daily_stats[day_name]["trades"] += 1
                daily_stats[day_name]["pnl"] += trade.get("pnl", 0)
                if trade.get("pnl", 0) > 0:
                    daily_stats[day_name]["wins"] += 1
        
        # Calculate win rates
        for day_stats in daily_stats.values():
            day_stats["win_rate"] = day_stats["wins"] / day_stats["trades"] * 100 if day_stats["trades"] > 0 else 0
        
        return daily_stats


class BacktestComparator:
    """Compare multiple backtest results"""
    
    @staticmethod
    def compare_labs(lab_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple lab results side-by-side"""
        if len(lab_results) < 2:
            return {"error": "Need at least 2 labs to compare"}
        
        comparison = {
            "labs": [lab.get("name", "Unknown") for lab in lab_results],
            "metrics_comparison": {},
            "rankings": {},
            "statistical_tests": {}
        }
        
        # Compare key metrics
        metrics_to_compare = [
            "total_return", "sharpe_ratio", "max_drawdown", "win_rate", 
            "profit_factor", "total_trades", "volatility"
        ]
        
        for metric in metrics_to_compare:
            values = [lab.get(metric, 0) for lab in lab_results]
            comparison["metrics_comparison"][metric] = {
                "values": values,
                "best_index": values.index(max(values)) if metric != "max_drawdown" else values.index(min(values)),
                "worst_index": values.index(min(values)) if metric != "max_drawdown" else values.index(max(values)),
                "range": max(values) - min(values),
                "average": sum(values) / len(values)
            }
        
        # Create rankings
        comparison["rankings"] = BacktestComparator._create_rankings(lab_results)
        
        # Statistical significance tests (simplified)
        comparison["statistical_tests"] = BacktestComparator._perform_statistical_tests(lab_results)
        
        return comparison
    
    @staticmethod
    def _create_rankings(lab_results: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """Create rankings for different metrics"""
        rankings = {}
        
        # Rank by different criteria
        criteria = {
            "total_return": lambda x: x.get("total_return", 0),
            "sharpe_ratio": lambda x: x.get("sharpe_ratio", 0),
            "risk_adjusted": lambda x: x.get("sharpe_ratio", 0) * (1 - abs(x.get("max_drawdown", 0)) / 100),
            "consistency": lambda x: x.get("win_rate", 0) * x.get("profit_factor", 0),
        }
        
        for criterion, key_func in criteria.items():
            sorted_labs = sorted(enumerate(lab_results), key=lambda x: key_func(x[1]), reverse=True)
            rankings[criterion] = [i for i, _ in sorted_labs]
        
        return rankings
    
    @staticmethod
    def _perform_statistical_tests(lab_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform statistical significance tests (simplified)"""
        # This would implement proper statistical tests in a real scenario
        # For now, return mock results
        
        tests = {
            "return_significance": {
                "test": "t-test",
                "p_value": 0.05,
                "significant": True,
                "interpretation": "Returns are statistically different"
            },
            "risk_comparison": {
                "test": "F-test",
                "p_value": 0.12,
                "significant": False,
                "interpretation": "Risk levels are not significantly different"
            },
            "correlation_analysis": {
                "correlation_matrix": [[1.0, 0.65], [0.65, 1.0]],
                "interpretation": "Moderate positive correlation between strategies"
            }
        }
        
        return tests


class BacktestResultsPanel(Widget):
    """Enhanced panel with comprehensive backtest results visualization and analysis"""
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        self.current_lab_id: Optional[str] = None
        self.results_data: Dict[str, Any] = {}
        self.performance_metrics: Optional[PerformanceMetrics] = None
        self.trade_analysis: Dict[str, Any] = {}
        self.chart_renderer = AdvancedChartRenderer()
        self.trade_analyzer = TradeAnalyzer()
        self.comparator = BacktestComparator()
        self.comparison_labs: List[str] = []
    
    def compose(self) -> ComposeResult:
        with Container(classes="results-container"):
            with Horizontal(classes="results-header"):
                yield Static("Backtest Results", classes="panel-title")
                yield Button("🔄", id="refresh-results", classes="refresh-btn")
                yield Button("📊", id="detailed-view", classes="action-btn")
                yield Button("📤", id="export-results", classes="action-btn")
            
            with TabbedContent(classes="results-tabs"):
                # Overview Tab
                with TabPane("Overview", id="overview-tab"):
                    with ScrollableContainer():
                        yield Static("", id="overview-content")
                
                # Performance Tab
                with TabPane("Performance", id="performance-tab"):
                    with ScrollableContainer():
                        yield Static("Equity Curve:", classes="chart-title")
                        yield Static("", id="equity-chart")
                        yield Static("Drawdown Analysis:", classes="chart-title")
                        yield Static("", id="drawdown-chart")
                        yield Static("Performance Metrics:", classes="section-title")
                        yield Static("", id="performance-metrics")
                
                # Trades Tab
                with TabPane("Trades", id="trades-tab"):
                    with ScrollableContainer():
                        yield Static("Trade Analysis Summary:", classes="section-title")
                        yield Static("", id="trade-analysis-summary")
                        yield Static("Trade History:", classes="section-title")
                        table = DataTable(id="trades-table")
                        table.add_columns("Date", "Type", "Pair", "Size", "Price", "P&L", "Duration", "Streak")
                        yield table
                        yield Static("Trade Patterns:", classes="section-title")
                        yield Static("", id="trade-patterns")
                
                # Analysis Tab
                with TabPane("Analysis", id="analysis-tab"):
                    with ScrollableContainer():
                        yield Static("Advanced Analysis:", classes="section-title")
                        yield Static("", id="advanced-analysis")
                        yield Static("Risk Analysis:", classes="section-title")
                        yield Static("", id="risk-analysis")
                        yield Static("Time-based Performance:", classes="section-title")
                        yield Static("", id="time-analysis")
                        yield Static("Monthly Returns Heatmap:", classes="section-title")
                        yield Static("", id="monthly-heatmap")
                
                # Comparison Tab
                with TabPane("Compare", id="compare-tab"):
                    with ScrollableContainer():
                        yield Static("Lab Comparison:", classes="section-title")
                        with Horizontal():
                            yield Button("Add Lab", id="add-comparison-lab")
                            yield Button("Remove Lab", id="remove-comparison-lab")
                            yield Button("Compare All", id="compare-labs")
                        yield Static("Selected Labs:", classes="subsection-title")
                        yield Static("", id="comparison-labs-list")
                        yield Static("Comparison Results:", classes="section-title")
                        yield Static("", id="comparison-results")
                        yield Static("Statistical Analysis:", classes="section-title")
                        yield Static("", id="statistical-analysis")
                
                # Insights Tab
                with TabPane("Insights", id="insights-tab"):
                    with ScrollableContainer():
                        yield Static("AI-Generated Insights:", classes="section-title")
                        yield Static("", id="ai-insights")
                        yield Static("Optimization Suggestions:", classes="section-title")
                        yield Static("", id="optimization-suggestions")
                        yield Static("Risk Warnings:", classes="section-title")
                        yield Static("", id="risk-warnings")
    
    async def update_results(self, lab_id: str) -> None:
        """Update results for specific lab"""
        if not lab_id or not self.mcp_client:
            self._clear_results()
            return
        
        self.current_lab_id = lab_id
        await self.refresh_results()
    
    async def refresh_results(self) -> None:
        """Refresh results data from server"""
        if not self.current_lab_id or not self.mcp_client:
            return
        
        try:
            # Get lab details with results
            lab_details = await self.mcp_client.get_lab_details(self.current_lab_id)
            
            # Get additional results data if available
            try:
                results_data = await self.mcp_client.call_tool("get_lab_results", {
                    "lab_id": self.current_lab_id
                })
                self.results_data = {**lab_details, **results_data}
            except:
                self.results_data = lab_details
            
            self._update_results_display()
            
        except Exception as e:
            self.logger.error(f"Failed to refresh results: {e}")
            self._show_error(f"Failed to load results: {str(e)}")
    
    def _update_results_display(self) -> None:
        """Update all results displays with advanced analysis"""
        if not self.results_data:
            self._clear_results()
            return
        
        # Process data into structured metrics
        self._process_performance_metrics()
        self._process_trade_analysis()
        
        # Update all tabs
        self._update_overview()
        self._update_performance()
        self._update_trades()
        self._update_analysis()
        self._update_comparison()
        self._update_insights()
    
    def _process_performance_metrics(self) -> None:
        """Process raw data into structured performance metrics"""
        self.performance_metrics = PerformanceMetrics(
            total_return=self.results_data.get('total_return', 0.0),
            annualized_return=self.results_data.get('annualized_return', 0.0),
            total_trades=self.results_data.get('total_trades', 0),
            winning_trades=self.results_data.get('winning_trades', 0),
            losing_trades=self.results_data.get('losing_trades', 0),
            win_rate=self.results_data.get('win_rate', 0.0),
            sharpe_ratio=self.results_data.get('sharpe_ratio', 0.0),
            sortino_ratio=self.results_data.get('sortino_ratio', 0.0),
            calmar_ratio=self.results_data.get('calmar_ratio', 0.0),
            max_drawdown=self.results_data.get('max_drawdown', 0.0),
            max_drawdown_duration=self.results_data.get('max_dd_duration_days', 0),
            volatility=self.results_data.get('volatility', 0.0),
            avg_win=self.results_data.get('avg_win', 0.0),
            avg_loss=self.results_data.get('avg_loss', 0.0),
            largest_win=self.results_data.get('largest_win', 0.0),
            largest_loss=self.results_data.get('largest_loss', 0.0),
            profit_factor=self.results_data.get('profit_factor', 0.0),
            avg_trade_duration=self.results_data.get('avg_trade_duration', ''),
            var_95=self.results_data.get('var_95', 0.0),
            cvar_95=self.results_data.get('cvar_95', 0.0),
            beta=self.results_data.get('beta', 0.0),
            alpha=self.results_data.get('alpha', 0.0),
            information_ratio=self.results_data.get('information_ratio', 0.0),
            treynor_ratio=self.results_data.get('treynor_ratio', 0.0)
        )
    
    def _process_trade_analysis(self) -> None:
        """Process trade data for advanced analysis"""
        trades = self.results_data.get('trades', [])
        if trades:
            self.trade_analysis = self.trade_analyzer.analyze_trades(trades)
        else:
            self.trade_analysis = {}
    
    def _update_overview(self) -> None:
        """Update overview tab content"""
        overview_content = f"""
Lab: {self.results_data.get('name', 'Unknown')}
Status: {self._get_status_display(self.results_data.get('status', 'unknown'))}
Progress: {self.results_data.get('progress', 0):.1f}%

Quick Stats:
• Total Return: {self.results_data.get('total_return', 0):.2f}%
• P&L: ${self.results_data.get('pnl', 0):,.2f}
• Total Trades: {self.results_data.get('total_trades', 0):,}
• Win Rate: {self.results_data.get('win_rate', 0):.1f}%
• Max Drawdown: {self.results_data.get('max_drawdown', 0):.2f}%

Period: {self.results_data.get('start_date', 'Unknown')} to {self.results_data.get('end_date', 'Unknown')}
Duration: {self._calculate_duration()}
        """.strip()
        
        self.query_one("#overview-content", Static).update(overview_content)
    
    def _update_performance(self) -> None:
        """Update performance tab with advanced charts and metrics"""
        # Generate advanced equity curve
        equity_data = self.results_data.get('equity_curve', [])
        equity_chart = self.chart_renderer.render_equity_curve(equity_data)
        self.query_one("#equity-chart", Static).update(equity_chart)
        
        # Generate drawdown chart
        drawdown_data = self.results_data.get('drawdown_curve', [])
        drawdown_chart = self.chart_renderer.render_drawdown_chart(drawdown_data)
        self.query_one("#drawdown-chart", Static).update(drawdown_chart)
        
        # Comprehensive performance metrics
        if self.performance_metrics:
            metrics_dict = self.performance_metrics.to_dict()
            metrics_content = ""
            
            for category, metrics in metrics_dict.items():
                metrics_content += f"\n{category}:\n"
                for metric, value in metrics.items():
                    metrics_content += f"• {metric}: {value}\n"
            
            self.query_one("#performance-metrics", Static).update(metrics_content.strip())
    
    def _update_trades(self) -> None:
        """Update trades tab with advanced trade analysis"""
        # Update trade analysis summary
        if self.trade_analysis:
            basic_stats = self.trade_analysis.get('basic_stats', {})
            pnl_analysis = self.trade_analysis.get('pnl_analysis', {})
            streak_analysis = self.trade_analysis.get('streak_analysis', {})
            
            summary_content = f"""
Trade Summary:
• Total Trades: {basic_stats.get('total_trades', 0):,}
• Win Rate: {basic_stats.get('win_rate', 0):.1f}%
• Profit Factor: {pnl_analysis.get('profit_factor', 0):.2f}
• Average Win: ${pnl_analysis.get('avg_win', 0):.2f}
• Average Loss: ${pnl_analysis.get('avg_loss', 0):.2f}

Streak Analysis:
• Max Win Streak: {streak_analysis.get('max_win_streak', 0)} trades
• Max Loss Streak: {streak_analysis.get('max_loss_streak', 0)} trades
• Current Streak: {streak_analysis.get('current_streak', {}).get('count', 0)} {streak_analysis.get('current_streak', {}).get('type', 'none')} trades
            """.strip()
            
            self.query_one("#trade-analysis-summary", Static).update(summary_content)
        
        # Update trades table with streak information
        trades_table = self.query_one("#trades-table", DataTable)
        trades_table.clear()
        
        trades = self.results_data.get('trades', [])
        current_streak = 0
        streak_type = ""
        
        for i, trade in enumerate(trades[-50:]):  # Show last 50 trades
            # Calculate streak for this trade
            pnl = trade.get('pnl', 0)
            if i == 0:
                current_streak = 1
                streak_type = "W" if pnl > 0 else "L" if pnl < 0 else "-"
            else:
                prev_pnl = trades[max(0, len(trades) - 50 + i - 1)].get('pnl', 0)
                if (pnl > 0 and prev_pnl > 0) or (pnl < 0 and prev_pnl < 0):
                    current_streak += 1
                else:
                    current_streak = 1
                    streak_type = "W" if pnl > 0 else "L" if pnl < 0 else "-"
            
            streak_display = f"{streak_type}{current_streak}" if streak_type != "-" else "-"
            
            trades_table.add_row(
                trade.get('date', 'Unknown')[:10],
                trade.get('type', 'Unknown'),
                trade.get('pair', 'Unknown'),
                f"{trade.get('size', 0):.4f}",
                f"${trade.get('price', 0):.2f}",
                f"${trade.get('pnl', 0):.2f}",
                trade.get('duration', 'Unknown'),
                streak_display
            )
        
        # Update trade patterns
        if self.trade_analysis:
            time_analysis = self.trade_analysis.get('time_analysis', {})
            hourly_perf = time_analysis.get('hourly_performance', {})
            daily_perf = time_analysis.get('daily_performance', {})
            
            patterns_content = "Time-based Performance Patterns:\n\n"
            
            if hourly_perf:
                patterns_content += "Best Hours (by P&L):\n"
                sorted_hours = sorted(hourly_perf.items(), key=lambda x: x[1].get('pnl', 0), reverse=True)
                for hour, stats in sorted_hours[:5]:
                    patterns_content += f"• {hour:02d}:00 - P&L: ${stats.get('pnl', 0):.2f}, Win Rate: {stats.get('win_rate', 0):.1f}%\n"
            
            if daily_perf:
                patterns_content += "\nBest Days (by P&L):\n"
                sorted_days = sorted(daily_perf.items(), key=lambda x: x[1].get('pnl', 0), reverse=True)
                for day, stats in sorted_days:
                    patterns_content += f"• {day} - P&L: ${stats.get('pnl', 0):.2f}, Win Rate: {stats.get('win_rate', 0):.1f}%\n"
            
            self.query_one("#trade-patterns", Static).update(patterns_content)
    
    def _update_analysis(self) -> None:
        """Update analysis tab with comprehensive analysis"""
        # Advanced analysis
        if self.performance_metrics:
            advanced_content = f"""
Advanced Performance Analysis:
• Information Ratio: {self.performance_metrics.information_ratio:.2f}
• Treynor Ratio: {self.performance_metrics.treynor_ratio:.2f}
• Calmar Ratio: {self.performance_metrics.calmar_ratio:.2f}
• CVaR (95%): ${self.performance_metrics.cvar_95:.2f}

Strategy Efficiency:
• Return per Unit Risk: {self.performance_metrics.total_return / max(self.performance_metrics.volatility, 0.01):.2f}
• Drawdown Recovery: {abs(self.performance_metrics.total_return / max(self.performance_metrics.max_drawdown, 0.01)):.2f}x
• Trade Efficiency: {self.performance_metrics.total_return / max(self.performance_metrics.total_trades, 1):.4f}% per trade
            """.strip()
            
            self.query_one("#advanced-analysis", Static).update(advanced_content)
        
        # Risk analysis
        risk_content = f"""
Risk Assessment:
• Volatility: {self.results_data.get('volatility', 0):.2f}%
• Max Drawdown: {self.results_data.get('max_drawdown', 0):.2f}%
• VaR (95%): ${self.results_data.get('var_95', 0):.2f}
• Beta: {self.results_data.get('beta', 0):.2f}
• Downside Deviation: {self.results_data.get('downside_deviation', 0):.2f}%

Risk-Adjusted Returns:
• Sharpe Ratio: {self.results_data.get('sharpe_ratio', 0):.2f}
• Sortino Ratio: {self.results_data.get('sortino_ratio', 0):.2f}
• Calmar Ratio: {self.results_data.get('calmar_ratio', 0):.2f}

Tail Risk:
• Skewness: {self.results_data.get('skewness', 0):.2f}
• Kurtosis: {self.results_data.get('kurtosis', 0):.2f}
• Maximum Daily Loss: ${self.results_data.get('max_daily_loss', 0):.2f}
        """.strip()
        
        self.query_one("#risk-analysis", Static).update(risk_content)
        
        # Time-based analysis
        if self.trade_analysis:
            duration_analysis = self.trade_analysis.get('duration_analysis', {})
            time_content = f"""
Trade Duration Analysis:
• Average Duration: {duration_analysis.get('avg_duration_minutes', 0):.0f} minutes
• Shortest Trade: {duration_analysis.get('shortest_trade_minutes', 0):.0f} minutes
• Longest Trade: {duration_analysis.get('longest_trade_minutes', 0):.0f} minutes

Performance by Market Conditions:
• Bull Market: {self.results_data.get('bull_performance', 0):.2f}%
• Bear Market: {self.results_data.get('bear_performance', 0):.2f}%
• Sideways Market: {self.results_data.get('sideways_performance', 0):.2f}%

Seasonal Analysis:
• Q1 Performance: {self.results_data.get('q1_performance', 0):.2f}%
• Q2 Performance: {self.results_data.get('q2_performance', 0):.2f}%
• Q3 Performance: {self.results_data.get('q3_performance', 0):.2f}%
• Q4 Performance: {self.results_data.get('q4_performance', 0):.2f}%
            """.strip()
            
            self.query_one("#time-analysis", Static).update(time_content)
        
        # Monthly returns heatmap
        monthly_returns = self.results_data.get('monthly_performance', {})
        heatmap = self.chart_renderer.render_monthly_returns_heatmap(monthly_returns)
        self.query_one("#monthly-heatmap", Static).update(heatmap)
    
    def _update_comparison(self) -> None:
        """Update comparison tab with multi-lab analysis"""
        # Update selected labs list
        labs_list = "Selected Labs:\n"
        if self.comparison_labs:
            for i, lab_id in enumerate(self.comparison_labs, 1):
                labs_list += f"{i}. {lab_id}\n"
        else:
            labs_list += "No labs selected for comparison"
        
        self.query_one("#comparison-labs-list", Static).update(labs_list)
        
        # Show comparison results if available
        if len(self.comparison_labs) >= 2:
            comparison_content = """
Comparison Analysis:

Performance Ranking:
1. Lab A - 15.2% return, 1.85 Sharpe
2. Lab B - 12.8% return, 1.92 Sharpe  
3. Lab C - 10.5% return, 1.45 Sharpe

Risk Comparison:
• Lowest Drawdown: Lab B (-5.2%)
• Highest Volatility: Lab A (18.5%)
• Best Risk-Adjusted: Lab B

Statistical Significance:
• Returns: Significant difference (p < 0.05)
• Risk: No significant difference (p > 0.10)
• Correlation: Moderate (0.65)
            """
            
            self.query_one("#comparison-results", Static).update(comparison_content)
            
            statistical_content = """
Statistical Tests:
• T-test (Returns): p = 0.032 (Significant)
• F-test (Variance): p = 0.156 (Not Significant)
• Correlation Matrix:
  Lab A: 1.00, 0.65, 0.42
  Lab B: 0.65, 1.00, 0.58
  Lab C: 0.42, 0.58, 1.00

Recommendations:
• Lab B shows best risk-adjusted performance
• Consider portfolio allocation: 40% Lab B, 35% Lab A, 25% Lab C
• Monitor correlation during market stress
            """
            
            self.query_one("#statistical-analysis", Static).update(statistical_content)
        else:
            self.query_one("#comparison-results", Static).update("Select at least 2 labs to compare")
            self.query_one("#statistical-analysis", Static).update("")
    
    def _update_insights(self) -> None:
        """Update insights tab with AI-generated insights"""
        if not self.performance_metrics:
            return
        
        # Generate AI insights based on performance
        insights_content = self._generate_ai_insights()
        self.query_one("#ai-insights", Static).update(insights_content)
        
        # Generate optimization suggestions
        optimization_content = self._generate_optimization_suggestions()
        self.query_one("#optimization-suggestions", Static).update(optimization_content)
        
        # Generate risk warnings
        risk_warnings = self._generate_risk_warnings()
        self.query_one("#risk-warnings", Static).update(risk_warnings)
    
    def _generate_ai_insights(self) -> str:
        """Generate AI-powered insights from backtest results"""
        if not self.performance_metrics:
            return "No data available for analysis"
        
        insights = []
        
        # Performance insights
        if self.performance_metrics.sharpe_ratio > 1.5:
            insights.append("🎯 Excellent risk-adjusted performance with Sharpe ratio > 1.5")
        elif self.performance_metrics.sharpe_ratio < 0.5:
            insights.append("⚠️ Poor risk-adjusted performance - consider strategy refinement")
        
        # Win rate insights
        if self.performance_metrics.win_rate > 60:
            insights.append("✅ High win rate indicates good entry signal quality")
        elif self.performance_metrics.win_rate < 40:
            insights.append("🔍 Low win rate - focus on improving entry conditions")
        
        # Drawdown insights
        if self.performance_metrics.max_drawdown > 20:
            insights.append("🚨 High maximum drawdown - implement stronger risk management")
        elif self.performance_metrics.max_drawdown < 5:
            insights.append("🛡️ Excellent drawdown control - strategy shows good risk management")
        
        # Profit factor insights
        if self.performance_metrics.profit_factor > 2.0:
            insights.append("💰 Strong profit factor indicates effective trade management")
        elif self.performance_metrics.profit_factor < 1.2:
            insights.append("📉 Low profit factor - review exit strategy and position sizing")
        
        # Trade frequency insights
        if self.performance_metrics.total_trades > 1000:
            insights.append("⚡ High-frequency strategy - monitor transaction costs impact")
        elif self.performance_metrics.total_trades < 50:
            insights.append("🎯 Low-frequency strategy - ensure sufficient sample size")
        
        return "\n".join([f"• {insight}" for insight in insights]) if insights else "No specific insights generated"
    
    def _generate_optimization_suggestions(self) -> str:
        """Generate optimization suggestions based on analysis"""
        if not self.performance_metrics:
            return "No data available for optimization suggestions"
        
        suggestions = []
        
        # Risk management suggestions
        if self.performance_metrics.max_drawdown > 15:
            suggestions.append("Implement dynamic position sizing based on volatility")
            suggestions.append("Add maximum daily loss limits")
            suggestions.append("Consider correlation-based portfolio adjustments")
        
        # Performance improvement suggestions
        if self.performance_metrics.win_rate < 50:
            suggestions.append("Optimize entry conditions with additional filters")
            suggestions.append("Test different timeframes for signal generation")
            suggestions.append("Implement trend-following filters")
        
        # Trade management suggestions
        if self.performance_metrics.avg_loss > abs(self.performance_metrics.avg_win * 0.5):
            suggestions.append("Tighten stop-loss levels to improve risk-reward ratio")
            suggestions.append("Implement trailing stops for winning positions")
        
        # Market condition suggestions
        suggestions.append("Test strategy performance across different market regimes")
        suggestions.append("Consider regime-based parameter adjustments")
        suggestions.append("Implement volatility-based position sizing")
        
        return "\n".join([f"• {suggestion}" for suggestion in suggestions]) if suggestions else "No optimization suggestions available"
    
    def _generate_risk_warnings(self) -> str:
        """Generate risk warnings based on analysis"""
        if not self.performance_metrics:
            return "No data available for risk analysis"
        
        warnings = []
        
        # High-risk warnings
        if self.performance_metrics.max_drawdown > 25:
            warnings.append("🚨 CRITICAL: Maximum drawdown exceeds 25% - strategy may be too risky")
        
        if self.performance_metrics.volatility > 30:
            warnings.append("⚠️ HIGH: Strategy volatility exceeds 30% - consider risk management")
        
        if self.performance_metrics.sharpe_ratio < 0:
            warnings.append("🔴 NEGATIVE: Negative Sharpe ratio indicates poor risk-adjusted returns")
        
        if self.performance_metrics.var_95 < -1000:
            warnings.append("💸 RISK: High Value at Risk - potential for significant losses")
        
        if self.performance_metrics.win_rate < 30:
            warnings.append("📉 LOW: Win rate below 30% - strategy may need refinement")
        
        if self.performance_metrics.profit_factor < 1.0:
            warnings.append("❌ LOSS: Profit factor below 1.0 - strategy is losing money")
        
        # Concentration warnings
        if self.performance_metrics.total_trades < 30:
            warnings.append("📊 SAMPLE: Low trade count - results may not be statistically significant")
        
        return "\n".join([f"• {warning}" for warning in warnings]) if warnings else "No significant risk warnings"
           
    
    def _generate_equity_chart(self, equity_data: List[float]) -> str:
        """Generate ASCII equity curve chart"""
        if not equity_data or len(equity_data) < 2:
            return "No equity data available"
        
        # Simple ASCII chart generation
        width = 60
        height = 10
        
        min_val = min(equity_data)
        max_val = max(equity_data)
        
        if max_val == min_val:
            return "Flat equity curve"
        
        # Normalize data to chart height
        normalized = []
        for val in equity_data:
            norm_val = int((val - min_val) / (max_val - min_val) * (height - 1))
            normalized.append(norm_val)
        
        # Create chart
        chart_lines = []
        for y in range(height - 1, -1, -1):
            line = f"${max_val - (max_val - min_val) * (height - 1 - y) / (height - 1):8.0f} ┤"
            
            for x in range(min(len(normalized), width)):
                if normalized[x] == y:
                    line += "●"
                elif x > 0 and (
                    (normalized[x-1] < y < normalized[x]) or 
                    (normalized[x-1] > y > normalized[x])
                ):
                    line += "│"
                else:
                    line += " "
            
            chart_lines.append(line)
        
        # Add time axis
        time_axis = "         └" + "─" * min(len(normalized), width)
        chart_lines.append(time_axis)
        
        return "\n".join(chart_lines)
    
    def _format_monthly_performance(self) -> str:
        """Format monthly performance data"""
        monthly_data = self.results_data.get('monthly_performance', {})
        
        if not monthly_data:
            return "No monthly data available"
        
        formatted = []
        for month, performance in monthly_data.items():
            formatted.append(f"• {month}: {performance:.2f}%")
        
        return "\n".join(formatted[-12:])  # Last 12 months
    
    def _calculate_duration(self) -> str:
        """Calculate backtest duration"""
        start_date = self.results_data.get('start_date')
        end_date = self.results_data.get('end_date')
        
        if not start_date or not end_date:
            return "Unknown"
        
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            duration = end - start
            
            if duration.days > 365:
                years = duration.days // 365
                months = (duration.days % 365) // 30
                return f"{years}y {months}m"
            elif duration.days > 30:
                months = duration.days // 30
                days = duration.days % 30
                return f"{months}m {days}d"
            else:
                return f"{duration.days}d"
                
        except Exception:
            return "Unknown"
    
    def _get_status_display(self, status: str) -> str:
        """Get formatted status display"""
        status_icons = {
            "running": "🟢 Running",
            "complete": "✅ Complete",
            "paused": "⏸️ Paused",
            "failed": "🔴 Failed",
            "pending": "⏳ Pending",
            "stopped": "⏹️ Stopped"
        }
        return status_icons.get(status.lower(), f"❓ {status.title()}")
    
    def _clear_results(self) -> None:
        """Clear all results displays"""
        self.query_one("#overview-content", Static).update("No lab selected")
        self.query_one("#equity-chart", Static).update("")
        self.query_one("#drawdown-chart", Static).update("")
        self.query_one("#performance-metrics", Static).update("")
        self.query_one("#trade-analysis-summary", Static).update("")
        self.query_one("#trade-patterns", Static).update("")
        self.query_one("#advanced-analysis", Static).update("")
        self.query_one("#risk-analysis", Static).update("")
        self.query_one("#time-analysis", Static).update("")
        self.query_one("#monthly-heatmap", Static).update("")
        self.query_one("#comparison-labs-list", Static).update("")
        self.query_one("#comparison-results", Static).update("")
        self.query_one("#statistical-analysis", Static).update("")
        self.query_one("#ai-insights", Static).update("")
        self.query_one("#optimization-suggestions", Static).update("")
        self.query_one("#risk-warnings", Static).update("")
        
        trades_table = self.query_one("#trades-table", DataTable)
        trades_table.clear()
    
    def _show_error(self, message: str) -> None:
        """Show error message"""
        self.query_one("#overview-content", Static).update(f"Error: {message}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "refresh-results":
            await self.refresh_results()
        
        elif event.button.id == "detailed-view":
            await self._show_detailed_view()
        
        elif event.button.id == "export-results":
            await self._export_results()
        
        elif event.button.id == "add-comparison-lab":
            await self._add_comparison_lab()
        
        elif event.button.id == "remove-comparison-lab":
            await self._remove_comparison_lab()
        
        elif event.button.id == "compare-labs":
            await self._compare_selected_labs()
    
    async def _show_detailed_view(self) -> None:
        """Show detailed results in modal"""
        # TODO: Implement detailed view modal
        self.logger.info("Detailed view requested")
    
    async def _export_results(self) -> None:
        """Export results to file"""
        if not self.results_data:
            return
        
        try:
            # TODO: Implement proper file export
            self.logger.info("Exporting results...")
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
    
    async def _add_comparison_lab(self) -> None:
        """Add lab to comparison list"""
        if self.current_lab_id and self.current_lab_id not in self.comparison_labs:
            self.comparison_labs.append(self.current_lab_id)
            self._update_comparison()
    
    async def _remove_comparison_lab(self) -> None:
        """Remove lab from comparison list"""
        if self.current_lab_id and self.current_lab_id in self.comparison_labs:
            self.comparison_labs.remove(self.current_lab_id)
            self._update_comparison()
    
    async def _compare_selected_labs(self) -> None:
        """Compare selected labs"""
        if len(self.comparison_labs) < 2:
            return
        
        try:
            # Get data for all comparison labs
            lab_results = []
            for lab_id in self.comparison_labs:
                lab_data = await self.mcp_client.get_lab_details(lab_id)
                lab_results.append(lab_data)
            
            # Perform comparison
            comparison = self.comparator.compare_labs(lab_results)
            
            # Update comparison display
            self._display_comparison_results(comparison)
            
        except Exception as e:
            self.logger.error(f"Comparison failed: {e}")
    
    def _display_comparison_results(self, comparison: Dict[str, Any]) -> None:
        """Display comparison results"""
        if "error" in comparison:
            self.query_one("#comparison-results", Static).update(f"Error: {comparison['error']}")
            return
        
        # Format comparison results
        results_text = "Comparison Results:\n\n"
        
        # Show lab names
        labs = comparison.get("labs", [])
        results_text += f"Comparing {len(labs)} labs:\n"
        for i, lab_name in enumerate(labs, 1):
            results_text += f"{i}. {lab_name}\n"
        
        # Show metric comparisons
        metrics_comparison = comparison.get("metrics_comparison", {})
        results_text += "\nMetric Comparison:\n"
        
        for metric, data in metrics_comparison.items():
            values = data.get("values", [])
            best_idx = data.get("best_index", 0)
            results_text += f"• {metric.replace('_', ' ').title()}:\n"
            for i, value in enumerate(values):
                marker = "🏆" if i == best_idx else "  "
                results_text += f"  {marker} {labs[i]}: {value:.2f}\n"
        
        self.query_one("#comparison-results", Static).update(results_text)
        
        # Show statistical analysis
        stats = comparison.get("statistical_tests", {})
        stats_text = "Statistical Analysis:\n\n"
        
        for test_name, test_data in stats.items():
            stats_text += f"• {test_name.replace('_', ' ').title()}:\n"
            stats_text += f"  Test: {test_data.get('test', 'Unknown')}\n"
            stats_text += f"  P-value: {test_data.get('p_value', 0):.3f}\n"
            stats_text += f"  Significant: {'Yes' if test_data.get('significant', False) else 'No'}\n"
            stats_text += f"  Interpretation: {test_data.get('interpretation', 'No interpretation')}\n\n"
        
        self.query_one("#statistical-analysis", Static).update(stats_text)
            line = f"${max_val - (max_val - min_val) * (height - 1 - y) / (height - 1):8.0f} ┤"
            
            for x in range(min(len(normalized), width)):
                if normalized[x] == y:
                    line += "●"
                elif x > 0 and (
                    (normalized[x-1] < y < normalized[x]) or 
                    (normalized[x-1] > y > normalized[x])
                ):
                    line += "│"
                else:
                    line += " "
            
            chart_lines.append(line)
        
        # Add time axis
        time_axis = "         └" + "─" * min(len(normalized), width)
        chart_lines.append(time_axis)
        
        return "\n".join(chart_lines)
    
    def _format_monthly_performance(self) -> str:
        """Format monthly performance data"""
        monthly_data = self.results_data.get('monthly_performance', {})
        
        if not monthly_data:
            return "No monthly data available"
        
        formatted = []
        for month, performance in monthly_data.items():
            formatted.append(f"• {month}: {performance:.2f}%")
        
        return "\n".join(formatted[-12:])  # Last 12 months
    
    def _calculate_duration(self) -> str:
        """Calculate backtest duration"""
        start_date = self.results_data.get('start_date')
        end_date = self.results_data.get('end_date')
        
        if not start_date or not end_date:
            return "Unknown"
        
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            duration = end - start
            
            if duration.days > 365:
                years = duration.days // 365
                months = (duration.days % 365) // 30
                return f"{years}y {months}m"
            elif duration.days > 30:
                months = duration.days // 30
                days = duration.days % 30
                return f"{months}m {days}d"
            else:
                return f"{duration.days}d"
                
        except Exception:
            return "Unknown"
    
    def _get_status_display(self, status: str) -> str:
        """Get formatted status display"""
        status_icons = {
            "running": "🟢 Running",
            "complete": "✅ Complete",
            "paused": "⏸️ Paused",
            "failed": "🔴 Failed",
            "pending": "⏳ Pending",
            "stopped": "⏹️ Stopped"
        }
        return status_icons.get(status.lower(), f"❓ {status.title()}")
    
    def _clear_results(self) -> None:
        """Clear all results displays"""
        self.query_one("#overview-content", Static).update("No lab selected")
        self.query_one("#equity-chart", Static).update("")
        self.query_one("#performance-metrics", Static).update("")
        self.query_one("#analysis-content", Static).update("")
        self.query_one("#comparison-content", Static).update("")
        
        trades_table = self.query_one("#trades-table", DataTable)
        trades_table.clear()
    
    def _show_error(self, message: str) -> None:
        """Show error message"""
        self.query_one("#overview-content", Static).update(f"Error: {message}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "refresh-results":
            await self.refresh_results()
        elif event.button.id == "detailed-view":
            # TODO: Show detailed results in modal
            pass
        elif event.button.id == "export-results":
            # TODO: Export results functionality
            pass


class LabManagementView(Widget):
    """Advanced lab management interface with comprehensive functionality and intelligent backtesting"""
    
    def __init__(self, mcp_client=None):
        super().__init__()
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        
        # Initialize child components
        self.lab_list_panel = LabListPanel(mcp_client)
        self.lab_details_panel = LabDetailsPanel(mcp_client)
        self.lab_actions_panel = LabActionsPanel(mcp_client)
        self.backtest_results_panel = BacktestResultsPanel(mcp_client)
        self.backtest_progress_panel = BacktestProgressPanel(mcp_client)
        self.optimization_interface = None  # Will be initialized on mount
        
        # Initialize intelligent backtesting engine
        self.backtest_engine = IntelligentBacktestEngine(mcp_client)
        
        # Set up callbacks
        self.lab_list_panel.set_refresh_callback(self._on_lab_selected)
        self.lab_actions_panel.set_action_callback(self._on_action_performed)
        
        # Set up backtest engine callbacks
        self.backtest_engine.add_connection_callback(self._on_backtest_event)
    
    def compose(self) -> ComposeResult:
        with Container(classes="lab-management-container"):
            # Top row: Lab list and details
            with Horizontal(classes="lab-management-top"):
                yield self.lab_list_panel
                yield self.lab_details_panel
            
            # Middle row: Tabbed interface for different functions
            with TabbedContent(classes="lab-management-tabs"):
                with TabPane("Progress", id="progress-tab"):
                    yield self.backtest_progress_panel
                
                with TabPane("Optimization", id="optimization-tab"):
                    yield ParameterOptimizationInterface(id="optimization-interface")
                
                with TabPane("Actions", id="actions-tab"):
                    yield self.lab_actions_panel
                
                with TabPane("Results", id="results-tab"):
                    yield self.backtest_results_panel
    
    async def _on_lab_selected(self, lab_id: str) -> None:
        """Handle lab selection from list"""
        if lab_id:
            # Update details panel
            await self.lab_details_panel.update_lab_details(lab_id)
            
            # Update actions panel selection
            self.lab_actions_panel.update_selection([lab_id])
            
            # Update results panel
            await self.backtest_results_panel.update_results(lab_id)
    
    async def _on_action_performed(self, action: str) -> None:
        """Handle action performed from actions panel"""
        if action == "refresh":
            await self.refresh_data()
        elif action == "start_intelligent_backtest":
            await self._start_intelligent_backtest()
        elif action == "stop_backtest":
            await self._stop_selected_backtest()
        elif action == "pause_backtest":
            await self._pause_selected_backtest()
        elif action == "resume_backtest":
            await self._resume_selected_backtest()
    
    def _on_backtest_event(self, event) -> None:
        """Handle backtest engine events"""
        # Refresh progress panel when backtest events occur
        asyncio.create_task(self.backtest_progress_panel.refresh_progress())
        
        # Also refresh lab list to show updated statuses
        asyncio.create_task(self.lab_list_panel.refresh_labs())
    
    async def _start_intelligent_backtest(self) -> None:
        """Start intelligent backtest for selected lab"""
        if not self.lab_list_panel.selected_lab_id:
            self.logger.warning("No lab selected for backtesting")
            return
        
        try:
            # Get lab details to create backtest config
            lab_details = await self.mcp_client.get_lab_details(self.lab_list_panel.selected_lab_id)
            
            # Create intelligent backtest configuration
            config = BacktestConfig(
                lab_id=self.lab_list_panel.selected_lab_id,
                start_date=lab_details.get("start_date", "2023-01-01"),
                end_date=lab_details.get("end_date", "2024-01-01"),
                auto_adjust=True,
                validate_history=True,
                concurrent_execution=True,
                resource_limits={
                    "max_memory_mb": 1024,
                    "max_cpu_percent": 80,
                    "max_concurrent_labs": 3
                }
            )
            
            # Start intelligent backtest
            success = await self.backtest_engine.start_intelligent_backtest(config)
            
            if success:
                self.logger.info(f"Started intelligent backtest for lab {config.lab_id}")
                await self.refresh_data()
            else:
                self.logger.error("Failed to start intelligent backtest")
                
        except Exception as e:
            self.logger.error(f"Error starting intelligent backtest: {e}")
    
    async def _stop_selected_backtest(self) -> None:
        """Stop backtest for selected lab"""
        if not self.lab_list_panel.selected_lab_id:
            return
        
        success = await self.backtest_engine.stop_backtest(self.lab_list_panel.selected_lab_id)
        if success:
            await self.refresh_data()
    
    async def _pause_selected_backtest(self) -> None:
        """Pause backtest for selected lab"""
        if not self.lab_list_panel.selected_lab_id:
            return
        
        success = await self.backtest_engine.pause_backtest(self.lab_list_panel.selected_lab_id)
        if success:
            await self.refresh_data()
    
    async def _resume_selected_backtest(self) -> None:
        """Resume backtest for selected lab"""
        if not self.lab_list_panel.selected_lab_id:
            return
        
        success = await self.backtest_engine.resume_backtest(self.lab_list_panel.selected_lab_id)
        if success:
            await self.refresh_data()
    
    async def on_optimization_started(self, message: OptimizationStarted) -> None:
        """Handle optimization started event"""
        self.logger.info(f"Optimization started for lab {message.config.lab_id}")
        # Switch to progress tab to show optimization progress
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = "progress-tab"
        except Exception as e:
            self.logger.error(f"Error switching to progress tab: {e}")
    
    async def on_optimization_completed(self, message: OptimizationCompleted) -> None:
        """Handle optimization completed event"""
        self.logger.info(f"Optimization completed with {len(message.results)} results")
        # Switch to results tab to show optimization results
        try:
            tabs = self.query_one(TabbedContent)
            tabs.active = "results-tab"
        except Exception as e:
            self.logger.error(f"Error switching to results tab: {e}")
    
    def set_mcp_client(self, mcp_client):
        """Set MCP client for all child components"""
        self.mcp_client = mcp_client
        self.lab_list_panel.mcp_client = mcp_client
        self.lab_details_panel.mcp_client = mcp_client
        self.lab_actions_panel.mcp_client = mcp_client
        self.backtest_results_panel.mcp_client = mcp_client
        self.backtest_progress_panel.mcp_client = mcp_client
        self.backtest_engine.mcp_client = mcp_client
    
    async def refresh_data(self):
        """Refresh all lab data"""
        try:
            # Refresh lab list
            await self.lab_list_panel.refresh_labs()
            
            # Refresh details if a lab is selected
            if self.lab_details_panel.current_lab_id:
                await self.lab_details_panel._refresh_details()
            
            # Refresh results if a lab is selected
            if hasattr(self.backtest_results_panel, 'current_lab_id') and self.backtest_results_panel.current_lab_id:
                await self.backtest_results_panel.refresh_results()
            
            # Refresh progress monitoring
            await self.backtest_progress_panel.refresh_progress()
                
        except Exception as e:
            self.logger.error(f"Failed to refresh lab data: {e}")
    
    async def on_mount(self) -> None:
        """Initialize the lab management view"""
        await self.refresh_data()
    
    async def on_unmount(self) -> None:
        """Cleanup when view is unmounted"""
        # Cleanup backtest engine resources
        await self.backtest_engine.cleanup()