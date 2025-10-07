"""
Finetuning-related exceptions
"""

from .base import NonRetryableError


class FinetuneError(NonRetryableError):
    """Base class for finetuning-related errors"""
    
    def __init__(self, message: str = "Finetuning error occurred", **kwargs):
        super().__init__(
            message=message,
            error_code="FINETUNE_ERROR",
            recovery_suggestion="Adjust finetuning parameters and retry",
            **kwargs
        )


