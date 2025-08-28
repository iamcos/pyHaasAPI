"""
Performance Monitoring Dashboard

Real-time performance monitoring with ASCII charts, resource usage tracking,
and system health scoring with recommendations.
"""

import asyncio
import psutil
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import deque

from textual.widget import Widget
from textual.widgets import Static, Label, ProgressBar
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.timer import Timer

from mcp_tui_client.ui.components.charts import LineChart, BarChart, ASCIIChart
from mcp_tui_client.ui.components.panels import BasePanel, StatusPanel
from mcp_tui_client.services.mcp_client import MCPClientService


class PerformanceMetricsCollector:
    """Collects and manages performance metrics with history"""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.metrics_history = {
            "cpu_percent": deque(maxlen=history_size),
            "memory_percent": deque(maxlen=history_size),
            "disk_io_read": deque(maxlen=history_size),
            "disk_io_write": deque(maxlen=history_size),
            "network_sent": deque(maxlen=history_size),
            "network_recv": deque(maxlen=history_size),
            "api_response_time": deque(maxlen=history_size),
            "api_requests_per_sec": deque(maxlen=history_size),
            "active_connections": deque(maxlen=history_size),
            "error_rate": deque(maxlen=history_size),
        }
        self.timestamps = deque(maxlen=history_size)
        self.last_disk_io = None
        self.last_network_io = None
        self.api_call_times = deque(maxlen=60)  # Last 60 API calls
        self.error_count = 0
        self.total_requests = 0
    
    async def collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        current_time = datetime.now()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_rate = 0.0
        disk_write_rate = 0.0
        
        if self.last_disk_io and len(self.timestamps) > 0:
            time_diff = (current_time - self.timestamps[-1]).total_seconds()
            if time_diff > 0:
                disk_read_rate = (disk_io.read_bytes - self.last_disk_io.read_bytes) / time_diff / (1024**2)  # MB/s
                disk_write_rate = (disk_io.write_bytes - self.last_disk_io.write_bytes) / time_diff / (1024**2)  # MB/s
        
        self.last_disk_io = disk_io
        
        # Network I/O
        network_io = psutil.net_io_counters()
        network_sent_rate = 0.0
        network_recv_rate = 0.0
        
        if self.last_network_io and len(self.timestamps) > 0:
            time_diff = (current_time - self.timestamps[-1]).total_seconds()
            if time_diff > 0:
                network_sent_rate = (network_io.bytes_sent - self.last_network_io.bytes_sent) / time_diff / (1024**2)  # MB/s
                network_recv_rate = (network_io.bytes_recv - self.last_network_io.bytes_recv) / time_diff / (1024**2)  # MB/s
        
        self.last_network_io = network_io
        
        # Calculate API metrics
        api_response_time = statistics.mean(self.api_call_times) if self.api_call_times else 0.0
        
        # Calculate requests per second (last 60 seconds)
        recent_calls = [t for t in self.api_call_times if (current_time.timestamp() - t) <= 60]
        api_requests_per_sec = len(recent_calls) / 60.0
        
        # Error rate (percentage of failed requests in last 100 requests)
        error_rate = (self.error_count / max(self.total_requests, 1)) * 100
        
        # Active connections (estimate based on network activity)
        active_connections = min(10, max(1, int(network_sent_rate + network_recv_rate)))
        
        # Store metrics
        metrics = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_io_read": disk_read_rate,
            "disk_io_write": disk_write_rate,
            "network_sent": network_sent_rate,
            "network_recv": network_recv_rate,
            "api_response_time": api_response_time,
            "api_requests_per_sec": api_requests_per_sec,
            "active_connections": active_connections,
            "error_rate": error_rate,
        }
        
        # Add to history
        for key, value in metrics.items():
            self.metrics_history[key].append(value)
        
        self.timestamps.append(current_time)
        
        return metrics
    
    def record_api_call(self, response_time: float, success: bool = True) -> None:
        """Record an API call for metrics"""
        self.api_call_times.append(time.time())
        self.total_requests += 1
        if not success:
            self.error_count += 1
    
    def get_metric_history(self, metric_name: str, duration_minutes: int = 30) -> List[float]:
        """Get metric history for specified duration"""
        if metric_name not in self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        # Find the index where we should start
        start_index = 0
        for i, timestamp in enumerate(self.timestamps):
            if timestamp >= cutoff_time:
                start_index = i
                break
        
        return list(self.metrics_history[metric_name])[start_index:]
    
    def get_metric_stats(self, metric_name: str, duration_minutes: int = 30) -> Dict[str, float]:
        """Get statistical summary of a metric"""
        history = self.get_metric_history(metric_name, duration_minutes)
        
        if not history:
            return {"min": 0, "max": 0, "avg": 0, "current": 0}
        
        return {
            "min": min(history),
            "max": max(history),
            "avg": statistics.mean(history),
            "current": history[-1] if history else 0
        }


