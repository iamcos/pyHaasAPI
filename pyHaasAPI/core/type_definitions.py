"""
Type Definitions for pyHaasAPI v2

This module provides comprehensive type definitions and protocols
for ensuring type safety throughout the codebase.
"""

from typing import (
    Any, Dict, List, Optional, Union, Tuple, Callable, Awaitable, 
    Protocol, TypeVar, Generic, Literal, TypedDict, NamedTuple
)
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

# Type Variables
T = TypeVar('T')
R = TypeVar('R')
K = TypeVar('K')
V = TypeVar('V')

# Common Type Aliases
JSONValue = Union[str, int, float, bool, None, List['JSONValue'], Dict[str, 'JSONValue']]
JSONDict = Dict[str, JSONValue]
JSONList = List[JSONValue]

# ID Types
LabID = str
BotID = str
AccountID = str
ScriptID = str
MarketTag = str
BacktestID = str
OrderID = str

# Status Types
class LabStatus(Enum):
    """Lab execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BotStatus(Enum):
    """Bot status"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"

class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class PositionMode(Enum):
    """Position mode"""
    HEDGE = "hedge"
    ONE_WAY = "one_way"

class MarginMode(Enum):
    """Margin mode"""
    CROSS = "cross"
    ISOLATED = "isolated"

# Protocol Definitions
class AsyncClientProtocol(Protocol):
    """Protocol for async client"""
    async def execute(self, request: Any) -> Any: ...
    async def get(self, endpoint: str, **kwargs) -> Any: ...
    async def post(self, endpoint: str, data: Any = None, **kwargs) -> Any: ...
    async def put(self, endpoint: str, data: Any = None, **kwargs) -> Any: ...
    async def delete(self, endpoint: str, **kwargs) -> Any: ...

class AuthenticationProtocol(Protocol):
    """Protocol for authentication"""
    async def authenticate(self, email: str, password: str) -> Any: ...
    async def refresh_token(self) -> Any: ...
    async def logout(self) -> None: ...
    def is_authenticated(self) -> bool: ...

class CacheProtocol(Protocol):
    """Protocol for caching"""
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def clear(self) -> None: ...

class LoggerProtocol(Protocol):
    """Protocol for logging"""
    def debug(self, message: str, **kwargs) -> None: ...
    def info(self, message: str, **kwargs) -> None: ...
    def warning(self, message: str, **kwargs) -> None: ...
    def error(self, message: str, **kwargs) -> None: ...
    def critical(self, message: str, **kwargs) -> None: ...

# Data Structure Types
@dataclass
class TimeRange:
    """Time range specification"""
    start: datetime
    end: datetime

@dataclass
class PaginationParams:
    """Pagination parameters"""
    page: int = 0
    page_size: int = 100
    max_pages: Optional[int] = None

@dataclass
class FilterParams:
    """Filter parameters"""
    field: str
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", "contains", "regex"]
    value: Any

@dataclass
class SortParams:
    """Sort parameters"""
    field: str
    direction: Literal["asc", "desc"] = "asc"

# API Request/Response Types
class APIRequest(TypedDict, total=False):
    """Base API request structure"""
    method: str
    endpoint: str
    data: Optional[JSONDict]
    params: Optional[JSONDict]
    headers: Optional[Dict[str, str]]

class APIResponse(TypedDict, total=False):
    """Base API response structure"""
    status_code: int
    data: Optional[JSONValue]
    error: Optional[str]
    timestamp: str

# Configuration Types
@dataclass
class ClientConfig:
    """Client configuration"""
    host: str = "127.0.0.1"
    port: int = 8090
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    verify_ssl: bool = True

@dataclass
class AuthConfig:
    """Authentication configuration"""
    email: str
    password: str
    auto_refresh: bool = True
    refresh_threshold: float = 300.0  # 5 minutes

@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    ttl: float = 300.0  # 5 minutes
    max_size: int = 1000
    cleanup_interval: float = 600.0  # 10 minutes

# Error Types
class ErrorCode(Enum):
    """Error codes"""
    AUTHENTICATION_FAILED = "auth_failed"
    INVALID_REQUEST = "invalid_request"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"

