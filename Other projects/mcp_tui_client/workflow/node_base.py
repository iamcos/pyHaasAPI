"""
Base classes for workflow nodes and connections.

This module defines the core abstractions for the node-based workflow system,
including node ports, connections, and validation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type, Optional, Union, Callable
from enum import Enum
import json
import uuid
from datetime import datetime


class PortType(Enum):
    """Types of node ports."""
    INPUT = "input"
    OUTPUT = "output"


class DataType(Enum):
    """Supported data types for node ports."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DICT = "dict"
    LIST = "list"
    BACKTEST_RESULT = "backtest_result"
    BOT_CONFIG = "bot_config"
    MARKET_DATA = "market_data"
    PERFORMANCE_METRICS = "performance_metrics"
    TRADE_LOG = "trade_log"
    ANALYSIS_RESULT = "analysis_result"
    CHART_DATA = "chart_data"
    ALERT_CONFIG = "alert_config"


@dataclass
class ValidationError:
    """Represents a validation error in a workflow node."""
    node_id: str
    message: str
    error_type: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class NodePort:
    """Represents an input or output port on a workflow node."""
    name: str
    port_type: PortType
    data_type: DataType
    required: bool = True
    description: str = ""
    default_value: Any = None
    connections: List['Connection'] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate port configuration after initialization."""
        if not self.name:
            raise ValueError("Port name cannot be empty")
        if self.port_type == PortType.OUTPUT and self.default_value is not None:
            raise ValueError("Output ports cannot have default values")
    
    def can_connect_to(self, other_port: 'NodePort') -> bool:
        """Check if this port can connect to another port."""
        if self.port_type == other_port.port_type:
            return False  # Cannot connect same port types
        
        if self.port_type == PortType.OUTPUT:
            # This is output, other is input
            return self.data_type == other_port.data_type
        else:
            # This is input, other is output
            return other_port.data_type == self.data_type
    
    def add_connection(self, connection: 'Connection') -> None:
        """Add a connection to this port."""
        if connection not in self.connections:
            self.connections.append(connection)
    
    def remove_connection(self, connection: 'Connection') -> None:
        """Remove a connection from this port."""
        if connection in self.connections:
            self.connections.remove(connection)
    
    def is_connected(self) -> bool:
        """Check if this port has any connections."""
        return len(self.connections) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize port to dictionary."""
        return {
            'name': self.name,
            'port_type': self.port_type.value,
            'data_type': self.data_type.value,
            'required': self.required,
            'description': self.description,
            'default_value': self.default_value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodePort':
        """Deserialize port from dictionary."""
        return cls(
            name=data['name'],
            port_type=PortType(data['port_type']),
            data_type=DataType(data['data_type']),
            required=data.get('required', True),
            description=data.get('description', ''),
            default_value=data.get('default_value')
        )


@dataclass
class Connection:
    """Represents a connection between two node ports."""
    connection_id: str
    source_node_id: str
    source_port_name: str
    target_node_id: str
    target_port_name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate connection after initialization."""
        if not all([self.source_node_id, self.source_port_name, 
                   self.target_node_id, self.target_port_name]):
            raise ValueError("All connection fields must be specified")
        
        if self.source_node_id == self.target_node_id:
            raise ValueError("Cannot connect node to itself")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize connection to dictionary."""
        return {
            'connection_id': self.connection_id,
            'source_node_id': self.source_node_id,
            'source_port_name': self.source_port_name,
            'target_node_id': self.target_node_id,
            'target_port_name': self.target_port_name,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Connection':
        """Deserialize connection from dictionary."""
        return cls(
            connection_id=data['connection_id'],
            source_node_id=data['source_node_id'],
            source_port_name=data['source_port_name'],
            target_node_id=data['target_node_id'],
            target_port_name=data['target_port_name'],
            created_at=datetime.fromisoformat(data['created_at'])
        )


class WorkflowNode(ABC):
    """Base class for all workflow nodes."""
    
    def __init__(self, node_id: str = None, name: str = "", description: str = ""):
        """Initialize workflow node."""
        self.node_id = node_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.description = description
        self.inputs: Dict[str, NodePort] = {}
        self.outputs: Dict[str, NodePort] = {}
        self.parameters: Dict[str, Any] = {}
        self.position: Dict[str, float] = {'x': 0, 'y': 0}
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        
        # Initialize node-specific ports and parameters
        self._initialize_ports()
        self._initialize_parameters()
    
    @abstractmethod
    def _initialize_ports(self) -> None:
        """Initialize input and output ports for this node type."""
        pass
    
    @abstractmethod
    def _initialize_parameters(self) -> None:
        """Initialize parameters for this node type."""
        pass
    
    @abstractmethod
    async def execute(self, context: 'ExecutionContext') -> Dict[str, Any]:
        """Execute the node logic and return output values."""
        pass
    
    def validate(self) -> List[ValidationError]:
        """Validate node configuration and return any errors."""
        errors = []
        
        # Check required input ports are connected or have default values
        for port_name, port in self.inputs.items():
            if port.required and not port.is_connected() and port.default_value is None:
                errors.append(ValidationError(
                    node_id=self.node_id,
                    message=f"Required input port '{port_name}' is not connected",
                    error_type="missing_connection"
                ))
        
        # Validate parameters
        param_errors = self._validate_parameters()
        errors.extend(param_errors)
        
        return errors
    
    def _validate_parameters(self) -> List[ValidationError]:
        """Validate node parameters. Override in subclasses."""
        return []
    
    def add_input_port(self, name: str, data_type: DataType, required: bool = True, 
                      description: str = "", default_value: Any = None) -> NodePort:
        """Add an input port to the node."""
        port = NodePort(
            name=name,
            port_type=PortType.INPUT,
            data_type=data_type,
            required=required,
            description=description,
            default_value=default_value
        )
        self.inputs[name] = port
        return port
    
    def add_output_port(self, name: str, data_type: DataType, 
                       description: str = "") -> NodePort:
        """Add an output port to the node."""
        port = NodePort(
            name=name,
            port_type=PortType.OUTPUT,
            data_type=data_type,
            description=description
        )
        self.outputs[name] = port
        return port
    
    def get_input_value(self, port_name: str, context: 'ExecutionContext') -> Any:
        """Get the value for an input port from connected nodes or default."""
        if port_name not in self.inputs:
            raise ValueError(f"Input port '{port_name}' not found")
        
        port = self.inputs[port_name]
        
        # If port is connected, get value from source node
        if port.connections:
            connection = port.connections[0]  # Assume single connection for inputs
            source_node_id = connection.source_node_id
            source_port_name = connection.source_port_name
            
            if source_node_id in context.node_outputs:
                source_outputs = context.node_outputs[source_node_id]
                if source_port_name in source_outputs:
                    return source_outputs[source_port_name]
            
            raise RuntimeError(f"Source node '{source_node_id}' output not available")
        
        # Use default value if available
        if port.default_value is not None:
            return port.default_value
        
        # Check if value is in parameters
        if port_name in self.parameters:
            return self.parameters[port_name]
        
        if port.required:
            raise RuntimeError(f"Required input port '{port_name}' has no value")
        
        return None
    
    def set_parameter(self, name: str, value: Any) -> None:
        """Set a parameter value."""
        self.parameters[name] = value
        self.modified_at = datetime.now()
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a parameter value."""
        return self.parameters.get(name, default)
    
    def set_position(self, x: float, y: float) -> None:
        """Set node position in workflow canvas."""
        self.position = {'x': x, 'y': y}
        self.modified_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            'node_id': self.node_id,
            'node_type': self.__class__.__name__,
            'name': self.name,
            'description': self.description,
            'position': self.position,
            'parameters': self.parameters,
            'inputs': {name: port.to_dict() for name, port in self.inputs.items()},
            'outputs': {name: port.to_dict() for name, port in self.outputs.items()},
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowNode':
        """Deserialize node from dictionary. Override in subclasses."""
        # This is a base implementation - subclasses should override
        node = cls(
            node_id=data['node_id'],
            name=data['name'],
            description=data['description']
        )
        node.position = data['position']
        node.parameters = data['parameters']
        node.created_at = datetime.fromisoformat(data['created_at'])
        node.modified_at = datetime.fromisoformat(data['modified_at'])
        return node
    
    def clone(self) -> 'WorkflowNode':
        """Create a copy of this node with a new ID."""
        node_dict = self.to_dict()
        node_dict['node_id'] = str(uuid.uuid4())
        node_dict['created_at'] = datetime.now().isoformat()
        node_dict['modified_at'] = datetime.now().isoformat()
        return self.__class__.from_dict(node_dict)
    
    def __str__(self) -> str:
        """String representation of the node."""
        return f"{self.__class__.__name__}(id={self.node_id[:8]}, name='{self.name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation of the node."""
        return (f"{self.__class__.__name__}(node_id='{self.node_id}', "
                f"name='{self.name}', inputs={len(self.inputs)}, "
                f"outputs={len(self.outputs)})")