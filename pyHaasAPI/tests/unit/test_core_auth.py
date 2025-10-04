"""
Unit tests for AuthenticationManager core functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from pyHaasAPI.core.auth import AuthenticationManager, AuthSession
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.exceptions import AuthenticationError, InvalidCredentialsError, SessionExpiredError


class TestAuthSession:
    """Test AuthSession functionality."""
    
    def test_auth_session_creation(self):
        """Test AuthSession creation."""
        session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=datetime.now()
        )
        
        assert session.user_id == "user123"
        assert session.interface_key == "key456"
        assert session.is_active is True
        assert session.expires_at is None
    
    def test_auth_session_with_expiry(self):
        """Test AuthSession with expiry."""
        now = datetime.now()
        expires_at = now + timedelta(hours=1)
        
        session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=now,
            expires_at=expires_at
        )
        
        assert session.expires_at == expires_at
        assert not session.is_expired
        assert session.time_until_expiry == timedelta(hours=1)
    
    def test_auth_session_expired(self):
        """Test expired AuthSession."""
        now = datetime.now()
        expires_at = now - timedelta(hours=1)  # Expired 1 hour ago
        
        session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=now,
            expires_at=expires_at
        )
        
        assert session.is_expired is True
        assert session.time_until_expiry is None
    
    def test_auth_session_to_dict(self):
        """Test AuthSession to_dict conversion."""
        now = datetime.now()
        session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=now
        )
        
        data = session.to_dict()
        assert data["user_id"] == "user123"
        assert data["interface_key"] == "key456"
        assert data["is_active"] is True


class TestAuthenticationManager:
    """Test AuthenticationManager functionality."""
    
    def test_auth_manager_initialization(self):
        """Test AuthenticationManager initialization."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        assert auth_manager.email == "test@example.com"
        assert auth_manager.password == "password123"
        assert auth_manager.session is None
        assert auth_manager.is_authenticated() is False
    
    @pytest.mark.asyncio
    async def test_auth_manager_login_success(self):
        """Test successful login."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Mock successful login response
        mock_response = {
            "success": True,
            "data": {
                "userId": "user123",
                "interfaceKey": "key456"
            }
        }
        
        mock_client.post.return_value = mock_response
        
        await auth_manager.login()
        
        assert auth_manager.is_authenticated() is True
        assert auth_manager.session is not None
        assert auth_manager.session.user_id == "user123"
        assert auth_manager.session.interface_key == "key456"
    
    @pytest.mark.asyncio
    async def test_auth_manager_login_failure(self):
        """Test login failure."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="wrongpassword"
        )
        
        # Mock failed login response
        mock_response = {
            "success": False,
            "error": "Invalid credentials"
        }
        
        mock_client.post.return_value = mock_response
        
        with pytest.raises(InvalidCredentialsError):
            await auth_manager.login()
    
    @pytest.mark.asyncio
    async def test_auth_manager_login_with_one_time_code(self):
        """Test login with one-time code."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Mock OTC response
        mock_response = {
            "success": True,
            "data": {
                "userId": "user123",
                "interfaceKey": "key456",
                "requiresOTC": True
            }
        }
        
        mock_client.post.return_value = mock_response
        
        # Mock OTC completion
        mock_otc_response = {
            "success": True,
            "data": {
                "userId": "user123",
                "interfaceKey": "key456"
            }
        }
        
        mock_client.post.side_effect = [mock_response, mock_otc_response]
        
        await auth_manager.login_with_one_time_code("123456")
        
        assert auth_manager.is_authenticated() is True
        assert auth_manager.session is not None
    
    @pytest.mark.asyncio
    async def test_auth_manager_logout(self):
        """Test logout functionality."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Set up authenticated session
        auth_manager.session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=datetime.now()
        )
        
        await auth_manager.logout()
        
        assert auth_manager.session is None
        assert auth_manager.is_authenticated() is False
    
    @pytest.mark.asyncio
    async def test_auth_manager_refresh_session(self):
        """Test session refresh."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Set up expired session
        auth_manager.session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=datetime.now(),
            expires_at=datetime.now() - timedelta(hours=1)  # Expired
        )
        
        # Mock refresh response
        mock_response = {
            "success": True,
            "data": {
                "userId": "user123",
                "interfaceKey": "newkey789"
            }
        }
        
        mock_client.post.return_value = mock_response
        
        await auth_manager.refresh_session()
        
        assert auth_manager.is_authenticated() is True
        assert auth_manager.session.interface_key == "newkey789"
    
    @pytest.mark.asyncio
    async def test_auth_manager_get_headers(self):
        """Test getting authentication headers."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Set up authenticated session
        auth_manager.session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=datetime.now()
        )
        
        headers = await auth_manager.get_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer key456"
    
    @pytest.mark.asyncio
    async def test_auth_manager_get_headers_not_authenticated(self):
        """Test getting headers when not authenticated."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        with pytest.raises(AuthenticationError):
            await auth_manager.get_headers()
    
    @pytest.mark.asyncio
    async def test_auth_manager_validate_session(self):
        """Test session validation."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Test with no session
        assert not auth_manager.validate_session()
        
        # Test with valid session
        auth_manager.session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=datetime.now()
        )
        assert auth_manager.validate_session()
        
        # Test with expired session
        auth_manager.session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=datetime.now(),
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert not auth_manager.validate_session()
    
    @pytest.mark.asyncio
    async def test_auth_manager_auto_refresh(self):
        """Test automatic session refresh."""
        mock_client = AsyncMock(spec=AsyncHaasClient)
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Set up session that will expire soon
        auth_manager.session = AuthSession(
            user_id="user123",
            interface_key="key456",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=5)  # Expires in 5 minutes
        )
        
        # Mock refresh response
        mock_response = {
            "success": True,
            "data": {
                "userId": "user123",
                "interfaceKey": "newkey789"
            }
        }
        
        mock_client.post.return_value = mock_response
        
        # Should auto-refresh when getting headers
        headers = await auth_manager.get_headers()
        
        assert headers["Authorization"] == "Bearer newkey789"
        mock_client.post.assert_called()

