from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, ListItem, ListView, Label, Placeholder
from textual.screen import Screen
from textual.binding import Binding
from pathlib import Path

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.logging import initialize_logging, get_logger
logger = get_logger("tui.app")

from .screens.server_screen import ServerScreen
from .screens.script_screen import ScriptScreen
from .screens.bot_screen import BotScreen
from .screens.lab_screen import LabScreen
from .screens.project_screen import ProjectScreen

class Sidebar(Vertical):
    def compose(self) -> ComposeResult:
        yield Label("⚡ PYHAAS V2", id="sidebar-title")
        yield ListView(
            ListItem(Label("🏠 Dashboard"), id="menu-dashboard"),
            ListItem(Label("� Projects"), id="menu-projects"),
            ListItem(Label("📜 Scripts"), id="menu-scripts"),
            ListItem(Label("🤖 Bot Monitor"), id="menu-bots"),
            ListItem(Label("🧪 Labs"), id="menu-labs"),
            ListItem(Label("🖥️ Servers"), id="menu-servers"),
            id="sidebar-menu"
        )

class DashboardScreen(Static):
    def compose(self) -> ComposeResult:
        yield Label("pyHaasAPI Dashboard", id="screen-title")
        
        with Container(id="dashboard-grid"):
            with Vertical(id="stats-summary"):
                yield Label("System Overview", classes="dashboard-header")
                self.server_count = Label("Servers: 0", classes="stat-item")
                self.bot_count = Label("Bots Monitoring: 0", classes="stat-item")
                yield self.server_count
                yield self.bot_count
            
            with Vertical(id="quick-actions"):
                yield Label("Quick Actions", classes="dashboard-header")
                yield Button("Refresh Status", variant="primary", id="dash-refresh-btn")
                yield Button("Server Manager", variant="default", id="dash-srv-btn")

    def on_mount(self) -> None:
        self.update_stats()

    def update_stats(self) -> None:
        try:
            # Safely access app.server_manager
            sm = self.app.server_manager
            self.server_count.update(f"Servers Configured: [cyan]{len(sm.servers)}[/]")
            # We can't know bot count without fetching, but we can show server IDs
            srv_list = ", ".join(sm.servers.keys())
            self.bot_count.update(f"Active Servers: [green]{srv_list}[/]")
        except Exception:
            pass

