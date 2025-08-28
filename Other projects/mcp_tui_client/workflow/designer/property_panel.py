"""
Property panel for workflow designer.

This module provides a property panel for editing node properties and parameters.
"""

from typing import Dict, Any, Optional, Callable, List, Union
from textual.widget import Widget
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Label, Input, Button, Checkbox, Select
from textual.widgets.select import Option
from textual import events
from rich.panel import Panel
from rich.text import Text

from ..node_base import WorkflowNode, DataType


class PropertyEditor(Widget):
    """Base class for property editors."""
    
    def __init__(self, property_name: str, property_value: Any, property_config: Dict[str, Any], **kwargs):
        """Initialize property editor."""
        super().__init__(**kwargs)
        self.property_name = property_name
        self.property_value = property_value
        self.property_config = property_config
        self.on_value_changed: Optional[Callable[[str, Any], None]] = None
    
    def get_value(self) -> Any:
        """Get the current property value."""
        return self.property_value
    
    def set_value(self, value: Any) -> None:
        """Set the property value."""
        self.property_value = value
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the display to reflect current value."""
        pass
    
    def _notify_change(self, new_value: Any) -> None:
        """Notify parent of value change."""
        if self.property_value != new_value:
            self.property_value = new_value
            if self.on_value_changed:
                self.on_value_changed(self.property_name, new_value)


class StringPropertyEditor(PropertyEditor):
    """Editor for string properties."""
    
    def compose(self):
        """Compose the string editor."""
        with Vertical():
            yield Label(f"{self.property_name}:", classes="property-label")
            
            description = self.property_config.get('description', '')
            if description:
                yield Label(description, classes="property-description")
            
            self.input = Input(
                value=str(self.property_value),
                placeholder=self.property_config.get('placeholder', ''),
                classes="property-input"
            )
            yield self.input
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self.input.on_changed = self._on_input_changed
    
    def _on_input_changed(self, value: str) -> None:
        """Handle input change."""
        self._notify_change(value)
    
    def get_value(self) -> str:
        """Get current value."""
        return self.input.value if hasattr(self, 'input') else str(self.property_value)
    
    def _update_display(self) -> None:
        """Update display."""
        if hasattr(self, 'input'):
            self.input.value = str(self.property_value)


class NumberPropertyEditor(PropertyEditor):
    """Editor for numeric properties."""
    
    def compose(self):
        """Compose the number editor."""
        with Vertical():
            yield Label(f"{self.property_name}:", classes="property-label")
            
            description = self.property_config.get('description', '')
            if description:
                yield Label(description, classes="property-description")
            
            # Show min/max if specified
            min_val = self.property_config.get('min')
            max_val = self.property_config.get('max')
            if min_val is not None or max_val is not None:
                range_text = f"Range: {min_val or '∞'} to {max_val or '∞'}"
                yield Label(range_text, classes="property-range")
            
            self.input = Input(
                value=str(self.property_value),
                classes="property-input"
            )
            yield self.input
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self.input.on_changed = self._on_input_changed
    
    def _on_input_changed(self, value: str) -> None:
        """Handle input change."""
        try:
            # Determine if integer or float
            property_type = self.property_config.get('type', 'float')
            if property_type == 'integer':
                numeric_value = int(value) if value else 0
            else:
                numeric_value = float(value) if value else 0.0
            
            # Validate range
            min_val = self.property_config.get('min')
            max_val = self.property_config.get('max')
            
            if min_val is not None and numeric_value < min_val:
                numeric_value = min_val
                self.input.value = str(numeric_value)
            
            if max_val is not None and numeric_value > max_val:
                numeric_value = max_val
                self.input.value = str(numeric_value)
            
            self._notify_change(numeric_value)
            
        except ValueError:
            # Invalid input, revert to previous value
            self.input.value = str(self.property_value)
    
    def get_value(self) -> Union[int, float]:
        """Get current value."""
        try:
            property_type = self.property_config.get('type', 'float')
            if property_type == 'integer':
                return int(self.input.value) if hasattr(self, 'input') else int(self.property_value)
            else:
                return float(self.input.value) if hasattr(self, 'input') else float(self.property_value)
        except ValueError:
            return self.property_value
    
    def _update_display(self) -> None:
        """Update display."""
        if hasattr(self, 'input'):
            self.input.value = str(self.property_value)


class BooleanPropertyEditor(PropertyEditor):
    """Editor for boolean properties."""
    
    def compose(self):
        """Compose the boolean editor."""
        with Vertical():
            description = self.property_config.get('description', '')
            
            self.checkbox = Checkbox(
                self.property_name,
                value=bool(self.property_value),
                classes="property-checkbox"
            )
            yield self.checkbox
            
            if description:
                yield Label(description, classes="property-description")
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self.checkbox.on_changed = self._on_checkbox_changed
    
    def _on_checkbox_changed(self, value: bool) -> None:
        """Handle checkbox change."""
        self._notify_change(value)
    
    def get_value(self) -> bool:
        """Get current value."""
        return self.checkbox.value if hasattr(self, 'checkbox') else bool(self.property_value)
    
    def _update_display(self) -> None:
        """Update display."""
        if hasattr(self, 'checkbox'):
            self.checkbox.value = bool(self.property_value)


class ChoicePropertyEditor(PropertyEditor):
    """Editor for choice/enum properties."""
    
    def compose(self):
        """Compose the choice editor."""
        with Vertical():
            yield Label(f"{self.property_name}:", classes="property-label")
            
            description = self.property_config.get('description', '')
            if description:
                yield Label(description, classes="property-description")
            
            choices = self.property_config.get('choices', [])
            options = [Option(str(choice), choice) for choice in choices]
            
            self.select = Select(
                options=options,
                value=self.property_value,
                classes="property-select"
            )
            yield self.select
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self.select.on_changed = self._on_select_changed
    
    def _on_select_changed(self, value: Any) -> None:
        """Handle select change."""
        self._notify_change(value)
    
    def get_value(self) -> Any:
        """Get current value."""
        return self.select.value if hasattr(self, 'select') else self.property_value
    
    def _update_display(self) -> None:
        """Update display."""
        if hasattr(self, 'select'):
            self.select.value = self.property_value


class ListPropertyEditor(PropertyEditor):
    """Editor for list properties."""
    
    def compose(self):
        """Compose the list editor."""
        with Vertical():
            yield Label(f"{self.property_name}:", classes="property-label")
            
            description = self.property_config.get('description', '')
            if description:
                yield Label(description, classes="property-description")
            
            # For now, edit as JSON string
            list_str = str(self.property_value) if isinstance(self.property_value, list) else "[]"
            
            self.input = Input(
                value=list_str,
                placeholder="[item1, item2, ...]",
                classes="property-input"
            )
            yield self.input
            
            yield Label("Enter as JSON array", classes="property-hint")
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self.input.on_changed = self._on_input_changed
    
    def _on_input_changed(self, value: str) -> None:
        """Handle input change."""
        try:
            import json
            list_value = json.loads(value) if value else []
            if isinstance(list_value, list):
                self._notify_change(list_value)
            else:
                # Invalid format, revert
                self.input.value = str(self.property_value)
        except json.JSONDecodeError:
            # Invalid JSON, don't update
            pass
    
    def get_value(self) -> List[Any]:
        """Get current value."""
        try:
            import json
            return json.loads(self.input.value) if hasattr(self, 'input') else self.property_value
        except (json.JSONDecodeError, AttributeError):
            return self.property_value if isinstance(self.property_value, list) else []
    
    def _update_display(self) -> None:
        """Update display."""
        if hasattr(self, 'input'):
            self.input.value = str(self.property_value)


class DictPropertyEditor(PropertyEditor):
    """Editor for dictionary properties."""
    
    def compose(self):
        """Compose the dict editor."""
        with Vertical():
            yield Label(f"{self.property_name}:", classes="property-label")
            
            description = self.property_config.get('description', '')
            if description:
                yield Label(description, classes="property-description")
            
            # For now, edit as JSON string
            dict_str = str(self.property_value) if isinstance(self.property_value, dict) else "{}"
            
            self.input = Input(
                value=dict_str,
                placeholder='{"key": "value"}',
                classes="property-input"
            )
            yield self.input
            
            yield Label("Enter as JSON object", classes="property-hint")
    
    def on_mount(self) -> None:
        """Handle mount event."""
        self.input.on_changed = self._on_input_changed
    
    def _on_input_changed(self, value: str) -> None:
        """Handle input change."""
        try:
            import json
            dict_value = json.loads(value) if value else {}
            if isinstance(dict_value, dict):
                self._notify_change(dict_value)
            else:
                # Invalid format, revert
                self.input.value = str(self.property_value)
        except json.JSONDecodeError:
            # Invalid JSON, don't update
            pass
    
    def get_value(self) -> Dict[str, Any]:
        """Get current value."""
        try:
            import json
            return json.loads(self.input.value) if hasattr(self, 'input') else self.property_value
        except (json.JSONDecodeError, AttributeError):
            return self.property_value if isinstance(self.property_value, dict) else {}
    
    def _update_display(self) -> None:
        """Update display."""
        if hasattr(self, 'input'):
            self.input.value = str(self.property_value)


class PropertyPanel(Widget):
    """Property panel for editing node properties."""
    
    def __init__(self, **kwargs):
        """Initialize property panel."""
        super().__init__(**kwargs)
        
        # Current state
        self.selected_node: Optional[WorkflowNode] = None
        self.property_editors: Dict[str, PropertyEditor] = {}
        
        # UI components
        self.properties_container: Optional[Vertical] = None
        self.node_info_label: Optional[Label] = None
        
        # Callbacks
        self.on_property_changed: Optional[Callable[[str, str, Any], None]] = None
    
    def compose(self):
        """Compose the property panel."""
        with Vertical():
            yield Label("Properties", classes="panel-title")
            
            # Node information
            self.node_info_label = Label("No node selected", classes="node-info")
            yield self.node_info_label
            
            # Properties container
            self.properties_container = Vertical(classes="properties-container")
            yield self.properties_container
    
    def set_selected_node(self, node: Optional[WorkflowNode]) -> None:
        """Set the currently selected node."""
        self.selected_node = node
        self._update_properties()
    
    def _update_properties(self) -> None:
        """Update the properties display."""
        if not self.properties_container:
            return
        
        # Clear existing editors
        self.properties_container.remove_children()
        self.property_editors.clear()
        
        if not self.selected_node:
            # No node selected
            if self.node_info_label:
                self.node_info_label.update("No node selected")
            return
        
        # Update node info
        if self.node_info_label:
            node_name = self.selected_node.name or self.selected_node.__class__.__name__
            node_type = self.selected_node.__class__.__name__
            self.node_info_label.update(f"{node_name} ({node_type})")
        
        # Create property editors
        self._create_basic_properties()
        self._create_parameter_editors()
        self._create_port_information()
    
    def _create_basic_properties(self) -> None:
        """Create editors for basic node properties."""
        if not self.selected_node or not self.properties_container:
            return
        
        # Node name editor
        name_editor = StringPropertyEditor(
            "name",
            self.selected_node.name,
            {"description": "Display name for this node"},
            classes="property-editor"
        )
        name_editor.on_value_changed = self._on_basic_property_changed
        self.properties_container.mount(name_editor)
        self.property_editors["name"] = name_editor
        
        # Node description editor
        desc_editor = StringPropertyEditor(
            "description",
            self.selected_node.description,
            {"description": "Description of this node's purpose"},
            classes="property-editor"
        )
        desc_editor.on_value_changed = self._on_basic_property_changed
        self.properties_container.mount(desc_editor)
        self.property_editors["description"] = desc_editor
    
    def _create_parameter_editors(self) -> None:
        """Create editors for node parameters."""
        if not self.selected_node or not self.properties_container:
            return
        
        # Add section header
        self.properties_container.mount(Label("Parameters", classes="section-header"))
        
        # Get parameter definitions if available
        param_definitions = getattr(self.selected_node, '_parameter_definitions', {})
        
        # Create editors for each parameter
        for param_name, param_value in self.selected_node.parameters.items():
            param_config = param_definitions.get(param_name, {})
            
            # Determine parameter type
            param_type = param_config.get('type', self._infer_parameter_type(param_value))
            
            # Create appropriate editor
            editor = self._create_parameter_editor(param_name, param_value, param_type, param_config)
            if editor:
                editor.on_value_changed = self._on_parameter_changed
                self.properties_container.mount(editor)
                self.property_editors[param_name] = editor
    
    def _create_parameter_editor(self, param_name: str, param_value: Any, 
                               param_type: str, param_config: Dict[str, Any]) -> Optional[PropertyEditor]:
        """Create appropriate editor for parameter type."""
        
        if param_type == 'boolean':
            return BooleanPropertyEditor(param_name, param_value, param_config, classes="property-editor")
        
        elif param_type in ['integer', 'float']:
            config = param_config.copy()
            config['type'] = param_type
            return NumberPropertyEditor(param_name, param_value, config, classes="property-editor")
        
        elif param_type == 'choice' or 'choices' in param_config:
            return ChoicePropertyEditor(param_name, param_value, param_config, classes="property-editor")
        
        elif param_type == 'list':
            return ListPropertyEditor(param_name, param_value, param_config, classes="property-editor")
        
        elif param_type == 'dict':
            return DictPropertyEditor(param_name, param_value, param_config, classes="property-editor")
        
        else:
            # Default to string editor
            return StringPropertyEditor(param_name, param_value, param_config, classes="property-editor")
    
    def _infer_parameter_type(self, value: Any) -> str:
        """Infer parameter type from value."""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, list):
            return 'list'
        elif isinstance(value, dict):
            return 'dict'
        else:
            return 'string'
    
    def _create_port_information(self) -> None:
        """Create display for node port information."""
        if not self.selected_node or not self.properties_container:
            return
        
        # Add section header
        self.properties_container.mount(Label("Ports", classes="section-header"))
        
        # Input ports
        if self.selected_node.inputs:
            self.properties_container.mount(Label("Inputs:", classes="port-section"))
            for port_name, port in self.selected_node.inputs.items():
                port_info = f"  • {port_name} ({port.data_type.value})"
                if port.required:
                    port_info += " *"
                if port.description:
                    port_info += f" - {port.description}"
                
                self.properties_container.mount(Label(port_info, classes="port-info"))
        
        # Output ports
        if self.selected_node.outputs:
            self.properties_container.mount(Label("Outputs:", classes="port-section"))
            for port_name, port in self.selected_node.outputs.items():
                port_info = f"  • {port_name} ({port.data_type.value})"
                if port.description:
                    port_info += f" - {port.description}"
                
                self.properties_container.mount(Label(port_info, classes="port-info"))
    
    def _on_basic_property_changed(self, property_name: str, value: Any) -> None:
        """Handle basic property changes."""
        if not self.selected_node:
            return
        
        if property_name == "name":
            self.selected_node.name = value
        elif property_name == "description":
            self.selected_node.description = value
        
        # Notify callback
        if self.on_property_changed:
            self.on_property_changed(self.selected_node.node_id, property_name, value)
    
    def _on_parameter_changed(self, property_name: str, value: Any) -> None:
        """Handle parameter changes."""
        if not self.selected_node:
            return
        
        # Update node parameter
        self.selected_node.set_parameter(property_name, value)
        
        # Notify callback
        if self.on_property_changed:
            self.on_property_changed(self.selected_node.node_id, property_name, value)
    
    def refresh_properties(self) -> None:
        """Refresh the properties display."""
        self._update_properties()
    
    def get_property_values(self) -> Dict[str, Any]:
        """Get all current property values."""
        values = {}
        for prop_name, editor in self.property_editors.items():
            values[prop_name] = editor.get_value()
        return values
    
    def validate_properties(self) -> List[str]:
        """Validate all property values."""
        errors = []
        
        if not self.selected_node:
            return errors
        
        # Validate node
        validation_errors = self.selected_node.validate()
        for error in validation_errors:
            errors.append(f"{error.error_type}: {error.message}")
        
        return errors
    
    def reset_properties(self) -> None:
        """Reset all properties to their original values."""
        if self.selected_node:
            self._update_properties()
    
    def export_properties(self) -> Dict[str, Any]:
        """Export current properties for external use."""
        if not self.selected_node:
            return {}
        
        return {
            'node_id': self.selected_node.node_id,
            'node_type': self.selected_node.__class__.__name__,
            'name': self.selected_node.name,
            'description': self.selected_node.description,
            'parameters': self.selected_node.parameters.copy(),
            'position': self.selected_node.position.copy()
        }