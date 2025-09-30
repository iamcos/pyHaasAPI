"""
Async Factory for pyHaasAPI v2

This module provides factory functions for creating async clients
with different configurations and presets.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .async_client import AsyncHaasClientWrapper, AsyncClientConfig
from .async_utils import RateLimitConfig, RetryConfig, BatchConfig
from .client import AsyncHaasClient
from .auth import AuthenticationManager
from .logging import get_logger

logger = get_logger("async_factory")


@dataclass
class ClientPreset:
    """Preset configuration for async client"""
    name: str
    description: str
    config: AsyncClientConfig


class AsyncClientFactory:
    """
    Factory for creating async clients with different configurations.
    
    Provides preset configurations for different use cases and
    custom configuration options.
    """

    # Preset configurations
    PRESETS = {
        "development": ClientPreset(
            name="development",
            description="Development configuration with relaxed limits",
            config=AsyncClientConfig(
                rate_limit=RateLimitConfig(max_requests=1000, time_window=60.0),
                retry=RetryConfig(max_retries=2, base_delay=0.5),
                batch=BatchConfig(batch_size=5, max_concurrent=3),
                cache_ttl=60.0,
                max_concurrent_requests=5,
                request_timeout=10.0,
                enable_caching=True,
                enable_rate_limiting=False,
                enable_retry=True,
                enable_batch_processing=True
            )
        ),
        
        "production": ClientPreset(
            name="production",
            description="Production configuration with strict limits",
            config=AsyncClientConfig(
                rate_limit=RateLimitConfig(max_requests=100, time_window=60.0, burst_limit=5),
                retry=RetryConfig(max_retries=3, base_delay=1.0, max_delay=30.0),
                batch=BatchConfig(batch_size=10, max_concurrent=5, delay_between_batches=0.2),
                cache_ttl=300.0,
                max_concurrent_requests=10,
                request_timeout=30.0,
                enable_caching=True,
                enable_rate_limiting=True,
                enable_retry=True,
                enable_batch_processing=True
            )
        ),
        
        "high_performance": ClientPreset(
            name="high_performance",
            description="High performance configuration for bulk operations",
            config=AsyncClientConfig(
                rate_limit=RateLimitConfig(max_requests=500, time_window=60.0, burst_limit=20),
                retry=RetryConfig(max_retries=2, base_delay=0.5, max_delay=10.0),
                batch=BatchConfig(batch_size=20, max_concurrent=10, delay_between_batches=0.1),
                cache_ttl=600.0,
                max_concurrent_requests=20,
                request_timeout=60.0,
                enable_caching=True,
                enable_rate_limiting=True,
                enable_retry=True,
                enable_batch_processing=True
            )
        ),
        
        "conservative": ClientPreset(
            name="conservative",
            description="Conservative configuration with strict rate limiting",
            config=AsyncClientConfig(
                rate_limit=RateLimitConfig(max_requests=50, time_window=60.0, burst_limit=2),
                retry=RetryConfig(max_retries=5, base_delay=2.0, max_delay=60.0),
                batch=BatchConfig(batch_size=5, max_concurrent=2, delay_between_batches=0.5),
                cache_ttl=900.0,
                max_concurrent_requests=3,
                request_timeout=45.0,
                enable_caching=True,
                enable_rate_limiting=True,
                enable_retry=True,
                enable_batch_processing=True
            )
        ),
        
        "testing": ClientPreset(
            name="testing",
            description="Testing configuration with minimal limits",
            config=AsyncClientConfig(
                rate_limit=RateLimitConfig(max_requests=1000, time_window=60.0),
                retry=RetryConfig(max_retries=1, base_delay=0.1),
                batch=BatchConfig(batch_size=3, max_concurrent=2),
                cache_ttl=30.0,
                max_concurrent_requests=3,
                request_timeout=5.0,
                enable_caching=False,
                enable_rate_limiting=False,
                enable_retry=False,
                enable_batch_processing=True
            )
        )
    }

    @classmethod
    def create_client(
        cls,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager,
        preset: Optional[str] = None,
        custom_config: Optional[AsyncClientConfig] = None
    ) -> AsyncHaasClientWrapper:
        """
        Create an async client with specified configuration.
        
        Args:
            client: The base async client
            auth_manager: Authentication manager
            preset: Preset configuration name
            custom_config: Custom configuration
            
        Returns:
            Configured async client wrapper
            
        Raises:
            ValueError: If preset is not found
        """
        if custom_config:
            config = custom_config
        elif preset:
            if preset not in cls.PRESETS:
                raise ValueError(f"Unknown preset: {preset}. Available presets: {list(cls.PRESETS.keys())}")
            config = cls.PRESETS[preset].config
        else:
            config = AsyncClientConfig()  # Default configuration
        
        logger.info(f"Creating async client with configuration: {preset or 'custom'}")
        return AsyncHaasClientWrapper(client, auth_manager, config)

    @classmethod
    def create_development_client(
        cls,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ) -> AsyncHaasClientWrapper:
        """Create a development client"""
        return cls.create_client(client, auth_manager, "development")

    @classmethod
    def create_production_client(
        cls,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ) -> AsyncHaasClientWrapper:
        """Create a production client"""
        return cls.create_client(client, auth_manager, "production")

    @classmethod
    def create_high_performance_client(
        cls,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ) -> AsyncHaasClientWrapper:
        """Create a high performance client"""
        return cls.create_client(client, auth_manager, "high_performance")

    @classmethod
    def create_conservative_client(
        cls,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ) -> AsyncHaasClientWrapper:
        """Create a conservative client"""
        return cls.create_client(client, auth_manager, "conservative")

    @classmethod
    def create_testing_client(
        cls,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager
    ) -> AsyncHaasClientWrapper:
        """Create a testing client"""
        return cls.create_client(client, auth_manager, "testing")

    @classmethod
    def get_available_presets(cls) -> List[str]:
        """Get list of available presets"""
        return list(cls.PRESETS.keys())

    @classmethod
    def get_preset_info(cls, preset: str) -> Optional[Dict[str, Any]]:
        """Get information about a preset"""
        if preset not in cls.PRESETS:
            return None
        
        preset_obj = cls.PRESETS[preset]
        return {
            "name": preset_obj.name,
            "description": preset_obj.description,
            "config": {
                "rate_limit": {
                    "max_requests": preset_obj.config.rate_limit.max_requests,
                    "time_window": preset_obj.config.rate_limit.time_window,
                    "burst_limit": preset_obj.config.rate_limit.burst_limit
                },
                "retry": {
                    "max_retries": preset_obj.config.retry.max_retries,
                    "base_delay": preset_obj.config.retry.base_delay,
                    "max_delay": preset_obj.config.retry.max_delay
                },
                "batch": {
                    "batch_size": preset_obj.config.batch.batch_size,
                    "max_concurrent": preset_obj.config.batch.max_concurrent,
                    "delay_between_batches": preset_obj.config.batch.delay_between_batches
                },
                "cache_ttl": preset_obj.config.cache_ttl,
                "max_concurrent_requests": preset_obj.config.max_concurrent_requests,
                "request_timeout": preset_obj.config.request_timeout,
                "enable_caching": preset_obj.config.enable_caching,
                "enable_rate_limiting": preset_obj.config.enable_rate_limiting,
                "enable_retry": preset_obj.config.enable_retry,
                "enable_batch_processing": preset_obj.config.enable_batch_processing
            }
        }

    @classmethod
    def create_custom_client(
        cls,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager,
        **kwargs
    ) -> AsyncHaasClientWrapper:
        """
        Create a client with custom configuration.
        
        Args:
            client: The base async client
            auth_manager: Authentication manager
            **kwargs: Configuration parameters
            
        Returns:
            Configured async client wrapper
        """
        # Create custom configuration
        config = AsyncClientConfig()
        
        # Update configuration with provided parameters
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                logger.warning(f"Unknown configuration parameter: {key}")
        
        return cls.create_client(client, auth_manager, custom_config=config)


# Convenience functions

def create_async_client(
    client: AsyncHaasClient,
    auth_manager: AuthenticationManager,
    preset: str = "production"
) -> AsyncHaasClientWrapper:
    """
    Create an async client with the specified preset.
    
    Args:
        client: The base async client
        auth_manager: Authentication manager
        preset: Preset configuration name
        
    Returns:
        Configured async client wrapper
    """
    return AsyncClientFactory.create_client(client, auth_manager, preset)


def create_async_client_with_config(
    client: AsyncHaasClient,
    auth_manager: AuthenticationManager,
    config: AsyncClientConfig
) -> AsyncHaasClientWrapper:
    """
    Create an async client with custom configuration.
    
    Args:
        client: The base async client
        auth_manager: Authentication manager
        config: Custom configuration
        
    Returns:
        Configured async client wrapper
    """
    return AsyncClientFactory.create_client(client, auth_manager, custom_config=config)


# Context manager for async client

class AsyncClientContext:
    """Context manager for async client with automatic cleanup"""
    
    def __init__(
        self,
        client: AsyncHaasClient,
        auth_manager: AuthenticationManager,
        preset: str = "production"
    ):
        self.client = client
        self.auth_manager = auth_manager
        self.preset = preset
        self.async_client = None

    async def __aenter__(self) -> AsyncHaasClientWrapper:
        """Enter async context"""
        self.async_client = AsyncClientFactory.create_client(
            self.client, self.auth_manager, self.preset
        )
        await self.async_client.__aenter__()
        return self.async_client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context"""
        if self.async_client:
            await self.async_client.__aexit__(exc_type, exc_val, exc_tb)


# Utility functions for common async patterns

async def with_async_client(
    client: AsyncHaasClient,
    auth_manager: AuthenticationManager,
    preset: str = "production"
):
    """Context manager for async client"""
    return AsyncClientContext(client, auth_manager, preset)


async def execute_with_async_client(
    client: AsyncHaasClient,
    auth_manager: AuthenticationManager,
    operation: callable,
    preset: str = "production",
    *args,
    **kwargs
):
    """Execute an operation with an async client"""
    async with AsyncClientContext(client, auth_manager, preset) as async_client:
        return await operation(async_client, *args, **kwargs)
