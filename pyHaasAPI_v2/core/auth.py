"""
Authentication manager for pyHaasAPI v2

Handles email/password authentication, one-time code processing,
session management, and authentication state tracking.
"""

import asyncio
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..config.api_config import APIConfig
from ..exceptions import (
    AuthenticationError, InvalidCredentialsError, SessionExpiredError, 
    OneTimeCodeError, APIError
)
from .client import AsyncHaasClient
from .logging import get_logger


@dataclass
class AuthSession:
    """Authentication session data"""
    user_id: str
    interface_key: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at
    
    @property
    def time_until_expiry(self) -> Optional[timedelta]:
        """Get time until session expires"""
        if self.expires_at is None:
            return None
        return self.expires_at - datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "user_id": self.user_id,
            "interface_key": self.interface_key,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active
        }


class AuthenticationManager:
    """
    Authentication manager for HaasOnline API
    
    Handles the complete authentication flow including email/password
    authentication and one-time code processing.
    """
    
    def __init__(self, client: AsyncHaasClient, config: APIConfig):
        self.client = client
        self.config = config
        self.logger = get_logger("auth")
        
        # Session management
        self._session: Optional[AuthSession] = None
        self._auth_lock = asyncio.Lock()
        
        # Authentication state
        self._authenticated = False
        self._last_auth_time: Optional[datetime] = None
    
    async def authenticate(
        self, 
        email: Optional[str] = None, 
        password: Optional[str] = None
    ) -> AuthSession:
        """
        Authenticate with email and password
        
        Args:
            email: Email address (uses config if not provided)
            password: Password (uses config if not provided)
            
        Returns:
            AuthSession object with authentication details
            
        Raises:
            AuthenticationError: If authentication fails
            InvalidCredentialsError: If credentials are invalid
        """
        async with self._auth_lock:
            # Use provided credentials or fall back to config
            auth_email = email or self.config.email
            auth_password = password or self.config.password
            
            if not auth_email or not auth_password:
                raise InvalidCredentialsError("Email and password must be provided")
            
            self.logger.info(f"Authenticating with email: {auth_email}")
            
            try:
                # Step 1: Initial authentication request
                auth_response = await self._initial_auth(auth_email, auth_password)
                
                # Step 2: Handle one-time code if required
                if auth_response.get("R") == 1:  # One-time code required
                    self.logger.info("One-time code required, waiting for user input...")
                    otc = await self._get_one_time_code()
                    auth_response = await self._complete_auth_with_otc(auth_email, auth_password, otc)
                
                # Step 3: Create session
                session = self._create_session(auth_response)
                
                # Step 4: Update authentication state
                self._session = session
                self._authenticated = True
                self._last_auth_time = datetime.now()
                
                self.logger.info(f"Authentication successful for user: {session.user_id}")
                return session
                
            except Exception as e:
                self.logger.error(f"Authentication failed: {e}")
                if isinstance(e, (AuthenticationError, InvalidCredentialsError)):
                    raise
                else:
                    raise AuthenticationError(f"Authentication failed: {e}")
    
    async def _initial_auth(self, email: str, password: str) -> Dict[str, Any]:
        """Perform initial authentication request"""
        import random
        interface_key = "".join(f"{random.randint(0, 100)}" for _ in range(10))
        try:
            response = await self.client.get_json(
                "/UserAPI.php",
                params={
                    "channel": "LOGIN_WITH_CREDENTIALS",
                    "email": email,
                    "password": password,
                    "interfaceKey": interface_key,
                }
            )
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "Authentication failed")
                if "invalid" in error_msg.lower() or "incorrect" in error_msg.lower():
                    raise InvalidCredentialsError(error_msg)
                else:
                    raise AuthenticationError(error_msg)
            
            return response.get("Data", {})
            
        except APIError as e:
            raise AuthenticationError(f"API error during authentication: {e}")
    
    async def _complete_auth_with_otc(
        self, 
        email: str, 
        password: str, 
        one_time_code: str
    ) -> Dict[str, Any]:
        """Complete authentication with one-time code"""
        try:
            response = await self.client.post_json(
                "/User",
                data={
                    "channel": "LOGIN_WITH_OTC",
                    "email": email,
                    "password": password,
                    "one_time_code": one_time_code
                }
            )
            
            if not response.get("Success", False):
                error_msg = response.get("Error", "One-time code authentication failed")
                raise OneTimeCodeError(error_msg)
            
            return response.get("Data", {})
            
        except APIError as e:
            raise OneTimeCodeError(f"API error during OTC authentication: {e}")
    
    async def _get_one_time_code(self) -> str:
        """
        Get one-time code from user
        
        This is a placeholder implementation. In a real application,
        this would prompt the user for input or integrate with
        a notification system.
        """
        # For now, we'll raise an error indicating OTC is required
        # In a real implementation, this would be handled by the calling code
        raise OneTimeCodeError(
            "One-time code required. Please check your email and provide the code.",
            recovery_suggestion="Use the complete_authentication method with OTC parameter"
        )
    
    def _create_session(self, auth_data: Dict[str, Any]) -> AuthSession:
        """Create authentication session from response data"""
        user_id = auth_data.get("UserId", "")
        interface_key = auth_data.get("InterfaceKey", "")
        
        if not user_id or not interface_key:
            raise AuthenticationError("Invalid authentication response: missing user data")
        
        # Create session with default 24-hour expiry
        expires_at = datetime.now() + timedelta(hours=24)
        
        return AuthSession(
            user_id=user_id,
            interface_key=interface_key,
            created_at=datetime.now(),
            expires_at=expires_at,
            is_active=True
        )
    
    async def refresh_session(self) -> AuthSession:
        """
        Refresh the current session
        
        Returns:
            New AuthSession object
            
        Raises:
            AuthenticationError: If refresh fails
            SessionExpiredError: If session is expired
        """
        if not self._session:
            raise AuthenticationError("No active session to refresh")
        
        if self._session.is_expired:
            raise SessionExpiredError("Session has expired")
        
        self.logger.info("Refreshing authentication session")
        
        try:
            # Use the refresh endpoint
            response = await self.client.post_json(
                "/User",
                data={
                    "channel": "REFRESH_SESSION",
                    "userid": self._session.user_id,
                    "interfacekey": self._session.interface_key
                }
            )
            
            if not response.get("Success", False):
                raise AuthenticationError("Session refresh failed")
            
            # Update session with new data
            auth_data = response.get("Data", {})
            new_interface_key = auth_data.get("InterfaceKey", self._session.interface_key)
            
            self._session.interface_key = new_interface_key
            self._session.expires_at = datetime.now() + timedelta(hours=24)
            self._last_auth_time = datetime.now()
            
            self.logger.info("Session refreshed successfully")
            return self._session
            
        except Exception as e:
            self.logger.error(f"Session refresh failed: {e}")
            raise AuthenticationError(f"Session refresh failed: {e}")
    
    async def validate_session(self) -> bool:
        """
        Validate the current session
        
        Returns:
            True if session is valid, False otherwise
        """
        if not self._session or not self._authenticated:
            return False
        
        if self._session.is_expired:
            self.logger.warning("Session has expired")
            return False
        
        try:
            # Test session with a simple API call
            response = await self.client.get_json(
                "/User",
                params={
                    "channel": "REFRESH_LICENSE",
                    "userid": self._session.user_id,
                    "interfacekey": self._session.interface_key
                }
            )
            
            return response.get("Success", False)
            
        except Exception as e:
            self.logger.warning(f"Session validation failed: {e}")
            return False
    
    async def logout(self) -> None:
        """Logout and clear session"""
        if self._session:
            try:
                await self.client.post_json(
                    "/User",
                    data={
                        "channel": "LOGOUT",
                        "userid": self._session.user_id,
                        "interfacekey": self._session.interface_key
                    }
                )
            except Exception as e:
                self.logger.warning(f"Logout request failed: {e}")
        
        # Clear session data
        self._session = None
        self._authenticated = False
        self._last_auth_time = None
        
        self.logger.info("Logged out successfully")
    
    async def ensure_authenticated(self) -> AuthSession:
        """
        Ensure we have a valid authenticated session
        
        Returns:
            Valid AuthSession object
            
        Raises:
            AuthenticationError: If authentication cannot be established
        """
        # Check if we have a valid session
        if self._session and self._authenticated and not self._session.is_expired:
            # Validate session is still working
            if await self.validate_session():
                return self._session
            else:
                self.logger.warning("Session validation failed, attempting refresh")
                try:
                    return await self.refresh_session()
                except Exception:
                    self.logger.warning("Session refresh failed, re-authenticating")
        
        # Need to authenticate
        if not self.config.is_authenticated:
            raise AuthenticationError("No credentials available for authentication")
        
        return await self.authenticate()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests
        
        Returns:
            Dictionary with authentication headers
        """
        if not self._session:
            return {}
        
        return {
            "X-User-ID": self._session.user_id,
            "X-Interface-Key": self._session.interface_key
        }
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        return (
            self._authenticated and 
            self._session is not None and 
            not self._session.is_expired
        )
    
    @property
    def session(self) -> Optional[AuthSession]:
        """Get current session"""
        return self._session
    
    @property
    def user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self._session.user_id if self._session else None
    
    @property
    def interface_key(self) -> Optional[str]:
        """Get current interface key"""
        return self._session.interface_key if self._session else None


# Convenience function for complete authentication with OTC
async def complete_authentication(
    client: AsyncHaasClient,
    config: APIConfig,
    email: str,
    password: str,
    one_time_code: str
) -> AuthSession:
    """
    Complete authentication with email, password, and one-time code
    
    Args:
        client: AsyncHaasClient instance
        config: APIConfig instance
        email: Email address
        password: Password
        one_time_code: One-time code from email
        
    Returns:
        AuthSession object
        
    Raises:
        AuthenticationError: If authentication fails
    """
    auth_manager = AuthenticationManager(client, config)
    
    # Set credentials in config temporarily
    original_email = config.email
    original_password = config.password
    config.email = email
    config.password = password
    
    try:
        # Perform initial authentication
        auth_response = await auth_manager._initial_auth(email, password)
        
        # Complete with OTC
        if auth_response.get("R") == 1:
            auth_response = await auth_manager._complete_auth_with_otc(email, password, one_time_code)
        
        # Create and return session
        session = auth_manager._create_session(auth_response)
        auth_manager._session = session
        auth_manager._authenticated = True
        
        return session
        
    finally:
        # Restore original config
        config.email = original_email
        config.password = original_password
