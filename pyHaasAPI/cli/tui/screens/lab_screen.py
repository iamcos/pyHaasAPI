from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Button, DataTable, Static, Input, ListView, ListItem
from textual.screen import Screen
from textual.binding import Binding

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig

class LabScreen(Vertical):
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
        self.server_manager = tui_app.server_manager
        from pyHaasAPI.core.logging import get_logger
        self.logger = get_logger("LabScreen")

    def compose(self) -> ComposeResult:
        yield Label("Server Labs", id="screen-title")
        yield ListView(id="lab-sweep-list")
        yield Label("Ready", id="lab-status-label")
        yield Horizontal(
            Button("Refresh", variant="primary", id="refresh-labs-btn"),
            Button("Sync All", variant="default", id="sync-all-labs-btn"),
            classes="button-bar"
        )

    def on_mount(self) -> None:
        self.run_worker(self.refresh_projects())

    async def refresh_projects(self) -> None:
        # In a real impl, we'd load projects from projects.json
        # For sweep view, we fetch current labs from all servers
        list_view = self.query_one("#lab-sweep-list")
        status_label = self.query_one("#lab-status-label")
        list_view.clear()
        status_label.update("📡 [yellow]Fetching lab projects...[/]")
        self.app.notify("Syncing labs from all servers...", title="Lab Refresh", severity="information")
        self.tui_app.cached_analysis.refresh_lab_counts()
        
        total_labs = 0
        for server_name in self.server_manager.servers.keys():
            try:
                async with self.server_manager.server_session(server_name):
                    config = APIConfig()
                    config.port = self.server_manager.get_active_server_config().local_ports[0]
                    
                    async with AsyncHaasClient(config) as client:
                        auth = self.tui_app.get_auth_manager(server_name, client)
                        await auth.ensure_authenticated()
                        lab_api = LabAPI(client, auth)
                        labs = await lab_api.get_labs()
                        for lab in labs:
                            local_count = self.tui_app.cached_analysis.get_local_count(lab.lab_id)
                            sync_pct = (local_count / lab.completed_backtests * 100) if lab.completed_backtests > 0 else 0
                            
                            status_style = "green" if sync_pct >= 100 and local_count > 0 else "yellow"
                            sync_info = f"[{status_style}]{local_count}/{lab.completed_backtests}[/]"
                            
                            label_text = f"[cyan][{server_name}][/] [white]{lab.name}[/] {sync_info}"
                            item = ListItem(Label(label_text))
                            # Store metadata for selection
                            item.lab_data = {
                                "server_name": server_name,
                                "lab_id": str(lab.lab_id),
                                "name": lab.name
                            }
                            list_view.append(item)
                            total_labs += 1
            except Exception as e:
                self.logger.exception(f"Critical error fetching labs from {server_name}")
                list_view.append(ListItem(Label(f"[red][{server_name}] Error: {str(e)[:60]}[/]")))
        
        status_label.update(f"✅ Found [bold green]{total_labs}[/] labs across all servers.")
        self.app.notify(f"Total labs found: {total_labs}", title="Labs Updated")

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if hasattr(event.item, "lab_data"):
            data = event.item.lab_data
            self.logger.info(f"Lab selected: {data}")
            self.app.notify(f"Opening {data['name']} on {data['server_name']}...")
            from .lab_detail_screen import LabDetailScreen
            content = self.app.query_one("#main-content")
            for child in content.children:
                child.remove()
            content.mount(LabDetailScreen(self.app, data["server_name"], data["lab_id"], data["name"]))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-labs-btn":
            await self.refresh_projects()
        elif event.button.id == "sync-all-labs-btn":
            self.app.notify("Starting global lab sync...")
            self.run_worker(self._manual_global_sync())

    async def _manual_global_sync(self):
        """Perform manual sync and refresh UI after."""
        # Pass full_sweep=True to ignore the auto-sync toggle for manual trigger
        await self.tui_app.lab_sync_service.sync_all_servers(full_sweep=True)
        await self.refresh_projects()
        self.app.notify("Global lab sync completed.")

class MarketSelectModal(Screen):
    """A modal screen for fuzzy searching and selecting markets."""
    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Select Markets (Fuzzy Search)", id="modal-title"),
            Input(placeholder="Type to filter markets...", id="market-search-input"),
            ListView(id="market-results"),
            Horizontal(
                Button("Done", variant="success", id="done-btn"),
                Button("Cancel", variant="error", id="cancel-btn"),
            ),
            id="modal-container"
        )
