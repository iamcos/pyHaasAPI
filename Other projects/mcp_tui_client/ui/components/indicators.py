"""
Indicator Components

Status and progress indicators for real-time feedback.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

from textual.widget import Widget
from textual.widgets import Static, Label, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.timer import Timer


class IndicatorStatus(Enum):
    """Status levels for indicators"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    NEUTRAL = "neutral"


class StatusIndicator(Container):
    """Visual status indicator with color coding"""
    
    DEFAULT_CSS = """
    StatusIndicator {
        height: 1;
        width: auto;
        layout: horizontal;
        align: center middle;
    }
    
    StatusIndicator .status-icon {
        width: 3;
        text-align: center;
    }
    
    StatusIndicator .status-text {
        width: 1fr;
        margin: 0 1;
    }
    
    StatusIndicator.success .status-icon {
        color: $success;
    }
    
    StatusIndicator.warning .status-icon {
        color: $warning;
    }
    
    StatusIndicator.error .status-icon {
        color: $error;
    }
    
    StatusIndicator.info .status-icon {
        color: $info;
    }
    
    StatusIndicator.neutral .status-icon {
        color: $text-muted;
    }
    """
    
    status = reactive(IndicatorStatus.NEUTRAL)
    text = reactive("")
    
    def __init__(
        self,
        status: IndicatorStatus = IndicatorStatus.NEUTRAL,
        text: str = "",
        show_icon: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.status = status
        self.text = text
        self.show_icon = show_icon
        self.status_icons = {
            IndicatorStatus.SUCCESS: "✓",
            IndicatorStatus.WARNING: "⚠",
            IndicatorStatus.ERROR: "✗",
            IndicatorStatus.INFO: "ℹ",
            IndicatorStatus.NEUTRAL: "○"
        }
    
    def compose(self) -> ComposeResult:
        """Compose status indicator"""
        if self.show_icon:
            yield Label(
                self.status_icons[self.status],
                classes="status-icon",
                id="status-icon"
            )
        yield Label(self.text, classes="status-text", id="status-text")
    
    def set_status(self, status: IndicatorStatus, text: str = None) -> None:
        """Update status and optional text"""
        self.status = status
        if text is not None:
            self.text = text
    
    def watch_status(self, new_status: IndicatorStatus) -> None:
        """React to status changes"""
        # Update CSS class
        for status_type in IndicatorStatus:
            self.remove_class(status_type.value)
        self.add_class(new_status.value)
        
        # Update icon
        if self.show_icon:
            try:
                icon_label = self.query_one("#status-icon", Label)
                icon_label.update(self.status_icons[new_status])
            except:
                pass
    
    def watch_text(self, new_text: str) -> None:
        """React to text changes"""
        try:
            text_label = self.query_one("#status-text", Label)
            text_label.update(new_text)
        except:
            pass


class ProgressIndicator(Container):
    """Progress indicator with percentage and optional ETA"""
    
    DEFAULT_CSS = """
    ProgressIndicator {
        height: 4;
        width: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    ProgressIndicator .progress-header {
        dock: top;
        height: 1;
        layout: horizontal;
    }
    
    ProgressIndicator .progress-title {
        width: 1fr;
    }
    
    ProgressIndicator .progress-percentage {
        width: auto;
    }
    
    ProgressIndicator .progress-bar {
        height: 1;
        margin: 1 0;
    }
    
    ProgressIndicator .progress-footer {
        dock: bottom;
        height: 1;
        layout: horizontal;
        color: $text-muted;
    }
    
    ProgressIndicator .progress-eta {
        width: 1fr;
    }
    
    ProgressIndicator .progress-speed {
        width: auto;
    }
    """
    
    progress = reactive(0.0)  # 0.0 to 1.0
    title = reactive("")
    
    def __init__(
        self,
        title: str = "Progress",
        show_percentage: bool = True,
        show_eta: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.show_percentage = show_percentage
        self.show_eta = show_eta
        self.start_time: Optional[datetime] = None
        self.estimated_total: Optional[float] = None
    
    def compose(self) -> ComposeResult:
        """Compose progress indicator"""
        # Header with title and percentage
        header = Horizontal(classes="progress-header")
        header.mount(Label(self.title, classes="progress-title", id="progress-title"))
        if self.show_percentage:
            header.mount(Label("0%", classes="progress-percentage", id="progress-percentage"))
        yield header
        
        # Progress bar
        yield ProgressBar(
            total=100,
            show_percentage=False,
            classes="progress-bar",
            id="progress-bar"
        )
        
        # Footer with ETA and speed
        if self.show_eta:
            footer = Horizontal(classes="progress-footer")
            footer.mount(Label("", classes="progress-eta", id="progress-eta"))
            footer.mount(Label("", classes="progress-speed", id="progress-speed"))
            yield footer
    
    def start_progress(self, estimated_total: float = None) -> None:
        """Start progress tracking"""
        self.start_time = datetime.now()
        self.estimated_total = estimated_total
        self.progress = 0.0
    
    def update_progress(self, current: float, total: float = None) -> None:
        """Update progress value"""
        if total:
            self.progress = min(current / total, 1.0)
        else:
            self.progress = min(current, 1.0)
        
        self._update_eta()
    
    def set_progress(self, progress: float) -> None:
        """Set progress directly (0.0 to 1.0)"""
        self.progress = max(0.0, min(progress, 1.0))
        self._update_eta()
    
    def complete_progress(self) -> None:
        """Mark progress as complete"""
        self.progress = 1.0
        self._update_eta()
    
    def _update_eta(self) -> None:
        """Update ETA calculation"""
        if not self.show_eta or not self.start_time or self.progress <= 0:
            return
        
        try:
            elapsed = datetime.now() - self.start_time
            if self.progress < 1.0:
                estimated_total_time = elapsed / self.progress
                remaining_time = estimated_total_time - elapsed
                
                eta_label = self.query_one("#progress-eta", Label)
                speed_label = self.query_one("#progress-speed", Label)
                
                # Format remaining time
                if remaining_time.total_seconds() > 3600:
                    eta_text = f"ETA: {remaining_time.total_seconds()/3600:.1f}h"
                elif remaining_time.total_seconds() > 60:
                    eta_text = f"ETA: {remaining_time.total_seconds()/60:.1f}m"
                else:
                    eta_text = f"ETA: {remaining_time.total_seconds():.0f}s"
                
                eta_label.update(eta_text)
                
                # Calculate speed (progress per second)
                speed = self.progress / elapsed.total_seconds()
                speed_label.update(f"{speed*100:.1f}%/s")
            else:
                # Completed
                eta_label = self.query_one("#progress-eta", Label)
                speed_label = self.query_one("#progress-speed", Label)
                eta_label.update("Completed")
                speed_label.update(f"Total: {elapsed.total_seconds():.1f}s")
        except:
            pass
    
    def watch_progress(self, new_progress: float) -> None:
        """React to progress changes"""
        try:
            # Update progress bar
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.progress = int(new_progress * 100)
            
            # Update percentage
            if self.show_percentage:
                percentage_label = self.query_one("#progress-percentage", Label)
                percentage_label.update(f"{new_progress*100:.1f}%")
        except:
            pass
    
    def watch_title(self, new_title: str) -> None:
        """React to title changes"""
        try:
            title_label = self.query_one("#progress-title", Label)
            title_label.update(new_title)
        except:
            pass


class ConnectionIndicator(StatusIndicator):
    """Connection status indicator with auto-refresh"""
    
    def __init__(
        self,
        connection_name: str = "Connection",
        check_callback: Optional[callable] = None,
        check_interval: int = 30,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.connection_name = connection_name
        self.check_callback = check_callback
        self.check_interval = check_interval
        self.last_check: Optional[datetime] = None
        self.check_timer: Optional[Timer] = None
        
        # Set initial status
        self.set_status(IndicatorStatus.NEUTRAL, f"{connection_name}: Checking...")
    
    async def on_mount(self) -> None:
        """Start connection monitoring"""
        if self.check_callback:
            await self.check_connection()
            self.check_timer = self.set_interval(self.check_interval, self.check_connection)
    
    async def check_connection(self) -> None:
        """Check connection status"""
        if not self.check_callback:
            return
        
        try:
            is_connected = await self.check_callback()
            self.last_check = datetime.now()
            
            if is_connected:
                self.set_status(
                    IndicatorStatus.SUCCESS,
                    f"{self.connection_name}: Connected"
                )
            else:
                self.set_status(
                    IndicatorStatus.ERROR,
                    f"{self.connection_name}: Disconnected"
                )
        except Exception as e:
            self.set_status(
                IndicatorStatus.ERROR,
                f"{self.connection_name}: Error - {str(e)[:30]}"
            )
    
    def on_unmount(self) -> None:
        """Clean up timer"""
        if self.check_timer:
            self.check_timer.stop()


class PerformanceIndicator(Container):
    """Performance metrics indicator"""
    
    DEFAULT_CSS = """
    PerformanceIndicator {
        height: 6;
        width: 1fr;
        border: solid $accent;
        padding: 1;
    }
    
    PerformanceIndicator .perf-title {
        dock: top;
        height: 1;
        text-align: center;
        text-style: bold;
    }
    
    PerformanceIndicator .perf-metrics {
        height: 1fr;
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
    }
    
    PerformanceIndicator .perf-metric {
        text-align: center;
        border: solid $surface;
        padding: 0 1;
    }
    
    PerformanceIndicator .metric-value {
        text-style: bold;
        color: $success;
    }
    
    PerformanceIndicator .metric-value.negative {
        color: $error;
    }
    
    PerformanceIndicator .metric-label {
        color: $text-muted;
    }
    """
    
    def __init__(self, title: str = "Performance", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.metrics: Dict[str, float] = {}
    
    def compose(self) -> ComposeResult:
        """Compose performance indicator"""
        yield Label(self.title, classes="perf-title")
        yield Container(classes="perf-metrics", id="perf-metrics")
    
    def set_metrics(self, metrics: Dict[str, float]) -> None:
        """Set performance metrics"""
        self.metrics = metrics
        self._update_display()
    
    def update_metric(self, name: str, value: float) -> None:
        """Update a single metric"""
        self.metrics[name] = value
        self._update_display()
    
    def _update_display(self) -> None:
        """Update metrics display"""
        try:
            metrics_container = self.query_one("#perf-metrics")
            metrics_container.remove_children()
            
            for name, value in self.metrics.items():
                metric_container = Vertical(classes="perf-metric")
                
                # Value
                value_label = Label(
                    self._format_metric_value(value),
                    classes="metric-value"
                )
                if value < 0:
                    value_label.add_class("negative")
                
                # Label
                label_label = Label(name, classes="metric-label")
                
                metric_container.mount(value_label)
                metric_container.mount(label_label)
                metrics_container.mount(metric_container)
        except:
            pass
    
    def _format_metric_value(self, value: float) -> str:
        """Format metric value for display"""
        if abs(value) >= 1000000:
            return f"{value/1000000:.1f}M"
        elif abs(value) >= 1000:
            return f"{value/1000:.1f}K"
        elif abs(value) >= 1:
            return f"{value:.2f}"
        else:
            return f"{value:.4f}"


class LoadingIndicator(Container):
    """Animated loading indicator"""
    
    DEFAULT_CSS = """
    LoadingIndicator {
        height: 3;
        width: 1fr;
        align: center middle;
    }
    
    LoadingIndicator .loading-spinner {
        width: auto;
        text-align: center;
    }
    
    LoadingIndicator .loading-text {
        width: 1fr;
        text-align: center;
        margin: 1 0 0 0;
    }
    """
    
    def __init__(self, text: str = "Loading...", **kwargs):
        super().__init__(**kwargs)
        self.loading_text = text
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        """Compose loading indicator"""
        yield Label(self.spinner_chars[0], classes="loading-spinner", id="spinner")
        yield Label(self.loading_text, classes="loading-text", id="loading-text")
    
    async def on_mount(self) -> None:
        """Start spinner animation"""
        self.spinner_timer = self.set_interval(0.1, self._update_spinner)
    
    def _update_spinner(self) -> None:
        """Update spinner animation"""
        try:
            spinner_label = self.query_one("#spinner", Label)
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            spinner_label.update(self.spinner_chars[self.spinner_index])
        except:
            pass
    
    def set_text(self, text: str) -> None:
        """Update loading text"""
        self.loading_text = text
        try:
            text_label = self.query_one("#loading-text", Label)
            text_label.update(text)
        except:
            pass
    
    def on_unmount(self) -> None:
        """Clean up timer"""
        if self.spinner_timer:
            self.spinner_timer.stop()


class AlertIndicator(Container):
    """Alert indicator with auto-dismiss"""
    
    DEFAULT_CSS = """
    AlertIndicator {
        height: 3;
        width: 1fr;
        border: solid $warning;
        background: $warning 20%;
        padding: 1;
        margin: 1 0;
    }
    
    AlertIndicator.error {
        border: solid $error;
        background: $error 20%;
    }
    
    AlertIndicator.success {
        border: solid $success;
        background: $success 20%;
    }
    
    AlertIndicator.info {
        border: solid $info;
        background: $info 20%;
    }
    
    AlertIndicator .alert-content {
        layout: horizontal;
        align: center middle;
    }
    
    AlertIndicator .alert-icon {
        width: 3;
        text-align: center;
    }
    
    AlertIndicator .alert-message {
        width: 1fr;
        margin: 0 1;
    }
    
    AlertIndicator .alert-close {
        width: 3;
        text-align: center;
    }
    """
    
    def __init__(
        self,
        message: str,
        alert_type: IndicatorStatus = IndicatorStatus.WARNING,
        auto_dismiss: bool = True,
        dismiss_timeout: int = 5,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.message = message
        self.alert_type = alert_type
        self.auto_dismiss = auto_dismiss
        self.dismiss_timeout = dismiss_timeout
        self.dismiss_timer: Optional[Timer] = None
        
        self.add_class(alert_type.value)
    
    def compose(self) -> ComposeResult:
        """Compose alert indicator"""
        content = Horizontal(classes="alert-content")
        
        # Icon
        icons = {
            IndicatorStatus.SUCCESS: "✓",
            IndicatorStatus.WARNING: "⚠",
            IndicatorStatus.ERROR: "✗",
            IndicatorStatus.INFO: "ℹ",
        }
        icon = icons.get(self.alert_type, "!")
        content.mount(Label(icon, classes="alert-icon"))
        
        # Message
        content.mount(Label(self.message, classes="alert-message"))
        
        # Close button
        content.mount(Label("×", classes="alert-close", id="close-button"))
        
        yield content
    
    async def on_mount(self) -> None:
        """Start auto-dismiss timer"""
        if self.auto_dismiss:
            self.dismiss_timer = self.set_timer(self.dismiss_timeout, self.dismiss)
    
    async def on_click(self) -> None:
        """Handle click to dismiss"""
        await self.dismiss()
    
    async def dismiss(self) -> None:
        """Dismiss the alert"""
        if self.dismiss_timer:
            self.dismiss_timer.stop()
        await self.remove()
    
    def on_unmount(self) -> None:
        """Clean up timer"""
        if self.dismiss_timer:
            self.dismiss_timer.stop()