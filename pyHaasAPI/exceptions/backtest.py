"""
Backtest-related exceptions
"""

from .base import NonRetryableError


class BacktestError(NonRetryableError):
    """Base class for backtest-related errors"""
    
    def __init__(self, message: str = "Backtest operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="BACKTEST_ERROR",
            recovery_suggestion="Check backtest configuration and try again",
            **kwargs
        )


class BacktestNotFoundError(BacktestError):
    """Raised when backtest is not found"""
    
    def __init__(self, backtest_id: str, **kwargs):
        super().__init__(
            message=f"Backtest not found: {backtest_id}",
            error_code="BACKTEST_NOT_FOUND",
            context={"backtest_id": backtest_id},
            recovery_suggestion="Check backtest ID and try again",
            **kwargs
        )
        self.backtest_id = backtest_id


class BacktestExecutionError(BacktestError):
    """Raised when backtest execution fails"""
    
    def __init__(self, backtest_id: str, **kwargs):
        super().__init__(
            message=f"Backtest execution failed: {backtest_id}",
            error_code="BACKTEST_EXECUTION_ERROR",
            context={"backtest_id": backtest_id},
            recovery_suggestion="Check backtest parameters and script",
            **kwargs
        )
        self.backtest_id = backtest_id


class BacktestConfigurationError(BacktestError):
    """Raised when backtest configuration is invalid"""
    
    def __init__(self, config_field: str, value: any, **kwargs):
        super().__init__(
            message=f"Invalid backtest configuration '{config_field}': {value}",
            error_code="BACKTEST_CONFIG_ERROR",
            context={"config_field": config_field, "value": str(value)},
            **kwargs
        )
        self.config_field = config_field
        self.value = value


class BacktestDataError(BacktestError):
    """Raised when backtest data operation fails"""
    
    def __init__(self, backtest_id: str, **kwargs):
        super().__init__(
            message=f"Backtest data operation failed: {backtest_id}",
            error_code="BACKTEST_DATA_ERROR",
            context={"backtest_id": backtest_id},
            recovery_suggestion="Check backtest data availability",
            **kwargs
        )
        self.backtest_id = backtest_id



