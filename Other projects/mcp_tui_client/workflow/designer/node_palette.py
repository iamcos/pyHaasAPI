"""
Node palette for workflow designer.

This module provides a palette of available nodes that can be dragged
onto the workflow canvas.
"""

from typing import Dict, List, Optional, Callable
from textual.widget import Widget
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label, Button, Input, Tree
from textual.widgets.tree import TreeNode
from textual import events
from rich.text import Text
from rich.panel import Panel

from ..node_registry import NodeRegistry, get_global_registry, NodeInfo, NodeCategory


class NodePaletteItem(Static):
    """Individual node item in the palette."""
    
    def __init__(self, node_info: NodeInfo, **kwargs):
        """Initialize node palette item."""
        super().__init__(**kwargs)
        self.node_info = node_info
        self.is_dragging = False
    
    def render(self):
        """Render the node palette item."""
        icon = self.node_info.icon
        name = self.node_info.display_name
        description = self.node_info.description
        
        # Truncate description if too long
        if len(description) > 40:
            description = description[:37] + "..."
        
        content = f"{icon} {name}\n{description}"
        
        style = "bold blue on white" if self.is_dragging else "white"
        return Panel(content, style=style, height=4)
    
    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Handle mouse down for drag start."""
        if event.button == 1:  # Left mouse button
            self.is_dragging = True
            self.refresh()
            
            # Notify parent about drag start
            parent = self.parent
            while parent and not isinstance(parent, NodePalette):
                parent = parent.parent
            
            if parent and hasattr(parent, 'on_node_drag_start'):
                parent.on_node_drag_start(self.node_info.node_type)
    
    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Handle mouse up for drag end."""
        if self.is_dragging:
            self.is_dragging = False
            self.refresh()


class NodePalette(Widget):
    """Palette widget showing available workflow nodes."""
    
    def __init__(self, node_registry: Optional[NodeRegistry] = None, **kwargs):
        """Initialize node palette."""
        super().__init__(**kwargs)
        self.node_registry = node_registry or get_global_registry()
        
        # UI components
        self.search_input: Optional[Input] = None
        self.category_tree: Optional[Tree] = None
        self.node_list: Optional[Vertical] = None
        
        # State
        self.current_category: Optional[str] = None
        self.search_filter: str = ""
        self.filtered_nodes: List[NodeInfo] = []
        
        # Callbacks
        self.on_node_drag_start: Optional[Callable[[str], None]] = None
        self.on_node_selected: Optional[Callable[[NodeInfo], None]] = None
    
    def compose(self):
        """Compose the node palette interface."""
        with Vertical():
            yield Label("Node Palette", classes="palette-title")
            
            # Search box
            self.search_input = Input(placeholder="Search nodes...", classes="search-input")
            yield self.search_input
            
            # Category tree and node list
            with Horizontal():
                # Category tree
                self.category_tree = Tree("Categories", classes="category-tree")
                yield self.category_tree
                
                # Node list
                with Vertical(classes="node-list-container"):
                    yield Label("Nodes", classes="section-title")
                    self.node_list = Vertical(classes="node-list")
                    yield self.node_list
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self._populate_categories()
        self._populate_nodes()
        
        # Set up search input handler
        if self.search_input:
            self.search_input.on_changed = self._on_search_changed
    
    def _populate_categories(self) -> None:
        """Populate the category tree."""
        if not self.category_tree:
            return
        
        # Get all categories
        categories = self.node_registry.get_categories()
        
        # Add category nodes
        category_nodes = {}
        for category in sorted(categories):
            # Get node count for category
            nodes_in_category = self.node_registry.get_nodes_by_category(category)
            node_count = len(nodes_in_category)
            
            # Create category display name
            display_name = f"{category.replace('_', ' ').title()} ({node_count})"
            
            # Add to tree
            category_node = self.category_tree.root.add(display_name, data=category)
            category_nodes[category] = category_node
        
        # Add "All Nodes" option
        all_nodes = self.node_registry.get_all_nodes()
        all_node = self.category_tree.root.add(f"All Nodes ({len(all_nodes)})", data="all")
        
        # Expand root by default
        self.category_tree.root.expand()
    
    def _populate_nodes(self, category: Optional[str] = None) -> None:
        """Populate the node list."""
        if not self.node_list:
            return
        
        # Clear existing nodes
        self.node_list.remove_children()
        
        # Get nodes to display
        if category == "all" or category is None:
            nodes = list(self.node_registry.get_all_nodes().values())
        else:
            nodes = self.node_registry.get_nodes_by_category(category)
        
        # Apply search filter
        if self.search_filter:
            nodes = [
                node for node in nodes
                if (self.search_filter.lower() in node.display_name.lower() or
                    self.search_filter.lower() in node.description.lower() or
                    any(self.search_filter.lower() in tag.lower() for tag in node.tags))
            ]
        
        # Sort nodes by display name
        nodes.sort(key=lambda n: n.display_name)
        
        # Create node items
        for node_info in nodes:
            node_item = NodePaletteItem(node_info, classes="node-item")
            self.node_list.mount(node_item)
        
        self.filtered_nodes = nodes
    
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle category selection."""
        if event.node.data:
            self.current_category = event.node.data
            self._populate_nodes(self.current_category)
    
    def _on_search_changed(self, value: str) -> None:
        """Handle search input changes."""
        self.search_filter = value
        self._populate_nodes(self.current_category)
    
    def on_node_drag_start(self, node_type: str) -> None:
        """Handle node drag start."""
        if self.on_node_drag_start:
            self.on_node_drag_start(node_type)
    
    def get_node_info(self, node_type: str) -> Optional[NodeInfo]:
        """Get node info by type."""
        return self.node_registry.get_node_info(node_type)
    
    def refresh_nodes(self) -> None:
        """Refresh the node list."""
        self._populate_nodes(self.current_category)
    
    def set_category_filter(self, category: str) -> None:
        """Set the current category filter."""
        self.current_category = category
        self._populate_nodes(category)
    
    def set_search_filter(self, search_text: str) -> None:
        """Set the search filter."""
        self.search_filter = search_text
        if self.search_input:
            self.search_input.value = search_text
        self._populate_nodes(self.current_category)
    
    def get_filtered_nodes(self) -> List[NodeInfo]:
        """Get currently filtered nodes."""
        return self.filtered_nodes.copy()
    
    def add_favorite_node(self, node_type: str) -> None:
        """Add a node to favorites (placeholder for future implementation)."""
        # This could be implemented to maintain a favorites category
        pass
    
    def remove_favorite_node(self, node_type: str) -> None:
        """Remove a node from favorites (placeholder for future implementation)."""
        # This could be implemented to maintain a favorites category
        pass
    
    def get_node_statistics(self) -> Dict[str, int]:
        """Get statistics about available nodes."""
        return self.node_registry.get_node_statistics()
    
    def export_node_list(self) -> List[Dict[str, str]]:
        """Export current node list for external use."""
        return [
            {
                'node_type': node.node_type,
                'display_name': node.display_name,
                'description': node.description,
                'category': node.category,
                'icon': node.icon,
                'tags': node.tags
            }
            for node in self.filtered_nodes
        ]