"""
Bot-related exceptions
"""

from .base import NonRetryableError


class BotError(NonRetryableError):
    """Base class for bot-related errors"""
    
    def __init__(self, message: str = "Bot operation failed", **kwargs):
        # Ensure default codes are present if not supplied
        kwargs.setdefault("error_code", "BOT_ERROR")
        kwargs.setdefault("recovery_suggestion", "Check bot configuration and try again")
        super().__init__(message=message, **kwargs)


class BotCreationError(BotError):
    """Base class for bot creation errors"""
    
    def __init__(self, message: str = "Bot creation failed", **kwargs):
        kwargs.setdefault("error_code", "BOT_CREATION_ERROR")
        super().__init__(message=message, **kwargs)


class BotConfigurationError(BotError):
    """Raised when bot configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid bot configuration '{config_field}': {value}",
            error_code="BOT_CONFIG_ERROR",
            context={"config_field": config_field, "value": str(value)},
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class InvalidBotConfigurationError(BotConfigurationError):
    """Raised when bot configuration is invalid (legacy)"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            config_field=config_field,
            value=value,
            **kwargs
        )


class BotActivationError(BotCreationError):
    """Raised when bot activation fails"""
    
    def __init__(self, bot_id: str, **kwargs):
        super().__init__(
            message=f"Failed to activate bot: {bot_id}",
            error_code="BOT_ACTIVATION_ERROR",
            context={"bot_id": bot_id},
            recovery_suggestion="Check bot status and configuration",
            **kwargs
        )
        self.bot_id = bot_id


class BotDeactivationError(BotCreationError):
    """Raised when bot deactivation fails"""
    
    def __init__(self, bot_id: str, **kwargs):
        super().__init__(
            message=f"Failed to deactivate bot: {bot_id}",
            error_code="BOT_DEACTIVATION_ERROR",
            context={"bot_id": bot_id},
            recovery_suggestion="Check bot status and try again",
            **kwargs
        )
        self.bot_id = bot_id


class BotNotFoundError(BotCreationError):
    """Raised when bot is not found"""
    
    def __init__(self, bot_id: str, **kwargs):
        super().__init__(
            message=f"Bot not found: {bot_id}",
            error_code="BOT_NOT_FOUND",
            context={"bot_id": bot_id},
            recovery_suggestion="Check bot ID and try again",
            **kwargs
        )
        self.bot_id = bot_id


class BotParameterError(BotCreationError):
    """Raised when bot parameter is invalid"""
    
    def __init__(self, parameter: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid bot parameter '{parameter}': {value}",
            error_code="BOT_PARAMETER_ERROR",
            context={"parameter": parameter, "value": str(value)},
            **kwargs
        )
        self.parameter = parameter
        self.value = value
