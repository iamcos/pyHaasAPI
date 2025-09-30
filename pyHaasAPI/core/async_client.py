"""
Async Client for pyHaasAPI v2

This module provides a comprehensive async client wrapper that integrates
all async utilities for optimal performance and reliability.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable, TypeVar, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .async_utils import (
    AsyncRateLimiter, AsyncRetryHandler, AsyncBatchProcessor, AsyncProgressTracker,
    AsyncContextManager, AsyncSemaphoreManager, AsyncCache, AsyncQueue,
    RateLimitConfig, RetryConfig, BatchConfig
)
from .client import AsyncHaasClient
from .auth import AuthenticationManager
from .logging import get_logger

logger = get_logger("async_client")

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class AsyncClientConfig:
    """Configuration for async client"""
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    cache_ttl: float = 300.0  # 5 minutes
    max_concurrent_requests: int = 10
    request_timeout: float = 30.0
    enable_caching: bool = True
    enable_rate_limiting: bool = True
    enable_retry: bool = True
    enable_batch_processing: bool = True


class AsyncHaasClientWrapper:
    """
    Async client wrapper with comprehensive async support.
    
    Provides a high-level async interface with rate limiting, retry logic,
    batch processing, caching, and progress tracking.
    """

    def __init__(
        self,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager,
        config: Optional[AsyncClientConfig] = None
    ):
        self.client = client
        self.auth_manager = auth_manager
        self.config = config or AsyncClientConfig()
        self.logger = get_logger("async_client_wrapper")
        
        # Initialize async utilities
        self.rate_limiter = AsyncRateLimiter(self.config.rate_limit) if self.config.enable_rate_limiting else None
        self.retry_handler = AsyncRetryHandler(self.config.retry) if self.config.enable_retry else None
        self.batch_processor = AsyncBatchProcessor(self.config.batch) if self.config.enable_batch_processing else None
        self.cache = AsyncCache(self.config.cache_ttl) if self.config.enable_caching else None
        self.semaphore = AsyncSemaphoreManager(self.config.max_concurrent_requests)
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cached_requests": 0,
            "retried_requests": 0,
            "rate_limited_requests": 0,
            "start_time": time.time()
        }

    # Core Async Operations

    async def execute_request(
        self,
        request_func: Callable[..., Awaitable[T]],
        *args,
        use_cache: bool = True,
        cache_key: Optional[str] = None,
        **kwargs
    ) -> T:
        """
        Execute a request with full async support.
        
        Args:
            request_func: The request function to execute
            *args: Arguments for the request function
            use_cache: Whether to use caching
            cache_key: Custom cache key
            **kwargs: Keyword arguments for the request function
            
        Returns:
            The result of the request
            
        Raises:
            Exception: If the request fails after all retries
        """
        # Generate cache key if not provided
        if use_cache and self.cache and not cache_key:
            cache_key = self._generate_cache_key(request_func.__name__, args, kwargs)
        
        # Check cache first
        if use_cache and self.cache and cache_key:
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                self.stats["cached_requests"] += 1
                self.logger.debug(f"Cache hit for {request_func.__name__}")
                return cached_result
        
        # Execute request with async support
        async with self.semaphore:
            # Rate limiting
            if self.rate_limiter:
                async with self.rate_limiter:
                    pass
            
            # Execute with retry logic
            if self.retry_handler:
                result = await self.retry_handler.execute_with_retry(
                    self._execute_single_request, request_func, *args, **kwargs
                )
            else:
                result = await self._execute_single_request(request_func, *args, **kwargs)
            
            # Cache result
            if use_cache and self.cache and cache_key:
                await self.cache.set(cache_key, result)
            
            # Update statistics
            self.stats["total_requests"] += 1
            self.stats["successful_requests"] += 1
            
            return result

    async def _execute_single_request(
        self,
        request_func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """Execute a single request without retry logic"""
        try:
            return await asyncio.wait_for(
                request_func(*args, **kwargs),
                timeout=self.config.request_timeout
            )
        except asyncio.TimeoutError:
            self.stats["failed_requests"] += 1
            self.logger.error(f"Request timeout for {request_func.__name__}")
            raise
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"Request failed for {request_func.__name__}: {e}")
            raise

    # Batch Operations

    async def execute_batch_requests(
        self,
        requests: List[tuple[Callable, tuple, dict]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Union[T, Exception]]:
        """
        Execute multiple requests in batches.
        
        Args:
            requests: List of (function, args, kwargs) tuples
            progress_callback: Optional progress callback function
            
        Returns:
            List of results or exceptions
        """
        if not self.batch_processor:
            # Fallback to sequential execution
            results = []
            for i, (func, args, kwargs) in enumerate(requests):
                try:
                    result = await self.execute_request(func, *args, **kwargs)
                    results.append(result)
                except Exception as e:
                    results.append(e)
                
                if progress_callback:
                    progress_callback(i + 1, len(requests))
            
            return results
        
        # Use batch processor
        async def process_request(request_data: tuple) -> Union[T, Exception]:
            func, args, kwargs = request_data
            try:
                return await self.execute_request(func, *args, **kwargs)
            except Exception as e:
                return e
        
        return await self.batch_processor.process_batches(
            requests, process_request, progress_callback
        )

    # Parallel Operations

    async def execute_parallel_requests(
        self,
        requests: List[tuple[Callable, tuple, dict]],
        max_concurrent: Optional[int] = None
    ) -> List[Union[T, Exception]]:
        """
        Execute multiple requests in parallel.
        
        Args:
            requests: List of (function, args, kwargs) tuples
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of results or exceptions
        """
        max_concurrent = max_concurrent or self.config.max_concurrent_requests
        
        async def execute_single(request_data: tuple) -> Union[T, Exception]:
            func, args, kwargs = request_data
            try:
                return await self.execute_request(func, *args, **kwargs)
            except Exception as e:
                return e
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def limited_execute(request_data: tuple) -> Union[T, Exception]:
            async with semaphore:
                return await execute_single(request_data)
        
        # Execute all requests
        tasks = [limited_execute(request) for request in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

    # Utility Methods

    def _generate_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key for request"""
        import hashlib
        import json
        
        # Create a hash of the function name, args, and kwargs
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs
        }
        
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()

    async def clear_cache(self) -> None:
        """Clear the cache"""
        if self.cache:
            await self.cache.clear()
            self.logger.info("Cache cleared")

    async def cleanup_cache(self) -> None:
        """Clean up expired cache entries"""
        if self.cache:
            await self.cache.cleanup_expired()

    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        uptime = time.time() - self.stats["start_time"]
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "requests_per_second": self.stats["total_requests"] / uptime if uptime > 0 else 0,
            "success_rate": self.stats["successful_requests"] / self.stats["total_requests"] if self.stats["total_requests"] > 0 else 0,
            "cache_hit_rate": self.stats["cached_requests"] / self.stats["total_requests"] if self.stats["total_requests"] > 0 else 0
        }

    def reset_statistics(self) -> None:
        """Reset client statistics"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cached_requests": 0,
            "retried_requests": 0,
            "rate_limited_requests": 0,
            "start_time": time.time()
        }

    # Context Manager Support

    async def __aenter__(self):
        """Enter async context"""
        self.logger.info("Async client context entered")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context"""
        if exc_type is None:
            self.logger.info("Async client context exited successfully")
        else:
            self.logger.error(f"Async client context exited with error: {exc_val}")
        
        # Cleanup
        await self.cleanup_cache()

    # Health Check

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check client
        try:
            # Simple health check - try to get labs
            await self.execute_request(self.client.get_labs)
            health_status["components"]["client"] = "healthy"
        except Exception as e:
            health_status["components"]["client"] = f"unhealthy: {e}"
            health_status["status"] = "unhealthy"
        
        # Check cache
        if self.cache:
            try:
                await self.cache.get("health_check")
                health_status["components"]["cache"] = "healthy"
            except Exception as e:
                health_status["components"]["cache"] = f"unhealthy: {e}"
                health_status["status"] = "unhealthy"
        
        # Check rate limiter
        if self.rate_limiter:
            health_status["components"]["rate_limiter"] = "healthy"
        
        # Check retry handler
        if self.retry_handler:
            health_status["components"]["retry_handler"] = "healthy"
        
        # Check batch processor
        if self.batch_processor:
            health_status["components"]["batch_processor"] = "healthy"
        
        return health_status

    # Configuration Management

    def update_config(self, config: AsyncClientConfig) -> None:
        """Update client configuration"""
        self.config = config
        
        # Reinitialize utilities with new config
        self.rate_limiter = AsyncRateLimiter(self.config.rate_limit) if self.config.enable_rate_limiting else None
        self.retry_handler = AsyncRetryHandler(self.config.retry) if self.config.enable_retry else None
        self.batch_processor = AsyncBatchProcessor(self.config.batch) if self.config.enable_batch_processing else None
        self.cache = AsyncCache(self.config.cache_ttl) if self.config.enable_caching else None
        self.semaphore = AsyncSemaphoreManager(self.config.max_concurrent_requests)
        
        self.logger.info("Client configuration updated")

    def get_config(self) -> AsyncClientConfig:
        """Get current configuration"""
        return self.config
