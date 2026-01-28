from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, DataTable, Static
from textual.screen import Screen

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig

class BotScreen(Vertical):
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
        self.server_manager = tui_app.server_manager
        from pyHaasAPI.core.logging import get_logger
        self.logger = get_logger("BotScreen")

    def compose(self) -> ComposeResult:
        yield Label("Bot Sweep View", id="screen-title")
        yield DataTable(id="bot-table")
        yield Label("Ready", id="bot-status-label")
        yield Horizontal(
            Button("Refresh All", variant="primary", id="refresh-bots-btn"),
            classes="button-bar"
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Server", "Name", "Status", "ROE%")
        self.run_worker(self.refresh_bots())

    async def refresh_bots(self) -> None:
        table = self.query_one(DataTable)
        status_label = self.query_one("#bot-status-label")
        table.clear()
        status_label.update("📡 [yellow]Connecting to servers...[/]")
        self.app.notify("Fetching bots from all servers...", title="Bot Refresh", severity="information")
        
        total_bots = 0
        for server_name in self.server_manager.servers.keys():
            try:
                async with self.server_manager.server_session(server_name):
                    config = APIConfig()
                    config.port = self.server_manager.get_active_server_config().local_ports[0]
                    
                    async with AsyncHaasClient(config) as client:
                        auth = self.tui_app.get_auth_manager(server_name, client)
                        await auth.ensure_authenticated()
                        bot_api = BotAPI(client, auth)
                        bots = await bot_api.get_all_bots()
                        for b in bots:
                            # Colorize status
                            status = str(b.status).upper()
                            if status == "ACTIVE" or status == "RUNNING" or b.is_active:
                                status_display = f"[green]ACTIVE[/]"
                            elif "ERROR" in status or "FAILED" in status:
                                status_display = f"[red]{status}[/]"
                            else:
                                status_display = f"[yellow]{status}[/]"
                                
                            table.add_row(f"[cyan]{server_name}[/]", b.bot_name[:30], status_display, "N/A")
                            total_bots += 1
            except Exception as e:
                self.logger.exception(f"Critical error fetching bots from {server_name}")
                table.add_row(f"[red]{server_name}[/]", "[red]Error[/]", f"[red]{str(e)[:50]}[/]", "N/A")
        
        status_label.update(f"✅ Found [bold green]{total_bots}[/] bots across all servers.")
        self.app.notify(f"Total bots found: {total_bots}", title="Labs Updated")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-bots-btn":
            await self.refresh_bots()
