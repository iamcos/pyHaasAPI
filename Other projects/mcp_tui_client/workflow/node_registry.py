"""
Node registry for managing workflow node types.

This module provides a registry system for discovering and instantiating
different types of workflow nodes.
"""

from typing import Dict, Type, List, Optional, Callable
from .node_base import WorkflowNode
import inspect


class NodeCategory:
    """Categories for organizing nodes."""
    INPUT = "input"
    PROCESSING = "processing"
    OUTPUT = "output"
    TRADING = "trading"
    ANALYSIS = "analysis"
    MARKET_DATA = "market_data"
    UTILITY = "utility"


class NodeInfo:
    """Information about a registered node type."""
    
    def __init__(self, node_class: Type[WorkflowNode], category: str, 
                 display_name: str = None, description: str = None,
                 icon: str = None, tags: List[str] = None):
        self.node_class = node_class
        self.category = category
        self.display_name = display_name or node_class.__name__
        self.description = description or node_class.__doc__ or ""
        self.icon = icon or "⚙️"
        self.tags = tags or []
        self.node_type = node_class.__name__
    
    def create_instance(self, **kwargs) -> WorkflowNode:
        """Create an instance of this node type."""
        return self.node_class(**kwargs)


class NodeRegistry:
    """Registry for managing workflow node types."""
    
    def __init__(self):
        self._nodes: Dict[str, NodeInfo] = {}
        self._categories: Dict[str, List[str]] = {}
        self._tags: Dict[str, List[str]] = {}
    
    def register(self, node_class: Type[WorkflowNode], category: str,
                display_name: str = None, description: str = None,
                icon: str = None, tags: List[str] = None) -> None:
        """Register a node type."""
        if not issubclass(node_class, WorkflowNode):
            raise ValueError(f"Node class must inherit from WorkflowNode")
        
        node_type = node_class.__name__
        node_info = NodeInfo(
            node_class=node_class,
            category=category,
            display_name=display_name,
            description=description,
            icon=icon,
            tags=tags or []
        )
        
        self._nodes[node_type] = node_info
        
        # Update category index
        if category not in self._categories:
            self._categories[category] = []
        if node_type not in self._categories[category]:
            self._categories[category].append(node_type)
        
        # Update tag index
        for tag in node_info.tags:
            if tag not in self._tags:
                self._tags[tag] = []
            if node_type not in self._tags[tag]:
                self._tags[tag].append(node_type)
    
    def unregister(self, node_type: str) -> None:
        """Unregister a node type."""
        if node_type not in self._nodes:
            return
        
        node_info = self._nodes[node_type]
        
        # Remove from category index
        if node_info.category in self._categories:
            if node_type in self._categories[node_info.category]:
                self._categories[node_info.category].remove(node_type)
            if not self._categories[node_info.category]:
                del self._categories[node_info.category]
        
        # Remove from tag index
        for tag in node_info.tags:
            if tag in self._tags and node_type in self._tags[tag]:
                self._tags[tag].remove(node_type)
                if not self._tags[tag]:
                    del self._tags[tag]
        
        # Remove from main registry
        del self._nodes[node_type]
    
    def get_node_info(self, node_type: str) -> Optional[NodeInfo]:
        """Get information about a node type."""
        return self._nodes.get(node_type)
    
    def create_node(self, node_type: str, **kwargs) -> Optional[WorkflowNode]:
        """Create an instance of a node type."""
        node_info = self.get_node_info(node_type)
        if node_info:
            return node_info.create_instance(**kwargs)
        return None
    
    def get_all_nodes(self) -> Dict[str, NodeInfo]:
        """Get all registered node types."""
        return self._nodes.copy()
    
    def get_nodes_by_category(self, category: str) -> List[NodeInfo]:
        """Get all nodes in a specific category."""
        node_types = self._categories.get(category, [])
        return [self._nodes[node_type] for node_type in node_types]
    
    def get_nodes_by_tag(self, tag: str) -> List[NodeInfo]:
        """Get all nodes with a specific tag."""
        node_types = self._tags.get(tag, [])
        return [self._nodes[node_type] for node_type in node_types]
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return list(self._categories.keys())
    
    def get_tags(self) -> List[str]:
        """Get all available tags."""
        return list(self._tags.keys())
    
    def search_nodes(self, query: str) -> List[NodeInfo]:
        """Search for nodes by name, description, or tags."""
        query = query.lower()
        results = []
        
        for node_info in self._nodes.values():
            # Search in display name
            if query in node_info.display_name.lower():
                results.append(node_info)
                continue
            
            # Search in description
            if query in node_info.description.lower():
                results.append(node_info)
                continue
            
            # Search in tags
            if any(query in tag.lower() for tag in node_info.tags):
                results.append(node_info)
                continue
            
            # Search in node type
            if query in node_info.node_type.lower():
                results.append(node_info)
                continue
        
        return results
    
    def auto_discover(self, module_name: str) -> int:
        """Auto-discover and register nodes from a module."""
        try:
            import importlib
            module = importlib.import_module(module_name)
            registered_count = 0
            
            for name in dir(module):
                obj = getattr(module, name)
                
                # Check if it's a WorkflowNode subclass
                if (inspect.isclass(obj) and 
                    issubclass(obj, WorkflowNode) and 
                    obj != WorkflowNode):
                    
                    # Try to get registration info from class attributes
                    category = getattr(obj, '_category', NodeCategory.UTILITY)
                    display_name = getattr(obj, '_display_name', None)
                    description = getattr(obj, '_description', None)
                    icon = getattr(obj, '_icon', None)
                    tags = getattr(obj, '_tags', None)
                    
                    self.register(
                        node_class=obj,
                        category=category,
                        display_name=display_name,
                        description=description,
                        icon=icon,
                        tags=tags
                    )
                    registered_count += 1
            
            return registered_count
            
        except ImportError as e:
            raise ValueError(f"Could not import module '{module_name}': {e}")
    
    def get_node_statistics(self) -> Dict[str, int]:
        """Get statistics about registered nodes."""
        return {
            'total_nodes': len(self._nodes),
            'categories': len(self._categories),
            'tags': len(self._tags),
            'nodes_per_category': {
                category: len(nodes) 
                for category, nodes in self._categories.items()
            }
        }
    
    def validate_registry(self) -> List[str]:
        """Validate the registry and return any issues."""
        issues = []
        
        for node_type, node_info in self._nodes.items():
            try:
                # Try to create an instance to validate the node class
                instance = node_info.create_instance()
                
                # Validate that the node has required methods
                if not hasattr(instance, 'execute'):
                    issues.append(f"Node '{node_type}' missing execute method")
                
                if not hasattr(instance, 'validate'):
                    issues.append(f"Node '{node_type}' missing validate method")
                
                # Validate ports are properly initialized
                if not hasattr(instance, 'inputs') or not hasattr(instance, 'outputs'):
                    issues.append(f"Node '{node_type}' missing input/output ports")
                
            except Exception as e:
                issues.append(f"Node '{node_type}' cannot be instantiated: {e}")
        
        return issues


# Global registry instance
_global_registry = NodeRegistry()


def register_node(category: str, display_name: str = None, 
                 description: str = None, icon: str = None, 
                 tags: List[str] = None):
    """Decorator for registering node classes."""
    def decorator(node_class: Type[WorkflowNode]):
        _global_registry.register(
            node_class=node_class,
            category=category,
            display_name=display_name,
            description=description,
            icon=icon,
            tags=tags
        )
        return node_class
    return decorator


def get_global_registry() -> NodeRegistry:
    """Get the global node registry."""
    return _global_registry