class SystemHealthScorer:
    """Calculates system health score and provides recommendations"""
    
    def __init__(self):
        self.weight_factors = {
            "cpu_percent": 0.25,
            "memory_percent": 0.25,
            "disk_io": 0.15,
            "network_io": 0.10,
            "api_response_time": 0.15,
            "error_rate": 0.10
        }
    
    def calculate_health_score(self, metrics: Dict[str, float]) -> Tuple[int, str, List[str]]:
        """Calculate overall system health score (0-100) with status and recommendations"""
        
        # Individual component scores (0-100, higher is better)
        cpu_score = max(0, 100 - metrics.get("cpu_percent", 0))
        memory_score = max(0, 100 - metrics.get("memory_percent", 0))
        
        # Disk I/O score (penalize high I/O)
        disk_io_total = metrics.get("disk_io_read", 0) + metrics.get("disk_io_write", 0)
        disk_score = max(0, 100 - min(100, disk_io_total * 10))  # 10 MB/s = 0 score
        
        # Network I/O score
        network_io_total = metrics.get("network_sent", 0) + metrics.get("network_recv", 0)
        network_score = max(0, 100 - min(100, network_io_total * 5))  # 20 MB/s = 0 score
        
        # API response time score (penalize slow responses)
        api_response_time = metrics.get("api_response_time", 0)
        api_score = max(0, 100 - min(100, api_response_time / 10))  # 1000ms = 0 score
        
        # Error rate score
        error_rate = metrics.get("error_rate", 0)
        error_score = max(0, 100 - error_rate)
        
        # Calculate weighted overall score
        overall_score = (
            cpu_score * self.weight_factors["cpu_percent"] +
            memory_score * self.weight_factors["memory_percent"] +
            disk_score * self.weight_factors["disk_io"] +
            network_score * self.weight_factors["network_io"] +
            api_score * self.weight_factors["api_response_time"] +
            error_score * self.weight_factors["error_rate"]
        )
        
        # Determine status
        if overall_score >= 80:
            status = "excellent"
        elif overall_score >= 60:
            status = "good"
        elif overall_score >= 40:
            status = "warning"
        else:
            status = "critical"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, {
            "cpu": cpu_score,
            "memory": memory_score,
            "disk": disk_score,
            "network": network_score,
            "api": api_score,
            "error": error_score
        })
        
        return int(overall_score), status, recommendations
    
    def _generate_recommendations(self, metrics: Dict[str, float], scores: Dict[str, float]) -> List[str]:
        """Generate specific recommendations based on metrics"""
        recommendations = []
        
        # CPU recommendations
        if scores["cpu"] < 50:
            cpu_percent = metrics.get("cpu_percent", 0)
            if cpu_percent > 90:
                recommendations.append("🔥 Critical: CPU usage is very high. Consider closing unnecessary applications.")
            elif cpu_percent > 70:
                recommendations.append("⚠️ Warning: High CPU usage detected. Monitor system performance.")
        
        # Memory recommendations
        if scores["memory"] < 50:
            memory_percent = metrics.get("memory_percent", 0)
            if memory_percent > 90:
                recommendations.append("🔥 Critical: Memory usage is very high. Consider restarting the application.")
            elif memory_percent > 80:
                recommendations.append("⚠️ Warning: High memory usage. Monitor for memory leaks.")
        
        # Disk I/O recommendations
        if scores["disk"] < 50:
            disk_total = metrics.get("disk_io_read", 0) + metrics.get("disk_io_write", 0)
            if disk_total > 50:
                recommendations.append("💾 High disk I/O activity. Consider optimizing data operations.")
        
        # Network recommendations
        if scores["network"] < 50:
            network_total = metrics.get("network_sent", 0) + metrics.get("network_recv", 0)
            if network_total > 10:
                recommendations.append("🌐 High network activity. Check for unnecessary data transfers.")
        
        # API performance recommendations
        if scores["api"] < 50:
            api_time = metrics.get("api_response_time", 0)
            if api_time > 2000:
                recommendations.append("🐌 Very slow API responses. Check network connectivity and server status.")
            elif api_time > 1000:
                recommendations.append("⏱️ Slow API responses detected. Monitor server performance.")
        
        # Error rate recommendations
        if scores["error"] < 70:
            error_rate = metrics.get("error_rate", 0)
            if error_rate > 10:
                recommendations.append("❌ High error rate detected. Check logs for recurring issues.")
            elif error_rate > 5:
                recommendations.append("⚠️ Elevated error rate. Monitor for potential issues.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ System is performing well. Continue monitoring.")
        
        return recommendations


