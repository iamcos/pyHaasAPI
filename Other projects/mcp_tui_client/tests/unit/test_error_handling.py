"""
Unit tests for error handling framework.
"""

import pytest
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from mcp_tui_client.utils.errors import (
    ErrorCategory, ErrorSeverity, ErrorContext, ErrorInfo,
    MCPTUIError, ConnectionError, AuthenticationError, ValidationError,
    ConfigurationError, WorkflowExecutionError, APIError,
    ErrorHandler, get_error_handler, handle_error, error_handler
)


class TestErrorCategories:
    """Test error category and severity enums."""
    
    def test_error_categories(self):
        """Test error category enum values."""
        assert ErrorCategory.CONNECTION.value == "connection"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.UNKNOWN.value == "unknown"
    
    def test_error_severities(self):
        """Test error severity enum values."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestErrorContext:
    """Test error context data structure."""
    
    def test_error_context_creation(self):
        """Test error context creation with default values."""
        context = ErrorContext()
        assert context.user_id is None
        assert context.session_id is None
        assert context.component is None
        assert context.operation is None
        assert context.additional_data == {}
    
    def test_error_context_with_data(self):
        """Test error context with provided data."""
        context = ErrorContext(
            user_id="user123",
            component="test_component",
            operation="test_operation",
            additional_data={"key": "value"}
        )
        assert context.user_id == "user123"
        assert context.component == "test_component"
        assert context.operation == "test_operation"
        assert context.additional_data["key"] == "value"


class TestErrorInfo:
    """Test error info data structure."""
    
    def test_error_info_creation(self):
        """Test error info creation."""
        context = ErrorContext(user_id="test_user")
        error_info = ErrorInfo(
            error_id="test-123",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            user_message="User friendly message",
            technical_details="Technical details",
            timestamp=datetime.now(),
            context=context
        )
        
        assert error_info.error_id == "test-123"
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.message == "Test error"
        assert error_info.user_message == "User friendly message"
        assert error_info.context.user_id == "test_user"
    
    def test_error_info_to_dict(self):
        """Test error info serialization to dictionary."""
        context = ErrorContext(user_id="test_user")
        error_info = ErrorInfo(
            error_id="test-123",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            user_message="User friendly message",
            technical_details="Technical details",
            timestamp=datetime.now(),
            context=context
        )
        
        error_dict = error_info.to_dict()
        assert error_dict["error_id"] == "test-123"
        assert error_dict["category"] == "validation"
        assert error_dict["severity"] == "medium"
        assert error_dict["context"]["user_id"] == "test_user"


class TestMCPTUIError:
    """Test base MCP TUI error class."""
    
    def test_mcp_tui_error_creation(self):
        """Test MCP TUI error creation with defaults."""
        error = MCPTUIError("Test error")
        assert error.message == "Test error"
        assert error.category == ErrorCategory.UNKNOWN
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.user_message == "An unexpected error occurred. Please try again."
        assert isinstance(error.context, ErrorContext)
        assert error.recovery_suggestions == []
    
    def test_mcp_tui_error_with_parameters(self):
        """Test MCP TUI error creation with parameters."""
        context = ErrorContext(user_id="test_user")
        error = MCPTUIError(
            "Test error",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            user_message="Custom user message",
            context=context,
            recovery_suggestions=["Try again", "Check input"]
        )
        
        assert error.message == "Test error"
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.HIGH
        assert error.user_message == "Custom user message"
        assert error.context.user_id == "test_user"
        assert "Try again" in error.recovery_suggestions


class TestSpecificErrors:
    """Test specific error types."""
    
    def test_connection_error(self):
        """Test connection error."""
        error = ConnectionError("Connection failed")
        assert error.category == ErrorCategory.CONNECTION
        assert error.severity == ErrorSeverity.HIGH
        assert "Check MCP server is running" in error.recovery_suggestions
    
    def test_authentication_error(self):
        """Test authentication error."""
        error = AuthenticationError("Auth failed")
        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.severity == ErrorSeverity.HIGH
        assert "Check your credentials" in error.recovery_suggestions
    
    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid data", field="username")
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.field == "username"
        assert "Check input format" in error.recovery_suggestions
    
    def test_configuration_error(self):
        """Test configuration error."""
        error = ConfigurationError("Config invalid")
        assert error.category == ErrorCategory.CONFIGURATION
        assert error.severity == ErrorSeverity.HIGH
        assert "Check configuration file" in error.recovery_suggestions
    
    def test_workflow_execution_error(self):
        """Test workflow execution error."""
        error = WorkflowExecutionError("Workflow failed", node_id="node-123")
        assert error.category == ErrorCategory.WORKFLOW
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.node_id == "node-123"
        assert "Check workflow configuration" in error.recovery_suggestions
    
    def test_api_error(self):
        """Test API error."""
        error = APIError("API call failed", status_code=500)
        assert error.category == ErrorCategory.API
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.status_code == 500
        assert "Try the request again" in error.recovery_suggestions


class TestErrorHandler:
    """Test error handler functionality."""
    
    def test_error_handler_creation(self):
        """Test error handler creation."""
        handler = ErrorHandler()
        assert handler.error_history == []
        assert handler.error_callbacks == {}
        assert len(handler.recovery_strategies) > 0
    
    def test_handle_mcp_error(self):
        """Test handling MCP TUI error."""
        handler = ErrorHandler()
        error = ValidationError("Invalid input")
        
        error_info = handler.handle_error(error, auto_recover=False)
        
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.message == "Invalid input"
        assert len(handler.error_history) == 1
    
    def test_handle_generic_error(self):
        """Test handling generic Python error."""
        handler = ErrorHandler()
        error = ValueError("Invalid value")
        
        error_info = handler.handle_error(error, auto_recover=False)
        
        assert error_info.category == ErrorCategory.VALIDATION  # ValueError categorized as validation
        assert error_info.message == "Invalid value"
        assert len(handler.error_history) == 1
    
    def test_error_categorization(self):
        """Test automatic error categorization."""
        handler = ErrorHandler()
        
        # Test connection error categorization
        connection_error = ConnectionError("Connection timeout")
        error_info = handler.handle_error(connection_error, auto_recover=False)
        assert error_info.category == ErrorCategory.CONNECTION
        
        # Test generic error categorization
        value_error = ValueError("Invalid value")
        error_info = handler.handle_error(value_error, auto_recover=False)
        assert error_info.category == ErrorCategory.VALIDATION
    
    def test_error_callbacks(self):
        """Test error callback registration and execution."""
        handler = ErrorHandler()
        callback_called = False
        
        def test_callback(error_info):
            nonlocal callback_called
            callback_called = True
            assert error_info.category == ErrorCategory.VALIDATION
        
        handler.register_callback(ErrorCategory.VALIDATION, test_callback)
        
        error = ValidationError("Test error")
        handler.handle_error(error, auto_recover=False)
        
        assert callback_called
    
    def test_recovery_strategy_registration(self):
        """Test recovery strategy registration."""
        handler = ErrorHandler()
        recovery_called = False
        
        def test_recovery(error_info):
            nonlocal recovery_called
            recovery_called = True
            return True
        
        handler.register_recovery_strategy(ErrorCategory.VALIDATION, test_recovery)
        
        error = ValidationError("Test error")
        handler.handle_error(error, auto_recover=True)
        
        assert recovery_called
    
    def test_error_history(self):
        """Test error history tracking."""
        handler = ErrorHandler()
        
        # Add multiple errors
        handler.handle_error(ValidationError("Error 1"), auto_recover=False)
        handler.handle_error(ConnectionError("Error 2"), auto_recover=False)
        handler.handle_error(APIError("Error 3"), auto_recover=False)
        
        history = handler.get_error_history()
        assert len(history) == 3
        
        # Test limited history
        limited_history = handler.get_error_history(limit=2)
        assert len(limited_history) == 2
        assert limited_history[0].message == "Error 2"  # Most recent first
        assert limited_history[1].message == "Error 3"
    
    def test_error_statistics(self):
        """Test error statistics generation."""
        handler = ErrorHandler()
        
        # Add errors of different categories and severities
        handler.handle_error(ValidationError("Error 1"), auto_recover=False)
        handler.handle_error(ValidationError("Error 2"), auto_recover=False)
        handler.handle_error(ConnectionError("Error 3"), auto_recover=False)
        
        stats = handler.get_error_stats()
        
        assert stats["total"] == 3
        assert stats["by_category"]["validation"] == 2
        assert stats["by_category"]["connection"] == 1
        assert stats["by_severity"]["medium"] == 2
        assert stats["by_severity"]["high"] == 1
    
    def test_export_error_report(self):
        """Test error report export."""
        handler = ErrorHandler()
        
        # Add some errors
        handler.handle_error(ValidationError("Error 1"), auto_recover=False)
        handler.handle_error(ConnectionError("Error 2"), auto_recover=False)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            report_path = f.name
        
        try:
            success = handler.export_error_report(report_path)
            assert success
            
            # Verify report content
            with open(report_path, 'r') as f:
                report = json.load(f)
            
            assert "generated_at" in report
            assert "stats" in report
            assert "errors" in report
            assert len(report["errors"]) == 2
            assert report["stats"]["total"] == 2
        finally:
            import os
            os.unlink(report_path)
    
    def test_clear_error_history(self):
        """Test clearing error history."""
        handler = ErrorHandler()
        
        # Add some errors
        handler.handle_error(ValidationError("Error 1"), auto_recover=False)
        handler.handle_error(ConnectionError("Error 2"), auto_recover=False)
        
        assert len(handler.error_history) == 2
        
        handler.clear_error_history()
        assert len(handler.error_history) == 0


class TestGlobalErrorHandler:
    """Test global error handler functions."""
    
    def test_get_error_handler(self):
        """Test getting global error handler."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        # Should return the same instance
        assert handler1 is handler2
    
    def test_handle_error_function(self):
        """Test global handle_error function."""
        error = ValidationError("Test error")
        error_info = handle_error(error, auto_recover=False)
        
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.message == "Test error"


class TestErrorDecorator:
    """Test error handling decorator."""
    
    def test_error_decorator_basic(self):
        """Test basic error decorator functionality."""
        @error_handler(category=ErrorCategory.API, severity=ErrorSeverity.HIGH, reraise=False)
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert isinstance(result, ErrorInfo)
        assert result.category == ErrorCategory.API
        assert result.severity == ErrorSeverity.HIGH
    
    def test_error_decorator_with_reraise(self):
        """Test error decorator with reraise option."""
        @error_handler(category=ErrorCategory.API, reraise=True)
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_function()
    
    def test_error_decorator_success(self):
        """Test error decorator with successful function."""
        @error_handler(category=ErrorCategory.API)
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_error_decorator_with_mcp_error(self):
        """Test error decorator with MCP TUI error."""
        @error_handler(category=ErrorCategory.VALIDATION, reraise=False)
        def test_function():
            raise ValidationError("Validation failed")
        
        result = test_function()
        assert isinstance(result, ErrorInfo)
        assert result.category == ErrorCategory.VALIDATION
        assert result.message == "Validation failed"