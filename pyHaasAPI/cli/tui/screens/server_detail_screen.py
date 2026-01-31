import asyncio
from typing import Optional, List, Dict, Any
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, Container, Grid
from textual.widgets import Label, Button, DataTable, Static, ProgressBar, Sparkline
from textual import work, on
from pyHaasAPI.core.logging import get_logger
logger = get_logger("tui.detail")

from pyHaasAPI.core.server_manager import ServerManager, ServerStatus
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.api.lab.lab_api import LabAPI

class ResourceWidget(Vertical):
    """A small widget to display a single resource metric with a label and value."""
    def __init__(self, label: str, unit: str = "%"):
        super().__init__()
        self.resource_label = label
        self.unit = unit
        self._value = "..."

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(f"[bold]{self.resource_label}:[/] ", classes="res-label")
            self.value_label = Label(self._value, classes="res-value")
            yield self.value_label
        yield ProgressBar(total=100, show_percentage=False, id=f"pb-{self.resource_label.lower()}")

    def update_value(self, value: str):
        self._value = value
        self.value_label.update(f"{value}{self.unit}" if value != "N/A" else "N/A")
        try:
            # Try to parse numeric part for progress bar
            numeric = float(value.replace("%", "").strip())
            self.query_one(ProgressBar).progress = numeric
        except (ValueError, Exception):
            pass

