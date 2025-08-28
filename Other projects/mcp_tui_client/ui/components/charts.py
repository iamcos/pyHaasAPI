"""
Chart Components

Enhanced ASCII-based chart rendering components for terminal display with
real-time updates and advanced visualization capabilities.
"""

from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import math
import asyncio

from textual.widget import Widget
from textual.widgets import Static, Label
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.timer import Timer

from ..services.chart_renderer import (
    ASCIIChartRenderer, RealTimeChartRenderer, ChartConfig, ChartType, 
    ChartStyle, DataSeries, OHLCData
)
from ..utils.logging import get_logger


class EnhancedASCIIChart(Container):
    """Enhanced ASCII chart component with advanced rendering capabilities"""
    
    DEFAULT_CSS = """
    EnhancedASCIIChart {
        height: auto;
        min-height: 10;
        border: solid $accent;
        padding: 1;
    }
    
    EnhancedASCIIChart .chart-title {
        dock: top;
        height: 1;
        text-align: center;
        background: $accent;
        color: $text;
    }
    
    EnhancedASCIIChart .chart-content {
        height: 1fr;
        padding: 1;
        overflow: hidden;
    }
    
    EnhancedASCIIChart .chart-legend {
        dock: bottom;
        height: 2;
        background: $surface;
        padding: 0 1;
    }
    
    EnhancedASCIIChart .chart-status {
        dock: bottom;
        height: 1;
        background: $primary;
        color: $text;
        text-align: right;
        padding: 0 1;
    }
    """
    
    title = reactive("")
    
    def __init__(
        self,
        title: str = "Chart",
        chart_type: ChartType = ChartType.LINE,
        config: Optional[ChartConfig] = None,
        real_time: bool = False,
        update_interval: float = 1.0,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.logger = get_logger(__name__)
        
        # Chart configuration
        self.title = title
        self.chart_type = chart_type
        self.config = config or ChartConfig(
            width=80, 
            height=20, 
            title=title,
            style=ChartStyle.STANDARD
        )
        
        # Real-time settings
        self.real_time = real_time
        self.update_interval = update_interval
        self.update_timer: Optional[Timer] = None
        
        # Data and rendering
        self.data: List[Any] = []
        self.data_series: List[DataSeries] = []
        self.ohlc_data: List[OHLCData] = []
        self.chart_content = ""
        self.last_update = datetime.now()
        
        # Renderers
        if real_time:
            self.renderer = RealTimeChartRenderer(self._on_chart_update)
        else:
            self.renderer = ASCIIChartRenderer()
        
        # Callbacks
        self.on_data_update: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def compose(self) -> ComposeResult:
        """Compose enhanced chart layout"""
        yield Label(self.title, classes="chart-title")
        yield Container(classes="chart-content", id="chart-content")
        if self.config.show_legend:
            yield Container(classes="chart-legend", id="chart-legend")
        if self.real_time:
            yield Label("", classes="chart-status", id="chart-status")
    
    def on_mount(self) -> None:
        """Initialize chart when mounted"""
        if self.real_time:
            self._start_real_time_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def set_data(self, data: List[Any]) -> None:
        """Set chart data and refresh display"""
        try:
            self.data = data
            self.last_update = datetime.now()
            
            # Convert data based on chart type
            if self.chart_type == ChartType.LINE:
                if isinstance(data[0], (int, float)):
                    self.data_series = [DataSeries("Data", data)]
                elif isinstance(data[0], dict) and 'name' in data[0]:
                    self.data_series = [DataSeries(d['name'], d['data']) for d in data]
            
            self.refresh_chart()
            
            # Notify callback
            if self.on_data_update:
                self.on_data_update(data)
                
        except Exception as e:
            self.logger.error(f"Error setting chart data: {e}")
            if self.on_error:
                self.on_error(e)
    
    def set_ohlcv_data(self, ohlcv_data: List[Dict[str, Any]]) -> None:
        """Set OHLCV data for candlestick charts"""
        try:
            self.ohlc_data = []
            for item in ohlcv_data:
                ohlc = OHLCData(
                    timestamp=item.get('timestamp', datetime.now()),
                    open=float(item['open']),
                    high=float(item['high']),
                    low=float(item['low']),
                    close=float(item['close']),
                    volume=float(item.get('volume', 0)) if item.get('volume') else None
                )
                self.ohlc_data.append(ohlc)
            
            self.last_update = datetime.now()
            self.refresh_chart()
            
        except Exception as e:
            self.logger.error(f"Error setting OHLCV data: {e}")
            if self.on_error:
                self.on_error(e)
    
    def add_data_point(self, data_point: Any) -> None:
        """Add single data point (for real-time updates)"""
        try:
            if self.chart_type == ChartType.CANDLESTICK:
                if isinstance(data_point, dict):
                    ohlc = OHLCData(
                        timestamp=data_point.get('timestamp', datetime.now()),
                        open=float(data_point['open']),
                        high=float(data_point['high']),
                        low=float(data_point['low']),
                        close=float(data_point['close']),
                        volume=float(data_point.get('volume', 0)) if data_point.get('volume') else None
                    )
                    self.ohlc_data.append(ohlc)
                    
                    # Keep only recent data for performance
                    max_points = self.config.width * 2
                    if len(self.ohlc_data) > max_points:
                        self.ohlc_data = self.ohlc_data[-max_points:]
            else:
                self.data.append(data_point)
                
                # Keep only recent data for performance
                max_points = self.config.width * 2
                if len(self.data) > max_points:
                    self.data = self.data[-max_points:]
                    if self.data_series:
                        for series in self.data_series:
                            if len(series.data) > max_points:
                                series.data = series.data[-max_points:]
            
            self.last_update = datetime.now()
            self.refresh_chart()
            
        except Exception as e:
            self.logger.error(f"Error adding data point: {e}")
            if self.on_error:
                self.on_error(e)
    
    def refresh_chart(self) -> None:
        """Refresh chart display using appropriate renderer"""
        try:
            if self.chart_type == ChartType.LINE:
                if self.data_series:
                    self.chart_content = self.renderer.render_line_chart(
                        self.data_series, self.config
                    )
                else:
                    self.chart_content = "No data series available"
                    
            elif self.chart_type == ChartType.CANDLESTICK:
                if self.ohlc_data:
                    self.chart_content = self.renderer.render_candlestick_chart(
                        self.ohlc_data, self.config, show_volume=True
                    )
                else:
                    self.chart_content = "No OHLC data available"
                    
            elif self.chart_type == ChartType.AREA:
                if self.data_series:
                    self.chart_content = self.renderer.render_area_chart(
                        self.data_series, self.config
                    )
                else:
                    self.chart_content = "No data series available"
                    
            elif self.chart_type == ChartType.BAR:
                if self.data:
                    labels = [f"Item {i+1}" for i in range(len(self.data))]
                    self.chart_content = self.renderer.render_bar_chart(
                        self.data, labels, self.config
                    )
                else:
                    self.chart_content = "No data available"
            else:
                self.chart_content = f"Chart type {self.chart_type.value} not implemented"
            
            self._update_display()
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error refreshing chart: {e}")
            self.chart_content = f"Error rendering chart: {str(e)}"
            self._update_display()
    
    def _update_display(self) -> None:
        """Update the chart display"""
        try:
            content_container = self.query_one("#chart-content")
            content_container.remove_children()
            content_container.mount(Static(self.chart_content))
        except Exception as e:
            self.logger.error(f"Error updating chart display: {e}")
    
    def _update_status(self) -> None:
        """Update status display for real-time charts"""
        if not self.real_time:
            return
            
        try:
            status_label = self.query_one("#chart-status", Label)
            data_count = len(self.ohlc_data) if self.chart_type == ChartType.CANDLESTICK else len(self.data)
            status_text = f"Points: {data_count} | Updated: {self.last_update.strftime('%H:%M:%S')}"
            status_label.update(status_text)
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
    
    def _start_real_time_updates(self) -> None:
        """Start real-time update timer"""
        if self.update_timer:
            self.update_timer.stop()
        
        self.update_timer = self.set_interval(
            self.update_interval, 
            self._real_time_update_callback
        )
    
    def _real_time_update_callback(self) -> None:
        """Callback for real-time updates"""
        # This would be overridden or connected to data source
        # For now, just refresh the display
        self._update_status()
    
    def _on_chart_update(self, chart_id: str, updated_chart: str) -> None:
        """Callback for chart updates from real-time renderer"""
        self.chart_content = updated_chart
        self._update_display()
    
    def watch_title(self, new_title: str) -> None:
        """React to title changes"""
        try:
            title_label = self.query_one(".chart-title", Label)
            title_label.update(new_title)
            self.config.title = new_title
        except Exception as e:
            self.logger.error(f"Error updating title: {e}")
    
    def set_config(self, config: ChartConfig) -> None:
        """Update chart configuration"""
        self.config = config
        self.refresh_chart()
    
    def export_chart_data(self) -> Dict[str, Any]:
        """Export chart data for analysis or storage"""
        return {
            'type': self.chart_type.value,
            'title': self.title,
            'data': self.data,
            'data_series': [{'name': s.name, 'data': s.data} for s in self.data_series],
            'ohlc_data': [
                {
                    'timestamp': ohlc.timestamp.isoformat(),
                    'open': ohlc.open,
                    'high': ohlc.high,
                    'low': ohlc.low,
                    'close': ohlc.close,
                    'volume': ohlc.volume
                } for ohlc in self.ohlc_data
            ],
            'last_update': self.last_update.isoformat(),
            'config': {
                'width': self.config.width,
                'height': self.config.height,
                'style': self.config.style.value
            }
        }


# Backward compatibility - keep original class name
class ASCIIChart(EnhancedASCIIChart):
    """Backward compatibility wrapper"""
    
    def __init__(self, **kwargs):
        # Convert old parameters to new format
        if 'chart_width' in kwargs:
            kwargs.setdefault('config', ChartConfig()).width = kwargs.pop('chart_width')
        if 'chart_height' in kwargs:
            kwargs.setdefault('config', ChartConfig()).height = kwargs.pop('chart_height')
        
        super().__init__(**kwargs)


class LineChart(EnhancedASCIIChart):
    """Enhanced line chart component"""
    
    def __init__(self, **kwargs):
        kwargs['chart_type'] = ChartType.LINE
        super().__init__(**kwargs)
        self.min_value: Optional[float] = None
        self.max_value: Optional[float] = None
    
    def set_line_data(
        self, 
        data: List[float], 
        name: str = "Line", 
        marker: str = "●"
    ) -> None:
        """Set line chart data with optional styling"""
        series = DataSeries(name, data, marker=marker)
        self.data_series = [series]
        self.data = data
        self.refresh_chart()
    
    def add_line_series(
        self, 
        data: List[float], 
        name: str, 
        marker: str = "○"
    ) -> None:
        """Add additional line series to chart"""
        series = DataSeries(name, data, marker=marker)
        self.data_series.append(series)
        self.refresh_chart()
    
    def set_value_range(self, min_val: float, max_val: float) -> None:
        """Set explicit value range for Y-axis"""
        self.min_value = min_val
        self.max_value = max_val
        self.config.y_min = min_val
        self.config.y_max = max_val
        self.refresh_chart()


class CandlestickChart(EnhancedASCIIChart):
    """Enhanced candlestick chart for OHLCV data"""
    
    def __init__(self, show_volume: bool = True, **kwargs):
        kwargs['chart_type'] = ChartType.CANDLESTICK
        super().__init__(**kwargs)
        self.show_volume = show_volume
        self.time_labels: List[str] = []
    
    def set_candlestick_data(
        self, 
        ohlcv_data: List[Dict[str, Any]], 
        time_labels: List[str] = None
    ) -> None:
        """Set OHLCV data for candlestick chart"""
        try:
            self.set_ohlcv_data(ohlcv_data)
            self.time_labels = time_labels or []
        except Exception as e:
            self.logger.error(f"Error setting candlestick data: {e}")
            if self.on_error:
                self.on_error(e)
    
    def add_candlestick_data(self, ohlcv_point: Dict[str, Any]) -> None:
        """Add single OHLCV data point for real-time updates"""
        self.add_data_point(ohlcv_point)
    
    def set_volume_display(self, show_volume: bool) -> None:
        """Toggle volume display"""
        self.show_volume = show_volume
        self.refresh_chart()
    
    def refresh_chart(self) -> None:
        """Override to include volume display setting"""
        try:
            if self.ohlc_data:
                self.chart_content = self.renderer.render_candlestick_chart(
                    self.ohlc_data, self.config, show_volume=self.show_volume
                )
            else:
                self.chart_content = "No OHLC data available"
            
            self._update_display()
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error refreshing candlestick chart: {e}")
            self.chart_content = f"Error rendering chart: {str(e)}"
            self._update_display()


class PerformanceChart(LineChart):
    """Performance chart with additional metrics display"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.metrics: Dict[str, float] = {}
        self.config.percentage_format = True
    
    def set_performance_data(
        self, 
        returns: List[float], 
        metrics: Dict[str, float] = None,
        benchmark_returns: List[float] = None
    ) -> None:
        """Set performance data with optional metrics and benchmark"""
        try:
            # Convert returns to cumulative performance
            cumulative = [1.0]  # Start at 100%
            for ret in returns:
                cumulative.append(cumulative[-1] * (1 + ret))
            
            # Create main performance series
            self.data_series = [DataSeries("Performance", cumulative, marker="●")]
            
            # Add benchmark if provided
            if benchmark_returns:
                benchmark_cumulative = [1.0]
                for ret in benchmark_returns:
                    benchmark_cumulative.append(benchmark_cumulative[-1] * (1 + ret))
                self.data_series.append(DataSeries("Benchmark", benchmark_cumulative, marker="○"))
            
            self.data = cumulative
            self.metrics = metrics or {}
            self.refresh_chart()
            self._update_legend()
            
        except Exception as e:
            self.logger.error(f"Error setting performance data: {e}")
            if self.on_error:
                self.on_error(e)
    
    def add_performance_point(self, return_value: float, benchmark_return: float = None) -> None:
        """Add single performance data point"""
        try:
            if self.data:
                new_cumulative = self.data[-1] * (1 + return_value)
                self.add_data_point(new_cumulative)
                
                # Update main series
                if self.data_series:
                    self.data_series[0].data.append(new_cumulative)
                    
                    # Update benchmark if provided
                    if benchmark_return is not None and len(self.data_series) > 1:
                        benchmark_data = self.data_series[1].data
                        if benchmark_data:
                            new_benchmark = benchmark_data[-1] * (1 + benchmark_return)
                            self.data_series[1].data.append(new_benchmark)
                        
        except Exception as e:
            self.logger.error(f"Error adding performance point: {e}")
    
    def _update_legend(self) -> None:
        """Update legend with performance metrics"""
        if not self.config.show_legend or not self.metrics:
            return
        
        try:
            legend_container = self.query_one("#chart-legend")
            legend_container.remove_children()
            
            legend_text = []
            for key, value in self.metrics.items():
                if isinstance(value, float):
                    if 'return' in key.lower() or 'ratio' in key.lower():
                        legend_text.append(f"{key}: {value:.2%}")
                    else:
                        legend_text.append(f"{key}: {value:.4f}")
                else:
                    legend_text.append(f"{key}: {value}")
            
            legend_container.mount(Label(" | ".join(legend_text)))
        except Exception as e:
            self.logger.error(f"Error updating legend: {e}")
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate performance metrics from current data"""
        if not self.data or len(self.data) < 2:
            return {}
        
        try:
            # Calculate returns
            returns = []
            for i in range(1, len(self.data)):
                ret = (self.data[i] / self.data[i-1]) - 1
                returns.append(ret)
            
            if not returns:
                return {}
            
            # Calculate metrics
            total_return = (self.data[-1] / self.data[0]) - 1
            avg_return = statistics.mean(returns)
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0
            
            # Sharpe ratio (assuming risk-free rate of 0)
            sharpe_ratio = avg_return / volatility if volatility > 0 else 0
            
            # Maximum drawdown
            peak = self.data[0]
            max_drawdown = 0
            for value in self.data:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            metrics = {
                'Total Return': total_return,
                'Avg Return': avg_return,
                'Volatility': volatility,
                'Sharpe Ratio': sharpe_ratio,
                'Max Drawdown': max_drawdown
            }
            
            self.metrics = metrics
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            return {}


class BarChart(EnhancedASCIIChart):
    """Enhanced bar chart component"""
    
    def __init__(self, orientation: str = "vertical", **kwargs):
        kwargs['chart_type'] = ChartType.BAR
        super().__init__(**kwargs)
        self.orientation = orientation  # "vertical" or "horizontal"
        self.labels: List[str] = []
    
    def set_bar_data(self, values: List[float], labels: List[str] = None) -> None:
        """Set bar chart data"""
        self.data = values
        self.labels = labels or [f"Bar {i+1}" for i in range(len(values))]
        self.refresh_chart()
    
    def refresh_chart(self) -> None:
        """Override to use orientation setting"""
        try:
            if self.data:
                self.chart_content = self.renderer.render_bar_chart(
                    self.data, self.labels, self.config, self.orientation
                )
            else:
                self.chart_content = "No data available"
            
            self._update_display()
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error refreshing bar chart: {e}")
            self.chart_content = f"Error rendering chart: {str(e)}"
            self._update_display()


class AreaChart(EnhancedASCIIChart):
    """Area chart component with filled regions"""
    
    def __init__(self, fill_char: str = "▓", **kwargs):
        kwargs['chart_type'] = ChartType.AREA
        super().__init__(**kwargs)
        self.fill_char = fill_char
    
    def set_area_data(
        self, 
        data: List[float], 
        name: str = "Area", 
        fill_char: str = None
    ) -> None:
        """Set area chart data"""
        if fill_char:
            self.fill_char = fill_char
        
        series = DataSeries(name, data)
        self.data_series = [series]
        self.data = data
        self.refresh_chart()
    
    def refresh_chart(self) -> None:
        """Override to use fill character"""
        try:
            if self.data_series:
                self.chart_content = self.renderer.render_area_chart(
                    self.data_series, self.config, self.fill_char
                )
            else:
                self.chart_content = "No data series available"
            
            self._update_display()
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error refreshing area chart: {e}")
            self.chart_content = f"Error rendering chart: {str(e)}"
            self._update_display()


class ScatterPlot(EnhancedASCIIChart):
    """Scatter plot component"""
    
    def __init__(self, marker: str = "●", **kwargs):
        kwargs['chart_type'] = ChartType.SCATTER
        super().__init__(**kwargs)
        self.marker = marker
        self.x_data: List[float] = []
        self.y_data: List[float] = []
    
    def set_scatter_data(
        self, 
        x_data: List[float], 
        y_data: List[float], 
        marker: str = None
    ) -> None:
        """Set scatter plot data"""
        if len(x_data) != len(y_data):
            raise ValueError("X and Y data must have same length")
        
        if marker:
            self.marker = marker
        
        self.x_data = x_data
        self.y_data = y_data
        self.refresh_chart()
    
    def refresh_chart(self) -> None:
        """Override to render scatter plot"""
        try:
            if self.x_data and self.y_data:
                self.chart_content = self.renderer.render_scatter_plot(
                    self.x_data, self.y_data, self.config, self.marker
                )
            else:
                self.chart_content = "No scatter data available"
            
            self._update_display()
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error refreshing scatter plot: {e}")
            self.chart_content = f"Error rendering chart: {str(e)}"
            self._update_display()


class HistogramChart(EnhancedASCIIChart):
    """Histogram chart component"""
    
    def __init__(self, bins: int = 10, **kwargs):
        kwargs['chart_type'] = ChartType.HISTOGRAM
        super().__init__(**kwargs)
        self.bins = bins
    
    def set_histogram_data(self, data: List[float], bins: int = None) -> None:
        """Set histogram data"""
        if bins:
            self.bins = bins
        
        self.data = data
        self.refresh_chart()
    
    def refresh_chart(self) -> None:
        """Override to render histogram"""
        try:
            if self.data:
                self.chart_content = self.renderer.render_histogram(
                    self.data, self.bins, self.config
                )
            else:
                self.chart_content = "No data available"
            
            self._update_display()
            self._update_status()
            
        except Exception as e:
            self.logger.error(f"Error refreshing histogram: {e}")
            self.chart_content = f"Error rendering chart: {str(e)}"
            self._update_display()


class RealTimeChart(EnhancedASCIIChart):
    """Real-time chart with automatic updates"""
    
    def __init__(
        self, 
        chart_type: ChartType = ChartType.LINE,
        update_interval: float = 1.0,
        max_points: int = 100,
        **kwargs
    ):
        kwargs['chart_type'] = chart_type
        kwargs['real_time'] = True
        kwargs['update_interval'] = update_interval
        super().__init__(**kwargs)
        
        self.max_points = max_points
        self.data_buffer: List[Any] = []
        self.auto_scroll = True
    
    def add_real_time_data(self, data_point: Any) -> None:
        """Add data point for real-time display"""
        self.data_buffer.append(data_point)
        
        # Keep buffer size manageable
        if len(self.data_buffer) > self.max_points:
            self.data_buffer = self.data_buffer[-self.max_points:]
        
        # Update chart data
        if self.chart_type == ChartType.CANDLESTICK:
            self.add_data_point(data_point)
        else:
            self.data = self.data_buffer.copy()
            if self.data_series:
                self.data_series[0].data = self.data_buffer.copy()
            self.refresh_chart()
    
    def set_auto_scroll(self, enabled: bool) -> None:
        """Enable/disable auto-scrolling"""
        self.auto_scroll = enabled
    
    def clear_data(self) -> None:
        """Clear all data"""
        self.data_buffer.clear()
        self.data.clear()
        if self.data_series:
            for series in self.data_series:
                series.data.clear()
        if self.ohlc_data:
            self.ohlc_data.clear()
        self.refresh_chart()


class MultiChart(Container):
    """Container for multiple charts with synchronized axes"""
    
    DEFAULT_CSS = """
    MultiChart {
        height: auto;
        border: solid $accent;
        padding: 1;
    }
    
    MultiChart .multi-chart-title {
        dock: top;
        height: 1;
        text-align: center;
        background: $accent;
        color: $text;
    }
    """
    
    def __init__(
        self, 
        title: str = "Multi Chart",
        sync_axes: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.logger = get_logger(__name__)
        self.title = title
        self.sync_axes = sync_axes
        self.charts: List[EnhancedASCIIChart] = []
        self.shared_config: Optional[ChartConfig] = None
    
    def compose(self) -> ComposeResult:
        """Compose multi-chart layout"""
        yield Label(self.title, classes="multi-chart-title")
        yield Container(id="charts-container")
    
    def add_chart(self, chart: EnhancedASCIIChart) -> None:
        """Add chart to multi-chart display"""
        try:
            self.charts.append(chart)
            
            # Sync axes if enabled
            if self.sync_axes and self.shared_config:
                chart.set_config(self.shared_config)
            
            # Mount chart
            charts_container = self.query_one("#charts-container")
            charts_container.mount(chart)
            
        except Exception as e:
            self.logger.error(f"Error adding chart: {e}")
    
    def set_shared_config(self, config: ChartConfig) -> None:
        """Set shared configuration for all charts"""
        self.shared_config = config
        
        if self.sync_axes:
            for chart in self.charts:
                chart.set_config(config)
    
    def sync_chart_axes(self) -> None:
        """Synchronize axes across all charts"""
        if not self.charts:
            return
        
        try:
            # Find global min/max values
            all_values = []
            for chart in self.charts:
                if chart.data:
                    if isinstance(chart.data[0], (int, float)):
                        all_values.extend(chart.data)
                    elif hasattr(chart, 'ohlc_data') and chart.ohlc_data:
                        for ohlc in chart.ohlc_data:
                            all_values.extend([ohlc.high, ohlc.low])
            
            if all_values:
                global_min = min(all_values)
                global_max = max(all_values)
                
                # Update all chart configs
                for chart in self.charts:
                    chart.config.y_min = global_min
                    chart.config.y_max = global_max
                    chart.refresh_chart()
                    
        except Exception as e:
            self.logger.error(f"Error syncing chart axes: {e}")
    
    def export_all_charts(self) -> Dict[str, Any]:
        """Export data from all charts"""
        export_data = {
            'title': self.title,
            'sync_axes': self.sync_axes,
            'charts': []
        }
        
        for i, chart in enumerate(self.charts):
            chart_data = chart.export_chart_data()
            chart_data['index'] = i
            export_data['charts'].append(chart_data)
        
        return export_data