"""
Container Components

Responsive layout containers with automatic sizing and advanced layouts.
"""

from typing import List, Dict, Any, Optional, Union, Callable
from enum import Enum

from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane, Button, Label, Collapsible
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.geometry import Size


class LayoutMode(Enum):
    """Layout modes for responsive containers"""
    AUTO = "auto"
    FIXED = "fixed"
    FLEX = "flex"
    GRID = "grid"


class ResponsiveContainer(Container):
    """Container that automatically adjusts layout based on available space"""
    
    DEFAULT_CSS = """
    ResponsiveContainer {
        height: 1fr;
        width: 1fr;
    }
    
    ResponsiveContainer.compact {
        layout: vertical;
    }
    
    ResponsiveContainer.normal {
        layout: horizontal;
    }
    
    ResponsiveContainer.wide {
        layout: grid;
        grid-size: 2 2;
    }
    """
    
    layout_mode = reactive(LayoutMode.AUTO)
    
    def __init__(
        self,
        layout_mode: LayoutMode = LayoutMode.AUTO,
        breakpoints: Dict[str, int] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.layout_mode = layout_mode
        self.breakpoints = breakpoints or {
            "compact": 80,   # Less than 80 columns
            "normal": 120,   # 80-120 columns
            "wide": 160      # More than 120 columns
        }
        self.current_size_class = "normal"
        self.child_widgets: List[Widget] = []
    
    def add_responsive_child(self, widget: Widget, size_classes: List[str] = None) -> None:
        """Add a child widget with responsive behavior"""
        widget.size_classes = size_classes or ["compact", "normal", "wide"]
        self.child_widgets.append(widget)
        self._update_layout()
    
    def on_resize(self, size: Size) -> None:
        """Handle container resize"""
        self._determine_size_class(size.width)
        self._update_layout()
    
    def _determine_size_class(self, width: int) -> None:
        """Determine current size class based on width"""
        if width < self.breakpoints["compact"]:
            new_class = "compact"
        elif width < self.breakpoints["normal"]:
            new_class = "normal"
        else:
            new_class = "wide"
        
        if new_class != self.current_size_class:
            self.current_size_class = new_class
            self.remove_class("compact", "normal", "wide")
            self.add_class(new_class)
    
    def _update_layout(self) -> None:
        """Update layout based on current size class"""
        if self.layout_mode == LayoutMode.AUTO:
            # Remove existing children
            self.remove_children()
            
            # Add children based on size class
            visible_children = [
                child for child in self.child_widgets
                if self.current_size_class in getattr(child, 'size_classes', [])
            ]
            
            for child in visible_children:
                self.mount(child)


class SplitContainer(Container):
    """Container that splits space between widgets with resizable dividers"""
    
    DEFAULT_CSS = """
    SplitContainer {
        height: 1fr;
        width: 1fr;
    }
    
    SplitContainer.horizontal {
        layout: horizontal;
    }
    
    SplitContainer.vertical {
        layout: vertical;
    }
    
    SplitContainer .split-pane {
        border: solid $primary;
        margin: 0 1;
    }
    
    SplitContainer .split-divider {
        width: 1;
        background: $accent;
    }
    """
    
    def __init__(
        self,
        orientation: str = "horizontal",
        split_ratios: List[float] = None,
        resizable: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.orientation = orientation
        self.split_ratios = split_ratios or [0.5, 0.5]
        self.resizable = resizable
        self.panes: List[Container] = []
        
        self.add_class(orientation)
    
    def add_pane(self, widget: Widget, ratio: float = None) -> Container:
        """Add a pane to the split container"""
        pane = Container(classes="split-pane")
        pane.mount(widget)
        
        if ratio:
            if self.orientation == "horizontal":
                pane.styles.width = f"{ratio * 100}%"
            else:
                pane.styles.height = f"{ratio * 100}%"
        
        self.panes.append(pane)
        self.mount(pane)
        
        return pane
    
    def set_split_ratios(self, ratios: List[float]) -> None:
        """Update split ratios"""
        self.split_ratios = ratios
        self._update_pane_sizes()
    
    def _update_pane_sizes(self) -> None:
        """Update pane sizes based on ratios"""
        for i, (pane, ratio) in enumerate(zip(self.panes, self.split_ratios)):
            if self.orientation == "horizontal":
                pane.styles.width = f"{ratio * 100}%"
            else:
                pane.styles.height = f"{ratio * 100}%"


class TabbedContainer(Container):
    """Enhanced tabbed container with dynamic tab management"""
    
    DEFAULT_CSS = """
    TabbedContainer {
        height: 1fr;
        width: 1fr;
    }
    
    TabbedContainer .tab-controls {
        dock: top;
        height: 3;
        background: $surface;
    }
    
    TabbedContainer .tab-content {
        height: 1fr;
        padding: 1;
    }
    """
    
    active_tab = reactive("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tabs: Dict[str, Dict[str, Any]] = {}
        self.tab_order: List[str] = []
    
    def compose(self) -> ComposeResult:
        """Compose tabbed container layout"""
        yield Container(classes="tab-controls", id="tab-controls")
        yield Container(classes="tab-content", id="tab-content")
    
    def add_tab(
        self,
        tab_id: str,
        title: str,
        content: Widget,
        closable: bool = False,
        icon: str = None
    ) -> None:
        """Add a new tab"""
        self.tabs[tab_id] = {
            "title": title,
            "content": content,
            "closable": closable,
            "icon": icon
        }
        
        if tab_id not in self.tab_order:
            self.tab_order.append(tab_id)
        
        self._update_tab_controls()
        
        # Set as active if it's the first tab
        if not self.active_tab:
            self.active_tab = tab_id
    
    def remove_tab(self, tab_id: str) -> None:
        """Remove a tab"""
        if tab_id in self.tabs:
            del self.tabs[tab_id]
            if tab_id in self.tab_order:
                self.tab_order.remove(tab_id)
            
            # Switch to another tab if this was active
            if self.active_tab == tab_id:
                if self.tab_order:
                    self.active_tab = self.tab_order[0]
                else:
                    self.active_tab = ""
            
            self._update_tab_controls()
    
    def switch_to_tab(self, tab_id: str) -> None:
        """Switch to a specific tab"""
        if tab_id in self.tabs:
            self.active_tab = tab_id
    
    def _update_tab_controls(self) -> None:
        """Update tab control buttons"""
        try:
            controls_container = self.query_one("#tab-controls")
            controls_container.remove_children()
            
            tab_buttons = Horizontal()
            
            for tab_id in self.tab_order:
                tab_info = self.tabs[tab_id]
                
                # Create tab button
                button_text = tab_info["title"]
                if tab_info.get("icon"):
                    button_text = f"{tab_info['icon']} {button_text}"
                
                tab_button = Button(
                    button_text,
                    variant="primary" if tab_id == self.active_tab else "default",
                    id=f"tab-{tab_id}"
                )
                tab_buttons.mount(tab_button)
                
                # Add close button if closable
                if tab_info["closable"]:
                    close_button = Button(
                        "×",
                        variant="error",
                        size="small",
                        id=f"close-{tab_id}"
                    )
                    tab_buttons.mount(close_button)
            
            controls_container.mount(tab_buttons)
        except:
            pass  # Container might not be mounted yet
    
    def watch_active_tab(self, new_tab: str) -> None:
        """React to active tab changes"""
        self._update_tab_content()
        self._update_tab_controls()
    
    def _update_tab_content(self) -> None:
        """Update the content area with active tab content"""
        try:
            content_container = self.query_one("#tab-content")
            content_container.remove_children()
            
            if self.active_tab and self.active_tab in self.tabs:
                content = self.tabs[self.active_tab]["content"]
                content_container.mount(content)
        except:
            pass
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle tab button presses"""
        button_id = event.button.id
        
        if button_id and button_id.startswith("tab-"):
            tab_id = button_id[4:]  # Remove "tab-" prefix
            self.switch_to_tab(tab_id)
        elif button_id and button_id.startswith("close-"):
            tab_id = button_id[6:]  # Remove "close-" prefix
            self.remove_tab(tab_id)


class CollapsibleContainer(Container):
    """Container that can be collapsed/expanded"""
    
    DEFAULT_CSS = """
    CollapsibleContainer {
        height: auto;
        border: solid $primary;
        margin: 1 0;
    }
    
    CollapsibleContainer .collapsible-header {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
    }
    
    CollapsibleContainer .collapsible-content {
        padding: 1;
    }
    
    CollapsibleContainer.collapsed .collapsible-content {
        display: none;
    }
    """
    
    expanded = reactive(True)
    
    def __init__(
        self,
        title: str,
        content: Widget,
        expanded: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self.content_widget = content
        self.expanded = expanded
    
    def compose(self) -> ComposeResult:
        """Compose collapsible container"""
        # Header with toggle button
        header = Horizontal(classes="collapsible-header")
        toggle_button = Button(
            f"{'▼' if self.expanded else '▶'} {self.title}",
            variant="primary",
            id="toggle-button"
        )
        header.mount(toggle_button)
        yield header
        
        # Content area
        content_container = Container(classes="collapsible-content", id="content")
        content_container.mount(self.content_widget)
        yield content_container
    
    def toggle(self) -> None:
        """Toggle expanded/collapsed state"""
        self.expanded = not self.expanded
    
    def expand(self) -> None:
        """Expand the container"""
        self.expanded = True
    
    def collapse(self) -> None:
        """Collapse the container"""
        self.expanded = False
    
    def watch_expanded(self, expanded: bool) -> None:
        """React to expanded state changes"""
        if expanded:
            self.remove_class("collapsed")
        else:
            self.add_class("collapsed")
        
        # Update toggle button
        try:
            toggle_button = self.query_one("#toggle-button", Button)
            icon = "▼" if expanded else "▶"
            toggle_button.label = f"{icon} {self.title}"
        except:
            pass
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle toggle button press"""
        if event.button.id == "toggle-button":
            self.toggle()


class GridContainer(Container):
    """Advanced grid container with responsive grid layout"""
    
    DEFAULT_CSS = """
    GridContainer {
        layout: grid;
        height: 1fr;
        width: 1fr;
    }
    
    GridContainer .grid-item {
        border: solid $accent;
        padding: 1;
        margin: 0;
    }
    """
    
    def __init__(
        self,
        columns: int = 2,
        rows: int = 2,
        gap: int = 1,
        auto_size: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.grid_columns = columns
        self.grid_rows = rows
        self.gap = gap
        self.auto_size = auto_size
        self.grid_items: List[Widget] = []
        
        # Set grid layout
        self.styles.grid_size_columns = columns
        self.styles.grid_size_rows = rows
        self.styles.grid_gutter = gap
    
    def add_grid_item(
        self,
        widget: Widget,
        column: int = None,
        row: int = None,
        column_span: int = 1,
        row_span: int = 1
    ) -> None:
        """Add item to grid with optional positioning"""
        grid_item = Container(classes="grid-item")
        grid_item.mount(widget)
        
        # Set grid positioning if specified
        if column is not None:
            grid_item.styles.column_span = column_span
        if row is not None:
            grid_item.styles.row_span = row_span
        
        self.grid_items.append(grid_item)
        self.mount(grid_item)
        
        # Auto-resize grid if needed
        if self.auto_size:
            self._auto_resize_grid()
    
    def set_grid_size(self, columns: int, rows: int) -> None:
        """Update grid dimensions"""
        self.grid_columns = columns
        self.grid_rows = rows
        self.styles.grid_size_columns = columns
        self.styles.grid_size_rows = rows
    
    def _auto_resize_grid(self) -> None:
        """Automatically resize grid to fit items"""
        item_count = len(self.grid_items)
        if item_count == 0:
            return
        
        # Calculate optimal grid size
        import math
        optimal_columns = math.ceil(math.sqrt(item_count))
        optimal_rows = math.ceil(item_count / optimal_columns)
        
        if optimal_columns != self.grid_columns or optimal_rows != self.grid_rows:
            self.set_grid_size(optimal_columns, optimal_rows)


class FlexContainer(Container):
    """Flexible container with flex-box like behavior"""
    
    DEFAULT_CSS = """
    FlexContainer {
        height: 1fr;
        width: 1fr;
    }
    
    FlexContainer.row {
        layout: horizontal;
    }
    
    FlexContainer.column {
        layout: vertical;
    }
    
    FlexContainer .flex-item {
        margin: 1;
    }
    """
    
    def __init__(
        self,
        direction: str = "row",  # "row" or "column"
        justify: str = "start",  # "start", "center", "end", "space-between"
        align: str = "stretch",  # "start", "center", "end", "stretch"
        wrap: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.direction = direction
        self.justify = justify
        self.align = align
        self.wrap = wrap
        self.flex_items: List[Dict[str, Any]] = []
        
        self.add_class(direction)
    
    def add_flex_item(
        self,
        widget: Widget,
        flex_grow: int = 0,
        flex_shrink: int = 1,
        flex_basis: str = "auto",
        align_self: str = None
    ) -> None:
        """Add flexible item to container"""
        flex_item = Container(classes="flex-item")
        flex_item.mount(widget)
        
        # Store flex properties
        item_info = {
            "widget": flex_item,
            "flex_grow": flex_grow,
            "flex_shrink": flex_shrink,
            "flex_basis": flex_basis,
            "align_self": align_self or self.align
        }
        
        self.flex_items.append(item_info)
        self.mount(flex_item)
        
        # Apply flex styles (simplified)
        if flex_grow > 0:
            if self.direction == "row":
                flex_item.styles.width = f"{flex_grow}fr"
            else:
                flex_item.styles.height = f"{flex_grow}fr"