#!/usr/bin/env python3
"""
Data Cache Service Example

Demonstrates the usage of DataCacheService with intelligent caching,
real-time data updates, and persistence features.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from mcp_tui_client.services.data_cache import (
    DataCacheService, CacheEntryType, CacheStats
)
from mcp_tui_client.services.mcp_client import MCPClientService, MCPConfig
from mcp_tui_client.utils.logging import setup_logging


async def simulate_api_call(data_type: str, delay: float = 0.1) -> dict:
    """Simulate an API call with some delay"""
    await asyncio.sleep(delay)
    return {
        "data_type": data_type,
        "timestamp": datetime.now().isoformat(),
        "value": f"simulated_{data_type}_data",
        "metadata": {"source": "api", "cached": False}
    }


async def demonstrate_basic_caching():
    """Demonstrate basic caching functionality"""
    print("\n=== Basic Caching Demo ===")
    
    # Create cache service
    cache = DataCacheService(
        max_size=100,
        default_ttl=300,
        enable_persistence=False  # Disable for demo
    )
    
    try:
        # Cache miss - will fetch data
        print("1. Cache miss - fetching data...")
        start_time = datetime.now()
        
        async def fetch_bot_data():
            return await simulate_api_call("bot_123")
        
        data = await cache.get(
            "bot_123_data",
            fetch_func=fetch_bot_data,
            entry_type=CacheEntryType.BOT_DATA
        )
        
        fetch_time = (datetime.now() - start_time).total_seconds()
        print(f"   Fetched in {fetch_time:.3f}s: {data['value']}")
        
        # Cache hit - will use cached data
        print("2. Cache hit - using cached data...")
        start_time = datetime.now()
        
        cached_data = await cache.get("bot_123_data")
        
        cache_time = (datetime.now() - start_time).total_seconds()
        print(f"   Retrieved in {cache_time:.6f}s: {cached_data['value']}")
        print(f"   Speed improvement: {fetch_time/cache_time:.1f}x faster")
        
        # Show cache stats
        stats = cache.get_cache_stats()
        print(f"3. Cache stats: {stats['hit_count']} hits, {stats['miss_count']} misses, "
              f"{stats['hit_rate']:.1%} hit rate")
        
    finally:
        await cache.shutdown()


async def demonstrate_intelligent_invalidation():
    """Demonstrate intelligent cache invalidation"""
    print("\n=== Intelligent Invalidation Demo ===")
    
    cache = DataCacheService(max_size=100, enable_persistence=False)
    
    try:
        # Add data with dependencies
        await cache.put(
            "bot_performance",
            {"profit": 1000, "trades": 50},
            CacheEntryType.PERFORMANCE_METRICS,
            dependencies={"bot_123_data"}
        )
        
        await cache.put(
            "bot_123_data",
            {"status": "active", "balance": 5000},
            CacheEntryType.BOT_DATA
        )
        
        print("1. Added bot data and performance metrics (with dependency)")
        
        # Verify both entries exist
        bot_data = await cache.get("bot_123_data")
        performance = await cache.get("bot_performance")
        print(f"   Bot data: {bot_data}")
        print(f"   Performance: {performance}")
        
        # Invalidate base data - should also invalidate dependent data
        print("2. Invalidating bot data...")
        await cache.invalidate("bot_123_data")
        
        # Check if dependent data was also invalidated
        bot_data_after = await cache.get("bot_123_data")
        performance_after = await cache.get("bot_performance")
        
        print(f"   Bot data after invalidation: {bot_data_after}")
        print(f"   Performance after invalidation: {performance_after}")
        print("   ✓ Dependent data was automatically invalidated")
        
    finally:
        await cache.shutdown()


async def demonstrate_real_time_updates():
    """Demonstrate real-time data updates and subscriptions"""
    print("\n=== Real-Time Data Updates Demo ===")
    
    cache = DataCacheService(max_size=100, enable_persistence=False)
    
    # Track received updates
    received_updates = []
    
    def price_update_handler(data_type: str, data: dict):
        received_updates.append((data_type, data))
        print(f"   📈 Price update: {data_type} = {data}")
    
    try:
        # Subscribe to real-time price updates
        await cache.subscribe_real_time_updates("market_prices", price_update_handler)
        print("1. Subscribed to market price updates")
        
        # Simulate price updates
        print("2. Simulating price updates...")
        await cache.update_real_time_data("market_prices", {"BTC": 45000, "ETH": 2800})
        await asyncio.sleep(0.1)  # Allow callback to execute
        
        await cache.update_real_time_data("market_prices", {"BTC": 45100, "ETH": 2820})
        await asyncio.sleep(0.1)
        
        await cache.update_real_time_data("market_prices", {"BTC": 44950, "ETH": 2790})
        await asyncio.sleep(0.1)
        
        print(f"3. Received {len(received_updates)} updates")
        
        # Get current real-time data
        current_prices = cache.get_real_time_data("market_prices")
        print(f"4. Current prices: {current_prices}")
        
    finally:
        await cache.shutdown()


async def demonstrate_ttl_and_cleanup():
    """Demonstrate TTL-based expiration and cleanup"""
    print("\n=== TTL and Cleanup Demo ===")
    
    cache = DataCacheService(
        max_size=100, 
        enable_persistence=False,
        cleanup_interval=1  # Fast cleanup for demo
    )
    
    try:
        # Add data with different TTL values
        await cache.put("short_lived", "expires_soon", CacheEntryType.MARKET_DATA, ttl_override=1)
        await cache.put("long_lived", "expires_later", CacheEntryType.STATIC_DATA, ttl_override=5)
        
        print("1. Added short-lived (1s TTL) and long-lived (5s TTL) data")
        
        # Check initial state
        short_data = await cache.get("short_lived")
        long_data = await cache.get("long_lived")
        print(f"   Short-lived: {short_data}")
        print(f"   Long-lived: {long_data}")
        
        # Wait for short-lived data to expire
        print("2. Waiting 2 seconds for short-lived data to expire...")
        await asyncio.sleep(2)
        
        # Check after expiration
        short_data_after = await cache.get("short_lived")
        long_data_after = await cache.get("long_lived")
        print(f"   Short-lived after 2s: {short_data_after}")
        print(f"   Long-lived after 2s: {long_data_after}")
        
        if short_data_after is None and long_data_after is not None:
            print("   ✓ TTL-based expiration working correctly")
        
    finally:
        await cache.shutdown()


async def demonstrate_persistence():
    """Demonstrate cache persistence"""
    print("\n=== Persistence Demo ===")
    
    # Create temporary directory for persistence
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_path = Path(temp_dir) / "cache_demo"
        
        # First cache instance - add data and persist
        cache1 = DataCacheService(
            max_size=100,
            persistence_path=str(cache_path),
            enable_persistence=True
        )
        
        try:
            await cache1.put("persistent_data", "this_should_survive", CacheEntryType.STATIC_DATA)
            await cache1.update_real_time_data("persistent_rt", {"value": 42})
            
            print("1. Added data to first cache instance")
            
            # Force persistence
            await cache1._persist_cache_data()
            print("2. Persisted cache data to disk")
            
        finally:
            await cache1.shutdown()
        
        # Second cache instance - load persisted data
        cache2 = DataCacheService(
            max_size=100,
            persistence_path=str(cache_path),
            enable_persistence=True
        )
        
        try:
            # Load persisted data
            await cache2._load_persisted_data()
            print("3. Created new cache instance and loaded persisted data")
            
            # Check if data was restored
            restored_data = await cache2.get("persistent_data")
            restored_rt = cache2.get_real_time_data("persistent_rt")
            
            print(f"   Restored cache data: {restored_data}")
            print(f"   Restored real-time data: {restored_rt}")
            
            if restored_data and restored_rt:
                print("   ✓ Data persistence working correctly")
            
        finally:
            await cache2.shutdown()


async def demonstrate_performance_monitoring():
    """Demonstrate cache performance monitoring"""
    print("\n=== Performance Monitoring Demo ===")
    
    cache = DataCacheService(max_size=50, enable_persistence=False)
    
    try:
        # Add various types of data
        data_types = [
            (CacheEntryType.BOT_DATA, "bot"),
            (CacheEntryType.LAB_DATA, "lab"),
            (CacheEntryType.MARKET_DATA, "market"),
            (CacheEntryType.STATIC_DATA, "static")
        ]
        
        print("1. Adding test data...")
        for i in range(20):
            entry_type, prefix = data_types[i % len(data_types)]
            await cache.put(f"{prefix}_{i}", f"data_{i}", entry_type)
        
        # Generate some cache hits and misses
        print("2. Generating cache activity...")
        for i in range(30):
            key = f"bot_{i % 10}"  # Some hits, some misses
            await cache.get(key)
        
        # Show detailed statistics
        stats = cache.get_cache_stats()
        print("3. Cache Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.3f}")
            else:
                print(f"   {key}: {value}")
        
        # Show cache entries info
        entries_info = cache.get_cache_entries_info()
        print(f"4. Cache contains {len(entries_info)} entries:")
        
        # Group by entry type
        by_type = {}
        for entry in entries_info:
            entry_type = entry["entry_type"]
            by_type[entry_type] = by_type.get(entry_type, 0) + 1
        
        for entry_type, count in by_type.items():
            print(f"   {entry_type}: {count} entries")
        
        # Optimize cache
        print("5. Optimizing cache...")
        optimization_results = await cache.optimize_cache()
        print(f"   Optimization results: {optimization_results}")
        
    finally:
        await cache.shutdown()


async def main():
    """Run all demonstrations"""
    # Set up logging
    setup_logging(level="INFO")
    
    print("🚀 Data Cache Service Demonstration")
    print("=" * 50)
    
    try:
        await demonstrate_basic_caching()
        await demonstrate_intelligent_invalidation()
        await demonstrate_real_time_updates()
        await demonstrate_ttl_and_cleanup()
        await demonstrate_persistence()
        await demonstrate_performance_monitoring()
        
        print("\n✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())