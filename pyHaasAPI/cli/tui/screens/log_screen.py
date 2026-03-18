from typing import List, Optional
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Button, DataTable, Static, Log
from textual.screen import Screen
from textual import work, on

from pyHaasAPI.core.server_log_service import ServerLogService
from pyHaasAPI.core.logging import get_logger

logger = get_logger("tui.logs")

class LogScreen(Screen):
    """Screen for viewing remote HTS logs and screen sessions."""
    
    def __init__(self, tui_app, server_name: str):
        super().__init__()
        self.tui_app = tui_app
        self.server_name = server_name
        self.log_service = ServerLogService(tui_app.server_manager)
        self._sessions = []

    def compose(self) -> ComposeResult:
        yield Label(f"Logs & Sessions: [bold cyan]{self.server_name}[/]", id="screen-title")
        
        with Horizontal(id="detail-header-actions"):
            yield Button("← Back", id="back-btn", variant="default")
            yield Button("Refresh Sessions", id="refresh-sessions-btn", variant="primary")
            yield Label("", id="log-status-msg")

        with Container(id="log-view-container"):
            with Vertical(classes="dashboard-card", id="sessions-list-card"):
                yield Label("📺 [bold]Active Screen Sessions[/]", classes="card-header")
                self.session_table = DataTable(id="session-table")
                yield self.session_table
            
            with Vertical(classes="dashboard-card", id="log-viewer-card"):
                yield Label("📄 [bold]Session Content / Logs[/]", classes="card-header")
                self.log_output = Log(id="log-display")
                yield self.log_output
                with Horizontal(classes="log-actions"):
                    yield Button("Export to File", id="export-logs-btn", variant="success")

    def on_mount(self) -> None:
        self.session_table.add_columns("ID", "Name", "Date", "Status")
        self.refresh_log_sessions()

    @work(exclusive=True)
    async def refresh_log_sessions(self) -> None:
        self.query_one("#log-status-msg", Label).update("Fetching sessions...")
        sessions = await self.log_service.list_screen_sessions(self.server_name)
        self.session_table.clear()
        self._sessions = sessions
        
        for s in sessions:
            self.session_table.add_row(s['id'], s['name'], s['date'], s['status'], key=s['id'])
        
        self.query_one("#log-status-msg", Label).update(f"Found {len(sessions)} sessions.")

    @on(DataTable.RowSelected, "#session-table")
    async def on_session_selected(self, event: DataTable.RowSelected) -> None:
        session_id = str(event.row_key.value)
        self.query_one("#log-status-msg", Label).update(f"Fetching snapshot for {session_id}...")
        snapshot = await self.log_service.get_screen_snapshot(self.server_name, session_id)
        
        log_widget = self.query_one("#log-display", Log)
        log_widget.clear()
        log_widget.write(snapshot)
        self.query_one("#log-status-msg", Label).update(f"Snapshot loaded for {session_id}.")

    @on(Button.Pressed)
    async def on_button_click(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id == "refresh-sessions-btn":
            self.run_worker(self.refresh_log_sessions())
        elif event.button.id == "export-logs-btn":
            self.export_current_logs()

    @work(exclusive=True)
    async def export_current_logs(self) -> None:
        output_file = f"logs_{self.server_name}_export.txt"
        success, msg = await self.log_service.export_filtered_logs(self.server_name, output_file)
        if success:
            self.app.notify(f"Logs exported to {output_file}", severity="information")
        else:
            self.app.notify(f"Export failed: {msg}", severity="error")
