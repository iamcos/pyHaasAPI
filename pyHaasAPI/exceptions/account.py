"""
Account-related exceptions
"""

from .base import NonRetryableError


class AccountError(NonRetryableError):
    """Base class for account-related errors"""
    
    def __init__(self, message: str = "Account operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="ACCOUNT_ERROR",
            recovery_suggestion="Check account configuration and try again",
            **kwargs
        )


class AccountNotFoundError(AccountError):
    """Raised when account is not found"""
    
    def __init__(self, account_id: str, **kwargs):
        super().__init__(
            message=f"Account not found: {account_id}",
            error_code="ACCOUNT_NOT_FOUND",
            context={"account_id": account_id},
            recovery_suggestion="Check account ID and try again",
            **kwargs
        )
        self.account_id = account_id


class AccountConfigurationError(AccountError):
    """Raised when account configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid account configuration '{config_field}': {value}",
            error_code="ACCOUNT_CONFIG_ERROR",
            context={"config_field": config_field, "value": str(value)},
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class AccountBalanceError(AccountError):
    """Raised when account balance operation fails"""
    
    def __init__(self, account_id: str, **kwargs):
        super().__init__(
            message=f"Account balance operation failed: {account_id}",
            error_code="ACCOUNT_BALANCE_ERROR",
            context={"account_id": account_id},
            recovery_suggestion="Check account balance and try again",
            **kwargs
        )
        self.account_id = account_id


class AccountPermissionError(AccountError):
    """Raised when account permission is insufficient"""
    
    def __init__(self, account_id: str, operation: str, **kwargs):
        super().__init__(
            message=f"Insufficient permissions for operation '{operation}' on account: {account_id}",
            error_code="ACCOUNT_PERMISSION_ERROR",
            context={"account_id": account_id, "operation": operation},
            recovery_suggestion="Check account permissions and try again",
            **kwargs
        )
        self.account_id = account_id
        self.operation = operation



