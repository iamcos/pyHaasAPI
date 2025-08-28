"""
Dashboard View

Main dashboard with system overview and quick actions.
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Static, Label, Button, ProgressBar
from textual.reactive import reactive
from textual.timer import Timer

from mcp_tui_client.ui.components.panels import StatusPanel, DataPanel
from mcp_tui_client.ui.components.indicators import (
    StatusIndicator, IndicatorStatus, ConnectionIndicator, 
    PerformanceIndicator, LoadingIndicator
)
from mcp_tui_client.ui.components.system_status import SystemStatusDashboard
from mcp_tui_client.ui.components.performance_monitoring import PerformanceChartPanel
from mcp_tui_client.services.mcp_client import MCPClientService


class SystemStatusPanel(StatusPanel):
    """Enhanced panel showing system status and connectivity with real-time monitoring"""
    
    def __init__(self, **kwargs):
        # Initialize attributes first
        self.mcp_client: Optional[MCPClientService] = None
        self.update_timer: Optional[Timer] = None
        self.system_metrics = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "memory_used_gb": 0.0,
            "memory_total_gb": 0.0,
            "disk_percent": 0.0,
            "network_sent_mb": 0.0,
            "network_recv_mb": 0.0
        }
        self.last_network_stats = None
        self.connection_health = {
            "mcp_connected": False,
            "haas_connected": False,
            "last_mcp_check": None,
            "last_haas_check": None,
            "mcp_response_time": 0.0,
            "haas_response_time": 0.0
        }
        
        # Call parent constructor
        super().__init__(title="System Status", **kwargs)
    
    def compose(self) -> ComposeResult:
        """Compose system status panel with real-time indicators"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize system monitoring"""
        await self._initialize_status_items()
        # Start periodic updates every 5 seconds
        self.update_timer = self.set_interval(5.0, self._update_system_metrics)
        # Initial update
        await self._update_system_metrics()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for connection monitoring"""
        self.mcp_client = mcp_client
        if mcp_client:
            # Add connection state callback
            mcp_client.add_connection_callback(self._on_mcp_connection_change)
    
    async def _initialize_status_items(self) -> None:
        """Initialize all status items"""
        # Connection status
        self.add_status_item(
            "mcp_connection", 
            "🔗 MCP Server", 
            "Checking...", 
            "neutral"
        )
        self.add_status_item(
            "haas_connection", 
            "🏦 HaasOnline", 
            "Checking...", 
            "neutral"
        )
        
        # System metrics
        self.add_status_item(
            "cpu_usage", 
            "🖥️ CPU Usage", 
            "0%", 
            "normal"
        )
        self.add_status_item(
            "memory_usage", 
            "💾 Memory", 
            "0 GB / 0 GB", 
            "normal"
        )
        self.add_status_item(
            "disk_usage", 
            "💿 Disk Usage", 
            "0%", 
            "normal"
        )
        self.add_status_item(
            "network_activity", 
            "🌐 Network", 
            "0 MB/s ↑↓", 
            "normal"
        )
        
        # Response times
        self.add_status_item(
            "mcp_response_time", 
            "⚡ MCP Response", 
            "0ms", 
            "normal"
        )
        self.add_status_item(
            "system_uptime", 
            "⏱️ Uptime", 
            "0s", 
            "normal"
        )
    
    async def _update_system_metrics(self) -> None:
        """Update all system metrics"""
        try:
            # Update system metrics
            await self._update_cpu_usage()
            await self._update_memory_usage()
            await self._update_disk_usage()
            await self._update_network_activity()
            await self._update_uptime()
            
            # Update connection status
            await self._check_connections()
            
        except Exception as e:
            self.set_status("error", f"Metrics update failed: {str(e)}")
    
    async def _update_cpu_usage(self) -> None:
        """Update CPU usage metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            self.system_metrics["cpu_percent"] = cpu_percent
            
            # Determine status based on CPU usage
            if cpu_percent > 90:
                status = "error"
            elif cpu_percent > 70:
                status = "warning"
            else:
                status = "normal"
            
            self.add_status_item(
                "cpu_usage", 
                "🖥️ CPU Usage", 
                f"{cpu_percent:.1f}%", 
                status
            )
        except Exception as e:
            self.add_status_item(
                "cpu_usage", 
                "🖥️ CPU Usage", 
                "Error", 
                "error"
            )
    
    async def _update_memory_usage(self) -> None:
        """Update memory usage metrics"""
        try:
            memory = psutil.virtual_memory()
            used_gb = memory.used / (1024**3)
            total_gb = memory.total / (1024**3)
            percent = memory.percent
            
            self.system_metrics["memory_percent"] = percent
            self.system_metrics["memory_used_gb"] = used_gb
            self.system_metrics["memory_total_gb"] = total_gb
            
            # Determine status based on memory usage
            if percent > 90:
                status = "error"
            elif percent > 80:
                status = "warning"
            else:
                status = "normal"
            
            self.add_status_item(
                "memory_usage", 
                "💾 Memory", 
                f"{used_gb:.1f}GB / {total_gb:.1f}GB ({percent:.1f}%)", 
                status
            )
        except Exception as e:
            self.add_status_item(
                "memory_usage", 
                "💾 Memory", 
                "Error", 
                "error"
            )
    
    async def _update_disk_usage(self) -> None:
        """Update disk usage metrics"""
        try:
            disk = psutil.disk_usage('/')
            percent = (disk.used / disk.total) * 100
            self.system_metrics["disk_percent"] = percent
            
            # Determine status based on disk usage
            if percent > 95:
                status = "error"
            elif percent > 85:
                status = "warning"
            else:
                status = "normal"
            
            self.add_status_item(
                "disk_usage", 
                "💿 Disk Usage", 
                f"{percent:.1f}%", 
                status
            )
        except Exception as e:
            self.add_status_item(
                "disk_usage", 
                "💿 Disk Usage", 
                "Error", 
                "error"
            )
    
    async def _update_network_activity(self) -> None:
        """Update network activity metrics"""
        try:
            current_stats = psutil.net_io_counters()
            
            if self.last_network_stats:
                # Calculate rates (bytes per second)
                time_diff = 5.0  # Update interval
                sent_rate = (current_stats.bytes_sent - self.last_network_stats.bytes_sent) / time_diff
                recv_rate = (current_stats.bytes_recv - self.last_network_stats.bytes_recv) / time_diff
                
                # Convert to MB/s
                sent_mb_s = sent_rate / (1024**2)
                recv_mb_s = recv_rate / (1024**2)
                
                self.system_metrics["network_sent_mb"] = sent_mb_s
                self.system_metrics["network_recv_mb"] = recv_mb_s
                
                # Determine status based on network activity
                total_activity = sent_mb_s + recv_mb_s
                if total_activity > 100:  # > 100 MB/s
                    status = "warning"
                else:
                    status = "normal"
                
                self.add_status_item(
                    "network_activity", 
                    "🌐 Network", 
                    f"↑{sent_mb_s:.1f} ↓{recv_mb_s:.1f} MB/s", 
                    status
                )
            else:
                self.add_status_item(
                    "network_activity", 
                    "🌐 Network", 
                    "Measuring...", 
                    "neutral"
                )
            
            self.last_network_stats = current_stats
            
        except Exception as e:
            self.add_status_item(
                "network_activity", 
                "🌐 Network", 
                "Error", 
                "error"
            )
    
    async def _update_uptime(self) -> None:
        """Update system uptime"""
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_delta = timedelta(seconds=uptime_seconds)
            
            # Format uptime
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                uptime_str = f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                uptime_str = f"{hours}h {minutes}m"
            else:
                uptime_str = f"{minutes}m"
            
            self.add_status_item(
                "system_uptime", 
                "⏱️ Uptime", 
                uptime_str, 
                "normal"
            )
        except Exception as e:
            self.add_status_item(
                "system_uptime", 
                "⏱️ Uptime", 
                "Error", 
                "error"
            )
    
    async def _check_connections(self) -> None:
        """Check MCP and HaasOnline connections"""
        # Check MCP connection
        await self._check_mcp_connection()
        
        # Check HaasOnline connection (through MCP)
        await self._check_haas_connection()
    
    async def _check_mcp_connection(self) -> None:
        """Check MCP server connection"""
        if not self.mcp_client:
            self.add_status_item(
                "mcp_connection", 
                "🔗 MCP Server", 
                "Not configured", 
                "error"
            )
            return
        
        try:
            start_time = time.time()
            
            if self.mcp_client.is_connected:
                # Test with health check
                await self.mcp_client.health_check()
                response_time = (time.time() - start_time) * 1000  # ms
                
                self.connection_health["mcp_connected"] = True
                self.connection_health["mcp_response_time"] = response_time
                self.connection_health["last_mcp_check"] = datetime.now()
                
                self.add_status_item(
                    "mcp_connection", 
                    "🔗 MCP Server", 
                    "Connected", 
                    "normal"
                )
                self.add_status_item(
                    "mcp_response_time", 
                    "⚡ MCP Response", 
                    f"{response_time:.0f}ms", 
                    "normal" if response_time < 1000 else "warning"
                )
            else:
                self.connection_health["mcp_connected"] = False
                self.add_status_item(
                    "mcp_connection", 
                    "🔗 MCP Server", 
                    "Disconnected", 
                    "error"
                )
                self.add_status_item(
                    "mcp_response_time", 
                    "⚡ MCP Response", 
                    "N/A", 
                    "error"
                )
                
        except Exception as e:
            self.connection_health["mcp_connected"] = False
            self.add_status_item(
                "mcp_connection", 
                "🔗 MCP Server", 
                f"Error: {str(e)[:20]}", 
                "error"
            )
            self.add_status_item(
                "mcp_response_time", 
                "⚡ MCP Response", 
                "Error", 
                "error"
            )
    
    async def _check_haas_connection(self) -> None:
        """Check HaasOnline connection through MCP"""
        if not self.mcp_client or not self.mcp_client.is_connected:
            self.add_status_item(
                "haas_connection", 
                "🏦 HaasOnline", 
                "MCP Disconnected", 
                "error"
            )
            return
        
        try:
            start_time = time.time()
            
            # Test HaasOnline connection through MCP
            haas_status = await self.mcp_client.get_haas_status()
            response_time = (time.time() - start_time) * 1000  # ms
            
            if haas_status and haas_status.get("connected", False):
                self.connection_health["haas_connected"] = True
                self.connection_health["haas_response_time"] = response_time
                self.connection_health["last_haas_check"] = datetime.now()
                
                self.add_status_item(
                    "haas_connection", 
                    "🏦 HaasOnline", 
                    "Connected", 
                    "normal"
                )
            else:
                self.connection_health["haas_connected"] = False
                self.add_status_item(
                    "haas_connection", 
                    "🏦 HaasOnline", 
                    "Disconnected", 
                    "error"
                )
                
        except Exception as e:
            self.connection_health["haas_connected"] = False
            self.add_status_item(
                "haas_connection", 
                "🏦 HaasOnline", 
                f"Error: {str(e)[:20]}", 
                "error"
            )
    
    def _on_mcp_connection_change(self, new_state) -> None:
        """Handle MCP connection state changes"""
        from mcp_tui_client.services.mcp_client import ConnectionState
        
        if new_state == ConnectionState.CONNECTED:
            self.add_status_item(
                "mcp_connection", 
                "🔗 MCP Server", 
                "Connected", 
                "normal"
            )
        elif new_state == ConnectionState.CONNECTING:
            self.add_status_item(
                "mcp_connection", 
                "🔗 MCP Server", 
                "Connecting...", 
                "neutral"
            )
        elif new_state == ConnectionState.RECONNECTING:
            self.add_status_item(
                "mcp_connection", 
                "🔗 MCP Server", 
                "Reconnecting...", 
                "warning"
            )
        else:
            self.add_status_item(
                "mcp_connection", 
                "🔗 MCP Server", 
                "Disconnected", 
                "error"
            )
    
    def get_system_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive system diagnostics"""
        return {
            "system_metrics": self.system_metrics.copy(),
            "connection_health": self.connection_health.copy(),
            "timestamp": datetime.now().isoformat(),
            "mcp_client_info": self.mcp_client.connection_info if self.mcp_client else None
        }
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "system_health": "unknown",
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check system resources
            if self.system_metrics["cpu_percent"] > 90:
                diagnostics["issues"].append("High CPU usage detected")
                diagnostics["recommendations"].append("Consider closing unnecessary applications")
            
            if self.system_metrics["memory_percent"] > 90:
                diagnostics["issues"].append("High memory usage detected")
                diagnostics["recommendations"].append("Consider restarting the application")
            
            if self.system_metrics["disk_percent"] > 95:
                diagnostics["issues"].append("Low disk space")
                diagnostics["recommendations"].append("Free up disk space")
            
            # Check connections
            if not self.connection_health["mcp_connected"]:
                diagnostics["issues"].append("MCP server connection failed")
                diagnostics["recommendations"].append("Check MCP server status and network connectivity")
            
            if not self.connection_health["haas_connected"]:
                diagnostics["issues"].append("HaasOnline connection failed")
                diagnostics["recommendations"].append("Check HaasOnline API credentials and status")
            
            # Determine overall health
            if not diagnostics["issues"]:
                diagnostics["system_health"] = "healthy"
            elif len(diagnostics["issues"]) <= 2:
                diagnostics["system_health"] = "warning"
            else:
                diagnostics["system_health"] = "critical"
            
            return diagnostics
            
        except Exception as e:
            diagnostics["system_health"] = "error"
            diagnostics["issues"].append(f"Diagnostics failed: {str(e)}")
            return diagnostics
    
    def on_unmount(self) -> None:
        """Clean up timers and callbacks"""
        if self.update_timer:
            self.update_timer.stop()
        
        if self.mcp_client:
            self.mcp_client.remove_connection_callback(self._on_mcp_connection_change)


class QuickActionsPanel(DataPanel):
    """Enhanced panel with quick action buttons and common operations"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Quick Actions", **kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.action_callbacks = {}
    
    def compose(self) -> ComposeResult:
        """Compose quick actions panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize quick actions"""
        await self._setup_quick_actions()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for actions"""
        self.mcp_client = mcp_client
    
    def set_action_callback(self, action: str, callback: callable) -> None:
        """Set callback for specific action"""
        self.action_callbacks[action] = callback
    
    async def _setup_quick_actions(self) -> None:
        """Set up quick action buttons and shortcuts"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            # Create action buttons container
            actions_container = Vertical()
            
            # Navigation shortcuts
            actions_container.mount(Static("🚀 Navigation", classes="action-section-title"))
            actions_container.mount(Static("  F2 - Bot Management", classes="action-item"))
            actions_container.mount(Static("  F3 - Lab Management", classes="action-item"))
            actions_container.mount(Static("  F4 - Script Editor", classes="action-item"))
            actions_container.mount(Static("  F5 - Workflow Designer", classes="action-item"))
            actions_container.mount(Static("  F6 - Market Data", classes="action-item"))
            actions_container.mount(Static("  F7 - Analytics", classes="action-item"))
            
            # Quick actions
            actions_container.mount(Static("⚡ Quick Actions", classes="action-section-title"))
            
            # Create action buttons
            button_container = Horizontal(classes="action-buttons")
            
            refresh_btn = Button("Refresh All", id="refresh-all-btn", variant="primary")
            emergency_btn = Button("Emergency Stop", id="emergency-stop-btn", variant="error")
            backup_btn = Button("Backup Config", id="backup-config-btn", variant="default")
            
            button_container.mount(refresh_btn)
            button_container.mount(emergency_btn)
            button_container.mount(backup_btn)
            
            actions_container.mount(button_container)
            
            # System shortcuts
            actions_container.mount(Static("🔧 System", classes="action-section-title"))
            actions_container.mount(Static("  Ctrl+R - Refresh Dashboard", classes="action-item"))
            actions_container.mount(Static("  Ctrl+Q - Quit Application", classes="action-item"))
            actions_container.mount(Static("  Ctrl+H - Help", classes="action-item"))
            
            content_container.mount(actions_container)
            
        except Exception as e:
            self.set_status("error", f"Setup failed: {str(e)}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        
        try:
            if button_id == "refresh-all-btn":
                await self._handle_refresh_all()
            elif button_id == "emergency-stop-btn":
                await self._handle_emergency_stop()
            elif button_id == "backup-config-btn":
                await self._handle_backup_config()
        except Exception as e:
            self.set_status("error", f"Action failed: {str(e)}")
    
    async def _handle_refresh_all(self) -> None:
        """Handle refresh all action"""
        if "refresh_all" in self.action_callbacks:
            await self.action_callbacks["refresh_all"]()
        else:
            # Default refresh behavior
            self.set_status("success", "Refreshing all data...")
    
    async def _handle_emergency_stop(self) -> None:
        """Handle emergency stop action"""
        if not self.mcp_client:
            self.set_status("error", "MCP client not available")
            return
        
        try:
            # Get all active bots and stop them
            bots = await self.mcp_client.get_all_bots()
            active_bots = [bot for bot in bots if bot.get("is_active", False)]
            
            if not active_bots:
                self.set_status("info", "No active bots to stop")
                return
            
            # Stop all active bots
            for bot in active_bots:
                await self.mcp_client.deactivate_bot(bot["bot_id"])
            
            self.set_status("success", f"Emergency stop: {len(active_bots)} bots stopped")
            
        except Exception as e:
            self.set_status("error", f"Emergency stop failed: {str(e)}")
    
    async def _handle_backup_config(self) -> None:
        """Handle backup configuration action"""
        if "backup_config" in self.action_callbacks:
            await self.action_callbacks["backup_config"]()
        else:
            self.set_status("info", "Backup feature not implemented")


class ActiveBotsPanel(DataPanel):
    """Enhanced panel showing active bots summary with real-time updates"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Active Bots", auto_refresh=True, refresh_interval=30, **kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.active_bots = []
        self.bot_performance = {}
    
    def compose(self) -> ComposeResult:
        """Compose active bots panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize active bots monitoring"""
        if self.mcp_client:
            self.set_data_source(self._fetch_active_bots_data)
            await self.refresh_data()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for bot data"""
        self.mcp_client = mcp_client
        if mcp_client:
            self.set_data_source(self._fetch_active_bots_data)
    
    async def _fetch_active_bots_data(self) -> Dict[str, Any]:
        """Fetch active bots data from MCP server"""
        if not self.mcp_client or not self.mcp_client.is_connected:
            raise Exception("MCP client not connected")
        
        try:
            # Get all bots
            all_bots = await self.mcp_client.get_all_bots()
            
            # Filter active bots
            active_bots = [bot for bot in all_bots if bot.get("is_active", False)]
            
            # Get performance data for each active bot
            bot_performance = {}
            for bot in active_bots:
                try:
                    bot_details = await self.mcp_client.get_bot_details(bot["bot_id"])
                    bot_performance[bot["bot_id"]] = {
                        "name": bot.get("name", "Unknown"),
                        "performance_24h": bot_details.get("performance_24h", 0.0),
                        "total_trades": bot_details.get("total_trades", 0),
                        "win_rate": bot_details.get("win_rate", 0.0),
                        "current_position": bot_details.get("current_position", "None"),
                        "last_trade": bot_details.get("last_trade_time", "Never"),
                        "status": bot_details.get("status", "Unknown")
                    }
                except Exception as e:
                    # If we can't get details, use basic info
                    bot_performance[bot["bot_id"]] = {
                        "name": bot.get("name", "Unknown"),
                        "performance_24h": 0.0,
                        "total_trades": 0,
                        "win_rate": 0.0,
                        "current_position": "Unknown",
                        "last_trade": "Unknown",
                        "status": "Error"
                    }
            
            self.active_bots = active_bots
            self.bot_performance = bot_performance
            
            return {
                "active_bots": active_bots,
                "bot_performance": bot_performance,
                "total_active": len(active_bots)
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch bot data: {str(e)}")
    
    async def _display_data(self, data: Dict[str, Any]) -> None:
        """Display active bots data"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            active_bots = data.get("active_bots", [])
            bot_performance = data.get("bot_performance", {})
            total_active = data.get("total_active", 0)
            
            # Update title with count
            self.title = f"Active Bots ({total_active})"
            
            bots_container = Vertical()
            
            if not active_bots:
                bots_container.mount(Static("No active bots", classes="no-data"))
            else:
                # Sort bots by performance
                sorted_bots = sorted(
                    active_bots, 
                    key=lambda b: bot_performance.get(b["bot_id"], {}).get("performance_24h", 0),
                    reverse=True
                )
                
                for bot in sorted_bots[:5]:  # Show top 5 bots
                    bot_id = bot["bot_id"]
                    perf_data = bot_performance.get(bot_id, {})
                    
                    name = perf_data.get("name", "Unknown")[:20]  # Truncate long names
                    performance = perf_data.get("performance_24h", 0.0)
                    win_rate = perf_data.get("win_rate", 0.0)
                    trades = perf_data.get("total_trades", 0)
                    status = perf_data.get("status", "Unknown")
                    
                    # Format performance with color coding
                    if performance > 0:
                        perf_icon = "📈"
                        perf_color = "green"
                    elif performance < 0:
                        perf_icon = "📉"
                        perf_color = "red"
                    else:
                        perf_icon = "➖"
                        perf_color = "yellow"
                    
                    # Create bot summary line
                    bot_line = f"{perf_icon} {name}: {performance:+.2f}% | WR: {win_rate:.1f}% | Trades: {trades}"
                    
                    bot_widget = Static(bot_line, classes=f"bot-item bot-{perf_color}")
                    bots_container.mount(bot_widget)
                
                # Show summary if more than 5 bots
                if len(active_bots) > 5:
                    remaining = len(active_bots) - 5
                    summary_widget = Static(f"... and {remaining} more bots", classes="bot-summary")
                    bots_container.mount(summary_widget)
                
                # Overall performance summary
                total_performance = sum(
                    perf.get("performance_24h", 0) for perf in bot_performance.values()
                )
                avg_performance = total_performance / len(active_bots) if active_bots else 0
                
                summary_line = f"Total Performance: {total_performance:+.2f}% | Avg: {avg_performance:+.2f}%"
                summary_widget = Static(summary_line, classes="performance-summary")
                bots_container.mount(summary_widget)
            
            content_container.mount(bots_container)
            
        except Exception as e:
            self.set_status("error", f"Display failed: {str(e)}")


class RunningLabsPanel(DataPanel):
    """Enhanced panel showing running labs with current backtest status"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Running Labs", auto_refresh=True, refresh_interval=15, **kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.running_labs = []
        self.lab_status = {}
    
    def compose(self) -> ComposeResult:
        """Compose running labs panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize running labs monitoring"""
        if self.mcp_client:
            self.set_data_source(self._fetch_running_labs_data)
            await self.refresh_data()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for lab data"""
        self.mcp_client = mcp_client
        if mcp_client:
            self.set_data_source(self._fetch_running_labs_data)
    
    async def _fetch_running_labs_data(self) -> Dict[str, Any]:
        """Fetch running labs data from MCP server"""
        if not self.mcp_client or not self.mcp_client.is_connected:
            raise Exception("MCP client not connected")
        
        try:
            # Get all labs
            all_labs = await self.mcp_client.get_all_labs()
            
            # Filter running labs
            running_labs = [lab for lab in all_labs if lab.get("status") in ["running", "executing", "optimizing"]]
            
            # Get detailed status for each running lab
            lab_status = {}
            for lab in running_labs:
                try:
                    lab_details = await self.mcp_client.get_lab_details(lab["lab_id"])
                    lab_status[lab["lab_id"]] = {
                        "name": lab.get("name", "Unknown"),
                        "status": lab_details.get("status", "Unknown"),
                        "progress": lab_details.get("progress", 0),
                        "estimated_completion": lab_details.get("estimated_completion", "Unknown"),
                        "current_period": lab_details.get("current_period", "Unknown"),
                        "total_periods": lab_details.get("total_periods", 0),
                        "script_name": lab_details.get("script_name", "Unknown"),
                        "trading_pair": lab_details.get("trading_pair", "Unknown")
                    }
                except Exception as e:
                    # If we can't get details, use basic info
                    lab_status[lab["lab_id"]] = {
                        "name": lab.get("name", "Unknown"),
                        "status": lab.get("status", "Unknown"),
                        "progress": 0,
                        "estimated_completion": "Unknown",
                        "current_period": "Unknown",
                        "total_periods": 0,
                        "script_name": "Unknown",
                        "trading_pair": "Unknown"
                    }
            
            self.running_labs = running_labs
            self.lab_status = lab_status
            
            return {
                "running_labs": running_labs,
                "lab_status": lab_status,
                "total_running": len(running_labs)
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch lab data: {str(e)}")
    
    async def _display_data(self, data: Dict[str, Any]) -> None:
        """Display running labs data"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            running_labs = data.get("running_labs", [])
            lab_status = data.get("lab_status", {})
            total_running = data.get("total_running", 0)
            
            # Update title with count
            self.title = f"Running Labs ({total_running})"
            
            labs_container = Vertical()
            
            if not running_labs:
                labs_container.mount(Static("No running labs", classes="no-data"))
            else:
                # Sort labs by progress (running first, then by progress)
                sorted_labs = sorted(
                    running_labs,
                    key=lambda l: (
                        0 if lab_status.get(l["lab_id"], {}).get("status") == "running" else 1,
                        -lab_status.get(l["lab_id"], {}).get("progress", 0)
                    )
                )
                
                for lab in sorted_labs[:5]:  # Show top 5 labs
                    lab_id = lab["lab_id"]
                    status_data = lab_status.get(lab_id, {})
                    
                    name = status_data.get("name", "Unknown")[:20]  # Truncate long names
                    status = status_data.get("status", "Unknown")
                    progress = status_data.get("progress", 0)
                    trading_pair = status_data.get("trading_pair", "Unknown")
                    
                    # Format status with appropriate icon
                    if status == "running":
                        status_icon = "🔄"
                        status_color = "blue"
                    elif status == "optimizing":
                        status_icon = "⚡"
                        status_color = "yellow"
                    elif status == "executing":
                        status_icon = "▶️"
                        status_color = "green"
                    else:
                        status_icon = "❓"
                        status_color = "gray"
                    
                    # Create lab summary line
                    lab_line = f"{status_icon} {name} ({trading_pair}): {progress:.1f}% - {status.title()}"
                    
                    lab_widget = Static(lab_line, classes=f"lab-item lab-{status_color}")
                    labs_container.mount(lab_widget)
                    
                    # Add progress bar for running labs
                    if progress > 0:
                        progress_bar = ProgressBar(total=100, show_eta=False)
                        progress_bar.advance(progress)
                        labs_container.mount(progress_bar)
                
                # Show summary if more than 5 labs
                if len(running_labs) > 5:
                    remaining = len(running_labs) - 5
                    summary_widget = Static(f"... and {remaining} more labs", classes="lab-summary")
                    labs_container.mount(summary_widget)
                
                # Overall progress summary
                total_progress = sum(
                    status.get("progress", 0) for status in lab_status.values()
                )
                avg_progress = total_progress / len(running_labs) if running_labs else 0
                
                summary_line = f"Average Progress: {avg_progress:.1f}%"
                summary_widget = Static(summary_line, classes="progress-summary")
                labs_container.mount(summary_widget)
            
            content_container.mount(labs_container)
            
        except Exception as e:
            self.set_status("error", f"Display failed: {str(e)}")


class RecentAlertsPanel(DataPanel):
    """Enhanced panel showing recent alerts and important notifications"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Recent Alerts", auto_refresh=True, refresh_interval=10, **kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.recent_alerts = []
        self.alert_history = []
        self.max_alerts = 10
    
    def compose(self) -> ComposeResult:
        """Compose recent alerts panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize alerts monitoring"""
        if self.mcp_client:
            self.set_data_source(self._fetch_alerts_data)
            await self.refresh_data()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for alerts data"""
        self.mcp_client = mcp_client
        if mcp_client:
            self.set_data_source(self._fetch_alerts_data)
    
    async def _fetch_alerts_data(self) -> Dict[str, Any]:
        """Fetch recent alerts data from MCP server"""
        if not self.mcp_client or not self.mcp_client.is_connected:
            raise Exception("MCP client not connected")
        
        try:
            # Get system alerts and notifications
            alerts = []
            
            # Check for bot alerts
            try:
                bot_alerts = await self.mcp_client.get_bot_alerts()
                for alert in bot_alerts:
                    alerts.append({
                        "type": "bot",
                        "severity": alert.get("severity", "info"),
                        "message": alert.get("message", "Bot alert"),
                        "timestamp": alert.get("timestamp", datetime.now()),
                        "source": alert.get("bot_name", "Unknown Bot")
                    })
            except:
                pass
            
            # Check for lab alerts
            try:
                lab_alerts = await self.mcp_client.get_lab_alerts()
                for alert in lab_alerts:
                    alerts.append({
                        "type": "lab",
                        "severity": alert.get("severity", "info"),
                        "message": alert.get("message", "Lab alert"),
                        "timestamp": alert.get("timestamp", datetime.now()),
                        "source": alert.get("lab_name", "Unknown Lab")
                    })
            except:
                pass
            
            # Check for system alerts
            try:
                system_alerts = await self.mcp_client.get_system_alerts()
                for alert in system_alerts:
                    alerts.append({
                        "type": "system",
                        "severity": alert.get("severity", "info"),
                        "message": alert.get("message", "System alert"),
                        "timestamp": alert.get("timestamp", datetime.now()),
                        "source": "System"
                    })
            except:
                pass
            
            # If no alerts from server, create some mock alerts for demonstration
            if not alerts:
                alerts = [
                    {
                        "type": "system",
                        "severity": "info",
                        "message": "System monitoring active",
                        "timestamp": datetime.now(),
                        "source": "System"
                    }
                ]
            
            # Sort alerts by timestamp (newest first)
            alerts.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            
            # Keep only recent alerts
            recent_alerts = alerts[:self.max_alerts]
            
            self.recent_alerts = recent_alerts
            
            return {
                "recent_alerts": recent_alerts,
                "total_alerts": len(alerts),
                "critical_count": len([a for a in alerts if a.get("severity") == "critical"]),
                "warning_count": len([a for a in alerts if a.get("severity") == "warning"]),
                "info_count": len([a for a in alerts if a.get("severity") == "info"])
            }
            
        except Exception as e:
            raise Exception(f"Failed to fetch alerts data: {str(e)}")
    
    async def _display_data(self, data: Dict[str, Any]) -> None:
        """Display recent alerts data"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            recent_alerts = data.get("recent_alerts", [])
            critical_count = data.get("critical_count", 0)
            warning_count = data.get("warning_count", 0)
            info_count = data.get("info_count", 0)
            
            # Update title with counts
            self.title = f"Recent Alerts ({critical_count}🔴 {warning_count}🟡 {info_count}🔵)"
            
            alerts_container = Vertical()
            
            if not recent_alerts:
                alerts_container.mount(Static("No recent alerts", classes="no-data"))
            else:
                for alert in recent_alerts[:7]:  # Show top 7 alerts
                    severity = alert.get("severity", "info")
                    message = alert.get("message", "Unknown alert")[:50]  # Truncate long messages
                    source = alert.get("source", "Unknown")
                    timestamp = alert.get("timestamp", datetime.now())
                    
                    # Format severity with appropriate icon and color
                    if severity == "critical":
                        severity_icon = "🔴"
                        severity_color = "red"
                    elif severity == "warning":
                        severity_icon = "🟡"
                        severity_color = "yellow"
                    elif severity == "error":
                        severity_icon = "🔴"
                        severity_color = "red"
                    else:
                        severity_icon = "🔵"
                        severity_color = "blue"
                    
                    # Format timestamp
                    if isinstance(timestamp, datetime):
                        time_str = timestamp.strftime("%H:%M:%S")
                    else:
                        time_str = "Unknown"
                    
                    # Create alert line
                    alert_line = f"{severity_icon} [{time_str}] {source}: {message}"
                    
                    alert_widget = Static(alert_line, classes=f"alert-item alert-{severity_color}")
                    alerts_container.mount(alert_widget)
                
                # Show summary
                if len(recent_alerts) > 7:
                    remaining = len(recent_alerts) - 7
                    summary_widget = Static(f"... and {remaining} more alerts", classes="alert-summary")
                    alerts_container.mount(summary_widget)
            
            content_container.mount(alerts_container)
            
        except Exception as e:
            self.set_status("error", f"Display failed: {str(e)}")
    
    def add_custom_alert(self, alert_type: str, severity: str, message: str, source: str = "User") -> None:
        """Add a custom alert to the panel"""
        custom_alert = {
            "type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now(),
            "source": source
        }
        
        self.recent_alerts.insert(0, custom_alert)
        
        # Keep only max alerts
        if len(self.recent_alerts) > self.max_alerts:
            self.recent_alerts = self.recent_alerts[:self.max_alerts]
        
        # Refresh display
        asyncio.create_task(self.refresh_data())
    
    async def _calculate_portfolio_performance(self) -> List[float]:
        """Calculate portfolio performance over time"""
        try:
            # This would typically fetch historical performance data
            # For now, we'll simulate based on current bot performance
            if not self.performance_history:
                return [0.0]
            
            # Extract performance values from history
            performance_values = []
            for data in self.performance_history[-30:]:  # Last 30 data points
                bot_perf = data.get("bot_performance", {})
                total_perf = bot_perf.get("total_performance", 0.0)
                performance_values.append(total_perf)
            
            return performance_values if performance_values else [0.0]
            
        except Exception:
            return [0.0]
    
    async def _calculate_system_health(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall system health score"""
        try:
            health_score = 100.0
            issues = []
            recommendations = []
            
            # Check resource usage
            resources = performance_data.get("resource_usage", {})
            
            cpu_percent = resources.get("cpu_percent", 0)
            if cpu_percent > 90:
                health_score -= 20
                issues.append("High CPU usage")
                recommendations.append("Consider reducing bot count or optimizing scripts")
            elif cpu_percent > 70:
                health_score -= 10
                issues.append("Moderate CPU usage")
            
            memory_percent = resources.get("memory_percent", 0)
            if memory_percent > 90:
                health_score -= 20
                issues.append("High memory usage")
                recommendations.append("Restart application or reduce memory-intensive operations")
            elif memory_percent > 80:
                health_score -= 10
                issues.append("Moderate memory usage")
            
            disk_percent = resources.get("disk_percent", 0)
            if disk_percent > 95:
                health_score -= 15
                issues.append("Low disk space")
                recommendations.append("Free up disk space")
            
            # Check bot performance
            bot_perf = performance_data.get("bot_performance", {})
            if not bot_perf.get("error"):
                avg_performance = bot_perf.get("average_performance", 0)
                if avg_performance < -5:
                    health_score -= 15
                    issues.append("Poor bot performance")
                    recommendations.append("Review bot strategies and risk management")
                
                profitability_rate = bot_perf.get("profitability_rate", 0)
                if profitability_rate < 0.3:
                    health_score -= 10
                    issues.append("Low profitability rate")
                    recommendations.append("Optimize bot parameters or disable underperforming bots")
            
            # Check MCP connection
            if not self.mcp_client or not self.mcp_client.is_connected:
                health_score -= 25
                issues.append("MCP server disconnected")
                recommendations.append("Check MCP server status and network connectivity")
            
            # Determine health status
            if health_score >= 90:
                status = "excellent"
            elif health_score >= 75:
                status = "good"
            elif health_score >= 60:
                status = "fair"
            elif health_score >= 40:
                status = "poor"
            else:
                status = "critical"
            
            return {
                "score": max(0, health_score),
                "status": status,
                "issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {
                "score": 0,
                "status": "error",
                "issues": [f"Health calculation failed: {str(e)}"],
                "recommendations": ["Check system status"]
            }
    
    async def _display_data(self, data: Dict[str, Any]) -> None:
        """Display performance data with ASCII charts"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            perf_container = Vertical()
            
            # System Health Summary
            health = data.get("system_health", {})
            health_score = health.get("score", 0)
            health_status = health.get("status", "unknown")
            
            health_line = f"🏥 System Health: {health_score:.1f}/100 ({health_status.upper()})"
            perf_container.mount(Static(health_line, classes=f"health-{health_status}"))
            
            # Resource Usage Chart
            resources = data.get("resource_usage", {})
            if not resources.get("error"):
                perf_container.mount(Static("📊 Resource Usage:", classes="section-title"))
                
                cpu_chart = self._create_resource_bar("CPU", resources.get("cpu_percent", 0), 100)
                memory_chart = self._create_resource_bar("Memory", resources.get("memory_percent", 0), 100)
                disk_chart = self._create_resource_bar("Disk", resources.get("disk_percent", 0), 100)
                
                perf_container.mount(Static(cpu_chart, classes="resource-bar"))
                perf_container.mount(Static(memory_chart, classes="resource-bar"))
                perf_container.mount(Static(disk_chart, classes="resource-bar"))
            
            # Portfolio Performance Chart
            portfolio_perf = data.get("portfolio_performance", [])
            if portfolio_perf and len(portfolio_perf) > 1:
                perf_container.mount(Static("📈 Portfolio Performance:", classes="section-title"))
                
                chart = self._create_line_chart(portfolio_perf, "Performance %")
                perf_container.mount(Static(chart, classes="performance-chart"))
            
            # Bot Performance Summary
            bot_perf = data.get("bot_performance", {})
            if not bot_perf.get("error"):
                perf_container.mount(Static("🤖 Bot Performance:", classes="section-title"))
                
                total_bots = bot_perf.get("total_bots", 0)
                avg_perf = bot_perf.get("average_performance", 0)
                profitable = bot_perf.get("profitable_bots", 0)
                total_trades = bot_perf.get("total_trades", 0)
                
                bot_summary = f"Bots: {total_bots} | Avg: {avg_perf:+.2f}% | Profitable: {profitable}/{total_bots} | Trades: {total_trades}"
                perf_container.mount(Static(bot_summary, classes="bot-summary"))
            
            # System Issues and Recommendations
            issues = health.get("issues", [])
            recommendations = health.get("recommendations", [])
            
            if issues:
                perf_container.mount(Static("⚠️ Issues:", classes="section-title"))
                for issue in issues[:3]:  # Show top 3 issues
                    perf_container.mount(Static(f"  • {issue}", classes="issue-item"))
            
            if recommendations:
                perf_container.mount(Static("💡 Recommendations:", classes="section-title"))
                for rec in recommendations[:2]:  # Show top 2 recommendations
                    perf_container.mount(Static(f"  • {rec}", classes="recommendation-item"))
            
            content_container.mount(perf_container)
            
        except Exception as e:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            content_container.mount(Static(f"Display error: {str(e)}", classes="error-message"))
    
    def _create_resource_bar(self, name: str, value: float, max_value: float) -> str:
        """Create ASCII resource usage bar"""
        bar_width = 30
        filled_width = int((value / max_value) * bar_width)
        
        # Color coding based on usage
        if value > 90:
            bar_char = "█"
            status = "CRITICAL"
        elif value > 70:
            bar_char = "▓"
            status = "HIGH"
        elif value > 50:
            bar_char = "▒"
            status = "MEDIUM"
        else:
            bar_char = "░"
            status = "LOW"
        
        bar = bar_char * filled_width + "░" * (bar_width - filled_width)
        return f"{name:>6}: [{bar}] {value:5.1f}% {status}"
    
    def _create_line_chart(self, data: List[float], label: str) -> str:
        """Create ASCII line chart"""
        if not data or len(data) < 2:
            return "No data available"
        
        # Normalize data to chart height
        min_val = min(data)
        max_val = max(data)
        
        if max_val == min_val:
            # All values are the same
            mid_line = "─" * len(data)
            return f"{max_val:6.1f} ┤{mid_line}\n{min_val:6.1f} ┤"
        
        range_val = max_val - min_val
        chart_height = 8
        
        # Create chart lines
        chart_lines = []
        for row in range(chart_height):
            line_value = max_val - (row * range_val / (chart_height - 1))
            line = f"{line_value:6.1f} ┤"
            
            for i, value in enumerate(data):
                # Determine if this row should have a point
                normalized_value = (value - min_val) / range_val
                row_threshold = 1 - (row / (chart_height - 1))
                
                if abs(normalized_value - row_threshold) < (1 / chart_height):
                    if i == 0:
                        line += "╭"
                    elif i == len(data) - 1:
                        line += "╮"
                    else:
                        # Check trend
                        if i > 0 and data[i] > data[i-1]:
                            line += "╱"
                        elif i > 0 and data[i] < data[i-1]:
                            line += "╲"
                        else:
                            line += "─"
                else:
                    line += " "
            
            chart_lines.append(line)
        
        # Add time axis
        time_axis = "       ┼" + "─" * (len(data) - 1)
        chart_lines.append(time_axis)
        
        return "\n".join(chart_lines)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.performance_history:
            return {"status": "No data", "health_score": 0}
        
        latest_data = self.performance_history[-1]
        health = latest_data.get("system_health", {})
        
        return {
            "health_score": health.get("score", 0),
            "health_status": health.get("status", "unknown"),
            "issues_count": len(health.get("issues", [])),
            "recommendations_count": len(health.get("recommendations", [])),
            "timestamp": latest_data.get("timestamp", datetime.now()).isoformat()
        }


class MarketOverviewPanel(DataPanel):
    """Enhanced panel with market overview and price monitoring"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Market Overview", auto_refresh=True, refresh_interval=30, **kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.market_data = {}
        self.price_history = {}
        self.watched_pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]
    
    def compose(self) -> ComposeResult:
        """Compose market overview panel"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize market monitoring"""
        if self.mcp_client:
            self.set_data_source(self._fetch_market_data)
            await self.refresh_data()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for market data"""
        self.mcp_client = mcp_client
        if mcp_client:
            self.set_data_source(self._fetch_market_data)
    
    def set_watched_pairs(self, pairs: List[str]) -> None:
        """Set the trading pairs to watch"""
        self.watched_pairs = pairs
    
    async def _fetch_market_data(self) -> Dict[str, Any]:
        """Fetch market data from MCP server"""
        if not self.mcp_client or not self.mcp_client.is_connected:
            # Return simulated data when not connected
            return await self._get_simulated_market_data()
        
        try:
            # Get available markets
            markets = await self.mcp_client.get_all_markets()
            
            market_snapshots = {}
            for market in markets[:10]:  # Limit to first 10 markets
                try:
                    market_tag = market.get("market_tag", "")
                    if market_tag:
                        snapshot = await self.mcp_client.get_market_snapshot(market_tag)
                        market_snapshots[market_tag] = snapshot
                except Exception:
                    continue
            
            # Process market data
            processed_data = await self._process_market_data(market_snapshots)
            
            return {
                "markets": processed_data,
                "total_markets": len(market_snapshots),
                "timestamp": datetime.now(),
                "status": "live"
            }
            
        except Exception as e:
            # Fallback to simulated data
            simulated = await self._get_simulated_market_data()
            simulated["error"] = str(e)
            return simulated
    
    async def _get_simulated_market_data(self) -> Dict[str, Any]:
        """Get simulated market data for testing"""
        import random
        
        simulated_markets = {}
        
        for pair in self.watched_pairs:
            # Generate realistic price data
            base_prices = {
                "BTC/USDT": 43000,
                "ETH/USDT": 2600,
                "BNB/USDT": 310,
                "ADA/USDT": 0.45,
                "SOL/USDT": 95
            }
            
            base_price = base_prices.get(pair, 100)
            
            # Add some random variation
            price_change = random.uniform(-5, 5)  # -5% to +5%
            current_price = base_price * (1 + price_change / 100)
            
            volume_24h = random.uniform(1000000, 10000000)  # Random volume
            
            simulated_markets[pair] = {
                "symbol": pair,
                "price": current_price,
                "price_change_24h": price_change,
                "volume_24h": volume_24h,
                "high_24h": current_price * 1.05,
                "low_24h": current_price * 0.95,
                "market_cap": current_price * random.uniform(10000000, 100000000),
                "last_updated": datetime.now()
            }
        
        return {
            "markets": simulated_markets,
            "total_markets": len(simulated_markets),
            "timestamp": datetime.now(),
            "status": "simulated"
        }
    
    async def _process_market_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw market data into standardized format"""
        processed = {}
        
        for market_tag, snapshot in raw_data.items():
            try:
                # Extract relevant data from snapshot
                # This would depend on the actual structure of market snapshots
                processed[market_tag] = {
                    "symbol": market_tag,
                    "price": snapshot.get("last_price", 0),
                    "price_change_24h": snapshot.get("price_change_24h", 0),
                    "volume_24h": snapshot.get("volume_24h", 0),
                    "high_24h": snapshot.get("high_24h", 0),
                    "low_24h": snapshot.get("low_24h", 0),
                    "bid": snapshot.get("bid", 0),
                    "ask": snapshot.get("ask", 0),
                    "last_updated": datetime.now()
                }
                
                # Store price history
                if market_tag not in self.price_history:
                    self.price_history[market_tag] = []
                
                self.price_history[market_tag].append({
                    "price": processed[market_tag]["price"],
                    "timestamp": datetime.now()
                })
                
                # Keep only last 100 price points
                if len(self.price_history[market_tag]) > 100:
                    self.price_history[market_tag] = self.price_history[market_tag][-100:]
                
            except Exception:
                continue
        
        return processed
    
    async def _display_data(self, data: Dict[str, Any]) -> None:
        """Display market data"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            markets = data.get("markets", {})
            status = data.get("status", "unknown")
            total_markets = data.get("total_markets", 0)
            
            market_container = Vertical()
            
            # Status header
            status_line = f"📊 Market Data ({status.upper()}) - {total_markets} markets"
            if data.get("error"):
                status_line += f" | Error: {data['error'][:30]}"
            
            market_container.mount(Static(status_line, classes="market-status"))
            
            if not markets:
                market_container.mount(Static("No market data available", classes="no-data"))
            else:
                # Sort markets by volume or alphabetically
                sorted_markets = sorted(
                    markets.items(),
                    key=lambda x: x[1].get("volume_24h", 0),
                    reverse=True
                )
                
                # Display top markets
                for symbol, market_data in sorted_markets[:8]:  # Show top 8 markets
                    price = market_data.get("price", 0)
                    change_24h = market_data.get("price_change_24h", 0)
                    volume_24h = market_data.get("volume_24h", 0)
                    
                    # Format price based on value
                    if price > 1000:
                        price_str = f"${price:,.0f}"
                    elif price > 1:
                        price_str = f"${price:.2f}"
                    else:
                        price_str = f"${price:.4f}"
                    
                    # Format volume
                    if volume_24h > 1000000:
                        volume_str = f"{volume_24h/1000000:.1f}M"
                    elif volume_24h > 1000:
                        volume_str = f"{volume_24h/1000:.1f}K"
                    else:
                        volume_str = f"{volume_24h:.0f}"
                    
                    # Choose icon and color based on price change
                    if change_24h > 0:
                        change_icon = "📈"
                        change_color = "green"
                    elif change_24h < 0:
                        change_icon = "📉"
                        change_color = "red"
                    else:
                        change_icon = "➖"
                        change_color = "yellow"
                    
                    # Create market line
                    market_line = f"{change_icon} {symbol:>12}: {price_str:>10} ({change_24h:+.2f}%) Vol: {volume_str}"
                    
                    market_widget = Static(market_line, classes=f"market-item market-{change_color}")
                    market_container.mount(market_widget)
                
                # Market summary
                if len(markets) > 0:
                    total_volume = sum(m.get("volume_24h", 0) for m in markets.values())
                    avg_change = sum(m.get("price_change_24h", 0) for m in markets.values()) / len(markets)
                    
                    positive_markets = sum(1 for m in markets.values() if m.get("price_change_24h", 0) > 0)
                    negative_markets = sum(1 for m in markets.values() if m.get("price_change_24h", 0) < 0)
                    
                    summary_line = f"Summary: {positive_markets}↗ {negative_markets}↘ | Avg: {avg_change:+.2f}% | Vol: {total_volume/1000000:.1f}M"
                    market_container.mount(Static(summary_line, classes="market-summary"))
                
                # Price trend indicators
                trending_up = []
                trending_down = []
                
                for symbol, market_data in markets.items():
                    change = market_data.get("price_change_24h", 0)
                    if change > 5:  # More than 5% gain
                        trending_up.append((symbol, change))
                    elif change < -5:  # More than 5% loss
                        trending_down.append((symbol, change))
                
                if trending_up:
                    trending_up.sort(key=lambda x: x[1], reverse=True)
                    top_gainers = ", ".join([f"{s} (+{c:.1f}%)" for s, c in trending_up[:3]])
                    market_container.mount(Static(f"🚀 Top Gainers: {top_gainers}", classes="trending-up"))
                
                if trending_down:
                    trending_down.sort(key=lambda x: x[1])
                    top_losers = ", ".join([f"{s} ({c:.1f}%)" for s, c in trending_down[:3]])
                    market_container.mount(Static(f"📉 Top Losers: {top_losers}", classes="trending-down"))
            
            content_container.mount(market_container)
            
        except Exception as e:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            content_container.mount(Static(f"Display error: {str(e)}", classes="error-message"))
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Get market summary"""
        if not self.market_data:
            return {"status": "No data", "total_markets": 0}
        
        markets = self.market_data.get("markets", {})
        if not markets:
            return {"status": "No data", "total_markets": 0}
        
        positive_count = sum(1 for m in markets.values() if m.get("price_change_24h", 0) > 0)
        negative_count = sum(1 for m in markets.values() if m.get("price_change_24h", 0) < 0)
        avg_change = sum(m.get("price_change_24h", 0) for m in markets.values()) / len(markets)
        
        # Determine market sentiment
        if avg_change > 2:
            sentiment = "bullish"
        elif avg_change < -2:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            "total_markets": len(markets),
            "positive_count": positive_count,
            "negative_count": negative_count,
            "average_change": avg_change,
            "sentiment": sentiment,
            "status": self.market_data.get("status", "unknown")
        }


class DashboardView(Widget):
    """Main dashboard with system overview"""
    
    def compose(self) -> ComposeResult:
        yield Horizontal(
            SystemStatusPanel(classes="panel"),
            QuickActionsPanel(classes="panel"),
            classes="dashboard-top"
        )
        yield Horizontal(
            ActiveBotsPanel(classes="panel"),
            RunningLabsPanel(classes="panel"),
            RecentAlertsPanel(classes="panel"),
            classes="dashboard-middle"
        )
        yield Horizontal(
            PerformanceChartPanel(classes="panel"),
            MarketOverviewPanel(classes="panel"),
            classes="dashboard-bottom"
        )
    
    def set_mcp_client(self, mcp_client):
        """Set MCP client for data updates"""
        self.mcp_client = mcp_client
    
    async def refresh_data(self):
        """Refresh dashboard data"""
        # TODO: Implement data refresh
        pass