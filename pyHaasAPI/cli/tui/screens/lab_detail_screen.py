import asyncio
import json
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import Label, Button, DataTable, Static, ProgressBar, ListView, ListItem
from textual.screen import ModalScreen

from pyHaasAPI.core.analysis_manager import AnalysisManager
from pyHaasAPI.api.backtest import BacktestAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.config.api_config import APIConfig

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

    def compose(self) -> ComposeResult:
        yield Label(f"Lab Analysis: [bold cyan]{self.lab_name}[/]", id="screen-title")
        
        with Container(id="analysis-metrics-container"):
            yield Label("Performance Summary", classes="section-header")
            yield DataTable(id="analysis-table")
            
        with Vertical(id="analysis-controls"):
            yield Label("Background Sync Status", classes="section-header")
            yield Label("Idle", id="sync-status")
            yield ProgressBar(total=100, show_percentage=True, id="sync-progress")
            yield Horizontal(
                Button("Download & Analyze All", variant="primary", id="start-sync-btn"),
                Button("Create Bot from Best", variant="success", id="create-bot-btn"),
                Button("Add to Project", variant="default", id="add-to-proj-btn"),
                Button("Back to Labs", variant="error", id="back-btn"),
                classes="button-bar"
            )

    def on_mount(self) -> None:
        table = self.query_one("#analysis-table", DataTable)
        table.add_columns("Backtest ID", "Net Profit", "Win Rate%", "DD%", "Trades", "ROE%")
        self.run_worker(self.fetch_backtest_list())

    async def fetch_backtest_list(self) -> None:
        """Fetch list of backtest IDs from server."""
        try:
            async with self.tui_app.server_manager.server_session(self.server_name):
                config = APIConfig()
                config.port = self.tui_app.server_manager.get_active_server_config().local_ports[0]
                
                async with AsyncHaasClient(config) as client:
                    auth = self.tui_app.get_auth_manager(self.server_name, client)
                    await auth.ensure_authenticated()
                    
                    backtest_api = BacktestAPI(client, auth)
                    # Use get_backtest_results to get the list
                    results = await backtest_api.get_backtest_results(self.lab_id)
                    self.backtest_ids = [getattr(r, "backtest_id") for r in results]
                    
                    self.query_one("#sync-status").update(f"Found {len(self.backtest_ids)} backtests.")
                    await self.refresh_analysis_table()
        except Exception as e:
            self.tui_app.notify(f"Error fetching backtests: {e}", severity="error")

    async def refresh_analysis_table(self) -> None:
        """Update table with cached analysis results."""
        table = self.query_one("#analysis-table", DataTable)
        table.clear()
        
        metrics_list = await self.analysis_manager.analyze_lab(self.server_name, self.lab_id, self.backtest_ids)
        for m in metrics_list:
            table.add_row(
                m.backtest_id[:8],
                f"{m.net_profit:.2f}",
                f"{m.win_rate_pct:.1f}%",
                f"{m.max_drawdown_pct:.1f}%",
                str(m.total_trades),
                f"{(m.net_profit / 1000 * 100):.1f}%" # Assuming 1000 base for ROE
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            from .lab_screen import LabScreen
            content = self.tui_app.query_one("#main-content")
            for child in content.children:
                child.remove()
            content.mount(LabScreen(self.tui_app))
            
        elif event.button.id == "start-sync-btn":
            await self.start_sync()
        elif event.button.id == "create-bot-btn":
            await self.create_bot_from_best()
        elif event.button.id == "add-to-proj-btn":
            self.tui_app.push_screen(
                AddToProjectModal(list(self.tui_app.project_manager.projects.keys())),
                self.handle_add_to_project
            )

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

    async def start_sync(self) -> None:
        """Trigger background download and periodic UI refresh."""
        self.query_one("#sync-status").update("📥 [yellow]Downloading reports...[/]")
        
        async with self.tui_app.server_manager.server_session(self.server_name):
            config = APIConfig()
            config.port = self.tui_app.server_manager.get_active_server_config().local_ports[0]
            
            async with AsyncHaasClient(config) as client:
                auth = self.tui_app.get_auth_manager(self.server_name, client)
                await auth.ensure_authenticated()
                
                # Start background task in manager
                await self.analysis_manager.start_background_download(
                    self.server_name, self.lab_id, self.backtest_ids, client, auth
                )
                
                self.run_worker(self.monitor_sync_progress())

    async def monitor_sync_progress(self) -> None:
        """Poll cache status and update table."""
        pb = self.query_one("#sync-progress", ProgressBar)
        while True:
            cached_count = sum(1 for bt_id in self.backtest_ids if self.analysis_manager.is_cached(self.server_name, self.lab_id, bt_id))
            if self.backtest_ids:
                progress = (cached_count / len(self.backtest_ids)) * 100
                pb.update(progress=progress)
            
            if cached_count == len(self.backtest_ids) and cached_count > 0:
                self.query_one("#sync-status").update("✅ [green]Analysis Complete[/]")
                await self.refresh_analysis_table()
                break
            
            await self.refresh_analysis_table()
            await asyncio.sleep(2)
