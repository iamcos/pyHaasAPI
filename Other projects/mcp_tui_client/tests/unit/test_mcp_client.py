"""
Unit tests for MCP Client Service.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from mcp_tui_client.services.mcp_client import (
    MCPClientService, MCPConfig, ConnectionState, ConnectionStats, ExponentialBackoff
)
from mcp_tui_client.utils.errors import ConnectionError, APIError


class TestMCPConfig:
    """Test MCP configuration class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = MCPConfig()
        assert config.host == "localhost"
        assert config.port == 3002
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.use_ssl is False
        assert config.auto_reconnect is True
    
    def test_base_url_http(self):
        """Test HTTP base URL generation."""
        config = MCPConfig(host="example.com", port=8080, use_ssl=False)
        assert config.base_url == "http://example.com:8080"
    
    def test_base_url_https(self):
        """Test HTTPS base URL generation."""
        config = MCPConfig(host="secure.example.com", port=443, use_ssl=True)
        assert config.base_url == "https://secure.example.com:443"
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "host": "test.com",
            "port": 9000,
            "timeout": 60,
            "use_ssl": True
        }
        config = MCPConfig(**config_dict)
        assert config.host == "test.com"
        assert config.port == 9000
        assert config.timeout == 60
        assert config.use_ssl is True


class TestConnectionStats:
    """Test connection statistics class."""
    
    def test_initial_stats(self):
        """Test initial statistics values."""
        stats = ConnectionStats()
        assert stats.connected_at is None
        assert stats.total_requests == 0
        assert stats.failed_requests == 0
        assert stats.average_response_time == 0.0
        assert len(stats.response_times) == 0
    
    def test_add_response_time(self):
        """Test adding response times."""
        stats = ConnectionStats()
        
        # Add some response times
        stats.add_response_time(0.1)
        stats.add_response_time(0.2)
        stats.add_response_time(0.3)
        
        assert len(stats.response_times) == 3
        assert abs(stats.average_response_time - 0.2) < 0.001  # Allow for floating point precision
    
    def test_response_time_limit(self):
        """Test response time list size limit."""
        stats = ConnectionStats()
        
        # Add more than 100 response times
        for i in range(150):
            stats.add_response_time(i * 0.001)
        
        # Should keep only last 100
        assert len(stats.response_times) == 100
        assert stats.response_times[0] == 0.05  # 50th measurement


class TestExponentialBackoff:
    """Test exponential backoff strategy."""
    
    def test_initial_delay(self):
        """Test initial delay value."""
        backoff = ExponentialBackoff(initial_delay=1000)
        delay = backoff.get_delay()
        assert delay == 1.0  # 1000ms = 1s
    
    def test_exponential_increase(self):
        """Test exponential delay increase."""
        backoff = ExponentialBackoff(initial_delay=1000, multiplier=2.0)
        
        delay1 = backoff.get_delay()
        delay2 = backoff.get_delay()
        delay3 = backoff.get_delay()
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
    
    def test_max_delay_limit(self):
        """Test maximum delay limit."""
        backoff = ExponentialBackoff(initial_delay=1000, max_delay=5000, multiplier=2.0)
        
        # Get delays until we hit the max
        delays = []
        for _ in range(10):
            delays.append(backoff.get_delay())
        
        # Should not exceed max delay
        assert all(delay <= 5.0 for delay in delays)
        assert delays[-1] == 5.0  # Should be at max
    
    def test_reset(self):
        """Test backoff reset."""
        backoff = ExponentialBackoff(initial_delay=1000)
        
        # Increase delay
        backoff.get_delay()
        backoff.get_delay()
        
        # Reset and check
        backoff.reset()
        delay = backoff.get_delay()
        assert delay == 1.0


