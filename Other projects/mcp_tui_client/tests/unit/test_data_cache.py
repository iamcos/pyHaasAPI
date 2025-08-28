"""
Unit tests for DataCacheService

Tests for LRU cache, TTL support, intelligent invalidation, real-time data propagation,
and data persistence functionality.
"""

import asyncio
import json
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from mcp_tui_client.services.data_cache import (
    DataCacheService, CacheEntry, CacheEntryType, InvalidationStrategy,
    LRUCache, CacheStats
)


class TestLRUCache:
    """Test LRU cache implementation"""
    
    def test_basic_operations(self):
        """Test basic cache operations"""
        cache = LRUCache(max_size=3)
        
        # Create test entries
        entry1 = CacheEntry(
            key="key1",
            value="value1",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        entry2 = CacheEntry(
            key="key2",
            value="value2",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        # Test put and get
        cache.put("key1", entry1)
        cache.put("key2", entry2)
        
        assert cache.get("key1") == entry1
        assert cache.get("key2") == entry2
        assert cache.get("nonexistent") is None
        assert cache.size() == 2
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full"""
        cache = LRUCache(max_size=2)
        
        # Create test entries
        entries = []
        for i in range(3):
            entry = CacheEntry(
                key=f"key{i}",
                value=f"value{i}",
                entry_type=CacheEntryType.STATIC_DATA,
                created_at=datetime.now(),
                last_accessed=datetime.now()
            )
            entries.append(entry)
        
        # Fill cache
        cache.put("key0", entries[0])
        cache.put("key1", entries[1])
        
        # Access key0 to make it most recently used
        cache.get("key0")
        
        # Add third entry, should evict key1 (least recently used)
        evicted = cache.put("key2", entries[2])
        
        assert evicted == entries[1]
        assert cache.get("key0") == entries[0]  # Still in cache
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == entries[2]  # Newly added
    
    def test_ttl_expiration(self):
        """Test TTL-based expiration"""
        cache = LRUCache(max_size=10)
        
        # Create expired entry
        expired_entry = CacheEntry(
            key="expired",
            value="expired_value",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now() - timedelta(seconds=10),
            last_accessed=datetime.now() - timedelta(seconds=10),
            ttl_seconds=5  # Expired 5 seconds ago
        )
        
        # Create valid entry
        valid_entry = CacheEntry(
            key="valid",
            value="valid_value",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=300  # Valid for 5 minutes
        )
        
        cache.put("expired", expired_entry)
        cache.put("valid", valid_entry)
        
        # Expired entry should be removed on access
        assert cache.get("expired") is None
        assert cache.get("valid") == valid_entry
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries"""
        cache = LRUCache(max_size=10)
        
        # Add expired and valid entries
        for i in range(5):
            expired_entry = CacheEntry(
                key=f"expired{i}",
                value=f"expired_value{i}",
                entry_type=CacheEntryType.STATIC_DATA,
                created_at=datetime.now() - timedelta(seconds=10),
                last_accessed=datetime.now() - timedelta(seconds=10),
                ttl_seconds=5
            )
            cache.put(f"expired{i}", expired_entry)
        
        for i in range(3):
            valid_entry = CacheEntry(
                key=f"valid{i}",
                value=f"valid_value{i}",
                entry_type=CacheEntryType.STATIC_DATA,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=300
            )
            cache.put(f"valid{i}", valid_entry)
        
        # Cleanup expired entries
        expired_count = cache.cleanup_expired()
        
        assert expired_count == 5
        assert cache.size() == 3


class TestDataCacheService:
    """Test DataCacheService functionality"""
    
    @pytest.fixture
    async def cache_service(self):
        """Create cache service for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DataCacheService(
                max_size=100,
                default_ttl=300,
                persistence_path=temp_dir,
                enable_persistence=True,
                cleanup_interval=1  # Fast cleanup for testing
            )
            yield service
            await service.shutdown()
    
    @pytest.mark.asyncio
    async def test_basic_cache_operations(self, cache_service):
        """Test basic cache get/put operations"""
        # Test put and get
        await cache_service.put("test_key", "test_value", CacheEntryType.STATIC_DATA)
        
        result = await cache_service.get("test_key")
        assert result == "test_value"
        
        # Test cache miss
        result = await cache_service.get("nonexistent_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_function(self, cache_service):
        """Test cache with fetch function for misses"""
        fetch_mock = Mock(return_value="fetched_value")
        
        # First call should fetch and cache
        result = await cache_service.get(
            "fetch_key", 
            fetch_func=fetch_mock,
            entry_type=CacheEntryType.STATIC_DATA
        )
        
        assert result == "fetched_value"
        assert fetch_mock.call_count == 1
        
        # Second call should use cache
        result = await cache_service.get("fetch_key")
        assert result == "fetched_value"
        assert fetch_mock.call_count == 1  # Not called again
    
    @pytest.mark.asyncio
    async def test_async_fetch_function(self, cache_service):
        """Test cache with async fetch function"""
        async def async_fetch():
            await asyncio.sleep(0.01)  # Simulate async work
            return "async_fetched_value"
        
        result = await cache_service.get(
            "async_fetch_key",
            fetch_func=async_fetch,
            entry_type=CacheEntryType.STATIC_DATA
        )
        
        assert result == "async_fetched_value"
        
        # Verify it's cached
        result = await cache_service.get("async_fetch_key")
        assert result == "async_fetched_value"
    
    @pytest.mark.asyncio
    async def test_ttl_by_entry_type(self, cache_service):
        """Test different TTL values by entry type"""
        # Market data should have short TTL
        await cache_service.put("market_data", "market_value", CacheEntryType.MARKET_DATA)
        
        # Static data should have long TTL
        await cache_service.put("static_data", "static_value", CacheEntryType.STATIC_DATA)
        
        # Check cache entries have correct TTL
        entries_info = cache_service.get_cache_entries_info()
        
        market_entry = next(e for e in entries_info if e["key"] == "market_data")
        static_entry = next(e for e in entries_info if e["key"] == "static_data")
        
        assert market_entry["ttl_seconds"] == 5  # Market data TTL
        assert static_entry["ttl_seconds"] == 86400  # Static data TTL
    
    @pytest.mark.asyncio
    async def test_invalidation(self, cache_service):
        """Test cache invalidation"""
        # Add test data
        await cache_service.put("key1", "value1", CacheEntryType.STATIC_DATA)
        await cache_service.put("key2", "value2", CacheEntryType.BOT_DATA)
        await cache_service.put("key3", "value3", CacheEntryType.BOT_DATA)
        
        # Test single key invalidation
        result = await cache_service.invalidate("key1")
        assert result is True
        assert await cache_service.get("key1") is None
        assert await cache_service.get("key2") == "value2"
        
        # Test invalidation by type
        count = await cache_service.invalidate_by_type(CacheEntryType.BOT_DATA)
        assert count == 2
        assert await cache_service.get("key2") is None
        assert await cache_service.get("key3") is None
    
    @pytest.mark.asyncio
    async def test_invalidation_by_pattern(self, cache_service):
        """Test pattern-based invalidation"""
        # Add test data with patterns
        await cache_service.put("bot_123_data", "bot_data", CacheEntryType.BOT_DATA)
        await cache_service.put("bot_456_data", "bot_data", CacheEntryType.BOT_DATA)
        await cache_service.put("lab_789_data", "lab_data", CacheEntryType.LAB_DATA)
        
        # Invalidate all bot data
        count = await cache_service.invalidate_by_pattern(r"bot_\d+_data")
        assert count == 2
        
        # Verify only bot data was invalidated
        assert await cache_service.get("bot_123_data") is None
        assert await cache_service.get("bot_456_data") is None
        assert await cache_service.get("lab_789_data") == "lab_data"
    
    @pytest.mark.asyncio
    async def test_dependency_invalidation(self, cache_service):
        """Test dependency-based invalidation"""
        # Add data with dependencies
        await cache_service.put(
            "dependent_data", 
            "dependent_value",
            CacheEntryType.STATIC_DATA,
            dependencies={"base_data"}
        )
        
        await cache_service.put("base_data", "base_value", CacheEntryType.STATIC_DATA)
        
        # Invalidating base data should invalidate dependent data
        await cache_service.invalidate("base_data")
        
        assert await cache_service.get("base_data") is None
        assert await cache_service.get("dependent_data") is None
    
    @pytest.mark.asyncio
    async def test_real_time_data_updates(self, cache_service):
        """Test real-time data updates and subscriptions"""
        callback_data = []
        
        def callback(data_type: str, data: any):
            callback_data.append((data_type, data))
        
        # Subscribe to updates
        await cache_service.subscribe_real_time_updates("market_prices", callback)
        
        # Update real-time data
        await cache_service.update_real_time_data("market_prices", {"BTC": 50000, "ETH": 3000})
        
        # Wait for callback
        await asyncio.sleep(0.01)
        
        # Verify callback was called
        assert len(callback_data) == 1
        assert callback_data[0][0] == "market_prices"
        assert callback_data[0][1] == {"BTC": 50000, "ETH": 3000}
        
        # Verify data is accessible
        data = cache_service.get_real_time_data("market_prices")
        assert data == {"BTC": 50000, "ETH": 3000}
    
    @pytest.mark.asyncio
    async def test_real_time_data_unsubscribe(self, cache_service):
        """Test unsubscribing from real-time data updates"""
        callback_data = []
        
        def callback(data_type: str, data: any):
            callback_data.append((data_type, data))
        
        # Subscribe and then unsubscribe
        await cache_service.subscribe_real_time_updates("test_data", callback)
        result = await cache_service.unsubscribe_real_time_updates("test_data", callback)
        
        assert result is True
        
        # Update data - callback should not be called
        await cache_service.update_real_time_data("test_data", "test_value")
        await asyncio.sleep(0.01)
        
        assert len(callback_data) == 0
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_service):
        """Test cache statistics"""
        # Add some data
        await cache_service.put("key1", "value1", CacheEntryType.STATIC_DATA)
        await cache_service.put("key2", "value2", CacheEntryType.BOT_DATA)
        
        # Access data to generate hits
        await cache_service.get("key1")
        await cache_service.get("key1")
        await cache_service.get("nonexistent")  # Miss
        
        stats = cache_service.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["hit_count"] == 2
        assert stats["miss_count"] == 1
        assert stats["hit_rate"] == 2/3
        assert stats["total_size_bytes"] > 0
    
    @pytest.mark.asyncio
    async def test_cache_optimization(self, cache_service):
        """Test cache optimization"""
        # Add expired entries
        for i in range(5):
            await cache_service.put(
                f"expired_key{i}",
                f"expired_value{i}",
                CacheEntryType.STATIC_DATA,
                ttl_override=0  # Immediately expired
            )
        
        # Add valid entries
        for i in range(3):
            await cache_service.put(
                f"valid_key{i}",
                f"valid_value{i}",
                CacheEntryType.STATIC_DATA
            )
        
        # Wait a bit for expiration
        await asyncio.sleep(0.01)
        
        # Optimize cache
        results = await cache_service.optimize_cache()
        
        assert results["expired_entries_removed"] >= 0
        assert results["final_entry_count"] <= 8  # Some may have been cleaned up
    
    @pytest.mark.asyncio
    async def test_clear_cache(self, cache_service):
        """Test cache clearing"""
        # Add test data
        await cache_service.put("key1", "value1", CacheEntryType.STATIC_DATA)
        await cache_service.put("key2", "value2", CacheEntryType.BOT_DATA)
        
        # Clear specific type
        count = await cache_service.clear_cache(CacheEntryType.BOT_DATA)
        assert count == 1
        assert await cache_service.get("key1") == "value1"
        assert await cache_service.get("key2") is None
        
        # Clear all
        count = await cache_service.clear_cache()
        assert count == 1
        assert await cache_service.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_persistence(self, cache_service):
        """Test data persistence"""
        # Add test data
        await cache_service.put("persistent_key", "persistent_value", CacheEntryType.STATIC_DATA)
        await cache_service.update_real_time_data("persistent_rt", {"data": "value"})
        
        # Force persistence
        await cache_service._persist_cache_data()
        
        # Create new cache service with same persistence path
        new_service = DataCacheService(
            max_size=100,
            persistence_path=cache_service.persistence_path,
            enable_persistence=True
        )
        
        try:
            # Load persisted data
            await new_service._load_persisted_data()
            
            # Verify data was restored
            result = await new_service.get("persistent_key")
            assert result == "persistent_value"
            
            rt_data = new_service.get_real_time_data("persistent_rt")
            assert rt_data == {"data": "value"}
            
        finally:
            await new_service.shutdown()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, cache_service):
        """Test error handling in cache operations"""
        # Test fetch function error
        def failing_fetch():
            raise ValueError("Fetch failed")
        
        with pytest.raises(Exception):
            await cache_service.get("error_key", fetch_func=failing_fetch)
        
        # Test invalid regex pattern
        with pytest.raises(ValueError):
            await cache_service.invalidate_by_pattern("[invalid regex")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, cache_service):
        """Test concurrent cache operations"""
        async def put_data(key_prefix: str, count: int):
            for i in range(count):
                await cache_service.put(f"{key_prefix}_{i}", f"value_{i}", CacheEntryType.STATIC_DATA)
        
        async def get_data(key_prefix: str, count: int):
            results = []
            for i in range(count):
                result = await cache_service.get(f"{key_prefix}_{i}")
                results.append(result)
            return results
        
        # Run concurrent operations
        await asyncio.gather(
            put_data("concurrent1", 10),
            put_data("concurrent2", 10),
            put_data("concurrent3", 10)
        )
        
        # Verify all data was stored
        results = await asyncio.gather(
            get_data("concurrent1", 10),
            get_data("concurrent2", 10),
            get_data("concurrent3", 10)
        )
        
        for result_set in results:
            assert len(result_set) == 10
            assert all(r is not None for r in result_set)


class TestCacheEntry:
    """Test CacheEntry functionality"""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation and properties"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=300
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.entry_type == CacheEntryType.STATIC_DATA
        assert entry.ttl_seconds == 300
        assert not entry.is_expired
        assert entry.age_seconds >= 0
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic"""
        # Create expired entry
        expired_entry = CacheEntry(
            key="expired",
            value="value",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now() - timedelta(seconds=10),
            last_accessed=datetime.now() - timedelta(seconds=10),
            ttl_seconds=5
        )
        
        assert expired_entry.is_expired
        
        # Create non-expiring entry
        no_ttl_entry = CacheEntry(
            key="no_ttl",
            value="value",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now() - timedelta(seconds=10),
            last_accessed=datetime.now() - timedelta(seconds=10),
            ttl_seconds=None
        )
        
        assert not no_ttl_entry.is_expired
    
    def test_cache_entry_touch(self):
        """Test cache entry touch functionality"""
        entry = CacheEntry(
            key="test",
            value="value",
            entry_type=CacheEntryType.STATIC_DATA,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=0
        )
        
        original_access_time = entry.last_accessed
        original_count = entry.access_count
        
        # Wait a bit and touch
        time.sleep(0.01)
        entry.touch()
        
        assert entry.last_accessed > original_access_time
        assert entry.access_count == original_count + 1


class TestCacheStats:
    """Test CacheStats functionality"""
    
    def test_cache_stats_calculations(self):
        """Test cache statistics calculations"""
        stats = CacheStats(
            total_entries=10,
            total_size_bytes=1000,
            hit_count=80,
            miss_count=20
        )
        
        assert stats.hit_rate == 0.8
        assert stats.average_entry_size == 100.0
        
        # Test with zero values
        empty_stats = CacheStats()
        assert empty_stats.hit_rate == 0.0
        assert empty_stats.average_entry_size == 0.0


if __name__ == "__main__":
    pytest.main([__file__])