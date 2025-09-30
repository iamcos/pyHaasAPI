"""
Server-related exceptions for pyHaasAPI v2
"""

from .base import HaasAPIError


class ServerError(HaasAPIError):
    """Base exception for server-related errors"""
    pass


class ServerConnectionError(ServerError):
    """Server connection failed"""
    pass


class ServerAuthenticationError(ServerError):
    """Server authentication failed"""
    pass


class ServerTimeoutError(ServerError):
    """Server request timeout"""
    pass


class ServerUnavailableError(ServerError):
    """Server is unavailable"""
    pass


class ServerConfigurationError(ServerError):
    """Server configuration error"""
    pass
