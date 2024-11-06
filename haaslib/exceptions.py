class HaaslibException(Exception):
    """Base exception for haaslib."""
    pass

class HaasApiError(HaaslibException):
    """Raised when API returns an error."""
    pass

class AuthenticationError(HaasApiError):
    """Raised when authentication fails."""
    pass

class ResourceNotFoundError(HaasApiError):
    """Raised when requested resource is not found."""
    pass

class ValidationError(HaaslibException):
    """Raised when input validation fails."""
    pass 