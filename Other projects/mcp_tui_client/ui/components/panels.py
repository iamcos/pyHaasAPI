"""
Panel Components

Reusable panel components with different layouts and purposes.
"""

from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from textual.widget import Widget
from textual.widgets import Static, Label, Button, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult


class BasePanel(Container):
    """Base panel with common functionality"""
    
    DEFAULT_CSS = """
    BasePanel {
        border: solid $primary;
        padding: 1;
        margin: 1;
    }
    
    BasePanel > .panel-header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        text-align: center;
        content-align: center middle;
    }
    
    BasePanel > .panel-content {
        padding: 1;
    }
    
    BasePanel > .panel-footer {
        dock: bottom;
        height: 1;
        background: $surface;
    }
    """
    
    title = reactive("")
    status = reactive("normal")  # normal, warning, error, success
    
    def __init__(
        self,
        title: str = "",
        show_header: bool = True,
        show_footer: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        # Set attributes before setting reactive properties
        self.show_header = show_header
        self.show_footer = show_footer
        self.last_updated = datetime.now()
        # Set reactive property last
        self.title = title
    
    def compose(self) -> ComposeResult:
        """Compose the panel layout"""
        if self.show_header:
            yield Label(self.title, classes="panel-header")
        
        yield Container(classes="panel-content", id="panel-content")
        
        if self.show_footer:
            yield Container(classes="panel-footer", id="panel-footer")
    
    def update_content(self, content: Widget) -> None:
        """Update panel content"""
        content_container = self.query_one("#panel-content")
        content_container.remove_children()
        content_container.mount(content)
        self.last_updated = datetime.now()
    
    def set_status(self, status: str, message: str = "") -> None:
        """Set panel status with optional message"""
        self.status = status
        if message and self.show_footer:
            try:
                footer = self.query_one("#panel-footer")
                footer.remove_children()
                footer.mount(Label(message))
            except Exception:
                # Footer not available, ignore
                pass
    
    def watch_title(self, new_title: str) -> None:
        """React to title changes"""
        if self.show_header:
            try:
                header = self.query_one(".panel-header", Label)
                header.update(new_title)
            except:
                # Widget not composed yet, ignore
                pass
    
    def watch_status(self, new_status: str) -> None:
        """React to status changes"""
        try:
            # Update panel styling based on status
            self.remove_class("status-normal", "status-warning", "status-error", "status-success")
            self.add_class(f"status-{new_status}")
        except:
            # Widget not ready yet, ignore
            pass


class StatusPanel(BasePanel):
    """Panel for displaying status information"""
    
    DEFAULT_CSS = """
    StatusPanel {
        height: auto;
        min-height: 8;
    }
    
    StatusPanel .status-item {
        height: 1;
        margin: 0 1;
    }
    
    StatusPanel .status-label {
        width: 1fr;
    }
    
    StatusPanel .status-value {
        width: auto;
        text-align: right;
    }
    """
    
    def __init__(self, title: str = "Status", **kwargs):
        super().__init__(title=title, show_header=True, show_footer=True, **kwargs)
        self.status_items: Dict[str, Any] = {}
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def add_status_item(self, key: str, label: str, value: Any, status: str = "normal") -> None:
        """Add or update a status item"""
        self.status_items[key] = {
            "label": label,
            "value": value,
            "status": status,
            "updated": datetime.now()
        }
        self._refresh_status_display()
    
    def remove_status_item(self, key: str) -> None:
        """Remove a status item"""
        if key in self.status_items:
            del self.status_items[key]
            self._refresh_status_display()
    
    def update_status_item(self, key: str, value: Any, status: str = None) -> None:
        """Update an existing status item"""
        if key in self.status_items:
            self.status_items[key]["value"] = value
            if status:
                self.status_items[key]["status"] = status
            self.status_items[key]["updated"] = datetime.now()
            self._refresh_status_display()
    
    def _refresh_status_display(self) -> None:
        """Refresh the status display"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            for key, item in self.status_items.items():
                status_row = Horizontal(classes="status-item")
                status_row.mount(Label(item["label"], classes="status-label"))
                
                value_label = Label(str(item["value"]), classes="status-value")
                value_label.add_class(f"status-{item['status']}")
                status_row.mount(value_label)
                
                content_container.mount(status_row)
        except Exception:
            # Component not mounted yet, ignore
            pass


class DataPanel(BasePanel):
    """Panel for displaying data with optional refresh capability"""
    
    def __init__(
        self,
        title: str = "Data",
        auto_refresh: bool = False,
        refresh_interval: int = 30,
        **kwargs
    ):
        super().__init__(title=title, show_header=True, show_footer=True, **kwargs)
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        self.data_source: Optional[Callable] = None
        self.is_loading = False
    
    def set_data_source(self, data_source: Callable) -> None:
        """Set the data source function"""
        self.data_source = data_source
    
    async def refresh_data(self) -> None:
        """Refresh panel data"""
        if not self.data_source or self.is_loading:
            return
        
        self.is_loading = True
        self.set_status("normal", "Loading...")
        
        try:
            data = await self.data_source()
            await self._display_data(data)
            self.set_status("success", f"Updated: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            self.set_status("error", f"Error: {str(e)}")
        finally:
            self.is_loading = False
    
    async def _display_data(self, data: Any) -> None:
        """Display the data (to be overridden by subclasses)"""
        content_container = self.query_one("#panel-content")
        content_container.remove_children()
        content_container.mount(Label(str(data)))


class ChartPanel(DataPanel):
    """Panel specifically for displaying charts"""
    
    DEFAULT_CSS = """
    ChartPanel {
        min-height: 15;
    }
    
    ChartPanel .chart-container {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }
    """
    
    def __init__(self, title: str = "Chart", chart_type: str = "line", **kwargs):
        super().__init__(title=title, **kwargs)
        self.chart_type = chart_type
        self.chart_data: List[Any] = []
    
    async def _display_data(self, data: Any) -> None:
        """Display chart data"""
        self.chart_data = data if isinstance(data, list) else [data]
        
        content_container = self.query_one("#panel-content")
        content_container.remove_children()
        
        chart_container = Container(classes="chart-container")
        
        # Simple ASCII chart rendering (placeholder)
        chart_text = self._render_ascii_chart(self.chart_data)
        chart_container.mount(Static(chart_text))
        
        content_container.mount(chart_container)
    
    def _render_ascii_chart(self, data: List[Any]) -> str:
        """Render simple ASCII chart (placeholder implementation)"""
        if not data:
            return "No data available"
        
        # Simple bar chart representation
        if isinstance(data[0], (int, float)):
            max_val = max(data) if data else 1
            min_val = min(data) if data else 0
            range_val = max_val - min_val if max_val != min_val else 1
            
            chart_lines = []
            for i, value in enumerate(data):
                normalized = (value - min_val) / range_val
                bar_length = int(normalized * 40)  # 40 char width
                bar = "█" * bar_length + "░" * (40 - bar_length)
                chart_lines.append(f"{i:2d}: {bar} {value}")
            
            return "\n".join(chart_lines)
        
        return "Chart data format not supported"


class ActionPanel(BasePanel):
    """Panel with action buttons and controls"""
    
    DEFAULT_CSS = """
    ActionPanel {
        height: auto;
        min-height: 6;
    }
    
    ActionPanel .action-buttons {
        height: auto;
        align: center middle;
    }
    
    ActionPanel Button {
        margin: 0 1;
        min-width: 12;
    }
    """
    
    def __init__(self, title: str = "Actions", **kwargs):
        super().__init__(title=title, show_header=True, **kwargs)
        self.actions: Dict[str, Dict[str, Any]] = {}
    
    def add_action(
        self,
        action_id: str,
        label: str,
        callback: Callable,
        variant: str = "default",
        disabled: bool = False
    ) -> None:
        """Add an action button"""
        self.actions[action_id] = {
            "label": label,
            "callback": callback,
            "variant": variant,
            "disabled": disabled
        }
        self._refresh_actions()
    
    def remove_action(self, action_id: str) -> None:
        """Remove an action button"""
        if action_id in self.actions:
            del self.actions[action_id]
            self._refresh_actions()
    
    def enable_action(self, action_id: str, enabled: bool = True) -> None:
        """Enable or disable an action"""
        if action_id in self.actions:
            self.actions[action_id]["disabled"] = not enabled
            self._refresh_actions()
    
    def _refresh_actions(self) -> None:
        """Refresh the action buttons display"""
        content_container = self.query_one("#panel-content")
        content_container.remove_children()
        
        button_container = Horizontal(classes="action-buttons")
        
        for action_id, action in self.actions.items():
            button = Button(
                action["label"],
                variant=action["variant"],
                disabled=action["disabled"],
                id=f"action-{action_id}"
            )
            button_container.mount(button)
        
        content_container.mount(button_container)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        if button_id and button_id.startswith("action-"):
            action_id = button_id[7:]  # Remove "action-" prefix
            if action_id in self.actions:
                callback = self.actions[action_id]["callback"]
                if callback:
                    await callback()