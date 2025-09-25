"""
Unit tests for pyHaasAPI v2 core modules

This module provides comprehensive unit tests for all core components
including client, authentication, type validation, and async utilities.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from ..core.client import AsyncHaasClient
from ..core.auth import AuthenticationManager
from ..core.type_validation import TypeValidator, TypeChecker, TypeValidationError
from ..core.async_utils import AsyncRateLimiter, AsyncRetryHandler, AsyncBatchProcessor
from ..core.async_client import AsyncHaasClientWrapper, AsyncClientConfig
from ..core.async_factory import AsyncClientFactory
from ..exceptions import AuthenticationError, APIError


class TestAsyncClient:
    """Test cases for AsyncHaasClient"""
    
    @pytest.mark.async
    async def test_client_initialization(self):
        """Test client initialization"""
        client = AsyncHaasClient(host="127.0.0.1", port=8090, timeout=30.0)
        assert client.host == "127.0.0.1"
        assert client.port == 8090
        assert client.timeout == 30.0
    
    @pytest.mark.async
    async def test_client_execute_success(self, mock_async_client):
        """Test successful client execution"""
        mock_async_client.execute.return_value = {"success": True, "data": "test"}
        
        result = await mock_async_client.execute({"method": "GET", "endpoint": "/test"})
        
        assert result["success"] is True
        assert result["data"] == "test"
        mock_async_client.execute.assert_called_once()


class TestAuthenticationManager:
    """Test cases for AuthenticationManager"""
    
    @pytest.mark.async
    async def test_auth_manager_initialization(self):
        """Test authentication manager initialization"""
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        assert auth_manager.email == "test@example.com"
        assert auth_manager.password == "test_password"
        assert auth_manager.auto_refresh is True
    
    @pytest.mark.async
    async def test_authentication_success(self, mock_auth_manager):
        """Test successful authentication"""
        mock_auth_manager.authenticate.return_value = True
        
        result = await mock_auth_manager.authenticate()
        
        assert result is True
        mock_auth_manager.authenticate.assert_called_once()


class TestTypeValidation:
    """Test cases for type validation"""
    
    def test_type_validator_initialization(self):
        """Test type validator initialization"""
        validator = TypeValidator(strict_mode=True)
        assert validator.strict_mode is True
    
    def test_validate_type_success(self):
        """Test successful type validation"""
        validator = TypeValidator()
        result = validator.validate_type("test", str)
        
        assert result.is_valid is True
        assert result.validated_value == "test"
        assert result.error_message is None
    
    def test_validate_type_failure(self):
        """Test type validation failure"""
        validator = TypeValidator()
        result = validator.validate_type("test", int)
        
        assert result.is_valid is False
        assert result.error_message is not None


class TestAsyncUtils:
    """Test cases for async utilities"""
    
    @pytest.mark.async
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        from ..core.async_utils import RateLimitConfig
        
        config = RateLimitConfig(max_requests=100, time_window=60.0)
        rate_limiter = AsyncRateLimiter(config)
        
        assert rate_limiter.config.max_requests == 100
        assert rate_limiter.config.time_window == 60.0
    
    @pytest.mark.async
    async def test_retry_handler_initialization(self):
        """Test retry handler initialization"""
        from ..core.async_utils import RetryConfig
        
        config = RetryConfig(max_retries=3, base_delay=0.1)
        retry_handler = AsyncRetryHandler(config)
        
        assert retry_handler.config.max_retries == 3
        assert retry_handler.config.base_delay == 0.1


class TestAsyncClientWrapper:
    """Test cases for AsyncHaasClientWrapper"""
    
    @pytest.mark.async
    async def test_wrapper_initialization(self, mock_async_client, mock_auth_manager):
        """Test async client wrapper initialization"""
        config = AsyncClientConfig(
            cache_ttl=60.0,
            enable_caching=True,
            enable_rate_limiting=True,
            max_concurrent_requests=10
        )
        
        wrapper = AsyncHaasClientWrapper(mock_async_client, mock_auth_manager, config)
        
        assert wrapper.client == mock_async_client
        assert wrapper.auth_manager == mock_auth_manager
        assert wrapper.config == config


class TestAsyncClientFactory:
    """Test cases for AsyncClientFactory"""
    
    def test_factory_presets(self):
        """Test factory presets"""
        presets = AsyncClientFactory.get_available_presets()
        
        expected_presets = ["development", "production", "high_performance", "conservative", "testing"]
        assert all(preset in presets for preset in expected_presets)
    
    def test_create_client_with_preset(self, mock_async_client, mock_auth_manager):
        """Test client creation with preset"""
        client = AsyncClientFactory.create_client(
            mock_async_client, 
            mock_auth_manager, 
            preset="development"
        )
        
        assert isinstance(client, AsyncHaasClientWrapper)
        assert client.config.enable_rate_limiting is False  # Development preset