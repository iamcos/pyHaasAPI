import asyncio
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Button, DataTable, Input, Static
from textual.screen import Screen
from textual.worker import Worker, get_current_worker
from textual import work
from pyHaasAPI.core.server_manager import ServerManager, ServerConfig, ServerStatus
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.client import AsyncHaasClient

class ServerScreen(Static):
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
        self.server_manager = tui_app.server_manager

    def compose(self) -> ComposeResult:
        yield Label("Manage Servers & Resources", id="screen-title")
        yield DataTable(id="server-table")
        yield Horizontal(
            Button("Add Server", variant="success", id="add-server-btn"),
            Button("Refresh Stats", variant="primary", id="refresh-btn"),
            classes="button-bar"
        )
        yield Vertical(id="edit-form", classes="hidden")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        # Store column keys for later updates
        self.col_cpu = table.add_column("CPU", key="cpu")
        self.col_ram = table.add_column("RAM", key="ram")
        self.col_disk = table.add_column("Disk", key="disk")
        self.col_bots = table.add_column("Bots", key="bots")
        # Add static columns at start
        table.add_column("Name", key="name")
        table.add_column("Host", key="host")
        table.add_column("Status", key="status")
        
        # Re-order columns visually
        table.cursor_type = "row"
        self.refresh_table()
        # Auto-refresh every 10 seconds for the main list (to be safe with sequential SSH)
        self.set_interval(10, self.refresh_table)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn":
            self.refresh_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # Extract the actual value from the RowKey object
        server_name = str(event.row_key.value)
        from .server_detail_screen import ServerDetailScreen
        content = self.app.query_one("#main-content")
        
        # Replace current screen with details
        for child in content.children:
            child.remove()
        content.mount(ServerDetailScreen(self.tui_app, server_name))

    @work(exclusive=True)
    async def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        
        # Determine current active server
        active = self.server_manager.get_active_server_name()

        # If table is empty, do full build
        if table.row_count == 0:
            for name, srv in self.server_manager.servers.items():
                status_str = "CONNECTED" if srv.status == ServerStatus.CONNECTED else srv.status.value.upper()
                if active == name:
                    status_str = f"[bold green]{status_str}[/]"
                    
                table.add_row(
                    "...", "...", "...", "...",
                    name, srv.config.hostname, status_str,
                    key=name
                )
        else:
            # Just update the Status column for already existing rows
            for name, srv in self.server_manager.servers.items():
                try:
                    status_str = "CONNECTED" if srv.status == ServerStatus.CONNECTED else srv.status.value.upper()
                    if active == name:
                        status_str = f"[bold green]{status_str}[/]"
                    table.update_cell(name, "status", status_str)
                except Exception: pass

        # Second pass: Fetch live data
        # We process them sequentially with a small delay to avoid overwhelming the network
        # and respect the "sequentially connectable" environment if it affects SSH.
        for name in list(self.server_manager.servers.keys()):
            self.fetch_server_stats(name)
            await asyncio.sleep(0.1)

    @work(group="server_stats")
    async def fetch_server_stats(self, server_name: str) -> None:
        table = self.query_one(DataTable)
        
        # 1. Fetch Resources via SSH (Non-tunneling)
        resources = await self.server_manager.get_server_resources(server_name)
        
        # 2. Fetch Bot Count
        bot_count = "[dim]n/a[/]"
        srv_status = self.server_manager.servers.get(server_name)
        haas_status = resources.get("haas_status", "Unk")
        
        if srv_status and srv_status.status == ServerStatus.CONNECTED:
            try:
                # Active tunnel check
                client = AsyncHaasClient(self.tui_app.settings.api_config)
                client.config.port = srv_status.config.local_ports[0]
                auth_manager = self.tui_app.get_auth_manager(server_name, client)
                
                async with client:
                    from pyHaasAPI.api.bot.bot_api import BotAPI
                    bot_api = BotAPI(client, auth_manager)
                    bots = await bot_api.get_all_bots()
                    active_bots = sum(1 for b in bots if b.status == "ACTIVE")
                    bot_count = f"[bold green]{active_bots}[/]/[white]{len(bots)}[/]"
            except Exception:
                bot_count = "[red]API Err[/]"
        else:
             if haas_status == "Running":
                 bot_count = "[cyan]Running (no tunnel)[/]"
             elif haas_status == "Stopped":
                 bot_count = "[yellow]Stopped[/]"
             else:
                 bot_count = "[dim]n/a[/]"

        # Update table safely
        cpu = resources.get("cpu_load", "[red]Err[/]")
        ram = resources.get("ram_usage", "[red]Err[/]")
        disk = resources.get("disk_usage", "[red]Err[/]")
        
        if not resources.get("success"):
            error_preview = resources.get("error", "Timeout")[:15]
            cpu = ram = disk = f"[red]{error_preview}[/]"

        self._update_row_safe(table, server_name, cpu, ram, disk, bot_count)

    def _update_row_safe(self, table: DataTable, row_key: str, cpu: str, ram: str, disk: str, bots: str) -> None:
        try:
            # Direct update as we are in the main event loop (Async worker)
            table.update_cell(row_key, "cpu", cpu)
            table.update_cell(row_key, "ram", ram)
            table.update_cell(row_key, "disk", disk)
            table.update_cell(row_key, "bots", bots)
            
            # Refresh status column too in case it changed during fetch
            srv = self.server_manager.servers.get(row_key)
            if srv:
                status_str = "CONNECTED" if srv.status == ServerStatus.CONNECTED else srv.status.value.upper()
                if self.server_manager.active_server == row_key:
                    status_str = f"[bold green]{status_str}[/]"
                table.update_cell(row_key, "status", status_str)
        except Exception:
            pass


