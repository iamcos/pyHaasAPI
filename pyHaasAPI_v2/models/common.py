"""
Common data models for pyHaasAPI v2

Provides base models and common data structures used across all API modules.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Base API response wrapper"""
    success: bool = Field(alias="Success", default=True, description="Whether the request was successful")
    error: str = Field(alias="Error", default="", description="Error message if any")
    data: Optional[T] = Field(alias="Data", default=None, description="Response data")
    
    @validator("success")
    def validate_success(cls, v):
        """Validate success field"""
        return bool(v)
    
    @property
    def is_success(self) -> bool:
        """Check if response is successful"""
        return self.success and not self.error
    
    @property
    def is_error(self) -> bool:
        """Check if response contains an error"""
        return not self.success or bool(self.error)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response"""
    items: List[T] = Field(description="List of items in current page")
    total_count: int = Field(alias="totalCount", description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(alias="pageSize", default=100, description="Number of items per page")
    total_pages: int = Field(alias="totalPages", description="Total number of pages")
    has_next: bool = Field(alias="hasNext", default=False, description="Whether there is a next page")
    has_previous: bool = Field(alias="hasPrevious", default=False, description="Whether there is a previous page")
    
    @validator("total_count", "page", "page_size", "total_pages")
    def validate_positive_integers(cls, v):
        """Validate positive integer values"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
    
    @validator("total_pages")
    def validate_total_pages(cls, v, values):
        """Validate total pages calculation"""
        if "total_count" in values and "page_size" in values:
            expected_pages = (values["total_count"] + values["page_size"] - 1) // values["page_size"]
            if v != expected_pages:
                raise ValueError("Total pages calculation is incorrect")
        return v
    
    @validator("has_next", "has_previous")
    def validate_page_navigation(cls, v, values):
        """Validate page navigation flags"""
        if "page" in values and "total_pages" in values:
            if values["page"] < values["total_pages"] and not v:
                raise ValueError("has_next should be True when page < total_pages")
            if values["page"] > 1 and not v:
                raise ValueError("has_previous should be True when page > 1")
        return v


class ErrorResponse(BaseModel):
    """Error response model"""
    error_code: str = Field(alias="errorCode", description="Error code")
    error_message: str = Field(alias="errorMessage", description="Error message")
    error_details: Optional[Dict[str, Any]] = Field(alias="errorDetails", default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(alias="requestId", default=None, description="Request ID for tracking")
    
    @validator("error_code")
    def validate_error_code(cls, v):
        """Validate error code format"""
        if not v or not isinstance(v, str):
            raise ValueError("Error code must be a non-empty string")
        return v.upper()
    
    @validator("error_message")
    def validate_error_message(cls, v):
        """Validate error message"""
        if not v or not isinstance(v, str):
            raise ValueError("Error message must be a non-empty string")
        return v


class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime = Field(alias="createdAt", default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(alias="updatedAt", default=None, description="Last update timestamp")
    
    @validator("updated_at")
    def validate_updated_at(cls, v, values):
        """Validate updated_at is after created_at"""
        if v and "created_at" in values and v < values["created_at"]:
            raise ValueError("updated_at must be after created_at")
        return v


class IdentifiableModel(BaseModel):
    """Base model with ID field"""
    id: str = Field(description="Unique identifier")
    
    @validator("id")
    def validate_id(cls, v):
        """Validate ID format"""
        if not v or not isinstance(v, str):
            raise ValueError("ID must be a non-empty string")
        return v


class NamedModel(BaseModel):
    """Base model with name field"""
    name: str = Field(description="Name")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate name format"""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        return v.strip()


class StatusModel(BaseModel):
    """Base model with status field"""
    status: str = Field(description="Status")
    
    @validator("status")
    def validate_status(cls, v):
        """Validate status format"""
        if not v or not isinstance(v, str):
            raise ValueError("Status must be a non-empty string")
        return v.upper()


class ConfigurableModel(BaseModel):
    """Base model with configuration fields"""
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration parameters")
    
    @validator("config")
    def validate_config(cls, v):
        """Validate configuration"""
        if not isinstance(v, dict):
            raise ValueError("Config must be a dictionary")
        return v
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set_config_value(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
    
    def remove_config_value(self, key: str) -> Any:
        """Remove configuration value"""
        return self.config.pop(key, None)


class MetadataModel(BaseModel):
    """Base model with metadata fields"""
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    tags: List[str] = Field(default_factory=list, description="Tags")
    
    @validator("metadata")
    def validate_metadata(cls, v):
        """Validate metadata"""
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags"""
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        return [str(tag).strip() for tag in v if tag]
    
    def add_tag(self, tag: str) -> None:
        """Add a tag"""
        if tag and tag not in self.tags:
            self.tags.append(tag.strip())
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag"""
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
    
    def has_tag(self, tag: str) -> bool:
        """Check if model has a tag"""
        return tag in self.tags


class BaseEntityModel(TimestampedModel, IdentifiableModel, NamedModel, StatusModel, ConfigurableModel, MetadataModel):
    """Base model combining all common features"""
    pass


class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=100, ge=1, le=1000, description="Number of items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="asc", description="Sort order (asc or desc)")
    
    @validator("sort_order")
    def validate_sort_order(cls, v):
        """Validate sort order"""
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()
    
    @property
    def offset(self) -> int:
        """Calculate offset for pagination"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit for pagination"""
        return self.page_size


class FilterParams(BaseModel):
    """Filter parameters for API requests"""
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter criteria")
    
    @validator("filters")
    def validate_filters(cls, v):
        """Validate filters"""
        if not isinstance(v, dict):
            raise ValueError("Filters must be a dictionary")
        return v
    
    def add_filter(self, key: str, value: Any) -> None:
        """Add a filter"""
        self.filters[key] = value
    
    def remove_filter(self, key: str) -> Any:
        """Remove a filter"""
        return self.filters.pop(key, None)
    
    def get_filter(self, key: str, default: Any = None) -> Any:
        """Get a filter value"""
        return self.filters.get(key, default)
    
    def has_filter(self, key: str) -> bool:
        """Check if filter exists"""
        return key in self.filters


class SearchParams(BaseModel):
    """Search parameters for API requests"""
    query: Optional[str] = Field(default=None, description="Search query")
    search_fields: List[str] = Field(default_factory=list, description="Fields to search in")
    case_sensitive: bool = Field(default=False, description="Whether search is case sensitive")
    
    @validator("query")
    def validate_query(cls, v):
        """Validate search query"""
        if v is not None and not isinstance(v, str):
            raise ValueError("Query must be a string")
        return v.strip() if v else None
    
    @validator("search_fields")
    def validate_search_fields(cls, v):
        """Validate search fields"""
        if not isinstance(v, list):
            raise ValueError("Search fields must be a list")
        return [str(field).strip() for field in v if field]
