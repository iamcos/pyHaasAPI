"""
Network-related exceptions
"""

from .base import RetryableError


class NetworkError(RetryableError):
    """Base class for network-related errors"""
    
    def __init__(self, message: str = "Network error occurred", **kwargs):
        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            recovery_suggestion="Check your network connection and try again",
            **kwargs
        )


class ConnectionError(NetworkError):
    """Raised when connection fails"""
    
    def __init__(self, message: str = "Connection failed", **kwargs):
        super().__init__(
            message=message,
            error_code="CONNECTION_ERROR",
            recovery_suggestion="Check your internet connection and API endpoint",
            **kwargs
        )


class TimeoutError(NetworkError):
    """Raised when network operation times out"""
    
    def __init__(self, message: str = "Network operation timed out", timeout: float = None, **kwargs):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            context={"timeout": timeout} if timeout else {},
            recovery_suggestion="Try again with a longer timeout",
            **kwargs
        )
        self.timeout = timeout


class DNSResolutionError(NetworkError):
    """Raised when DNS resolution fails"""
    
    def __init__(self, hostname: str, **kwargs):
        super().__init__(
            message=f"Failed to resolve hostname: {hostname}",
            error_code="DNS_RESOLUTION_ERROR",
            context={"hostname": hostname},
            recovery_suggestion="Check your DNS settings and hostname",
            **kwargs
        )
        self.hostname = hostname


class SSLVerificationError(NetworkError):
    """Raised when SSL verification fails"""
    
    def __init__(self, message: str = "SSL verification failed", **kwargs):
        super().__init__(
            message=message,
            error_code="SSL_VERIFICATION_ERROR",
            recovery_suggestion="Check SSL certificate or disable SSL verification",
            **kwargs
        )
