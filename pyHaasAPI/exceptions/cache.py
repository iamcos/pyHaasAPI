"""
Cache-related exceptions
"""

from .base import RetryableError, NonRetryableError


class CacheError(RetryableError):
    """Base class for cache-related errors"""
    
    def __init__(self, message: str = "Cache error occurred", **kwargs):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            recovery_suggestion="Try again or clear cache",
            **kwargs
        )


class CacheKeyError(CacheError):
    """Raised when cache key is invalid"""
    
    def __init__(self, key: str, **kwargs):
        super().__init__(
            message=f"Invalid cache key: {key}",
            error_code="CACHE_KEY_ERROR",
            context={"key": key},
            **kwargs
        )
        self.key = key


class CacheExpiredError(CacheError):
    """Raised when cached data has expired"""
    
    def __init__(self, key: str, **kwargs):
        super().__init__(
            message=f"Cache expired for key: {key}",
            error_code="CACHE_EXPIRED",
            context={"key": key},
            recovery_suggestion="Refresh the data from source",
            **kwargs
        )
        self.key = key


class CacheCorruptionError(NonRetryableError):
    """Raised when cached data is corrupted"""
    
    def __init__(self, key: str, **kwargs):
        super().__init__(
            message=f"Cache corruption detected for key: {key}",
            error_code="CACHE_CORRUPTION",
            context={"key": key},
            recovery_suggestion="Clear cache and refresh data",
            **kwargs
        )
        self.key = key


class CacheWriteError(CacheError):
    """Raised when cache write operation fails"""
    
    def __init__(self, key: str, **kwargs):
        super().__init__(
            message=f"Failed to write to cache: {key}",
            error_code="CACHE_WRITE_ERROR",
            context={"key": key},
            **kwargs
        )
        self.key = key


class CacheReadError(CacheError):
    """Raised when cache read operation fails"""
    
    def __init__(self, key: str, **kwargs):
        super().__init__(
            message=f"Failed to read from cache: {key}",
            error_code="CACHE_READ_ERROR",
            context={"key": key},
            **kwargs
        )
        self.key = key
