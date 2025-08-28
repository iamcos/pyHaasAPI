"""
Main workflow designer interface.

This module provides the main workflow designer interface that combines
the canvas, node palette, and property panels.
"""

from typing import Dict, Any, Optional, List, Callable
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Input, Label
from textual.widget import Widget
from textual.message import Message
from textual.binding import Binding
from textual import events
import asyncio

from ..workflow_definition import WorkflowDefinition, WorkflowMetadata
from ..node_registry import get_global_registry
from ..workflow_engine import WorkflowEngine
from .workflow_canvas import WorkflowCanvas
from .node_palette import NodePalette
from .property_panel import PropertyPanel
from .workflow_templates import WorkflowTemplateManager


class WorkflowDesigner(Widget):
    """Main workflow designer interface."""
    
    BINDINGS = [
        Binding("ctrl+n", "new_workflow", "New Workflow"),
        Binding("ctrl+o", "open_workflow", "Open Workflow"),
        Binding("ctrl+s", "save_workflow", "Save Workflow"),
        Binding("ctrl+r", "run_workflow", "Run Workflow"),
        Binding("ctrl+t", "test_workflow", "Test Workflow"),
        Binding("delete", "delete_selected", "Delete Selected"),
        Binding("ctrl+z", "undo", "Undo"),
        Binding("ctrl+y", "redo", "Redo"),
        Binding("f1", "show_help", "Help"),
    ]
    
    class WorkflowChanged(Message):
        """Message sent when workflow is modified."""
        
        def __init__(self, workflow: WorkflowDefinition) -> None:
            self.workflow = workflow
            super().__init__()
    
    class NodeSelected(Message):
        """Message sent when a node is selected."""
        
        def __init__(self, node_id: Optional[str]) -> None:
            self.node_id = node_id
            super().__init__()
    
    def __init__(self, **kwargs):
        """Initialize workflow designer."""
        super().__init__(**kwargs)
        
        # Core components
        self.node_registry = get_global_registry()
        self.workflow_engine = WorkflowEngine(self.node_registry)
        self.template_manager = WorkflowTemplateManager()
        
        # Current workflow
        self.current_workflow: Optional[WorkflowDefinition] = None
        self.workflow_file_path: Optional[str] = None
        self.is_modified = False
        
        # UI components
        self.canvas: Optional[WorkflowCanvas] = None
        self.node_palette: Optional[NodePalette] = None
        self.property_panel: Optional[PropertyPanel] = None
        
        # Undo/Redo system
        self.undo_stack: List[WorkflowDefinition] = []
        self.redo_stack: List[WorkflowDefinition] = []
        self.max_undo_levels = 50
        
        # Callbacks
        self.on_workflow_run: Optional[Callable] = None
        self.on_workflow_save: Optional[Callable] = None
    
    def compose(self) -> ComposeResult:
        """Compose the workflow designer interface."""
        with Vertical():
            # Header with workflow info
            with Horizontal(classes="designer-header"):
                yield Label("Workflow Designer", classes="title")
                yield Button("New", id="btn-new", classes="header-button")
                yield Button("Open", id="btn-open", classes="header-button")
                yield Button("Save", id="btn-save", classes="header-button")
                yield Button("Run", id="btn-run", classes="header-button")
                yield Button("Test", id="btn-test", classes="header-button")
            
            # Main designer area
            with Horizontal(classes="designer-main"):
                # Node palette on the left
                self.node_palette = NodePalette(classes="node-palette")
                yield self.node_palette
                
                # Canvas in the center
                self.canvas = WorkflowCanvas(classes="workflow-canvas")
                yield self.canvas
                
                # Property panel on the right
                self.property_panel = PropertyPanel(classes="property-panel")
                yield self.property_panel
            
            # Status bar
            with Horizontal(classes="designer-status"):
                yield Label("Ready", id="status-label")
                yield Label("", id="workflow-info")
    
    def on_mount(self) -> None:
        """Handle mount event."""
        # Set up component communication
        if self.canvas:
            self.canvas.on_node_selected = self._on_node_selected
            self.canvas.on_node_moved = self._on_node_moved
            self.canvas.on_connection_created = self._on_connection_created
            self.canvas.on_connection_deleted = self._on_connection_deleted
        
        if self.node_palette:
            self.node_palette.on_node_drag_start = self._on_node_drag_start
        
        if self.property_panel:
            self.property_panel.on_property_changed = self._on_property_changed
        
        # Create new workflow by default
        self.action_new_workflow()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "btn-new":
            self.action_new_workflow()
        elif button_id == "btn-open":
            self.action_open_workflow()
        elif button_id == "btn-save":
            self.action_save_workflow()
        elif button_id == "btn-run":
            self.action_run_workflow()
        elif button_id == "btn-test":
            self.action_test_workflow()
    
    def action_new_workflow(self) -> None:
        """Create a new workflow."""
        if self.is_modified:
            # In a real implementation, show save dialog
            pass
        
        # Create new workflow
        metadata = WorkflowMetadata(name="New Workflow")
        self.current_workflow = WorkflowDefinition(metadata=metadata)
        self.workflow_file_path = None
        self.is_modified = False
        
        # Clear undo/redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # Update UI
        if self.canvas:
            self.canvas.set_workflow(self.current_workflow)
        
        self._update_status("New workflow created")
        self._update_workflow_info()
    
    def action_open_workflow(self) -> None:
        """Open an existing workflow."""
        # In a real implementation, show file dialog
        # For now, we'll use a placeholder
        self._update_status("Open workflow not implemented yet")
    
    def action_save_workflow(self) -> None:
        """Save the current workflow."""
        if not self.current_workflow:
            return
        
        if self.workflow_file_path:
            self._save_workflow_to_file(self.workflow_file_path)
        else:
            # In a real implementation, show save dialog
            self._update_status("Save as... not implemented yet")
    
    async def action_run_workflow(self) -> None:
        """Run the current workflow."""
        if not self.current_workflow:
            self._update_status("No workflow to run")
            return
        
        # Validate workflow first
        validation_errors = self.workflow_engine.validate_workflow(self.current_workflow)
        if validation_errors:
            error_msg = f"Validation failed: {len(validation_errors)} errors"
            self._update_status(error_msg)
            return
        
        self._update_status("Running workflow...")
        
        try:
            # Execute workflow
            result = await self.workflow_engine.execute_workflow(self.current_workflow)
            
            if result.status.value == "completed":
                self._update_status(f"Workflow completed in {result.total_execution_time:.2f}s")
            else:
                self._update_status(f"Workflow failed: {result.error}")
            
            # Notify callback if set
            if self.on_workflow_run:
                self.on_workflow_run(result)
                
        except Exception as e:
            self._update_status(f"Execution error: {str(e)}")
    
    async def action_test_workflow(self) -> None:
        """Test the current workflow (dry run)."""
        if not self.current_workflow:
            self._update_status("No workflow to test")
            return
        
        self._update_status("Testing workflow...")
        
        try:
            # Perform dry run
            dry_run_result = await self.workflow_engine.dry_run_workflow(self.current_workflow)
            
            validation_errors = dry_run_result.get('validation_errors', [])
            if validation_errors:
                self._update_status(f"Test failed: {len(validation_errors)} validation errors")
            else:
                estimated_time = dry_run_result.get('estimated_duration', 0)
                node_count = len(dry_run_result.get('execution_plan', []))
                self._update_status(f"Test passed: {node_count} nodes, ~{estimated_time:.1f}s estimated")
                
        except Exception as e:
            self._update_status(f"Test error: {str(e)}")
    
    def action_delete_selected(self) -> None:
        """Delete selected nodes or connections."""
        if self.canvas:
            self.canvas.delete_selected()
            self._mark_modified()
    
    def action_undo(self) -> None:
        """Undo last action."""
        if self.undo_stack and self.current_workflow:
            # Save current state to redo stack
            self.redo_stack.append(self.current_workflow.clone())
            
            # Restore previous state
            self.current_workflow = self.undo_stack.pop()
            
            # Update canvas
            if self.canvas:
                self.canvas.set_workflow(self.current_workflow)
            
            self._update_status("Undo")
    
    def action_redo(self) -> None:
        """Redo last undone action."""
        if self.redo_stack and self.current_workflow:
            # Save current state to undo stack
            self.undo_stack.append(self.current_workflow.clone())
            
            # Restore next state
            self.current_workflow = self.redo_stack.pop()
            
            # Update canvas
            if self.canvas:
                self.canvas.set_workflow(self.current_workflow)
            
            self._update_status("Redo")
    
    def action_show_help(self) -> None:
        """Show help information."""
        help_text = \"\"\"
        Workflow Designer Help
        
        Keyboard Shortcuts:
        - Ctrl+N: New workflow
        - Ctrl+O: Open workflow
        - Ctrl+S: Save workflow
        - Ctrl+R: Run workflow
        - Ctrl+T: Test workflow
        - Delete: Delete selected
        - Ctrl+Z: Undo
        - Ctrl+Y: Redo
        - F1: Show this help
        
        Mouse Operations:
        - Drag nodes from palette to canvas
        - Click nodes to select
        - Drag nodes to move
        - Right-click for context menu
        \"\"\"
        
        # In a real implementation, show help dialog
        self._update_status("Help: See documentation for keyboard shortcuts")
    
    def _on_node_selected(self, node_id: Optional[str]) -> None:
        """Handle node selection."""
        if self.property_panel and self.current_workflow:
            if node_id:
                node = self.current_workflow.get_node(node_id)
                self.property_panel.set_selected_node(node)
            else:
                self.property_panel.set_selected_node(None)
        
        # Send message
        self.post_message(self.NodeSelected(node_id))
    
    def _on_node_moved(self, node_id: str, x: float, y: float) -> None:
        """Handle node movement."""
        if self.current_workflow:
            node = self.current_workflow.get_node(node_id)
            if node:
                node.set_position(x, y)
                self._mark_modified()
    
    def _on_connection_created(self, source_node_id: str, source_port: str,
                             target_node_id: str, target_port: str) -> None:
        """Handle connection creation."""
        if self.current_workflow:
            from ..node_base import Connection
            import uuid
            
            connection = Connection(
                connection_id=str(uuid.uuid4()),
                source_node_id=source_node_id,
                source_port_name=source_port,
                target_node_id=target_node_id,
                target_port_name=target_port
            )
            
            try:
                self.current_workflow.add_connection(connection)
                self._mark_modified()
                self._update_status("Connection created")
            except Exception as e:
                self._update_status(f"Connection failed: {str(e)}")
    
    def _on_connection_deleted(self, connection_id: str) -> None:
        """Handle connection deletion."""
        if self.current_workflow:
            self.current_workflow.remove_connection(connection_id)
            self._mark_modified()
            self._update_status("Connection deleted")
    
    def _on_node_drag_start(self, node_type: str) -> None:
        """Handle node drag start from palette."""
        if self.canvas:
            self.canvas.start_node_placement(node_type)
    
    def _on_property_changed(self, node_id: str, property_name: str, value: Any) -> None:
        """Handle property changes."""
        if self.current_workflow:
            node = self.current_workflow.get_node(node_id)
            if node:
                node.set_parameter(property_name, value)
                self._mark_modified()
                
                # Update canvas display
                if self.canvas:
                    self.canvas.refresh_node(node_id)
    
    def _mark_modified(self) -> None:
        """Mark workflow as modified."""
        if not self.is_modified and self.current_workflow:
            # Save current state to undo stack
            self.undo_stack.append(self.current_workflow.clone())
            
            # Limit undo stack size
            if len(self.undo_stack) > self.max_undo_levels:
                self.undo_stack.pop(0)
            
            # Clear redo stack
            self.redo_stack.clear()
        
        self.is_modified = True
        self._update_workflow_info()
        
        # Send change message
        if self.current_workflow:
            self.post_message(self.WorkflowChanged(self.current_workflow))
    
    def _save_workflow_to_file(self, file_path: str) -> None:
        """Save workflow to file."""
        if not self.current_workflow:
            return
        
        try:
            from ..serialization import save_workflow
            save_workflow(self.current_workflow, file_path)
            
            self.workflow_file_path = file_path
            self.is_modified = False
            
            self._update_status(f"Workflow saved to {file_path}")
            self._update_workflow_info()
            
            # Notify callback if set
            if self.on_workflow_save:
                self.on_workflow_save(self.current_workflow, file_path)
                
        except Exception as e:
            self._update_status(f"Save failed: {str(e)}")
    
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        status_label = self.query_one("#status-label", Label)
        if status_label:
            status_label.update(message)
    
    def _update_workflow_info(self) -> None:
        """Update workflow information display."""
        info_label = self.query_one("#workflow-info", Label)
        if info_label and self.current_workflow:
            workflow_name = self.current_workflow.metadata.name
            modified_indicator = "*" if self.is_modified else ""
            node_count = len(self.current_workflow.nodes)
            connection_count = len(self.current_workflow.connections)
            
            info_text = f"{workflow_name}{modified_indicator} | {node_count} nodes, {connection_count} connections"
            info_label.update(info_text)
    
    def load_workflow(self, workflow: WorkflowDefinition, file_path: Optional[str] = None) -> None:
        """Load a workflow into the designer."""
        self.current_workflow = workflow
        self.workflow_file_path = file_path
        self.is_modified = False
        
        # Clear undo/redo stacks
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # Update UI
        if self.canvas:
            self.canvas.set_workflow(workflow)
        
        self._update_status("Workflow loaded")
        self._update_workflow_info()
    
    def get_current_workflow(self) -> Optional[WorkflowDefinition]:
        """Get the current workflow."""
        return self.current_workflow
    
    def set_workflow_run_callback(self, callback: Callable) -> None:
        """Set callback for workflow run events."""
        self.on_workflow_run = callback
    
    def set_workflow_save_callback(self, callback: Callable) -> None:
        """Set callback for workflow save events."""
        self.on_workflow_save = callback
    
    def add_node_to_workflow(self, node_type: str, x: float, y: float) -> Optional[str]:
        """Add a node to the current workflow."""
        if not self.current_workflow:
            return None
        
        # Create node instance
        node_info = self.node_registry.get_node_info(node_type)
        if not node_info:
            self._update_status(f"Unknown node type: {node_type}")
            return None
        
        try:
            node = node_info.create_instance()
            node.set_position(x, y)
            
            # Add to workflow
            self.current_workflow.add_node(node)
            
            # Update canvas
            if self.canvas:
                self.canvas.add_node_visual(node)
            
            self._mark_modified()
            self._update_status(f"Added {node_type} node")
            
            return node.node_id
            
        except Exception as e:
            self._update_status(f"Failed to add node: {str(e)}")
            return None
    
    def remove_node_from_workflow(self, node_id: str) -> bool:
        """Remove a node from the current workflow."""
        if not self.current_workflow:
            return False
        
        try:
            self.current_workflow.remove_node(node_id)
            
            # Update canvas
            if self.canvas:
                self.canvas.remove_node_visual(node_id)
            
            self._mark_modified()
            self._update_status("Node removed")
            
            return True
            
        except Exception as e:
            self._update_status(f"Failed to remove node: {str(e)}")
            return False