class HaasTUI(App):
    CSS = """
    Screen {
        background: #1e1e2e;
    }
    
    Sidebar {
        width: 30;
        background: #181825;
        border-right: tall #313244;
        padding: 1;
    }
    
    #sidebar-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        background: #313244;
        color: #f5e0dc;
        margin-bottom: 2;
        border: heavy #89b4fa;
        height: 3;
        content-align: center middle;
    }
    
    ListView {
        background: transparent;
    }
    
    ListItem {
        padding: 1 2;
        color: #cdd6f4;
    }
    
    ListItem:hover {
        background: #313244;
        color: #89b4fa;
    }
    
    ListItem.--highlight {
        background: #45475a;
        color: #fab387;
        text-style: bold;
    }
    
    #screen-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        color: #cba6f7;
        margin-bottom: 1;
        border-bottom: double #cba6f7;
    }
    
    #dashboard-grid {
        layout: grid;
        grid-size: 2;
        grid-gutter: 2;
        padding: 2;
    }
    
    #stats-summary, #quick-actions {
        border: panel #45475a;
        padding: 1;
        background: #181825;
    }
    
    .dashboard-header {
        text-style: bold;
        color: #89b4fa;
        margin-bottom: 1;
        text-align: center;
    }
    
    .stat-item {
        margin-left: 2;
        margin-bottom: 1;
    }
    
    .button-bar {
        height: 5;
        align: center middle;
        margin-top: 1;
        background: #11111b;
        border-top: tall #313244;
    }
    
    Button {
        min-width: 18;
    }

    DataTable {
        height: 1fr;
        border: solid #313244;
        background: #1e1e2e;
        color: #cdd6f4;
    }
    
    DataTable > .datatable--header {
        background: #313244;
        color: #f9e2af;
        text-style: bold;
    }
    
    #main-content {
        padding: 1;
        background: #1e1e2e;
        height: 1fr;
    }
    
    Footer {
        background: #11111b;
        color: #a6adc8;
    }
    
    Header {
        background: #11111b;
        color: #cdd6f4;
    }
    
    /* Lab Screen styles */
    #project-list, #lab-sweep-list {
        height: 1fr;
        border: solid #45475a;
        background: #11111b;
    }
    
    /* Modal styles */
    #modal-container, #modal-content {
        width: 80%;
        height: 80%;
        background: #181825;
        border: thick #89b4fa;
        padding: 2;
        align: center middle;
    }
    
    #modal-title {
        text-align: center;
        text-style: bold;
        color: #f9e2af;
        margin-bottom: 2;
    }
    
    #modal-buttons {
        margin-top: 2;
        align: center middle;
        height: 3;
    }

    #server-filter-bar {
        height: 3;
        margin-bottom: 1;
        align: left middle;
        background: #11111b;
        padding-left: 1;
        border: solid #313244;
    }

    #server-filter-label {
        color: #89b4fa;
        text-style: bold;
        padding-right: 1;
        padding-top: 1;
    }

    .server-filter-btn {
        margin-right: 1;
        min-width: 8;
        height: 1;
        border: none;
        background: #313244;
    }

    .server-filter-btn.active {
        background: #89b4fa;
        color: #11111b;
        text-style: bold;
    }

    #modal-lab-list {
        height: 1fr;
        border: solid #313244;
        background: #11111b;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    Input {
        background: #11111b;
        border: tall #313244;
        color: #cdd6f4;
        margin-bottom: 1;
    }
    
    Input:focus {
        border: tall #89b4fa;
    }

    LabScreen, ProjectScreen, BotScreen, LabDetailScreen {
        height: 1fr;
    }

    #project-layout-container {
        height: 1fr;
    }

    #project-list-sidebar {
        width: 30;
        border-right: solid #313244;
    }

    .sidebar-label {
        text-align: center;
        text-style: underline;
        color: #89b4fa;
        padding: 1;
    }
    
    /* Lab Detail Styles */
    #analysis-metrics-container {
        height: 1fr;
    }
    
    .section-header {
        text-style: bold;
        color: #f9e2af;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    #sync-status-container {
        height: 3;
        align: left middle;
        margin-bottom: 1;
    }
    
    #sync-status {
        width: 1fr;
        color: #cdd6f4;
    }
    
    .mini-btn {
        min-width: 15;
        height: 1;
        border: none;
        background: #313244;
        margin-left: 1;
    }

    #sync-progress {
        margin-bottom: 1;
    }

    /* Server Detail Styles */
    #dashboard-grid-detail {
        layout: grid;
        grid-size: 2;
        grid-rows: auto auto auto;
        grid-gutter: 0 1;
        padding: 1;
        overflow-y: scroll;
    }

    #resources-card {
        column-span: 1;
        height: auto;
    }

    #diagnostics-card {
        column-span: 1;
        height: auto;
    }

    #bots-card, #labs-card {
        column-span: 2;
        height: auto;
        min-height: 15;
        margin-top: 1;
    }

    #detail-bot-table, #detail-lab-table {
        height: auto;
        min-height: 13;
    }

    .dashboard-card {
        border: solid #45475a;
        background: #181825;
        padding: 0 1;
        margin: 0;
    }

    .card-header {
        text-align: left;
        color: #f9e2af;
        text-style: bold;
        padding: 0 1;
        width: 1fr;
    }

    .card-header-container {
        height: 3;
        background: #313244;
        align: left middle;
        margin-bottom: 1;
        padding: 0 1;
    }

    .header-btn {
        min-width: 14;
        height: 1;
        margin-left: 1;
        border: none;
        background: #45475a;
    }

    ResourceWidget {
        margin-bottom: 0;
        height: 1;
        padding: 0 1;
    }

    .res-label {
        width: 8;
        color: #89b4fa;
    }

    .res-value {
        width: 6;
        text-align: right;
        color: #a6e3a1;
    }

    ProgressBar {
        width: 1fr;
        margin-top: 0;
    }
    
    ProgressBar > .progressbar--bar {
        background: #313244;
    }
    
    ProgressBar > .progressbar--complete {
        background: #a6e3a1;
    }

    #sparkline-container {
        height: 3;
        margin: 0;
        background: #11111b;
        border: inner #313244;
    }

    .spark-box {
        width: 1fr;
        padding: 0;
    }

    .spark-box Label {
        text-align: center;
        color: #6c7086;
    }

    Sparkline {
        width: 1fr;
        height: 2;
        color: #89b4fa;
    }

    #cpu-sparkline {
        color: #fab387;
    }

    #ram-sparkline {
        color: #a6e3a1;
    }

    #diag-info {
        height: 1fr;
        padding: 1;
        color: #cdd6f4;
    }
    
    #restart-haas-btn {
        margin-top: 1;
    }

    #detail-header-actions {
        height: 3;
        align: left middle;
        padding: 0 2;
        background: #11111b;
        border-bottom: solid #313244;
    }

    #detail-header-actions Button {
        margin-right: 1;
        min-width: 12;
    }

    #detail-status-msg {
        margin-left: 2;
        color: #fab387;
        text-style: italic;
    }
    
    #detail-haas-status {
        text-align: center;
        margin-top: 1;
        text-style: bold;
    }

    #detail-bot-table, #detail-lab-table {
        height: 1fr;
    }

    /* Lab Visualization Styles */
    #analysis-metrics-container {
        height: 1fr;
        border: solid #45475a;
        margin: 1;
        padding: 1;
    }

    #viz-container {
        height: 1fr;
        overflow-y: scroll;
    }

    .viz-card {
        background: #1e1e2e;
        border: solid #45475a;
        margin: 1;
        padding: 1;
        min-height: 15;
    }

    #viz-grid {
        layout: grid;
        grid-size: 2;
        grid-gutter: 2;
        height: auto;
    }

    .ascii-chart {
        padding: 1;
        color: #89b4fa;
    }
    
    .section-header {
        text-style: bold;
        color: #f9e2af;
        margin-bottom: 1;
    }
    #log-view-container {
        layout: vertical;
        padding: 1;
        height: 1fr;
    }
    
    #sessions-list-card {
        height: 15;
        margin-bottom: 1;
    }
    
    #log-viewer-card {
        height: 1fr;
    }
    
    #log-display {
        background: #11111b;
        color: #cdd6f4;
        border: solid #313244;
        height: 1fr;
        font-family: monospace;
    }
    
    .log-actions {
        height: 3;
        align: right middle;
        padding-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Toggle dark mode"),
    ]

    def __init__(self):
        super().__init__()
        # Initialize logging
        initialize_logging()
        logger.info("TUI Application starting...")
        
        self.settings = Settings()
        self.server_manager = ServerManager(self.settings)
        
        # New Managers
        from pyHaasAPI.core.project_manager import ProjectManager
        from pyHaasAPI.core.analysis_manager import AnalysisManager
        from pyHaasAPI.core.project_orchestrator import ProjectOrchestrator
        self.project_manager = ProjectManager()
        self.analysis_manager = AnalysisManager(self)
        
        from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService
        self.cached_analysis = CachedAnalysisService(Path("unified_cache"))
        
        from pyHaasAPI.services.lab.lab_sync_service import LabSyncService
        self.lab_sync_service = LabSyncService(self)
        
        self.project_orchestrator = ProjectOrchestrator(self)

        # Cache auth managers to reuse sessions
        self.auth_managers: dict[str, AuthenticationManager] = {}

    def get_auth_manager(self, server_name: str, client: AsyncHaasClient) -> AuthenticationManager:
        """Get or create an AuthenticationManager for a server."""
        if server_name not in self.auth_managers:
            from pyHaasAPI.config.api_config import APIConfig
            
            # Use a fresh config for this manager
            config = APIConfig()
            srv_cfg = self.server_manager.servers[server_name].config
            config.port = srv_cfg.local_ports[0]
            config.server_name = server_name
            
            # Use specific credentials if set in servers.json
            if srv_cfg.api_email:
                config.email = srv_cfg.api_email
            if srv_cfg.api_password:
                config.password = srv_cfg.api_password
                
            self.auth_managers[server_name] = AuthenticationManager(client, config)
        
        # Update client reference in case it changed
        self.auth_managers[server_name].client = client
        return self.auth_managers[server_name]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Sidebar(),
            Container(DashboardScreen(), id="main-content"),
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Start background services."""
        await self.lab_sync_service.start()

    async def on_unmount(self) -> None:
        """Stop background services."""
        await self.lab_sync_service.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Global button handler for debugging and main menu."""
        # self.notify(f"Global Button: {event.button.id}")
        pass

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "sidebar-menu":
            return
            
        item_id = event.item.id
        content = self.query_one("#main-content")
        for child in content.children:
            child.remove()
        
        if item_id == "menu-dashboard":
            content.mount(DashboardScreen())
        elif item_id == "menu-servers":
            content.mount(ServerScreen(self))
        elif item_id == "menu-scripts":
            content.mount(ScriptScreen(self))
        elif item_id == "menu-projects":
            content.mount(ProjectScreen(self))
        elif item_id == "menu-bots":
            content.mount(BotScreen(self))  # Pass app reference
        elif item_id == "menu-labs":
            content.mount(LabScreen(self))  # Pass app reference

if __name__ == "__main__":
    app = HaasTUI()
    app.run()
