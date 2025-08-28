"""
Workflow definition and execution context classes.

This module defines the structure for workflows and execution contexts.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import json
import uuid

from .node_base import WorkflowNode, Connection, ValidationError


@dataclass
class ExecutionContext:
    """Context for workflow execution."""
    workflow_id: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    execution_state: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    current_node: Optional[str] = None
    completed_nodes: Set[str] = field(default_factory=set)
    failed_nodes: Set[str] = field(default_factory=set)
    progress_callback: Optional[callable] = None
    
    def set_node_output(self, node_id: str, port_name: str, value: Any) -> None:
        """Set output value for a node port."""
        if node_id not in self.node_outputs:
            self.node_outputs[node_id] = {}
        self.node_outputs[node_id][port_name] = value
    
    def get_node_output(self, node_id: str, port_name: str) -> Any:
        """Get output value from a node port."""
        return self.node_outputs.get(node_id, {}).get(port_name)
    
    def mark_node_completed(self, node_id: str) -> None:
        """Mark a node as completed."""
        self.completed_nodes.add(node_id)
        if node_id in self.failed_nodes:
            self.failed_nodes.remove(node_id)
    
    def mark_node_failed(self, node_id: str) -> None:
        """Mark a node as failed."""
        self.failed_nodes.add(node_id)
        if node_id in self.completed_nodes:
            self.completed_nodes.remove(node_id)
    
    def is_node_completed(self, node_id: str) -> bool:
        """Check if a node is completed."""
        return node_id in self.completed_nodes
    
    def is_node_failed(self, node_id: str) -> bool:
        """Check if a node failed."""
        return node_id in self.failed_nodes
    
    def get_progress(self, total_nodes: int) -> float:
        """Get execution progress as percentage."""
        if total_nodes == 0:
            return 100.0
        return (len(self.completed_nodes) / total_nodes) * 100.0
    
    def report_progress(self, message: str = None) -> None:
        """Report progress to callback if available."""
        if self.progress_callback:
            self.progress_callback(self, message)


@dataclass
class WorkflowMetadata:
    """Metadata for a workflow."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'author': self.author,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowMetadata':
        """Deserialize metadata from dictionary."""
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            author=data.get('author', ''),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at'])
        )


