"""
Serialization utilities for workflow nodes and definitions.

This module provides utilities for serializing and deserializing workflow
components to/from various formats.
"""

import json
import pickle
import base64
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import yaml

from .node_base import WorkflowNode, NodePort, Connection, DataType, PortType
from .workflow_definition import WorkflowDefinition, WorkflowMetadata
from .node_registry import NodeRegistry, get_global_registry


class SerializationError(Exception):
    """Exception raised during serialization/deserialization."""
    pass


class WorkflowSerializer:
    """Handles serialization of workflow components."""
    
    def __init__(self, node_registry: Optional[NodeRegistry] = None):
        self.node_registry = node_registry or get_global_registry()
    
    def serialize_workflow(self, workflow: WorkflowDefinition, 
                          format: str = 'json') -> Union[str, bytes]:
        """Serialize a workflow to the specified format."""
        if format.lower() == 'json':
            return self._serialize_to_json(workflow)
        elif format.lower() == 'yaml':
            return self._serialize_to_yaml(workflow)
        elif format.lower() == 'pickle':
            return self._serialize_to_pickle(workflow)
        else:
            raise SerializationError(f"Unsupported format: {format}")
    
    def deserialize_workflow(self, data: Union[str, bytes], 
                           format: str = 'json') -> WorkflowDefinition:
        """Deserialize a workflow from the specified format."""
        if format.lower() == 'json':
            return self._deserialize_from_json(data)
        elif format.lower() == 'yaml':
            return self._deserialize_from_yaml(data)
        elif format.lower() == 'pickle':
            return self._deserialize_from_pickle(data)
        else:
            raise SerializationError(f"Unsupported format: {format}")
    
    def save_workflow(self, workflow: WorkflowDefinition, 
                     file_path: Union[str, Path], 
                     format: str = None) -> None:
        """Save a workflow to a file."""
        file_path = Path(file_path)
        
        if format is None:
            # Infer format from file extension
            ext = file_path.suffix.lower()
            if ext == '.json':
                format = 'json'
            elif ext in ['.yaml', '.yml']:
                format = 'yaml'
            elif ext == '.pkl':
                format = 'pickle'
            else:
                format = 'json'  # Default
        
        serialized_data = self.serialize_workflow(workflow, format)
        
        if format == 'pickle':
            file_path.write_bytes(serialized_data)
        else:
            file_path.write_text(serialized_data, encoding='utf-8')
    
    def load_workflow(self, file_path: Union[str, Path], 
                     format: str = None) -> WorkflowDefinition:
        """Load a workflow from a file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise SerializationError(f"File not found: {file_path}")
        
        if format is None:
            # Infer format from file extension
            ext = file_path.suffix.lower()
            if ext == '.json':
                format = 'json'
            elif ext in ['.yaml', '.yml']:
                format = 'yaml'
            elif ext == '.pkl':
                format = 'pickle'
            else:
                format = 'json'  # Default
        
        if format == 'pickle':
            data = file_path.read_bytes()
        else:
            data = file_path.read_text(encoding='utf-8')
        
        return self.deserialize_workflow(data, format)
    
    def _serialize_to_json(self, workflow: WorkflowDefinition) -> str:
        """Serialize workflow to JSON."""
        try:
            workflow_dict = workflow.to_dict()
            return json.dumps(workflow_dict, indent=2, default=self._json_serializer)
        except Exception as e:
            raise SerializationError(f"JSON serialization failed: {e}")
    
    def _deserialize_from_json(self, json_data: str) -> WorkflowDefinition:
        """Deserialize workflow from JSON."""
        try:
            workflow_dict = json.loads(json_data)
            return WorkflowDefinition.from_dict(workflow_dict, self.node_registry)
        except Exception as e:
            raise SerializationError(f"JSON deserialization failed: {e}")
    
    def _serialize_to_yaml(self, workflow: WorkflowDefinition) -> str:
        """Serialize workflow to YAML."""
        try:
            workflow_dict = workflow.to_dict()
            return yaml.dump(workflow_dict, default_flow_style=False, 
                           allow_unicode=True, sort_keys=False)
        except Exception as e:
            raise SerializationError(f"YAML serialization failed: {e}")
    
    def _deserialize_from_yaml(self, yaml_data: str) -> WorkflowDefinition:
        """Deserialize workflow from YAML."""
        try:
            workflow_dict = yaml.safe_load(yaml_data)
            return WorkflowDefinition.from_dict(workflow_dict, self.node_registry)
        except Exception as e:
            raise SerializationError(f"YAML deserialization failed: {e}")
    
    def _serialize_to_pickle(self, workflow: WorkflowDefinition) -> bytes:
        """Serialize workflow to pickle format."""
        try:
            return pickle.dumps(workflow)
        except Exception as e:
            raise SerializationError(f"Pickle serialization failed: {e}")
    
    def _deserialize_from_pickle(self, pickle_data: bytes) -> WorkflowDefinition:
        """Deserialize workflow from pickle format."""
        try:
            return pickle.loads(pickle_data)
        except Exception as e:
            raise SerializationError(f"Pickle deserialization failed: {e}")
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for complex objects."""
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):  # Objects with to_dict method
            return obj.to_dict()
        elif isinstance(obj, set):
            return list(obj)
        else:
            return str(obj)
    
    def export_node_template(self, node: WorkflowNode) -> Dict[str, Any]:
        """Export a node as a reusable template."""
        template = {
            'node_type': node.__class__.__name__,
            'template_name': node.name,
            'description': node.description,
            'parameters': node.parameters.copy(),
            'input_ports': {
                name: port.to_dict() 
                for name, port in node.inputs.items()
            },
            'output_ports': {
                name: port.to_dict() 
                for name, port in node.outputs.items()
            },
            'created_at': node.created_at.isoformat(),
            'version': '1.0.0'
        }
        return template
    
    def import_node_template(self, template: Dict[str, Any]) -> WorkflowNode:
        """Import a node from a template."""
        node_type = template['node_type']
        node_info = self.node_registry.get_node_info(node_type)
        
        if not node_info:
            raise SerializationError(f"Unknown node type: {node_type}")
        
        # Create node instance
        node = node_info.create_instance()
        
        # Apply template settings
        node.name = template.get('template_name', node.name)
        node.description = template.get('description', node.description)
        node.parameters.update(template.get('parameters', {}))
        
        return node
    
    def create_workflow_bundle(self, workflows: List[WorkflowDefinition], 
                             metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a bundle containing multiple workflows."""
        bundle = {
            'bundle_id': str(uuid.uuid4()),
            'bundle_metadata': metadata or {},
            'workflows': [workflow.to_dict() for workflow in workflows],
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        return bundle
    
    def extract_workflow_bundle(self, bundle: Dict[str, Any]) -> List[WorkflowDefinition]:
        """Extract workflows from a bundle."""
        workflows = []
        
        for workflow_data in bundle.get('workflows', []):
            workflow = WorkflowDefinition.from_dict(workflow_data, self.node_registry)
            workflows.append(workflow)
        
        return workflows


class NodeTemplateManager:
    """Manages node templates for reuse."""
    
    def __init__(self, template_dir: Union[str, Path] = None):
        self.template_dir = Path(template_dir or "~/.mcp-tui/templates").expanduser()
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.serializer = WorkflowSerializer()
    
    def save_template(self, node: WorkflowNode, template_name: str = None) -> str:
        """Save a node as a template."""
        template_name = template_name or f"{node.__class__.__name__}_{node.name}"
        template_name = self._sanitize_filename(template_name)
        
        template = self.serializer.export_node_template(node)
        template_file = self.template_dir / f"{template_name}.json"
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        
        return str(template_file)
    
    def load_template(self, template_name: str) -> WorkflowNode:
        """Load a node template."""
        template_file = self.template_dir / f"{template_name}.json"
        
        if not template_file.exists():
            raise SerializationError(f"Template not found: {template_name}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        return self.serializer.import_node_template(template)
    
    def list_templates(self) -> List[str]:
        """List available templates."""
        templates = []
        for template_file in self.template_dir.glob("*.json"):
            templates.append(template_file.stem)
        return sorted(templates)
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a template."""
        template_file = self.template_dir / f"{template_name}.json"
        
        if template_file.exists():
            template_file.unlink()
            return True
        
        return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for cross-platform compatibility."""
        import re
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        return filename


# Global serializer instance
_global_serializer = WorkflowSerializer()


def save_workflow(workflow: WorkflowDefinition, file_path: Union[str, Path], 
                 format: str = None) -> None:
    """Save a workflow to a file using the global serializer."""
    _global_serializer.save_workflow(workflow, file_path, format)


def load_workflow(file_path: Union[str, Path], format: str = None) -> WorkflowDefinition:
    """Load a workflow from a file using the global serializer."""
    return _global_serializer.load_workflow(file_path, format)