import asyncio
import json
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Button, DataTable, Static, ProgressBar, ListView, ListItem
from textual.screen import ModalScreen
from typing import List, Any
from pyHaasAPI.analysis.metrics import RunMetrics

from pyHaasAPI.core.analysis_manager import AnalysisManager
from pyHaasAPI.api.backtest import BacktestAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.stage2_service import Stage2Service

class CreateProjectModal(ModalScreen[tuple[str, str]]):
    """Modal for creating a new project."""
    def compose(self) -> ComposeResult:
        with Vertical(id="modal-content"):
            yield Label("Create New Project", id="modal-title")
            from textual.widgets import Input
            yield Input(placeholder="Project Name", id="new-proj-name")
            yield Input(placeholder="Description (Optional)", id="new-proj-desc")
            with Horizontal(id="modal-buttons"):
                yield Button("Create", variant="success", id="create-btn")
                yield Button("Cancel", variant="error", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            name = self.query_one("#new-proj-name").value
            desc = self.query_one("#new-proj-desc").value
            if name:
                self.dismiss((name, desc))
        else:
            self.dismiss(None)

class AddToProjectModal(ModalScreen[str]):
    """Modal for selecting a project to add a lab to."""
    def __init__(self, projects: list[str]):
        super().__init__()
        self.projects = projects

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-content"):
            yield Label("Select Project", id="modal-title")
            if not self.projects:
                 yield Label("[dim]No projects found. Create one first![/]")
                 yield Button("Close", id="cancel-btn")
            else:
                yield ListView(*[ListItem(Label(p), id=f"proj-{p}") for p in self.projects], id="project-selector")
                with Horizontal(id="modal-buttons"):
                    yield Button("Cancel", variant="error", id="cancel-btn")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item and event.item.id:
            project_name = event.item.id.replace("proj-", "")
            self.dismiss(project_name)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

class LabDetailScreen(Vertical):
    def __init__(self, tui_app, server_name: str, lab_id: str, lab_name: str):
        super().__init__()
        self.tui_app = tui_app
        self.server_name = server_name
        self.lab_id = lab_id
        self.lab_name = lab_name
        self.analysis_manager = tui_app.analysis_manager
        self.backtest_ids = []
        self.metrics_list: List[RunMetrics] = []
        self.auto_sync = tui_app.lab_sync_service.is_auto_sync_enabled(server_name, lab_id)
        self.remote_count = 0

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.server_name}] Lab Analysis: [bold cyan]{self.lab_name}[/]", id="screen-title")
        
        with Container(id="analysis-metrics-container"):
            yield Label("Performance Summary", classes="section-header")
            yield DataTable(id="analysis-table")
            
        with Vertical(id="analysis-controls"):
            yield Label("Synchronization Status", classes="section-header")
            with Horizontal(id="sync-status-container"):
                yield Label("Idle", id="sync-status")
                yield Button("Auto-Sync: OFF", id="toggle-auto-sync-btn", variant="default", classes="mini-btn")
            yield ProgressBar(total=100, show_percentage=True, id="sync-progress")
            yield Horizontal(
                Button("Download All", variant="primary", id="start-sync-btn"),
                Button("Visualize", variant="warning", id="visualize-btn"),
                Button("Finetune", variant="success", id="finetune-btn"),
                classes="button-bar"
            )
            yield Label("Project Actions", classes="section-header")
            yield Horizontal(
                Button("Add to Project", variant="default", id="add-to-proj-btn"),
                Button("Create Project", variant="default", id="create-proj-btn"),
                Button("Create Bot", variant="primary", id="create-bot-btn"),
                Button("Back to Labs", variant="error", id="back-btn"),
                classes="button-bar"
            )

    def on_mount(self) -> None:
        table = self.query_one("#analysis-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Add sortable columns
        table.add_columns(
            "Backtest ID", 
            "Net Profit", 
            "Win Rate%", 
            "DD%", 
            "Trades", 
            "ROE%"
        )
        
        # Track current sort
        self.sort_column = "ROE%"
        self.sort_reverse = True
        
        # Initialize auto-sync state from service
        self.auto_sync = self.tui_app.lab_sync_service.is_auto_sync_enabled(self.server_name, self.lab_id)
        self._update_auto_sync_ui()
        
        self.run_worker(self.fetch_backtest_list())

    async def fetch_backtest_list(self) -> None:
        """Fetch list of backtest IDs from server."""
        try:
            async with self.tui_app.server_manager.server_session(self.server_name):
                config = APIConfig()
                config.port = self.tui_app.server_manager.servers[self.server_name].config.local_ports[0]
                
                async with AsyncHaasClient(config) as client:
                    auth = self.tui_app.get_auth_manager(self.server_name, client)
                    await auth.ensure_authenticated()
                    
                    backtest_api = BacktestAPI(client, auth)
                    # Use get_all_backtests_for_lab to get the list
                    results = await backtest_api.get_all_backtests_for_lab(self.lab_id)
                    online_ids = [getattr(r, "backtest_id") for r in results]
                    self.remote_count = len(online_ids)
                    
                    # Merge with local cache
                    self.backtest_ids = await self.tui_app.analysis_manager.get_all_available_backtest_ids(self.lab_id, online_ids)
                    
                    self._update_sync_status_label()
                    await self.refresh_analysis_table()
        except Exception as e:
            self.tui_app.notify(f"Error fetching backtests: {e}", severity="error")

    def _update_auto_sync_ui(self) -> None:
        """Update the auto-sync button appearance."""
        btn = self.query_one("#toggle-auto-sync-btn", Button)
        btn.label = f"Auto-Sync: {'ON' if self.auto_sync else 'OFF'}"
        btn.variant = "success" if self.auto_sync else "default"

    def _update_sync_status_label(self) -> None:
        """Update the status label with local/remote counts"""
        local_count = sum(1 for bt_id in self.backtest_ids if self.analysis_manager.is_cached(self.server_name, self.lab_id, bt_id))
        
        if self.remote_count > 0:
            if local_count >= self.remote_count:
                status = f"✅ [green]Synced ({local_count}/{self.remote_count})[/]"
            else:
                status = f"📥 [yellow]Progress: {local_count}/{self.remote_count}[/]"
        else:
            status = "[dim]0/0 (No data)[/]"
            
        self.query_one("#sync-status").update(status)

    async def refresh_analysis_table(self) -> None:
        """Update table with cached analysis results."""
        from rich.text import Text
        
        table = self.query_one("#analysis-table", DataTable)
        table.clear()
        
        self.metrics_list = await self.analysis_manager.analyze_lab(self.server_name, self.lab_id, self.backtest_ids)
        
        # Sort metrics based on current sort column
        self._sort_metrics()
        
        # Add rows with color coding
        for idx, m in enumerate(self.metrics_list):
            # Color code ROI
            roi_text = Text(f"{m.roi_pct:.1f}%")
            if m.roi_pct > 10:
                roi_text.stylize("bold green")
            elif m.roi_pct > 0:
                roi_text.stylize("green")
            elif m.roi_pct < -10:
                roi_text.stylize("bold red")
            elif m.roi_pct < 0:
                roi_text.stylize("red")
            
            # Color code win rate
            wr_text = Text(f"{m.win_rate_pct:.1f}%")
            if m.win_rate_pct >= 60:
                wr_text.stylize("green")
            elif m.win_rate_pct >= 50:
                wr_text.stylize("yellow")
            else:
                wr_text.stylize("red")
            
            # Color code drawdown
            dd_text = Text(f"{m.max_drawdown_pct:.1f}%")
            if m.max_drawdown_pct < 10:
                dd_text.stylize("green")
            elif m.max_drawdown_pct < 20:
                dd_text.stylize("yellow")
            else:
                dd_text.stylize("red")
            
            # Highlight top 3 performers
            bt_id = Text(m.backtest_id[:8])
            if idx < 3:
                bt_id.stylize("bold cyan")
            
            table.add_row(
                bt_id,
                f"{m.net_profit:.2f}",
                wr_text,
                dd_text,
                str(m.total_trades),
                roi_text
            )
    
    def _sort_metrics(self) -> None:
        """Sort metrics based on current sort column."""
        sort_key_map = {
            "Backtest ID": lambda x: x.backtest_id,
            "Net Profit": lambda x: x.net_profit,
            "Win Rate%": lambda x: x.win_rate_pct,
            "DD%": lambda x: x.max_drawdown_pct,
            "Trades": lambda x: x.total_trades,
            "ROE%": lambda x: x.roi_pct
        }
        
        if self.sort_column in sort_key_map:
            self.metrics_list.sort(key=sort_key_map[self.sort_column], reverse=self.sort_reverse)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "back-btn":
            from .lab_screen import LabScreen
            content = self.tui_app.query_one("#main-content")
            for child in content.children:
                child.remove()
            content.mount(LabScreen(self.tui_app))
            
        elif button_id == "start-sync-btn":
            await self.start_sync()
        elif button_id == "visualize-btn":
            if not self.metrics_list:
                self.tui_app.notify("No analyzed data to visualize. Sync first!", severity="warning")
                return
            from .lab_visualization_screen import LabVisualizationScreen
            content = self.tui_app.query_one("#main-content")
            for child in content.children:
                child.remove()
            content.mount(LabVisualizationScreen(self.tui_app, self.server_name, self.lab_id, self.lab_name, self.metrics_list))
        elif button_id == "create-bot-btn":
            await self.create_bot_from_best()
        elif button_id == "add-to-proj-btn":
            self.tui_app.push_screen(
                AddToProjectModal(list(self.tui_app.project_manager.projects.keys())),
                self.handle_add_to_project
            )
        elif button_id == "create-proj-btn":
            self.tui_app.push_screen(
                CreateProjectModal(),
                self.handle_create_project
            )
        elif button_id == "toggle-auto-sync-btn":
            self.tui_app.lab_sync_service.toggle_auto_sync(self.server_name, self.lab_id)
            self.auto_sync = self.tui_app.lab_sync_service.is_auto_sync_enabled(self.server_name, self.lab_id)
            self._update_auto_sync_ui()
            self.app.notify(f"Auto-Sync {'enabled' if self.auto_sync else 'disabled'}")
            if self.auto_sync:
                self.run_worker(self.start_sync())
        elif button_id == "finetune-btn":
            self.tui_app.notify("Finetuning feature coming soon!", severity="info")
    
    async def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header clicks for sorting."""
        column_key = event.column_key
        table = event.data_table
        
        # Get column label from key
        column_label = str(column_key.value) if hasattr(column_key, 'value') else str(column_key)
        
        # Toggle sort direction if same column, otherwise default to descending
        if self.sort_column == column_label:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_label
            # Default sort direction based on column type
            self.sort_reverse = column_label not in ["DD%"]  # Ascending for drawdown, descending for others
        
        # Refresh table with new sort
        await self.refresh_analysis_table()
        
        # Update column headers with sort indicators
        self._update_column_headers()
    
    def _update_column_headers(self) -> None:
        """Update column headers to show sort indicators."""
        table = self.query_one("#analysis-table", DataTable)
        
        # Note: Textual DataTable doesn't support dynamic header updates easily
        # So we'll show sort info in the status label instead
        sort_dir = "▼" if self.sort_reverse else "▲"
        self.tui_app.notify(f"Sorted by {self.sort_column} {sort_dir}", timeout=2)
    
    def handle_create_project(self, data: tuple[str, str] | None) -> None:
        if data:
            name, desc = data
            try:
                self.tui_app.project_manager.create_project(name, desc)
                self.tui_app.notify(f"Created project '{name}'")
                # Now add the lab to it
                self.handle_add_to_project(name)
            except Exception as e:
                self.tui_app.notify(f"Failed to create project: {e}", severity="error")

    def handle_add_to_project(self, project_name: str | None) -> None:
        if project_name:
            from pyHaasAPI.models.project import LabProjectConfig
            lab_config = LabProjectConfig(
                lab_id=self.lab_id,
                lab_name=self.lab_name,
                server_name=self.server_name
            )
            if self.tui_app.project_manager.add_lab_to_project(project_name, lab_config):
                self.tui_app.notify(f"Added '{self.lab_name}' to project '{project_name}'")
            else:
                self.tui_app.notify(f"Lab already in project '{project_name}'", severity="warning")

    async def create_bot_from_best(self) -> None:
        """Create a bot from the top backtest configuration."""
        metrics_list = await self.analysis_manager.analyze_lab(self.server_name, self.lab_id, self.backtest_ids)
        if not metrics_list:
            self.tui_app.notify("No analyzed backtests found. Please sync first!", severity="error")
            return
            
        best = metrics_list[0]
        self.tui_app.notify(f"Creating bot from backtest {best.backtest_id[:8]}...", title="Bot Creation")
        
        try:
            async with self.tui_app.server_manager.server_session(self.server_name):
                config = APIConfig()
                config.port = self.tui_app.server_manager.get_active_server_config().local_ports[0]
                
                async with AsyncHaasClient(config) as client:
                    auth = self.tui_app.get_auth_manager(self.server_name, client)
                    await auth.ensure_authenticated()
                    
                    from pyHaasAPI.api.bot.bot_api import BotAPI
                    bot_api = BotAPI(client, auth)
                    
                    bot_name = f"Lab_{self.lab_name[:10]}_{best.net_profit:.0f}P"
                    await bot_api.create_bot_from_lab(self.lab_id, best.backtest_id, bot_name)
                    
                    self.tui_app.notify(f"Successfully created bot: {bot_name}", severity="information")
        except Exception as e:
            self.tui_app.notify(f"Failed to create bot: {e}", severity="error")

    async def run_finetune(self) -> None:
        """Clone lab and apply winning parameters."""
        if not self.metrics_list:
            self.tui_app.notify("No analyzed backtests found. Sync first!", severity="error")
            return
            
        best = self.metrics_list[0]
        self.tui_app.notify(f"Finetuning based on backtest {best.backtest_id[:8]}...", title="Finetune")
        
        try:
            async with self.tui_app.server_manager.server_session(self.server_name):
                # We need Stage2Service
                async with self.tui_app.server_manager.server_session(self.server_name):
                    config = APIConfig()
                    config.port = self.tui_app.server_manager.get_active_server_config().local_ports[0]
                    
                    async with AsyncHaasClient(config) as client:
                        auth = self.tui_app.get_auth_manager(self.server_name, client)
                        await auth.ensure_authenticated()
                        
                        from pyHaasAPI.api.lab.lab_api import LabAPI
                        from pyHaasAPI.api.script.script_api import ScriptAPI
                        lab_api = LabAPI(client, auth)
                        script_api = ScriptAPI(client, auth)
                        
                        stage2 = Stage2Service(lab_api, script_api)
                        
                        # Get full runtime data for parameters
                        runtime = await self.analysis_manager.extractor._extract_raw_runtime(
                            self.analysis_manager.get_report_path(self.server_name, self.lab_id, best.backtest_id)
                        )
                        winning_params = runtime.get("Data", {}).get("P", {})
                        
                        new_lab_id = await stage2.clone_for_finetune(
                            self.lab_id, f"{self.lab_name[:10]}_FT", winning_params
                        )
                        
                        self.tui_app.notify(f"Finetune Lab Created! ID: {new_lab_id[:8]}", severity="success")
        except Exception as e:
            self.tui_app.notify(f"Finetune Failed: {e}", severity="error")

    async def start_sync(self) -> None:
        """Trigger background download and periodic UI refresh."""
        self.query_one("#sync-status").update("📥 [yellow]Downloading reports...[/]")
        
        # Use the unified sync service
        await self.tui_app.lab_sync_service.sync_lab(self.server_name, self.lab_id)
        
        # Start monitoring
        self.run_worker(self.monitor_sync_progress())

    async def monitor_sync_progress(self) -> None:
        """Poll cache status and update table."""
        pb = self.query_one("#sync-progress", ProgressBar)
        while True:
            cached_count = sum(1 for bt_id in self.backtest_ids if self.analysis_manager.is_cached(self.server_name, self.lab_id, bt_id))
            if self.backtest_ids:
                progress = (cached_count / len(self.backtest_ids)) * 100
                pb.update(progress=progress)
            
            self._update_sync_status_label()
            
            if cached_count == len(self.backtest_ids) and cached_count > 0:
                # If auto-sync is off, we stop. If it's on, we might want to stay alive?
                # Actually, monitor_sync_progress should finish when the current list is done.
                await self.refresh_analysis_table()
                break
            
            await self.refresh_analysis_table()
            await asyncio.sleep(2)
            
            # If auto-sync is ON, we might want to re-fetch the list occasionally?
            # For now, let's keep it simple: sync the known list.
