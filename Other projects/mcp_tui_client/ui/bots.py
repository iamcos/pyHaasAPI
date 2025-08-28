"""
Bot Management View

Comprehensive bot management interface with list and detail views.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widget import Widget
from textual.widgets import Static, DataTable, Button, Input, Label, Select
from textual.reactive import reactive
from textual.message import Message

from .components.tables import FilterableTable, PaginatedTable
from .components.panels import BasePanel, StatusPanel, ActionPanel
from .components.indicators import StatusIndicator, IndicatorStatus, PerformanceIndicator
from ..services.mcp_client import MCPClientService
from ..utils.logging import get_logger


class BotStatusFilter(Container):
    """Filter controls for bot status and search"""
    
    DEFAULT_CSS = """
    BotStatusFilter {
        height: 4;
        dock: top;
        background: $surface;
        padding: 1;
    }
    
    BotStatusFilter .filter-row {
        height: 1;
        layout: horizontal;
        align: center middle;
    }
    
    BotStatusFilter .filter-item {
        margin: 0 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.status_filter = "all"
        self.search_text = ""
        self.sort_column = "name"
        self.sort_reverse = False
    
    def compose(self) -> ComposeResult:
        """Compose filter controls"""
        # First row: Search and status filter
        filter_row1 = Horizontal(classes="filter-row")
        filter_row1.mount(Label("Search:", classes="filter-item"))
        filter_row1.mount(Input(
            placeholder="Search bots...",
            id="bot-search",
            classes="filter-item"
        ))
        filter_row1.mount(Label("Status:", classes="filter-item"))
        filter_row1.mount(Select(
            [
                ("All", "all"),
                ("Active", "active"),
                ("Paused", "paused"),
                ("Stopped", "stopped"),
                ("Error", "error")
            ],
            value="all",
            id="status-filter",
            classes="filter-item"
        ))
        yield filter_row1
        
        # Second row: Sort controls and actions
        filter_row2 = Horizontal(classes="filter-row")
        filter_row2.mount(Label("Sort by:", classes="filter-item"))
        filter_row2.mount(Select(
            [
                ("Name", "name"),
                ("Status", "status"),
                ("P&L", "pnl"),
                ("Trades", "trades"),
                ("Created", "created")
            ],
            value="name",
            id="sort-select",
            classes="filter-item"
        ))
        filter_row2.mount(Button("↑↓", id="sort-direction", classes="filter-item"))
        filter_row2.mount(Button("Refresh", id="refresh-bots", classes="filter-item"))
        filter_row2.mount(Button("New Bot", id="create-bot", classes="filter-item"))
        yield filter_row2
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        if event.input.id == "bot-search":
            self.search_text = event.value
            self.post_message(self.FilterChanged())
    
    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter selection changes"""
        if event.select.id == "status-filter":
            self.status_filter = event.value
            self.post_message(self.FilterChanged())
        elif event.select.id == "sort-select":
            self.sort_column = event.value
            self.post_message(self.SortChanged())
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "sort-direction":
            self.sort_reverse = not self.sort_reverse
            event.button.label = "↓" if self.sort_reverse else "↑"
            self.post_message(self.SortChanged())
        elif event.button.id == "refresh-bots":
            self.post_message(self.RefreshRequested())
        elif event.button.id == "create-bot":
            self.post_message(self.CreateBotRequested())
    
    class FilterChanged(Message):
        """Message sent when filter criteria change"""
        pass
    
    class SortChanged(Message):
        """Message sent when sort criteria change"""
        pass
    
    class RefreshRequested(Message):
        """Message sent when refresh is requested"""
        pass
    
    class CreateBotRequested(Message):
        """Message sent when create bot is requested"""
        pass


class BotListPanel(BasePanel):
    """Enhanced panel with bot list and overview"""
    
    DEFAULT_CSS = """
    BotListPanel {
        height: 1fr;
        min-height: 20;
    }
    
    BotListPanel .bot-table {
        height: 1fr;
    }
    
    BotListPanel .bot-summary {
        dock: bottom;
        height: 3;
        background: $surface;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(title="Trading Bots", show_header=True, show_footer=True, **kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.bots_data: List[Dict[str, Any]] = []
        self.filtered_bots: List[Dict[str, Any]] = []
        self.selected_bot: Optional[Dict[str, Any]] = None
        self.logger = get_logger(__name__)
    
    def compose(self) -> ComposeResult:
        """Compose bot list panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize panel on mount"""
        await self._setup_components()
        if self.mcp_client:
            await self.refresh_bots()
    
    async def _setup_components(self) -> None:
        """Set up panel components"""
        content_container = self.query_one("#panel-content")
        
        # Add filter controls
        self.filter_controls = BotStatusFilter()
        content_container.mount(self.filter_controls)
        
        # Add bot table
        self.bot_table = PaginatedTable(
            columns=["Name", "Status", "P&L (24h)", "Trades", "Account", "Market", "Created"],
            page_size=20,
            show_header=True,
            show_footer=True,
            classes="bot-table"
        )
        content_container.mount(self.bot_table)
        
        # Add summary panel
        self.summary_panel = Container(classes="bot-summary")
        self.summary_label = Label("No bots loaded")
        self.summary_panel.mount(self.summary_label)
        content_container.mount(self.summary_panel)
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for data operations"""
        self.mcp_client = mcp_client
    
    async def refresh_bots(self) -> None:
        """Refresh bot data from MCP server"""
        if not self.mcp_client:
            self.set_status("error", "MCP client not available")
            return
        
        try:
            self.set_status("normal", "Loading bots...")
            
            # Get all bots
            bots_response = await self.mcp_client.get_all_bots()
            
            if isinstance(bots_response, dict) and "bots" in bots_response:
                self.bots_data = bots_response["bots"]
            elif isinstance(bots_response, list):
                self.bots_data = bots_response
            else:
                self.bots_data = []
            
            # Process and format bot data
            formatted_bots = []
            for bot in self.bots_data:
                formatted_bot = await self._format_bot_data(bot)
                formatted_bots.append(formatted_bot)
            
            self.bots_data = formatted_bots
            await self._apply_filters()
            self._update_summary()
            
            self.set_status("success", f"Loaded {len(self.bots_data)} bots")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh bots: {e}")
            self.set_status("error", f"Failed to load bots: {str(e)}")
    
    async def _format_bot_data(self, bot: Dict[str, Any]) -> Dict[str, Any]:
        """Format bot data for display"""
        # Get bot status with icon
        status = bot.get("status", "unknown").lower()
        status_icons = {
            "active": "🟢 Active",
            "paused": "🟡 Paused", 
            "stopped": "🔴 Stopped",
            "error": "❌ Error",
            "unknown": "⚪ Unknown"
        }
        
        # Format P&L
        pnl = bot.get("pnl_24h", 0)
        pnl_str = f"${pnl:+.2f}" if isinstance(pnl, (int, float)) else str(pnl)
        
        # Format trade count
        trades = bot.get("trade_count", 0)
        trades_str = str(trades) if isinstance(trades, int) else "0"
        
        # Format creation date
        created = bot.get("created_at", "")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                created_str = created_dt.strftime("%Y-%m-%d")
            except:
                created_str = str(created)[:10]
        else:
            created_str = "Unknown"
        
        return {
            "Name": bot.get("name", "Unknown"),
            "Status": status_icons.get(status, f"⚪ {status.title()}"),
            "P&L (24h)": pnl_str,
            "Trades": trades_str,
            "Account": bot.get("account_name", "Unknown"),
            "Market": bot.get("market", "Unknown"),
            "Created": created_str,
            "_raw_data": bot,  # Store original data
            "_status": status,
            "_pnl": pnl,
            "_trades": trades
        }
    
    async def _apply_filters(self) -> None:
        """Apply current filters to bot data"""
        filtered = self.bots_data.copy()
        
        # Apply status filter
        if self.filter_controls.status_filter != "all":
            filtered = [
                bot for bot in filtered 
                if bot.get("_status") == self.filter_controls.status_filter
            ]
        
        # Apply search filter
        if self.filter_controls.search_text:
            search_lower = self.filter_controls.search_text.lower()
            filtered = [
                bot for bot in filtered
                if any(
                    search_lower in str(value).lower()
                    for key, value in bot.items()
                    if not key.startswith("_")
                )
            ]
        
        # Apply sorting
        sort_key = self.filter_controls.sort_column
        if sort_key == "name":
            filtered.sort(key=lambda x: x.get("Name", ""), reverse=self.filter_controls.sort_reverse)
        elif sort_key == "status":
            filtered.sort(key=lambda x: x.get("_status", ""), reverse=self.filter_controls.sort_reverse)
        elif sort_key == "pnl":
            filtered.sort(key=lambda x: x.get("_pnl", 0), reverse=self.filter_controls.sort_reverse)
        elif sort_key == "trades":
            filtered.sort(key=lambda x: x.get("_trades", 0), reverse=self.filter_controls.sort_reverse)
        elif sort_key == "created":
            filtered.sort(key=lambda x: x.get("Created", ""), reverse=self.filter_controls.sort_reverse)
        
        self.filtered_bots = filtered
        
        # Update table
        self.bot_table.set_data(filtered)
    
    def _update_summary(self) -> None:
        """Update bot summary information"""
        total_bots = len(self.bots_data)
        filtered_count = len(self.filtered_bots)
        
        if total_bots == 0:
            summary_text = "No bots available"
        else:
            # Count by status
            status_counts = {}
            total_pnl = 0
            total_trades = 0
            
            for bot in self.bots_data:
                status = bot.get("_status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
                
                pnl = bot.get("_pnl", 0)
                if isinstance(pnl, (int, float)):
                    total_pnl += pnl
                
                trades = bot.get("_trades", 0)
                if isinstance(trades, int):
                    total_trades += trades
            
            status_parts = []
            for status, count in status_counts.items():
                status_parts.append(f"{status}: {count}")
            
            summary_text = (
                f"Total: {total_bots} bots ({filtered_count} shown) | "
                f"{' | '.join(status_parts)} | "
                f"Total P&L: ${total_pnl:+.2f} | "
                f"Total Trades: {total_trades}"
            )
        
        self.summary_label.update(summary_text)
    
    async def on_bot_status_filter_filter_changed(self, message: BotStatusFilter.FilterChanged) -> None:
        """Handle filter changes"""
        await self._apply_filters()
        self._update_summary()
    
    async def on_bot_status_filter_sort_changed(self, message: BotStatusFilter.SortChanged) -> None:
        """Handle sort changes"""
        await self._apply_filters()
    
    async def on_bot_status_filter_refresh_requested(self, message: BotStatusFilter.RefreshRequested) -> None:
        """Handle refresh requests"""
        await self.refresh_bots()
    
    async def on_bot_status_filter_create_bot_requested(self, message: BotStatusFilter.CreateBotRequested) -> None:
        """Handle create bot requests"""
        self.post_message(self.CreateBotRequested())
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle bot selection"""
        if 0 <= event.row_index < len(self.filtered_bots):
            self.selected_bot = self.filtered_bots[event.row_index]
            self.post_message(self.BotSelected(self.selected_bot))
    
    def get_selected_bot(self) -> Optional[Dict[str, Any]]:
        """Get currently selected bot"""
        return self.selected_bot
    
    class BotSelected(Message):
        """Message sent when a bot is selected"""
        def __init__(self, bot_data: Dict[str, Any]):
            super().__init__()
            self.bot_data = bot_data
    
    class CreateBotRequested(Message):
        """Message sent when create bot is requested"""
        pass


class BotDetailsPanel(BasePanel):
    """Enhanced panel with detailed bot information and real-time updates"""
    
    DEFAULT_CSS = """
    BotDetailsPanel {
        height: 1fr;
        min-height: 30;
    }
    
    BotDetailsPanel .bot-info {
        height: auto;
        padding: 1;
    }
    
    BotDetailsPanel .info-section {
        margin: 1 0;
        border: solid $accent;
        padding: 1;
    }
    
    BotDetailsPanel .info-title {
        text-style: bold;
        color: $primary;
        margin: 0 0 1 0;
    }
    
    BotDetailsPanel .info-item {
        height: 1;
        layout: horizontal;
        margin: 0 0 0 1;
    }
    
    BotDetailsPanel .info-label {
        width: 15;
        color: $text-muted;
    }
    
    BotDetailsPanel .info-value {
        width: 1fr;
        text-style: bold;
    }
    
    BotDetailsPanel .performance-grid {
        layout: grid;
        grid-size: 3 3;
        grid-gutter: 1;
        height: 12;
    }
    
    BotDetailsPanel .metric-card {
        border: solid $surface;
        padding: 1;
        text-align: center;
    }
    
    BotDetailsPanel .metric-value {
        text-style: bold;
        color: $success;
    }
    
    BotDetailsPanel .metric-value.negative {
        color: $error;
    }
    
    BotDetailsPanel .metric-label {
        color: $text-muted;
    }
    
    BotDetailsPanel .chart-container {
        height: 15;
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }
    
    BotDetailsPanel .trade-history {
        height: 12;
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }
    
    BotDetailsPanel .config-editor {
        height: 15;
        border: solid $accent;
        padding: 1;
        margin: 1 0;
    }
    
    BotDetailsPanel .tab-buttons {
        dock: top;
        height: 3;
        layout: horizontal;
        background: $surface;
        padding: 1;
    }
    
    BotDetailsPanel .tab-button {
        margin: 0 1;
    }
    
    BotDetailsPanel .tab-button.active {
        background: $primary;
        color: $text;
    }
    
    BotDetailsPanel .trade-table {
        height: 1fr;
    }
    
    BotDetailsPanel .position-info {
        height: 4;
        background: $surface;
        padding: 1;
        margin: 1 0;
    }
    
    BotDetailsPanel .position-grid {
        layout: grid;
        grid-size: 4 1;
        grid-gutter: 1;
        height: 2;
    }
    
    BotDetailsPanel .position-item {
        text-align: center;
        border: solid $surface;
        padding: 0 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(title="Bot Details", show_header=True, show_footer=True, **kwargs)
        self.current_bot: Optional[Dict[str, Any]] = None
        self.mcp_client: Optional[MCPClientService] = None
        self.auto_refresh_enabled = True
        self.refresh_interval = 30  # seconds
        self.refresh_task: Optional[asyncio.Task] = None
        self.logger = get_logger(__name__)
        
        # Tab management
        self.current_tab = "overview"
        self.tabs = ["overview", "performance", "trades", "positions", "config"]
        
        # Data storage
        self.trade_history: List[Dict[str, Any]] = []
        self.position_data: Dict[str, Any] = {}
        self.performance_data: List[Dict[str, Any]] = []
    
    def compose(self) -> ComposeResult:
        """Compose bot details panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize panel on mount"""
        await self._setup_components()
        if self.auto_refresh_enabled:
            await self._start_auto_refresh()
    
    async def _setup_components(self) -> None:
        """Set up panel components"""
        content_container = self.query_one("#panel-content")
        
        # Create tab buttons
        tab_buttons = []
        for tab in self.tabs:
            tab_name = tab.replace("_", " ").title()
            button = Button(
                tab_name,
                id=f"tab-{tab}",
                classes="tab-button" + (" active" if tab == self.current_tab else "")
            )
            tab_buttons.append(button)
        
        # Mount tab container with buttons
        self.tab_container = Horizontal(*tab_buttons, classes="tab-buttons")
        self.content_area = Container(id="tab-content")
        
        await content_container.mount(self.tab_container, self.content_area)
        
        # Show empty state initially
        await self._show_empty_state()
    
    async def _show_empty_state(self) -> None:
        """Show empty state when no bot is selected"""
        self.content_area.remove_children()
        await self.content_area.mount(Label(
            "Select a bot from the list to view details",
            classes="info-title"
        ))
        self.title = "Bot Details"
        self.set_status("neutral", "No bot selected")
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for data operations"""
        self.mcp_client = mcp_client
    
    async def show_bot_details(self, bot_data: Dict[str, Any]) -> None:
        """Show details for selected bot"""
        self.current_bot = bot_data
        raw_data = bot_data.get("_raw_data", {})
        
        # Update title
        bot_name = bot_data.get("Name", "Unknown Bot")
        self.title = f"Bot Details: {bot_name}"
        
        print(f"🤖 BotDetailsPanel: Showing details for {bot_name}")
        print(f"📋 Raw data: {raw_data}")
        
        try:
            # Get detailed bot information from MCP server
            if self.mcp_client and raw_data.get("bot_id"):
                print(f"🔗 Loading detailed data for bot_id: {raw_data['bot_id']}")
                detailed_data = await self.mcp_client.get_bot_details(raw_data["bot_id"])
                if detailed_data:
                    raw_data.update(detailed_data)
                    print(f"✅ Updated raw data with detailed info")
                
                # Load additional data
                await self._load_trade_history(raw_data["bot_id"])
                await self._load_position_data(raw_data["bot_id"])
                await self._load_performance_data(raw_data["bot_id"])
            else:
                print(f"⚠️ No MCP client or bot_id available")
            
            print(f"🎨 Rendering current tab: {self.current_tab}")
            await self._render_current_tab()
            self.set_status("success", f"Showing details for {bot_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to load bot details: {e}")
            print(f"❌ Error loading bot details: {e}")
            import traceback
            traceback.print_exc()
            self.set_status("error", f"Failed to load details: {str(e)}")
            await self._render_current_tab()  # Show with available data
    
    async def _load_trade_history(self, bot_id: str) -> None:
        """Load trade history for the bot"""
        try:
            if self.mcp_client:
                trades_response = await self.mcp_client.get_bot_trades(bot_id)
                self.trade_history = trades_response.get("trades", []) if isinstance(trades_response, dict) else []
        except Exception as e:
            self.logger.error(f"Failed to load trade history: {e}")
            self.trade_history = []
    
    async def _load_position_data(self, bot_id: str) -> None:
        """Load current position data for the bot"""
        try:
            if self.mcp_client:
                position_response = await self.mcp_client.get_bot_positions(bot_id)
                self.position_data = position_response if isinstance(position_response, dict) else {}
        except Exception as e:
            self.logger.error(f"Failed to load position data: {e}")
            self.position_data = {}
    
    async def _load_performance_data(self, bot_id: str) -> None:
        """Load performance history for the bot"""
        try:
            if self.mcp_client:
                perf_response = await self.mcp_client.get_bot_performance_history(bot_id)
                self.performance_data = perf_response.get("history", []) if isinstance(perf_response, dict) else []
        except Exception as e:
            self.logger.error(f"Failed to load performance data: {e}")
            self.performance_data = []
    
    async def _render_current_tab(self) -> None:
        """Render the currently selected tab"""
        if self.current_tab == "overview":
            await self._render_overview_tab()
        elif self.current_tab == "performance":
            await self._render_performance_tab()
        elif self.current_tab == "trades":
            await self._render_trades_tab()
        elif self.current_tab == "positions":
            await self._render_positions_tab()
        elif self.current_tab == "config":
            await self._render_config_tab()
    
    async def _render_overview_tab(self) -> None:
        """Render the overview tab with basic bot information"""
        print(f"🎨 Rendering overview tab")
        if not self.current_bot:
            print("⚠️ No current bot to render")
            return
        
        bot_data = self.current_bot
        raw_data = bot_data.get("_raw_data", {})
        
        print(f"📊 Bot data: {bot_data.get('Name', 'Unknown')}")
        print(f"🔧 Raw data keys: {list(raw_data.keys())}")
        
        self.content_area.remove_children()
        
        # Create content as a single text display for simplicity
        content_lines = []
        content_lines.append("=== BASIC INFORMATION ===")
        content_lines.append(f"Name: {bot_data.get('Name', 'Unknown')}")
        content_lines.append(f"Status: {bot_data.get('Status', 'Unknown')}")
        content_lines.append(f"Account: {bot_data.get('Account', 'Unknown')}")
        content_lines.append(f"Market: {bot_data.get('Market', 'Unknown')}")
        content_lines.append(f"Strategy: {raw_data.get('strategy_name', 'Unknown')}")
        content_lines.append(f"Created: {bot_data.get('Created', 'Unknown')}")
        content_lines.append(f"Last Updated: {raw_data.get('last_updated', 'Unknown')}")
        content_lines.append(f"Bot ID: {raw_data.get('bot_id', 'Unknown')}")
        content_lines.append("")
        
        content_lines.append("=== PERFORMANCE METRICS ===")
        metrics = [
            ("Total P&L", raw_data.get("total_pnl", 0), "$"),
            ("24h P&L", bot_data.get("_pnl", 0), "$"),
            ("Total Trades", bot_data.get("_trades", 0), ""),
            ("Win Rate", raw_data.get("win_rate", 0), "%"),
            ("Profit Factor", raw_data.get("profit_factor", 0), ""),
            ("Sharpe Ratio", raw_data.get("sharpe_ratio", 0), ""),
            ("Max Drawdown", raw_data.get("max_drawdown", 0), "%"),
            ("Avg Trade", raw_data.get("avg_trade_pnl", 0), "$"),
            ("Best Trade", raw_data.get("best_trade", 0), "$")
        ]
        
        for label, value, suffix in metrics:
            if isinstance(value, (int, float)):
                if suffix == "$":
                    formatted_value = f"${value:+.2f}"
                elif suffix == "%":
                    formatted_value = f"{value:.1f}%"
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
            
            content_lines.append(f"{label}: {formatted_value}")
        
        content_text = "\n".join(content_lines)
        await self.content_area.mount(Static(content_text, classes="bot-info"))
    
    async def _render_performance_tab(self) -> None:
        """Render the performance tab with charts and detailed metrics"""
        self.content_area.remove_children()
        
        content_lines = []
        content_lines.append("=== PERFORMANCE CHART ===")
        
        # Create performance chart
        chart_content = self._create_performance_chart()
        content_lines.append(chart_content)
        content_lines.append("")
        
        content_lines.append("=== DETAILED PERFORMANCE METRICS ===")
        
        if self.current_bot:
            raw_data = self.current_bot.get("_raw_data", {})
            
            detailed_metrics = [
                ("Total Return", raw_data.get("total_return", 0), "%"),
                ("Annualized Return", raw_data.get("annualized_return", 0), "%"),
                ("Volatility", raw_data.get("volatility", 0), "%"),
                ("Sharpe Ratio", raw_data.get("sharpe_ratio", 0), ""),
                ("Sortino Ratio", raw_data.get("sortino_ratio", 0), ""),
                ("Calmar Ratio", raw_data.get("calmar_ratio", 0), ""),
                ("Max Drawdown", raw_data.get("max_drawdown", 0), "%"),
                ("Recovery Factor", raw_data.get("recovery_factor", 0), ""),
                ("Profit Factor", raw_data.get("profit_factor", 0), ""),
                ("Payoff Ratio", raw_data.get("payoff_ratio", 0), ""),
                ("Win Rate", raw_data.get("win_rate", 0), "%"),
                ("Average Win", raw_data.get("avg_win", 0), "$"),
                ("Average Loss", raw_data.get("avg_loss", 0), "$"),
                ("Largest Win", raw_data.get("largest_win", 0), "$"),
                ("Largest Loss", raw_data.get("largest_loss", 0), "$")
            ]
            
            for label, value, suffix in detailed_metrics:
                if isinstance(value, (int, float)):
                    if suffix == "$":
                        formatted_value = f"${value:+.2f}"
                    elif suffix == "%":
                        formatted_value = f"{value:.2f}%"
                    else:
                        formatted_value = f"{value:.3f}"
                else:
                    formatted_value = str(value)
                
                content_lines.append(f"{label}: {formatted_value}")
        
        content_text = "\n".join(content_lines)
        await self.content_area.mount(Static(content_text, classes="bot-info"))
    
    async def _render_trades_tab(self) -> None:
        """Render the trades tab with trade history"""
        self.content_area.remove_children()
        
        content_lines = []
        content_lines.append("=== TRADE HISTORY ===")
        
        if self.trade_history:
            # Show recent trades
            content_lines.append("Recent Trades (Last 10):")
            content_lines.append("Time       | Side | Symbol   | Quantity | Price    | P&L      | Fee")
            content_lines.append("-" * 70)
            
            for trade in self.trade_history[:10]:  # Show last 10 trades
                time_str = self._format_timestamp(trade.get("timestamp", ""))
                side = trade.get("side", "").upper()
                symbol = trade.get("symbol", "")
                quantity = f"{trade.get('quantity', 0):.4f}"
                price = f"${trade.get('price', 0):.2f}"
                pnl = f"${trade.get('pnl', 0):+.2f}"
                fee = f"${trade.get('fee', 0):.2f}"
                
                content_lines.append(f"{time_str:10} | {side:4} | {symbol:8} | {quantity:8} | {price:8} | {pnl:8} | {fee}")
            
            content_lines.append("")
            content_lines.append("=== TRADE SUMMARY ===")
            
            total_trades = len(self.trade_history)
            winning_trades = sum(1 for trade in self.trade_history if trade.get("pnl", 0) > 0)
            losing_trades = sum(1 for trade in self.trade_history if trade.get("pnl", 0) < 0)
            total_pnl = sum(trade.get("pnl", 0) for trade in self.trade_history)
            total_fees = sum(trade.get("fee", 0) for trade in self.trade_history)
            
            content_lines.append(f"Total Trades: {total_trades}")
            content_lines.append(f"Winning Trades: {winning_trades}")
            content_lines.append(f"Losing Trades: {losing_trades}")
            content_lines.append(f"Win Rate: {(winning_trades / total_trades * 100) if total_trades > 0 else 0:.1f}%")
            content_lines.append(f"Total P&L: ${total_pnl:+.2f}")
            content_lines.append(f"Total Fees: ${total_fees:.2f}")
            content_lines.append(f"Net P&L: ${total_pnl - total_fees:+.2f}")
        else:
            content_lines.append("No trade history available")
        
        content_text = "\n".join(content_lines)
        await self.content_area.mount(Static(content_text, classes="bot-info"))
    
    async def _render_positions_tab(self) -> None:
        """Render the positions tab with current positions"""
        self.content_area.remove_children()
        
        content_lines = []
        content_lines.append("=== CURRENT POSITIONS ===")
        
        if self.position_data:
            # Position summary
            content_lines.append("Position Summary:")
            content_lines.append(f"Total Value: ${self.position_data.get('total_value', 0):,.2f}")
            content_lines.append(f"Unrealized P&L: ${self.position_data.get('unrealized_pnl', 0):+.2f}")
            content_lines.append(f"Margin Used: ${self.position_data.get('margin_used', 0):,.2f}")
            content_lines.append(f"Free Margin: ${self.position_data.get('free_margin', 0):,.2f}")
            content_lines.append("")
            
            # Individual positions
            positions = self.position_data.get("positions", [])
            if positions:
                content_lines.append("Individual Positions:")
                for position in positions:
                    symbol = position.get("symbol", "Unknown")
                    side = position.get("side", "Unknown")
                    size = position.get("size", 0)
                    entry_price = position.get("entry_price", 0)
                    current_price = position.get("current_price", 0)
                    unrealized_pnl = position.get("unrealized_pnl", 0)
                    
                    content_lines.append(f"  {symbol} ({side}):")
                    content_lines.append(f"    Size: {size:.4f}")
                    content_lines.append(f"    Entry Price: ${entry_price:.4f}")
                    content_lines.append(f"    Current Price: ${current_price:.4f}")
                    content_lines.append(f"    Unrealized P&L: ${unrealized_pnl:+.2f}")
                    content_lines.append("")
            else:
                content_lines.append("No individual positions")
        else:
            content_lines.append("No position data available")
        
        content_text = "\n".join(content_lines)
        await self.content_area.mount(Static(content_text, classes="bot-info"))
    
    async def _render_config_tab(self) -> None:
        """Render the configuration tab with bot settings editor"""
        self.content_area.remove_children()
        
        if not self.current_bot:
            return
        
        raw_data = self.current_bot.get("_raw_data", {})
        
        content_lines = []
        content_lines.append("=== BOT CONFIGURATION ===")
        content_lines.append("")
        
        # Basic configuration
        content_lines.append("Basic Settings:")
        config_items = [
            ("Script ID", raw_data.get("script_id", "Unknown")),
            ("Account ID", raw_data.get("account_id", "Unknown")),
            ("Market", raw_data.get("market", "Unknown")),
            ("Position Size", raw_data.get("position_size", "Unknown")),
            ("Risk Level", raw_data.get("risk_level", "Unknown"))
        ]
        
        for label, value in config_items:
            content_lines.append(f"  {label}: {value}")
        
        content_lines.append("")
        
        # Risk management settings
        content_lines.append("Risk Management:")
        risk_items = [
            ("Stop Loss", raw_data.get("stop_loss", "Not set")),
            ("Take Profit", raw_data.get("take_profit", "Not set")),
            ("Max Position Size", raw_data.get("max_position_size", "Not set")),
            ("Max Daily Loss", raw_data.get("max_daily_loss", "Not set")),
            ("Max Drawdown", raw_data.get("max_drawdown_limit", "Not set"))
        ]
        
        for label, value in risk_items:
            content_lines.append(f"  {label}: {value}")
        
        content_lines.append("")
        
        # Strategy parameters
        content_lines.append("Strategy Parameters:")
        parameters = raw_data.get("parameters", {})
        if parameters:
            for param_name, param_value in parameters.items():
                content_lines.append(f"  {param_name}: {param_value}")
        else:
            content_lines.append("  No strategy parameters configured")
        
        content_lines.append("")
        content_lines.append("Configuration Actions:")
        content_lines.append("  [Edit Config] [Save Config] [Reset Config] [Export Config]")
        content_lines.append("  (Configuration editing not yet implemented)")
        
        content_text = "\n".join(content_lines)
        await self.content_area.mount(Static(content_text, classes="bot-info"))
    
    def _create_performance_chart(self) -> str:
        """Create ASCII performance chart"""
        if not self.performance_data:
            return "No performance data available for chart"
        
        # Extract P&L values
        pnl_values = [item.get("pnl", 0) for item in self.performance_data]
        
        if not pnl_values or all(v == 0 for v in pnl_values):
            return "No P&L data to display"
        
        # Create simple ASCII chart
        chart_width = 60
        chart_height = 15
        
        min_val = min(pnl_values)
        max_val = max(pnl_values)
        val_range = max_val - min_val if max_val != min_val else 1
        
        chart_lines = []
        chart_lines.append("Performance Chart (P&L over time)")
        chart_lines.append("─" * chart_width)
        
        # Create chart body
        for row in range(chart_height):
            line = ""
            threshold = max_val - (row / (chart_height - 1)) * val_range
            
            # Y-axis label
            line += f"{threshold:8.2f} ┤"
            
            # Chart data
            for i, value in enumerate(pnl_values):
                x_pos = int(i * (chart_width - 12) / len(pnl_values))
                if len(line) <= x_pos + 12:
                    line += " " * (x_pos + 12 - len(line) + 1)
                
                if abs(value - threshold) <= val_range / chart_height:
                    if value >= 0:
                        line = line[:x_pos + 12] + "█" + line[x_pos + 13:]
                    else:
                        line = line[:x_pos + 12] + "▄" + line[x_pos + 13:]
            
            chart_lines.append(line)
        
        # Add time axis
        time_axis = "         └" + "─" * (chart_width - 12)
        chart_lines.append(time_axis)
        
        return "\n".join(chart_lines)
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display"""
        if not timestamp:
            return "Unknown"
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%m/%d %H:%M")
        except:
            return str(timestamp)[:16]
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if not button_id:
            return
        
        # Tab switching
        if button_id.startswith("tab-"):
            tab_name = button_id.replace("tab-", "")
            if tab_name in self.tabs:
                await self._switch_tab(tab_name)
        
        # Configuration actions
        elif button_id == "edit-config":
            await self._edit_config()
        elif button_id == "save-config":
            await self._save_config()
        elif button_id == "reset-config":
            await self._reset_config()
        elif button_id == "export-config":
            await self._export_config()
    
    async def _switch_tab(self, tab_name: str) -> None:
        """Switch to a different tab"""
        if tab_name == self.current_tab:
            return
        
        # Update tab buttons
        for tab in self.tabs:
            try:
                button = self.query_one(f"#tab-{tab}", Button)
                if tab == tab_name:
                    button.add_class("active")
                else:
                    button.remove_class("active")
            except:
                pass
        
        self.current_tab = tab_name
        await self._render_current_tab()
    
    async def _edit_config(self) -> None:
        """Enable configuration editing"""
        # TODO: Implement configuration editing
        self.set_status("info", "Configuration editing not yet implemented")
    
    async def _save_config(self) -> None:
        """Save configuration changes"""
        # TODO: Implement configuration saving
        self.set_status("info", "Configuration saving not yet implemented")
    
    async def _reset_config(self) -> None:
        """Reset configuration to defaults"""
        # TODO: Implement configuration reset
        self.set_status("info", "Configuration reset not yet implemented")
    
    async def _export_config(self) -> None:
        """Export configuration to file"""
        # TODO: Implement configuration export
        self.set_status("info", "Configuration export not yet implemented")


    
    async def _start_auto_refresh(self) -> None:
        """Start auto-refresh task"""
        if self.refresh_task:
            self.refresh_task.cancel()
        
        self.refresh_task = asyncio.create_task(self._auto_refresh_loop())
    
    async def _auto_refresh_loop(self) -> None:
        """Auto-refresh loop"""
        while self.auto_refresh_enabled:
            try:
                await asyncio.sleep(self.refresh_interval)
                if self.current_bot and self.mcp_client:
                    await self.refresh_current_bot()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Auto-refresh error: {e}")
    
    async def refresh_current_bot(self) -> None:
        """Refresh current bot details"""
        if self.current_bot:
            # Reload data for current bot
            raw_data = self.current_bot.get("_raw_data", {})
            if self.mcp_client and raw_data.get("bot_id"):
                try:
                    # Reload all data
                    await self._load_trade_history(raw_data["bot_id"])
                    await self._load_position_data(raw_data["bot_id"])
                    await self._load_performance_data(raw_data["bot_id"])
                    
                    # Re-render current tab
                    await self._render_current_tab()
                except Exception as e:
                    self.logger.error(f"Failed to refresh bot data: {e}")
    
    def on_unmount(self) -> None:
        """Clean up on unmount"""
        if self.refresh_task:
            self.refresh_task.cancel()


class BotActionsPanel(ActionPanel):
    """Enhanced panel with bot action buttons and batch operations"""
    
    DEFAULT_CSS = """
    BotActionsPanel {
        height: auto;
        min-height: 12;
    }
    
    BotActionsPanel .action-section {
        margin: 1 0;
        border: solid $accent;
        padding: 1;
    }
    
    BotActionsPanel .section-title {
        text-style: bold;
        color: $primary;
        margin: 0 0 1 0;
    }
    
    BotActionsPanel .action-grid {
        layout: grid;
        grid-size: 3 3;
        grid-gutter: 1;
        height: auto;
    }
    
    BotActionsPanel .batch-controls {
        layout: horizontal;
        height: 3;
        align: center middle;
    }
    
    BotActionsPanel .emergency-section {
        background: $error 20%;
        border: solid $error;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(title="Bot Actions", **kwargs)
        self.current_bot: Optional[Dict[str, Any]] = None
        self.selected_bots: List[Dict[str, Any]] = []
        self.mcp_client: Optional[MCPClientService] = None
        self.logger = get_logger(__name__)
    
    def compose(self) -> ComposeResult:
        """Compose bot actions panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize panel on mount"""
        await self._setup_actions()
    
    async def _setup_actions(self) -> None:
        """Set up action sections"""
        content_container = self.query_one("#panel-content")
        content_container.remove_children()
        
        # Single Bot Actions Section
        single_section = Container(classes="action-section")
        single_section.mount(Label("Single Bot Actions", classes="section-title"))
        
        single_grid = Container(classes="action-grid")
        
        # Single bot action buttons
        single_actions = [
            ("start-bot", "▶ Start", "primary", self._start_bot),
            ("pause-bot", "⏸ Pause", "warning", self._pause_bot),
            ("stop-bot", "⏹ Stop", "error", self._stop_bot),
            ("resume-bot", "▶ Resume", "success", self._resume_bot),
            ("delete-bot", "🗑 Delete", "error", self._delete_bot),
            ("clone-bot", "📋 Clone", "default", self._clone_bot),
            ("edit-bot", "✏ Edit", "default", self._edit_bot),
            ("view-logs", "📄 Logs", "default", self._view_logs),
            ("deploy-lab", "🚀 Deploy", "primary", self._deploy_from_lab)
        ]
        
        for action_id, label, variant, callback in single_actions:
            button = Button(
                label,
                variant=variant,
                disabled=True,  # Disabled until bot is selected
                id=action_id
            )
            single_grid.mount(button)
        
        single_section.mount(single_grid)
        content_container.mount(single_section)
        
        # Batch Operations Section
        batch_section = Container(classes="action-section")
        batch_section.mount(Label("Batch Operations", classes="section-title"))
        
        batch_controls = Horizontal(classes="batch-controls")
        batch_controls.mount(Button("Start All", id="batch-start", variant="primary", disabled=True))
        batch_controls.mount(Button("Pause All", id="batch-pause", variant="warning", disabled=True))
        batch_controls.mount(Button("Stop All", id="batch-stop", variant="error", disabled=True))
        batch_controls.mount(Label("Selected: 0 bots", id="batch-count"))
        
        batch_section.mount(batch_controls)
        content_container.mount(batch_section)
        
        # Emergency Controls Section
        emergency_section = Container(classes="action-section emergency-section")
        emergency_section.mount(Label("Emergency Controls", classes="section-title"))
        
        emergency_controls = Horizontal(classes="batch-controls")
        emergency_controls.mount(Button(
            "🚨 EMERGENCY STOP ALL",
            id="emergency-stop",
            variant="error"
        ))
        emergency_controls.mount(Button(
            "⚠ Pause All Active",
            id="emergency-pause",
            variant="warning"
        ))
        
        emergency_section.mount(emergency_controls)
        content_container.mount(emergency_section)
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for bot operations"""
        self.mcp_client = mcp_client
    
    def set_current_bot(self, bot_data: Optional[Dict[str, Any]]) -> None:
        """Set current bot and update action availability"""
        self.current_bot = bot_data
        self._update_action_states()
    
    def set_selected_bots(self, selected_bots: List[Dict[str, Any]]) -> None:
        """Set selected bots for batch operations"""
        self.selected_bots = selected_bots
        self._update_batch_states()
    
    def _update_action_states(self) -> None:
        """Update action button states based on current bot"""
        has_bot = self.current_bot is not None
        
        # Get bot status if available
        bot_status = None
        if has_bot:
            bot_status = self.current_bot.get("_status", "unknown")
        
        # Update single bot action buttons
        action_states = {
            "start-bot": has_bot and bot_status in ["stopped", "paused"],
            "pause-bot": has_bot and bot_status == "active",
            "stop-bot": has_bot and bot_status in ["active", "paused"],
            "resume-bot": has_bot and bot_status == "paused",
            "delete-bot": has_bot,
            "clone-bot": has_bot,
            "edit-bot": has_bot,
            "view-logs": has_bot,
            "deploy-lab": True  # Always available for creating new bots
        }
        
        for action_id, enabled in action_states.items():
            try:
                button = self.query_one(f"#{action_id}", Button)
                button.disabled = not enabled
            except:
                pass  # Button might not exist yet
    
    def _update_batch_states(self) -> None:
        """Update batch operation states"""
        has_selection = len(self.selected_bots) > 0
        
        # Update batch buttons
        batch_buttons = ["batch-start", "batch-pause", "batch-stop"]
        for button_id in batch_buttons:
            try:
                button = self.query_one(f"#{button_id}", Button)
                button.disabled = not has_selection
            except:
                pass
        
        # Update count label
        try:
            count_label = self.query_one("#batch-count", Label)
            count_label.update(f"Selected: {len(self.selected_bots)} bots")
        except:
            pass
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        
        if not button_id:
            return
        
        try:
            # Single bot actions
            if button_id == "start-bot":
                await self._start_bot()
            elif button_id == "pause-bot":
                await self._pause_bot()
            elif button_id == "stop-bot":
                await self._stop_bot()
            elif button_id == "resume-bot":
                await self._resume_bot()
            elif button_id == "delete-bot":
                await self._delete_bot()
            elif button_id == "clone-bot":
                await self._clone_bot()
            elif button_id == "edit-bot":
                await self._edit_bot()
            elif button_id == "view-logs":
                await self._view_logs()
            elif button_id == "deploy-lab":
                await self._deploy_from_lab()
            
            # Batch operations
            elif button_id == "batch-start":
                await self._batch_start()
            elif button_id == "batch-pause":
                await self._batch_pause()
            elif button_id == "batch-stop":
                await self._batch_stop()
            
            # Emergency operations
            elif button_id == "emergency-stop":
                await self._emergency_stop_all()
            elif button_id == "emergency-pause":
                await self._emergency_pause_all()
                
        except Exception as e:
            self.logger.error(f"Action failed: {e}")
            self.set_status("error", f"Action failed: {str(e)}")
    
    async def _start_bot(self) -> None:
        """Start the current bot"""
        if not self.current_bot or not self.mcp_client:
            return
        
        bot_id = self.current_bot.get("_raw_data", {}).get("bot_id")
        if not bot_id:
            self.set_status("error", "Bot ID not available")
            return
        
        self.set_status("normal", "Starting bot...")
        try:
            await self.mcp_client.activate_bot(bot_id)
            self.set_status("success", "Bot started successfully")
            self.post_message(self.BotActionCompleted("start", self.current_bot))
        except Exception as e:
            self.set_status("error", f"Failed to start bot: {str(e)}")
    
    async def _pause_bot(self) -> None:
        """Pause the current bot"""
        if not self.current_bot or not self.mcp_client:
            return
        
        bot_id = self.current_bot.get("_raw_data", {}).get("bot_id")
        if not bot_id:
            return
        
        self.set_status("normal", "Pausing bot...")
        try:
            await self.mcp_client.pause_bot(bot_id)
            self.set_status("success", "Bot paused successfully")
            self.post_message(self.BotActionCompleted("pause", self.current_bot))
        except Exception as e:
            self.set_status("error", f"Failed to pause bot: {str(e)}")
    
    async def _stop_bot(self) -> None:
        """Stop the current bot"""
        if not self.current_bot or not self.mcp_client:
            return
        
        bot_id = self.current_bot.get("_raw_data", {}).get("bot_id")
        if not bot_id:
            return
        
        self.set_status("normal", "Stopping bot...")
        try:
            await self.mcp_client.deactivate_bot(bot_id)
            self.set_status("success", "Bot stopped successfully")
            self.post_message(self.BotActionCompleted("stop", self.current_bot))
        except Exception as e:
            self.set_status("error", f"Failed to stop bot: {str(e)}")
    
    async def _resume_bot(self) -> None:
        """Resume the current bot"""
        if not self.current_bot or not self.mcp_client:
            return
        
        bot_id = self.current_bot.get("_raw_data", {}).get("bot_id")
        if not bot_id:
            return
        
        self.set_status("normal", "Resuming bot...")
        try:
            await self.mcp_client.resume_bot(bot_id)
            self.set_status("success", "Bot resumed successfully")
            self.post_message(self.BotActionCompleted("resume", self.current_bot))
        except Exception as e:
            self.set_status("error", f"Failed to resume bot: {str(e)}")
    
    async def _delete_bot(self) -> None:
        """Delete the current bot"""
        if not self.current_bot or not self.mcp_client:
            return
        
        # TODO: Add confirmation dialog
        bot_id = self.current_bot.get("_raw_data", {}).get("bot_id")
        if not bot_id:
            return
        
        self.set_status("normal", "Deleting bot...")
        try:
            await self.mcp_client.delete_bot(bot_id)
            self.set_status("success", "Bot deleted successfully")
            self.post_message(self.BotActionCompleted("delete", self.current_bot))
        except Exception as e:
            self.set_status("error", f"Failed to delete bot: {str(e)}")
    
    async def _clone_bot(self) -> None:
        """Clone the current bot"""
        if not self.current_bot or not self.mcp_client:
            return
        
        bot_id = self.current_bot.get("_raw_data", {}).get("bot_id")
        if not bot_id:
            self.set_status("error", "Bot ID not available")
            return
        
        self.set_status("normal", "Cloning bot...")
        try:
            # Get bot configuration
            bot_config = await self.mcp_client.get_bot_details(bot_id)
            if not bot_config:
                self.set_status("error", "Failed to get bot configuration")
                return
            
            # Create clone with modified name
            clone_name = f"{bot_config.get('name', 'Bot')}_Clone_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            clone_config = bot_config.copy()
            clone_config['name'] = clone_name
            
            # Remove ID fields that shouldn't be copied
            for field in ['bot_id', 'created_at', 'last_updated']:
                clone_config.pop(field, None)
            
            # Create the cloned bot
            result = await self.mcp_client.create_bot(clone_config)
            if result:
                self.set_status("success", f"Bot cloned successfully as '{clone_name}'")
                self.post_message(self.BotActionCompleted("clone", self.current_bot))
            else:
                self.set_status("error", "Failed to create bot clone")
                
        except Exception as e:
            self.set_status("error", f"Failed to clone bot: {str(e)}")
    
    async def _edit_bot(self) -> None:
        """Edit the current bot"""
        if not self.current_bot:
            return
        
        # Post message to open bot configuration editor
        self.post_message(self.EditBotRequested(self.current_bot))
    
    async def _view_logs(self) -> None:
        """View bot logs"""
        if not self.current_bot:
            return
        
        # Post message to open bot logs viewer
        self.post_message(self.ViewLogsRequested(self.current_bot))
    
    async def _deploy_from_lab(self) -> None:
        """Deploy bot from lab results"""
        self.post_message(self.DeployFromLabRequested())
    
    async def _batch_start(self) -> None:
        """Start all selected bots"""
        await self._batch_operation("start", self.mcp_client.activate_bot)
    
    async def _batch_pause(self) -> None:
        """Pause all selected bots"""
        await self._batch_operation("pause", self.mcp_client.pause_bot)
    
    async def _batch_stop(self) -> None:
        """Stop all selected bots"""
        await self._batch_operation("stop", self.mcp_client.deactivate_bot)
    
    async def _batch_operation(self, operation: str, operation_func: Callable) -> None:
        """Execute batch operation on selected bots with improved error handling"""
        if not self.selected_bots or not self.mcp_client:
            return
        
        total_bots = len(self.selected_bots)
        self.set_status("normal", f"Executing {operation} on {total_bots} bots...")
        
        # Use semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent operations
        
        async def execute_operation_with_semaphore(bot):
            async with semaphore:
                try:
                    bot_id = bot.get("_raw_data", {}).get("bot_id")
                    bot_name = bot.get("Name", "Unknown")
                    
                    if not bot_id:
                        self.logger.warning(f"No bot_id found for bot {bot_name}")
                        return {"success": False, "error": "No bot ID", "bot_name": bot_name}
                    
                    await operation_func(bot_id)
                    return {"success": True, "bot_name": bot_name}
                    
                except Exception as e:
                    error_msg = str(e)
                    self.logger.error(f"Batch {operation} failed for bot {bot_name}: {error_msg}")
                    return {"success": False, "error": error_msg, "bot_name": bot_name}
        
        # Execute all operations concurrently
        tasks = [execute_operation_with_semaphore(bot) for bot in self.selected_bots]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        error_count = 0
        failed_bots = []
        
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                failed_bots.append(f"Unknown: {str(result)}")
            elif isinstance(result, dict):
                if result.get("success"):
                    success_count += 1
                else:
                    error_count += 1
                    bot_name = result.get("bot_name", "Unknown")
                    error = result.get("error", "Unknown error")
                    failed_bots.append(f"{bot_name}: {error}")
            else:
                error_count += 1
                failed_bots.append("Unknown: Unexpected result")
        
        # Update status based on results
        if error_count == 0:
            self.set_status("success", f"✅ Successfully {operation}ed all {success_count} bots")
        elif success_count == 0:
            self.set_status("error", f"❌ Failed to {operation} all {total_bots} bots")
        else:
            self.set_status("warning", f"⚠️ {operation.title()}ed {success_count}/{total_bots} bots ({error_count} failed)")
        
        # Log failed operations for debugging
        if failed_bots:
            self.logger.warning(f"Batch {operation} failures: {'; '.join(failed_bots[:5])}")  # Log first 5 failures
        
        self.post_message(self.BatchActionCompleted(operation, success_count, error_count, failed_bots))
    
    async def _emergency_stop_all(self) -> None:
        """Emergency stop all bots with confirmation"""
        if not self.mcp_client:
            return
        
        # Post message to show confirmation dialog
        self.post_message(self.EmergencyActionRequested("stop"))
    
    async def _emergency_pause_all(self) -> None:
        """Emergency pause all active bots with confirmation"""
        if not self.mcp_client:
            return
        
        # Post message to show confirmation dialog
        self.post_message(self.EmergencyActionRequested("pause"))
    
    async def execute_emergency_stop(self) -> None:
        """Execute emergency stop after confirmation"""
        if not self.mcp_client:
            return
        
        self.set_status("normal", "Emergency stop - getting all active bots...")
        try:
            # Get all active bots and stop them
            all_bots_response = await self.mcp_client.get_all_bots()
            
            if isinstance(all_bots_response, dict) and "bots" in all_bots_response:
                all_bots = all_bots_response["bots"]
            elif isinstance(all_bots_response, list):
                all_bots = all_bots_response
            else:
                all_bots = []
            
            active_bots = [
                bot for bot in all_bots 
                if bot.get("status", "").lower() in ["active", "running"]
            ]
            
            if not active_bots:
                self.set_status("info", "No active bots to stop")
                return
            
            self.set_status("normal", f"🚨 Emergency stopping {len(active_bots)} active bots...")
            
            # Stop all active bots concurrently with limited concurrency
            semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent operations
            
            async def stop_bot_with_semaphore(bot):
                async with semaphore:
                    try:
                        bot_id = bot.get("bot_id")
                        if bot_id:
                            await self.mcp_client.deactivate_bot(bot_id)
                            return True
                    except Exception as e:
                        self.logger.error(f"Failed to stop bot {bot.get('name', 'Unknown')}: {e}")
                        return False
                    return False
            
            tasks = [stop_bot_with_semaphore(bot) for bot in active_bots]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if r is True)
            error_count = len(results) - success_count
            
            if error_count == 0:
                self.set_status("success", f"🚨 Emergency stop completed: {success_count} bots stopped")
            else:
                self.set_status("warning", f"🚨 Emergency stop completed: {success_count} stopped, {error_count} failed")
            
            self.post_message(self.EmergencyActionCompleted("stop", success_count, error_count))
            
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")
            self.set_status("error", f"🚨 Emergency stop failed: {str(e)}")
    
    async def execute_emergency_pause(self) -> None:
        """Execute emergency pause after confirmation"""
        if not self.mcp_client:
            return
        
        self.set_status("normal", "Emergency pause - getting all active bots...")
        try:
            all_bots_response = await self.mcp_client.get_all_bots()
            
            if isinstance(all_bots_response, dict) and "bots" in all_bots_response:
                all_bots = all_bots_response["bots"]
            elif isinstance(all_bots_response, list):
                all_bots = all_bots_response
            else:
                all_bots = []
            
            active_bots = [
                bot for bot in all_bots 
                if bot.get("status", "").lower() == "active"
            ]
            
            if not active_bots:
                self.set_status("info", "No active bots to pause")
                return
            
            self.set_status("normal", f"⚠️ Emergency pausing {len(active_bots)} active bots...")
            
            # Pause all active bots concurrently with limited concurrency
            semaphore = asyncio.Semaphore(5)
            
            async def pause_bot_with_semaphore(bot):
                async with semaphore:
                    try:
                        bot_id = bot.get("bot_id")
                        if bot_id:
                            await self.mcp_client.pause_bot(bot_id)
                            return True
                    except Exception as e:
                        self.logger.error(f"Failed to pause bot {bot.get('name', 'Unknown')}: {e}")
                        return False
                    return False
            
            tasks = [pause_bot_with_semaphore(bot) for bot in active_bots]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if r is True)
            error_count = len(results) - success_count
            
            if error_count == 0:
                self.set_status("success", f"⚠️ Emergency pause completed: {success_count} bots paused")
            else:
                self.set_status("warning", f"⚠️ Emergency pause completed: {success_count} paused, {error_count} failed")
            
            self.post_message(self.EmergencyActionCompleted("pause", success_count, error_count))
            
        except Exception as e:
            self.logger.error(f"Emergency pause failed: {e}")
            self.set_status("error", f"⚠️ Emergency pause failed: {str(e)}")
    
    class BotActionCompleted(Message):
        """Message sent when a bot action is completed"""
        def __init__(self, action: str, bot_data: Dict[str, Any]):
            super().__init__()
            self.action = action
            self.bot_data = bot_data
    
    class BatchActionCompleted(Message):
        """Message sent when a batch action is completed"""
        def __init__(self, action: str, success_count: int, error_count: int, failed_bots: List[str] = None):
            super().__init__()
            self.action = action
            self.success_count = success_count
            self.error_count = error_count
            self.failed_bots = failed_bots or []
    
    class DeployFromLabRequested(Message):
        """Message sent when deploy from lab is requested"""
        pass
    
    class EditBotRequested(Message):
        """Message sent when bot editing is requested"""
        def __init__(self, bot_data: Dict[str, Any]):
            super().__init__()
            self.bot_data = bot_data
    
    class ViewLogsRequested(Message):
        """Message sent when log viewing is requested"""
        def __init__(self, bot_data: Dict[str, Any]):
            super().__init__()
            self.bot_data = bot_data
    
    class EmergencyActionRequested(Message):
        """Message sent when emergency action is requested"""
        def __init__(self, action: str):
            super().__init__()
            self.action = action  # "stop" or "pause"
    
    class EmergencyActionCompleted(Message):
        """Message sent when emergency action is completed"""
        def __init__(self, action: str, success_count: int, error_count: int):
            super().__init__()
            self.action = action
            self.success_count = success_count
            self.error_count = error_count


class ConfirmationDialog(Widget):
    """Confirmation dialog for critical operations"""
    
    DEFAULT_CSS = """
    ConfirmationDialog {
        background: $surface;
        border: solid $error;
        padding: 2;
        width: 60;
        height: 15;
        margin: 5;
    }
    
    ConfirmationDialog .dialog-title {
        text-style: bold;
        color: $error;
        text-align: center;
        margin: 0 0 2 0;
    }
    
    ConfirmationDialog .dialog-message {
        text-align: center;
        margin: 1 0;
        color: $text;
    }
    
    ConfirmationDialog .dialog-warning {
        text-align: center;
        margin: 1 0;
        color: $warning;
        text-style: bold;
    }
    
    ConfirmationDialog .dialog-buttons {
        dock: bottom;
        layout: horizontal;
        height: 3;
        align: center middle;
        margin: 2 0 0 0;
    }
    
    ConfirmationDialog .dialog-button {
        margin: 0 2;
        min-width: 12;
    }
    """
    
    def __init__(self, title: str, message: str, warning: str = "", **kwargs):
        super().__init__(**kwargs)
        self.dialog_title = title
        self.dialog_message = message
        self.dialog_warning = warning
    
    def compose(self) -> ComposeResult:
        """Compose confirmation dialog"""
        yield Label(self.dialog_title, classes="dialog-title")
        yield Label(self.dialog_message, classes="dialog-message")
        
        if self.dialog_warning:
            yield Label(self.dialog_warning, classes="dialog-warning")
        
        # Dialog buttons
        buttons = Horizontal(classes="dialog-buttons")
        buttons.mount(Button("Cancel", id="dialog-cancel", variant="default", classes="dialog-button"))
        buttons.mount(Button("Confirm", id="dialog-confirm", variant="error", classes="dialog-button"))
        yield buttons
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "dialog-cancel":
            self.post_message(self.DialogCancelled())
        elif event.button.id == "dialog-confirm":
            self.post_message(self.DialogConfirmed())
    
    class DialogCancelled(Message):
        """Message sent when dialog is cancelled"""
        pass
    
    class DialogConfirmed(Message):
        """Message sent when dialog is confirmed"""
        pass


class BotDeploymentWizard(Widget):
    """Wizard for deploying bots from lab results"""
    
    DEFAULT_CSS = """
    BotDeploymentWizard {
        background: $surface;
        border: solid $primary;
        padding: 2;
        width: 80;
        height: 30;
        margin: 2;
    }
    
    BotDeploymentWizard .wizard-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        margin: 0 0 2 0;
    }
    
    BotDeploymentWizard .wizard-step {
        margin: 1 0;
        padding: 1;
        border: solid $accent;
    }
    
    BotDeploymentWizard .step-title {
        text-style: bold;
        color: $accent;
        margin: 0 0 1 0;
    }
    
    BotDeploymentWizard .form-row {
        layout: horizontal;
        height: 3;
        align: center middle;
        margin: 0 0 1 0;
    }
    
    BotDeploymentWizard .form-label {
        width: 20;
        color: $text-muted;
    }
    
    BotDeploymentWizard .form-input {
        width: 1fr;
        margin: 0 1;
    }
    
    BotDeploymentWizard .wizard-buttons {
        dock: bottom;
        layout: horizontal;
        height: 3;
        align: center middle;
        margin: 2 0 0 0;
    }
    
    BotDeploymentWizard .wizard-button {
        margin: 0 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.lab_results: List[Dict[str, Any]] = []
        self.accounts: List[Dict[str, Any]] = []
        self.selected_lab: Optional[Dict[str, Any]] = None
        self.bot_config: Dict[str, Any] = {}
        self.logger = get_logger(__name__)
    
    def compose(self) -> ComposeResult:
        """Compose deployment wizard"""
        yield Label("🚀 Bot Deployment Wizard", classes="wizard-title")
        
        # Step 1: Select Lab Results
        step1 = Container(classes="wizard-step")
        step1.mount(Label("Step 1: Select Lab Results", classes="step-title"))
        
        lab_row = Horizontal(classes="form-row")
        lab_row.mount(Label("Lab Results:", classes="form-label"))
        lab_row.mount(Select(
            [("Loading...", "loading")],
            value="loading",
            id="lab-select",
            classes="form-input"
        ))
        step1.mount(lab_row)
        
        yield step1
        
        # Step 2: Bot Configuration
        step2 = Container(classes="wizard-step")
        step2.mount(Label("Step 2: Bot Configuration", classes="step-title"))
        
        name_row = Horizontal(classes="form-row")
        name_row.mount(Label("Bot Name:", classes="form-label"))
        name_row.mount(Input(
            placeholder="Enter bot name...",
            id="bot-name",
            classes="form-input"
        ))
        step2.mount(name_row)
        
        account_row = Horizontal(classes="form-row")
        account_row.mount(Label("Account:", classes="form-label"))
        account_row.mount(Select(
            [("Loading...", "loading")],
            value="loading",
            id="account-select",
            classes="form-input"
        ))
        step2.mount(account_row)
        
        leverage_row = Horizontal(classes="form-row")
        leverage_row.mount(Label("Leverage:", classes="form-label"))
        leverage_row.mount(Input(
            placeholder="1.0",
            id="leverage",
            classes="form-input"
        ))
        step2.mount(leverage_row)
        
        yield step2
        
        # Step 3: Risk Management
        step3 = Container(classes="wizard-step")
        step3.mount(Label("Step 3: Risk Management", classes="step-title"))
        
        max_positions_row = Horizontal(classes="form-row")
        max_positions_row.mount(Label("Max Positions:", classes="form-label"))
        max_positions_row.mount(Input(
            placeholder="1",
            id="max-positions",
            classes="form-input"
        ))
        step3.mount(max_positions_row)
        
        stop_loss_row = Horizontal(classes="form-row")
        stop_loss_row.mount(Label("Stop Loss %:", classes="form-label"))
        stop_loss_row.mount(Input(
            placeholder="5.0",
            id="stop-loss",
            classes="form-input"
        ))
        step3.mount(stop_loss_row)
        
        yield step3
        
        # Wizard buttons
        buttons = Horizontal(classes="wizard-buttons")
        buttons.mount(Button("Cancel", id="cancel-wizard", variant="default", classes="wizard-button"))
        buttons.mount(Button("Deploy Bot", id="deploy-bot", variant="primary", classes="wizard-button"))
        yield buttons
    
    async def on_mount(self) -> None:
        """Initialize wizard on mount"""
        await self._load_wizard_data()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for data operations"""
        self.mcp_client = mcp_client
    
    async def _load_wizard_data(self) -> None:
        """Load lab results and accounts for wizard"""
        if not self.mcp_client:
            return
        
        try:
            # Load lab results
            labs_response = await self.mcp_client.get_all_labs()
            if isinstance(labs_response, dict) and "labs" in labs_response:
                self.lab_results = labs_response["labs"]
            elif isinstance(labs_response, list):
                self.lab_results = labs_response
            else:
                self.lab_results = []
            
            # Filter for completed labs with good results
            completed_labs = [
                lab for lab in self.lab_results
                if lab.get("status") == "completed" and lab.get("total_return", 0) > 0
            ]
            
            # Update lab select options
            lab_options = [("Select lab results...", "")]
            for lab in completed_labs:
                lab_name = lab.get("name", "Unknown Lab")
                total_return = lab.get("total_return", 0)
                lab_options.append((f"{lab_name} (Return: {total_return:.2f}%)", lab.get("lab_id", "")))
            
            lab_select = self.query_one("#lab-select", Select)
            lab_select.set_options(lab_options)
            
            # Load accounts
            accounts_response = await self.mcp_client.get_all_accounts()
            if isinstance(accounts_response, dict) and "accounts" in accounts_response:
                self.accounts = accounts_response["accounts"]
            elif isinstance(accounts_response, list):
                self.accounts = accounts_response
            else:
                self.accounts = []
            
            # Update account select options
            account_options = [("Select account...", "")]
            for account in self.accounts:
                account_name = account.get("name", "Unknown Account")
                account_balance = account.get("balance", 0)
                account_options.append((f"{account_name} (${account_balance:.2f})", account.get("account_id", "")))
            
            account_select = self.query_one("#account-select", Select)
            account_select.set_options(account_options)
            
        except Exception as e:
            self.logger.error(f"Failed to load wizard data: {e}")
    
    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes"""
        if event.select.id == "lab-select" and event.value:
            # Find selected lab
            self.selected_lab = next(
                (lab for lab in self.lab_results if lab.get("lab_id") == event.value),
                None
            )
            
            if self.selected_lab:
                # Auto-populate bot name
                lab_name = self.selected_lab.get("name", "Lab")
                bot_name = f"Bot_{lab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                name_input = self.query_one("#bot-name", Input)
                name_input.value = bot_name
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "cancel-wizard":
            self.post_message(self.WizardCancelled())
        elif event.button.id == "deploy-bot":
            await self._deploy_bot()
    
    async def _deploy_bot(self) -> None:
        """Deploy bot with configured settings"""
        if not self.mcp_client or not self.selected_lab:
            return
        
        try:
            # Collect form data
            bot_name = self.query_one("#bot-name", Input).value
            account_id = self.query_one("#account-select", Select).value
            leverage = float(self.query_one("#leverage", Input).value or "1.0")
            max_positions = int(self.query_one("#max-positions", Input).value or "1")
            stop_loss = float(self.query_one("#stop-loss", Input).value or "0.0")
            
            if not bot_name or not account_id:
                self.post_message(self.WizardError("Please fill in all required fields"))
                return
            
            # Create bot configuration from lab results
            bot_config = {
                "name": bot_name,
                "account_id": account_id,
                "script_id": self.selected_lab.get("script_id"),
                "market": self.selected_lab.get("market"),
                "leverage": leverage,
                "max_positions": max_positions,
                "stop_loss_percentage": stop_loss,
                "parameters": self.selected_lab.get("parameters", {}),
                "auto_start": True
            }
            
            # Deploy the bot
            result = await self.mcp_client.create_bot(bot_config)
            
            if result:
                bot_id = result.get("bot_id") if isinstance(result, dict) else None
                self.post_message(self.BotDeployed(bot_config, bot_id))
            else:
                self.post_message(self.WizardError("Failed to deploy bot"))
                
        except ValueError as e:
            self.post_message(self.WizardError(f"Invalid input: {str(e)}"))
        except Exception as e:
            self.logger.error(f"Bot deployment failed: {e}")
            self.post_message(self.WizardError(f"Deployment failed: {str(e)}"))
    
    class WizardCancelled(Message):
        """Message sent when wizard is cancelled"""
        pass
    
    class BotDeployed(Message):
        """Message sent when bot is successfully deployed"""
        def __init__(self, bot_config: Dict[str, Any], bot_id: Optional[str]):
            super().__init__()
            self.bot_config = bot_config
            self.bot_id = bot_id
    
    class WizardError(Message):
        """Message sent when wizard encounters an error"""
        def __init__(self, error_message: str):
            super().__init__()
            self.error_message = error_message


class BotPerformanceChart(BasePanel):
    """Enhanced panel with bot performance charts and metrics"""
    
    DEFAULT_CSS = """
    BotPerformanceChart {
        height: 1fr;
        min-height: 15;
    }
    
    BotPerformanceChart .chart-container {
        height: 1fr;
        border: solid $accent;
        padding: 1;
    }
    
    BotPerformanceChart .chart-controls {
        dock: top;
        height: 3;
        background: $surface;
        padding: 1;
    }
    
    BotPerformanceChart .control-row {
        height: 1;
        layout: horizontal;
        align: center middle;
    }
    
    BotPerformanceChart .metrics-summary {
        dock: bottom;
        height: 4;
        background: $surface;
        padding: 1;
    }
    
    BotPerformanceChart .metrics-grid {
        layout: grid;
        grid-size: 4 1;
        grid-gutter: 1;
        height: 2;
    }
    
    BotPerformanceChart .metric-item {
        text-align: center;
        border: solid $surface;
        padding: 0 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(title="Performance Chart", show_header=True, show_footer=True, **kwargs)
        self.current_bot: Optional[Dict[str, Any]] = None
        self.chart_timeframe = "24h"
        self.chart_type = "pnl"
        self.performance_data: List[Dict[str, Any]] = []
        self.mcp_client: Optional[MCPClientService] = None
        self.logger = get_logger(__name__)
    
    def compose(self) -> ComposeResult:
        """Compose performance chart panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize panel on mount"""
        await self._setup_components()
    
    async def _setup_components(self) -> None:
        """Set up chart components"""
        content_container = self.query_one("#panel-content")
        
        # Chart controls
        controls_container = Container(classes="chart-controls")
        
        # Timeframe controls
        timeframe_row = Horizontal(classes="control-row")
        timeframe_row.mount(Label("Timeframe:", classes="filter-item"))
        timeframe_row.mount(Select(
            [
                ("1 Hour", "1h"),
                ("24 Hours", "24h"),
                ("7 Days", "7d"),
                ("30 Days", "30d")
            ],
            value="24h",
            id="timeframe-select"
        ))
        timeframe_row.mount(Label("Chart:", classes="filter-item"))
        timeframe_row.mount(Select(
            [
                ("P&L", "pnl"),
                ("Equity", "equity"),
                ("Trades", "trades"),
                ("Drawdown", "drawdown")
            ],
            value="pnl",
            id="chart-type-select"
        ))
        timeframe_row.mount(Button("Refresh", id="refresh-chart"))
        
        controls_container.mount(timeframe_row)
        content_container.mount(controls_container)
        
        # Chart container
        self.chart_container = Container(classes="chart-container")
        self.chart_display = Static("Select a bot to view performance chart", id="chart-display")
        self.chart_container.mount(self.chart_display)
        content_container.mount(self.chart_container)
        
        # Metrics summary
        metrics_container = Container(classes="metrics-summary")
        metrics_container.mount(Label("Performance Summary", classes="section-title"))
        
        self.metrics_grid = Container(classes="metrics-grid")
        
        # Initialize empty metrics
        metric_labels = ["Total P&L", "Win Rate", "Sharpe Ratio", "Max DD"]
        for label in metric_labels:
            metric_item = Container(classes="metric-item")
            metric_item.mount(Label("--", classes="metric-value"))
            metric_item.mount(Label(label, classes="metric-label"))
            self.metrics_grid.mount(metric_item)
        
        metrics_container.mount(self.metrics_grid)
        content_container.mount(metrics_container)
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for data operations"""
        self.mcp_client = mcp_client
    
    async def show_bot_performance(self, bot_data: Dict[str, Any]) -> None:
        """Show performance chart for selected bot"""
        self.current_bot = bot_data
        bot_name = bot_data.get("Name", "Unknown Bot")
        self.title = f"Performance: {bot_name}"
        
        await self._load_performance_data()
        await self._render_chart()
        self._update_metrics_summary()
    
    async def _load_performance_data(self) -> None:
        """Load performance data from MCP server"""
        if not self.current_bot or not self.mcp_client:
            return
        
        try:
            self.set_status("normal", "Loading performance data...")
            
            raw_data = self.current_bot.get("_raw_data", {})
            bot_id = raw_data.get("bot_id")
            
            if bot_id:
                # Get detailed performance data
                detailed_data = await self.mcp_client.get_bot_details(bot_id)
                
                # Extract performance history
                self.performance_data = detailed_data.get("performance_history", [])
                
                # If no history, create sample data based on current metrics
                if not self.performance_data:
                    self.performance_data = self._generate_sample_data()
            else:
                self.performance_data = self._generate_sample_data()
            
            self.set_status("success", "Performance data loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load performance data: {e}")
            self.set_status("error", f"Failed to load data: {str(e)}")
            self.performance_data = self._generate_sample_data()
    
    def _generate_sample_data(self) -> List[Dict[str, Any]]:
        """Generate sample performance data for demonstration"""
        import random
        from datetime import datetime, timedelta
        
        data = []
        base_pnl = self.current_bot.get("_pnl", 0) if self.current_bot else 0
        current_time = datetime.now()
        
        # Generate hourly data for the last 24 hours
        for i in range(24):
            timestamp = current_time - timedelta(hours=23-i)
            
            # Simulate P&L progression
            pnl_change = random.uniform(-50, 50)
            cumulative_pnl = base_pnl * (i + 1) / 24 + pnl_change
            
            data.append({
                "timestamp": timestamp.isoformat(),
                "pnl": cumulative_pnl,
                "equity": 10000 + cumulative_pnl,
                "trades": random.randint(0, 3),
                "drawdown": random.uniform(0, 5)
            })
        
        return data
    
    async def _render_chart(self) -> None:
        """Render the performance chart"""
        if not self.performance_data:
            self.chart_display.update("No performance data available")
            return
        
        chart_text = self._create_ascii_chart()
        self.chart_display.update(chart_text)
    
    def _create_ascii_chart(self) -> str:
        """Create ASCII chart from performance data"""
        if not self.performance_data:
            return "No data available"
        
        # Extract values based on chart type
        if self.chart_type == "pnl":
            values = [item.get("pnl", 0) for item in self.performance_data]
            title = "P&L Chart"
            unit = "$"
        elif self.chart_type == "equity":
            values = [item.get("equity", 0) for item in self.performance_data]
            title = "Equity Chart"
            unit = "$"
        elif self.chart_type == "trades":
            values = [item.get("trades", 0) for item in self.performance_data]
            title = "Trades Chart"
            unit = ""
        else:  # drawdown
            values = [item.get("drawdown", 0) for item in self.performance_data]
            title = "Drawdown Chart"
            unit = "%"
        
        if not values or all(v == 0 for v in values):
            return f"{title}\nNo data to display"
        
        # Create simple ASCII chart
        chart_width = 60
        chart_height = 10
        
        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Create chart lines
        chart_lines = []
        
        # Add title
        chart_lines.append(f"{title} ({self.chart_timeframe})")
        chart_lines.append("─" * chart_width)
        
        # Create chart body
        for row in range(chart_height):
            line = ""
            threshold = max_val - (row / (chart_height - 1)) * val_range
            
            # Y-axis label
            line += f"{threshold:6.1f}{unit} ┤"
            
            # Chart data
            for i, value in enumerate(values):
                x_pos = int(i * (chart_width - 10) / len(values))
                if len(line) <= x_pos + 10:
                    line += " " * (x_pos + 10 - len(line) + 1)
                
                if abs(value - threshold) <= val_range / chart_height:
                    if value >= 0:
                        line = line[:x_pos + 10] + "█" + line[x_pos + 11:]
                    else:
                        line = line[:x_pos + 10] + "▄" + line[x_pos + 11:]
            
            chart_lines.append(line)
        
        # Add time axis
        time_axis = "        └" + "─" * (chart_width - 10)
        chart_lines.append(time_axis)
        
        # Add time labels
        if self.performance_data:
            start_time = self.performance_data[0].get("timestamp", "")
            end_time = self.performance_data[-1].get("timestamp", "")
            
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                time_labels = f"         {start_dt.strftime('%H:%M')}"
                time_labels += " " * (chart_width - 20)
                time_labels += f"{end_dt.strftime('%H:%M')}"
                chart_lines.append(time_labels)
            except:
                pass
        
        return "\n".join(chart_lines)
    
    def _update_metrics_summary(self) -> None:
        """Update performance metrics summary"""
        if not self.performance_data or not self.current_bot:
            return
        
        try:
            # Calculate metrics from performance data
            pnl_values = [item.get("pnl", 0) for item in self.performance_data]
            total_pnl = pnl_values[-1] if pnl_values else 0
            
            # Win rate calculation (simplified)
            positive_periods = sum(1 for pnl in pnl_values if pnl > 0)
            win_rate = (positive_periods / len(pnl_values) * 100) if pnl_values else 0
            
            # Sharpe ratio (simplified)
            if len(pnl_values) > 1:
                returns = [pnl_values[i] - pnl_values[i-1] for i in range(1, len(pnl_values))]
                avg_return = sum(returns) / len(returns) if returns else 0
                return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5 if returns else 1
                sharpe_ratio = avg_return / return_std if return_std > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Max drawdown
            drawdowns = [item.get("drawdown", 0) for item in self.performance_data]
            max_drawdown = max(drawdowns) if drawdowns else 0
            
            # Update metric displays
            metrics = [
                (f"${total_pnl:+.2f}", "Total P&L"),
                (f"{win_rate:.1f}%", "Win Rate"),
                (f"{sharpe_ratio:.2f}", "Sharpe Ratio"),
                (f"{max_drawdown:.1f}%", "Max DD")
            ]
            
            metric_containers = self.metrics_grid.children
            for i, (value, label) in enumerate(metrics):
                if i < len(metric_containers):
                    container = metric_containers[i]
                    value_label = container.children[0]
                    label_label = container.children[1]
                    
                    value_label.update(value)
                    label_label.update(label)
                    
                    # Color coding for P&L
                    if i == 0:  # Total P&L
                        if total_pnl > 0:
                            value_label.add_class("positive")
                        elif total_pnl < 0:
                            value_label.add_class("negative")
        
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle chart control changes"""
        if event.select.id == "timeframe-select":
            self.chart_timeframe = event.value
            if self.current_bot:
                await self._load_performance_data()
                await self._render_chart()
        elif event.select.id == "chart-type-select":
            self.chart_type = event.value
            if self.current_bot:
                await self._render_chart()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "refresh-chart":
            if self.current_bot:
                await self._load_performance_data()
                await self._render_chart()
                self._update_metrics_summary()


class BotManagementView(Widget):
    """Comprehensive bot management interface with enhanced functionality"""
    
    DEFAULT_CSS = """
    BotManagementView {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        padding: 1;
    }
    
    BotManagementView .bot-list {
        row-span: 2;
    }
    
    BotManagementView .bot-details {
        height: 1fr;
    }
    
    BotManagementView .bot-actions {
        height: auto;
        min-height: 15;
    }
    
    BotManagementView .bot-performance {
        height: 1fr;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.selected_bot: Optional[Dict[str, Any]] = None
        self.logger = get_logger(__name__)
    
    def compose(self) -> ComposeResult:
        """Compose bot management interface"""
        # Bot list panel (left side, full height)
        self.bot_list_panel = BotListPanel(classes="bot-list")
        yield self.bot_list_panel
        
        # Bot details panel (top right)
        self.bot_details_panel = BotDetailsPanel(classes="bot-details")
        yield self.bot_details_panel
        
        # Bot actions panel (middle right)
        self.bot_actions_panel = BotActionsPanel(classes="bot-actions")
        yield self.bot_actions_panel
        
        # Bot performance chart (bottom right)
        self.bot_performance_panel = BotPerformanceChart(classes="bot-performance")
        yield self.bot_performance_panel
    
    async def on_mount(self) -> None:
        """Initialize the bot management view"""
        # Set up message handlers and initialize components
        if self.mcp_client:
            await self._setup_mcp_client()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for all panels"""
        self.mcp_client = mcp_client
        
        # Set MCP client for all child panels
        self.bot_list_panel.set_mcp_client(mcp_client)
        self.bot_details_panel.set_mcp_client(mcp_client)
        self.bot_actions_panel.set_mcp_client(mcp_client)
        self.bot_performance_panel.set_mcp_client(mcp_client)
    
    async def _setup_mcp_client(self) -> None:
        """Set up MCP client for all panels"""
        if self.mcp_client:
            self.bot_list_panel.set_mcp_client(self.mcp_client)
            self.bot_details_panel.set_mcp_client(self.mcp_client)
            self.bot_actions_panel.set_mcp_client(self.mcp_client)
            self.bot_performance_panel.set_mcp_client(self.mcp_client)
    
    async def refresh_data(self) -> None:
        """Refresh all bot data"""
        try:
            await self.bot_list_panel.refresh_bots()
            
            # Refresh current bot details if one is selected
            if self.selected_bot:
                await self.bot_details_panel.refresh_current_bot()
                await self.bot_performance_panel.show_bot_performance(self.selected_bot)
                
        except Exception as e:
            self.logger.error(f"Failed to refresh bot data: {e}")
    
    async def on_bot_list_panel_bot_selected(self, message: BotListPanel.BotSelected) -> None:
        """Handle bot selection from list panel"""
        self.selected_bot = message.bot_data
        
        # Update other panels with selected bot
        await self.bot_details_panel.show_bot_details(message.bot_data)
        self.bot_actions_panel.set_current_bot(message.bot_data)
        await self.bot_performance_panel.show_bot_performance(message.bot_data)
    
    async def on_bot_list_panel_create_bot_requested(self, message: BotListPanel.CreateBotRequested) -> None:
        """Handle create bot request"""
        # TODO: Implement bot creation dialog
        self.logger.info("Create bot requested")
    
    async def on_bot_actions_panel_bot_action_completed(self, message: BotActionsPanel.BotActionCompleted) -> None:
        """Handle completed bot actions"""
        self.logger.info(f"Bot action completed: {message.action} on {message.bot_data.get('Name', 'Unknown')}")
        
        # Refresh data after action
        await self.refresh_data()
    
    async def on_bot_actions_panel_batch_action_completed(self, message: BotActionsPanel.BatchActionCompleted) -> None:
        """Handle completed batch actions"""
        self.logger.info(f"Batch action completed: {message.action} - {message.success_count} success, {message.error_count} errors")
        
        # Refresh data after batch action
        await self.refresh_data()
    
    async def on_bot_actions_panel_deploy_from_lab_requested(self, message: BotActionsPanel.DeployFromLabRequested) -> None:
        """Handle deploy from lab request"""
        self.logger.info("Deploy from lab requested")
        await self._show_deployment_wizard()
    
    async def on_bot_actions_panel_emergency_action_requested(self, message: BotActionsPanel.EmergencyActionRequested) -> None:
        """Handle emergency action request with confirmation"""
        if message.action == "stop":
            await self._show_emergency_stop_confirmation()
        elif message.action == "pause":
            await self._show_emergency_pause_confirmation()
    
    async def on_bot_actions_panel_edit_bot_requested(self, message: BotActionsPanel.EditBotRequested) -> None:
        """Handle bot editing request"""
        self.logger.info(f"Edit bot requested for {message.bot_data.get('Name', 'Unknown')}")
        # TODO: Implement bot configuration editor
    
    async def on_bot_actions_panel_view_logs_requested(self, message: BotActionsPanel.ViewLogsRequested) -> None:
        """Handle view logs request"""
        self.logger.info(f"View logs requested for {message.bot_data.get('Name', 'Unknown')}")
        # TODO: Implement log viewer
    
    def get_selected_bot(self) -> Optional[Dict[str, Any]]:
        """Get currently selected bot"""
        return self.selected_bot
    
    def get_bot_list_panel(self) -> BotListPanel:
        """Get bot list panel reference"""
        return self.bot_list_panel
    
    def get_bot_details_panel(self) -> BotDetailsPanel:
        """Get bot details panel reference"""
        return self.bot_details_panel
    
    def get_bot_actions_panel(self) -> BotActionsPanel:
        """Get bot actions panel reference"""
        return self.bot_actions_panel
    
    def get_bot_performance_panel(self) -> BotPerformanceChart:
        """Get bot performance panel reference"""
        return self.bot_performance_panel
    
    async def _show_deployment_wizard(self) -> None:
        """Show bot deployment wizard"""
        try:
            # Create and show deployment wizard
            wizard = BotDeploymentWizard()
            wizard.set_mcp_client(self.mcp_client)
            
            # Mount wizard as overlay
            await self.mount(wizard)
            
            # Set up wizard message handlers
            wizard.message_handlers = {
                BotDeploymentWizard.WizardCancelled: self._on_wizard_cancelled,
                BotDeploymentWizard.BotDeployed: self._on_bot_deployed,
                BotDeploymentWizard.WizardError: self._on_wizard_error
            }
            
        except Exception as e:
            self.logger.error(f"Failed to show deployment wizard: {e}")
    
    async def _show_emergency_stop_confirmation(self) -> None:
        """Show emergency stop confirmation dialog"""
        try:
            dialog = ConfirmationDialog(
                title="🚨 EMERGENCY STOP ALL BOTS",
                message="This will immediately stop ALL active trading bots.",
                warning="⚠️ This action cannot be undone and may result in open positions!"
            )
            
            # Mount dialog as overlay
            await self.mount(dialog)
            
            # Set up dialog message handlers
            dialog.message_handlers = {
                ConfirmationDialog.DialogCancelled: self._on_emergency_stop_cancelled,
                ConfirmationDialog.DialogConfirmed: self._on_emergency_stop_confirmed
            }
            
        except Exception as e:
            self.logger.error(f"Failed to show emergency stop confirmation: {e}")
    
    async def _show_emergency_pause_confirmation(self) -> None:
        """Show emergency pause confirmation dialog"""
        try:
            dialog = ConfirmationDialog(
                title="⚠️ EMERGENCY PAUSE ALL BOTS",
                message="This will immediately pause ALL active trading bots.",
                warning="Bots will stop trading but positions will remain open."
            )
            
            # Mount dialog as overlay
            await self.mount(dialog)
            
            # Set up dialog message handlers
            dialog.message_handlers = {
                ConfirmationDialog.DialogCancelled: self._on_emergency_pause_cancelled,
                ConfirmationDialog.DialogConfirmed: self._on_emergency_pause_confirmed
            }
            
        except Exception as e:
            self.logger.error(f"Failed to show emergency pause confirmation: {e}")
    
    async def _on_wizard_cancelled(self, message) -> None:
        """Handle wizard cancellation"""
        # Remove wizard overlay
        wizard = self.query_one(BotDeploymentWizard)
        await wizard.remove()
    
    async def _on_bot_deployed(self, message: BotDeploymentWizard.BotDeployed) -> None:
        """Handle successful bot deployment"""
        # Remove wizard overlay
        wizard = self.query_one(BotDeploymentWizard)
        await wizard.remove()
        
        # Refresh bot list to show new bot
        await self.refresh_data()
        
        bot_name = message.bot_config.get("name", "Unknown")
        self.logger.info(f"Bot deployed successfully: {bot_name}")
    
    async def _on_wizard_error(self, message: BotDeploymentWizard.WizardError) -> None:
        """Handle wizard error"""
        self.logger.error(f"Deployment wizard error: {message.error_message}")
        # Keep wizard open to allow user to fix the error
    
    async def _on_emergency_stop_cancelled(self, message) -> None:
        """Handle emergency stop cancellation"""
        dialog = self.query_one(ConfirmationDialog)
        await dialog.remove()
    
    async def _on_emergency_stop_confirmed(self, message) -> None:
        """Handle emergency stop confirmation"""
        dialog = self.query_one(ConfirmationDialog)
        await dialog.remove()
        
        # Execute emergency stop
        await self.bot_actions_panel.execute_emergency_stop()
    
    async def _on_emergency_pause_cancelled(self, message) -> None:
        """Handle emergency pause cancellation"""
        dialog = self.query_one(ConfirmationDialog)
        await dialog.remove()
    
    async def _on_emergency_pause_confirmed(self, message) -> None:
        """Handle emergency pause confirmation"""
        dialog = self.query_one(ConfirmationDialog)
        await dialog.remove()
        
        # Execute emergency pause
        await self.bot_actions_panel.execute_emergency_pause()