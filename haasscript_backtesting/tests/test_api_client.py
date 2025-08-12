"""
Tests for HaasOnline API client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from haasscript_backtesting.config.haasonline_config import HaasOnlineConfig
from haasscript_backtesting.api_client.haasonline_client import (
    HaasOnlineClient,
    HaasOnlineAPIError,
    AuthenticationError,
    RateLimiter
)
from haasscript_backtesting.api_client.request_models import (
    ScriptRecordRequest,
    DebugTestRequest,
    QuickTestRequest,
    BacktestRequest
)
from haasscript_backtesting.api_client.response_models import (
    ScriptRecordResponse,
    DebugTestResponse,
    QuickTestResponse,
    BacktestResponse,
    ExecutionStatus
)


@pytest.fixture
def mock_config():
    """Create mock HaasOnline configuration."""
    return HaasOnlineConfig(
        server_url="http://localhost:9000",
        api_key="test_key",
        api_secret="test_secret",
        username="test@example.com",
        password="test_password"
    )


@pytest.fixture
def mock_client(mock_config):
    """Create mock HaasOnline client."""
    return HaasOnlineClient(mock_config)


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter(requests_per_second=2, burst_limit=5)
        
        # Should allow initial requests up to burst limit
        for _ in range(5):
            await limiter.acquire()
        
        # Next request should be delayed
        import time
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time
        
        # Should have waited at least some time
        assert elapsed > 0


class TestHaasOnlineClient:
    """Test HaasOnline API client."""
    
    def test_client_initialization(self, mock_config):
        """Test client initialization."""
        client = HaasOnlineClient(mock_config)
        
        assert client.config == mock_config
        assert not client._authenticated
        assert client._auth_token is None
        assert client._user_id is None
        assert client._interface_key is None
    
    def test_context_manager(self, mock_client):
        """Test context manager functionality."""
        with patch.object(mock_client, '_setup_session') as mock_setup:
            with patch.object(mock_client, 'close') as mock_close:
                with mock_client as client:
                    assert client == mock_client
                    mock_setup.assert_called_once()
                mock_close.assert_called_once()
    
    @patch('requests.Session')
    def test_setup_session(self, mock_session_class, mock_client):
        """Test HTTP session setup."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_client._setup_session()
        
        assert mock_client.session == mock_session
        mock_session.mount.assert_called()
        assert mock_session.headers.update.called
    
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request, mock_client):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Success": True, "Data": {"test": "value"}}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        mock_client._setup_session()
        result = mock_client._make_request("GET", "http://test.com")
        
        assert result["Success"] is True
        assert result["Data"]["test"] == "value"
    
    @patch('requests.Session.request')
    def test_make_request_api_error(self, mock_request, mock_client):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Success": False, "Error": "Test error"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        mock_client._setup_session()
        
        with pytest.raises(HaasOnlineAPIError) as exc_info:
            mock_client._make_request("GET", "http://test.com")
        
        assert "Test error" in str(exc_info.value)
    
    @patch('requests.Session.request')
    def test_make_request_http_error(self, mock_request, mock_client):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP error")
        mock_request.return_value = mock_response
        
        mock_client._setup_session()
        
        with pytest.raises(HaasOnlineAPIError) as exc_info:
            mock_client._make_request("GET", "http://test.com")
        
        assert "Request failed" in str(exc_info.value)
    
    def test_generate_interface_key(self, mock_client):
        """Test interface key generation."""
        key = mock_client._generate_interface_key()
        
        assert len(key) == 10
        assert key.isdigit()
    
    @patch.object(HaasOnlineClient, '_make_request')
    def test_authenticate_with_api_key(self, mock_request, mock_client):
        """Test API key authentication."""
        mock_request.return_value = {
            "Success": True,
            "Data": {"UserId": "test_user_id"}
        }
        
        result = mock_client._authenticate_with_api_key()
        
        assert result is True
        assert mock_client._authenticated is True
        assert mock_client._user_id == "test_user_id"
        assert mock_client._interface_key is not None
    
    @patch.object(HaasOnlineClient, '_make_request')
    def test_authenticate_with_api_key_failure(self, mock_request, mock_client):
        """Test API key authentication failure."""
        mock_request.return_value = {
            "Success": False,
            "Error": "Invalid API key"
        }
        
        with pytest.raises(AuthenticationError) as exc_info:
            mock_client._authenticate_with_api_key()
        
        assert "Invalid API key" in str(exc_info.value)
        assert mock_client._authenticated is False
    
    @patch.object(HaasOnlineClient, '_make_request')
    def test_test_connection(self, mock_request, mock_client):
        """Test connection testing."""
        mock_request.return_value = {"Success": True}
        
        result = mock_client.test_connection()
        
        assert result is True
        mock_request.assert_called_once()
    
    @patch.object(HaasOnlineClient, '_make_request')
    def test_get_server_info(self, mock_request, mock_client):
        """Test server info retrieval."""
        expected_data = {"version": "1.0", "features": ["backtest"]}
        mock_request.return_value = {"Data": expected_data}
        
        result = mock_client.get_server_info()
        
        assert result == expected_data
    
    @patch.object(HaasOnlineClient, '_ensure_authenticated')
    @patch.object(HaasOnlineClient, '_make_request')
    def test_get_script_record(self, mock_request, mock_auth, mock_client):
        """Test script record retrieval."""
        request = ScriptRecordRequest(script_id="test_script")
        
        mock_request.return_value = {
            "Data": {
                "ScriptId": "test_script",
                "Name": "Test Script",
                "Content": "// test content",
                "ScriptType": 1,
                "Parameters": {"param1": "value1"},
                "CreatedAt": "2023-01-01T00:00:00",
                "ModifiedAt": "2023-01-01T00:00:00",
                "CompileLogs": ["log1", "log2"],
                "IsValid": True
            }
        }
        
        result = mock_client.get_script_record(request)
        
        assert isinstance(result, ScriptRecordResponse)
        assert result.script_id == "test_script"
        assert result.name == "Test Script"
        assert result.is_valid is True
        mock_auth.assert_called_once()
    
    @patch.object(HaasOnlineClient, '_ensure_authenticated')
    @patch.object(HaasOnlineClient, '_make_request')
    def test_execute_debug_test(self, mock_request, mock_auth, mock_client):
        """Test debug test execution."""
        request = DebugTestRequest(
            script_id="test_script",
            script_content="// test",
            parameters={"param1": "value1"}
        )
        
        mock_request.return_value = {
            "Success": True,
            "Data": {
                "CompilationLogs": ["Compilation successful"],
                "Errors": [],
                "Warnings": ["Warning: unused variable"],
                "ExecutionTimeMs": 100,
                "MemoryUsageMb": 5.0,
                "IsValid": True
            }
        }
        
        result = mock_client.execute_debug_test(request)
        
        assert isinstance(result, DebugTestResponse)
        assert result.success is True
        assert result.is_valid is True
        assert len(result.warnings) == 1
        assert result.execution_time_ms == 100
        mock_auth.assert_called_once()
    
    @patch.object(HaasOnlineClient, '_ensure_authenticated')
    @patch.object(HaasOnlineClient, '_make_request')
    def test_execute_quick_test(self, mock_request, mock_auth, mock_client):
        """Test quick test execution."""
        request = QuickTestRequest(
            script_id="test_script",
            account_id="test_account",
            market_tag="BINANCE_BTC_USDT",
            interval=60
        )
        
        mock_request.return_value = {
            "Success": True,
            "Data": {
                "ExecutionId": "exec_123",
                "Trades": [
                    {
                        "Timestamp": "2023-01-01T00:00:00",
                        "Action": "ACTION_A",
                        "Price": 50000.0,
                        "Amount": 0.001,
                        "Fee": 0.05,
                        "ProfitLoss": 0.0,
                        "BalanceAfter": 999.95
                    }
                ],
                "FinalBalance": 1050.0,
                "TotalProfitLoss": 50.0,
                "ExecutionLogs": ["Trade executed"],
                "RuntimeData": {"indicator1": 0.5},
                "ExecutionTimeMs": 5000
            }
        }
        
        result = mock_client.execute_quick_test(request)
        
        assert isinstance(result, QuickTestResponse)
        assert result.success is True
        assert result.execution_id == "exec_123"
        assert len(result.trades) == 1
        assert result.final_balance == 1050.0
        mock_auth.assert_called_once()
    
    @patch.object(HaasOnlineClient, '_ensure_authenticated')
    @patch.object(HaasOnlineClient, '_make_request')
    def test_execute_backtest(self, mock_request, mock_auth, mock_client):
        """Test backtest execution."""
        request = BacktestRequest(
            script_id="test_script",
            account_id="test_account",
            market_tag="BINANCE_BTC_USDT",
            start_time=1640995200,  # 2022-01-01
            end_time=1672531200,    # 2023-01-01
            interval=60,
            trade_amount=1000.0
        )
        
        mock_request.return_value = {
            "Success": True,
            "Data": {
                "BacktestId": "bt_123",
                "ExecutionId": "exec_456",
                "Status": "queued",
                "EstimatedCompletion": "2023-01-01T01:00:00"
            }
        }
        
        result = mock_client.execute_backtest(request)
        
        assert isinstance(result, BacktestResponse)
        assert result.success is True
        assert result.backtest_id == "bt_123"
        assert result.execution_id == "exec_456"
        assert result.status == ExecutionStatus.QUEUED
        mock_auth.assert_called_once()
    
    def test_ensure_authenticated_not_authenticated(self, mock_client):
        """Test ensure authenticated when not authenticated."""
        with patch.object(mock_client, 'authenticate') as mock_auth:
            mock_client._ensure_authenticated()
            mock_auth.assert_called_once()
    
    def test_ensure_authenticated_already_authenticated(self, mock_client):
        """Test ensure authenticated when already authenticated."""
        mock_client._authenticated = True
        
        with patch.object(mock_client, 'authenticate') as mock_auth:
            mock_client._ensure_authenticated()
            mock_auth.assert_not_called()


class TestAsyncMethods:
    """Test asynchronous methods."""
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_client):
        """Test async context manager."""
        with patch.object(mock_client, '_setup_async_session') as mock_setup:
            with patch.object(mock_client, 'aclose') as mock_close:
                async with mock_client as client:
                    assert client == mock_client
                    mock_setup.assert_called_once()
                mock_close.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession')
    async def test_setup_async_session(self, mock_session_class, mock_client):
        """Test async session setup."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        await mock_client._setup_async_session()
        
        assert mock_client.async_session == mock_session
        mock_session_class.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_integration(self, mock_client):
        """Test rate limiter integration with async requests."""
        # This would require more complex mocking of aiohttp
        # For now, just test that the rate limiter is created
        assert mock_client.rate_limiter is not None
        assert mock_client.rate_limiter.requests_per_second == mock_client.config.rate_limit.requests_per_second


if __name__ == "__main__":
    pytest.main([__file__])