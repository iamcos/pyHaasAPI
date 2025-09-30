"""
Testing-related exceptions
"""

from .base import NonRetryableError


class TestingError(NonRetryableError):
    """Base class for testing-related errors"""
    
    def __init__(self, message: str = "Testing operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="TESTING_ERROR",
            recovery_suggestion="Check testing configuration and try again",
            **kwargs
        )


class TestingConfigurationError(TestingError):
    """Raised when testing configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid testing configuration '{config_field}': {value}",
            error_code="TESTING_CONFIG_ERROR",
            context={"config_field": config_field, "value": str(value)},
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class TestingExecutionError(TestingError):
    """Raised when test execution fails"""
    
    def __init__(self, test_id: str, **kwargs):
        super().__init__(
            message=f"Test execution failed: {test_id}",
            error_code="TESTING_EXECUTION_ERROR",
            context={"test_id": test_id},
            recovery_suggestion="Check test parameters and try again",
            **kwargs
        )
        self.test_id = test_id


class TestingValidationError(TestingError):
    """Raised when test validation fails"""
    
    def __init__(self, test_id: str, validation_error: str, **kwargs):
        super().__init__(
            message=f"Test validation failed: {test_id} - {validation_error}",
            error_code="TESTING_VALIDATION_ERROR",
            context={"test_id": test_id, "validation_error": validation_error},
            recovery_suggestion="Fix test parameters and try again",
            **kwargs
        )
        self.test_id = test_id
        self.validation_error = validation_error



