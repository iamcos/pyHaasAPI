"""
Common data models for pyHaasAPI v2

Provides base models and common data structures used across all API modules.
Removes Pydantic dependency in favor of standard dataclasses.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic, Union, Type
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime

T = TypeVar("T")


class BaseModel:
    """
    Base model for all data classes providing dictionary serialization/deserialization
    with robust case-insensitive field mapping.
    """
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create instance from dictionary with safe field mapping
        
        Handles:
        - Case-insensitive key lookup
        - Common variations (PascalCase, camelCase, snake_case, short codes)
        - Nested dictionary conversion
        - List of objects conversion
        """
        if not data:
            return cls()
            
        # Get all fields for this dataclass
        if not is_dataclass(cls):
            raise TypeError(f"{cls.__name__} must be a dataclass")
            
        cls_fields = fields(cls)
        init_kwargs = {}
        
        # Helper to find value in data dictionary
        def find_value(field_name: str, field_type: Any) -> Any:
            # Try exact match first
            if field_name in data:
                return data[field_name]
                
            # Try variations
            variations = [
                field_name.lower(),
                field_name.upper(),
                field_name.title(),
                field_name.replace("_", ""),
                field_name.replace("_", "").lower(),
                # Common API short codes
                "".join([part[0].upper() for part in field_name.split("_")]), # e.g. script_id -> SI
                field_name.split("_")[-1].upper(), # e.g. lab_id -> ID
                "".join([part[0].upper() for part in field_name.split("_")]) + "D", # e.g. lab_id -> LID
            ]
            
            # Additional manual mappings can be added here or in specific models
            
            for key in data.keys():
                if key.lower() in variations or key in variations:
                    return data[key]
                    
            return None

        # Helper to process value based on type
        def process_value(value: Any, field_type: Any) -> Any:
            if value is None:
                return None
                
            # Handle recursive BaseModel/dataclass
            if hasattr(field_type, "from_dict") and isinstance(value, dict):
                return field_type.from_dict(value)
                
            # Handle List[BaseModel]
            # This is a basic check, might need more robust typing inspection for complex generics
            origin = getattr(field_type, "__origin__", None)
            args = getattr(field_type, "__args__", [])
            
            if origin is list and args:
                item_type = args[0]
                if hasattr(item_type, "from_dict") and isinstance(value, list):
                    return [item_type.from_dict(item) for item in value if isinstance(item, dict)]
            
            return value

        for f in cls_fields:
            raw_value = find_value(f.name, f.type)
            
            if raw_value is not None:
                init_kwargs[f.name] = process_value(raw_value, f.type)
        
        return cls(**init_kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if hasattr(value, "to_dict"):
                result[f.name] = value.to_dict()
            elif isinstance(value, list):
                result[f.name] = [
                    item.to_dict() if hasattr(item, "to_dict") else item 
                    for item in value
                ]
            else:
                result[f.name] = value
        return result


@dataclass
class ApiResponse(BaseModel, Generic[T]):
    """Base API response wrapper"""
    success: bool = True
    error: str = ""
    data: Optional[T] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApiResponse':
        # Custom handling for standard API response structure
        instance = cls()
        
        # Handle Success flag (boolean or int or string)
        success_val = data.get("Success", data.get("success", True))
        if isinstance(success_val, str):
            instance.success = success_val.lower() == "true"
        else:
            instance.success = bool(success_val)
            
        instance.error = str(data.get("Error", data.get("error", "")))
        
        # Data is generic, left as is or processed by caller
        instance.data = data.get("Data", data.get("data", None))
        
        return instance

    @property
    def is_success(self) -> bool:
        return self.success and not self.error

    @property
    def is_error(self) -> bool:
        return not self.success or bool(self.error)


@dataclass
class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response"""
    items: List[T] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 100
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False


@dataclass
class ErrorResponse(BaseModel):
    """Error response model"""
    error_code: str = ""
    error_message: str = ""
    error_details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = None


@dataclass
class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


@dataclass
class IdentifiableModel(BaseModel):
    """Base model with ID field"""
    id: str = ""


@dataclass
class NamedModel(BaseModel):
    """Base model with name field"""
    name: str = ""


@dataclass
class StatusModel(BaseModel):
    """Base model with status field"""
    status: str = ""


@dataclass
class ConfigurableModel(BaseModel):
    """Base model with configuration fields"""
    config: Dict[str, Any] = field(default_factory=dict)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set_config_value(self, key: str, value: Any) -> None:
        self.config[key] = value
    
    def remove_config_value(self, key: str) -> Any:
        return self.config.pop(key, None)


@dataclass
class MetadataModel(BaseModel):
    """Base model with metadata fields"""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def add_tag(self, tag: str) -> None:
        if tag and tag not in self.tags:
            self.tags.append(tag.strip())
    
    def remove_tag(self, tag: str) -> bool:
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def has_tag(self, tag: str) -> bool:
        return tag in self.tags


@dataclass
class BaseEntityModel(TimestampedModel, IdentifiableModel, NamedModel, StatusModel, ConfigurableModel, MetadataModel):
    """Base model combining all common features"""
    pass


@dataclass
class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = 1
    page_size: int = 100
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class FilterParams(BaseModel):
    """Filter parameters for API requests"""
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def add_filter(self, key: str, value: Any) -> None:
        self.filters[key] = value
    
    def remove_filter(self, key: str) -> Any:
        return self.filters.pop(key, None)
    
    def get_filter(self, key: str, default: Any = None) -> Any:
        return self.filters.get(key, default)
    
    def has_filter(self, key: str) -> bool:
        return key in self.filters


@dataclass
class SearchParams(BaseModel):
    """Search parameters for API requests"""
    query: Optional[str] = None
    search_fields: List[str] = field(default_factory=list)
    case_sensitive: bool = False
