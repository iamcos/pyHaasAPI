"""
Data Cache and Management Layer

Intelligent caching service for API responses and real-time data with LRU cache,
TTL support, intelligent invalidation, real-time data propagation, and persistence.
"""

import asyncio
import json
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union, Set, TypeVar, Generic
from enum import Enum
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from ..utils.errors import (
    CacheError, ErrorCategory, ErrorSeverity, 
    ErrorContext, handle_error, error_handler
)
from ..utils.logging import get_logger, get_performance_logger, timer

T = TypeVar('T')


class CacheEntryType(Enum):
    """Types of cache entries for intelligent invalidation"""
    BOT_DATA = "bot_data"
    LAB_DATA = "lab_data"
    SCRIPT_DATA = "script_data"
    MARKET_DATA = "market_data"
    ACCOUNT_DATA = "account_data"
    SYSTEM_STATUS = "system_status"
    BACKTEST_RESULTS = "backtest_results"
    PERFORMANCE_METRICS = "performance_metrics"
    REAL_TIME_DATA = "real_time_data"
    STATIC_DATA = "static_data"


class InvalidationStrategy(Enum):
    """Cache invalidation strategies"""
    TTL_ONLY = "ttl_only"
    EVENT_BASED = "event_based"
    DEPENDENCY_BASED = "dependency_based"
    MANUAL = "manual"


@dataclass
class CacheEntry(Generic[T]):
    """Represents a cache entry with metadata"""
    key: str
    value: T
    entry_type: CacheEntryType
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    dependencies: Set[str] = field(default_factory=set)
    invalidation_strategy: InvalidationStrategy = InvalidationStrategy.TTL_ONLY
    size_bytes: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL"""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds
    
    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def touch(self) -> None:
        """Update last accessed time and increment access count"""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics and metrics"""
    total_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    invalidation_count: int = 0
    persistence_saves: int = 0
    persistence_loads: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / total_requests if total_requests > 0 else 0.0
    
    @property
    def average_entry_size(self) -> float:
        """Calculate average entry size in bytes"""
        return self.total_size_bytes / self.total_entries if self.total_entries > 0 else 0.0


