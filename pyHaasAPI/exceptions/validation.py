"""
Validation-related exceptions
"""

from .base import NonRetryableError


class ValidationError(NonRetryableError):
    """Raised when input validation fails"""
    
    def __init__(self, message: str = "Validation failed", field: str = None, **kwargs):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context={"field": field} if field else {},
            recovery_suggestion="Check your input parameters",
            **kwargs
        )
        self.field = field


class InvalidParameterError(ValidationError):
    """Raised when a parameter is invalid"""
    
    def __init__(self, parameter: str, value: any, message: str = None, **kwargs):
        message = message or f"Invalid parameter '{parameter}': {value}"
        super().__init__(
            message=message,
            field=parameter,
            error_code="INVALID_PARAMETER",
            context={"parameter": parameter, "value": str(value)},
            **kwargs
        )


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing"""
    
    def __init__(self, parameter: str, **kwargs):
        super().__init__(
            message=f"Missing required parameter: {parameter}",
            field=parameter,
            error_code="MISSING_PARAMETER",
            context={"parameter": parameter},
            **kwargs
        )


class InvalidFormatError(ValidationError):
    """Raised when data format is invalid"""
    
    def __init__(self, field: str, expected_format: str, **kwargs):
        super().__init__(
            message=f"Invalid format for '{field}': expected {expected_format}",
            field=field,
            error_code="INVALID_FORMAT",
            context={"field": field, "expected_format": expected_format},
            **kwargs
        )


class InvalidRangeError(ValidationError):
    """Raised when a value is outside valid range"""
    
    def __init__(self, field: str, value: any, min_value: any = None, max_value: any = None, **kwargs):
        range_str = []
        if min_value is not None:
            range_str.append(f"min={min_value}")
        if max_value is not None:
            range_str.append(f"max={max_value}")
        
        message = f"Value '{value}' for '{field}' is outside valid range ({', '.join(range_str)})"
        super().__init__(
            message=message,
            field=field,
            error_code="INVALID_RANGE",
            context={"field": field, "value": str(value), "min_value": str(min_value), "max_value": str(max_value)},
            **kwargs
        )
