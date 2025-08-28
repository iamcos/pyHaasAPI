"""
ASCII Chart Rendering Engine

Comprehensive chart rendering system for terminal display with support for
various chart types, real-time updates, and advanced visualization features.
"""

import math
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logging import get_logger


class ChartType(Enum):
    """Chart type enumeration"""
    LINE = "line"
    CANDLESTICK = "candlestick"
    BAR = "bar"
    AREA = "area"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"


class ChartStyle(Enum):
    """Chart styling options"""
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPACT = "compact"


@dataclass
class ChartConfig:
    """Chart configuration settings"""
    width: int = 80
    height: int = 20
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    show_grid: bool = True
    show_legend: bool = True
    show_axes: bool = True
    style: ChartStyle = ChartStyle.STANDARD
    colors: bool = False  # For future color support
    
    # Axis configuration
    x_min: Optional[float] = None
    x_max: Optional[float] = None
    y_min: Optional[float] = None
    y_max: Optional[float] = None
    
    # Formatting
    decimal_places: int = 2
    percentage_format: bool = False
    scientific_notation: bool = False


@dataclass
class DataSeries:
    """Data series for chart rendering"""
    name: str
    data: List[Union[float, Tuple[float, float]]]
    color: str = "default"
    style: str = "solid"  # solid, dashed, dotted
    marker: str = "●"
    
    def __post_init__(self):
        """Validate data series"""
        if not self.data:
            raise ValueError("Data series cannot be empty")