class LRUCache(Generic[T]):
    """Thread-safe LRU cache implementation with TTL support"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[CacheEntry[T]]:
        """Get entry from cache, moving it to end (most recently used)"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired:
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            
            return entry
    
    def put(self, key: str, entry: CacheEntry[T]) -> Optional[CacheEntry[T]]:
        """Put entry in cache, evicting LRU entry if necessary"""
        with self._lock:
            evicted_entry = None
            
            # If key exists, remove old entry
            if key in self._cache:
                evicted_entry = self._cache[key]
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            
            # Evict LRU entries if over capacity
            while len(self._cache) > self.max_size:
                lru_key, lru_entry = self._cache.popitem(last=False)
                if evicted_entry is None:
                    evicted_entry = lru_entry
            
            return evicted_entry
    
    def remove(self, key: str) -> Optional[CacheEntry[T]]:
        """Remove entry from cache"""
        with self._lock:
            return self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all entries from cache"""
        with self._lock:
            self._cache.clear()
    
    def keys(self) -> List[str]:
        """Get all cache keys"""
        with self._lock:
            return list(self._cache.keys())
    
    def values(self) -> List[CacheEntry[T]]:
        """Get all cache entries"""
        with self._lock:
            return list(self._cache.values())
    
    def items(self) -> List[tuple[str, CacheEntry[T]]]:
        """Get all cache key-value pairs"""
        with self._lock:
            return list(self._cache.items())
    
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() 
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)


class DataCacheService:
    """Intelligent caching service for API responses and real-time data"""
    
    def __init__(
        self, 
        max_size: int = 1000,
        default_ttl: int = 300,
        persistence_path: Optional[str] = None,
        enable_persistence: bool = True,
        cleanup_interval: int = 60
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_persistence = enable_persistence
        self.cleanup_interval = cleanup_interval
        
        # Initialize cache
        self._cache: LRUCache[Any] = LRUCache(max_size)
        
        # Statistics
        self.stats = CacheStats()
        
        # Logging
        self.logger = get_logger(__name__, {"component": "data_cache"})
        self.perf_logger = get_performance_logger(__name__)
        
        # Real-time data management
        self._real_time_data: Dict[str, Any] = {}
        self._real_time_subscribers: Dict[str, List[Callable[[str, Any], None]]] = {}
        self._real_time_lock = asyncio.Lock()
        
        # Persistence
        if persistence_path:
            self.persistence_path = Path(persistence_path)
        else:
            self.persistence_path = Path.home() / ".mcp-tui" / "cache"
        
        self.persistence_path.mkdir(parents=True, exist_ok=True)
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._persistence_task: Optional[asyncio.Task] = None
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache")
        
        # Dependency tracking for intelligent invalidation
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_dependencies: Dict[str, Set[str]] = {}
        
        # Event-based invalidation
        self._invalidation_handlers: Dict[CacheEntryType, List[Callable[[str], bool]]] = {
            entry_type: [] for entry_type in CacheEntryType
        }
        
        # TTL configurations by entry type
        self._ttl_config: Dict[CacheEntryType, int] = {
            CacheEntryType.BOT_DATA: 30,  # 30 seconds for bot data
            CacheEntryType.LAB_DATA: 60,  # 1 minute for lab data
            CacheEntryType.SCRIPT_DATA: 300,  # 5 minutes for script data
            CacheEntryType.MARKET_DATA: 5,  # 5 seconds for market data
            CacheEntryType.ACCOUNT_DATA: 60,  # 1 minute for account data
            CacheEntryType.SYSTEM_STATUS: 10,  # 10 seconds for system status
            CacheEntryType.BACKTEST_RESULTS: 3600,  # 1 hour for backtest results
            CacheEntryType.PERFORMANCE_METRICS: 300,  # 5 minutes for performance metrics
            CacheEntryType.REAL_TIME_DATA: 0,  # No TTL for real-time data
            CacheEntryType.STATIC_DATA: 86400,  # 24 hours for static data
        }
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks for cleanup and persistence"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        if self.enable_persistence and not self._persistence_task:
            self._persistence_task = asyncio.create_task(self._periodic_persistence())
        
        # Load persisted data on startup
        if self.enable_persistence:
            await self._load_persisted_data()
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired entries"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                with timer(self.perf_logger, "cache_cleanup"):
                    expired_count = self._cache.cleanup_expired()
                    if expired_count > 0:
                        self.stats.eviction_count += expired_count
                        self.logger.debug(f"Cleaned up {expired_count} expired cache entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic cleanup: {e}")
    
    async def _periodic_persistence(self) -> None:
        """Periodic persistence of cache data"""
        while True:
            try:
                await asyncio.sleep(300)  # Save every 5 minutes
                await self._persist_cache_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in periodic persistence: {e}")
    
    @error_handler(category=ErrorCategory.CACHE, severity=ErrorSeverity.LOW)
    async def get(
        self, 
        key: str, 
        fetch_func: Optional[Callable[[], Any]] = None,
        entry_type: CacheEntryType = CacheEntryType.STATIC_DATA,
        ttl_override: Optional[int] = None
    ) -> Any:
        """Get data from cache with optional fetch function for cache misses"""
        with timer(self.perf_logger, f"cache_get:{entry_type.value}"):
            # Try to get from cache
            entry = self._cache.get(key)
            
            if entry is not None:
                self.stats.hit_count += 1
                self.logger.debug(f"Cache hit for key: {key}")
                return entry.value
            
            # Cache miss
            self.stats.miss_count += 1
            self.logger.debug(f"Cache miss for key: {key}")
            
            # If no fetch function provided, return None
            if fetch_func is None:
                return None
            
            # Fetch data using provided function
            try:
                if asyncio.iscoroutinefunction(fetch_func):
                    data = await fetch_func()
                else:
                    # Run sync function in executor to avoid blocking
                    data = await asyncio.get_event_loop().run_in_executor(
                        self._executor, fetch_func
                    )
                
                # Store in cache
                await self.put(key, data, entry_type, ttl_override)
                return data
                
            except Exception as e:
                self.logger.error(f"Error fetching data for key {key}: {e}")
                raise CacheError(f"Failed to fetch data: {e}") from e
    
    @error_handler(category=ErrorCategory.CACHE, severity=ErrorSeverity.LOW)
    async def put(
        self, 
        key: str, 
        value: Any, 
        entry_type: CacheEntryType = CacheEntryType.STATIC_DATA,
        ttl_override: Optional[int] = None,
        dependencies: Optional[Set[str]] = None
    ) -> None:
        """Put data in cache with intelligent TTL and dependency tracking"""
        with timer(self.perf_logger, f"cache_put:{entry_type.value}"):
            # Determine TTL
            ttl = ttl_override if ttl_override is not None else self._ttl_config.get(entry_type, self.default_ttl)
            
            # Calculate entry size
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                size_bytes = len(str(value).encode('utf-8'))
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                entry_type=entry_type,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl if ttl > 0 else None,
                dependencies=dependencies or set(),
                size_bytes=size_bytes
            )
            
            # Store in cache
            evicted_entry = self._cache.put(key, entry)
            
            # Update statistics
            self.stats.total_entries = self._cache.size()
            self.stats.total_size_bytes += size_bytes
            
            if evicted_entry:
                self.stats.eviction_count += 1
                self.stats.total_size_bytes -= evicted_entry.size_bytes
                self._remove_dependencies(evicted_entry.key)
            
            # Update dependency tracking
            if dependencies:
                self._add_dependencies(key, dependencies)
            
            self.logger.debug(f"Cached data for key: {key} (type: {entry_type.value}, ttl: {ttl}s)")
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry"""
        entry = self._cache.remove(key)
        
        if entry:
            self.stats.invalidation_count += 1
            self.stats.total_entries = self._cache.size()
            self.stats.total_size_bytes -= entry.size_bytes
            
            # Invalidate dependent entries BEFORE removing dependencies
            await self._invalidate_dependents(key)
            
            # Remove dependencies
            self._remove_dependencies(key)
            
            self.logger.debug(f"Invalidated cache entry: {key}")
            return True
        
        return False
    
    async def invalidate_by_type(self, entry_type: CacheEntryType) -> int:
        """Invalidate all cache entries of a specific type"""
        invalidated_count = 0
        keys_to_remove = []
        
        # Find entries to invalidate
        for key, entry in self._cache.items():
            if entry.entry_type == entry_type:
                keys_to_remove.append(key)
        
        # Remove entries
        for key in keys_to_remove:
            if await self.invalidate(key):
                invalidated_count += 1
        
        self.logger.info(f"Invalidated {invalidated_count} entries of type {entry_type.value}")
        return invalidated_count
    
    async def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a key pattern"""
        import re
        
        invalidated_count = 0
        keys_to_remove = []
        
        # Compile regex pattern
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        
        # Find matching entries
        for key in self._cache.keys():
            if regex.search(key):
                keys_to_remove.append(key)
        
        # Remove entries
        for key in keys_to_remove:
            if await self.invalidate(key):
                invalidated_count += 1
        
        self.logger.info(f"Invalidated {invalidated_count} entries matching pattern: {pattern}")
        return invalidated_count
    
    def _add_dependencies(self, key: str, dependencies: Set[str]) -> None:
        """Add dependency relationships for intelligent invalidation"""
        self._dependency_graph[key] = dependencies
        
        # Update reverse dependencies
        for dep in dependencies:
            if dep not in self._reverse_dependencies:
                self._reverse_dependencies[dep] = set()
            self._reverse_dependencies[dep].add(key)
    
    def _remove_dependencies(self, key: str) -> None:
        """Remove dependency relationships for a key"""
        # Remove from dependency graph
        dependencies = self._dependency_graph.pop(key, set())
        
        # Update reverse dependencies
        for dep in dependencies:
            if dep in self._reverse_dependencies:
                self._reverse_dependencies[dep].discard(key)
                if not self._reverse_dependencies[dep]:
                    del self._reverse_dependencies[dep]
        
        # Remove from reverse dependencies
        if key in self._reverse_dependencies:
            del self._reverse_dependencies[key]
    
    async def _invalidate_dependents(self, key: str) -> None:
        """Invalidate all entries that depend on the given key"""
        dependents = self._reverse_dependencies.get(key, set())
        
        for dependent in dependents.copy():  # Copy to avoid modification during iteration
            await self.invalidate(dependent)
    
    # Real-time data management
    
    async def update_real_time_data(self, data_type: str, data: Any) -> None:
        """Update real-time data and notify subscribers"""
        async with self._real_time_lock:
            old_data = self._real_time_data.get(data_type)
            self._real_time_data[data_type] = data
            
            # Cache real-time data with no TTL
            await self.put(
                f"realtime:{data_type}",
                data,
                CacheEntryType.REAL_TIME_DATA,
                ttl_override=0  # No expiration for real-time data
            )
            
            # Notify subscribers
            subscribers = self._real_time_subscribers.get(data_type, [])
            for callback in subscribers:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data_type, data)
                    else:
                        callback(data_type, data)
                except Exception as e:
                    self.logger.error(f"Error in real-time data callback: {e}")
            
            self.logger.debug(f"Updated real-time data: {data_type}")
    
    async def subscribe_real_time_updates(
        self, 
        data_type: str, 
        callback: Callable[[str, Any], None]
    ) -> None:
        """Subscribe to real-time data updates"""
        async with self._real_time_lock:
            if data_type not in self._real_time_subscribers:
                self._real_time_subscribers[data_type] = []
            
            self._real_time_subscribers[data_type].append(callback)
            
            # Send current data if available
            if data_type in self._real_time_data:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data_type, self._real_time_data[data_type])
                    else:
                        callback(data_type, self._real_time_data[data_type])
                except Exception as e:
                    self.logger.error(f"Error in initial real-time data callback: {e}")
        
        self.logger.debug(f"Subscribed to real-time updates: {data_type}")
    
    async def unsubscribe_real_time_updates(
        self, 
        data_type: str, 
        callback: Callable[[str, Any], None]
    ) -> bool:
        """Unsubscribe from real-time data updates"""
        async with self._real_time_lock:
            subscribers = self._real_time_subscribers.get(data_type, [])
            if callback in subscribers:
                subscribers.remove(callback)
                self.logger.debug(f"Unsubscribed from real-time updates: {data_type}")
                return True
            return False
    
    def get_real_time_data(self, data_type: str) -> Optional[Any]:
        """Get current real-time data"""
        return self._real_time_data.get(data_type)
    
    # Persistence methods
    
    async def _persist_cache_data(self) -> None:
        """Persist cache data to disk for offline access"""
        if not self.enable_persistence:
            return
        
        try:
            # Prepare data for persistence
            cache_data = {
                "entries": {},
                "real_time_data": self._real_time_data.copy(),
                "stats": {
                    "total_entries": self.stats.total_entries,
                    "total_size_bytes": self.stats.total_size_bytes,
                    "hit_count": self.stats.hit_count,
                    "miss_count": self.stats.miss_count,
                    "eviction_count": self.stats.eviction_count,
                    "invalidation_count": self.stats.invalidation_count
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Serialize cache entries (only non-expired ones)
            for key, entry in self._cache.items():
                if not entry.is_expired:
                    cache_data["entries"][key] = {
                        "value": entry.value,
                        "entry_type": entry.entry_type.value,
                        "created_at": entry.created_at.isoformat(),
                        "last_accessed": entry.last_accessed.isoformat(),
                        "access_count": entry.access_count,
                        "ttl_seconds": entry.ttl_seconds,
                        "dependencies": list(entry.dependencies),
                        "size_bytes": entry.size_bytes
                    }
            
            # Write to file
            cache_file = self.persistence_path / "cache_data.json"
            
            def write_cache_file():
                with open(cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2, default=str)
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor, write_cache_file
            )
            
            self.stats.persistence_saves += 1
            self.logger.debug(f"Persisted {len(cache_data['entries'])} cache entries")
            
        except Exception as e:
            self.logger.error(f"Failed to persist cache data: {e}")
    
    async def _load_persisted_data(self) -> None:
        """Load persisted cache data from disk"""
        if not self.enable_persistence:
            return
        
        cache_file = self.persistence_path / "cache_data.json"
        
        if not cache_file.exists():
            return
        
        try:
            def read_cache_file():
                with open(cache_file, 'r') as f:
                    return json.load(f)
            
            cache_data = await asyncio.get_event_loop().run_in_executor(
                self._executor, read_cache_file
            )
            
            # Restore cache entries
            entries_loaded = 0
            for key, entry_data in cache_data.get("entries", {}).items():
                try:
                    # Recreate cache entry
                    entry = CacheEntry(
                        key=key,
                        value=entry_data["value"],
                        entry_type=CacheEntryType(entry_data["entry_type"]),
                        created_at=datetime.fromisoformat(entry_data["created_at"]),
                        last_accessed=datetime.fromisoformat(entry_data["last_accessed"]),
                        access_count=entry_data["access_count"],
                        ttl_seconds=entry_data["ttl_seconds"],
                        dependencies=set(entry_data.get("dependencies", [])),
                        size_bytes=entry_data["size_bytes"]
                    )
                    
                    # Only load if not expired
                    if not entry.is_expired:
                        self._cache.put(key, entry)
                        entries_loaded += 1
                        
                        # Restore dependencies
                        if entry.dependencies:
                            self._add_dependencies(key, entry.dependencies)
                
                except Exception as e:
                    self.logger.warning(f"Failed to restore cache entry {key}: {e}")
            
            # Restore real-time data
            self._real_time_data.update(cache_data.get("real_time_data", {}))
            
            # Update statistics
            self.stats.total_entries = self._cache.size()
            self.stats.persistence_loads += 1
            
            self.logger.info(f"Loaded {entries_loaded} cache entries from persistence")
            
        except Exception as e:
            self.logger.error(f"Failed to load persisted cache data: {e}")
    
    # Cache management and monitoring
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            "total_entries": self.stats.total_entries,
            "total_size_bytes": self.stats.total_size_bytes,
            "total_size_mb": self.stats.total_size_bytes / (1024 * 1024),
            "hit_count": self.stats.hit_count,
            "miss_count": self.stats.miss_count,
            "hit_rate": self.stats.hit_rate,
            "eviction_count": self.stats.eviction_count,
            "invalidation_count": self.stats.invalidation_count,
            "average_entry_size": self.stats.average_entry_size,
            "max_size": self.max_size,
            "utilization": self.stats.total_entries / self.max_size,
            "persistence_saves": self.stats.persistence_saves,
            "persistence_loads": self.stats.persistence_loads,
            "real_time_data_types": len(self._real_time_data),
            "real_time_subscribers": sum(len(subs) for subs in self._real_time_subscribers.values())
        }
    
    def get_cache_entries_info(self) -> List[Dict[str, Any]]:
        """Get information about all cache entries"""
        entries_info = []
        
        for key, entry in self._cache.items():
            entries_info.append({
                "key": key,
                "entry_type": entry.entry_type.value,
                "size_bytes": entry.size_bytes,
                "created_at": entry.created_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "age_seconds": entry.age_seconds,
                "ttl_seconds": entry.ttl_seconds,
                "is_expired": entry.is_expired,
                "dependencies": list(entry.dependencies)
            })
        
        return entries_info
    
    async def clear_cache(self, entry_type: Optional[CacheEntryType] = None) -> int:
        """Clear cache entries, optionally filtered by type"""
        if entry_type is None:
            # Clear all entries
            count = self._cache.size()
            self._cache.clear()
            self._dependency_graph.clear()
            self._reverse_dependencies.clear()
            self.stats.total_entries = 0
            self.stats.total_size_bytes = 0
            self.logger.info(f"Cleared all {count} cache entries")
            return count
        else:
            # Clear entries of specific type
            return await self.invalidate_by_type(entry_type)
    
    async def optimize_cache(self) -> Dict[str, int]:
        """Optimize cache by removing expired entries and defragmenting"""
        with timer(self.perf_logger, "cache_optimization"):
            # Remove expired entries
            expired_count = self._cache.cleanup_expired()
            
            # Update statistics
            self.stats.total_entries = self._cache.size()
            self.stats.eviction_count += expired_count
            
            # Recalculate total size
            total_size = sum(entry.size_bytes for entry in self._cache.values())
            self.stats.total_size_bytes = total_size
            
            # Clean up orphaned dependencies
            orphaned_deps = 0
            valid_keys = set(self._cache.keys())
            
            # Clean dependency graph
            for key in list(self._dependency_graph.keys()):
                if key not in valid_keys:
                    del self._dependency_graph[key]
                    orphaned_deps += 1
            
            # Clean reverse dependencies
            for key in list(self._reverse_dependencies.keys()):
                if key not in valid_keys:
                    del self._reverse_dependencies[key]
                    orphaned_deps += 1
            
            optimization_results = {
                "expired_entries_removed": expired_count,
                "orphaned_dependencies_cleaned": orphaned_deps,
                "final_entry_count": self.stats.total_entries,
                "final_size_bytes": self.stats.total_size_bytes
            }
            
            self.logger.info(f"Cache optimization completed: {optimization_results}")
            return optimization_results
    
    async def shutdown(self) -> None:
        """Shutdown cache service and cleanup resources"""
        self.logger.info("Shutting down data cache service")
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        if self._persistence_task:
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass
        
        # Final persistence save
        if self.enable_persistence:
            await self._persist_cache_data()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        self.logger.info("Data cache service shutdown complete")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()