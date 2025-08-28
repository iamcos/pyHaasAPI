# Enhanced UI Components Library

This library provides a comprehensive set of reusable UI components for the MCP TUI Client with advanced features including data binding, theming, and responsive layouts.

## Features

### 🔄 Data Binding System
- Real-time data updates with automatic UI synchronization
- One-way and two-way data binding support
- Efficient change propagation with minimal UI updates
- Built-in data sources for common use cases

### 🎨 Advanced Theming
- Multiple built-in themes (Dark, Light, High Contrast)
- Custom theme creation and management
- Component-specific styling
- Runtime theme switching

### 📱 Responsive Layouts
- Automatic layout adjustment based on terminal size
- Breakpoint-based responsive design
- Flexible container systems
- Grid and flexbox-like layouts

### 📊 Rich Components
- Advanced data tables with sorting, filtering, and pagination
- ASCII-based charts and visualizations
- Status indicators and progress bars
- Form components with validation

## Quick Start

```python
from mcp_tui_client.ui.components import (
    DataBindingManager, ThemeManager,
    StatusPanel, DataTable, LineChart
)

# Initialize managers
data_manager = DataBindingManager()
theme_manager = ThemeManager()

# Create components
status_panel = StatusPanel(title="System Status")
data_table = DataTable(columns=["Name", "Value", "Status"])
chart = LineChart(title="Performance")

# Set up data binding
data_source = MyDataSource("system_metrics")
data_manager.register_data_source(data_source)
data_manager.create_binding(
    "cpu_usage",
    "system_metrics", 
    status_panel,
    "cpu_percent",
    "status_value"
)
```

## Core Components

### Panels
- **BasePanel**: Foundation panel with header, content, and footer
- **StatusPanel**: Real-time status display with indicators
- **DataPanel**: Data display with refresh capabilities
- **ChartPanel**: Chart container with built-in rendering
- **ActionPanel**: Button panel for user actions

### Tables
- **DataTable**: Basic data table with real-time updates
- **SortableTable**: Table with column sorting
- **FilterableTable**: Table with search and filtering
- **PaginatedTable**: Table with pagination support

### Charts
- **ASCIIChart**: Base chart component for terminal display
- **LineChart**: Line chart with trend visualization
- **CandlestickChart**: OHLCV candlestick charts
- **PerformanceChart**: Performance metrics visualization
- **BarChart**: Horizontal and vertical bar charts

### Containers
- **ResponsiveContainer**: Automatic layout adjustment
- **SplitContainer**: Resizable split layouts
- **TabbedContainer**: Dynamic tab management
- **CollapsibleContainer**: Expandable/collapsible sections
- **GridContainer**: Grid-based layouts
- **FlexContainer**: Flexible box layouts

### Indicators
- **StatusIndicator**: Color-coded status display
- **ProgressIndicator**: Progress bars with ETA
- **ConnectionIndicator**: Connection status monitoring
- **PerformanceIndicator**: Performance metrics display
- **LoadingIndicator**: Animated loading spinner
- **AlertIndicator**: Dismissible alert messages

### Forms
- **BaseForm**: Foundation form with validation
- **ConfigForm**: Configuration forms
- **SearchForm**: Search and filter forms
- **QuickActionForm**: Quick action dialogs

## Data Binding

### Basic Usage

```python
from mcp_tui_client.ui.components.data_binding import (
    DataBindingManager, RealTimeDataSource, BindingType
)

# Create data source
class MyDataSource(RealTimeDataSource):
    async def start_updates(self):
        # Start real-time updates
        pass
    
    async def stop_updates(self):
        # Stop updates
        pass

# Set up binding
manager = DataBindingManager()
source = MyDataSource("my_data")
manager.register_data_source(source)

# Bind to widget
binding = manager.create_binding(
    binding_id="my_binding",
    source_id="my_data",
    widget=my_widget,
    source_property="value",
    widget_property="content",
    binding_type=BindingType.ONE_WAY
)
```

### Built-in Data Sources

