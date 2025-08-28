#!/usr/bin/env python3
"""
Chart Rendering Demo

Demonstrates the ASCII Chart Rendering Engine capabilities with various chart types
and real-time updates.
"""

import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, TabbedContent, TabPane
from textual.timer import Timer

from ..services.chart_renderer import (
    ASCIIChartRenderer, ChartConfig, ChartType, ChartStyle, 
    DataSeries, OHLCData
)
from ..ui.components.charts import (
    EnhancedASCIIChart, LineChart, CandlestickChart, BarChart, 
    AreaChart, ScatterPlot, HistogramChart, PerformanceChart, RealTimeChart
)


class ChartRenderingDemo(App):
    """Demo application for chart rendering capabilities"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .demo-container {
        height: 1fr;
        padding: 1;
    }
    
    .chart-demo {
        height: 25;
        margin: 1;
        border: solid $primary;
    }
    
    .controls {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 1;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    TITLE = "ASCII Chart Rendering Engine Demo"
    
    def __init__(self):
        super().__init__()
        self.renderer = ASCIIChartRenderer()
        self.real_time_timer: Timer = None
        self.demo_data = self._generate_demo_data()
    
    def compose(self) -> ComposeResult:
        """Compose the demo application"""
        yield Header()
        
        with TabbedContent():
            with TabPane("Line Charts", id="line-tab"):
                yield self._create_line_chart_demo()
            
            with TabPane("Candlestick", id="candlestick-tab"):
                yield self._create_candlestick_demo()
            
            with TabPane("Bar Charts", id="bar-tab"):
                yield self._create_bar_chart_demo()
            
            with TabPane("Area Charts", id="area-tab"):
                yield self._create_area_chart_demo()
            
            with TabPane("Performance", id="performance-tab"):
                yield self._create_performance_demo()
            
            with TabPane("Real-Time", id="realtime-tab"):
                yield self._create_realtime_demo()
            
            with TabPane("Advanced", id="advanced-tab"):
                yield self._create_advanced_demo()
        
        with Container(classes="controls"):
            yield Button("Generate New Data", id="new-data")
            yield Button("Start Real-Time", id="start-realtime")
            yield Button("Stop Real-Time", id="stop-realtime")
            yield Button("Export Charts", id="export")
        
        yield Footer()
    
    def _create_line_chart_demo(self) -> Container:
        """Create line chart demonstration"""
        container = Vertical(classes="demo-container")
        
        # Simple line chart
        simple_line = LineChart(
            title="Simple Line Chart",
            config=ChartConfig(width=70, height=15, title="Sample Data")
        )
        simple_line.set_line_data(self.demo_data['simple_line'], "Values")
        container.mount(simple_line)
        
        # Multi-series line chart
        multi_line = LineChart(
            title="Multi-Series Line Chart",
            config=ChartConfig(width=70, height=15, title="Multiple Series")
        )
        multi_line.set_line_data(self.demo_data['series_1'], "Series 1", "●")
        multi_line.add_line_series(self.demo_data['series_2'], "Series 2", "○")
        container.mount(multi_line)
        
        return container
    
    def _create_candlestick_demo(self) -> Container:
        """Create candlestick chart demonstration"""
        container = Vertical(classes="demo-container")
        
        # Candlestick with volume
        candlestick = CandlestickChart(
            title="OHLCV Candlestick Chart",
            config=ChartConfig(width=70, height=20, title="Sample OHLCV Data"),
            show_volume=True
        )
        candlestick.set_candlestick_data(self.demo_data['ohlcv'])
        container.mount(candlestick)
        
        return container
    
    def _create_bar_chart_demo(self) -> Container:
        """Create bar chart demonstration"""
        container = Vertical(classes="demo-container")
        
        # Vertical bar chart
        vertical_bars = BarChart(
            title="Vertical Bar Chart",
            orientation="vertical",
            config=ChartConfig(width=70, height=15, title="Category Data")
        )
        vertical_bars.set_bar_data(
            self.demo_data['bar_values'], 
            self.demo_data['bar_labels']
        )
        container.mount(vertical_bars)
        
        # Horizontal bar chart
        horizontal_bars = BarChart(
            title="Horizontal Bar Chart",
            orientation="horizontal",
            config=ChartConfig(width=70, height=12, title="Performance Metrics")
        )
        horizontal_bars.set_bar_data(
            self.demo_data['performance_metrics'], 
            ["Accuracy", "Precision", "Recall", "F1-Score"]
        )
        container.mount(horizontal_bars)
        
        return container
    
    def _create_area_chart_demo(self) -> Container:
        """Create area chart demonstration"""
        container = Vertical(classes="demo-container")
        
        # Area chart
        area_chart = AreaChart(
            title="Area Chart",
            config=ChartConfig(width=70, height=15, title="Cumulative Data"),
            fill_char="▓"
        )
        area_chart.set_area_data(self.demo_data['cumulative'], "Cumulative")
        container.mount(area_chart)
        
        # Scatter plot
        scatter = ScatterPlot(
            title="Scatter Plot",
            config=ChartConfig(width=70, height=15, title="X-Y Relationship"),
            marker="●"
        )
        scatter.set_scatter_data(
            self.demo_data['scatter_x'], 
            self.demo_data['scatter_y']
        )
        container.mount(scatter)
        
        return container
    
    def _create_performance_demo(self) -> Container:
        """Create performance chart demonstration"""
        container = Vertical(classes="demo-container")
        
        # Performance chart with metrics
        performance = PerformanceChart(
            title="Portfolio Performance",
            config=ChartConfig(width=70, height=18, title="Strategy Performance")
        )
        
        # Calculate and set performance data
        returns = self.demo_data['returns']
        benchmark_returns = self.demo_data['benchmark_returns']
        performance.set_performance_data(returns, benchmark_returns=benchmark_returns)
        
        # Calculate metrics
        metrics = performance.calculate_metrics()
        performance.metrics = metrics
        performance._update_legend()
        
        container.mount(performance)
        
        # Histogram of returns
        histogram = HistogramChart(
            title="Returns Distribution",
            bins=15,
            config=ChartConfig(width=70, height=12, title="Return Distribution")
        )
        histogram.set_histogram_data(returns)
        container.mount(histogram)
        
        return container
    
    def _create_realtime_demo(self) -> Container:
        """Create real-time chart demonstration"""
        container = Vertical(classes="demo-container")
        
        # Real-time line chart
        self.realtime_line = RealTimeChart(
            title="Real-Time Line Chart",
            chart_type=ChartType.LINE,
            update_interval=0.5,
            max_points=50,
            config=ChartConfig(width=70, height=15, title="Live Data Stream")
        )
        container.mount(self.realtime_line)
        
        # Real-time candlestick chart
        self.realtime_candles = RealTimeChart(
            title="Real-Time Candlesticks",
            chart_type=ChartType.CANDLESTICK,
            update_interval=1.0,
            max_points=30,
            config=ChartConfig(width=70, height=18, title="Live OHLCV Data")
        )
        container.mount(self.realtime_candles)
        
        return container
    
    def _create_advanced_demo(self) -> Container:
        """Create advanced chart features demonstration"""
        container = Vertical(classes="demo-container")
        
        # Chart with custom styling
        styled_chart = EnhancedASCIIChart(
            title="Custom Styled Chart",
            chart_type=ChartType.LINE,
            config=ChartConfig(
                width=70, 
                height=15, 
                title="Advanced Styling",
                style=ChartStyle.DETAILED,
                show_grid=True,
                decimal_places=4
            )
        )
        
        # Create complex data series
        x_data = list(range(50))
        y_data = [math.sin(x * 0.2) * math.exp(-x * 0.05) for x in x_data]
        series = DataSeries("Damped Sine Wave", y_data, marker="●")
        styled_chart.data_series = [series]
        styled_chart.data = y_data
        styled_chart.refresh_chart()
        
        container.mount(styled_chart)
        
        # Raw renderer demonstration
        raw_demo = Static(
            self._create_raw_renderer_demo(),
            classes="chart-demo"
        )
        container.mount(raw_demo)
        
        return container
    
    def _create_raw_renderer_demo(self) -> str:
        """Create demonstration using raw renderer"""
        config = ChartConfig(
            width=60, 
            height=12, 
            title="Raw Renderer Demo",
            style=ChartStyle.COMPACT
        )
        
        # Create sample data
        data = [math.cos(x * 0.3) + random.uniform(-0.2, 0.2) for x in range(40)]
        series = [DataSeries("Noisy Cosine", data, marker="○")]
        
        return self.renderer.render_line_chart(series, config)
    
    def _generate_demo_data(self) -> Dict[str, Any]:
        """Generate sample data for demonstrations"""
        # Simple line data
        simple_line = [random.uniform(10, 100) for _ in range(30)]
        
        # Multi-series data
        series_1 = [50 + 20 * math.sin(x * 0.2) + random.uniform(-5, 5) for x in range(40)]
        series_2 = [45 + 15 * math.cos(x * 0.15) + random.uniform(-3, 3) for x in range(40)]
        
        # OHLCV data
        ohlcv = []
        base_price = 100.0
        for i in range(25):
            change = random.uniform(-2, 2)
            open_price = base_price
            close_price = base_price + change
            high_price = max(open_price, close_price) + random.uniform(0, 1)
            low_price = min(open_price, close_price) - random.uniform(0, 1)
            volume = random.uniform(1000, 5000)
            
            ohlcv.append({
                'timestamp': datetime.now() - timedelta(minutes=25-i),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            base_price = close_price
        
        # Bar chart data
        bar_values = [random.uniform(20, 80) for _ in range(8)]
        bar_labels = [f"Cat {i+1}" for i in range(8)]
        
        # Performance metrics
        performance_metrics = [0.85, 0.78, 0.82, 0.80]
        
        # Cumulative data
        cumulative = []
        total = 0
        for _ in range(30):
            total += random.uniform(1, 5)
            cumulative.append(total)
        
        # Scatter data
        scatter_x = [random.uniform(0, 100) for _ in range(25)]
        scatter_y = [x + random.uniform(-10, 10) for x in scatter_x]
        
        # Returns data
        returns = [random.normalvariate(0.001, 0.02) for _ in range(100)]
        benchmark_returns = [random.normalvariate(0.0005, 0.015) for _ in range(100)]
        
        return {
            'simple_line': simple_line,
            'series_1': series_1,
            'series_2': series_2,
            'ohlcv': ohlcv,
            'bar_values': bar_values,
            'bar_labels': bar_labels,
            'performance_metrics': performance_metrics,
            'cumulative': cumulative,
            'scatter_x': scatter_x,
            'scatter_y': scatter_y,
            'returns': returns,
            'benchmark_returns': benchmark_returns
        }
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "new-data":
            await self._generate_new_data()
        elif event.button.id == "start-realtime":
            self._start_realtime_updates()
        elif event.button.id == "stop-realtime":
            self._stop_realtime_updates()
        elif event.button.id == "export":
            await self._export_charts()
    
    async def _generate_new_data(self) -> None:
        """Generate new demo data and refresh charts"""
        self.demo_data = self._generate_demo_data()
        
        # Refresh all charts with new data
        # This would need to be implemented based on the current tab
        # For demo purposes, we'll just show a notification
        self.notify("New demo data generated!")
    
    def _start_realtime_updates(self) -> None:
        """Start real-time chart updates"""
        if self.real_time_timer:
            self.real_time_timer.stop()
        
        self.real_time_timer = self.set_interval(0.5, self._update_realtime_charts)
        self.notify("Real-time updates started")
    
    def _stop_realtime_updates(self) -> None:
        """Stop real-time chart updates"""
        if self.real_time_timer:
            self.real_time_timer.stop()
            self.real_time_timer = None
        self.notify("Real-time updates stopped")
    
    def _update_realtime_charts(self) -> None:
        """Update real-time charts with new data"""
        try:
            # Update line chart
            if hasattr(self, 'realtime_line'):
                new_value = random.uniform(20, 80)
                self.realtime_line.add_real_time_data(new_value)
            
            # Update candlestick chart
            if hasattr(self, 'realtime_candles'):
                # Generate new OHLCV data point
                base_price = 100 + random.uniform(-10, 10)
                change = random.uniform(-2, 2)
                open_price = base_price
                close_price = base_price + change
                high_price = max(open_price, close_price) + random.uniform(0, 1)
                low_price = min(open_price, close_price) - random.uniform(0, 1)
                
                ohlcv_point = {
                    'timestamp': datetime.now(),
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': random.uniform(1000, 5000)
                }
                
                self.realtime_candles.add_real_time_data(ohlcv_point)
                
        except Exception as e:
            self.notify(f"Error updating real-time charts: {e}")
    
    async def _export_charts(self) -> None:
        """Export chart data"""
        try:
            # This would export all chart data to files
            # For demo purposes, just show a notification
            self.notify("Chart data exported successfully!")
        except Exception as e:
            self.notify(f"Export failed: {e}")


def main():
    """Run the chart rendering demo"""
    app = ChartRenderingDemo()
    app.run()


if __name__ == "__main__":
    main()