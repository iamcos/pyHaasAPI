"""
Workflow canvas for visual node editing.

This module provides a canvas widget for displaying and editing workflow nodes
and connections in a visual interface.
"""

from typing import Dict, Any, Optional, List, Tuple, Callable, Set
from textual.widget import Widget
from textual.containers import Container
from textual.widgets import Static, Label
from textual.geometry import Offset, Size
from textual.message import Message
from textual import events
from textual.reactive import reactive
from rich.console import RenderableType
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
import math

from ..workflow_definition import WorkflowDefinition
from ..node_base import WorkflowNode, Connection


class NodeVisual(Static):
    """Visual representation of a workflow node."""
    
    def __init__(self, node: WorkflowNode, **kwargs):
        """Initialize node visual."""
        super().__init__(**kwargs)
        self.node = node
        self.is_selected = False
        self.is_dragging = False
        self.drag_offset = Offset(0, 0)
        
        # Visual properties
        self.width = 12
        self.height = 6
        
        # Port positions (relative to node)
        self.input_ports: Dict[str, Tuple[int, int]] = {}
        self.output_ports: Dict[str, Tuple[int, int]] = {}
        
        self._calculate_port_positions()
    
    def _calculate_port_positions(self) -> None:
        """Calculate port positions relative to node."""
        # Input ports on the left side
        input_count = len(self.node.inputs)
        if input_count > 0:
            for i, port_name in enumerate(self.node.inputs.keys()):
                y_offset = 1 + (i * (self.height - 2) // max(1, input_count - 1)) if input_count > 1 else self.height // 2
                self.input_ports[port_name] = (0, y_offset)
        
        # Output ports on the right side
        output_count = len(self.node.outputs)
        if output_count > 0:
            for i, port_name in enumerate(self.node.outputs.keys()):
                y_offset = 1 + (i * (self.height - 2) // max(1, output_count - 1)) if output_count > 1 else self.height // 2
                self.output_ports[port_name] = (self.width - 1, y_offset)
    
    def render(self) -> RenderableType:
        """Render the node visual."""
        # Create node content
        node_name = self.node.name or self.node.__class__.__name__
        if len(node_name) > self.width - 2:
            node_name = node_name[:self.width - 5] + "..."
        
        # Node type indicator
        node_type = self.node.__class__.__name__
        type_indicator = node_type[0].upper() if node_type else "N"
        
        # Create node display
        lines = []
        lines.append(f"[{type_indicator}] {node_name}")
        
        # Add input ports
        for port_name, (x, y) in self.input_ports.items():
            if y < len(lines):
                lines[y] = "●" + lines[y][1:] if len(lines[y]) > 1 else "●"
        
        # Add output ports
        for port_name, (x, y) in self.output_ports.items():
            while len(lines) <= y:
                lines.append(" " * self.width)
            if len(lines[y]) < self.width:
                lines[y] = lines[y].ljust(self.width - 1) + "●"
            else:
                lines[y] = lines[y][:-1] + "●"
        
        # Pad lines to node height
        while len(lines) < self.height:
            lines.append(" " * self.width)
        
        content = "\n".join(lines[:self.height])
        
        # Create panel with appropriate style
        style = "bold blue" if self.is_selected else "white"
        border_style = "blue" if self.is_selected else "dim white"
        
        return Panel(
            content,
            style=style,
            border_style=border_style,
            width=self.width,
            height=self.height
        )
    
    def get_port_position(self, port_name: str, is_output: bool = False) -> Optional[Tuple[int, int]]:
        """Get absolute position of a port."""
        ports = self.output_ports if is_output else self.input_ports
        if port_name in ports:
            rel_x, rel_y = ports[port_name]
            abs_x = self.offset.x + rel_x
            abs_y = self.offset.y + rel_y
            return (abs_x, abs_y)
        return None
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within node bounds."""
        return (self.offset.x <= x < self.offset.x + self.width and
                self.offset.y <= y < self.offset.y + self.height)
    
    def get_port_at_position(self, x: int, y: int) -> Optional[Tuple[str, bool]]:
        """Get port at given position."""
        rel_x = x - self.offset.x
        rel_y = y - self.offset.y
        
        # Check input ports
        for port_name, (px, py) in self.input_ports.items():
            if px == rel_x and py == rel_y:
                return (port_name, False)  # False = input port
        
        # Check output ports
        for port_name, (px, py) in self.output_ports.items():
            if px == rel_x and py == rel_y:
                return (port_name, True)  # True = output port
        
        return None


class ConnectionVisual:
    """Visual representation of a connection between nodes."""
    
    def __init__(self, connection: Connection, source_pos: Tuple[int, int], target_pos: Tuple[int, int]):
        """Initialize connection visual."""
        self.connection = connection
        self.source_pos = source_pos
        self.target_pos = target_pos
        self.is_selected = False
    
    def get_path_chars(self) -> List[Tuple[int, int, str]]:
        """Get characters to draw the connection path."""
        chars = []
        
        sx, sy = self.source_pos
        tx, ty = self.target_pos
        
        # Simple line drawing algorithm
        dx = abs(tx - sx)
        dy = abs(ty - sy)
        
        x, y = sx, sy
        x_inc = 1 if tx > sx else -1
        y_inc = 1 if ty > sy else -1
        
        error = dx - dy
        
        while True:
            # Choose character based on direction
            if x == sx and y == sy:
                char = "●"  # Source port
            elif x == tx and y == ty:
                char = "●"  # Target port
            else:
                # Determine line character
                if dx > dy:
                    char = "─"  # Horizontal line
                else:
                    char = "│"  # Vertical line
            
            chars.append((x, y, char))
            
            if x == tx and y == ty:
                break
            
            e2 = 2 * error
            if e2 > -dy:
                error -= dy
                x += x_inc
            if e2 < dx:
                error += dx
                y += y_inc
        
        return chars


class WorkflowCanvas(Widget):
    """Canvas for displaying and editing workflow nodes and connections."""
    
    # Reactive attributes
    selected_nodes: reactive[Set[str]] = reactive(set())
    
    def __init__(self, **kwargs):
        """Initialize workflow canvas."""
        super().__init__(**kwargs)
        
        # Workflow data
        self.workflow: Optional[WorkflowDefinition] = None
        self.node_visuals: Dict[str, NodeVisual] = {}
        self.connection_visuals: Dict[str, ConnectionVisual] = {}
        
        # Interaction state
        self.is_dragging = False
        self.drag_start_pos: Optional[Offset] = None
        self.dragging_node_id: Optional[str] = None
        self.is_connecting = False
        self.connection_start: Optional[Tuple[str, str, bool]] = None  # (node_id, port_name, is_output)
        self.placing_node_type: Optional[str] = None
        
        # Canvas properties
        self.canvas_offset = Offset(0, 0)
        self.zoom_level = 1.0
        
        # Callbacks
        self.on_node_selected: Optional[Callable[[Optional[str]], None]] = None
        self.on_node_moved: Optional[Callable[[str, float, float], None]] = None
        self.on_connection_created: Optional[Callable[[str, str, str, str], None]] = None
        self.on_connection_deleted: Optional[Callable[[str], None]] = None
    
    def set_workflow(self, workflow: WorkflowDefinition) -> None:
        """Set the workflow to display."""
        self.workflow = workflow
        self._rebuild_visuals()
        self.refresh()
    
    def _rebuild_visuals(self) -> None:
        """Rebuild all visual elements from workflow."""
        if not self.workflow:
            return
        
        # Clear existing visuals
        self.node_visuals.clear()
        self.connection_visuals.clear()
        
        # Create node visuals
        for node_id, node in self.workflow.nodes.items():
            node_visual = NodeVisual(node)
            # Position node based on its stored position
            pos_x = int(node.position.get('x', 0))
            pos_y = int(node.position.get('y', 0))
            node_visual.offset = Offset(pos_x, pos_y)
            self.node_visuals[node_id] = node_visual
        
        # Create connection visuals
        self._update_connection_visuals()
    
    def _update_connection_visuals(self) -> None:
        """Update connection visuals based on current node positions."""
        if not self.workflow:
            return
        
        self.connection_visuals.clear()
        
        for conn_id, connection in self.workflow.connections.items():
            source_visual = self.node_visuals.get(connection.source_node_id)
            target_visual = self.node_visuals.get(connection.target_node_id)
            
            if source_visual and target_visual:
                source_pos = source_visual.get_port_position(connection.source_port_name, True)
                target_pos = target_visual.get_port_position(connection.target_port_name, False)
                
                if source_pos and target_pos:
                    conn_visual = ConnectionVisual(connection, source_pos, target_pos)
                    self.connection_visuals[conn_id] = conn_visual
    
    def render(self) -> RenderableType:
        """Render the canvas."""
        if not self.workflow:
            return Panel("No workflow loaded", title="Workflow Canvas")
        
        # Create a text buffer for the canvas
        canvas_width = self.size.width - 2  # Account for panel borders
        canvas_height = self.size.height - 2
        
        # Initialize canvas buffer
        canvas_buffer = [[' ' for _ in range(canvas_width)] for _ in range(canvas_height)]
        
        # Draw connections first (so they appear behind nodes)
        for conn_visual in self.connection_visuals.values():
            for x, y, char in conn_visual.get_path_chars():
                # Adjust for canvas offset
                canvas_x = x - self.canvas_offset.x
                canvas_y = y - self.canvas_offset.y
                
                if 0 <= canvas_x < canvas_width and 0 <= canvas_y < canvas_height:
                    canvas_buffer[canvas_y][canvas_x] = char
        
        # Draw nodes
        for node_id, node_visual in self.node_visuals.items():
            node_x = node_visual.offset.x - self.canvas_offset.x
            node_y = node_visual.offset.y - self.canvas_offset.y
            
            # Only draw if node is visible
            if (node_x + node_visual.width > 0 and node_x < canvas_width and
                node_y + node_visual.height > 0 and node_y < canvas_height):
                
                # Get node content
                node_content = str(node_visual.render())
                node_lines = node_content.split('\n')
                
                # Draw node content to buffer
                for i, line in enumerate(node_lines):
                    draw_y = node_y + i
                    if 0 <= draw_y < canvas_height:
                        for j, char in enumerate(line):
                            draw_x = node_x + j
                            if 0 <= draw_x < canvas_width:
                                canvas_buffer[draw_y][draw_x] = char
        
        # Convert buffer to string
        canvas_content = '\n'.join(''.join(row) for row in canvas_buffer)
        
        # Create panel
        title = f"Workflow: {self.workflow.metadata.name}"
        if self.selected_nodes:
            title += f" | Selected: {len(self.selected_nodes)}"
        
        return Panel(canvas_content, title=title, border_style="blue")
    
    def on_click(self, event: events.Click) -> None:
        """Handle click events."""
        click_x = event.x + self.canvas_offset.x
        click_y = event.y + self.canvas_offset.y
        
        # Check if clicking on a node
        clicked_node_id = None
        for node_id, node_visual in self.node_visuals.items():
            if node_visual.contains_point(click_x, click_y):
                clicked_node_id = node_id
                break
        
        # Handle node selection
        if clicked_node_id:
            if event.ctrl:
                # Multi-select
                if clicked_node_id in self.selected_nodes:
                    self.selected_nodes.remove(clicked_node_id)
                else:
                    self.selected_nodes.add(clicked_node_id)
            else:
                # Single select
                self.selected_nodes = {clicked_node_id}
            
            # Update visual selection
            self._update_node_selection()
            
            # Notify callback
            if self.on_node_selected:
                selected_id = next(iter(self.selected_nodes)) if len(self.selected_nodes) == 1 else None
                self.on_node_selected(selected_id)
        
        else:
            # Clicked on empty space
            if self.placing_node_type:
                # Place new node
                self._place_node(self.placing_node_type, click_x, click_y)
                self.placing_node_type = None
            else:
                # Clear selection
                self.selected_nodes = set()
                self._update_node_selection()
                
                if self.on_node_selected:
                    self.on_node_selected(None)
        
        self.refresh()
    
    def on_mouse_down(self, event: events.MouseDown) -> None:
        """Handle mouse down events."""
        if event.button != 1:  # Only handle left mouse button
            return
        
        click_x = event.x + self.canvas_offset.x
        click_y = event.y + self.canvas_offset.y
        
        # Check if starting to drag a node
        for node_id, node_visual in self.node_visuals.items():
            if node_visual.contains_point(click_x, click_y):
                # Check if clicking on a port
                port_info = node_visual.get_port_at_position(click_x, click_y)
                if port_info:
                    # Start connection
                    port_name, is_output = port_info
                    self.is_connecting = True
                    self.connection_start = (node_id, port_name, is_output)
                else:
                    # Start dragging node
                    self.is_dragging = True
                    self.dragging_node_id = node_id
                    self.drag_start_pos = Offset(click_x, click_y)
                    node_visual.is_dragging = True
                    node_visual.drag_offset = Offset(
                        click_x - node_visual.offset.x,
                        click_y - node_visual.offset.y
                    )
                break
    
    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Handle mouse move events."""
        if self.is_dragging and self.dragging_node_id:
            # Update node position
            node_visual = self.node_visuals.get(self.dragging_node_id)
            if node_visual:
                new_x = event.x + self.canvas_offset.x - node_visual.drag_offset.x
                new_y = event.y + self.canvas_offset.y - node_visual.drag_offset.y
                
                node_visual.offset = Offset(new_x, new_y)
                
                # Update connections
                self._update_connection_visuals()
                self.refresh()
    
    def on_mouse_up(self, event: events.MouseUp) -> None:
        """Handle mouse up events."""
        if self.is_dragging and self.dragging_node_id:
            # Finish dragging
            node_visual = self.node_visuals.get(self.dragging_node_id)
            if node_visual:
                node_visual.is_dragging = False
                
                # Notify callback
                if self.on_node_moved:
                    self.on_node_moved(
                        self.dragging_node_id,
                        float(node_visual.offset.x),
                        float(node_visual.offset.y)
                    )
            
            self.is_dragging = False
            self.dragging_node_id = None
            self.drag_start_pos = None
        
        elif self.is_connecting and self.connection_start:
            # Finish connection
            click_x = event.x + self.canvas_offset.x
            click_y = event.y + self.canvas_offset.y
            
            # Find target port
            for node_id, node_visual in self.node_visuals.items():
                if node_visual.contains_point(click_x, click_y):
                    port_info = node_visual.get_port_at_position(click_x, click_y)
                    if port_info:
                        port_name, is_output = port_info
                        
                        # Create connection
                        source_node_id, source_port, source_is_output = self.connection_start
                        
                        if source_is_output and not is_output:
                            # Valid connection: output to input
                            if self.on_connection_created:
                                self.on_connection_created(
                                    source_node_id, source_port,
                                    node_id, port_name
                                )
                        elif not source_is_output and is_output:
                            # Valid connection: input to output (reverse)
                            if self.on_connection_created:
                                self.on_connection_created(
                                    node_id, port_name,
                                    source_node_id, source_port
                                )
                    break
            
            self.is_connecting = False
            self.connection_start = None
    
    def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        if event.key == "delete":
            self.delete_selected()
        elif event.key == "escape":
            # Cancel current operation
            if self.placing_node_type:
                self.placing_node_type = None
            elif self.is_connecting:
                self.is_connecting = False
                self.connection_start = None
            else:
                # Clear selection
                self.selected_nodes = set()
                self._update_node_selection()
                if self.on_node_selected:
                    self.on_node_selected(None)
            
            self.refresh()
    
    def _update_node_selection(self) -> None:
        """Update visual selection state of nodes."""
        for node_id, node_visual in self.node_visuals.items():
            node_visual.is_selected = node_id in self.selected_nodes
    
    def _place_node(self, node_type: str, x: int, y: int) -> None:
        """Place a new node at the specified position."""
        # This would be handled by the parent designer
        # For now, just clear the placement mode
        self.placing_node_type = None
    
    def start_node_placement(self, node_type: str) -> None:
        """Start node placement mode."""
        self.placing_node_type = node_type
    
    def delete_selected(self) -> None:
        """Delete selected nodes and connections."""
        if not self.workflow:
            return
        
        # Delete selected nodes
        for node_id in list(self.selected_nodes):
            if node_id in self.workflow.nodes:
                self.workflow.remove_node(node_id)
                if node_id in self.node_visuals:
                    del self.node_visuals[node_id]
        
        # Clear selection
        self.selected_nodes = set()
        
        # Update visuals
        self._update_connection_visuals()
        self.refresh()
    
    def add_node_visual(self, node: WorkflowNode) -> None:
        """Add visual representation for a node."""
        node_visual = NodeVisual(node)
        pos_x = int(node.position.get('x', 0))
        pos_y = int(node.position.get('y', 0))
        node_visual.offset = Offset(pos_x, pos_y)
        self.node_visuals[node.node_id] = node_visual
        
        self._update_connection_visuals()
        self.refresh()
    
    def remove_node_visual(self, node_id: str) -> None:
        """Remove visual representation for a node."""
        if node_id in self.node_visuals:
            del self.node_visuals[node_id]
        
        # Remove from selection
        if node_id in self.selected_nodes:
            self.selected_nodes.remove(node_id)
        
        self._update_connection_visuals()
        self.refresh()
    
    def refresh_node(self, node_id: str) -> None:
        """Refresh visual representation of a specific node."""
        if node_id in self.node_visuals:
            # Node visual will automatically update on next render
            self.refresh()
    
    def center_on_nodes(self) -> None:
        """Center the canvas view on all nodes."""
        if not self.node_visuals:
            return
        
        # Calculate bounding box of all nodes
        min_x = min(nv.offset.x for nv in self.node_visuals.values())
        max_x = max(nv.offset.x + nv.width for nv in self.node_visuals.values())
        min_y = min(nv.offset.y for nv in self.node_visuals.values())
        max_y = max(nv.offset.y + nv.height for nv in self.node_visuals.values())
        
        # Calculate center
        center_x = (min_x + max_x) // 2
        center_y = (min_y + max_y) // 2
        
        # Adjust canvas offset to center the view
        self.canvas_offset = Offset(
            center_x - self.size.width // 2,
            center_y - self.size.height // 2
        )
        
        self.refresh()