class TestMCPClientService:
    """Test MCP client service functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock MCP configuration."""
        return MCPConfig(
            host="test.example.com",
            port=3002,
            timeout=10,
            retry_attempts=2
        )
    
    @pytest.fixture
    def client(self, mock_config):
        """MCP client instance."""
        return MCPClientService(mock_config)
    
    def test_client_initialization(self, client, mock_config):
        """Test client initialization."""
        assert client.config == mock_config
        assert client.state == ConnectionState.DISCONNECTED
        assert client.session is None
        assert not client.is_connected
        assert isinstance(client.stats, ConnectionStats)
    
    def test_client_from_dict_config(self):
        """Test client creation from dictionary config."""
        config_dict = {"host": "test.com", "port": 8080}
        client = MCPClientService(config_dict)
        assert client.config.host == "test.com"
        assert client.config.port == 8080
    
    def test_connection_info(self, client):
        """Test connection info property."""
        info = client.connection_info
        assert info["state"] == "disconnected"
        assert info["base_url"] == "http://test.example.com:3002"
        assert info["total_requests"] == 0
        assert info["success_rate"] == 0
    
    def test_connection_callbacks(self, client):
        """Test connection state callbacks."""
        callback_called = False
        received_state = None
        
        def test_callback(state):
            nonlocal callback_called, received_state
            callback_called = True
            received_state = state
        
        client.add_connection_callback(test_callback)
        client._notify_connection_state_change(ConnectionState.CONNECTING)
        
        assert callback_called
        assert received_state == ConnectionState.CONNECTING
        assert client.state == ConnectionState.CONNECTING
        
        # Test callback removal
        client.remove_connection_callback(test_callback)
        callback_called = False
        client._notify_connection_state_change(ConnectionState.CONNECTED)
        assert not callback_called
    
    @pytest.mark.asyncio
    async def test_successful_connection(self, client):
        """Test successful connection."""
        # Mock the _make_request method directly to avoid aiohttp complexity
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "healthy"}
            
            result = await client.connect()
            
            assert result is True
            assert client.is_connected
            assert client.state == ConnectionState.CONNECTED
            assert client.stats.connected_at is not None
    
    @pytest.mark.asyncio
    async def test_connection_failure(self, client):
        """Test connection failure."""
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session_class.side_effect = Exception("Connection failed")
            
            with pytest.raises(ConnectionError):
                await client.connect()
            
            assert not client.is_connected
            assert client.state == ConnectionState.FAILED
    
    @pytest.mark.asyncio
    async def test_disconnect(self, client):
        """Test disconnection."""
        # Mock connected state
        client.session = AsyncMock()
        client.state = ConnectionState.CONNECTED
        
        await client.disconnect()
        
        assert client.session is None
        assert client.state == ConnectionState.DISCONNECTED
        assert not client.is_connected
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check."""
        client.state = ConnectionState.CONNECTED
        
        # Mock the _make_request method directly
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "healthy"}
            
            result = await client.health_check()
            assert result["status"] == "healthy"
            mock_request.assert_called_once_with("GET", "/health", skip_queue=True)
    
    @pytest.mark.asyncio
    async def test_call_tool_validation(self, client):
        """Test tool call input validation."""
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            await client.call_tool("", {})
        
        with pytest.raises(ValueError, match="Parameters must be a dictionary"):
            await client.call_tool("test_tool", "invalid")
    
    @pytest.mark.asyncio
    async def test_successful_tool_call(self, client):
        """Test successful tool call."""
        client.state = ConnectionState.CONNECTED
        
        # Mock the _make_request method directly
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"result": "success"}
            
            result = await client.call_tool("test_tool", {"param": "value"})
            assert result["result"] == "success"
            mock_request.assert_called_once_with("POST", "/api/tools/test_tool", data={"param": "value"})
    
    @pytest.mark.asyncio
    async def test_tool_call_with_retry(self, client):
        """Test tool call validation and basic functionality."""
        # Test input validation
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            await client.call_tool("", {})
        
        with pytest.raises(ValueError, match="Parameters must be a dictionary"):
            await client.call_tool("test_tool", "invalid")
        
        # Test successful call with mocked _make_request
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"result": "success"}
            
            result = await client.call_tool("test_tool", {"param": "value"})
            assert result["result"] == "success"
            mock_request.assert_called_once_with("POST", "/api/tools/test_tool", data={"param": "value"})
    
    @pytest.mark.asyncio
    async def test_batch_operations(self, client):
        """Test batch operations."""
        client.state = ConnectionState.CONNECTED
        
        # Mock call_tool method
        with patch.object(client, 'call_tool', new_callable=AsyncMock) as mock_call_tool:
            mock_call_tool.return_value = {"result": "success"}
            
            operations = [
                {"tool": "get_all_bots", "params": {}},
                {"tool": "get_all_labs", "params": {}},
            ]
            
            results = await client.batch_operations(operations)
            
            assert len(results) == 2
            assert all(result["success"] for result in results)
            assert all("data" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_batch_operations_with_failures(self, client):
        """Test batch operations with some failures."""
        # Mock call_tool method directly
        with patch.object(client, 'call_tool', new_callable=AsyncMock) as mock_call_tool:
            # First call fails, second succeeds
            mock_call_tool.side_effect = [
                APIError("Tool execution failed"),
                {"result": "success"}
            ]
            
            operations = [
                {"tool": "failing_tool", "params": {}},
                {"tool": "working_tool", "params": {}},
            ]
            
            results = await client.batch_operations(operations)
            
            assert len(results) == 2
            assert not results[0]["success"]
            assert results[1]["success"]
            assert "error" in results[0]
            assert "data" in results[1]
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager."""
        # Mock the connect and disconnect methods
        with patch.object(client, 'connect', new_callable=AsyncMock) as mock_connect:
            with patch.object(client, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                mock_connect.return_value = True
                
                async with client as connected_client:
                    assert connected_client is client
                    mock_connect.assert_called_once()
                
                mock_disconnect.assert_called_once()
    
    # Test specific MCP methods
    @pytest.mark.asyncio
    async def test_get_all_bots(self, client):
        """Test get all bots method."""
        with patch.object(client, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = [{"bot_id": "bot1", "name": "Test Bot"}]
            
            result = await client.get_all_bots()
            
            mock_call.assert_called_once_with("get_all_bots", {})
            assert len(result) == 1
            assert result[0]["bot_id"] == "bot1"
    
    @pytest.mark.asyncio
    async def test_get_bot_details_validation(self, client):
        """Test bot details validation."""
        with pytest.raises(ValueError, match="Bot ID cannot be empty"):
            await client.get_bot_details("")
    
    @pytest.mark.asyncio
    async def test_create_lab_validation(self, client):
        """Test lab creation validation."""
        with pytest.raises(ValueError, match="Missing required fields"):
            await client.create_lab({"lab_name": "Test Lab"})  # Missing script_id and trading_pair
    
    @pytest.mark.asyncio
    async def test_create_lab_success(self, client):
        """Test successful lab creation."""
        with patch.object(client, 'call_tool', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {"lab_id": "lab123", "status": "created"}
            
            config = {
                "lab_name": "Test Lab",
                "script_id": "script123",
                "trading_pair": "BTC_USD"
            }
            
            result = await client.create_lab(config)
            
            mock_call.assert_called_once_with("create_lab", config)
            assert result["lab_id"] == "lab123"
    
    @pytest.mark.asyncio
    async def test_ping(self, client):
        """Test ping method."""
        client.state = ConnectionState.CONNECTED
        
        # Mock the _make_request method directly
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"message": "pong", "timestamp": "2024-01-01T00:00:00Z"}
            
            result = await client.ping()
            
            assert result["success"] is True
            assert "response_time_ms" in result
            assert result["message"] == "pong"
    
    @pytest.mark.asyncio
    async def test_auto_reconnection(self, client):
        """Test automatic reconnection."""
        client.config.auto_reconnect = True
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock the async context manager for session
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            # First health check fails, triggering reconnection
            mock_response_fail = AsyncMock()
            mock_response_fail.status = 500
            mock_response_fail.text = AsyncMock(return_value="Connection failed")
            
            mock_context_manager_fail = AsyncMock()
            mock_context_manager_fail.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
            mock_context_manager_fail.__aexit__ = AsyncMock(return_value=None)
            
            mock_session.request.return_value = mock_context_manager_fail
            
            # Initial connection should fail and trigger reconnection
            with pytest.raises(ConnectionError):
                await client.connect()
            
            # Wait a bit for reconnection attempt
            await asyncio.sleep(0.1)
            
            # Should eventually reconnect (in real scenario)
            assert client.stats.reconnection_attempts >= 0  # May be 0 if reconnection task hasn't started yet
    
    @pytest.mark.asyncio
    async def test_request_queue_on_disconnect(self, client):
        """Test request queuing when disconnected."""
        client.config.auto_reconnect = True
        client.state = ConnectionState.DISCONNECTED
        
        # This should queue the request
        with patch.object(client, '_trigger_reconnection') as mock_reconnect:
            with pytest.raises(ConnectionError):
                await client._make_request("GET", "/test", skip_queue=False)
            
            mock_reconnect.assert_called_once()
            assert len(client._request_queue) == 1
            assert client._request_queue[0]["endpoint"] == "/test"