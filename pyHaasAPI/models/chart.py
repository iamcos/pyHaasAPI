"""
Chart models for pyHaasAPI v2

Provides data models for chart data, plots, axes, and visualizations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HaasChartAxisLabel(BaseModel):
    """Chart axis label"""
    text: Optional[str] = Field(alias="Text", default=None, description="Label text")
    value: Optional[float] = Field(alias="Value", default=None, description="Label value")
    color: Optional[str] = Field(alias="Color", default=None, description="Label color")
    text_color: Optional[str] = Field(alias="TextColor", default=None, description="Text color")
    
    class Config:
        populate_by_name = True


class HaasChartAxis(BaseModel):
    """Chart axis"""
    type: Optional[str] = Field(alias="Type", default=None, description="Axis type")
    side: Optional[str] = Field(alias="Side", default=None, description="Axis side")
    is_visible: bool = Field(alias="IsVisible", default=True, description="Whether axis is visible")
    labels: Optional[List[HaasChartAxisLabel]] = Field(alias="Labels", default=None, description="Axis labels")
    
    class Config:
        populate_by_name = True


class HaasChartCandle(BaseModel):
    """Chart candle data"""
    open: float = Field(alias="O", description="Open price")
    high: float = Field(alias="H", description="High price")
    low: float = Field(alias="L", description="Low price")
    close: float = Field(alias="C", description="Close price")
    volume: float = Field(alias="V", description="Volume")
    timestamp: Optional[int] = Field(alias="M", default=None, description="Timestamp")
    
    class Config:
        populate_by_name = True


class HaasChartColorScheme(BaseModel):
    """Chart color scheme"""
    font: Optional[str] = Field(alias="Font", default=None, description="Font color")
    axis: Optional[str] = Field(alias="Axis", default=None, description="Axis color")
    grid: Optional[str] = Field(alias="Grid", default=None, description="Grid color")
    text: Optional[str] = Field(alias="Text", default=None, description="Text color")
    background: Optional[str] = Field(alias="Background", default=None, description="Background color")
    price_ghost_line: Optional[str] = Field(alias="PriceGhostLine", default=None, description="Price ghost line color")
    volume_ghost_line: Optional[str] = Field(alias="VolumeGhostLine", default=None, description="Volume ghost line color")
    
    class Config:
        populate_by_name = True


class HaasChartPricePlotColorScheme(BaseModel):
    """Chart price plot color scheme"""
    up: Optional[str] = Field(alias="Up", default=None, description="Up candle color")
    up_fill: Optional[str] = Field(alias="UpFill", default=None, description="Up candle fill color")
    down: Optional[str] = Field(alias="Down", default=None, description="Down candle color")
    down_fill: Optional[str] = Field(alias="DownFill", default=None, description="Down candle fill color")
    marked: Optional[str] = Field(alias="Marked", default=None, description="Marked candle color")
    marked_fill: Optional[str] = Field(alias="MarkedFill", default=None, description="Marked candle fill color")
    
    class Config:
        populate_by_name = True


class HaasChartDataLine(BaseModel):
    """Chart data line"""
    guid: Optional[str] = Field(alias="Guid", default=None, description="Line GUID")
    name: Optional[str] = Field(alias="Name", default=None, description="Line name")
    interval: Optional[int] = Field(alias="Interval", default=None, description="Interval")
    color: Optional[str] = Field(alias="Color", default=None, description="Line color")
    width: Optional[float] = Field(alias="Width", default=None, description="Line width")
    type: Optional[str] = Field(alias="Type", default=None, description="Line type")
    style: Optional[str] = Field(alias="Style", default=None, description="Line style")
    decoration: Optional[str] = Field(alias="Decoration", default=None, description="Line decoration")
    side: Optional[str] = Field(alias="Side", default=None, description="Line side")
    line_shape_type: Optional[str] = Field(alias="LineShapeType", default=None, description="Line shape type")
    visible: bool = Field(alias="Visible", default=True, description="Whether line is visible")
    behind: bool = Field(alias="Behind", default=False, description="Whether line is behind")
    ignore_on_axis: bool = Field(alias="IgnoreOnAxis", default=False, description="Whether to ignore on axis")
    draw_trailing_line: bool = Field(alias="DrawTrailingLine", default=False, description="Whether to draw trailing line")
    fixed_value: Optional[float] = Field(alias="FixedValue", default=None, description="Fixed value")
    connected_lines: Optional[List[str]] = Field(alias="ConnectedLines", default=None, description="Connected lines")
    data_sets: Optional[List[Any]] = Field(alias="DataSets", default=None, description="Data sets")
    data_points: Optional[List[Any]] = Field(alias="DataPoints", default=None, description="Data points")
    
    class Config:
        populate_by_name = True


class HaasChartShapes(BaseModel):
    """Chart shapes"""
    type: Optional[str] = Field(alias="Type", default=None, description="Shape type")
    above_candle: bool = Field(alias="AboveCandle", default=False, description="Whether shape is above candle")
    text_color: Optional[str] = Field(alias="TextColor", default=None, description="Text color")
    color: Optional[str] = Field(alias="Color", default=None, description="Shape color")
    text: Optional[str] = Field(alias="Text", default=None, description="Shape text")
    size: Optional[float] = Field(alias="Size", default=None, description="Shape size")
    
    class Config:
        populate_by_name = True


class HaasChartAnnotations(BaseModel):
    """Chart annotations"""
    name: Optional[str] = Field(alias="Name", default=None, description="Annotation name")
    type: Optional[str] = Field(alias="Type", default=None, description="Annotation type")
    decoration: Optional[str] = Field(alias="Decoration", default=None, description="Annotation decoration")
    side: Optional[str] = Field(alias="Side", default=None, description="Annotation side")
    colors: Optional[List[str]] = Field(alias="Colors", default=None, description="Annotation colors")
    values: Optional[List[float]] = Field(alias="Values", default=None, description="Annotation values")
    timestamps: Optional[List[int]] = Field(alias="Timestamps", default=None, description="Annotation timestamps")
    
    class Config:
        populate_by_name = True


class HaasChartPricePlot(BaseModel):
    """Chart price plot"""
    market: Optional[str] = Field(alias="Market", default=None, description="Market")
    interval: Optional[int] = Field(alias="Interval", default=None, description="Interval")
    candles: Optional[List[HaasChartCandle]] = Field(alias="Candles", default=None, description="Candles")
    colors: Optional[HaasChartPricePlotColorScheme] = Field(alias="Colors", default=None, description="Color scheme")
    style: Optional[str] = Field(alias="Style", default=None, description="Plot style")
    side: Optional[str] = Field(alias="Side", default=None, description="Plot side")
    
    class Config:
        populate_by_name = True


class HaasChartPlot(BaseModel):
    """Chart plot"""
    plot_id: Optional[str] = Field(alias="PlotId", default=None, description="Plot ID")
    plot_index: Optional[int] = Field(alias="PlotIndex", default=None, description="Plot index")
    title: Optional[str] = Field(alias="Title", default=None, description="Plot title")
    height: Optional[float] = Field(alias="Height", default=None, description="Plot height")
    is_signal_plot: bool = Field(alias="IsSignalPlot", default=False, description="Whether this is a signal plot")
    right_axis: Optional[HaasChartAxis] = Field(alias="RightAxis", default=None, description="Right axis")
    left_axis: Optional[HaasChartAxis] = Field(alias="LeftAxis", default=None, description="Left axis")
    price_plot: Optional[HaasChartPricePlot] = Field(alias="PricePlot", default=None, description="Price plot")
    data_lines: Optional[List[HaasChartDataLine]] = Field(alias="DataLines", default=None, description="Data lines")
    shapes: Optional[List[HaasChartShapes]] = Field(alias="Shapes", default=None, description="Shapes")
    annotations: Optional[List[HaasChartAnnotations]] = Field(alias="Annotations", default=None, description="Annotations")
    trade_annotations: Optional[List[HaasChartAnnotations]] = Field(alias="TradeAnnotations", default=None, description="Trade annotations")
    
    class Config:
        populate_by_name = True


class HaasChartContainer(BaseModel):
    """Chart container"""
    guid: Optional[str] = Field(alias="Guid", default=None, description="Container GUID")
    interval: Optional[int] = Field(alias="Interval", default=None, description="Interval")
    plots: Optional[List[HaasChartPlot]] = Field(alias="Plots", default=None, description="Plots")
    colors: Optional[HaasChartColorScheme] = Field(alias="Colors", default=None, description="Color scheme")
    is_last_partition: bool = Field(alias="IsLastPartition", default=False, description="Whether this is the last partition")
    status: Optional[str] = Field(alias="Status", default=None, description="Status")
    
    class Config:
        populate_by_name = True


class HaasChartTradeMarket(BaseModel):
    """Chart trade market information"""
    unix: Optional[int] = Field(alias="Unix", default=None, description="Unix timestamp")
    price: Optional[float] = Field(alias="Price", default=None, description="Price")
    color: Optional[str] = Field(alias="Color", default=None, description="Color")
    text: Optional[str] = Field(alias="Text", default=None, description="Text")
    
    class Config:
        populate_by_name = True