class PerformanceChartPanel(BasePanel):
    """Main performance monitoring dashboard with ASCII charts and real-time metrics"""
    
    def __init__(self, **kwargs):
        super().__init__(title="Performance Monitoring", show_header=True, show_footer=True, **kwargs)
        self.metrics_collector = PerformanceMetricsCollector()
        self.health_scorer = SystemHealthScorer()
        self.mcp_client: Optional[MCPClientService] = None
        self.update_timer: Optional[Timer] = None
        self.current_metrics = {}
        self.health_score = 0
        self.health_status = "unknown"
        self.recommendations = []
    
    def compose(self) -> ComposeResult:
        """Compose performance monitoring dashboard"""
        yield from super().compose()
    
    async def on_mount(self) -> None:
        """Initialize performance monitoring"""
        await self._setup_dashboard()
        # Start monitoring with 5-second intervals
        self.update_timer = self.set_interval(5.0, self._update_performance_metrics)
        # Initial update
        await self._update_performance_metrics()
    
    def set_mcp_client(self, mcp_client: MCPClientService) -> None:
        """Set MCP client for API monitoring"""
        self.mcp_client = mcp_client
        if mcp_client:
            # Hook into MCP client for API call monitoring
            original_call = mcp_client.call_tool
            
            async def monitored_call(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await original_call(*args, **kwargs)
                    response_time = (time.time() - start_time) * 1000
                    self.metrics_collector.record_api_call(response_time, True)
                    return result
                except Exception as e:
                    response_time = (time.time() - start_time) * 1000
                    self.metrics_collector.record_api_call(response_time, False)
                    raise
            
            mcp_client.call_tool = monitored_call
    
    async def _setup_dashboard(self) -> None:
        """Set up the performance dashboard layout"""
        try:
            content_container = self.query_one("#panel-content")
            content_container.remove_children()
            
            # Create main dashboard layout
            dashboard_container = Vertical()
            
            # Top row: Health score and key metrics
            top_row = Horizontal(classes="performance-top-row")
            
            # Health score panel
            health_panel = Container(classes="health-score-panel")
            health_panel.mount(Label("System Health", classes="panel-title"))
            health_panel.mount(Label("Calculating...", classes="health-score", id="health-score"))
            health_panel.mount(Label("", classes="health-status", id="health-status"))
            top_row.mount(health_panel)
            
            # Key metrics panel
            metrics_panel = Container(classes="key-metrics-panel")
            metrics_panel.mount(Label("Key Metrics", classes="panel-title"))
            metrics_panel.mount(Label("CPU: 0%", classes="metric-item", id="cpu-metric"))
            metrics_panel.mount(Label("Memory: 0%", classes="metric-item", id="memory-metric"))
            metrics_panel.mount(Label("API: 0ms", classes="metric-item", id="api-metric"))
            metrics_panel.mount(Label("Errors: 0%", classes="metric-item", id="error-metric"))
            top_row.mount(metrics_panel)
            
            dashboard_container.mount(top_row)
            
            # Middle row: Performance charts
            charts_row = Horizontal(classes="performance-charts-row")
            
            # CPU and Memory chart
            cpu_memory_chart = LineChart(
                title="CPU & Memory Usage",
                width=40,
                height=12,
                id="cpu-memory-chart"
            )
            charts_row.mount(cpu_memory_chart)
            
            # Network I/O chart
            network_chart = LineChart(
                title="Network I/O (MB/s)",
                width=40,
                height=12,
                id="network-chart"
            )
            charts_row.mount(network_chart)
            
            dashboard_container.mount(charts_row)
            
            # Bottom row: Recommendations and alerts
            bottom_row = Horizontal(classes="performance-bottom-row")
            
            # Recommendations panel
            recommendations_panel = Container(classes="recommendations-panel")
            recommendations_panel.mount(Label("Recommendations", classes="panel-title"))
            recommendations_panel.mount(Container(id="recommendations-content"))
            bottom_row.mount(recommendations_panel)
            
            # Resource usage bars
            resources_panel = Container(classes="resources-panel")
            resources_panel.mount(Label("Resource Usage", classes="panel-title"))
            resources_panel.mount(Label("CPU", classes="resource-label"))
            resources_panel.mount(ProgressBar(total=100, show_percentage=True, id="cpu-progress"))
            resources_panel.mount(Label("Memory", classes="resource-label"))
            resources_panel.mount(ProgressBar(total=100, show_percentage=True, id="memory-progress"))
            resources_panel.mount(Label("Disk I/O", classes="resource-label"))
            resources_panel.mount(ProgressBar(total=100, show_percentage=True, id="disk-progress"))
            bottom_row.mount(resources_panel)
            
            dashboard_container.mount(bottom_row)
            
            content_container.mount(dashboard_container)
            
        except Exception as e:
            self.set_status("error", f"Dashboard setup failed: {str(e)}")
    
    async def _update_performance_metrics(self) -> None:
        """Update all performance metrics and displays"""
        try:
            # Collect current metrics
            self.current_metrics = await self.metrics_collector.collect_system_metrics()
            
            # Calculate health score
            self.health_score, self.health_status, self.recommendations = \
                self.health_scorer.calculate_health_score(self.current_metrics)
            
            # Update displays
            await self._update_health_display()
            await self._update_key_metrics_display()
            await self._update_charts()
            await self._update_recommendations_display()
            await self._update_resource_bars()
            
            # Update footer with last update time
            self.set_status("success", f"Updated: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.set_status("error", f"Metrics update failed: {str(e)}")
    
    async def _update_health_display(self) -> None:
        """Update health score display"""
        try:
            health_score_label = self.query_one("#health-score", Label)
            health_status_label = self.query_one("#health-status", Label)
            
            # Update score with color coding
            score_text = f"{self.health_score}/100"
            if self.health_score >= 80:
                score_color = "green"
                status_icon = "🟢"
            elif self.health_score >= 60:
                score_color = "yellow"
                status_icon = "🟡"
            elif self.health_score >= 40:
                score_color = "orange"
                status_icon = "🟠"
            else:
                score_color = "red"
                status_icon = "🔴"
            
            health_score_label.update(score_text)
            health_score_label.remove_class("green", "yellow", "orange", "red")
            health_score_label.add_class(score_color)
            
            status_text = f"{status_icon} {self.health_status.title()}"
            health_status_label.update(status_text)
            
        except Exception:
            pass  # Widget might not be ready
    
    async def _update_key_metrics_display(self) -> None:
        """Update key metrics display"""
        try:
            cpu_metric = self.query_one("#cpu-metric", Label)
            memory_metric = self.query_one("#memory-metric", Label)
            api_metric = self.query_one("#api-metric", Label)
            error_metric = self.query_one("#error-metric", Label)
            
            cpu_percent = self.current_metrics.get("cpu_percent", 0)
            memory_percent = self.current_metrics.get("memory_percent", 0)
            api_time = self.current_metrics.get("api_response_time", 0)
            error_rate = self.current_metrics.get("error_rate", 0)
            
            cpu_metric.update(f"CPU: {cpu_percent:.1f}%")
            memory_metric.update(f"Memory: {memory_percent:.1f}%")
            api_metric.update(f"API: {api_time:.0f}ms")
            error_metric.update(f"Errors: {error_rate:.1f}%")
            
        except Exception:
            pass  # Widget might not be ready
    
    async def _update_charts(self) -> None:
        """Update performance charts"""
        try:
            # Update CPU & Memory chart
            cpu_memory_chart = self.query_one("#cpu-memory-chart", LineChart)
            cpu_history = self.metrics_collector.get_metric_history("cpu_percent", 15)  # 15 minutes
            memory_history = self.metrics_collector.get_metric_history("memory_percent", 15)
            
            if cpu_history and memory_history:
                # Combine CPU and memory data for dual-line chart
                # For simplicity, we'll show CPU data (could be enhanced to show both)
                cpu_memory_chart.set_data(cpu_history[-30:])  # Last 30 data points
            
            # Update Network I/O chart
            network_chart = self.query_one("#network-chart", LineChart)
            network_sent_history = self.metrics_collector.get_metric_history("network_sent", 15)
            network_recv_history = self.metrics_collector.get_metric_history("network_recv", 15)
            
            if network_sent_history and network_recv_history:
                # Combine sent and received for total network activity
                network_total = [s + r for s, r in zip(network_sent_history, network_recv_history)]
                network_chart.set_data(network_total[-30:])  # Last 30 data points
            
        except Exception:
            pass  # Charts might not be ready
    
    async def _update_recommendations_display(self) -> None:
        """Update recommendations display"""
        try:
            recommendations_content = self.query_one("#recommendations-content", Container)
            recommendations_content.remove_children()
            
            if self.recommendations:
                for i, recommendation in enumerate(self.recommendations[:3]):  # Show top 3
                    rec_label = Label(recommendation, classes="recommendation-item")
                    recommendations_content.mount(rec_label)
            else:
                recommendations_content.mount(Label("No recommendations", classes="no-recommendations"))
            
        except Exception:
            pass  # Widget might not be ready
    
    async def _update_resource_bars(self) -> None:
        """Update resource usage progress bars"""
        try:
            cpu_progress = self.query_one("#cpu-progress", ProgressBar)
            memory_progress = self.query_one("#memory-progress", ProgressBar)
            disk_progress = self.query_one("#disk-progress", ProgressBar)
            
            cpu_percent = self.current_metrics.get("cpu_percent", 0)
            memory_percent = self.current_metrics.get("memory_percent", 0)
            disk_io_total = self.current_metrics.get("disk_io_read", 0) + self.current_metrics.get("disk_io_write", 0)
            disk_percent = min(100, disk_io_total * 10)  # Scale disk I/O to percentage
            
            cpu_progress.update(progress=cpu_percent)
            memory_progress.update(progress=memory_percent)
            disk_progress.update(progress=disk_percent)
            
        except Exception:
            pass  # Widget might not be ready
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": self.health_score,
            "health_status": self.health_status,
            "current_metrics": self.current_metrics.copy(),
            "recommendations": self.recommendations.copy(),
            "metric_stats": {
                metric: self.metrics_collector.get_metric_stats(metric, 30)
                for metric in ["cpu_percent", "memory_percent", "api_response_time", "error_rate"]
            }
        }
    
    async def export_performance_data(self, duration_hours: int = 1) -> Dict[str, Any]:
        """Export performance data for analysis"""
        duration_minutes = duration_hours * 60
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "duration_hours": duration_hours,
            "metrics_history": {},
            "summary_stats": {},
            "health_analysis": {
                "current_score": self.health_score,
                "current_status": self.health_status,
                "recommendations": self.recommendations
            }
        }
        
        # Export metric histories
        for metric_name in self.metrics_collector.metrics_history.keys():
            history = self.metrics_collector.get_metric_history(metric_name, duration_minutes)
            export_data["metrics_history"][metric_name] = history
            
            if history:
                export_data["summary_stats"][metric_name] = {
                    "min": min(history),
                    "max": max(history),
                    "avg": statistics.mean(history),
                    "median": statistics.median(history),
                    "std_dev": statistics.stdev(history) if len(history) > 1 else 0
                }
        
        return export_data
    
    def on_unmount(self) -> None:
        """Clean up timers"""
        if self.update_timer:
            self.update_timer.stop()