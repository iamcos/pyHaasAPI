"""
pyHaasAPI - Modern, Async, Type-Safe HaasOnline API Client

A comprehensive Python library for interacting with HaasOnline trading platform.
"""

__version__ = "2.0.0"
__author__ = "pyHaasAPI Team"
__email__ = "support@pyhaasapi.com"

# Minimal imports to avoid hanging
try:
    from .core.client import AsyncHaasClient
    from .core.auth import AuthenticationManager
except ImportError as e:
    print(f"Warning: Core imports failed: {e}")

# Exception hierarchy
try:
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
except ImportError as e:
    print(f"Warning: Exception imports failed: {e}")

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "AsyncHaasClient",
    "AuthenticationManager",
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