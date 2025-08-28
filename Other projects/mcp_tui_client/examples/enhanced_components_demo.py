#!/usr/bin/env python3
"""
Enhanced UI Components Demo

Demonstrates the enhanced base UI components library with data binding,
theming, and responsive layouts.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Label

# Import our enhanced components
from mcp_tui_client.ui.components import (
    # Core components
    BasePanel, StatusPanel, DataPanel, ChartPanel, ActionPanel,
    DataTable, SortableTable, FilterableTable,
    LineChart, CandlestickChart, PerformanceChart, BarChart,
    ResponsiveContainer, TabbedContainer, CollapsibleContainer,
    StatusIndicator, ProgressIndicator, LoadingIndicator,
    
    # Data binding system
    DataBindingManager, BotDataSource, MarketDataSource, SystemDataSource,
    BindableWidget, BindingType,
    
    # Theming system
    ThemeManager, Theme, ColorScheme, ComponentTheme, ThemeType,
)


class EnhancedComponentsDemo(App):
    """Demo application showcasing enhanced UI components"""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .demo-container {
        height: 1fr;
        layout: horizontal;
    }
    
    .left-panel {
        width: 1fr;
        margin: 1;
    }
    
    .right-panel {
        width: 1fr;
        margin: 1;
    }
    
    .controls-panel {
        height: 8;
        margin: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_theme", "Toggle Theme"),
        ("r", "refresh_data", "Refresh Data"),
        ("d", "toggle_demo", "Toggle Demo"),
    ]
    
    def __init__(self):
        super().__init__()
        self.data_binding_manager = DataBindingManager()
        self.theme_manager = ThemeManager(self)
        self.demo_active = False
        
        # Data sources
        self.bot_data_source = BotDataSource("demo_bot")
        self.market_data_source = MarketDataSource("BTC_USD")
        self.system_data_source = SystemDataSource()
        
        # Register data sources
        self.data_binding_manager.register_data_source(self.bot_data_source)
        self.data_binding_manager.register_data_source(self.market_data_source)
        self.data_binding_manager.register_data_source(self.system_data_source)
    
    def compose(self) -> ComposeResult:
        """Compose the demo application"""
        yield Header()
        
        # Main demo container
        demo_container = Container(classes="demo-container")
        
        # Left panel with various components
        left_panel = Container(classes="left-panel")
        left_panel.mount(self._create_status_panel())
        left_panel.mount(self._create_data_table_demo())
        left_panel.mount(self._create_chart_demo())
        
        # Right panel with more components
        right_panel = Container(classes="right-panel")
        right_panel.mount(self._create_responsive_demo())
        right_panel.mount(self._create_tabbed_demo())
        right_panel.mount(self._create_indicators_demo())
        
        demo_container.mount(left_panel)
        demo_container.mount(right_panel)
        
        yield demo_container
        
        # Controls panel
        yield self._create_controls_panel()
        
        yield Footer()
    
    def _create_status_panel(self) -> StatusPanel:
        """Create status panel with data binding"""
        status_panel = StatusPanel(title="System Status")
        
        # Bind to system data source
        self.data_binding_manager.create_binding(
            binding_id="system_cpu",
            source_id="system",
            widget=status_panel,
            source_property="cpu_usage",
            widget_property="cpu_status",
            converter=lambda x: f"{x}%"
        )
        
        # Add some initial status items
        status_panel.add_status_item("mcp_server", "MCP Server", "Connected", "success")
        status_panel.add_status_item("haas_api", "HaasOnline API", "Connected", "success")
        status_panel.add_status_item("websocket", "WebSocket", "Connected", "success")
        
        return status_panel
    
    def _create_data_table_demo(self) -> FilterableTable:
        """Create data table demo"""
        columns = ["Symbol", "Price", "Change", "Volume"]
        table = FilterableTable(
            columns=columns,
            show_header=True,
            show_footer=True
        )
        
        # Sample data
        sample_data = [
            {"Symbol": "BTC_USD", "Price": "45,123.45", "Change": "+2.34%", "Volume": "1.2M"},
            {"Symbol": "ETH_USD", "Price": "3,234.56", "Change": "-1.23%", "Volume": "2.5M"},
            {"Symbol": "ADA_USD", "Price": "0.4567", "Change": "+5.67%", "Volume": "890K"},
            {"Symbol": "DOT_USD", "Price": "12.34", "Change": "-0.45%", "Volume": "456K"},
        ]
        
        table.set_data(sample_data)
        return table
    
    def _create_chart_demo(self) -> ChartPanel:
        """Create chart demo panel"""
        chart_panel = ChartPanel(title="Performance Chart", chart_type="line")
        
        # Sample performance data
        performance_data = [100, 102, 98, 105, 110, 108, 115, 112, 118, 125]
        chart_panel._display_data(performance_data)
        
        return chart_panel
    
    def _create_responsive_demo(self) -> ResponsiveContainer:
        """Create responsive container demo"""
        responsive_container = ResponsiveContainer()
        
        # Add components that will be shown/hidden based on screen size
        compact_widget = Label("Compact View", classes="compact-only")
        normal_widget = Label("Normal View", classes="normal-wide")
        wide_widget = Label("Wide View", classes="wide-only")
        
        responsive_container.add_responsive_child(compact_widget, ["compact"])
        responsive_container.add_responsive_child(normal_widget, ["normal", "wide"])
        responsive_container.add_responsive_child(wide_widget, ["wide"])
        
        return responsive_container
    
    def _create_tabbed_demo(self) -> TabbedContainer:
        """Create tabbed container demo"""
        tabbed_container = TabbedContainer()
        
        # Add tabs
        tabbed_container.add_tab(
            "bots",
            "Bots",
            Label("Bot management content here"),
            closable=True,
            icon="🤖"
        )
        
        tabbed_container.add_tab(
            "labs",
            "Labs",
            Label("Lab management content here"),
            closable=True,
            icon="🧪"
        )
        
        tabbed_container.add_tab(
            "analytics",
            "Analytics",
            Label("Analytics content here"),
            closable=False,
            icon="📊"
        )
        
        return tabbed_container
    
    def _create_indicators_demo(self) -> Container:
        """Create indicators demo"""
        container = Container()
        
        # Status indicators
        success_indicator = StatusIndicator(
            status="success",
            text="All systems operational"
        )
        
        warning_indicator = StatusIndicator(
            status="warning",
            text="High CPU usage detected"
        )
        
        # Progress indicator
        progress_indicator = ProgressIndicator(
            title="Backtest Progress",
            show_percentage=True,
            show_eta=True
        )
        progress_indicator.start_progress()
        progress_indicator.set_progress(0.65)  # 65% complete
        
        # Loading indicator
        loading_indicator = LoadingIndicator(text="Loading market data...")
        
        container.mount(success_indicator)
        container.mount(warning_indicator)
        container.mount(progress_indicator)
        container.mount(loading_indicator)
        
        return container
    
    def _create_controls_panel(self) -> ActionPanel:
        """Create controls panel"""
        controls = ActionPanel(title="Demo Controls")
        
        controls.add_action(
            "start_demo",
            "Start Demo",
            self._start_demo,
            variant="primary"
        )
        
        controls.add_action(
            "stop_demo",
            "Stop Demo",
            self._stop_demo,
            variant="default"
        )
        
        controls.add_action(
            "toggle_theme",
            "Toggle Theme",
            self._toggle_theme,
            variant="default"
        )
        
        controls.add_action(
            "refresh_data",
            "Refresh Data",
            self._refresh_data,
            variant="default"
        )
        
        return controls
    
    async def _start_demo(self) -> None:
        """Start the demo with real-time updates"""
        if not self.demo_active:
            self.demo_active = True
            await self.data_binding_manager.start_all_sources()
            self.notify("Demo started - real-time updates enabled")
    
    async def _stop_demo(self) -> None:
        """Stop the demo"""
        if self.demo_active:
            self.demo_active = False
            await self.data_binding_manager.stop_all_sources()
            self.notify("Demo stopped")
    
    async def _toggle_theme(self) -> None:
        """Toggle between themes"""
        current_theme = self.theme_manager.get_current_theme()
        if current_theme:
            if current_theme.name == "Dark":
                self.theme_manager.set_theme("Light")
                self.notify("Switched to Light theme")
            elif current_theme.name == "Light":
                self.theme_manager.set_theme("High Contrast")
                self.notify("Switched to High Contrast theme")
            else:
                self.theme_manager.set_theme("Dark")
                self.notify("Switched to Dark theme")
    
    async def _refresh_data(self) -> None:
        """Refresh all data sources"""
        self.notify("Refreshing data...")
        
        # Simulate data refresh
        await asyncio.sleep(1)
        
        # Update some sample data
        self.bot_data_source.set_data("profit", 156.78)
        self.bot_data_source.set_data("trades", 47)
        self.market_data_source.set_data("price", 46789.12)
        
        self.notify("Data refreshed")
    
    async def action_toggle_theme(self) -> None:
        """Action for theme toggle hotkey"""
        await self._toggle_theme()
    
    async def action_refresh_data(self) -> None:
        """Action for data refresh hotkey"""
        await self._refresh_data()
    
    async def action_toggle_demo(self) -> None:
        """Action for demo toggle hotkey"""
        if self.demo_active:
            await self._stop_demo()
        else:
            await self._start_demo()
    
    async def on_mount(self) -> None:
        """Initialize the demo"""
        self.title = "Enhanced UI Components Demo"
        self.sub_title = "Data Binding, Theming, and Responsive Layouts"
        
        # Start with demo active
        await self._start_demo()
    
    async def on_unmount(self) -> None:
        """Clean up when closing"""
        await self._stop_demo()
        self.data_binding_manager.cleanup()


class BindableLabel(BindableWidget, Label):
    """Example of a bindable widget"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def update_content(self, value: Any) -> None:
        """Update label content"""
        self.update(str(value))


def main():
    """Run the enhanced components demo"""
    app = EnhancedComponentsDemo()
    app.run()


if __name__ == "__main__":
    main()