@dataclass
class OHLCData:
    """OHLC (Open, High, Low, Close) data point"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    
    def __post_init__(self):
        """Validate OHLC data"""
        if self.high < max(self.open, self.close):
            raise ValueError("High must be >= max(open, close)")
        if self.low > min(self.open, self.close):
            raise ValueError("Low must be <= min(open, close)")


class ASCIIChartRenderer:
    """Advanced ASCII chart rendering engine"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Character sets for different chart elements
        self.chars = {
            'horizontal': '─',
            'vertical': '│',
            'corner_tl': '┌',
            'corner_tr': '┐',
            'corner_bl': '└',
            'corner_br': '┘',
            'cross': '┼',
            'tee_up': '┴',
            'tee_down': '┬',
            'tee_left': '┤',
            'tee_right': '├',
            'dot': '●',
            'circle': '○',
            'square': '■',
            'diamond': '◆',
            'triangle_up': '▲',
            'triangle_down': '▼',
            'bar_full': '█',
            'bar_three_quarters': '▉',
            'bar_half': '▌',
            'bar_quarter': '▎',
            'shade_light': '░',
            'shade_medium': '▒',
            'shade_dark': '▓'
        }
        
        # Candlestick characters
        self.candle_chars = {
            'body_bull': '█',  # Bullish body
            'body_bear': '▓',  # Bearish body
            'wick': '│',       # Wick
            'doji': '─'        # Doji
        }
    
    def render_line_chart(
        self, 
        series: List[DataSeries], 
        config: ChartConfig,
        x_labels: Optional[List[str]] = None
    ) -> str:
        """Render line chart with multiple series"""
        try:
            if not series:
                return "No data series provided"
            
            # Calculate data bounds
            all_values = []
            max_data_len = 0
            
            for s in series:
                if isinstance(s.data[0], tuple):
                    # X-Y data
                    all_values.extend([point[1] for point in s.data])
                else:
                    # Y data only
                    all_values.extend(s.data)
                max_data_len = max(max_data_len, len(s.data))
            
            if not all_values:
                return "No valid data points"
            
            y_min = config.y_min if config.y_min is not None else min(all_values)
            y_max = config.y_max if config.y_max is not None else max(all_values)
            
            if y_min == y_max:
                return self._render_flat_line(y_min, config)
            
            # Create chart grid
            chart_lines = []
            
            # Title
            if config.title:
                title_line = config.title.center(config.width)
                chart_lines.append(title_line)
                chart_lines.append("")
            
            # Chart area
            chart_height = config.height - (3 if config.show_axes else 0)
            chart_width = config.width - (12 if config.show_axes else 0)
            
            # Render chart content
            for y in range(chart_height - 1, -1, -1):
                line_chars = []
                
                # Y-axis label
                if config.show_axes:
                    current_value = y_min + (y / (chart_height - 1)) * (y_max - y_min)
                    if y == chart_height - 1:
                        y_label = f"{y_max:8.{config.decimal_places}f} ┤"
                    elif y == 0:
                        y_label = f"{y_min:8.{config.decimal_places}f} ┤"
                    elif y == chart_height // 2:
                        mid_val = (y_min + y_max) / 2
                        y_label = f"{mid_val:8.{config.decimal_places}f} ┤"
                    else:
                        y_label = "         │"
                    line_chars.append(y_label)
                
                # Plot data points
                for x in range(chart_width):
                    char = " "
                    
                    # Check each series for data at this position
                    for series_idx, s in enumerate(series):
                        data_x = int((x / chart_width) * len(s.data))
                        if data_x < len(s.data):
                            if isinstance(s.data[data_x], tuple):
                                _, value = s.data[data_x]
                            else:
                                value = s.data[data_x]
                            
                            # Normalize to chart coordinates
                            normalized_y = int(((value - y_min) / (y_max - y_min)) * (chart_height - 1))
                            
                            if normalized_y == y:
                                char = s.marker
                                break
                            elif x > 0 and data_x > 0:
                                # Check for line between points
                                prev_data_x = int(((x - 1) / chart_width) * len(s.data))
                                if prev_data_x < len(s.data):
                                    if isinstance(s.data[prev_data_x], tuple):
                                        _, prev_value = s.data[prev_data_x]
                                    else:
                                        prev_value = s.data[prev_data_x]
                                    
                                    prev_y = int(((prev_value - y_min) / (y_max - y_min)) * (chart_height - 1))
                                    
                                    if (prev_y < y < normalized_y) or (normalized_y < y < prev_y):
                                        char = "│"
                                        break
                    
                    line_chars.append(char)
                
                chart_lines.append("".join(line_chars))
            
            # X-axis
            if config.show_axes:
                x_axis = "         └" + "─" * chart_width
                chart_lines.append(x_axis)
                
                # X-axis labels
                if x_labels:
                    label_line = "          "
                    label_spacing = max(1, chart_width // len(x_labels))
                    for i, label in enumerate(x_labels):
                        if i * label_spacing < chart_width:
                            pos = i * label_spacing
                            if pos + len(label) <= chart_width:
                                label_line = label_line[:10 + pos] + label + label_line[10 + pos + len(label):]
                    chart_lines.append(label_line)
            
            # Legend
            if config.show_legend and len(series) > 1:
                chart_lines.append("")
                legend_parts = []
                for s in series:
                    legend_parts.append(f"{s.marker} {s.name}")
                chart_lines.append("Legend: " + " | ".join(legend_parts))
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            self.logger.error(f"Error rendering line chart: {e}")
            return f"Error rendering chart: {str(e)}"
    
    def render_candlestick_chart(
        self, 
        ohlc_data: List[OHLCData], 
        config: ChartConfig,
        show_volume: bool = False
    ) -> str:
        """Render candlestick chart with OHLC data"""
        try:
            if not ohlc_data:
                return "No OHLC data provided"
            
            # Calculate price range
            all_prices = []
            for candle in ohlc_data:
                all_prices.extend([candle.high, candle.low])
            
            price_min = config.y_min if config.y_min is not None else min(all_prices)
            price_max = config.y_max if config.y_max is not None else max(all_prices)
            
            if price_min == price_max:
                return f"Flat price at {price_min:.{config.decimal_places}f}"
            
            chart_lines = []
            
            # Title
            if config.title:
                chart_lines.append(config.title.center(config.width))
                chart_lines.append("")
            
            # Chart dimensions
            chart_height = config.height - (4 if config.show_axes else 0)
            chart_width = config.width - (12 if config.show_axes else 0)
            
            # Volume chart height if enabled
            volume_height = 0
            if show_volume and any(c.volume for c in ohlc_data):
                volume_height = chart_height // 4
                chart_height -= volume_height
            
            price_range = price_max - price_min
            
            # Render price chart
            for y in range(chart_height - 1, -1, -1):
                line_chars = []
                
                # Y-axis price labels
                if config.show_axes:
                    current_price = price_min + (y / (chart_height - 1)) * price_range
                    if y == chart_height - 1:
                        price_label = f"{price_max:8.{config.decimal_places}f} ┤"
                    elif y == 0:
                        price_label = f"{price_min:8.{config.decimal_places}f} ┤"
                    elif y == chart_height // 2:
                        mid_price = (price_min + price_max) / 2
                        price_label = f"{mid_price:8.{config.decimal_places}f} ┤"
                    else:
                        price_label = "         │"
                    line_chars.append(price_label)
                
                # Render candlesticks
                candles_per_char = max(1, len(ohlc_data) // chart_width)
                
                for x in range(chart_width):
                    candle_idx = int((x / chart_width) * len(ohlc_data))
                    if candle_idx < len(ohlc_data):
                        candle = ohlc_data[candle_idx]
                        char = self._get_candlestick_char(candle, y, chart_height, price_min, price_range)
                        line_chars.append(char)
                    else:
                        line_chars.append(" ")
                
                chart_lines.append("".join(line_chars))
            
            # Volume chart
            if show_volume and volume_height > 0:
                chart_lines.append("")  # Separator
                volumes = [c.volume for c in ohlc_data if c.volume is not None]
                if volumes:
                    max_volume = max(volumes)
                    
                    for y in range(volume_height - 1, -1, -1):
                        line_chars = []
                        
                        if config.show_axes:
                            if y == volume_height - 1:
                                vol_label = f"{max_volume:8.0f} ┤"
                            elif y == 0:
                                vol_label = f"{'0':8} ┤"
                            else:
                                vol_label = "         │"
                            line_chars.append(vol_label)
                        
                        # Render volume bars
                        for x in range(chart_width):
                            candle_idx = int((x / chart_width) * len(ohlc_data))
                            if candle_idx < len(ohlc_data) and ohlc_data[candle_idx].volume:
                                volume = ohlc_data[candle_idx].volume
                                bar_height = int((volume / max_volume) * (volume_height - 1))
                                
                                if y <= bar_height:
                                    line_chars.append("█")
                                else:
                                    line_chars.append(" ")
                            else:
                                line_chars.append(" ")
                        
                        chart_lines.append("".join(line_chars))
            
            # X-axis
            if config.show_axes:
                x_axis = "         └" + "─" * chart_width
                chart_lines.append(x_axis)
                
                # Time labels
                if len(ohlc_data) > 0:
                    label_line = "          "
                    num_labels = min(5, len(ohlc_data))
                    for i in range(num_labels):
                        idx = int((i / (num_labels - 1)) * (len(ohlc_data) - 1)) if num_labels > 1 else 0
                        timestamp = ohlc_data[idx].timestamp
                        time_str = timestamp.strftime("%H:%M")
                        pos = int((i / (num_labels - 1)) * (chart_width - len(time_str))) if num_labels > 1 else 0
                        
                        if pos + len(time_str) <= chart_width:
                            label_line = label_line[:10 + pos] + time_str + label_line[10 + pos + len(time_str):]
                    
                    chart_lines.append(label_line)
            
            return "\n".join(chart_lines)
            
        except Exception as e:
            self.logger.error(f"Error rendering candlestick chart: {e}")
            return f"Error rendering candlestick chart: {str(e)}"
    
    def render_area_chart(
        self, 
        series: List[DataSeries], 
        config: ChartConfig,
        fill_char: str = "▓"
    ) -> str:
        """Render area chart with filled regions"""
        try:
            if not series:
                return "No data series provided"
            
            # Get base line chart
            line_chart = self.render_line_chart(series, config)
            
            # Convert to area chart by filling below lines
            lines = line_chart.split('\n')
            area_lines = []
            
            for line in lines:
                if '┤' in line or '│' in line:  # Chart data line
                    # Find data portion
                    if '┤' in line:
                        prefix = line[:line.index('┤') + 1]
                        data_part = line[line.index('┤') + 1:]
                    else:
                        prefix = line[:line.index('│') + 1]
                        data_part = line[line.index('│') + 1:]
                    
                    # Fill area below data points
                    filled_data = ""
                    fill_active = False
                    
                    for char in data_part:
                        if char in ['●', '○', '■', '◆']:  # Data point markers
                            filled_data += char
                            fill_active = True
                        elif char == '│':  # Line connector
                            filled_data += char
                            fill_active = True
                        elif fill_active and char == ' ':
                            filled_data += fill_char
                        else:
                            filled_data += char
                            if char != ' ':
                                fill_active = False
                    
                    area_lines.append(prefix + filled_data)
                else:
                    area_lines.append(line)
            
            return '\n'.join(area_lines)
            
        except Exception as e:
            self.logger.error(f"Error rendering area chart: {e}")
            return f"Error rendering area chart: {str(e)}"
    
    def render_bar_chart(
        self, 
        values: List[float], 
        labels: List[str], 
        config: ChartConfig,
        orientation: str = "vertical"
    ) -> str:
        """Render bar chart with horizontal or vertical bars"""
        try:
            if not values:
                return "No data provided"
            
            if len(labels) != len(values):
                labels = [f"Bar {i+1}" for i in range(len(values))]
            
            chart_lines = []
            
            # Title
            if config.title:
                chart_lines.append(config.title.center(config.width))
                chart_lines.append("")
            
            if orientation == "vertical":
                return self._render_vertical_bars(values, labels, config, chart_lines)
            else:
                return self._render_horizontal_bars(values, labels, config, chart_lines)
                
        except Exception as e:
            self.logger.error(f"Error rendering bar chart: {e}")
            return f"Error rendering bar chart: {str(e)}"
    
    def render_histogram(
        self, 
        data: List[float], 
        bins: int, 
        config: ChartConfig
    ) -> str:
        """Render histogram with frequency distribution"""
        try:
            if not data:
                return "No data provided"
            
            # Calculate histogram bins
            data_min = min(data)
            data_max = max(data)
            
            if data_min == data_max:
                return f"All values equal: {data_min:.{config.decimal_places}f}"
            
            bin_width = (data_max - data_min) / bins
            bin_counts = [0] * bins
            bin_labels = []
            
            # Count values in each bin
            for value in data:
                bin_idx = min(int((value - data_min) / bin_width), bins - 1)
                bin_counts[bin_idx] += 1
            
            # Create bin labels
            for i in range(bins):
                bin_start = data_min + i * bin_width
                bin_end = data_min + (i + 1) * bin_width
                bin_labels.append(f"{bin_start:.1f}-{bin_end:.1f}")
            
            # Render as horizontal bar chart
            return self.render_bar_chart(bin_counts, bin_labels, config, "horizontal")
            
        except Exception as e:
            self.logger.error(f"Error rendering histogram: {e}")
            return f"Error rendering histogram: {str(e)}"
    
    def render_scatter_plot(
        self, 
        x_data: List[float], 
        y_data: List[float], 
        config: ChartConfig,
        marker: str = "●"
    ) -> str:
        """Render scatter plot"""
        try:
            if len(x_data) != len(y_data):
                return "X and Y data must have same length"
            
            if not x_data:
                return "No data provided"
            
            # Create data series from x,y pairs
            scatter_data = list(zip(x_data, y_data))
            series = [DataSeries("Scatter", scatter_data, marker=marker)]
            
            return self.render_line_chart(series, config)
            
        except Exception as e:
            self.logger.error(f"Error rendering scatter plot: {e}")
            return f"Error rendering scatter plot: {str(e)}"
    
    def _get_candlestick_char(
        self, 
        candle: OHLCData, 
        y_pos: int, 
        chart_height: int, 
        price_min: float, 
        price_range: float
    ) -> str:
        """Get appropriate character for candlestick at given position"""
        # Normalize prices to chart coordinates
        def price_to_y(price: float) -> int:
            return int(((price - price_min) / price_range) * (chart_height - 1))
        
        high_y = price_to_y(candle.high)
        low_y = price_to_y(candle.low)
        open_y = price_to_y(candle.open)
        close_y = price_to_y(candle.close)
        
        body_top = max(open_y, close_y)
        body_bottom = min(open_y, close_y)
        
        # Check if current position intersects with candle
        if low_y <= y_pos <= high_y:
            if body_bottom <= y_pos <= body_top:
                # Inside body
                if candle.close > candle.open:
                    return self.candle_chars['body_bull']  # Bullish
                elif candle.close < candle.open:
                    return self.candle_chars['body_bear']  # Bearish
                else:
                    return self.candle_chars['doji']  # Doji
            else:
                # Wick
                return self.candle_chars['wick']
        
        return " "
    
    def _render_flat_line(self, value: float, config: ChartConfig) -> str:
        """Render flat line for constant values"""
        chart_lines = []
        
        if config.title:
            chart_lines.append(config.title.center(config.width))
            chart_lines.append("")
        
        chart_height = config.height - (3 if config.show_axes else 0)
        chart_width = config.width - (12 if config.show_axes else 0)
        mid_y = chart_height // 2
        
        for y in range(chart_height - 1, -1, -1):
            if y == mid_y:
                line = f"{value:8.{config.decimal_places}f} ┤" + "─" * chart_width
            else:
                line = "         │" + " " * chart_width
            chart_lines.append(line)
        
        if config.show_axes:
            x_axis = "         └" + "─" * chart_width
            chart_lines.append(x_axis)
        
        return "\n".join(chart_lines)
    
    def _render_vertical_bars(
        self, 
        values: List[float], 
        labels: List[str], 
        config: ChartConfig, 
        chart_lines: List[str]
    ) -> str:
        """Render vertical bar chart"""
        max_val = max(values)
        min_val = min(values)
        
        if max_val == min_val:
            chart_lines.append(f"All values equal: {max_val:.{config.decimal_places}f}")
            return "\n".join(chart_lines)
        
        chart_height = config.height - len(chart_lines) - (3 if config.show_axes else 0)
        chart_width = config.width - (12 if config.show_axes else 0)
        
        value_range = max_val - min_val
        
        # Calculate bar width and spacing
        num_bars = len(values)
        bar_width = max(1, chart_width // (num_bars * 2))
        bar_spacing = max(1, (chart_width - num_bars * bar_width) // (num_bars + 1))
        
        # Render bars from top to bottom
        for y in range(chart_height - 1, -1, -1):
            line_chars = []
            
            # Y-axis label
            if config.show_axes:
                current_value = min_val + (y / (chart_height - 1)) * value_range
                if y == chart_height - 1:
                    y_label = f"{max_val:8.{config.decimal_places}f} ┤"
                elif y == 0:
                    y_label = f"{min_val:8.{config.decimal_places}f} ┤"
                else:
                    y_label = "         │"
                line_chars.append(y_label)
            
            # Render bars
            x_pos = 0
            for i, value in enumerate(values):
                # Add spacing
                line_chars.extend([" "] * bar_spacing)
                x_pos += bar_spacing
                
                # Calculate bar height at this y position
                normalized_value = (value - min_val) / value_range
                bar_height = int(normalized_value * (chart_height - 1))
                
                # Draw bar
                for _ in range(bar_width):
                    if y <= bar_height:
                        line_chars.append("█")
                    else:
                        line_chars.append(" ")
                    x_pos += 1
            
            chart_lines.append("".join(line_chars))
        
        # X-axis and labels
        if config.show_axes:
            x_axis = "         └" + "─" * (chart_width)
            chart_lines.append(x_axis)
            
            # Labels
            label_line = ["         ", " "]
            x_pos = bar_spacing
            for i, label in enumerate(labels):
                # Center label under bar
                label_start = x_pos + (bar_width - len(label)) // 2
                if label_start >= 0 and label_start + len(label) <= chart_width:
                    # Extend label_line if needed
                    while len(label_line) <= 10 + label_start + len(label):
                        label_line.append(" ")
                    
                    # Insert label
                    for j, char in enumerate(label):
                        if 10 + label_start + j < len(label_line):
                            label_line[10 + label_start + j] = char
                
                x_pos += bar_width + bar_spacing
            
            chart_lines.append("".join(label_line))
        
        return "\n".join(chart_lines)
    
    def _render_horizontal_bars(
        self, 
        values: List[float], 
        labels: List[str], 
        config: ChartConfig, 
        chart_lines: List[str]
    ) -> str:
        """Render horizontal bar chart"""
        max_val = max(values)
        min_val = min(values)
        
        if max_val == min_val:
            chart_lines.append(f"All values equal: {max_val:.{config.decimal_places}f}")
            return "\n".join(chart_lines)
        
        # Find max label length for alignment
        max_label_len = max(len(str(label)) for label in labels) if labels else 5
        chart_width = config.width - max_label_len - 15  # Space for label, value, and formatting
        
        value_range = max_val - min_val
        
        for i, value in enumerate(values):
            # Label
            label = labels[i] if i < len(labels) else f"Item {i+1}"
            label_part = f"{label:>{max_label_len}} │"
            
            # Bar
            if value_range > 0:
                bar_length = int(((value - min_val) / value_range) * chart_width)
            else:
                bar_length = 0
            
            bar_part = "█" * bar_length
            padding = " " * (chart_width - bar_length)
            value_part = f" {value:.{config.decimal_places}f}"
            
            chart_lines.append(label_part + bar_part + padding + value_part)
        
        return "\n".join(chart_lines)


class RealTimeChartRenderer(ASCIIChartRenderer):
    """Real-time chart renderer with update capabilities"""
    
    def __init__(self, update_callback: Optional[Callable] = None):
        super().__init__()
        self.update_callback = update_callback
        self.chart_cache: Dict[str, str] = {}
        self.data_cache: Dict[str, Any] = {}
    
    def update_chart_data(self, chart_id: str, new_data: Any) -> str:
        """Update chart data and re-render"""
        try:
            # Store new data
            self.data_cache[chart_id] = new_data
            
            # Re-render chart (implementation depends on chart type)
            # This is a simplified version - real implementation would
            # need to track chart type and configuration
            
            if chart_id in self.chart_cache:
                # Update existing chart
                updated_chart = self._re_render_chart(chart_id, new_data)
                self.chart_cache[chart_id] = updated_chart
                
                # Notify callback if provided
                if self.update_callback:
                    self.update_callback(chart_id, updated_chart)
                
                return updated_chart
            
            return "Chart not found"
            
        except Exception as e:
            self.logger.error(f"Error updating chart data: {e}")
            return f"Error updating chart: {str(e)}"
    
    def _re_render_chart(self, chart_id: str, new_data: Any) -> str:
        """Re-render chart with new data"""
        # This would be implemented based on stored chart configuration
        # For now, return a placeholder
        return f"Updated chart {chart_id} with new data"
    
    def register_chart(self, chart_id: str, chart_type: ChartType, config: ChartConfig) -> None:
        """Register a chart for real-time updates"""
        # Store chart configuration for future updates
        self.data_cache[chart_id] = {
            'type': chart_type,
            'config': config,
            'data': None
        }
    
    def get_chart(self, chart_id: str) -> Optional[str]:
        """Get cached chart"""
        return self.chart_cache.get(chart_id)
    
    def clear_cache(self) -> None:
        """Clear all cached charts"""
        self.chart_cache.clear()
        self.data_cache.clear()