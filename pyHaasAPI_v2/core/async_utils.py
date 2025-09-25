"""
Async Utilities for pyHaasAPI v2

This module provides comprehensive async support utilities including
rate limiting, retry logic, batch processing, and async context managers.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Awaitable, TypeVar, Generic, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager
from functools import wraps

from .logging import get_logger

logger = get_logger("async_utils")

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    max_requests: int = 100
    time_window: float = 60.0  # seconds
    burst_limit: int = 10
    backoff_factor: float = 1.5


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    batch_size: int = 10
    max_concurrent: int = 5
    delay_between_batches: float = 0.1


class AsyncRateLimiter:
    """
    Async rate limiter with token bucket algorithm.
    
    Provides rate limiting functionality for API calls with configurable
    limits and burst handling.
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.max_requests
        self.last_update = time.time()
        self.lock = asyncio.Lock()
        self.logger = get_logger("rate_limiter")

    async def acquire(self) -> None:
        """Acquire a token for making a request"""
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            
            # Add tokens based on time passed
            tokens_to_add = time_passed * (self.config.max_requests / self.config.time_window)
            self.tokens = min(self.config.max_requests, self.tokens + tokens_to_add)
            self.last_update = now
            
            # Check if we can make a request
            if self.tokens >= 1:
                self.tokens -= 1
                return
            
            # Calculate wait time
            wait_time = (1 - self.tokens) * (self.config.time_window / self.config.max_requests)
            
            if wait_time > 0:
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                self.tokens = 0

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class AsyncRetryHandler:
    """
    Async retry handler with exponential backoff.
    
    Provides robust retry logic for async operations with configurable
    retry strategies and backoff algorithms.
    """

    def __init__(self, config: RetryConfig):
        self.config = config
        self.logger = get_logger("retry_handler")

    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.config.max_retries:
                    self.logger.error(f"Max retries ({self.config.max_retries}) exceeded for {func.__name__}")
                    raise e
                
                # Calculate delay
                delay = self._calculate_delay(attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s")
                
                await asyncio.sleep(delay)
        
        # This should never be reached, but just in case
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        
        # Apply jitter if enabled
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        # Cap at max delay
        return min(delay, self.config.max_delay)


class AsyncBatchProcessor:
    """
    Async batch processor for handling multiple operations efficiently.
    
    Provides batch processing capabilities with concurrency control
    and progress tracking.
    """

    def __init__(self, config: BatchConfig):
        self.config = config
        self.logger = get_logger("batch_processor")

    async def process_batches(
        self,
        items: List[T],
        processor: Callable[[T], Awaitable[R]],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[R]:
        """Process items in batches with concurrency control"""
        results = []
        total_items = len(items)
        
        self.logger.info(f"Processing {total_items} items in batches of {self.config.batch_size}")
        
        for i in range(0, total_items, self.config.batch_size):
            batch = items[i:i + self.config.batch_size]
            batch_num = i // self.config.batch_size + 1
            total_batches = (total_items + self.config.batch_size - 1) // self.config.batch_size
            
            self.logger.debug(f"Processing batch {batch_num}/{total_batches} with {len(batch)} items")
            
            # Process batch with concurrency limit
            semaphore = asyncio.Semaphore(self.config.max_concurrent)
            batch_results = await self._process_batch(batch, processor, semaphore)
            results.extend(batch_results)
            
            # Progress callback
            if progress_callback:
                progress_callback(len(results), total_items)
            
            # Delay between batches
            if i + self.config.batch_size < total_items and self.config.delay_between_batches > 0:
                await asyncio.sleep(self.config.delay_between_batches)
        
        self.logger.info(f"Completed processing {len(results)} items")
        return results

    async def _process_batch(
        self,
        batch: List[T],
        processor: Callable[[T], Awaitable[R]],
        semaphore: asyncio.Semaphore
    ) -> List[R]:
        """Process a single batch with concurrency control"""
        async def process_item(item: T) -> R:
            async with semaphore:
                return await processor(item)
        
        tasks = [process_item(item) for item in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def process_with_retry(
        self,
        items: List[T],
        processor: Callable[[T], Awaitable[R]],
        retry_config: RetryConfig,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Union[R, Exception]]:
        """Process items with retry logic"""
        retry_handler = AsyncRetryHandler(retry_config)
        
        async def process_with_retry_wrapper(item: T) -> Union[R, Exception]:
            try:
                return await retry_handler.execute_with_retry(processor, item)
            except Exception as e:
                return e
        
        return await self.process_batches(items, process_with_retry_wrapper, progress_callback)


class AsyncProgressTracker:
    """
    Async progress tracker for long-running operations.
    
    Provides progress tracking and reporting for async operations
    with configurable update intervals.
    """

    def __init__(self, total: int, update_interval: float = 1.0):
        self.total = total
        self.completed = 0
        self.start_time = time.time()
        self.update_interval = update_interval
        self.last_update = 0
        self.logger = get_logger("progress_tracker")

    def update(self, increment: int = 1) -> None:
        """Update progress"""
        self.completed += increment
        now = time.time()
        
        if now - self.last_update >= self.update_interval:
            self._log_progress()
            self.last_update = now

    def _log_progress(self) -> None:
        """Log current progress"""
        percentage = (self.completed / self.total) * 100
        elapsed = time.time() - self.start_time
        
        if self.completed > 0:
            eta = (elapsed / self.completed) * (self.total - self.completed)
            self.logger.info(f"Progress: {self.completed}/{self.total} ({percentage:.1f}%) - ETA: {eta:.1f}s")
        else:
            self.logger.info(f"Progress: {self.completed}/{self.total} ({percentage:.1f}%)")

    def finish(self) -> None:
        """Mark progress as finished"""
        self.completed = self.total
        elapsed = time.time() - self.start_time
        self.logger.info(f"Completed: {self.total}/{self.total} (100%) - Total time: {elapsed:.1f}s")


class AsyncContextManager:
    """
    Async context manager for resource management.
    
    Provides async context management for resources that need
    proper cleanup and initialization.
    """

    def __init__(self, setup_func: Callable[[], Awaitable[T]], cleanup_func: Callable[[T], Awaitable[None]]):
        self.setup_func = setup_func
        self.cleanup_func = cleanup_func
        self.resource = None
        self.logger = get_logger("async_context")

    async def __aenter__(self) -> T:
        """Enter async context"""
        self.resource = await self.setup_func()
        self.logger.debug("Async context entered")
        return self.resource

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context"""
        if self.resource is not None:
            try:
                await self.cleanup_func(self.resource)
                self.logger.debug("Async context exited successfully")
            except Exception as e:
                self.logger.error(f"Error during async context cleanup: {e}")
                if exc_type is None:
                    raise


class AsyncSemaphoreManager:
    """
    Async semaphore manager for controlling concurrency.
    
    Provides semaphore management with automatic cleanup
    and configurable limits.
    """

    def __init__(self, limit: int):
        self.limit = limit
        self.semaphore = asyncio.Semaphore(limit)
        self.logger = get_logger("semaphore_manager")

    async def acquire(self) -> None:
        """Acquire semaphore"""
        await self.semaphore.acquire()
        self.logger.debug(f"Semaphore acquired, {self.semaphore._value} remaining")

    def release(self) -> None:
        """Release semaphore"""
        self.semaphore.release()
        self.logger.debug(f"Semaphore released, {self.semaphore._value} remaining")

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()


# Utility Functions

def async_retry(config: RetryConfig):
    """Decorator for async retry logic"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            retry_handler = AsyncRetryHandler(config)
            return await retry_handler.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator


def async_rate_limit(config: RateLimitConfig):
    """Decorator for async rate limiting"""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        rate_limiter = AsyncRateLimiter(config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async with rate_limiter:
                return await func(*args, **kwargs)
        return wrapper
    return decorator


async def async_sleep_with_progress(duration: float, update_interval: float = 1.0) -> None:
    """Sleep with progress updates"""
    start_time = time.time()
    elapsed = 0
    
    while elapsed < duration:
        remaining = duration - elapsed
        sleep_time = min(update_interval, remaining)
        
        await asyncio.sleep(sleep_time)
        elapsed = time.time() - start_time
        
        if remaining > update_interval:
            logger.debug(f"Sleep progress: {elapsed:.1f}/{duration:.1f}s")


async def async_timeout(seconds: float):
    """Async timeout context manager"""
    return asyncio.timeout(seconds)


async def async_gather_with_concurrency(
    tasks: List[Awaitable[T]],
    max_concurrent: int = 10
) -> List[T]:
    """Gather tasks with concurrency control"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def limited_task(task: Awaitable[T]) -> T:
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[limited_task(task) for task in tasks])


async def async_map_with_concurrency(
    items: List[T],
    func: Callable[[T], Awaitable[R]],
    max_concurrent: int = 10
) -> List[R]:
    """Map function over items with concurrency control"""
    tasks = [func(item) for item in items]
    return await async_gather_with_concurrency(tasks, max_concurrent)


# Async Context Managers

@asynccontextmanager
async def async_resource_manager(
    setup_func: Callable[[], Awaitable[T]],
    cleanup_func: Callable[[T], Awaitable[None]]
):
    """Async context manager for resource management"""
    resource = await setup_func()
    try:
        yield resource
    finally:
        await cleanup_func(resource)


@asynccontextmanager
async def async_semaphore_context(limit: int):
    """Async context manager for semaphore"""
    semaphore = asyncio.Semaphore(limit)
    try:
        yield semaphore
    finally:
        pass  # Semaphore cleanup is automatic


@asynccontextmanager
async def async_rate_limit_context(config: RateLimitConfig):
    """Async context manager for rate limiting"""
    rate_limiter = AsyncRateLimiter(config)
    try:
        yield rate_limiter
    finally:
        pass  # Rate limiter cleanup is automatic


# Async Utilities for Common Patterns

class AsyncCache:
    """Async cache with TTL support"""
    
    def __init__(self, ttl: float = 300.0):  # 5 minutes default
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl
        self.lock = asyncio.Lock()
        self.logger = get_logger("async_cache")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                else:
                    del self.cache[key]
            return None

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache"""
        async with self.lock:
            self.cache[key] = (value, time.time())

    async def clear(self) -> None:
        """Clear cache"""
        async with self.lock:
            self.cache.clear()

    async def cleanup_expired(self) -> None:
        """Clean up expired entries"""
        async with self.lock:
            now = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.cache.items()
                if now - timestamp >= self.ttl
            ]
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")


class AsyncQueue:
    """Async queue with size limits and timeout support"""
    
    def __init__(self, maxsize: int = 0):
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.logger = get_logger("async_queue")

    async def put(self, item: T, timeout: Optional[float] = None) -> None:
        """Put item in queue with optional timeout"""
        try:
            if timeout:
                await asyncio.wait_for(self.queue.put(item), timeout=timeout)
            else:
                await self.queue.put(item)
        except asyncio.TimeoutError:
            self.logger.warning("Queue put operation timed out")
            raise

    async def get(self, timeout: Optional[float] = None) -> T:
        """Get item from queue with optional timeout"""
        try:
            if timeout:
                return await asyncio.wait_for(self.queue.get(), timeout=timeout)
            else:
                return await self.queue.get()
        except asyncio.TimeoutError:
            self.logger.warning("Queue get operation timed out")
            raise

    async def task_done(self) -> None:
        """Mark task as done"""
        self.queue.task_done()

    async def join(self) -> None:
        """Wait for all tasks to be done"""
        await self.queue.join()

    def qsize(self) -> int:
        """Get queue size"""
        return self.queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()

    def full(self) -> bool:
        """Check if queue is full"""
        return self.queue.full()
