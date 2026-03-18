"""
Lab-related exceptions
"""

from .base import NonRetryableError


class LabError(NonRetryableError):
    """Base class for lab-related errors"""
    
    def __init__(self, message: str = "Lab operation failed", **kwargs):
        # Allow subclasses to override default values
        kwargs.setdefault("error_code", "LAB_ERROR")
        kwargs.setdefault("recovery_suggestion", "Check lab configuration and try again")
        super().__init__(
            message=message,
            **kwargs
        )


class LabNotFoundError(LabError):
    """Raised when lab is not found"""
    
    def __init__(self, lab_id: str, **kwargs):
        kwargs.setdefault("error_code", "LAB_NOT_FOUND")
        kwargs.setdefault("recovery_suggestion", "Check lab ID and try again")
        context = kwargs.get("context", {})
        context["lab_id"] = lab_id
        kwargs["context"] = context
        super().__init__(
            message=f"Lab not found: {lab_id}",
            **kwargs
        )
        self.lab_id = lab_id


class LabExecutionError(LabError):
    """Raised when lab execution fails"""
    
    def __init__(self, lab_id: str, message: str = None, **kwargs):
        if not message:
            message = f"Lab execution failed: {lab_id}"
        kwargs.setdefault("error_code", "LAB_EXECUTION_ERROR")
        kwargs.setdefault("recovery_suggestion", "Check lab configuration and script")
        context = kwargs.get("context", {})
        context["lab_id"] = lab_id
        kwargs["context"] = context
        super().__init__(
            message=message,
            **kwargs
        )
        self.lab_id = lab_id


class LabConfigurationError(LabError):
    """Raised when lab configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, message: str = None, **kwargs):
        kwargs.setdefault("error_code", "LAB_CONFIG_ERROR")
        if not message:
            message = f"Invalid lab configuration '{config_field}': {value}"
        context = kwargs.get("context", {})
        context.update({"config_field": config_field, "value": str(value)})
        kwargs["context"] = context
        super().__init__(
            message=message,
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class LabScriptError(LabError):
    """Raised when lab script is invalid"""
    
    def __init__(self, script_id: str, **kwargs):
        kwargs.setdefault("error_code", "LAB_SCRIPT_ERROR")
        kwargs.setdefault("recovery_suggestion", "Check script ID and availability")
        context = kwargs.get("context", {})
        context["script_id"] = script_id
        kwargs["context"] = context
        super().__init__(
            message=f"Invalid lab script: {script_id}",
            **kwargs
        )
        self.script_id = script_id


class LabParameterError(LabError):
    """Raised when lab parameter is invalid"""
    
    def __init__(self, parameter: str, value: any, **kwargs):
        kwargs.setdefault("error_code", "LAB_PARAMETER_ERROR")
        context = kwargs.get("context", {})
        context.update({"parameter": parameter, "value": str(value)})
        kwargs["context"] = context
        super().__init__(
            message=f"Invalid lab parameter '{parameter}': {value}",
            **kwargs
        )
        self.parameter = parameter
        self.value = value
