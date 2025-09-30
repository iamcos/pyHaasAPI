"""
Script-related exceptions
"""

from .base import NonRetryableError


class ScriptError(NonRetryableError):
    """Base class for script-related errors"""
    
    def __init__(self, message: str = "Script operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="SCRIPT_ERROR",
            recovery_suggestion="Check script configuration and try again",
            **kwargs
        )


class ScriptNotFoundError(ScriptError):
    """Raised when script is not found"""
    
    def __init__(self, script_id: str, **kwargs):
        super().__init__(
            message=f"Script not found: {script_id}",
            error_code="SCRIPT_NOT_FOUND",
            context={"script_id": script_id},
            recovery_suggestion="Check script ID and try again",
            **kwargs
        )
        self.script_id = script_id


class ScriptCreationError(ScriptError):
    """Raised when script creation fails"""
    
    def __init__(self, script_name: str, **kwargs):
        super().__init__(
            message=f"Script creation failed: {script_name}",
            error_code="SCRIPT_CREATION_ERROR",
            context={"script_name": script_name},
            recovery_suggestion="Check script parameters and try again",
            **kwargs
        )
        self.script_name = script_name


class ScriptConfigurationError(ScriptError):
    """Raised when script configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid script configuration '{config_field}': {value}",
            error_code="SCRIPT_CONFIG_ERROR",
            context={"config_field": config_field, "value": str(value)},
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class ScriptExecutionError(ScriptError):
    """Raised when script execution fails"""
    
    def __init__(self, script_id: str, **kwargs):
        super().__init__(
            message=f"Script execution failed: {script_id}",
            error_code="SCRIPT_EXECUTION_ERROR",
            context={"script_id": script_id},
            recovery_suggestion="Check script syntax and dependencies",
            **kwargs
        )
        self.script_id = script_id


class ScriptValidationError(ScriptError):
    """Raised when script validation fails"""
    
    def __init__(self, script_id: str, validation_error: str, **kwargs):
        super().__init__(
            message=f"Script validation failed: {script_id} - {validation_error}",
            error_code="SCRIPT_VALIDATION_ERROR",
            context={"script_id": script_id, "validation_error": validation_error},
            recovery_suggestion="Fix script syntax and try again",
            **kwargs
        )
        self.script_id = script_id
        self.validation_error = validation_error



