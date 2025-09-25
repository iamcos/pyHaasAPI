"""
API-related exceptions
"""

from .base import RetryableError, NonRetryableError


class APIError(RetryableError):
    """Base class for API-related errors"""
    
    def __init__(self, message: str, status_code: int = None, **kwargs):
        super().__init__(
            message=message,
            error_code="API_ERROR",
            context={"status_code": status_code} if status_code else {},
            **kwargs
        )
        self.status_code = status_code


class APIRequestError(APIError):
    """Raised when API request fails"""
    
    def __init__(self, message: str = "API request failed", **kwargs):
        super().__init__(
            message=message,
            error_code="API_REQUEST_ERROR",
            recovery_suggestion="Check your request parameters and try again",
            **kwargs
        )


class APIResponseError(APIError):
    """Raised when API response is invalid"""
    
    def __init__(self, message: str = "Invalid API response", **kwargs):
        super().__init__(
            message=message,
            error_code="API_RESPONSE_ERROR",
            recovery_suggestion="Check API status and try again",
            **kwargs
        )


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    
    def __init__(self, message: str = "API rate limit exceeded", retry_after: int = None, **kwargs):
        super().__init__(
            message=message,
            error_code="API_RATE_LIMIT",
            context={"retry_after": retry_after} if retry_after else {},
            recovery_suggestion=f"Wait {retry_after} seconds before retrying" if retry_after else "Wait before retrying",
            **kwargs
        )
        self.retry_after = retry_after


class APITimeoutError(APIError):
    """Raised when API request times out"""
    
    def __init__(self, message: str = "API request timed out", **kwargs):
        super().__init__(
            message=message,
            error_code="API_TIMEOUT",
            recovery_suggestion="Check your connection and try again",
            **kwargs
        )


class APIServerError(APIError):
    """Raised when API server returns 5xx error"""
    
    def __init__(self, message: str = "API server error", **kwargs):
        super().__init__(
            message=message,
            error_code="API_SERVER_ERROR",
            recovery_suggestion="Server is temporarily unavailable, try again later",
            **kwargs
        )


class APIClientError(NonRetryableError):
    """Raised when API client error occurs (4xx)"""
    
    def __init__(self, message: str = "API client error", **kwargs):
        super().__init__(
            message=message,
            error_code="API_CLIENT_ERROR",
            recovery_suggestion="Check your request parameters",
            **kwargs
        )
