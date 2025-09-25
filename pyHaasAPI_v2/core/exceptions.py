"""
Exception hierarchy for pyHaasAPI v2

Provides a comprehensive exception system with proper error handling
and categorization for different types of API and business logic errors.
"""

from typing import Optional, Dict, Any


class HaasAPIError(Exception):
    """Base exception for all pyHaasAPI errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(HaasAPIError):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class APIError(HaasAPIError):
    """Raised when API calls fail"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, error_code="API_ERROR", **kwargs)
        self.status_code = status_code


class ValidationError(HaasAPIError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field


class NetworkError(HaasAPIError):
    """Raised when network operations fail"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)


class ConfigurationError(HaasAPIError):
    """Raised when configuration is invalid"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class CacheError(HaasAPIError):
    """Raised when cache operations fail"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CACHE_ERROR", **kwargs)


class AnalysisError(HaasAPIError):
    """Raised when analysis operations fail"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="ANALYSIS_ERROR", **kwargs)


class BotCreationError(HaasAPIError):
    """Raised when bot creation fails"""
    
    def __init__(self, message: str, bot_id: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="BOT_CREATION_ERROR", **kwargs)
        self.bot_id = bot_id


class LabError(HaasAPIError):
    """Raised when lab operations fail"""
    
    def __init__(self, message: str, lab_id: Optional[str] = None, **kwargs):
        super().__init__(message, error_code="LAB_ERROR", **kwargs)
        self.lab_id = lab_id

