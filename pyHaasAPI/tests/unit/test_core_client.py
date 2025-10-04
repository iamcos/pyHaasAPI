"""
Unit tests for AsyncHaasClient core functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientTimeout
from pyHaasAPI.core.client import AsyncHaasClient, RateLimiter, RetryHandler
from pyHaasAPI.exceptions import NetworkError, ConnectionError, TimeoutError, APIError


class TestRateLimiter:
    """Test RateLimiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(max_requests=10, time_window=60)
        assert limiter.max_requests == 10
        assert limiter.time_window == 60
        assert len(limiter.requests) == 0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_within_limit(self):
        """Test acquiring within rate limit."""
        limiter = RateLimiter(max_requests=5, time_window=60)
        
        # Should be able to acquire 5 requests
        for _ in range(5):
            await limiter.acquire()
        
        assert len(limiter.requests) == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire_exceeds_limit(self):
        """Test acquiring when rate limit is exceeded."""
        limiter = RateLimiter(max_requests=2, time_window=1)  # 1 second window
        
        # Acquire first two requests
        await limiter.acquire()
        await limiter.acquire()
        
        # Third request should be blocked
        with pytest.raises(AssertionError):  # This will raise if not properly handled
            await limiter.acquire()


class TestRetryHandler:
    """Test RetryHandler functionality."""
    
    def test_retry_handler_initialization(self):
        """Test RetryHandler initialization."""
        handler = RetryHandler(max_retries=3, base_delay=1.0, max_delay=10.0)
        assert handler.max_retries == 3
        assert handler.base_delay == 1.0
        assert handler.max_delay == 10.0
    
    def test_retry_handler_calculate_delay(self):
        """Test delay calculation."""
        handler = RetryHandler(max_retries=3, base_delay=1.0, max_delay=10.0)
        
        # Test exponential backoff
        delay1 = handler._calculate_delay(0)
        delay2 = handler._calculate_delay(1)
        delay3 = handler._calculate_delay(2)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
    
    def test_retry_handler_calculate_delay_with_max(self):
        """Test delay calculation with max delay."""
        handler = RetryHandler(max_retries=3, base_delay=1.0, max_delay=2.0)
        
        delay = handler._calculate_delay(5)  # Should be capped at max_delay
        assert delay == 2.0


class TestAsyncHaasClient:
    """Test AsyncHaasClient functionality."""
    
    def test_client_initialization(self):
        """Test AsyncHaasClient initialization."""
        client = AsyncHaasClient(
            base_url="http://localhost:8090",
            timeout=30.0,
            max_retries=3
        )
        
        assert client.base_url == "http://localhost:8090"
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.rate_limiter is not None
        assert client.retry_handler is not None
    
    def test_client_initialization_with_defaults(self):
        """Test AsyncHaasClient initialization with defaults."""
        client = AsyncHaasClient()
        
        assert client.base_url == "http://localhost:8090"
        assert client.timeout == 30.0
        assert client.max_retries == 3
    
    @pytest.mark.asyncio
    async def test_client_get_request_success(self):
        """Test successful GET request."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.headers = {"Content-Type": "application/json"}
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch.object(client, '_get_session', return_value=mock_session):
            response = await client.get("/test")
            
            assert response == {"data": "test"}
            mock_session.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_post_request_success(self):
        """Test successful POST request."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"success": True})
        mock_response.headers = {"Content-Type": "application/json"}
        
        mock_session = AsyncMock()
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        with patch.object(client, '_get_session', return_value=mock_session):
            response = await client.post("/test", data={"key": "value"})
            
            assert response == {"success": True}
            mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_put_request_success(self):
        """Test successful PUT request."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"updated": True})
        mock_response.headers = {"Content-Type": "application/json"}
        
        mock_session = AsyncMock()
        mock_session.put.return_value.__aenter__.return_value = mock_response
        
        with patch.object(client, '_get_session', return_value=mock_session):
            response = await client.put("/test", data={"key": "value"})
            
            assert response == {"updated": True}
            mock_session.put.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_delete_request_success(self):
        """Test successful DELETE request."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"deleted": True})
        mock_response.headers = {"Content-Type": "application/json"}
        
        mock_session = AsyncMock()
        mock_session.delete.return_value.__aenter__.return_value = mock_response
        
        with patch.object(client, '_get_session', return_value=mock_session):
            response = await client.delete("/test")
            
            assert response == {"deleted": True}
            mock_session.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_request_with_headers(self):
        """Test request with custom headers."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        client.headers = {"Authorization": "Bearer token123"}
        
        # Mock the session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})
        mock_response.headers = {"Content-Type": "application/json"}
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch.object(client, '_get_session', return_value=mock_session):
            await client.get("/test")
            
            # Verify headers were passed
            call_args = mock_session.get.call_args
            assert "headers" in call_args.kwargs
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer token123"
    
    @pytest.mark.asyncio
    async def test_client_request_timeout(self):
        """Test request timeout handling."""
        client = AsyncHaasClient(base_url="http://localhost:8090", timeout=1.0)
        
        # Mock session that raises timeout
        mock_session = AsyncMock()
        mock_session.get.side_effect = asyncio.TimeoutError()
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(TimeoutError):
                await client.get("/test")
    
    @pytest.mark.asyncio
    async def test_client_request_connection_error(self):
        """Test connection error handling."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        
        # Mock session that raises connection error
        mock_session = AsyncMock()
        mock_session.get.side_effect = ConnectionError("Connection failed")
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(ConnectionError):
                await client.get("/test")
    
    @pytest.mark.asyncio
    async def test_client_request_http_error(self):
        """Test HTTP error handling."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        
        # Mock response with error status
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(return_value={"error": "Bad Request"})
        mock_response.headers = {"Content-Type": "application/json"}
        
        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch.object(client, '_get_session', return_value=mock_session):
            with pytest.raises(APIError):
                await client.get("/test")
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test AsyncHaasClient as context manager."""
        async with AsyncHaasClient(base_url="http://localhost:8090") as client:
            assert client is not None
            assert isinstance(client, AsyncHaasClient)
    
    @pytest.mark.asyncio
    async def test_client_session_management(self):
        """Test session management."""
        client = AsyncHaasClient(base_url="http://localhost:8090")
        
        # Test session creation
        session = await client._get_session()
        assert session is not None
        
        # Test session reuse
        session2 = await client._get_session()
        assert session is session2  # Should be the same session
        
        # Test session cleanup
        await client.close()
        # After close, should create new session
        session3 = await client._get_session()
        assert session3 is not session

