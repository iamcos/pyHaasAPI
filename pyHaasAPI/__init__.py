"""
pyHaasAPI - Modern, Async, Type-Safe HaasOnline API Client

A comprehensive Python library for interacting with HaasOnline trading platform.
Provides complete functionality for lab analysis, backtest processing, bot management,
and automated trading workflows with modern async/await support.

Key Features:
- Async/await support throughout
- Comprehensive type safety
- Domain-separated API modules
- Service layer with business logic
- Flexible reporting system
- Data dumping capabilities
- Robust error handling
- Performance optimization

Architecture:
- core/: Core infrastructure (client, auth, config, logging)
- api/: Domain-specific API modules (lab, bot, account, etc.)
- services/: Business logic services
- models/: Data models and schemas
- exceptions/: Exception hierarchy
- config/: Configuration management
- utils/: Utility functions
- cli/: CLI tools
"""

__version__ = "2.0.0"
__author__ = "pyHaasAPI Team"
__email__ = "support@pyhaasapi.com"

# Core imports
from .core.client import AsyncHaasClient
from .core.auth import AuthenticationManager
from .core.config import Settings
from .core.logging import setup_logging

# Async infrastructure
from .core.async_utils import (
    AsyncRateLimiter, AsyncRetryHandler, AsyncBatchProcessor, AsyncProgressTracker,
    AsyncContextManager, AsyncSemaphoreManager, AsyncCache, AsyncQueue,
    RateLimitConfig, RetryConfig, BatchConfig,
    async_retry, async_rate_limit, async_sleep_with_progress, async_timeout,
    async_gather_with_concurrency, async_map_with_concurrency,
    async_resource_manager, async_semaphore_context, async_rate_limit_context
)
from .core.async_client import AsyncHaasClientWrapper, AsyncClientConfig
from .core.async_factory import (
    AsyncClientFactory, ClientPreset,
    create_async_client, create_async_client_with_config,
    AsyncClientContext, with_async_client, execute_with_async_client
)

# Type checking and validation
from .core.type_validation import (
    TypeValidator, TypeChecker, TypeGuard, TypeConverter,
    ValidationResult, TypeValidationError,
    validate_type, convert_to_type, safe_convert
)
from .core.type_definitions import (
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
from .core.type_config import (
    TypeCheckingMode, TypeCheckingConfig, TypeValidationSettings, TypeConfigManager,
    get_type_config, get_validation_settings, is_type_checking_enabled,
    is_runtime_validation_enabled, is_decorator_validation_enabled,
    is_async_validation_enabled, is_module_excluded, is_function_excluded,
    update_type_config, save_type_config, get_config_summary
)
from .core.type_decorators import (
    TypeChecked, TypeValidated, TypeConverted,
    type_checked, type_validated, type_converted,
    strict_type_checked, lenient_type_checked, auto_convert
)

# API modules
from .api.lab import LabAPI
from .api.bot import BotAPI
from .api.account import AccountAPI
from .api.script import ScriptAPI
from .api.market import MarketAPI
from .api.backtest import BacktestAPI
from .api.order import OrderAPI

# Services
from .services import (
    LabService, LabAnalysisResult, LabExecutionResult, LabValidationResult,
    BotService, BotCreationResult, MassBotCreationResult, BotValidationResult,
    AnalysisService, BacktestPerformance, LabAnalysisResult, AnalysisReport,
    ReportingService, ReportType, ReportFormat, ReportConfig, ReportResult
)

# Tools
from .tools import (
    DataDumper, DumpFormat, DumpScope, DumpConfig, DumpResult,
    TestingManager, TestDataType, TestDataScope, TestDataConfig, TestDataResult,
    TestLabConfig, TestBotConfig, TestAccountConfig
)

# CLI
from .cli import (
    BaseCLI, AsyncBaseCLI, main, create_parser,
    LabCLI, BotCLI, AnalysisCLI, AccountCLI, ScriptCLI, MarketCLI, BacktestCLI, OrderCLI
)

# Main client class
from .core.client import HaasClient

# Exception hierarchy
from .exceptions import (
    HaasAPIError,
    AuthenticationError,
    APIError,
    ValidationError,
    NetworkError,
    ConfigurationError,
    CacheError,
    AnalysisError,
    BotCreationError,
    LabError,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    
    # Core
    "AsyncHaasClient",
    "HaasClient",
    "AuthenticationManager",
    "Settings",
    "setup_logging",
    
    # Async infrastructure
    "AsyncRateLimiter", "AsyncRetryHandler", "AsyncBatchProcessor", "AsyncProgressTracker",
    "AsyncContextManager", "AsyncSemaphoreManager", "AsyncCache", "AsyncQueue",
    "RateLimitConfig", "RetryConfig", "BatchConfig",
    "async_retry", "async_rate_limit", "async_sleep_with_progress", "async_timeout",
    "async_gather_with_concurrency", "async_map_with_concurrency",
    "async_resource_manager", "async_semaphore_context", "async_rate_limit_context",
    "AsyncHaasClientWrapper", "AsyncClientConfig",
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
    
    # API modules
    "LabAPI",
    "BotAPI", 
    "AccountAPI",
    "ScriptAPI",
    "MarketAPI",
    "BacktestAPI",
    "OrderAPI",
    
    # Services
    "LabService", "LabAnalysisResult", "LabExecutionResult", "LabValidationResult",
    "BotService", "BotCreationResult", "MassBotCreationResult", "BotValidationResult",
    "AnalysisService", "BacktestPerformance", "LabAnalysisResult", "AnalysisReport",
    "ReportingService", "ReportType", "ReportFormat", "ReportConfig", "ReportResult",
    
    # Tools
    "DataDumper", "DumpFormat", "DumpScope", "DumpConfig", "DumpResult",
    "TestingManager", "TestDataType", "TestDataScope", "TestDataConfig", "TestDataResult",
    "TestLabConfig", "TestBotConfig", "TestAccountConfig",
    
    # CLI
    "BaseCLI", "AsyncBaseCLI", "main", "create_parser",
    "LabCLI", "BotCLI", "AnalysisCLI", "AccountCLI", "ScriptCLI", "MarketCLI", "BacktestCLI", "OrderCLI",
    
    # Exceptions
    "HaasAPIError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "NetworkError",
    "ConfigurationError",
    "CacheError",
    "AnalysisError",
    "BotCreationError",
    "LabError",
]