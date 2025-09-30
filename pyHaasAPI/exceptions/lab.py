"""
Lab-related exceptions
"""

from .base import NonRetryableError


class LabError(NonRetryableError):
    """Base class for lab-related errors"""
    
    def __init__(self, message: str = "Lab operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="LAB_ERROR",
            recovery_suggestion="Check lab configuration and try again",
            **kwargs
        )


class LabNotFoundError(LabError):
    """Raised when lab is not found"""
    
    def __init__(self, lab_id: str, **kwargs):
        super().__init__(
            message=f"Lab not found: {lab_id}",
            error_code="LAB_NOT_FOUND",
            context={"lab_id": lab_id},
            recovery_suggestion="Check lab ID and try again",
            **kwargs
        )
        self.lab_id = lab_id


class LabExecutionError(LabError):
    """Raised when lab execution fails"""
    
    def __init__(self, lab_id: str, **kwargs):
        super().__init__(
            message=f"Lab execution failed: {lab_id}",
            error_code="LAB_EXECUTION_ERROR",
            context={"lab_id": lab_id},
            recovery_suggestion="Check lab configuration and script",
            **kwargs
        )
        self.lab_id = lab_id


class LabConfigurationError(LabError):
    """Raised when lab configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid lab configuration '{config_field}': {value}",
            error_code="LAB_CONFIG_ERROR",
            context={"config_field": config_field, "value": str(value)},
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class LabScriptError(LabError):
    """Raised when lab script is invalid"""
    
    def __init__(self, script_id: str, **kwargs):
        super().__init__(
            message=f"Invalid lab script: {script_id}",
            error_code="LAB_SCRIPT_ERROR",
            context={"script_id": script_id},
            recovery_suggestion="Check script ID and availability",
            **kwargs
        )
        self.script_id = script_id


class LabParameterError(LabError):
    """Raised when lab parameter is invalid"""
    
    def __init__(self, parameter: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid lab parameter '{parameter}': {value}",
            error_code="LAB_PARAMETER_ERROR",
            context={"parameter": parameter, "value": str(value)},
            **kwargs
        )
        self.parameter = parameter
        self.value = value
