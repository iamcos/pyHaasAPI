"""
Analysis-related exceptions
"""

from .base import NonRetryableError


class AnalysisError(NonRetryableError):
    """Base class for analysis-related errors"""
    
    def __init__(self, message: str = "Analysis error occurred", **kwargs):
        super().__init__(
            message=message,
            error_code="ANALYSIS_ERROR",
            recovery_suggestion="Check your analysis parameters and data",
            **kwargs
        )


class InsufficientDataError(AnalysisError):
    """Raised when there's insufficient data for analysis"""
    
    def __init__(self, required_count: int, actual_count: int, **kwargs):
        super().__init__(
            message=f"Insufficient data for analysis: need {required_count}, have {actual_count}",
            error_code="INSUFFICIENT_DATA",
            context={"required_count": required_count, "actual_count": actual_count},
            recovery_suggestion="Collect more data or reduce analysis requirements",
            **kwargs
        )
        self.required_count = required_count
        self.actual_count = actual_count


class InvalidAnalysisParametersError(AnalysisError):
    """Raised when analysis parameters are invalid"""
    
    def __init__(self, parameter: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid analysis parameter '{parameter}': {value}",
            error_code="INVALID_ANALYSIS_PARAMETERS",
            context={"parameter": parameter, "value": str(value)},
            **kwargs
        )
        self.parameter = parameter
        self.value = value


class AnalysisTimeoutError(AnalysisError):
    """Raised when analysis takes too long"""
    
    def __init__(self, timeout_seconds: float, **kwargs):
        super().__init__(
            message=f"Analysis timed out after {timeout_seconds} seconds",
            error_code="ANALYSIS_TIMEOUT",
            context={"timeout_seconds": timeout_seconds},
            recovery_suggestion="Try with smaller dataset or increase timeout",
            **kwargs
        )
        self.timeout_seconds = timeout_seconds


class DataValidationError(AnalysisError):
    """Raised when data validation fails during analysis"""
    
    def __init__(self, validation_error: str, **kwargs):
        super().__init__(
            message=f"Data validation failed: {validation_error}",
            error_code="DATA_VALIDATION_ERROR",
            context={"validation_error": validation_error},
            recovery_suggestion="Check data quality and format",
            **kwargs
        )
        self.validation_error = validation_error