@dataclass
class APIError:
    """API error structure"""
    code: ErrorCode
    message: str
    details: Optional[JSONDict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# Performance Types
@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0

@dataclass
class RequestMetrics:
    """Request metrics"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()

# Validation Types
class ValidationLevel(Enum):
    """Validation level"""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"

@dataclass
class ValidationConfig:
    """Validation configuration"""
    level: ValidationLevel = ValidationLevel.BASIC
    validate_inputs: bool = True
    validate_outputs: bool = True
    validate_types: bool = True
    validate_ranges: bool = True

# File Types
class FileType(Enum):
    """File types"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    TXT = "txt"
    BINARY = "binary"

@dataclass
class FileInfo:
    """File information"""
    path: Path
    size: int
    type: FileType
    created: datetime
    modified: datetime
    checksum: Optional[str] = None

# Event Types
class EventType(Enum):
    """Event types"""
    REQUEST_START = "request_start"
    REQUEST_END = "request_end"
    REQUEST_ERROR = "request_error"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"

@dataclass
class Event:
    """Event structure"""
    type: EventType
    data: JSONDict
    timestamp: datetime
    source: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# Callback Types
RequestCallback = Callable[[APIRequest], Awaitable[None]]
ResponseCallback = Callable[[APIResponse], Awaitable[None]]
ErrorCallback = Callable[[APIError], Awaitable[None]]
EventCallback = Callable[[Event], Awaitable[None]]

# Generic Types
@dataclass
class Result(Generic[T]):
    """Generic result type"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Optional[JSONDict] = None

@dataclass
class PaginatedResult(Generic[T]):
    """Paginated result type"""
    items: List[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

@dataclass
class BatchResult(Generic[T]):
    """Batch result type"""
    successful: List[T]
    failed: List[Tuple[T, str]]
    total: int
    success_rate: float

# Utility Types
class OptionalDict(TypedDict, total=False):
    """Optional dictionary type"""
    pass

class RequiredDict(TypedDict):
    """Required dictionary type"""
    pass

# Function Types
AsyncFunction = Callable[..., Awaitable[Any]]
SyncFunction = Callable[..., Any]
ValidatorFunction = Callable[[Any], bool]
ConverterFunction = Callable[[Any], Any]

# Decorator Types
Decorator = Callable[[Callable], Callable]
AsyncDecorator = Callable[[AsyncFunction], AsyncFunction]

# Context Manager Types
class AsyncContextManager(Protocol[T]):
    """Async context manager protocol"""
    async def __aenter__(self) -> T: ...
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

class SyncContextManager(Protocol[T]):
    """Sync context manager protocol"""
    def __enter__(self) -> T: ...
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...

# Iterator Types
class AsyncIterator(Protocol[T]):
    """Async iterator protocol"""
    def __aiter__(self) -> 'AsyncIterator[T]': ...
    async def __anext__(self) -> T: ...

class SyncIterator(Protocol[T]):
    """Sync iterator protocol"""
    def __iter__(self) -> 'SyncIterator[T]': ...
    def __next__(self) -> T: ...

# Factory Types
class Factory(Protocol[T]):
    """Factory protocol"""
    def create(self, **kwargs) -> T: ...

class AsyncFactory(Protocol[T]):
    """Async factory protocol"""
    async def create(self, **kwargs) -> T: ...

# Registry Types
class Registry(Protocol[T]):
    """Registry protocol"""
    def register(self, name: str, item: T) -> None: ...
    def get(self, name: str) -> Optional[T]: ...
    def list(self) -> List[str]: ...
    def unregister(self, name: str) -> None: ...

# Configuration Types
class Configurable(Protocol):
    """Configurable protocol"""
    def configure(self, config: Dict[str, Any]) -> None: ...
    def get_config(self) -> Dict[str, Any]: ...

# Observable Types
class Observable(Protocol):
    """Observable protocol"""
    def subscribe(self, callback: Callable[[Any], None]) -> None: ...
    def unsubscribe(self, callback: Callable[[Any], None]) -> None: ...
    def notify(self, event: Any) -> None: ...

# Stateful Types
class Stateful(Protocol):
    """Stateful protocol"""
    def get_state(self) -> Dict[str, Any]: ...
    def set_state(self, state: Dict[str, Any]) -> None: ...
    def reset_state(self) -> None: ...

# Lifecycle Types
class Lifecycle(Protocol):
    """Lifecycle protocol"""
    async def initialize(self) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def cleanup(self) -> None: ...

# Health Check Types
class HealthCheck(Protocol):
    """Health check protocol"""
    async def check_health(self) -> bool: ...
    async def get_status(self) -> Dict[str, Any]: ...

# Metrics Types
class Metrics(Protocol):
    """Metrics protocol"""
    def increment(self, name: str, value: float = 1.0) -> None: ...
    def gauge(self, name: str, value: float) -> None: ...
    def histogram(self, name: str, value: float) -> None: ...
    def timer(self, name: str) -> 'Timer': ...

class Timer(Protocol):
    """Timer protocol"""
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def elapsed(self) -> float: ...
