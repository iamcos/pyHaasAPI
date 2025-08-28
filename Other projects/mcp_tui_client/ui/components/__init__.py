"""
Base UI Components Library

This module provides reusable UI components for the MCP TUI Client with
data binding, theming, and responsive layout capabilities.
"""

from .panels import (
    BasePanel,
    StatusPanel,
    DataPanel,
    ChartPanel,
    ActionPanel,
)

from .tables import (
    DataTable,
    SortableTable,
    FilterableTable,
    PaginatedTable,
)

from .charts import (
    ASCIIChart,
    LineChart,
    CandlestickChart,
    PerformanceChart,
    BarChart,
)

from .forms import (
    BaseForm,
    ConfigForm,
    SearchForm,
    FilterForm,
    QuickActionForm,
    FieldType,
    FormField,
)

from .containers import (
    ResponsiveContainer,
    SplitContainer,
    TabbedContainer,
    CollapsibleContainer,
    GridContainer,
    FlexContainer,
)

from .indicators import (
    StatusIndicator,
    ProgressIndicator,
    ConnectionIndicator,
    PerformanceIndicator,
    LoadingIndicator,
    AlertIndicator,
    IndicatorStatus,
)

from .data_binding import (
    DataBinding,
    DataBindingManager,
    BindableWidget,
    RealTimeDataSource,
)

from .theming import (
    ThemeManager,
    Theme,
    ColorScheme,
    ComponentTheme,
)

__all__ = [
    # Panels
    "BasePanel",
    "StatusPanel", 
    "DataPanel",
    "ChartPanel",
    "ActionPanel",
    
    # Tables
    "DataTable",
    "SortableTable",
    "FilterableTable", 
    "PaginatedTable",
    
    # Charts
    "ASCIIChart",
    "LineChart",
    "CandlestickChart",
    "PerformanceChart",
    "BarChart",
    
    # Forms
    "BaseForm",
    "ConfigForm",
    "SearchForm",
    "FilterForm",
    "QuickActionForm",
    "FieldType",
    "FormField",
    
    # Containers
    "ResponsiveContainer",
    "SplitContainer",
    "TabbedContainer",
    "CollapsibleContainer",
    "GridContainer",
    "FlexContainer",
    
    # Indicators
    "StatusIndicator",
    "ProgressIndicator",
    "ConnectionIndicator",
    "PerformanceIndicator",
    "LoadingIndicator",
    "AlertIndicator",
    "IndicatorStatus",
    
    # Data Binding
    "DataBinding",
    "DataBindingManager",
    "BindableWidget",
    "RealTimeDataSource",
    
    # Theming
    "ThemeManager",
    "Theme",
    "ColorScheme",
    "ComponentTheme",
]