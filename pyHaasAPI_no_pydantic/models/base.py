"""
Base model classes for pyHaasAPI_no_pydantic

Provides base dataclass models with validation and serialization,
replacing Pydantic BaseModel with better performance.
"""

from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Any, Union, Type
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationMixin:
    """Mixin for validation functionality"""
    
    def validate(self) -> None:
        """Override in subclasses for custom validation"""
        pass
    
    def is_valid(self) -> bool:
        """Check if model is valid"""
        try:
            self.validate()
            return True
        except (ValueError, TypeError) as e:
            logger.warning(f"Validation failed for {self.__class__.__name__}: {e}")
            return False


@dataclass
class SerializationMixin:
    """Mixin for serialization functionality"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with field aliases"""
        result = {}
        for field_info in fields(self):
            field_name = field_info.name
            alias = getattr(field_info, 'alias', field_name)
            value = getattr(self, field_name)
            
            # Handle special types
            if isinstance(value, datetime):
                result[alias] = value.isoformat()
            elif hasattr(value, 'to_dict'):
                result[alias] = value.to_dict()
            elif isinstance(value, list):
                result[alias] = [
                    item.to_dict() if hasattr(item, 'to_dict') else item
                    for item in value
                ]
            else:
                result[alias] = value
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary with field aliases"""
        # Handle field aliases
        field_mapping = {}
        for field_info in fields(cls):
            field_name = field_info.name
            alias = getattr(field_info, 'alias', field_name)
            
            # Try alias first, then field name
            if alias in data:
                field_mapping[field_name] = data[alias]
            elif field_name in data:
                field_mapping[field_name] = data[field_name]
            elif hasattr(field_info, 'default'):
                # Use default value if available
                field_mapping[field_name] = field_info.default
            elif hasattr(field_info, 'default_factory'):
                # Use default factory if available
                field_mapping[field_name] = field_info.default_factory()
        
        return cls(**field_mapping)


@dataclass
class BaseModel(ValidationMixin, SerializationMixin):
    """
    Base model class with validation and serialization
    
    Replaces Pydantic BaseModel with dataclass-based implementation
    that provides better performance and simpler code.
    """
    
    def __post_init__(self):
        """Called after dataclass initialization"""
        # Auto-validate if validation is enabled
        if hasattr(self, '_auto_validate') and self._auto_validate:
            self.validate()
    
    def copy(self, **updates) -> 'BaseModel':
        """Create a copy with optional updates"""
        from dataclasses import asdict, replace
        
        current_data = asdict(self)
        current_data.update(updates)
        return self.__class__(**current_data)
    
    def update(self, **updates) -> 'BaseModel':
        """Create updated instance with new values"""
        return self.copy(**updates)
    
    def __str__(self) -> str:
        """String representation"""
        return f"{self.__class__.__name__}({', '.join(f'{k}={v}' for k, v in self.to_dict().items())})"
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in self.to_dict().items())})"


# Field function for creating fields with aliases (similar to Pydantic Field)
def Field(default=None, alias=None, description=None, **kwargs):
    """Create a field with alias support"""
    if alias:
        field_obj = field(default=default, **kwargs)
        field_obj.alias = alias
        if description:
            field_obj.description = description
        return field_obj
    return field(default=default, **kwargs)



