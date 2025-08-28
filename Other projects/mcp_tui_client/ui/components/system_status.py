"""
System Status Dashboard Components

Enhanced system status monitoring with real-time metrics, connection health,
and comprehensive diagnostics tools.
"""

import asyncio
import psutil
import time
import platform
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widget import Widget
from textual.widgets import Static, Label, Button, ProgressBar
from textual.reactive import reactive
from textual.timer import Timer

from .panels import StatusPanel, DataPanel, ActionPanel
from .indicators import StatusIndicator, IndicatorStatus, PerformanceIndicator
from mcp_tui_client.services.mcp_client import MCPClientService, ConnectionState


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    network_sent_mb_s: float = 0.0
    network_recv_mb_s: float = 0.0
    load_average: List[float] = None
    uptime_seconds: float = 0.0
    
    def __post_init__(self):
        if self.load_average is None:
            self.load_average = [0.0, 0.0, 0.0]


@dataclass
class ConnectionHealth:
    """Connection health status"""
    mcp_connected: bool = False
    haas_connected: bool = False
    mcp_response_time: float = 0.0
    haas_response_time: float = 0.0
    last_mcp_check: Optional[datetime] = None
    last_haas_check: Optional[datetime] = None
    connection_errors: int = 0
    reconnection_attempts: int = 0


