"""
Tests for Enhanced UI Components

Tests for data binding, theming, and responsive layout functionality.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from textual.widgets import Label
from textual.app import App

from mcp_tui_client.ui.components.data_binding import (
    DataBinding, DataBindingManager, RealTimeDataSource, BindingType,
    BotDataSource, MarketDataSource, SystemDataSource, DataChangeEvent
)
from mcp_tui_client.ui.components.theming import (
    ThemeManager, Theme, ColorScheme, ComponentTheme, ThemeType
)
from mcp_tui_client.ui.components.panels import BasePanel, StatusPanel
from mcp_tui_client.ui.components.containers import ResponsiveContainer, TabbedContainer


class TestDataBinding:
    """Test data binding functionality"""
    
    def test_data_change_event(self):
        """Test data change event creation"""
        event = DataChangeEvent("test_source", "test_property", "old", "new")
        
        assert event.source_id == "test_source"
        assert event.property_name == "test_property"
        assert event.old_value == "old"
        assert event.new_value == "new"
        assert isinstance(event.timestamp, datetime)
    
    def test_real_time_data_source(self):
        """Test real-time data source"""
        class TestDataSource(RealTimeDataSource):
            async def start_updates(self):
                pass
            
            async def stop_updates(self):
                pass
        
        source = TestDataSource("test_source")
        
        # Test data setting and getting
        source.set_data("test_prop", "test_value")
        assert source.get_data("test_prop") == "test_value"
        assert source.get_data("nonexistent", "default") == "default"
        
        # Test subscription
        callback_called = False
        received_event = None
        
        def callback(event):
            nonlocal callback_called, received_event
            callback_called = True
            received_event = event
        
        source.subscribe(callback)
        source.set_data("test_prop", "new_value")
        
        assert callback_called
        assert received_event.property_name == "test_prop"
        assert received_event.old_value == "test_value"
        assert received_event.new_value == "new_value"
    
    def test_data_binding_manager(self):
        """Test data binding manager"""
        manager = DataBindingManager()
        
        # Create mock data source
        class MockDataSource(RealTimeDataSource):
            async def start_updates(self):
                pass
            
            async def stop_updates(self):
                pass
        
        source = MockDataSource("test_source")
        manager.register_data_source(source)
        
        assert manager.get_data_source("test_source") == source
        
        # Test unregistration
        manager.unregister_data_source("test_source")
        assert manager.get_data_source("test_source") is None
    
    @pytest.mark.asyncio
    async def test_bot_data_source(self):
        """Test bot data source"""
        bot_source = BotDataSource("test_bot")
        
        # Test that it initializes correctly
        assert bot_source.source_id == "bot_test_bot"
        assert bot_source.bot_id == "test_bot"
        
        # Test start/stop (should not raise exceptions)
        await bot_source.start_updates()
        await asyncio.sleep(0.1)  # Let it run briefly
        await bot_source.stop_updates()
    
    @pytest.mark.asyncio
    async def test_market_data_source(self):
        """Test market data source"""
        market_source = MarketDataSource("BTC_USD")
        
        assert market_source.source_id == "market_BTC_USD"
        assert market_source.symbol == "BTC_USD"
        
        # Test start/stop
        await market_source.start_updates()
        await asyncio.sleep(0.1)
        await market_source.stop_updates()


class TestTheming:
    """Test theming functionality"""
    
    def test_color_scheme(self):
        """Test color scheme creation and conversion"""
        colors = ColorScheme(
            name="Test",
            primary="#ff0000",
            secondary="#00ff00",
            accent="#0000ff",
            surface="#ffffff",
            background="#000000",
            text="#333333",
            text_muted="#666666",
            success="#00aa00",
            warning="#ffaa00",
            error="#aa0000",
            info="#0000aa"
        )
        
        # Test CSS variables conversion
        css_vars = colors.to_css_vars()
        assert css_vars["--primary"] == "#ff0000"
        assert css_vars["--secondary"] == "#00ff00"
        
        # Test dictionary conversion
        color_dict = colors.to_dict()
        assert color_dict["name"] == "Test"
        assert color_dict["primary"] == "#ff0000"
        
        # Test from dictionary
        colors2 = ColorScheme.from_dict(color_dict)
        assert colors2.name == colors.name
        assert colors2.primary == colors.primary
    
    def test_component_theme(self):
        """Test component theme"""
        component_theme = ComponentTheme(
            component_name="TestComponent",
            styles={"border": "solid", "padding": "1"},
            colors={"color": "#ffffff", "background": "#000000"},
            spacing={"margin": "1"},
            typography={"font-size": "12px"}
        )
        
        # Test CSS generation
        css = component_theme.to_css()
        assert ".TestComponent" in css
        assert "border: solid;" in css
        assert "color: #ffffff;" in css
    
    def test_theme(self):
        """Test complete theme"""
        colors = ColorScheme(
            name="Test",
            primary="#ff0000", secondary="#00ff00", accent="#0000ff",
            surface="#ffffff", background="#000000", text="#333333",
            text_muted="#666666", success="#00aa00", warning="#ffaa00",
            error="#aa0000", info="#0000aa"
        )
        
        theme = Theme(
            name="Test Theme",
            theme_type=ThemeType.CUSTOM,
            color_scheme=colors
        )
        
        # Test component theme addition
        component_theme = ComponentTheme(
            component_name="TestComponent",
            styles={"border": "solid"}
        )
        theme.add_component_theme(component_theme)
        
        retrieved_theme = theme.get_component_theme("TestComponent")
        assert retrieved_theme == component_theme
        
        # Test CSS generation
        css = theme.to_css()
        assert ":root {" in css
        assert "--primary: #ff0000;" in css
        assert ".TestComponent" in css
    
    def test_theme_manager(self):
        """Test theme manager"""
        manager = ThemeManager()
        
        # Test built-in themes are loaded
        assert "Dark" in manager.get_theme_names()
        assert "Light" in manager.get_theme_names()
        assert "High Contrast" in manager.get_theme_names()
        
        # Test theme switching
        assert manager.set_theme("Light")
        current_theme = manager.get_current_theme()
        assert current_theme.name == "Light"
        
        # Test invalid theme
        assert not manager.set_theme("NonExistent")
        
        # Test custom theme creation
        custom_theme = manager.create_custom_theme(
            "My Custom Theme",
            base_theme_name="Dark",
            color_overrides={"primary": "#ff00ff"}
        )
        
        assert custom_theme is not None
        assert custom_theme.name == "My Custom Theme"
        assert custom_theme.color_scheme.primary == "#ff00ff"


class TestEnhancedPanels:
    """Test enhanced panel components"""
    
    def test_base_panel(self):
        """Test base panel functionality"""
        panel = BasePanel(title="Test Panel", show_header=True, show_footer=True)
        
        assert panel.title == "Test Panel"
        assert panel.show_header
        assert panel.show_footer
        
        # Test status setting
        panel.set_status("warning", "Test warning")
        assert panel.status == "warning"
    
    def test_status_panel(self):
        """Test status panel"""
        panel = StatusPanel(title="Status")
        
        # Test adding status items
        panel.add_status_item("test1", "Test Item 1", "OK", "success")
        panel.add_status_item("test2", "Test Item 2", "Warning", "warning")
        
        assert "test1" in panel.status_items
        assert "test2" in panel.status_items
        assert panel.status_items["test1"]["value"] == "OK"
        assert panel.status_items["test1"]["status"] == "success"
        
        # Test removing status items
        panel.remove_status_item("test1")
        assert "test1" not in panel.status_items
        assert "test2" in panel.status_items


class TestEnhancedContainers:
    """Test enhanced container components"""
    
    def test_responsive_container(self):
        """Test responsive container"""
        container = ResponsiveContainer()
        
        # Test breakpoints
        assert container.breakpoints["compact"] == 80
        assert container.breakpoints["normal"] == 120
        assert container.breakpoints["wide"] == 160
        
        # Test size class determination
        container._determine_size_class(60)
        assert container.current_size_class == "compact"
        
        container._determine_size_class(100)
        assert container.current_size_class == "normal"
        
        container._determine_size_class(150)
        assert container.current_size_class == "wide"
    
    def test_tabbed_container(self):
        """Test tabbed container"""
        container = TabbedContainer()
        
        # Test adding tabs
        test_widget = Label("Test content")
        container.add_tab("tab1", "Tab 1", test_widget, closable=True)
        container.add_tab("tab2", "Tab 2", Label("Tab 2 content"), closable=False)
        
        assert "tab1" in container.tabs
        assert "tab2" in container.tabs
        assert container.tabs["tab1"]["title"] == "Tab 1"
        assert container.tabs["tab1"]["closable"]
        assert not container.tabs["tab2"]["closable"]
        
        # Test tab switching
        container.switch_to_tab("tab2")
        assert container.active_tab == "tab2"
        
        # Test tab removal
        container.remove_tab("tab1")
        assert "tab1" not in container.tabs
        assert container.active_tab == "tab2"  # Should switch to remaining tab


class TestIntegration:
    """Integration tests for enhanced components"""
    
    @pytest.mark.asyncio
    async def test_data_binding_integration(self):
        """Test data binding with actual widgets"""
        # Create data source
        class TestSource(RealTimeDataSource):
            async def start_updates(self):
                pass
            async def stop_updates(self):
                pass
        
        source = TestSource("test")
        manager = DataBindingManager()
        manager.register_data_source(source)
        
        # Create widget
        label = Label("Initial")
        
        # Create binding
        binding = manager.create_binding(
            "test_binding",
            "test",
            label,
            "text_value",
            "renderable"
        )
        
        assert binding is not None
        
        # Update data and verify binding works
        source.set_data("text_value", "Updated text")
        
        # Clean up
        manager.cleanup()
    
    def test_theme_integration(self):
        """Test theme integration with components"""
        manager = ThemeManager()
        
        # Create a panel
        panel = BasePanel(title="Test Panel")
        
        # Test theme application (simplified)
        current_theme = manager.get_current_theme()
        assert current_theme is not None
        
        # Test theme switching
        original_theme = current_theme.name
        manager.set_theme("Light")
        new_theme = manager.get_current_theme()
        assert new_theme.name == "Light"
        assert new_theme.name != original_theme


if __name__ == "__main__":
    pytest.main([__file__])