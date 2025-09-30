"""
Order-related exceptions
"""

from .base import NonRetryableError


class OrderError(NonRetryableError):
    """Base class for order-related errors"""
    
    def __init__(self, message: str = "Order operation failed", **kwargs):
        super().__init__(
            message=message,
            error_code="ORDER_ERROR",
            recovery_suggestion="Check order configuration and try again",
            **kwargs
        )


class OrderNotFoundError(OrderError):
    """Raised when order is not found"""
    
    def __init__(self, order_id: str, **kwargs):
        super().__init__(
            message=f"Order not found: {order_id}",
            error_code="ORDER_NOT_FOUND",
            context={"order_id": order_id},
            recovery_suggestion="Check order ID and try again",
            **kwargs
        )
        self.order_id = order_id


class OrderExecutionError(OrderError):
    """Raised when order execution fails"""
    
    def __init__(self, order_id: str, **kwargs):
        super().__init__(
            message=f"Order execution failed: {order_id}",
            error_code="ORDER_EXECUTION_ERROR",
            context={"order_id": order_id},
            recovery_suggestion="Check order parameters and market conditions",
            **kwargs
        )
        self.order_id = order_id


class OrderValidationError(OrderError):
    """Raised when order validation fails"""
    
    def __init__(self, order_id: str, validation_error: str, **kwargs):
        super().__init__(
            message=f"Order validation failed: {order_id} - {validation_error}",
            error_code="ORDER_VALIDATION_ERROR",
            context={"order_id": order_id, "validation_error": validation_error},
            recovery_suggestion="Fix order parameters and try again",
            **kwargs
        )
        self.order_id = order_id
        self.validation_error = validation_error


class OrderCancellationError(OrderError):
    """Raised when order cancellation fails"""
    
    def __init__(self, order_id: str, **kwargs):
        super().__init__(
            message=f"Order cancellation failed: {order_id}",
            error_code="ORDER_CANCELLATION_ERROR",
            context={"order_id": order_id},
            recovery_suggestion="Check order status and try again",
            **kwargs
        )
        self.order_id = order_id



