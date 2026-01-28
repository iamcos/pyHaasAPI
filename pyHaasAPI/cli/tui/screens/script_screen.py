from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Label, Button, DataTable, Static
from textual.screen import Screen

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.cli.download_cli import DownloadCLI

class ScriptScreen(Static):
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
        self.server_manager = tui_app.server_manager
        self.download_cli = DownloadCLI()
        self.download_cli.server_manager = self.server_manager

    def compose(self) -> ComposeResult:
        yield Label("Manage HaasScripts", id="screen-title")
        yield DataTable(id="script-table")
        yield Horizontal(
            Button("Download All", variant="success", id="download-all-btn"),
            Button("Refresh", variant="primary", id="refresh-scripts-btn"),
            classes="button-bar"
        )

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Server", "Script Name", "Status")
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        # In a real impl, we would fetch script names from local haasScripts dir
        # or call the API to get current ones.
        table.add_row("srv01", "Example script", "Local")
