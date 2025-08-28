#!/usr/bin/env python3
"""
Simple Enhanced Components Demo

A simplified demo showing the key features of the enhanced UI components library.
"""

import asyncio
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Label

# Import our enhanced components
from mcp_tui_client.ui.components.panels import StatusPanel, DataPanel
from mcp_tui_client.ui.components.tables import DataTable
from mcp_tui_client.ui.components.charts import LineChart
from mcp_tui_client.ui.components.indicators import StatusIndicator, ProgressIndicator
from mcp_tui_client.ui.components.containers import TabbedContainer
from mcp_tui_client.ui.components.data_binding import DataBindingManager, RealTimeDataSource
from mcp_tui_client.ui.components.theming import ThemeManager


class SimpleDataSource(RealTimeDataSource):
    """Simple data source for demo"""
    
    def __init__(self):
        super().__init__("demo_data")
        self.counter = 0
        self.update_task = None
    
    async def start_updates(self):
        """Start updating data"""
        if self.update_task and not self.update_task.done():
            return
        self.update_task = asyncio.create_task(self._update_loop())
    
    async def stop_updates(self):
        """Stop updating data"""
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Update loop"""
        while True:
            try:
                await asyncio.sleep(2)  # Update every 2 seconds
                self.counter += 1
                
                # Update various data points
                self.set_data("counter", self.counter)
                self.set_data("timestamp", datetime.now().strftime("%H:%M:%S"))
                self.set_data("status", "running" if self.counter % 3 != 0 else "idle")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in update loop: {e}")
                await asyncio.sleep(5)


class SimpleComponentsDemo(App):
    """Simple demo application"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .demo-content {
        height: 1fr;
        layout: horizontal;
    }
    
    .left-column {
        width: 1fr;
        margin: 1;
    }
    
    .right-column {
        width: 1fr;
        margin: 1;
    }
    
    .controls {
        height: 5;
        margin: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_theme", "Toggle Theme"),
        ("s", "start_demo", "Start Demo"),
    ]
    
    def __init__(self):
        super().__init__()
        self.data_binding_manager = DataBindingManager()
        self.theme_manager = ThemeManager(self)
        self.data_source = SimpleDataSource()
        self.data_binding_manager.register_data_source(self.data_source)
        self.demo_running = False
    
    def compose(self) -> ComposeResult:
        """Compose the demo"""
        yield Header()
        
        # Main content
        content = Container(classes="demo-content")
        
        # Left column
        left = Container(classes="left-column")
        left.mount(self._create_status_panel())
        left.mount(self._create_data_table())
        
        # Right column  
        right = Container(classes="right-column")
        right.mount(self._create_indicators())
        right.mount(self._create_tabbed_content())
        
        content.mount(left)
        content.mount(right)
        yield content
        
        # Controls
        yield self._create_controls()
        
        yield Footer()
    
    def _create_status_panel(self) -> StatusPanel:
        """Create status panel"""
        panel = StatusPanel(title="System Status")
        panel.add_status_item("demo", "Demo Status", "Stopped", "warning")
        panel.add_status_item("theme", "Current Theme", "Dark", "info")
        panel.add_status_item("time", "Current Time", datetime.now().strftime("%H:%M:%S"), "success")
        return panel
    
    def _create_data_table(self) -> DataTable:
        """Create data table"""
        table = DataTable(
            columns=["Name", "Value", "Status"],
            show_header=True,
            show_footer=True
        )
        
        # Sample data
        data = [
            {"Name": "Counter", "Value": "0", "Status": "Ready"},
            {"Name": "Timer", "Value": "00:00", "Status": "Stopped"},
            {"Name": "Memory", "Value": "45%", "Status": "Normal"},
        ]
        table.set_data(data)
        return table
    
    def _create_indicators(self) -> Container:
        """Create indicators"""
        container = Container()
        
        # Status indicator
        status = StatusIndicator(
            status="neutral",
            text="Demo not started"
        )
        
        # Progress indicator
        progress = ProgressIndicator(
            title="Demo Progress",
            show_percentage=True
        )
        progress.set_progress(0.0)
        
        container.mount(status)
        container.mount(progress)
        return container
    
    def _create_tabbed_content(self) -> TabbedContainer:
        """Create tabbed content"""
        tabs = TabbedContainer()
        
        # Chart tab
        chart = LineChart(title="Demo Chart", width=40, height=10)
        chart.set_data([1, 3, 2, 5, 4, 6, 5, 8, 7, 9])
        tabs.add_tab("chart", "Chart", chart, icon="📊")
        
        # Info tab
        info = Label("This is a demo of the enhanced UI components library.\n\n"
                    "Features demonstrated:\n"
                    "• Data binding and real-time updates\n"
                    "• Theming system with multiple themes\n"
                    "• Responsive containers and layouts\n"
                    "• Status indicators and progress bars\n"
                    "• Tables with sorting and filtering\n"
                    "• ASCII charts and visualizations")
        tabs.add_tab("info", "Info", info, icon="ℹ️")
        
        return tabs
    
    def _create_controls(self) -> Container:
        """Create control buttons"""
        container = Container(classes="controls")
        
        buttons = Horizontal()
        buttons.mount(Button("Start Demo", id="start", variant="primary"))
        buttons.mount(Button("Stop Demo", id="stop", variant="default"))
        buttons.mount(Button("Toggle Theme", id="theme", variant="default"))
        buttons.mount(Button("Quit", id="quit", variant="error"))
        
        container.mount(buttons)
        return container
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "start":
            await self._start_demo()
        elif event.button.id == "stop":
            await self._stop_demo()
        elif event.button.id == "theme":
            await self._toggle_theme()
        elif event.button.id == "quit":
            await self.action_quit()
    
    async def _start_demo(self) -> None:
        """Start the demo"""
        if not self.demo_running:
            self.demo_running = True
            await self.data_source.start_updates()
            self.notify("Demo started!")
    
    async def _stop_demo(self) -> None:
        """Stop the demo"""
        if self.demo_running:
            self.demo_running = False
            await self.data_source.stop_updates()
            self.notify("Demo stopped!")
    
    async def _toggle_theme(self) -> None:
        """Toggle theme"""
        current = self.theme_manager.get_current_theme()
        if current and current.name == "Dark":
            self.theme_manager.set_theme("Light")
            self.notify("Switched to Light theme")
        else:
            self.theme_manager.set_theme("Dark")
            self.notify("Switched to Dark theme")
    
    async def action_toggle_theme(self) -> None:
        """Theme toggle action"""
        await self._toggle_theme()
    
    async def action_start_demo(self) -> None:
        """Start demo action"""
        await self._start_demo()
    
    async def on_mount(self) -> None:
        """Initialize demo"""
        self.title = "Enhanced Components Demo"
        self.sub_title = "Data Binding, Theming, and Responsive UI"
    
    async def on_unmount(self) -> None:
        """Cleanup"""
        await self._stop_demo()
        self.data_binding_manager.cleanup()


def main():
    """Run the simple demo"""
    app = SimpleComponentsDemo()
    app.run()


if __name__ == "__main__":
    main()