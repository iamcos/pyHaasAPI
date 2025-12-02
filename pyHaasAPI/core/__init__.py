"""
Core infrastructure for pyHaasAPI v2

Provides the foundational components including client, authentication,
configuration, and logging systems.
"""

from .client import AsyncHaasClient, HaasClient
from .auth import AuthenticationManager
from .config import Settings
from .logging import setup_logging, get_logger

# Async utilities
from .async_utils import (
    AsyncRateLimiter, AsyncRetryHandler, AsyncBatchProcessor, AsyncProgressTracker,
    AsyncContextManager, AsyncSemaphoreManager, AsyncCache, AsyncQueue,
    RateLimitConfig, RetryConfig, BatchConfig,
    async_retry, async_rate_limit, async_sleep_with_progress, async_timeout,
    async_gather_with_concurrency, async_map_with_concurrency,
    async_resource_manager, async_semaphore_context, async_rate_limit_context
)

# Async client
from .async_client import AsyncHaasClientWrapper, AsyncClientConfig

# Async factory
from .async_factory import (
    AsyncClientFactory, ClientPreset,
    create_async_client, create_async_client_with_config,
    AsyncClientContext, with_async_client, execute_with_async_client
)

# Type checking and validation
from .type_validation import (
    TypeValidator, TypeChecker, TypeGuard, TypeConverter,
    ValidationResult, TypeValidationError,
    validate_type, convert_to_type, safe_convert
)
# Optional type_definitions import
try:
    from .type_definitions import (
        JSONValue, JSONDict, JSONList,
        LabID, BotID, AccountID, ScriptID, MarketTag, BacktestID, OrderID,
        LabStatus, BotStatus, OrderStatus, PositionMode, MarginMode,
        AsyncClientProtocol, AuthenticationProtocol, CacheProtocol, LoggerProtocol,
        TimeRange, PaginationParams, FilterParams, SortParams,
    APIRequest, APIResponse, ClientConfig, AuthConfig, CacheConfig,
    ErrorCode, APIError, PerformanceMetrics, RequestMetrics,
    ValidationLevel, ValidationConfig, FileType, FileInfo,
    EventType, Event, RequestCallback, ResponseCallback, ErrorCallback, EventCallback,
    Result, PaginatedResult, BatchResult, OptionalDict, RequiredDict,
    AsyncFunction, SyncFunction, ValidatorFunction, ConverterFunction,
    Decorator, AsyncDecorator, AsyncContextManager, SyncContextManager,
    AsyncIterator, SyncIterator, Factory, AsyncFactory, Registry,
    Configurable, Observable, Stateful, Lifecycle, HealthCheck, Metrics, Timer
)
except ImportError:
    # type_definitions not available - define minimal stubs if needed
    pass

try:
    from .type_config import (
        TypeCheckingMode, TypeCheckingConfig, TypeValidationSettings, TypeConfigManager,
        get_type_config, get_validation_settings, is_type_checking_enabled,
        is_runtime_validation_enabled, is_decorator_validation_enabled,
        is_async_validation_enabled, is_module_excluded, is_function_excluded,
        update_type_config, save_type_config, get_config_summary
    )
except ImportError:
    pass

from .type_decorators import (
    TypeChecked, TypeValidated, TypeConverted,
    type_checked, type_validated, type_converted,
    strict_type_checked, lenient_type_checked, auto_convert
)

__all__ = [
    # Core
    "AsyncHaasClient",
    "HaasClient", 
    "AuthenticationManager",
    "Settings",
    "setup_logging",
    "get_logger",
    
    # Async utilities
    "AsyncRateLimiter", "AsyncRetryHandler", "AsyncBatchProcessor", "AsyncProgressTracker",
    "AsyncContextManager", "AsyncSemaphoreManager", "AsyncCache", "AsyncQueue",
    "RateLimitConfig", "RetryConfig", "BatchConfig",
    "async_retry", "async_rate_limit", "async_sleep_with_progress", "async_timeout",
    "async_gather_with_concurrency", "async_map_with_concurrency",
    "async_resource_manager", "async_semaphore_context", "async_rate_limit_context",
    
    # Async client
    "AsyncHaasClientWrapper", "AsyncClientConfig",
    
    # Async factory
    "AsyncClientFactory", "ClientPreset",
    "create_async_client", "create_async_client_with_config",
    "AsyncClientContext", "with_async_client", "execute_with_async_client",
    
    # Type checking and validation
    "TypeValidator", "TypeChecker", "TypeGuard", "TypeConverter",
    "ValidationResult", "TypeValidationError",
    "validate_type", "convert_to_type", "safe_convert",
    "JSONValue", "JSONDict", "JSONList",
    "LabID", "BotID", "AccountID", "ScriptID", "MarketTag", "BacktestID", "OrderID",
    "LabStatus", "BotStatus", "OrderStatus", "PositionMode", "MarginMode",
    "AsyncClientProtocol", "AuthenticationProtocol", "CacheProtocol", "LoggerProtocol",
    "TimeRange", "PaginationParams", "FilterParams", "SortParams",
    "APIRequest", "APIResponse", "ClientConfig", "AuthConfig", "CacheConfig",
    "ErrorCode", "APIError", "PerformanceMetrics", "RequestMetrics",
    "ValidationLevel", "ValidationConfig", "FileType", "FileInfo",
    "EventType", "Event", "RequestCallback", "ResponseCallback", "ErrorCallback", "EventCallback",
    "Result", "PaginatedResult", "BatchResult", "OptionalDict", "RequiredDict",
    "AsyncFunction", "SyncFunction", "ValidatorFunction", "ConverterFunction",
    "Decorator", "AsyncDecorator", "AsyncContextManager", "SyncContextManager",
    "AsyncIterator", "SyncIterator", "Factory", "AsyncFactory", "Registry",
    "Configurable", "Observable", "Stateful", "Lifecycle", "HealthCheck", "Metrics", "Timer",
    "TypeCheckingMode", "TypeCheckingConfig", "TypeValidationSettings", "TypeConfigManager",
    "get_type_config", "get_validation_settings", "is_type_checking_enabled",
    "is_runtime_validation_enabled", "is_decorator_validation_enabled",
    "is_async_validation_enabled", "is_module_excluded", "is_function_excluded",
    "update_type_config", "save_type_config", "get_config_summary",
    "TypeChecked", "TypeValidated", "TypeConverted",
    "type_checked", "type_validated", "type_converted",
    "strict_type_checked", "lenient_type_checked", "auto_convert",
]