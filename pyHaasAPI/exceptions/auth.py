"""
Authentication-related exceptions
"""

from .base import NonRetryableError


class AuthenticationError(NonRetryableError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        # Remove error_code and recovery_suggestion from kwargs if they exist to avoid duplicates
        kwargs.pop('error_code', None)
        kwargs.pop('recovery_suggestion', None)
        super().__init__(
            message=message,
            error_code="AUTH_FAILED",
            recovery_suggestion="Check your credentials and try again",
            **kwargs
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid"""
    
    def __init__(self, message: str = "Invalid credentials provided", **kwargs):
        # Remove error_code and recovery_suggestion from kwargs if they exist to avoid duplicates
        kwargs.pop('error_code', None)
        kwargs.pop('recovery_suggestion', None)
        super().__init__(
            message=message,
            error_code="INVALID_CREDENTIALS",
            recovery_suggestion="Verify your email and password are correct",
            **kwargs
        )


class SessionExpiredError(AuthenticationError):
    """Raised when session has expired"""
    
    def __init__(self, message: str = "Session has expired", **kwargs):
        super().__init__(
            message=message,
            error_code="SESSION_EXPIRED",
            recovery_suggestion="Re-authenticate to continue",
            **kwargs
        )


class OneTimeCodeError(AuthenticationError):
    """Raised when one-time code authentication fails"""
    
    def __init__(self, message: str = "One-time code authentication failed", **kwargs):
        # Remove error_code and recovery_suggestion from kwargs if they exist to avoid duplicates
        kwargs.pop('error_code', None)
        kwargs.pop('recovery_suggestion', None)
        super().__init__(
            message=message,
            error_code="OTC_FAILED",
            recovery_suggestion="Check your one-time code and try again",
            **kwargs
        )
