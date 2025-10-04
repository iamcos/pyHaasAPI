"""
Unit tests for AuthenticationManager.
"""

import pytest
from unittest.mock import AsyncMock, patch
from pyHaasAPI.core.auth import AuthenticationManager


class TestAuthenticationManager:
    """Test AuthenticationManager functionality."""
    
    @pytest.mark.asyncio
    async def test_auth_manager_initialization(self):
        """Test authentication manager initialization."""
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        
        assert auth_manager.email == "test@example.com"
        assert auth_manager.password == "test_password"
        assert auth_manager.is_authenticated is False
        assert auth_manager.token is None
    
    @pytest.mark.asyncio
    async def test_successful_authentication(self, mock_async_client):
        """Test successful authentication flow."""
        # Mock successful authentication response
        mock_async_client.post.return_value = {
            "data": {
                "token": "mock_auth_token",
                "user_id": "user_123",
                "success": True
            },
            "status_code": 200
        }
        
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager._client = mock_async_client
        
        result = await auth_manager.authenticate()
        
        assert result is True
        assert auth_manager.is_authenticated is True
        assert auth_manager.token == "mock_auth_token"
    
    @pytest.mark.asyncio
    async def test_failed_authentication_invalid_credentials(self, mock_async_client):
        """Test authentication failure with invalid credentials."""
        # Mock authentication failure response
        mock_async_client.post.return_value = {
            "error": "Invalid credentials",
            "status_code": 401
        }
        
        auth_manager = AuthenticationManager(
            email="wrong@example.com",
            password="wrong_password"
        )
        auth_manager._client = mock_async_client
        
        result = await auth_manager.authenticate()
        
        assert result is False
        assert auth_manager.is_authenticated is False
        assert auth_manager.token is None
    
    @pytest.mark.asyncio
    async def test_authentication_with_one_time_code(self, mock_async_client):
        """Test authentication with one-time code."""
        # Mock OTC authentication response
        mock_async_client.post.return_value = {
            "data": {
                "token": "mock_otc_token",
                "success": True
            },
            "status_code": 200
        }
        
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager._client = mock_async_client
        
        result = await auth_manager.authenticate_with_otc("123456")
        
        assert result is True
        assert auth_manager.is_authenticated is True
        assert auth_manager.token == "mock_otc_token"
    
    @pytest.mark.asyncio
    async def test_token_refresh(self, mock_async_client):
        """Test token refresh functionality."""
        # Mock token refresh response
        mock_async_client.post.return_value = {
            "data": {
                "token": "new_refresh_token",
                "success": True
            },
            "status_code": 200
        }
        
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager._client = mock_async_client
        auth_manager.token = "old_token"
        auth_manager.is_authenticated = True
        
        result = await auth_manager.refresh_token()
        
        assert result is True
        assert auth_manager.token == "new_refresh_token"
    
    @pytest.mark.asyncio
    async def test_logout(self):
        """Test logout functionality."""
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager.token = "mock_token"
        auth_manager.is_authenticated = True
        
        await auth_manager.logout()
        
        assert auth_manager.token is None
        assert auth_manager.is_authenticated is False
    
    @pytest.mark.asyncio
    async def test_get_auth_headers(self):
        """Test getting authentication headers."""
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager.token = "mock_token"
        auth_manager.is_authenticated = True
        
        headers = auth_manager.get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer mock_token"
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_not_authenticated(self):
        """Test getting auth headers when not authenticated."""
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        
        headers = auth_manager.get_auth_headers()
        
        assert headers == {}
    
    @pytest.mark.asyncio
    async def test_validate_credentials(self):
        """Test credential validation."""
        # Valid credentials
        auth_manager = AuthenticationManager(
            email="valid@example.com",
            password="valid_password"
        )
        
        assert auth_manager.validate_credentials() is True
        
        # Invalid email
        auth_manager.email = "invalid_email"
        assert auth_manager.validate_credentials() is False
        
        # Empty password
        auth_manager.email = "valid@example.com"
        auth_manager.password = ""
        assert auth_manager.validate_credentials() is False
    
    @pytest.mark.asyncio
    async def test_session_management(self):
        """Test session management functionality."""
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        
        # Test session start
        auth_manager.start_session()
        assert auth_manager.session_active is True
        
        # Test session end
        auth_manager.end_session()
        assert auth_manager.session_active is False
    
    @pytest.mark.asyncio
    async def test_authentication_timeout(self, mock_async_client):
        """Test authentication timeout handling."""
        import asyncio
        
        # Mock timeout
        mock_async_client.post.side_effect = asyncio.TimeoutError("Request timeout")
        
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager._client = mock_async_client
        
        with pytest.raises(asyncio.TimeoutError):
            await auth_manager.authenticate()
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, mock_async_client):
        """Test network error handling during authentication."""
        from aiohttp import ClientError
        
        # Mock network error
        mock_async_client.post.side_effect = ClientError("Network error")
        
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager._client = mock_async_client
        
        result = await auth_manager.authenticate()
        
        assert result is False
        assert auth_manager.is_authenticated is False
    
    @pytest.mark.asyncio
    async def test_concurrent_authentication(self, mock_async_client):
        """Test concurrent authentication requests."""
        import asyncio
        
        # Mock successful authentication
        mock_async_client.post.return_value = {
            "data": {"token": "mock_token", "success": True},
            "status_code": 200
        }
        
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager._client = mock_async_client
        
        # Run multiple authentication attempts concurrently
        tasks = [auth_manager.authenticate() for _ in range(3)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(results)
        assert auth_manager.is_authenticated is True