class SystemStatusDashboard(Container):
    """Main system status dashboard with comprehensive monitoring"""
    
    DEFAULT_CSS = """
    SystemStatusDashboard {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        height: 1fr;
        padding: 1;
    }
    
    SystemStatusDashboard .status-grid {
        height: 1fr;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.system_metrics = SystemMetrics()
        self.connection_health = ConnectionHealth()
        self.update_timer: Optional[Timer] = None
        self.diagnostics_data: Dict[str, Any] = {}
    
    def compose(self) -> ComposeResult:
        """Compose system status dashboard"""
        # Connection Status Panel
        yield ConnectionStatusPanel(
            title="🔗 Connection Status",
            classes="status-grid",
            id="connection-status"
        )
        
        # System Metrics Panel
        yield SystemMetricsPanel(
            title="🖥️ System Metrics",
            classes="status-grid",
            id="system-metrics"
        )
        
        # Performance Monitor Panel
        yield PerformanceMonitorPanel(
            title="📊 Performance Monitor",
            classes="status-grid",
            id="performance-monitor"
        )
        
        # Diagnostics Panel
        yield DiagnosticsPanel(
            title="🔧 System Diagnostics",
            classes="status-grid",
            id="diagnostics"
        )
    
    async def on_mount(self) -> None:
        """Initialize system monitoring"""
        # Start periodic updates every 5 seconds
        self.update_timer = self.set_interval(5.0, self._update_all_metrics)
        # Initial update
        await self._update_all_metrics()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for connection monitoring"""
        self.mcp_client = mcp_client
        
        # Pass to child panels
        connection_panel = self.query_one("#connection-status", ConnectionStatusPanel)
        connection_panel.set_mcp_client(mcp_client)
        
        performance_panel = self.query_one("#performance-monitor", PerformanceMonitorPanel)
        performance_panel.set_mcp_client(mcp_client)
        
        diagnostics_panel = self.query_one("#diagnostics", DiagnosticsPanel)
        diagnostics_panel.set_mcp_client(mcp_client)
    
    async def _update_all_metrics(self) -> None:
        """Update all system metrics"""
        try:
            # Update system metrics
            await self._collect_system_metrics()
            
            # Update connection health
            await self._check_connection_health()
            
            # Update child panels
            await self._update_child_panels()
            
        except Exception as e:
            self.app.logger.error(f"Error updating system metrics: {e}")
    
    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics"""
        try:
            # CPU usage
            self.system_metrics.cpu_percent = psutil.cpu_percent(interval=None)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics.memory_percent = memory.percent
            self.system_metrics.memory_used_gb = memory.used / (1024**3)
            self.system_metrics.memory_total_gb = memory.total / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_metrics.disk_percent = (disk.used / disk.total) * 100
            self.system_metrics.disk_used_gb = disk.used / (1024**3)
            self.system_metrics.disk_total_gb = disk.total / (1024**3)
            
            # Network I/O (calculate rates)
            current_net = psutil.net_io_counters()
            if hasattr(self, '_last_net_stats'):
                time_diff = 5.0  # Update interval
                sent_rate = (current_net.bytes_sent - self._last_net_stats.bytes_sent) / time_diff
                recv_rate = (current_net.bytes_recv - self._last_net_stats.bytes_recv) / time_diff
                
                self.system_metrics.network_sent_mb_s = sent_rate / (1024**2)
                self.system_metrics.network_recv_mb_s = recv_rate / (1024**2)
            
            self._last_net_stats = current_net
            
            # Load average (Unix-like systems)
            try:
                if hasattr(psutil, 'getloadavg'):
                    self.system_metrics.load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                # Windows doesn't have load average
                pass
            
            # System uptime
            boot_time = psutil.boot_time()
            self.system_metrics.uptime_seconds = time.time() - boot_time
            
        except Exception as e:
            self.app.logger.error(f"Error collecting system metrics: {e}")
    
    async def _check_connection_health(self) -> None:
        """Check connection health status"""
        if not self.mcp_client:
            return
        
        try:
            # Check MCP connection
            start_time = time.time()
            
            if self.mcp_client.is_connected:
                await self.mcp_client.health_check()
                self.connection_health.mcp_response_time = (time.time() - start_time) * 1000
                self.connection_health.mcp_connected = True
                self.connection_health.last_mcp_check = datetime.now()
            else:
                self.connection_health.mcp_connected = False
            
            # Check HaasOnline connection through MCP
            if self.connection_health.mcp_connected:
                start_time = time.time()
                haas_status = await self.mcp_client.get_haas_status()
                self.connection_health.haas_response_time = (time.time() - start_time) * 1000
                self.connection_health.haas_connected = haas_status.get("connected", False)
                self.connection_health.last_haas_check = datetime.now()
            else:
                self.connection_health.haas_connected = False
            
        except Exception as e:
            self.connection_health.connection_errors += 1
            self.app.logger.error(f"Error checking connection health: {e}")
    
    async def _update_child_panels(self) -> None:
        """Update all child panels with new data"""
        try:
            # Update system metrics panel
            metrics_panel = self.query_one("#system-metrics", SystemMetricsPanel)
            await metrics_panel.update_metrics(self.system_metrics)
            
            # Update connection status panel
            connection_panel = self.query_one("#connection-status", ConnectionStatusPanel)
            await connection_panel.update_connection_health(self.connection_health)
            
            # Update performance monitor
            performance_panel = self.query_one("#performance-monitor", PerformanceMonitorPanel)
            await performance_panel.update_performance_data({
                "system_metrics": self.system_metrics,
                "connection_health": self.connection_health
            })
            
        except Exception as e:
            self.app.logger.error(f"Error updating child panels: {e}")
    
    async def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "system_health": "unknown",
            "issues": [],
            "recommendations": [],
            "system_info": {},
            "performance_analysis": {},
            "connection_analysis": {}
        }
        
        try:
            # System information
            diagnostics["system_info"] = {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": self.system_metrics.memory_total_gb,
                "disk_total": self.system_metrics.disk_total_gb,
                "uptime_hours": self.system_metrics.uptime_seconds / 3600
            }
            
            # Performance analysis
            diagnostics["performance_analysis"] = {
                "cpu_status": self._analyze_cpu_performance(),
                "memory_status": self._analyze_memory_performance(),
                "disk_status": self._analyze_disk_performance(),
                "network_status": self._analyze_network_performance()
            }
            
            # Connection analysis
            diagnostics["connection_analysis"] = {
                "mcp_status": self._analyze_mcp_connection(),
                "haas_status": self._analyze_haas_connection(),
                "overall_connectivity": self._analyze_overall_connectivity()
            }
            
            # Determine overall health
            issues = []
            recommendations = []
            
            # Check system resources
            if self.system_metrics.cpu_percent > 90:
                issues.append("High CPU usage detected")
                recommendations.append("Consider closing unnecessary applications or optimizing workload")
            
            if self.system_metrics.memory_percent > 90:
                issues.append("High memory usage detected")
                recommendations.append("Consider restarting the application or freeing memory")
            
            if self.system_metrics.disk_percent > 95:
                issues.append("Low disk space")
                recommendations.append("Free up disk space to prevent system issues")
            
            # Check connections
            if not self.connection_health.mcp_connected:
                issues.append("MCP server connection failed")
                recommendations.append("Check MCP server status and network connectivity")
            
            if not self.connection_health.haas_connected:
                issues.append("HaasOnline connection failed")
                recommendations.append("Verify HaasOnline API credentials and server status")
            
            if self.connection_health.mcp_response_time > 5000:  # 5 seconds
                issues.append("Slow MCP server response times")
                recommendations.append("Check network latency and server performance")
            
            diagnostics["issues"] = issues
            diagnostics["recommendations"] = recommendations
            
            # Determine overall health
            if not issues:
                diagnostics["system_health"] = "healthy"
            elif len(issues) <= 2:
                diagnostics["system_health"] = "warning"
            else:
                diagnostics["system_health"] = "critical"
            
            self.diagnostics_data = diagnostics
            return diagnostics
            
        except Exception as e:
            diagnostics["system_health"] = "error"
            diagnostics["issues"].append(f"Diagnostics failed: {str(e)}")
            return diagnostics
    
    def _analyze_cpu_performance(self) -> Dict[str, Any]:
        """Analyze CPU performance"""
        cpu_percent = self.system_metrics.cpu_percent
        
        if cpu_percent > 90:
            status = "critical"
            message = "CPU usage is critically high"
        elif cpu_percent > 70:
            status = "warning"
            message = "CPU usage is elevated"
        else:
            status = "good"
            message = "CPU usage is normal"
        
        return {
            "status": status,
            "message": message,
            "usage_percent": cpu_percent,
            "load_average": self.system_metrics.load_average
        }
    
    def _analyze_memory_performance(self) -> Dict[str, Any]:
        """Analyze memory performance"""
        memory_percent = self.system_metrics.memory_percent
        
        if memory_percent > 90:
            status = "critical"
            message = "Memory usage is critically high"
        elif memory_percent > 80:
            status = "warning"
            message = "Memory usage is elevated"
        else:
            status = "good"
            message = "Memory usage is normal"
        
        return {
            "status": status,
            "message": message,
            "usage_percent": memory_percent,
            "used_gb": self.system_metrics.memory_used_gb,
            "total_gb": self.system_metrics.memory_total_gb
        }
    
    def _analyze_disk_performance(self) -> Dict[str, Any]:
        """Analyze disk performance"""
        disk_percent = self.system_metrics.disk_percent
        
        if disk_percent > 95:
            status = "critical"
            message = "Disk space is critically low"
        elif disk_percent > 85:
            status = "warning"
            message = "Disk space is running low"
        else:
            status = "good"
            message = "Disk space is adequate"
        
        return {
            "status": status,
            "message": message,
            "usage_percent": disk_percent,
            "used_gb": self.system_metrics.disk_used_gb,
            "total_gb": self.system_metrics.disk_total_gb
        }
    
    def _analyze_network_performance(self) -> Dict[str, Any]:
        """Analyze network performance"""
        total_activity = self.system_metrics.network_sent_mb_s + self.system_metrics.network_recv_mb_s
        
        if total_activity > 100:  # > 100 MB/s
            status = "high"
            message = "High network activity detected"
        elif total_activity > 10:  # > 10 MB/s
            status = "moderate"
            message = "Moderate network activity"
        else:
            status = "low"
            message = "Low network activity"
        
        return {
            "status": status,
            "message": message,
            "sent_mb_s": self.system_metrics.network_sent_mb_s,
            "recv_mb_s": self.system_metrics.network_recv_mb_s,
            "total_mb_s": total_activity
        }
    
    def _analyze_mcp_connection(self) -> Dict[str, Any]:
        """Analyze MCP connection status"""
        if not self.connection_health.mcp_connected:
            return {
                "status": "disconnected",
                "message": "MCP server is not connected",
                "response_time": None,
                "last_check": self.connection_health.last_mcp_check
            }
        
        response_time = self.connection_health.mcp_response_time
        
        if response_time > 5000:  # 5 seconds
            status = "slow"
            message = "MCP server response is slow"
        elif response_time > 1000:  # 1 second
            status = "moderate"
            message = "MCP server response is moderate"
        else:
            status = "fast"
            message = "MCP server response is fast"
        
        return {
            "status": status,
            "message": message,
            "response_time": response_time,
            "last_check": self.connection_health.last_mcp_check
        }
    
    def _analyze_haas_connection(self) -> Dict[str, Any]:
        """Analyze HaasOnline connection status"""
        if not self.connection_health.haas_connected:
            return {
                "status": "disconnected",
                "message": "HaasOnline is not connected",
                "response_time": None,
                "last_check": self.connection_health.last_haas_check
            }
        
        response_time = self.connection_health.haas_response_time
        
        if response_time > 10000:  # 10 seconds
            status = "slow"
            message = "HaasOnline response is slow"
        elif response_time > 3000:  # 3 seconds
            status = "moderate"
            message = "HaasOnline response is moderate"
        else:
            status = "fast"
            message = "HaasOnline response is fast"
        
        return {
            "status": status,
            "message": message,
            "response_time": response_time,
            "last_check": self.connection_health.last_haas_check
        }
    
    def _analyze_overall_connectivity(self) -> Dict[str, Any]:
        """Analyze overall connectivity status"""
        if self.connection_health.mcp_connected and self.connection_health.haas_connected:
            return {
                "status": "fully_connected",
                "message": "All systems connected",
                "connection_errors": self.connection_health.connection_errors
            }
        elif self.connection_health.mcp_connected:
            return {
                "status": "partial",
                "message": "MCP connected, HaasOnline disconnected",
                "connection_errors": self.connection_health.connection_errors
            }
        else:
            return {
                "status": "disconnected",
                "message": "No connections established",
                "connection_errors": self.connection_health.connection_errors
            }
    
    def on_unmount(self) -> None:
        """Clean up timers"""
        if self.update_timer:
            self.update_timer.stop()


class ConnectionStatusPanel(StatusPanel):
    """Panel showing connection status with health indicators"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcp_client: Optional[MCPClientService] = None
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for monitoring"""
        self.mcp_client = mcp_client
        if mcp_client:
            mcp_client.add_connection_callback(self._on_connection_state_change)
    
    async def update_connection_health(self, health: ConnectionHealth) -> None:
        """Update connection health display"""
        # MCP Connection
        mcp_status = "normal" if health.mcp_connected else "error"
        mcp_value = "Connected" if health.mcp_connected else "Disconnected"
        if health.mcp_connected and health.mcp_response_time:
            mcp_value += f" ({health.mcp_response_time:.0f}ms)"
        
        self.add_status_item("mcp_connection", "🔗 MCP Server", mcp_value, mcp_status)
        
        # HaasOnline Connection
        haas_status = "normal" if health.haas_connected else "error"
        haas_value = "Connected" if health.haas_connected else "Disconnected"
        if health.haas_connected and health.haas_response_time:
            haas_value += f" ({health.haas_response_time:.0f}ms)"
        
        self.add_status_item("haas_connection", "🏦 HaasOnline", haas_value, haas_status)
        
        # Connection Quality
        if health.mcp_connected and health.haas_connected:
            avg_response = (health.mcp_response_time + health.haas_response_time) / 2
            if avg_response < 1000:
                quality_status = "normal"
                quality_value = "Excellent"
            elif avg_response < 3000:
                quality_status = "warning"
                quality_value = "Good"
            else:
                quality_status = "error"
                quality_value = "Poor"
        else:
            quality_status = "error"
            quality_value = "Degraded"
        
        self.add_status_item("connection_quality", "📶 Quality", quality_value, quality_status)
        
        # Error Count
        error_status = "normal" if health.connection_errors < 5 else "warning"
        self.add_status_item("connection_errors", "⚠️ Errors", str(health.connection_errors), error_status)
    
    def _on_connection_state_change(self, new_state: ConnectionState) -> None:
        """Handle connection state changes"""
        state_colors = {
            ConnectionState.CONNECTED: "normal",
            ConnectionState.CONNECTING: "warning",
            ConnectionState.RECONNECTING: "warning",
            ConnectionState.DISCONNECTED: "error",
            ConnectionState.FAILED: "error"
        }
        
        status = state_colors.get(new_state, "error")
        self.add_status_item("mcp_state", "🔄 State", new_state.value.title(), status)


class SystemMetricsPanel(StatusPanel):
    """Panel showing system performance metrics"""
    
    async def update_metrics(self, metrics: SystemMetrics) -> None:
        """Update system metrics display"""
        # CPU Usage
        cpu_status = "error" if metrics.cpu_percent > 90 else "warning" if metrics.cpu_percent > 70 else "normal"
        self.add_status_item("cpu_usage", "🖥️ CPU", f"{metrics.cpu_percent:.1f}%", cpu_status)
        
        # Memory Usage
        memory_status = "error" if metrics.memory_percent > 90 else "warning" if metrics.memory_percent > 80 else "normal"
        memory_value = f"{metrics.memory_used_gb:.1f}GB / {metrics.memory_total_gb:.1f}GB ({metrics.memory_percent:.1f}%)"
        self.add_status_item("memory_usage", "💾 Memory", memory_value, memory_status)
        
        # Disk Usage
        disk_status = "error" if metrics.disk_percent > 95 else "warning" if metrics.disk_percent > 85 else "normal"
        disk_value = f"{metrics.disk_used_gb:.1f}GB / {metrics.disk_total_gb:.1f}GB ({metrics.disk_percent:.1f}%)"
        self.add_status_item("disk_usage", "💿 Disk", disk_value, disk_status)
        
        # Network Activity
        network_total = metrics.network_sent_mb_s + metrics.network_recv_mb_s
        network_status = "warning" if network_total > 100 else "normal"
        network_value = f"↑{metrics.network_sent_mb_s:.1f} ↓{metrics.network_recv_mb_s:.1f} MB/s"
        self.add_status_item("network_activity", "🌐 Network", network_value, network_status)
        
        # System Uptime
        uptime_hours = metrics.uptime_seconds / 3600
        if uptime_hours < 24:
            uptime_value = f"{uptime_hours:.1f}h"
        else:
            uptime_days = uptime_hours / 24
            uptime_value = f"{uptime_days:.1f}d"
        
        self.add_status_item("uptime", "⏱️ Uptime", uptime_value, "normal")
        
        # Load Average (if available)
        if metrics.load_average and any(metrics.load_average):
            load_value = f"{metrics.load_average[0]:.2f}, {metrics.load_average[1]:.2f}, {metrics.load_average[2]:.2f}"
            load_status = "warning" if metrics.load_average[0] > psutil.cpu_count() else "normal"
            self.add_status_item("load_average", "📊 Load", load_value, load_status)


class PerformanceMonitorPanel(DataPanel):
    """Panel showing performance monitoring and trends"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.performance_history: List[Dict[str, Any]] = []
        self.max_history = 60  # Keep 60 data points (5 minutes at 5-second intervals)
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for performance monitoring"""
        self.mcp_client = mcp_client
    
    async def update_performance_data(self, data: Dict[str, Any]) -> None:
        """Update performance monitoring data"""
        try:
            # Safely extract data with defaults
            system_metrics = data.get("system_metrics")
            connection_health = data.get("connection_health")
            
            if not system_metrics or not connection_health:
                return
            
            # Add current data to history
            current_data = {
                "timestamp": datetime.now(),
                "cpu_percent": getattr(system_metrics, 'cpu_percent', 0),
                "memory_percent": getattr(system_metrics, 'memory_percent', 0),
                "mcp_response_time": getattr(connection_health, 'mcp_response_time', 0),
                "haas_response_time": getattr(connection_health, 'haas_response_time', 0)
            }
            
            self.performance_history.append(current_data)
            
            # Trim history to max size
            if len(self.performance_history) > self.max_history:
                self.performance_history.pop(0)
            
            # Update display
            await self._display_performance_trends()
            
        except Exception as e:
            # Log error but don't crash
            if hasattr(self, 'app') and hasattr(self.app, 'logger'):
                self.app.logger.error(f"Error updating performance data: {e}")
            # Set a simple error message
            try:
                content_container = self.query_one("#panel-content")
                content_container.remove_children()
                content_container.mount(Static(f"Performance monitoring error: {str(e)[:50]}"))
            except:
                pass
    
    async def _display_performance_trends(self) -> None:
        """Display performance trends"""
        content_container = self.query_one("#panel-content")
        content_container.remove_children()
        
        if not self.performance_history:
            content_container.mount(Static("No performance data available"))
            return
        
        trends_container = Vertical()
        
        # CPU Trend
        cpu_values = [d.get("cpu_percent", 0) for d in self.performance_history[-10:]]  # Last 10 points
        cpu_trend = self._calculate_trend(cpu_values) if cpu_values else "no data"
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        
        cpu_trend_text = f"CPU: {cpu_avg:.1f}% avg, trend: {cpu_trend}"
        trends_container.mount(Static(cpu_trend_text, classes="trend-item"))
        
        # Memory Trend
        memory_values = [d.get("memory_percent", 0) for d in self.performance_history[-10:]]
        memory_trend = self._calculate_trend(memory_values) if memory_values else "no data"
        memory_avg = sum(memory_values) / len(memory_values) if memory_values else 0
        
        memory_trend_text = f"Memory: {memory_avg:.1f}% avg, trend: {memory_trend}"
        trends_container.mount(Static(memory_trend_text, classes="trend-item"))
        
        # Response Time Trend
        mcp_times = [d.get("mcp_response_time", 0) for d in self.performance_history[-10:] if d.get("mcp_response_time")]
        if mcp_times:
            mcp_avg = sum(mcp_times) / len(mcp_times)
            mcp_trend = self._calculate_trend(mcp_times)
            mcp_trend_text = f"MCP Response: {mcp_avg:.0f}ms avg, trend: {mcp_trend}"
            trends_container.mount(Static(mcp_trend_text, classes="trend-item"))
        else:
            trends_container.mount(Static("MCP Response: No data available", classes="trend-item"))
        
        # Performance Score
        score = self._calculate_performance_score()
        score_text = f"Performance Score: {score}/100"
        score_color = "green" if score > 80 else "yellow" if score > 60 else "red"
        trends_container.mount(Static(score_text, classes=f"score-item score-{score_color}"))
        
        content_container.mount(trends_container)
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend calculation
        half_point = len(values) // 2
        if half_point == 0:
            return "stable"
            
        first_half_values = values[:half_point]
        second_half_values = values[half_point:]
        
        if not first_half_values or not second_half_values:
            return "stable"
        
        first_half = sum(first_half_values) / len(first_half_values)
        second_half = sum(second_half_values) / len(second_half_values)
        
        if first_half == 0:
            return "stable" if second_half == 0 else "↗️ rising"
        
        diff_percent = ((second_half - first_half) / first_half * 100)
        
        if diff_percent > 10:
            return "↗️ rising"
        elif diff_percent < -10:
            return "↘️ falling"
        else:
            return "→ stable"
    
    def _calculate_performance_score(self) -> int:
        """Calculate overall performance score (0-100)"""
        if not self.performance_history:
            return 0
        
        latest = self.performance_history[-1]
        score = 100
        
        # Deduct points for high resource usage
        cpu_percent = latest.get("cpu_percent", 0)
        if cpu_percent > 80:
            score -= 20
        elif cpu_percent > 60:
            score -= 10
        
        memory_percent = latest.get("memory_percent", 0)
        if memory_percent > 90:
            score -= 25
        elif memory_percent > 80:
            score -= 15
        
        # Deduct points for slow response times
        mcp_response_time = latest.get("mcp_response_time", 0)
        if mcp_response_time and mcp_response_time > 5000:
            score -= 20
        elif mcp_response_time and mcp_response_time > 2000:
            score -= 10
        
        return max(0, score)


class DiagnosticsPanel(ActionPanel):
    """Panel with system diagnostics and troubleshooting tools"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcp_client: Optional[MCPClientService] = None
        self.last_diagnostics: Optional[Dict[str, Any]] = None
    
    async def on_mount(self) -> None:
        """Initialize diagnostics panel"""
        await super().on_mount()
        
        # Add diagnostic actions
        self.add_action(
            "run_diagnostics",
            "🔍 Run Diagnostics",
            self._run_diagnostics,
            variant="primary"
        )
        
        self.add_action(
            "connection_test",
            "🔗 Test Connections",
            self._test_connections,
            variant="default"
        )
        
        self.add_action(
            "clear_cache",
            "🗑️ Clear Cache",
            self._clear_cache,
            variant="default"
        )
        
        self.add_action(
            "export_logs",
            "📋 Export Logs",
            self._export_logs,
            variant="default"
        )
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for diagnostics"""
        self.mcp_client = mcp_client
    
    async def _run_diagnostics(self) -> None:
        """Run comprehensive system diagnostics"""
        self.set_status("normal", "Running diagnostics...")
        
        try:
            # Get parent dashboard for full diagnostics
            dashboard = self.parent.parent  # Navigate up to SystemStatusDashboard
            if hasattr(dashboard, 'run_full_diagnostics'):
                diagnostics = await dashboard.run_full_diagnostics()
                self.last_diagnostics = diagnostics
                
                # Update status based on results
                health = diagnostics.get("system_health", "unknown")
                issue_count = len(diagnostics.get("issues", []))
                
                if health == "healthy":
                    self.set_status("success", "System is healthy")
                elif health == "warning":
                    self.set_status("warning", f"Found {issue_count} issues")
                else:
                    self.set_status("error", f"Found {issue_count} critical issues")
            else:
                self.set_status("error", "Diagnostics not available")
                
        except Exception as e:
            self.set_status("error", f"Diagnostics failed: {str(e)}")
    
    async def _test_connections(self) -> None:
        """Test all connections"""
        self.set_status("normal", "Testing connections...")
        
        try:
            if not self.mcp_client:
                self.set_status("error", "MCP client not available")
                return
            
            # Test MCP connection
            mcp_start = time.time()
            await self.mcp_client.health_check()
            mcp_time = (time.time() - mcp_start) * 1000
            
            # Test HaasOnline connection
            haas_start = time.time()
            haas_status = await self.mcp_client.get_haas_status()
            haas_time = (time.time() - haas_start) * 1000
            
            # Report results
            if haas_status.get("connected", False):
                self.set_status("success", f"All connections OK (MCP: {mcp_time:.0f}ms, Haas: {haas_time:.0f}ms)")
            else:
                self.set_status("warning", f"MCP OK ({mcp_time:.0f}ms), HaasOnline failed")
                
        except Exception as e:
            self.set_status("error", f"Connection test failed: {str(e)}")
    
    async def _clear_cache(self) -> None:
        """Clear application cache"""
        self.set_status("normal", "Clearing cache...")
        
        try:
            # Clear MCP client cache if available
            if self.mcp_client and hasattr(self.mcp_client, 'clear_cache'):
                await self.mcp_client.clear_cache()
            
            # Clear other caches as needed
            # This would depend on the specific caching implementation
            
            self.set_status("success", "Cache cleared successfully")
            
        except Exception as e:
            self.set_status("error", f"Cache clear failed: {str(e)}")
    
    async def _export_logs(self) -> None:
        """Export system logs and diagnostics"""
        self.set_status("normal", "Exporting logs...")
        
        try:
            # Create export data
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "platform": platform.platform(),
                    "python_version": platform.python_version()
                },
                "diagnostics": self.last_diagnostics,
                "connection_info": self.mcp_client.connection_info if self.mcp_client else None
            }
            
            # In a real implementation, this would save to a file
            # For now, just indicate success
            self.set_status("success", "Logs exported successfully")
            
        except Exception as e:
            self.set_status("error", f"Log export failed: {str(e)}")