- **BotDataSource**: Trading bot metrics
- **MarketDataSource**: Real-time market data
- **SystemDataSource**: System performance metrics

## Theming

### Using Themes

```python
from mcp_tui_client.ui.components.theming import ThemeManager

# Initialize theme manager
theme_manager = ThemeManager(app)

# Switch themes
theme_manager.set_theme("Light")
theme_manager.set_theme("Dark")
theme_manager.set_theme("High Contrast")

# Get available themes
themes = theme_manager.get_theme_names()
```

### Creating Custom Themes

```python
# Create custom theme based on existing one
custom_theme = theme_manager.create_custom_theme(
    name="My Theme",
    base_theme_name="Dark",
    color_overrides={
        "primary": "#ff6b35",
        "accent": "#00d4aa"
    }
)

# Save theme
theme_manager.save_theme(custom_theme)
```

### Component Theming

```python
from mcp_tui_client.ui.components.theming import ComponentTheme

# Create component-specific theme
component_theme = ComponentTheme(
    component_name="MyWidget",
    styles={"border": "solid", "padding": "1"},
    colors={"color": "#ffffff", "background": "#000000"}
)

# Add to theme
theme.add_component_theme(component_theme)
```

## Responsive Design

### Responsive Containers

```python
from mcp_tui_client.ui.components.containers import ResponsiveContainer

# Create responsive container
container = ResponsiveContainer(
    breakpoints={
        "compact": 80,   # < 80 columns
        "normal": 120,   # 80-120 columns  
        "wide": 160      # > 120 columns
    }
)

# Add responsive children
container.add_responsive_child(
    compact_widget, 
    size_classes=["compact"]
)
container.add_responsive_child(
    normal_widget,
    size_classes=["normal", "wide"]
)
```

### Grid Layouts

```python
from mcp_tui_client.ui.components.containers import GridContainer

# Create grid
grid = GridContainer(columns=3, rows=2, auto_size=True)

# Add items
grid.add_grid_item(widget1, column=0, row=0)
grid.add_grid_item(widget2, column=1, row=0, column_span=2)
```

## Advanced Features

### Real-time Updates

All components support real-time data updates through the data binding system:

```python
# Data automatically updates UI
data_source.set_data("cpu_usage", 75.5)
data_source.set_data("memory_usage", 60.2)

# Batch updates
data_source.update_data({
    "cpu_usage": 75.5,
    "memory_usage": 60.2,
    "disk_usage": 45.8
})
```

### Event Handling

Components provide rich event handling:

```python
# Handle table row selection
async def on_row_selected(self, event):
    selected_data = self.table.data[event.row_index]
    await self.show_details(selected_data)

# Handle form submission
async def on_form_submit(self, form_data):
    await self.process_form(form_data)
```

### Validation

Forms include built-in validation:

```python
from mcp_tui_client.ui.components.forms import FormField, FieldType
from textual.validation import Number

# Create validated field
field = FormField(
    name="port",
    field_type=FieldType.NUMBER,
    label="Port Number",
    required=True,
    validator=Number(minimum=1, maximum=65535)
)
```

## Examples

See the `examples/` directory for complete working examples:

- `simple_components_demo.py`: Basic component usage
- `enhanced_components_demo.py`: Full-featured demo
- `data_binding_example.py`: Data binding examples
- `theming_example.py`: Theme customization

## Testing

Run the test suite:

```bash
python -m pytest mcp_tui_client/tests/unit/test_enhanced_components.py -v
```

## Performance

The enhanced components are designed for performance:

- Efficient data binding with minimal UI updates
- Lazy loading of component content
- Optimized rendering for large datasets
- Memory-efficient weak references

## Browser Compatibility

Components are designed for terminal environments and support:

- Various terminal sizes and capabilities
- Color and monochrome displays
- Keyboard and mouse navigation
- Screen readers and accessibility tools

## Contributing

When adding new components:

1. Extend appropriate base classes
2. Implement data binding support
3. Add theme-aware styling
4. Include comprehensive tests
5. Update documentation

## License

This library is part of the MCP TUI Client project and follows the same license terms.