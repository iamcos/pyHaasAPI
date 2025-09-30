"""
Configuration-related exceptions
"""

from .base import NonRetryableError


class ConfigurationError(NonRetryableError):
    """Raised when configuration is invalid or missing"""
    
    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            recovery_suggestion="Check your configuration settings",
            **kwargs
        )


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing"""
    
    def __init__(self, config_key: str, **kwargs):
        super().__init__(
            message=f"Missing required configuration: {config_key}",
            error_code="MISSING_CONFIG",
            context={"config_key": config_key},
            recovery_suggestion=f"Set the {config_key} configuration value",
            **kwargs
        )
        self.config_key = config_key


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration value is invalid"""
    
    def __init__(self, config_key: str, value: any, expected_type: str = None, **kwargs):
        message = f"Invalid configuration for '{config_key}': {value}"
        if expected_type:
            message += f" (expected {expected_type})"
        
        super().__init__(
            message=message,
            error_code="INVALID_CONFIG",
            context={"config_key": config_key, "value": str(value), "expected_type": expected_type},
            **kwargs
        )
        self.config_key = config_key
        self.value = value
        self.expected_type = expected_type


class EnvironmentVariableError(ConfigurationError):
    """Raised when environment variable is missing or invalid"""
    
    def __init__(self, env_var: str, **kwargs):
        super().__init__(
            message=f"Environment variable '{env_var}' is missing or invalid",
            error_code="ENV_VAR_ERROR",
            context={"env_var": env_var},
            recovery_suggestion=f"Set the {env_var} environment variable",
            **kwargs
        )
        self.env_var = env_var
