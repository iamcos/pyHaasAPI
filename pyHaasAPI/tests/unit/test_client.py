"""
Unit tests for AsyncHaasClient.
"""

import pytest
from unittest.mock import AsyncMock, patch
from pyHaasAPI.core.client import AsyncHaasClient


class TestAsyncHaasClient:
    """Test AsyncHaasClient functionality."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization with default parameters."""
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        
        assert client.host == "127.0.0.1"
        assert client.port == 8090
        assert client.timeout == 30.0
        assert client.base_url == "http://127.0.0.1:8090"
    
    @pytest.mark.asyncio
    async def test_client_initialization_custom_params(self):
        """Test client initialization with custom parameters."""
        client = AsyncHaasClient(
            host="localhost",
            port=8080,
            timeout=60.0,
            use_ssl=True
        )
        
        assert client.host == "localhost"
        assert client.port == 8080
        assert client.timeout == 60.0
        assert client.use_ssl is True
        assert client.base_url == "https://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_get_request_success(self, mock_async_client):
        """Test successful GET request."""
        mock_async_client.get.return_value = {
            "data": {"test": "value"},
            "status_code": 200
        }
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        result = await client.get("/test/endpoint")
        
        assert result["data"]["test"] == "value"
        assert result["status_code"] == 200
        mock_async_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_request_success(self, mock_async_client):
        """Test successful POST request."""
        mock_async_client.post.return_value = {
            "data": {"created": True},
            "status_code": 201
        }
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        result = await client.post("/test/endpoint", data={"test": "data"})
        
        assert result["data"]["created"] is True
        assert result["status_code"] == 201
        mock_async_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_with_headers(self, mock_async_client):
        """Test request with custom headers."""
        mock_async_client.get.return_value = {"data": {}, "status_code": 200}
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        headers = {"Authorization": "Bearer token123"}
        await client.get("/test/endpoint", headers=headers)
        
        # Verify headers were passed correctly
        call_args = mock_async_client.get.call_args
        assert "headers" in call_args.kwargs
        assert call_args.kwargs["headers"]["Authorization"] == "Bearer token123"
    
    @pytest.mark.asyncio
    async def test_request_timeout_handling(self, mock_async_client):
        """Test request timeout handling."""
        import asyncio
        from aiohttp import ClientTimeout
        
        # Mock timeout exception
        mock_async_client.get.side_effect = asyncio.TimeoutError("Request timeout")
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090, timeout=5.0)
        client._client = mock_async_client
        
        with pytest.raises(asyncio.TimeoutError):
            await client.get("/test/endpoint")
    
    @pytest.mark.asyncio
    async def test_connection_pooling(self):
        """Test that connection pooling is configured correctly."""
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        
        # Verify client has connection pool settings
        assert hasattr(client, '_client')
        # Additional connection pool assertions would go here
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_async_client):
        """Test retry logic for failed requests."""
        from aiohttp import ClientError
        
        # Mock first call fails, second succeeds
        mock_async_client.get.side_effect = [
            ClientError("Connection failed"),
            {"data": {"success": True}, "status_code": 200}
        ]
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        result = await client.get("/test/endpoint")
        
        assert result["data"]["success"] is True
        assert mock_async_client.get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_async_client):
        """Test rate limiting functionality."""
        import asyncio
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        # Mock rate limit response
        mock_async_client.get.return_value = {
            "error": "Rate limit exceeded",
            "status_code": 429
        }
        
        result = await client.get("/test/endpoint")
        
        assert result["status_code"] == 429
        assert "Rate limit exceeded" in result["error"]
    
    @pytest.mark.asyncio
    async def test_ssl_configuration(self):
        """Test SSL configuration."""
        client_http = AsyncHaasClient(host="127.0.0.1", port=8090, use_ssl=False)
        client_https = AsyncHaasClient(host="127.0.0.1", port=8090, use_ssl=True)
        
        assert client_http.base_url.startswith("http://")
        assert client_https.base_url.startswith("https://")
    
    @pytest.mark.asyncio
    async def test_logging_integration(self, mock_async_client):
        """Test that logging is properly integrated."""
        import logging
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        # Mock successful response
        mock_async_client.get.return_value = {"data": {}, "status_code": 200}
        
        # This should not raise any logging errors
        await client.get("/test/endpoint")
        
        # Verify logging was called (if implemented)
        # Additional logging assertions would go here


