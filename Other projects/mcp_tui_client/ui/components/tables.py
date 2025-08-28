"""
Table Components

Advanced table components with sorting, filtering, and pagination.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime

from textual.widget import Widget
from textual.widgets import DataTable as TextualDataTable, Input, Button, Label
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.coordinate import Coordinate


class DataTable(Container):
    """Enhanced data table with real-time updates"""
    
    DEFAULT_CSS = """
    DataTable {
        height: 1fr;
    }
    
    DataTable .table-header {
        dock: top;
        height: 3;
        background: $surface;
    }
    
    DataTable .table-content {
        height: 1fr;
    }
    
    DataTable .table-footer {
        dock: bottom;
        height: 3;
        background: $surface;
    }
    """
    
    def __init__(
        self,
        columns: List[str],
        show_header: bool = True,
        show_footer: bool = True,
        zebra_stripes: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.columns = columns
        self.show_header = show_header
        self.show_footer = show_footer
        self.zebra_stripes = zebra_stripes
        self.data: List[Dict[str, Any]] = []
        self.selected_row: Optional[int] = None
    
    def compose(self) -> ComposeResult:
        """Compose the table layout"""
        if self.show_header:
            yield Container(classes="table-header", id="table-header")
        
        yield Container(classes="table-content", id="table-content")
        
        if self.show_footer:
            yield Container(classes="table-footer", id="table-footer")
    
    async def on_mount(self) -> None:
        """Initialize the table on mount"""
        await self._setup_table()
    
    async def _setup_table(self) -> None:
        """Set up the data table widget"""
        content_container = self.query_one("#table-content")
        
        self.table_widget = TextualDataTable(
            zebra_stripes=self.zebra_stripes,
            cursor_type="row",
            id="data-table"
        )
        
        # Add columns
        for column in self.columns:
            self.table_widget.add_column(column, key=column)
        
        content_container.mount(self.table_widget)
        
        # Set up header if needed
        if self.show_header:
            await self._setup_header()
        
        # Set up footer if needed
        if self.show_footer:
            await self._setup_footer()
    
    async def _setup_header(self) -> None:
        """Set up table header with controls"""
        header_container = self.query_one("#table-header")
        header_container.mount(Label(f"Data Table ({len(self.data)} rows)"))
    
    async def _setup_footer(self) -> None:
        """Set up table footer with status"""
        footer_container = self.query_one("#table-footer")
        footer_container.mount(Label("Ready"))
    
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """Set table data"""
        self.data = data
        self._refresh_table()
    
    def add_row(self, row_data: Dict[str, Any]) -> None:
        """Add a single row"""
        self.data.append(row_data)
        self._add_table_row(row_data)
        self._update_header()
    
    def update_row(self, row_index: int, row_data: Dict[str, Any]) -> None:
        """Update a specific row"""
        if 0 <= row_index < len(self.data):
            self.data[row_index] = row_data
            self._refresh_table()
    
    def remove_row(self, row_index: int) -> None:
        """Remove a specific row"""
        if 0 <= row_index < len(self.data):
            del self.data[row_index]
            self._refresh_table()
    
    def clear_data(self) -> None:
        """Clear all table data"""
        self.data.clear()
        self.table_widget.clear()
        self._update_header()
    
    def _refresh_table(self) -> None:
        """Refresh the entire table"""
        self.table_widget.clear()
        for row_data in self.data:
            self._add_table_row(row_data)
        self._update_header()
    
    def _add_table_row(self, row_data: Dict[str, Any]) -> None:
        """Add a row to the table widget"""
        row_values = []
        for column in self.columns:
            value = row_data.get(column, "")
            row_values.append(str(value))
        self.table_widget.add_row(*row_values)
    
    def _update_header(self) -> None:
        """Update header with current row count"""
        if self.show_header:
            header_container = self.query_one("#table-header")
            header_container.remove_children()
            header_container.mount(Label(f"Data Table ({len(self.data)} rows)"))
    
    async def on_data_table_row_selected(self, event: TextualDataTable.RowSelected) -> None:
        """Handle row selection"""
        self.selected_row = event.row_index
        if self.show_footer:
            footer_container = self.query_one("#table-footer")
            footer_container.remove_children()
            footer_container.mount(Label(f"Selected row: {event.row_index + 1}"))


class SortableTable(DataTable):
    """Data table with sorting capabilities"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False
    
    async def _setup_header(self) -> None:
        """Set up sortable header"""
        header_container = self.query_one("#table-header")
        
        header_row = Horizontal()
        header_row.mount(Label(f"Sortable Table ({len(self.data)} rows)"))
        
        # Add sort controls
        sort_container = Horizontal()
        sort_container.mount(Label("Sort by:"))
        
        for column in self.columns:
            sort_button = Button(
                column,
                variant="outline",
                size="small",
                id=f"sort-{column}"
            )
            sort_container.mount(sort_button)
        
        header_row.mount(sort_container)
        header_container.mount(header_row)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sort button presses"""
        button_id = event.button.id
        if button_id and button_id.startswith("sort-"):
            column = button_id[5:]  # Remove "sort-" prefix
            await self.sort_by_column(column)
    
    async def sort_by_column(self, column: str) -> None:
        """Sort table by specified column"""
        if column not in self.columns:
            return
        
        # Toggle sort direction if same column
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Sort data
        def sort_key(row: Dict[str, Any]) -> Any:
            value = row.get(column, "")
            # Try to convert to number for proper sorting
            try:
                return float(value)
            except (ValueError, TypeError):
                return str(value).lower()
        
        self.data.sort(key=sort_key, reverse=self.sort_reverse)
        self._refresh_table()
        
        # Update footer with sort info
        if self.show_footer:
            footer_container = self.query_one("#table-footer")
            footer_container.remove_children()
            direction = "↓" if self.sort_reverse else "↑"
            footer_container.mount(Label(f"Sorted by {column} {direction}"))


class FilterableTable(SortableTable):
    """Data table with filtering capabilities"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_text: str = ""
        self.filtered_data: List[Dict[str, Any]] = []
    
    async def _setup_header(self) -> None:
        """Set up header with filter controls"""
        header_container = self.query_one("#table-header")
        
        # Filter input
        filter_row = Horizontal()
        filter_row.mount(Label("Filter:"))
        filter_input = Input(placeholder="Type to filter...", id="filter-input")
        filter_row.mount(filter_input)
        
        # Sort controls
        sort_row = Horizontal()
        sort_row.mount(Label("Sort:"))
        for column in self.columns:
            sort_button = Button(
                column,
                variant="outline", 
                size="small",
                id=f"sort-{column}"
            )
            sort_row.mount(sort_button)
        
        header_container.mount(Vertical(filter_row, sort_row))
    
    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes"""
        if event.input.id == "filter-input":
            self.filter_text = event.value.lower()
            await self.apply_filter()
    
    async def apply_filter(self) -> None:
        """Apply current filter to data"""
        if not self.filter_text:
            self.filtered_data = self.data.copy()
        else:
            self.filtered_data = []
            for row in self.data:
                # Check if filter text appears in any column
                for column in self.columns:
                    value = str(row.get(column, "")).lower()
                    if self.filter_text in value:
                        self.filtered_data.append(row)
                        break
        
        # Refresh table with filtered data
        self.table_widget.clear()
        for row_data in self.filtered_data:
            self._add_table_row(row_data)
        
        # Update header count
        header_container = self.query_one("#table-header")
        # Find and update the count label (simplified)
        count_text = f"Filtered Table ({len(self.filtered_data)}/{len(self.data)} rows)"
        
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """Override to maintain filter"""
        super().set_data(data)
        self.filtered_data = data.copy()
        if self.filter_text:
            asyncio.create_task(self.apply_filter())


class PaginatedTable(FilterableTable):
    """Data table with pagination"""
    
    def __init__(self, page_size: int = 50, **kwargs):
        super().__init__(**kwargs)
        self.page_size = page_size
        self.current_page = 0
        self.total_pages = 0
    
    async def _setup_footer(self) -> None:
        """Set up footer with pagination controls"""
        footer_container = self.query_one("#table-footer")
        
        pagination_row = Horizontal()
        
        # Previous page button
        prev_button = Button("◀ Prev", variant="outline", size="small", id="prev-page")
        pagination_row.mount(prev_button)
        
        # Page info
        page_info = Label("", id="page-info")
        pagination_row.mount(page_info)
        
        # Next page button
        next_button = Button("Next ▶", variant="outline", size="small", id="next-page")
        pagination_row.mount(next_button)
        
        footer_container.mount(pagination_row)
        self._update_pagination_info()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle pagination and sort button presses"""
        button_id = event.button.id
        
        if button_id == "prev-page":
            await self.previous_page()
        elif button_id == "next-page":
            await self.next_page()
        else:
            # Handle sort buttons
            await super().on_button_pressed(event)
    
    async def previous_page(self) -> None:
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            await self._refresh_page()
    
    async def next_page(self) -> None:
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self._refresh_page()
    
    async def _refresh_page(self) -> None:
        """Refresh current page display"""
        data_to_show = self.filtered_data if hasattr(self, 'filtered_data') else self.data
        
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        page_data = data_to_show[start_idx:end_idx]
        
        # Clear and populate table
        self.table_widget.clear()
        for row_data in page_data:
            self._add_table_row(row_data)
        
        self._update_pagination_info()
    
    def _update_pagination_info(self) -> None:
        """Update pagination information"""
        data_to_show = self.filtered_data if hasattr(self, 'filtered_data') else self.data
        self.total_pages = max(1, (len(data_to_show) + self.page_size - 1) // self.page_size)
        
        if self.show_footer:
            try:
                page_info = self.query_one("#page-info", Label)
                page_info.update(f"Page {self.current_page + 1} of {self.total_pages}")
                
                # Update button states
                prev_button = self.query_one("#prev-page", Button)
                next_button = self.query_one("#next-page", Button)
                
                prev_button.disabled = self.current_page == 0
                next_button.disabled = self.current_page >= self.total_pages - 1
            except:
                pass  # Widgets might not be mounted yet
    
    def set_data(self, data: List[Dict[str, Any]]) -> None:
        """Override to handle pagination"""
        super().set_data(data)
        self.current_page = 0
        self._update_pagination_info()
        asyncio.create_task(self._refresh_page())


# Import asyncio for async operations
import asyncio