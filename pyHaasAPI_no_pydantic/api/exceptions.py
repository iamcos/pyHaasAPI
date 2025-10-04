"""
API-specific exceptions for pyHaasAPI_no_pydantic

Provides comprehensive exception hierarchy for API operations
with clear error messages and context information.
"""

from typing import Optional, Dict, Any


class LabAPIError(Exception):
    """Base exception for lab API errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        """String representation with context"""
        parts = [self.message]
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")
        return " | ".join(parts)


class LabNotFoundError(LabAPIError):
    """Exception raised when lab is not found"""
    
    def __init__(self, lab_id: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Lab not found: {lab_id}",
            error_code="LAB_NOT_FOUND",
            context=context or {"lab_id": lab_id}
        )
        self.lab_id = lab_id


class LabExecutionError(LabAPIError):
    """Exception raised when lab execution fails"""
    
    def __init__(
        self,
        lab_id: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Lab execution failed for {lab_id}: {error_message}",
            error_code="LAB_EXECUTION_ERROR",
            context=context or {"lab_id": lab_id, "error": error_message}
        )
        self.lab_id = lab_id
        self.error_message = error_message


class LabConfigurationError(LabAPIError):
    """Exception raised when lab configuration is invalid"""
    
    def __init__(
        self,
        field_name: str,
        field_value: Any,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Lab configuration error in {field_name}: {error_message}",
            error_code="LAB_CONFIG_ERROR",
            context=context or {
                "field": field_name,
                "value": field_value,
                "error": error_message
            }
        )
        self.field_name = field_name
        self.field_value = field_value
        self.error_message = error_message


class APIConnectionError(LabAPIError):
    """Exception raised when API connection fails"""
    
    def __init__(
        self,
        endpoint: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"API connection failed for {endpoint}: {error_message}",
            error_code="API_CONNECTION_ERROR",
            context=context or {"endpoint": endpoint, "error": error_message}
        )
        self.endpoint = endpoint
        self.error_message = error_message


class APIResponseError(LabAPIError):
    """Exception raised when API response is invalid"""
    
    def __init__(
        self,
        endpoint: str,
        status_code: int,
        response_data: Any,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"API response error for {endpoint}: HTTP {status_code}",
            error_code="API_RESPONSE_ERROR",
            context=context or {
                "endpoint": endpoint,
                "status_code": status_code,
                "response": response_data
            }
        )
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_data = response_data