class WorkflowDefinition:
    """Definition of a workflow with nodes and connections."""
    
    def __init__(self, workflow_id: str = None, metadata: WorkflowMetadata = None):
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.metadata = metadata or WorkflowMetadata(name="Untitled Workflow")
        self.nodes: Dict[str, WorkflowNode] = {}
        self.connections: Dict[str, Connection] = {}
        self._dependency_graph: Optional[Dict[str, Set[str]]] = None
        self._reverse_dependency_graph: Optional[Dict[str, Set[str]]] = None
    
    def add_node(self, node: WorkflowNode) -> None:
        """Add a node to the workflow."""
        self.nodes[node.node_id] = node
        self._invalidate_dependency_cache()
        self.metadata.modified_at = datetime.now()
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its connections."""
        if node_id not in self.nodes:
            return
        
        # Remove all connections involving this node
        connections_to_remove = []
        for conn_id, connection in self.connections.items():
            if (connection.source_node_id == node_id or 
                connection.target_node_id == node_id):
                connections_to_remove.append(conn_id)
        
        for conn_id in connections_to_remove:
            self.remove_connection(conn_id)
        
        # Remove the node
        del self.nodes[node_id]
        self._invalidate_dependency_cache()
        self.metadata.modified_at = datetime.now()
    
    def add_connection(self, connection: Connection) -> bool:
        """Add a connection between nodes."""
        # Validate connection
        if connection.source_node_id not in self.nodes:
            raise ValueError(f"Source node '{connection.source_node_id}' not found")
        
        if connection.target_node_id not in self.nodes:
            raise ValueError(f"Target node '{connection.target_node_id}' not found")
        
        source_node = self.nodes[connection.source_node_id]
        target_node = self.nodes[connection.target_node_id]
        
        if connection.source_port_name not in source_node.outputs:
            raise ValueError(f"Source port '{connection.source_port_name}' not found")
        
        if connection.target_port_name not in target_node.inputs:
            raise ValueError(f"Target port '{connection.target_port_name}' not found")
        
        source_port = source_node.outputs[connection.source_port_name]
        target_port = target_node.inputs[connection.target_port_name]
        
        # Check port compatibility
        if not source_port.can_connect_to(target_port):
            raise ValueError(f"Incompatible port types: {source_port.data_type} -> {target_port.data_type}")
        
        # Check for cycles
        if self._would_create_cycle(connection):
            raise ValueError("Connection would create a cycle in the workflow")
        
        # Add connection
        self.connections[connection.connection_id] = connection
        source_port.add_connection(connection)
        target_port.add_connection(connection)
        
        self._invalidate_dependency_cache()
        self.metadata.modified_at = datetime.now()
        return True
    
    def remove_connection(self, connection_id: str) -> None:
        """Remove a connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Remove from ports
        source_node = self.nodes.get(connection.source_node_id)
        target_node = self.nodes.get(connection.target_node_id)
        
        if source_node and connection.source_port_name in source_node.outputs:
            source_port = source_node.outputs[connection.source_port_name]
            source_port.remove_connection(connection)
        
        if target_node and connection.target_port_name in target_node.inputs:
            target_port = target_node.inputs[connection.target_port_name]
            target_port.remove_connection(connection)
        
        # Remove from workflow
        del self.connections[connection_id]
        self._invalidate_dependency_cache()
        self.metadata.modified_at = datetime.now()
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        return self.connections.get(connection_id)
    
    def validate(self) -> List[ValidationError]:
        """Validate the entire workflow."""
        errors = []
        
        # Validate individual nodes
        for node in self.nodes.values():
            node_errors = node.validate()
            errors.extend(node_errors)
        
        # Check for disconnected required inputs
        for node in self.nodes.values():
            for port_name, port in node.inputs.items():
                if port.required and not port.is_connected() and port.default_value is None:
                    errors.append(ValidationError(
                        node_id=node.node_id,
                        message=f"Required input '{port_name}' is not connected",
                        error_type="disconnected_input"
                    ))
        
        # Check for cycles
        if self._has_cycles():
            errors.append(ValidationError(
                node_id="workflow",
                message="Workflow contains cycles",
                error_type="cycle_detected"
            ))
        
        return errors
    
    def get_execution_order(self) -> List[str]:
        """Get nodes in execution order (topological sort)."""
        if not self.nodes:
            return []
        
        # Build dependency graph
        self._build_dependency_graph()
        
        # Topological sort using Kahn's algorithm
        in_degree = {node_id: 0 for node_id in self.nodes}
        
        for node_id, dependencies in self._dependency_graph.items():
            for dep in dependencies:
                in_degree[node_id] += 1
        
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node_id = queue.pop(0)
            result.append(node_id)
            
            # Update in-degrees of dependent nodes
            for dependent in self._reverse_dependency_graph.get(node_id, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if len(result) != len(self.nodes):
            raise ValueError("Workflow contains cycles - cannot determine execution order")
        
        return result
    
    def _build_dependency_graph(self) -> None:
        """Build dependency graphs for execution ordering."""
        if self._dependency_graph is not None:
            return
        
        self._dependency_graph = {node_id: set() for node_id in self.nodes}
        self._reverse_dependency_graph = {node_id: set() for node_id in self.nodes}
        
        for connection in self.connections.values():
            source_id = connection.source_node_id
            target_id = connection.target_node_id
            
            # Target depends on source
            self._dependency_graph[target_id].add(source_id)
            self._reverse_dependency_graph[source_id].add(target_id)
    
    def _invalidate_dependency_cache(self) -> None:
        """Invalidate cached dependency graphs."""
        self._dependency_graph = None
        self._reverse_dependency_graph = None
    
    def _would_create_cycle(self, new_connection: Connection) -> bool:
        """Check if adding a connection would create a cycle."""
        # Temporarily add the connection to check for cycles
        temp_connections = self.connections.copy()
        temp_connections[new_connection.connection_id] = new_connection
        
        # Build temporary dependency graph
        temp_deps = {node_id: set() for node_id in self.nodes}
        
        for connection in temp_connections.values():
            source_id = connection.source_node_id
            target_id = connection.target_node_id
            temp_deps[target_id].add(source_id)
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle_dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dep in temp_deps.get(node_id, set()):
                if dep not in visited:
                    if has_cycle_dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle_dfs(node_id):
                    return True
        
        return False
    
    def _has_cycles(self) -> bool:
        """Check if the workflow has cycles."""
        self._build_dependency_graph()
        
        visited = set()
        rec_stack = set()
        
        def has_cycle_dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for dep in self._dependency_graph.get(node_id, set()):
                if dep not in visited:
                    if has_cycle_dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node_id)
            return False
        
        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle_dfs(node_id):
                    return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize workflow to dictionary."""
        return {
            'workflow_id': self.workflow_id,
            'metadata': self.metadata.to_dict(),
            'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            'connections': {conn_id: conn.to_dict() for conn_id, conn in self.connections.items()}
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize workflow to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], node_registry=None) -> 'WorkflowDefinition':
        """Deserialize workflow from dictionary."""
        from .node_registry import get_global_registry
        
        if node_registry is None:
            node_registry = get_global_registry()
        
        workflow = cls(
            workflow_id=data['workflow_id'],
            metadata=WorkflowMetadata.from_dict(data['metadata'])
        )
        
        # Recreate nodes
        for node_id, node_data in data['nodes'].items():
            node_type = node_data['node_type']
            node_info = node_registry.get_node_info(node_type)
            
            if node_info:
                node = node_info.node_class.from_dict(node_data)
                workflow.nodes[node_id] = node
            else:
                raise ValueError(f"Unknown node type: {node_type}")
        
        # Recreate connections
        for conn_id, conn_data in data['connections'].items():
            connection = Connection.from_dict(conn_data)
            workflow.connections[conn_id] = connection
            
            # Restore port connections
            source_node = workflow.nodes[connection.source_node_id]
            target_node = workflow.nodes[connection.target_node_id]
            
            if connection.source_port_name in source_node.outputs:
                source_port = source_node.outputs[connection.source_port_name]
                source_port.add_connection(connection)
            
            if connection.target_port_name in target_node.inputs:
                target_port = target_node.inputs[connection.target_port_name]
                target_port.add_connection(connection)
        
        return workflow
    
    @classmethod
    def from_json(cls, json_str: str, node_registry=None) -> 'WorkflowDefinition':
        """Deserialize workflow from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data, node_registry)
    
    def clone(self, new_name: str = None) -> 'WorkflowDefinition':
        """Create a copy of this workflow."""
        workflow_dict = self.to_dict()
        workflow_dict['workflow_id'] = str(uuid.uuid4())
        
        if new_name:
            workflow_dict['metadata']['name'] = new_name
        
        # Generate new IDs for nodes and connections
        node_id_mapping = {}
        for old_node_id in workflow_dict['nodes']:
            new_node_id = str(uuid.uuid4())
            node_id_mapping[old_node_id] = new_node_id
        
        # Update node IDs
        new_nodes = {}
        for old_node_id, node_data in workflow_dict['nodes'].items():
            new_node_id = node_id_mapping[old_node_id]
            node_data['node_id'] = new_node_id
            new_nodes[new_node_id] = node_data
        workflow_dict['nodes'] = new_nodes
        
        # Update connection IDs and node references
        new_connections = {}
        for conn_data in workflow_dict['connections'].values():
            conn_data['connection_id'] = str(uuid.uuid4())
            conn_data['source_node_id'] = node_id_mapping[conn_data['source_node_id']]
            conn_data['target_node_id'] = node_id_mapping[conn_data['target_node_id']]
            new_connections[conn_data['connection_id']] = conn_data
        workflow_dict['connections'] = new_connections
        
        return self.from_dict(workflow_dict)


# Alias for backward compatibility
Workflow = WorkflowDefinition