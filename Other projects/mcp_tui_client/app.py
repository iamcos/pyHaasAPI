"""
Main TUI Application Entry Point

This module contains the main application class and entry point for the MCP TUI Client.
"""

import asyncio
import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Type, Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Static
from textual.widget import Widget
from textual.screen import Screen
from textual.reactive import reactive
from textual.containers import Container

from .ui.dashboard import DashboardView
from .ui.bots import BotManagementView
from .ui.labs import LabManagementView
from .ui.scripts import ScriptEditorView
from .ui.workflows import WorkflowDesignerView
from .ui.markets import MarketDataView
from .ui.analytics import AnalyticsView
from .ui.settings import SettingsView
from .ui.navigation import MenuSystem, NavigationManager, GlobalSearch, HelpSystem
from .services.config import ConfigurationService
from .services.mcp_client import MCPClientService
from .utils.logging import setup_logging


class MainContainer(Container):
    """Main content container for different views with smooth transitions"""
    
    DEFAULT_CSS = """
    MainContainer {
        height: 1fr;
        width: 1fr;
        background: $background;
        padding: 0;
        margin: 0;
    }
    
    MainContainer .view-container {
        height: 1fr;
        width: 1fr;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    MainContainer .loading-indicator {
        height: 1fr;
        width: 1fr;
        text-align: center;
        content-align: center middle;
        background: $surface;
        color: $text-muted;
    }
    
    MainContainer .error-container {
        height: 1fr;
        width: 1fr;
        text-align: center;
        content-align: center middle;
        background: $surface;
        color: $error;
        border: solid $error;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_view = None
        self.view_history = []
        self.loading = False
        self.error_state = None
    
    def compose(self) -> ComposeResult:
        """Compose main container (initially empty)"""
        return []
    
    async def set_view(self, view_widget: Widget, view_name: str = None) -> None:
        """Set the current view with smooth transition"""
        try:
            self.loading = True
            
            # Remove current view if exists
            if self.current_view:
                await self.current_view.remove()
            
            # Clear any error state
            self.error_state = None
            
            # Add new view
            view_widget.add_class("view-container")
            await self.mount(view_widget)
            self.current_view = view_widget
            
            # Update history
            if view_name and (not self.view_history or self.view_history[-1] != view_name):
                self.view_history.append(view_name)
                if len(self.view_history) > 20:  # Limit history
                    self.view_history.pop(0)
            
            self.loading = False
            
        except Exception as e:
            self.loading = False
            self.error_state = str(e)
            await self.show_error(f"Failed to load view: {e}")
    
    async def show_loading(self, message: str = "Loading...") -> None:
        """Show loading indicator"""
        if self.current_view:
            await self.current_view.remove()
            self.current_view = None
        
        loading_widget = Static(message, classes="loading-indicator")
        await self.mount(loading_widget)
        self.current_view = loading_widget
        self.loading = True
    
    async def show_error(self, error_message: str) -> None:
        """Show error state"""
        if self.current_view:
            await self.current_view.remove()
            self.current_view = None
        
        error_widget = Static(f"Error: {error_message}", classes="error-container")
        await self.mount(error_widget)
        self.current_view = error_widget
        self.error_state = error_message
        self.loading = False
    
    def get_current_view_info(self) -> Dict[str, Any]:
        """Get information about current view"""
        return {
            "has_view": self.current_view is not None,
            "view_type": type(self.current_view).__name__ if self.current_view else None,
            "loading": self.loading,
            "error": self.error_state,
            "history_length": len(self.view_history),
            "recent_views": self.view_history[-5:] if self.view_history else []
        }


class MCPTUIApp(App):
    """Main TUI application using Textual framework"""
    
    CSS_PATH = "styles.css"
    TITLE = "MCP TUI Client - HaasOnline Trading Interface"
    SUB_TITLE = "Terminal-based Trading Bot & Lab Management"
    
    # Global keyboard shortcuts and navigation system
    BINDINGS = [
        # Application control
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("escape", "cancel", "Cancel/Back"),
        
        # Navigation shortcuts (F-keys for main views)
        Binding("f1", "show_dashboard", "Dashboard", show=True),
        Binding("f2", "show_bots", "Bot Management", show=True),
        Binding("f3", "show_labs", "Lab Management", show=True),
        Binding("f4", "show_scripts", "Script Editor", show=True),
        Binding("f5", "show_workflows", "Workflow Designer", show=True),
        Binding("f6", "show_markets", "Market Data", show=True),
        Binding("f7", "show_analytics", "Analytics", show=True),
        Binding("f8", "show_settings", "Settings", show=True),
        
        # Navigation control
        Binding("alt+left", "nav_back", "Back", show=True),
        Binding("alt+right", "nav_forward", "Forward", show=True),
        Binding("ctrl+home", "nav_home", "Home", show=True),
        
        # Global actions
        Binding("ctrl+r", "refresh", "Refresh", show=True),
        Binding("ctrl+h", "help", "Help", show=True),
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+o", "open", "Open"),
        Binding("ctrl+n", "new", "New"),
        Binding("ctrl+f", "search", "Search"),
        
        # Quick actions
        Binding("ctrl+shift+b", "quick_bot_action", "Quick Bot"),
        Binding("ctrl+shift+l", "quick_lab_action", "Quick Lab"),
        Binding("ctrl+shift+w", "quick_workflow", "Quick Workflow"),
        
        # System actions
        Binding("f9", "toggle_fullscreen", "Fullscreen"),
        Binding("f10", "toggle_menu", "Menu"),
        Binding("f11", "toggle_debug", "Debug"),
        Binding("f12", "system_info", "System Info"),
        
        # Theme and display
        Binding("ctrl+t", "toggle_theme", "Theme"),
        Binding("ctrl+plus", "zoom_in", "Zoom In"),
        Binding("ctrl+minus", "zoom_out", "Zoom Out"),
        Binding("ctrl+0", "zoom_reset", "Reset Zoom"),
    ]
    
    # Screen management for different application views
    SCREENS = {
        "dashboard": DashboardView,
        "bots": BotManagementView,
        "labs": LabManagementView,
        "scripts": ScriptEditorView,
        "workflows": WorkflowDesignerView,
        "markets": MarketDataView,
        "analytics": AnalyticsView,
        "settings": SettingsView,
    }
    
    # Reactive state for current view
    current_view = reactive("dashboard")
    connection_status = reactive("disconnected")
    
    def __init__(self, config_path: Optional[str] = None):
        super().__init__()
        self.config_service = ConfigurationService(config_path)
        self.mcp_client = None
        self.view_history = ["dashboard"]  # Navigation history
        self.screen_instances = {}  # Cache screen instances
        
        # Set up logging
        setup_logging(self.config_service.get_log_level())
        self.logger = logging.getLogger(__name__)
        
        # Initialize screen instances
        self._initialize_screens()
        
    def _initialize_screens(self) -> None:
        """Initialize screen instances for better performance"""
        for screen_name, screen_class in self.SCREENS.items():
            try:
                screen_instance = screen_class()
                if hasattr(screen_instance, 'set_app_reference'):
                    screen_instance.set_app_reference(self)
                self.screen_instances[screen_name] = screen_instance
            except Exception as e:
                self.logger.error(f"Failed to initialize {screen_name} screen: {e}")
    
    async def on_mount(self) -> None:
        """Initialize the application on mount"""
        self.logger.info("Starting MCP TUI Client")
        
        # Initialize MCP client
        await self._initialize_mcp_connection()
        
        # Set initial view
        await self.action_show_dashboard()
        
        # Start background tasks
        self._start_background_tasks()
    
    async def _initialize_mcp_connection(self) -> None:
        """Initialize MCP client connection with comprehensive retry logic"""
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempting MCP connection (attempt {attempt + 1}/{max_retries})")
                
                # Get MCP configuration
                mcp_config = self.config_service.get_mcp_settings()
                
                # Create and connect MCP client
                self.mcp_client = MCPClientService(mcp_config)
                await self.mcp_client.connect()
                
                # Test connection with a simple call
                if hasattr(self.mcp_client, 'test_connection'):
                    await self.mcp_client.test_connection()
                
                self.connection_status = "connected"
                self.logger.info("Successfully connected to MCP server")
                
                # Distribute MCP client to all initialized screens
                for screen_name, screen in self.screen_instances.items():
                    try:
                        if hasattr(screen, 'set_mcp_client'):
                            screen.set_mcp_client(self.mcp_client)
                            self.logger.debug(f"MCP client set for {screen_name} screen")
                    except Exception as screen_error:
                        self.logger.warning(f"Failed to set MCP client for {screen_name}: {screen_error}")
                
                # Initialize navigation manager callback
                try:
                    nav_manager = self.query_one("#navigation-manager", NavigationManager)
                    nav_manager.set_view_change_callback(self._handle_navigation)
                    self.logger.debug("Navigation manager callback initialized")
                except Exception as nav_error:
                    self.logger.warning(f"Navigation manager initialization failed: {nav_error}")
                
                # Notify successful connection
                self.notify("Connected to MCP server", severity="information")
                return
                
            except Exception as e:
                self.logger.error(f"MCP connection attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                else:
                    # Final failure
                    self.connection_status = "error"
                    self.logger.error("All MCP connection attempts failed")
                    self.notify("Failed to connect to MCP server", severity="error")
                    
                    # Continue in offline mode
                    self.logger.info("Continuing in offline mode")
                    break
    
    def _start_background_tasks(self) -> None:
        """Start background tasks for real-time updates"""
        # TODO: Implement background tasks for:
        # - Real-time data updates
        # - Connection health monitoring
        # - Periodic data refresh
        pass
    
    def compose(self) -> ComposeResult:
        """Compose the main application layout with header, content, and footer"""
        # Header with application title and status
        yield Header(show_clock=True, name="MCP TUI Client", id="app-header")
        
        # Menu system for hierarchical navigation
        yield MenuSystem(id="menu-system")
        
        # Navigation manager with breadcrumbs and history
        yield NavigationManager(id="navigation-manager")
        
        # Main content container for different views
        yield MainContainer(id="main-container")
        
        # Footer with status information and shortcuts
        yield Footer(id="app-footer")
    
    # Navigation action methods
    async def action_show_dashboard(self) -> None:
        """Show the dashboard view"""
        await self._switch_view("dashboard")
    
    async def action_show_bots(self) -> None:
        """Show the bot management view"""
        await self._switch_view("bots")
    
    async def action_show_labs(self) -> None:
        """Show the lab management view"""
        await self._switch_view("labs")
    
    async def action_show_scripts(self) -> None:
        """Show the script editor view"""
        await self._switch_view("scripts")
    
    async def action_show_workflows(self) -> None:
        """Show the workflow designer view"""
        await self._switch_view("workflows")
    
    async def action_show_markets(self) -> None:
        """Show the market data view"""
        await self._switch_view("markets")
    
    async def action_show_analytics(self) -> None:
        """Show the analytics view"""
        await self._switch_view("analytics")
    
    async def action_show_settings(self) -> None:
        """Show the settings view"""
        await self._switch_view("settings")
    
    async def _switch_view(self, view_name: str) -> None:
        """Switch to a different view with smooth transitions and error handling"""
        if self.current_view == view_name:
            return
        
        try:
            # Get main container
            main_container = self.query_one("#main-container", MainContainer)
            
            # Show loading state
            await main_container.show_loading(f"Loading {view_name.title()}...")
            
            # Get or create new view instance
            if view_name in self.screen_instances:
                new_view = self.screen_instances[view_name]
                # Refresh the view if it has refresh capability
                if hasattr(new_view, 'refresh_data'):
                    await new_view.refresh_data()
            else:
                # Create new instance
                view_class = self.SCREENS.get(view_name, DashboardView)
                new_view = view_class()
                
                # Set up view with dependencies
                if hasattr(new_view, 'set_mcp_client') and self.mcp_client:
                    new_view.set_mcp_client(self.mcp_client)
                if hasattr(new_view, 'set_app_reference'):
                    new_view.set_app_reference(self)
                if hasattr(new_view, 'set_config_service'):
                    new_view.set_config_service(self.config_service)
                
                self.screen_instances[view_name] = new_view
            
            # Set the new view
            await main_container.set_view(new_view, view_name)
            
            # Update navigation manager
            try:
                nav_manager = self.query_one("#navigation-manager", NavigationManager)
                await nav_manager.navigate_to(
                    view_name,
                    view_name.replace("_", " ").title(),
                    {"timestamp": datetime.now().isoformat()}
                )
            except Exception as nav_error:
                self.logger.warning(f"Navigation manager update failed: {nav_error}")
            
            # Update current view
            previous_view = self.current_view
            self.current_view = view_name
            
            self.logger.info(f"Successfully switched from {previous_view} to {view_name} view")
            
            # Notify successful view change
            self.notify(f"Switched to {view_name.replace('_', ' ').title()}", severity="information")
            
        except Exception as e:
            self.logger.error(f"Failed to switch to {view_name} view: {e}")
            
            # Show error in main container
            main_container = self.query_one("#main-container", MainContainer)
            await main_container.show_error(f"Failed to load {view_name} view: {str(e)}")
            
            # Fallback to dashboard if not already trying dashboard
            if view_name != "dashboard":
                self.logger.info("Attempting fallback to dashboard")
                await self._switch_view("dashboard")
    
    # Global action methods
    async def action_refresh(self) -> None:
        """Refresh the current view"""
        try:
            main_container = self.query_one("#main-container", MainContainer)
            if main_container.current_view and hasattr(main_container.current_view, 'refresh_data'):
                await main_container.current_view.refresh_data()
                self.logger.info(f"Refreshed {self.current_view} view")
        except Exception as e:
            self.logger.error(f"Failed to refresh view: {e}")
    
    async def action_help(self) -> None:
        """Show help dialog with contextual documentation"""
        # Show comprehensive help system
        help_view = HelpSystem()
        
        # Switch to help view
        main_container = self.query_one("#main-container", MainContainer)
        if main_container.current_view:
            await main_container.current_view.remove()
        await main_container.mount(help_view)
        main_container.current_view = help_view
    
    async def action_cancel(self) -> None:
        """Cancel current operation or go back"""
        # Go back in navigation history if available
        if len(self.view_history) > 1:
            previous_view = self.view_history.pop()
            await self._switch_view(previous_view)
    
    async def action_save(self) -> None:
        """Save current work (context-dependent)"""
        main_container = self.query_one("#main-container", MainContainer)
        if main_container.current_view and hasattr(main_container.current_view, 'save'):
            await main_container.current_view.save()
    
    async def action_open(self) -> None:
        """Open file/workflow (context-dependent)"""
        main_container = self.query_one("#main-container", MainContainer)
        if main_container.current_view and hasattr(main_container.current_view, 'open'):
            await main_container.current_view.open()
    
    async def action_new(self) -> None:
        """Create new item (context-dependent)"""
        main_container = self.query_one("#main-container", MainContainer)
        if main_container.current_view and hasattr(main_container.current_view, 'new'):
            await main_container.current_view.new()
    
    async def action_search(self) -> None:
        """Global search functionality"""
        # Show global search interface
        search_view = GlobalSearch()
        if self.mcp_client:
            # Add search providers
            from .ui.navigation.search_system import BotSearchProvider, LabSearchProvider
            search_view.add_provider(BotSearchProvider(self.mcp_client))
            search_view.add_provider(LabSearchProvider(self.mcp_client))
        
        # Switch to search view
        main_container = self.query_one("#main-container", MainContainer)
        if main_container.current_view:
            await main_container.current_view.remove()
        await main_container.mount(search_view)
        main_container.current_view = search_view
    
    async def action_quick_bot_action(self) -> None:
        """Quick bot action shortcut"""
        await self.action_show_bots()
        # TODO: Show quick bot action dialog
    
    async def action_quick_lab_action(self) -> None:
        """Quick lab action shortcut"""
        await self.action_show_labs()
        # TODO: Show quick lab creation dialog
    
    async def action_quick_workflow(self) -> None:
        """Quick workflow action shortcut"""
        await self.action_show_workflows()
        # TODO: Show quick workflow creation dialog
    
    # Navigation control actions
    async def action_nav_back(self) -> None:
        """Navigate back in history"""
        try:
            nav_manager = self.query_one("#navigation-manager", NavigationManager)
            success = await nav_manager.go_back()
            if not success:
                self.notify("No previous view in history", severity="information")
        except Exception as e:
            self.logger.error(f"Failed to navigate back: {e}")
    
    async def action_nav_forward(self) -> None:
        """Navigate forward in history"""
        try:
            nav_manager = self.query_one("#navigation-manager", NavigationManager)
            success = await nav_manager.go_forward()
            if not success:
                self.notify("No forward view in history", severity="information")
        except Exception as e:
            self.logger.error(f"Failed to navigate forward: {e}")
    
    async def action_nav_home(self) -> None:
        """Navigate to home (dashboard)"""
        await self.action_show_dashboard()
    
    # System and display actions
    async def action_toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode"""
        # Note: Fullscreen is typically handled by terminal emulator
        self.notify("Fullscreen toggle (use terminal controls)", severity="information")
    
    async def action_toggle_menu(self) -> None:
        """Toggle menu bar visibility"""
        try:
            menu_system = self.query_one("#menu-system", MenuSystem)
            menu_bar = menu_system.query_one("#menu-bar")
            menu_bar.display = not menu_bar.display
            self.notify(f"Menu bar {'shown' if menu_bar.display else 'hidden'}", severity="information")
        except Exception as e:
            self.logger.error(f"Failed to toggle menu: {e}")
    
    async def action_toggle_debug(self) -> None:
        """Toggle debug mode"""
        # Toggle debug logging level
        current_level = self.config_service.get_log_level()
        new_level = "DEBUG" if current_level != "DEBUG" else "INFO"
        self.config_service.set_log_level(new_level)
        
        # Update logger
        logging.getLogger().setLevel(getattr(logging, new_level))
        self.notify(f"Debug mode {'enabled' if new_level == 'DEBUG' else 'disabled'}", severity="information")
    
    async def action_system_info(self) -> None:
        """Show system information"""
        try:
            import psutil
            import platform
            
            # Gather system information
            system_info = {
                "Platform": platform.system(),
                "Architecture": platform.machine(),
                "Python Version": platform.python_version(),
                "CPU Usage": f"{psutil.cpu_percent()}%",
                "Memory Usage": f"{psutil.virtual_memory().percent}%",
                "Connection Status": self.connection_status,
                "Current View": self.current_view,
                "MCP Client": "Connected" if self.mcp_client else "Disconnected"
            }
            
            # Format info message
            info_lines = [f"{key}: {value}" for key, value in system_info.items()]
            info_message = "\n".join(info_lines)
            
            self.notify(info_message, title="System Information", timeout=10)
            
        except ImportError:
            # Fallback without psutil
            basic_info = {
                "Platform": platform.system(),
                "Python Version": platform.python_version(),
                "Connection Status": self.connection_status,
                "Current View": self.current_view,
            }
            info_lines = [f"{key}: {value}" for key, value in basic_info.items()]
            info_message = "\n".join(info_lines)
            self.notify(info_message, title="System Information", timeout=10)
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            self.notify("Failed to retrieve system information", severity="error")
    
    async def action_toggle_theme(self) -> None:
        """Toggle between light and dark themes"""
        # Get current theme from config
        current_theme = self.config_service.get_ui_preferences().get("theme", "dark")
        new_theme = "light" if current_theme == "dark" else "dark"
        
        # Update theme in config
        ui_prefs = self.config_service.get_ui_preferences()
        ui_prefs["theme"] = new_theme
        self.config_service.set_ui_preferences(ui_prefs)
        
        # Apply theme (this would require CSS variable updates)
        self.notify(f"Theme switched to {new_theme}", severity="information")
        # TODO: Implement actual theme switching with CSS variables
    
    async def action_zoom_in(self) -> None:
        """Increase UI scale"""
        self.notify("Zoom in (use terminal font size controls)", severity="information")
    
    async def action_zoom_out(self) -> None:
        """Decrease UI scale"""
        self.notify("Zoom out (use terminal font size controls)", severity="information")
    
    async def action_zoom_reset(self) -> None:
        """Reset UI scale"""
        self.notify("Zoom reset (use terminal font size controls)", severity="information")
    
    def watch_current_view(self, new_view: str) -> None:
        """React to current view changes"""
        self.sub_title = f"Current: {new_view.title()}"
    
    def watch_connection_status(self, status: str) -> None:
        """React to connection status changes"""
        if status == "connected":
            self.notify("Connected to MCP server", severity="information")
        elif status == "error":
            self.notify("MCP connection failed", severity="error")
    
    async def on_unmount(self) -> None:
        """Cleanup when application is closing"""
        self.logger.info("MCP TUI Client shutting down")
        
        # Cleanup MCP client
        if self.mcp_client:
            try:
                await self.mcp_client.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting MCP client: {e}")
        
        # Save user preferences
        try:
            self.config_service.save_config()
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    async def _handle_navigation(self, view_id: str, context: Dict[str, Any]) -> None:
        """Handle navigation manager view changes"""
        # Map view IDs to action methods
        view_actions = {
            "dashboard": self.action_show_dashboard,
            "bots": self.action_show_bots,
            "labs": self.action_show_labs,
            "scripts": self.action_show_scripts,
            "workflows": self.action_show_workflows,
            "markets": self.action_show_markets,
            "analytics": self.action_show_analytics,
            "settings": self.action_show_settings,
        }
        
        action = view_actions.get(view_id)
        if action:
            await action()


def main():
    """Main entry point for the TUI application"""
    app = MCPTUIApp()
    app.run()


if __name__ == "__main__":
    main()