class ServerDetailScreen(Vertical):
    """Detailed dashboard for a specific server."""
    
    def __init__(self, tui_app, server_name: str):
        super().__init__()
        self.tui_app = tui_app
        # Ensure it's a string (in case RowKey was passed)
        from textual.widgets._data_table import RowKey
        if isinstance(server_name, RowKey):
            self.server_name = str(server_name.value)
        else:
            self.server_name = str(server_name)
        self.server_manager = tui_app.server_manager
        self.cpu_history = [0.0] * 50
        self.ram_history = [0.0] * 50
        
    def compose(self) -> ComposeResult:
        yield Label(f"Server Dashboard: [bold cyan]{self.server_name}[/]", id="screen-title")
        
        with Horizontal(id="detail-header-actions"):
            yield Button("← Back to List", id="back-to-list-btn", variant="default")
            yield Button("Connect", id="detail-connect-btn", variant="success")
            yield Button("Refresh", id="detail-refresh-btn", variant="primary")
            yield Label("", id="detail-status-msg")

        with Container(id="dashboard-grid-detail"):
            with Vertical(classes="dashboard-card", id="resources-card"):
                yield Label("🚀 [bold]System Resources[/]", classes="card-header")
                with Horizontal():
                    self.cpu_widget = ResourceWidget("CPU", unit="")
                    self.ram_widget = ResourceWidget("RAM")
                    self.disk_widget = ResourceWidget("Disk")
                    yield self.cpu_widget
                    yield self.ram_widget
                    yield self.disk_widget
                
                with Horizontal(id="sparkline-container"):
                    yield Vertical(Label("CPU History"), Sparkline(id="cpu-sparkline"), classes="spark-box")
                    yield Vertical(Label("RAM History"), Sparkline(id="ram-sparkline"), classes="spark-box")
                
                yield Label("Haas Status: [yellow]Checking...[/]", id="detail-haas-status")

            with Vertical(classes="dashboard-card", id="diagnostics-card"):
                yield Label("🔍 [bold]Diagnostics[/]", classes="card-header")
                self.diag_info = Static("Fetching diagnostics...", id="diag-info")
                yield self.diag_info
                yield Button("Restart Haas Service", id="restart-haas-btn", variant="warning")

            with Vertical(classes="dashboard-card", id="bots-card"):
                yield Label("🤖 [bold]Top Bots[/]", classes="card-header")
                self.bot_table = DataTable(id="detail-bot-table")
                yield self.bot_table

            with Vertical(classes="dashboard-card", id="labs-card"):
                yield Label("🧪 [bold]Active Labs[/]", classes="card-header")
                self.lab_table = DataTable(id="detail-lab-table")
                yield self.lab_table

    def on_mount(self) -> None:
        # Initialize tables
        bt = self.query_one("#detail-bot-table", DataTable)
        bt.add_columns("Name", "Status", "Market", "ROI%", "Trades")
        
        lt = self.query_one("#detail-lab-table", DataTable)
        lt.add_columns("Lab Name", "Status", "Completed", "Scheduled")
        
        self.refresh_stats()
        # High-frequency refresh for dedicated dashboard
        self.set_interval(3, self.refresh_stats)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        self.app.notify(f"Pressed: {button_id}")
        logger.info(f"Button pressed: {button_id}")
        
        if button_id == "back-to-list-btn":
            from .server_screen import ServerScreen
            content = self.app.query_one("#main-content")
            # Clear and go back
            for child in content.children:
                child.remove()
            content.mount(ServerScreen(self.tui_app))
            
        elif button_id == "detail-refresh-btn":
            self.refresh_stats(manual=True)
            
        elif button_id == "detail-connect-btn":
            self.toggle_connection()
            
        elif button_id == "restart-haas-btn":
            self.app.notify("Restarting Haas Service...", severity="warning")
            self.run_worker(self._restart_service(), exclusive=True, group="server_actions")

    async def _restart_service(self) -> None:
        """Execute restart and handle UI feedback"""
        try:
            success, msg = await self.server_manager.restart_service(self.server_name)
            if success:
                 self.app.notify(f"Restart Initiated: {msg}", severity="information")
                 # Optional: Trigger a reconnect loop or delay
            else:
                 self.app.notify(f"Restart Failed: {msg}", severity="error")
        except Exception as e:
            self.app.notify(f"Error during restart: {str(e)}", severity="error")

    @work(exclusive=True, name="connection_task")
    async def toggle_connection(self) -> None:
        srv = self.server_manager.servers.get(self.server_name)
        if not srv: 
            self.app.notify(f"Server {self.server_name} not found in manager", severity="error")
            return
        
        btn = self.query_one("#detail-connect-btn", Button)
        msg = self.query_one("#detail-status-msg", Label)
        
        btn.disabled = True
        try:
            if srv.status == ServerStatus.CONNECTED:
                msg.update("Disconnecting...")
                self.app.notify(f"Disconnecting tunnel for {self.server_name}...")
                await self.server_manager.disconnect_server(self.server_name)
                msg.update("[green]Disconnected.[/]")
            else:
                msg.update("Connecting (Switching)...")
                self.app.notify(f"Initiating tunnel switch to {self.server_name}...")
                
                # Using switch_server instead of connect_server to handle the single-tunnel policy safely
                # switch_server will disconnect the active server if it's different.
                success = await self.server_manager.switch_server(self.server_name)
                
                if success:
                    msg.update("[green]Tunnel Established.[/]")
                    self.app.notify(f"Connected to {self.server_name} successfully.", severity="information")
                else:
                    err = srv.last_error or "Unknown Error - check SSH keys/ports"
                    msg.update(f"[red]Failed: {err[:20]}[/]")
                    self.app.notify(f"Connection failed: {err}", severity="error")
        except Exception as e:
            err_msg = str(e)
            self.app.notify(f"Connection Error: {err_msg}", severity="error")
            msg.update(f"[red]Error: {err_msg[:30]}[/]")
        finally:
            btn.disabled = False
        
        self.refresh_stats(manual=True)

    def _get_bot_row_data(self, b) -> list:
        """Generate row data list for a bot"""
        status = "[green]ACTIVE[/]" if b.is_active else f"[yellow]{b.status}[/]"
        roi_style = "green" if b.roi > 0 else ("red" if b.roi < 0 else "white")
        roi_display = f"[{roi_style}]{b.roi:.2f}%[/]" if b.roi != 0 else "[dim]0.00%[/]"
        return [
            b.bot_name[:15] or "Unnamed", 
            status, 
            b.market_tag[:10] or "N/A",
            roi_display,
            str(b.total_trades)
        ]

    @work(exclusive=True)
    async def refresh_stats(self, manual: bool = False) -> None:
        if manual:
            self.app.notify(f"Refreshing {self.server_name} dashboard...")
        
        # 1. Fetch Resources
        resources = await self.server_manager.get_server_resources(self.server_name)
        
        cpu_val = resources.get("cpu_load", "N/A")
        ram_val = resources.get("ram_usage", "N/A").replace("%", "")
        disk_val = resources.get("disk_usage", "N/A").replace("%", "")
        
        self.cpu_widget.update_value(cpu_val)
        self.ram_widget.update_value(ram_val)
        self.disk_widget.update_value(disk_val)
        
        # Update Sparklines with actual history
        try:
            val_cpu = float(cpu_val) if isinstance(cpu_val, (int, float)) else float(cpu_val.replace("%",""))
            val_ram = float(ram_val) if isinstance(ram_val, (int, float)) else float(ram_val.replace("%",""))
            
            self.cpu_history.append(val_cpu)
            self.ram_history.append(val_ram)
            self.cpu_history = self.cpu_history[-50:]
            self.ram_history = self.ram_history[-50:]
            
            self.query_one("#cpu-sparkline", Sparkline).data = self.cpu_history
            self.query_one("#ram-sparkline", Sparkline).data = self.ram_history
        except: pass

        h_status = resources.get("haas_status", "Unknown")
        hs_label = self.query_one("#detail-haas-status", Label)
        if h_status == "Running":
            hs_label.update("Haas Status: [green]Running[/]")
        else:
            hs_label.update(f"Haas Status: [red]{h_status}[/]")

        srv = self.server_manager.servers.get(self.server_name)
        active = self.server_manager.active_server
        
        diag_text = f"SSH Status: [{'green' if resources.get('success') else 'red'}]"
        diag_text += f"{'OK' if resources.get('success') else 'FAILED'}[/]\n"
        diag_text += f"Active Tunnel: [{'green' if active == self.server_name else 'yellow'}]"
        diag_text += f"{'YES' if active == self.server_name else 'NO'}[/]\n"
        diag_text += f"Manager State: [bold cyan]{srv.status.value.upper() if srv else 'N/A'}[/]\n"
        
        # Show which credentials are being used
        from pyHaasAPI.config.api_config import APIConfig
        cfg = APIConfig()
        if srv and srv.config.api_email:
            email = srv.config.api_email
        else:
            email = cfg.email
        diag_text += f"Auth: [dim]{email}[/]\n"

        if srv and srv.last_error:
            diag_text += f"Last Err: [red]{str(srv.last_error)[:40]}[/]\n"
        diag_text += f"Local Port: {srv.config.local_ports[0] if srv else 'N/A'}\n"
        diag_text += f"Last Sync: {asyncio.get_event_loop().time():.1f}"
        
        self.diag_info.update(diag_text)

        # Update Connect button state
        btn = self.query_one("#detail-connect-btn", Button)
        if srv and srv.status == ServerStatus.CONNECTED:
            btn.label = "Disconnect"
            btn.variant = "error"
        else:
            btn.label = "Connect"
            btn.variant = "success"

        # 2. Fetch Bots & Labs if connected
        await self.fetch_api_details(srv)

    async def on_unmount(self) -> None:
        """Clean up resources on unmount"""
        if hasattr(self, "_active_client") and self._active_client:
            await self._active_client.close()
            self._active_client = None

    async def _get_or_create_client(self, srv_status) -> Optional[AsyncHaasClient]:
        """Get or create a persistent client for the active server"""
        # If we have a client but the tunnel is down/changed, we might want to refresh?
        # For now, a simple check: if we have one, return it. logic elsewhere handles errors.
        if hasattr(self, "_active_client") and self._active_client:
            return self._active_client
            
        try:
            from pyHaasAPI.config.api_config import APIConfig
            
            # Use a fresh config for this specific tunnel
            config = APIConfig()
            config.port = srv_status.config.local_ports[0]
            config.server_name = self.server_name
            
            if srv_status.config.api_email:
                config.email = srv_status.config.api_email
            if srv_status.config.api_password:
                config.password = srv_status.config.api_password
            
            # Create and connect persistent client
            client = AsyncHaasClient(config)
            await client.connect()
            self._active_client = client
            return client
        except Exception as e:
            logger.error(f"Failed to create client for {self.server_name}: {e}")
            return None

    async def fetch_api_details(self, srv_status) -> None:
        bot_table = self.query_one("#detail-bot-table", DataTable)
        lab_table = self.query_one("#detail-lab-table", DataTable)
        
        if not srv_status or srv_status.status != ServerStatus.CONNECTED:
            # Clear client if we are disconnected
            if hasattr(self, "_active_client") and self._active_client:
                await self._active_client.close()
                self._active_client = None
                
            # Only clear and add if not already in "Disconnected" view
            if bot_table.row_count != 1 or "Connect to view" not in str(bot_table.get_cell_at((0, 0))):
                bot_table.clear()
                lab_table.clear()
                bot_table.add_row("[dim]Connect to view bots[/]", "", "", "", "")
                lab_table.add_row("[dim]Connect to view labs[/]", "", "", "")
            return

        try:
            client = await self._get_or_create_client(srv_status)
            if not client:
                return

            # Get auth manager reusing this persistent client
            auth = self.tui_app.get_auth_manager(self.server_name, client)
            
            # We do NOT use 'async with client:' here as we want to keep it open
            await auth.ensure_authenticated()
            
            # Update Bots
            bot_api = BotAPI(client, auth)
            bots = await bot_api.get_all_bots()
            
            col_keys = list(bot_table.columns.keys())
            for i, b in enumerate(bots[:20]): # Up to 20 bots
                row_key = f"bot_{i}"
                row_data = self._get_bot_row_data(b)
                
                if row_key in bot_table.rows:
                    # Update existing row
                    for col_idx, value in enumerate(row_data):
                        if col_idx < len(col_keys):
                            bot_table.update_cell(row_key, col_keys[col_idx], value)
                else:
                    # Add new row
                    bot_table.add_row(*row_data, key=row_key)
            
            # Update Labs
            lab_api = LabAPI(client, auth)
            labs = await lab_api.get_labs()
            lab_col_keys = list(lab_table.columns.keys())
            for i, l in enumerate(labs[:20]): # Up to 20 labs
                row_key = f"lab_{i}"
                
                # Status mapping with colors
                status_map = {
                    0: "[dim]IDLE[/]",
                    1: "[cyan]ACTIVE[/]",
                    2: "[bold green]RUNNING[/]",
                    3: "[green]COMPLETED[/]",
                    4: "[green]COMPLETED[/]",
                    5: "[bold red]FAILED[/]",
                    6: "[yellow]CANCELLED[/]"
                }
                status_display = status_map.get(l.status, f"[dim]{l.status}[/]")
                
                # If not running, typically zero active planned tests
                scheduled = str(l.scheduled_backtests) if l.status == 2 else "[dim]0[/]"
                
                row_data = [
                    l.name[:25] or "Unnamed Lab", 
                    status_display, 
                    str(l.completed_backtests), 
                    scheduled
                ]
                
                if row_key in lab_table.rows:
                    for col_idx, value in enumerate(row_data):
                        if col_idx < len(lab_col_keys):
                            lab_table.update_cell(row_key, lab_col_keys[col_idx], value)
                else:
                    lab_table.add_row(*row_data, key=row_key)

        except Exception as e:
            err_msg = str(e)
            from pyHaasAPI.config.api_config import APIConfig
            cfg = APIConfig()
            used_email = srv_status.config.api_email or cfg.email
            
            if "credentials" in err_msg.lower() or "auth" in err_msg.lower():
                # Avoid flooding table with errors, perhaps clear first if lots of rows
                if bot_table.row_count > 1:
                     bot_table.clear()
                
                # Only add if empty (to avoid flicker/duplication)
                if bot_table.row_count == 0:
                    bot_table.add_row("[bold red]Auth Failed[/]", f"[red]Email: {used_email}[/]", "")
                
                self.app.notify(f"Auth failed for {used_email} on {self.server_name}", severity="error")
                
                # Invalidating client might be good idea if auth fails hard
                if hasattr(self, "_active_client") and self._active_client:
                    await self._active_client.close()
                    self._active_client = None
            else:
                # Show more of the error message to help diagnostics
                if bot_table.row_count > 1:
                     bot_table.clear()
                if bot_table.row_count == 0:
                    bot_table.add_row(f"[red]Error: {err_msg[:60]}[/]", "", "")
                    if len(err_msg) > 60:
                         bot_table.add_row(f"[red]{err_msg[60:120]}[/]", "", "")
