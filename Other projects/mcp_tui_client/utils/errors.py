"""
Error handling framework for MCP TUI Client

Provides comprehensive error handling, categorization, and recovery strategies.
"""

import logging
import traceback
import sys
from enum import Enum
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import json


class ErrorCategory(Enum):
    """Error categories for classification and handling"""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    API = "api"
    UI = "ui"
    WORKFLOW = "workflow"
    DATA = "data"
    CACHE = "cache"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """Comprehensive error information"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    technical_details: str
    timestamp: datetime
    context: ErrorContext
    stack_trace: Optional[str] = None
    recovery_suggestions: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "error_id": self.error_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "user_message": self.user_message,
            "technical_details": self.technical_details,
            "timestamp": self.timestamp.isoformat(),
            "context": {
                "user_id": self.context.user_id,
                "session_id": self.context.session_id,
                "component": self.context.component,
                "operation": self.context.operation,
                "request_id": self.context.request_id,
                "additional_data": self.context.additional_data
            },
            "stack_trace": self.stack_trace,
            "recovery_suggestions": self.recovery_suggestions,
            "related_errors": self.related_errors
        }


class MCPTUIError(Exception):
    """Base exception for MCP TUI Client"""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: Optional[str] = None,
        context: Optional[ErrorContext] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.context = context or ErrorContext()
        self.recovery_suggestions = recovery_suggestions or []
    
    def _generate_user_message(self) -> str:
        """Generate user-friendly error message"""
        category_messages = {
            ErrorCategory.CONNECTION: "Unable to connect to the server. Please check your connection settings.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials.",
            ErrorCategory.VALIDATION: "Invalid input provided. Please check your data and try again.",
            ErrorCategory.CONFIGURATION: "Configuration error. Please check your settings.",
            ErrorCategory.NETWORK: "Network error occurred. Please check your internet connection.",
            ErrorCategory.API: "Server error occurred. Please try again later.",
            ErrorCategory.UI: "Interface error occurred. Please refresh the application.",
            ErrorCategory.WORKFLOW: "Workflow execution failed. Please check your workflow configuration.",
            ErrorCategory.DATA: "Data processing error occurred. Please check your data format.",
            ErrorCategory.SYSTEM: "System error occurred. Please contact support if the issue persists.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
        }
        return category_messages.get(self.category, "An error occurred. Please try again.")


class ConnectionError(MCPTUIError):
    """MCP server connection errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CONNECTION,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check MCP server is running",
                "Verify host and port settings",
                "Check network connectivity",
                "Try reconnecting"
            ],
            **kwargs
        )


class AuthenticationError(MCPTUIError):
    """Authentication and authorization errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check your credentials",
                "Verify API key is valid",
                "Contact administrator for access",
                "Try logging in again"
            ],
            **kwargs
        )


class ValidationError(MCPTUIError):
    """Data validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        self.field = field
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Check input format",
                "Verify required fields are filled",
                "Review validation rules",
                "Try with different values"
            ],
            **kwargs
        )


class ConfigurationError(MCPTUIError):
    """Configuration-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check configuration file",
                "Verify settings are correct",
                "Reset to default configuration",
                "Contact support for help"
            ],
            **kwargs
        )


class WorkflowExecutionError(MCPTUIError):
    """Workflow execution errors"""
    
    def __init__(self, message: str, node_id: Optional[str] = None, **kwargs):
        self.node_id = node_id
        super().__init__(
            message,
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Check workflow configuration",
                "Verify node connections",
                "Review input parameters",
                "Try running individual nodes"
            ],
            **kwargs
        )


class APIError(MCPTUIError):
    """API-related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        self.status_code = status_code
        super().__init__(
            message,
            category=ErrorCategory.API,
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Try the request again",
                "Check server status",
                "Verify request parameters",
                "Contact support if issue persists"
            ],
            **kwargs
        )


