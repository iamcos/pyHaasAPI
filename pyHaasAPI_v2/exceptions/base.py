"""
Base exception classes for pyHaasAPI v2
"""

from typing import Any, Dict, Optional


class HaasAPIError(Exception):
    """
    Base exception for all pyHaasAPI errors.
    
    Provides structured error information with context and recovery suggestions.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_suggestion: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.recovery_suggestion = recovery_suggestion
        self.original_error = original_error
    
    def __str__(self) -> str:
        """String representation with context information"""
        parts = [self.message]
        
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")
        
        if self.recovery_suggestion:
            parts.append(f"Recovery: {self.recovery_suggestion}")
        
        return " | ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "recovery_suggestion": self.recovery_suggestion,
            "original_error": str(self.original_error) if self.original_error else None
        }


class RetryableError(HaasAPIError):
    """
    Base class for errors that can be retried.
    
    Used for network issues, temporary API failures, etc.
    """
    pass


class NonRetryableError(HaasAPIError):
    """
    Base class for errors that should not be retried.
    
    Used for authentication failures, validation errors, etc.
    """
    pass