class CacheError(MCPTUIError):
    """Cache-related errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.LOW,
            recovery_suggestions=[
                "Clear cache and try again",
                "Check available disk space",
                "Verify cache configuration",
                "Restart the application"
            ],
            **kwargs
        )


class ErrorHandler:
    """Centralized error handling and recovery system"""
    
    def __init__(self, app_context: Optional[Any] = None):
        self.app_context = app_context
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self) -> None:
        """Set up default recovery strategies"""
        self.recovery_strategies = {
            ErrorCategory.CONNECTION: self._handle_connection_error,
            ErrorCategory.AUTHENTICATION: self._handle_auth_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.CONFIGURATION: self._handle_config_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.API: self._handle_api_error,
            ErrorCategory.UI: self._handle_ui_error,
            ErrorCategory.WORKFLOW: self._handle_workflow_error,
            ErrorCategory.DATA: self._handle_data_error,
            ErrorCategory.SYSTEM: self._handle_system_error,
        }
    
    def handle_error(
        self,
        error: Union[Exception, MCPTUIError],
        context: Optional[ErrorContext] = None,
        auto_recover: bool = True
    ) -> ErrorInfo:
        """Handle an error with comprehensive logging and recovery"""
        
        # Generate unique error ID
        error_id = self._generate_error_id()
        
        # Extract error information
        if isinstance(error, MCPTUIError):
            category = error.category
            severity = error.severity
            message = error.message
            user_message = error.user_message
            recovery_suggestions = error.recovery_suggestions
            error_context = error.context
        else:
            category = self._categorize_error(error)
            severity = self._assess_severity(error)
            message = str(error)
            user_message = self._generate_user_message(error, category)
            recovery_suggestions = self._get_recovery_suggestions(category)
            error_context = context or ErrorContext()
        
        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=message,
            user_message=user_message,
            technical_details=self._get_technical_details(error),
            timestamp=datetime.now(),
            context=error_context,
            stack_trace=self._get_stack_trace(error),
            recovery_suggestions=recovery_suggestions
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Store in history
        self.error_history.append(error_info)
        
        # Trigger callbacks
        self._trigger_callbacks(error_info)
        
        # Attempt recovery if enabled
        if auto_recover:
            self._attempt_recovery(error_info)
        
        return error_info
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and message"""
        error_type = type(error).__name__.lower()
        error_message = str(error).lower()
        
        # Connection-related errors
        if any(keyword in error_type for keyword in ['connection', 'timeout', 'socket']):
            return ErrorCategory.CONNECTION
        
        # Authentication errors
        if any(keyword in error_message for keyword in ['auth', 'credential', 'unauthorized', 'forbidden']):
            return ErrorCategory.AUTHENTICATION
        
        # Validation errors
        if any(keyword in error_type for keyword in ['validation', 'value', 'type']):
            return ErrorCategory.VALIDATION
        
        # Configuration errors
        if any(keyword in error_message for keyword in ['config', 'setting', 'parameter']):
            return ErrorCategory.CONFIGURATION
        
        # Network errors
        if any(keyword in error_type for keyword in ['network', 'http', 'url', 'dns']):
            return ErrorCategory.NETWORK
        
        # API errors
        if any(keyword in error_message for keyword in ['api', 'server', 'response']):
            return ErrorCategory.API
        
        return ErrorCategory.UNKNOWN
    
    def _assess_severity(self, error: Exception) -> ErrorSeverity:
        """Assess error severity"""
        error_type = type(error).__name__.lower()
        
        # Critical errors
        if any(keyword in error_type for keyword in ['system', 'memory', 'disk', 'critical']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(keyword in error_type for keyword in ['connection', 'auth', 'security']):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(keyword in error_type for keyword in ['validation', 'api', 'network']):
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    def _generate_user_message(self, error: Exception, category: ErrorCategory) -> str:
        """Generate user-friendly error message"""
        temp_error = MCPTUIError("", category=category)
        return temp_error._generate_user_message()
    
    def _get_recovery_suggestions(self, category: ErrorCategory) -> List[str]:
        """Get recovery suggestions for error category"""
        suggestions = {
            ErrorCategory.CONNECTION: [
                "Check network connection",
                "Verify server is running",
                "Try reconnecting"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Check credentials",
                "Verify API key",
                "Try logging in again"
            ],
            ErrorCategory.VALIDATION: [
                "Check input format",
                "Verify required fields",
                "Review validation rules"
            ],
            ErrorCategory.CONFIGURATION: [
                "Check configuration file",
                "Verify settings",
                "Reset to defaults"
            ]
        }
        return suggestions.get(category, ["Try again", "Contact support"])
    
    def _get_technical_details(self, error: Exception) -> str:
        """Get technical error details"""
        return f"{type(error).__name__}: {str(error)}"
    
    def _get_stack_trace(self, error: Exception) -> Optional[str]:
        """Get stack trace if available"""
        try:
            return traceback.format_exc()
        except:
            return None
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error information"""
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)
        
        self.logger.log(
            log_level,
            f"Error {error_info.error_id}: {error_info.message} "
            f"[{error_info.category.value}] [{error_info.severity.value}]"
        )
        
        if error_info.stack_trace and error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"Stack trace for {error_info.error_id}:\n{error_info.stack_trace}")
    
    def _trigger_callbacks(self, error_info: ErrorInfo) -> None:
        """Trigger registered error callbacks"""
        callbacks = self.error_callbacks.get(error_info.category, [])
        for callback in callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"Error in callback: {e}")
    
    def _attempt_recovery(self, error_info: ErrorInfo) -> bool:
        """Attempt automatic error recovery"""
        strategy = self.recovery_strategies.get(error_info.category)
        if strategy:
            try:
                return strategy(error_info)
            except Exception as e:
                self.logger.error(f"Recovery strategy failed: {e}")
        return False
    
    # Default recovery strategies
    def _handle_connection_error(self, error_info: ErrorInfo) -> bool:
        """Handle connection errors"""
        self.logger.info(f"Attempting connection recovery for {error_info.error_id}")
        # Implementation would depend on app context
        return False
    
    def _handle_auth_error(self, error_info: ErrorInfo) -> bool:
        """Handle authentication errors"""
        self.logger.info(f"Attempting auth recovery for {error_info.error_id}")
        # Implementation would depend on app context
        return False
    
    def _handle_validation_error(self, error_info: ErrorInfo) -> bool:
        """Handle validation errors"""
        self.logger.info(f"Validation error logged: {error_info.error_id}")
        # Usually no automatic recovery for validation errors
        return False
    
    def _handle_config_error(self, error_info: ErrorInfo) -> bool:
        """Handle configuration errors"""
        self.logger.info(f"Attempting config recovery for {error_info.error_id}")
        # Could attempt to reset to defaults
        return False
    
    def _handle_network_error(self, error_info: ErrorInfo) -> bool:
        """Handle network errors"""
        self.logger.info(f"Attempting network recovery for {error_info.error_id}")
        # Could implement retry logic
        return False
    
    def _handle_api_error(self, error_info: ErrorInfo) -> bool:
        """Handle API errors"""
        self.logger.info(f"Attempting API recovery for {error_info.error_id}")
        # Could implement retry with backoff
        return False
    
    def _handle_ui_error(self, error_info: ErrorInfo) -> bool:
        """Handle UI errors"""
        self.logger.info(f"Attempting UI recovery for {error_info.error_id}")
        # Could attempt to refresh UI components
        return False
    
    def _handle_workflow_error(self, error_info: ErrorInfo) -> bool:
        """Handle workflow errors"""
        self.logger.info(f"Workflow error logged: {error_info.error_id}")
        # Usually requires manual intervention
        return False
    
    def _handle_data_error(self, error_info: ErrorInfo) -> bool:
        """Handle data errors"""
        self.logger.info(f"Data error logged: {error_info.error_id}")
        # Usually requires data correction
        return False
    
    def _handle_system_error(self, error_info: ErrorInfo) -> bool:
        """Handle system errors"""
        self.logger.critical(f"System error: {error_info.error_id}")
        # System errors usually require immediate attention
        return False
    
    def register_callback(self, category: ErrorCategory, callback: Callable[[ErrorInfo], None]) -> None:
        """Register error callback for specific category"""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable[[ErrorInfo], bool]) -> None:
        """Register custom recovery strategy"""
        self.recovery_strategies[category] = strategy
    
    def get_error_history(self, limit: Optional[int] = None) -> List[ErrorInfo]:
        """Get error history"""
        if limit:
            return self.error_history[-limit:]
        return self.error_history.copy()
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_history:
            return {"total": 0}
        
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            "total": len(self.error_history),
            "by_category": category_counts,
            "by_severity": severity_counts,
            "recent_errors": len([e for e in self.error_history if (datetime.now() - e.timestamp).seconds < 3600])
        }
    
    def export_error_report(self, file_path: str, limit: Optional[int] = None) -> bool:
        """Export error report to file"""
        try:
            errors = self.get_error_history(limit)
            report = {
                "generated_at": datetime.now().isoformat(),
                "stats": self.get_error_stats(),
                "errors": [error.to_dict() for error in errors]
            }
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Error report exported to {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export error report: {e}")
            return False
    
    def clear_error_history(self) -> None:
        """Clear error history"""
        self.error_history.clear()
        self.logger.info("Error history cleared")


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_error(
    error: Union[Exception, MCPTUIError],
    context: Optional[ErrorContext] = None,
    auto_recover: bool = True
) -> ErrorInfo:
    """Convenience function to handle errors using global handler"""
    return get_error_handler().handle_error(error, context, auto_recover)


# Decorator for automatic error handling
def error_handler(
    category: Optional[ErrorCategory] = None,
    severity: Optional[ErrorSeverity] = None,
    auto_recover: bool = True,
    reraise: bool = False
):
    """Decorator for automatic error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create context from function info
                context = ErrorContext(
                    component=func.__module__,
                    operation=func.__name__
                )
                
                # Handle the error
                if isinstance(e, MCPTUIError):
                    if category:
                        e.category = category
                    if severity:
                        e.severity = severity
                    error_info = handle_error(e, context, auto_recover)
                else:
                    mcp_error = MCPTUIError(
                        str(e),
                        category=category or ErrorCategory.UNKNOWN,
                        severity=severity or ErrorSeverity.MEDIUM,
                        context=context
                    )
                    error_info = handle_error(mcp_error, context, auto_recover)
                
                if reraise:
                    raise
                
                return error_info
        return wrapper
    return decorator