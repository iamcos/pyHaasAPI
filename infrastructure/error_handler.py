#!/usr/bin/env python3
"""
Error Handling and Retry System

This module provides comprehensive error handling, retry mechanisms, and graceful
error recovery for the distributed trading bot testing automation system.
"""

import time
import logging
import traceback
from typing import Dict, List, Optional, Any, Callable, Type, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import functools
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification"""
    CONNECTION = "connection"
    API = "api"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    DATA_ERROR = "data_error"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """Information about an error occurrence"""
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: float
    context: Dict[str, Any]
    traceback_info: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: List[Type[Exception]] = None
    stop_on_exceptions: List[Type[Exception]] = None

class ErrorClassifier:
    """Classifies errors into categories and severity levels"""
    
    def __init__(self):
        self.classification_rules = {
            # Connection errors
            'ConnectionError': (ErrorCategory.CONNECTION, ErrorSeverity.HIGH),
            'ConnectionRefusedError': (ErrorCategory.CONNECTION, ErrorSeverity.HIGH),
            'ConnectionResetError': (ErrorCategory.CONNECTION, ErrorSeverity.MEDIUM),
            'ConnectionAbortedError': (ErrorCategory.CONNECTION, ErrorSeverity.MEDIUM),
            'TimeoutError': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
            'socket.timeout': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
            'requests.exceptions.Timeout': (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
            'requests.exceptions.ConnectionError': (ErrorCategory.CONNECTION, ErrorSeverity.HIGH),
            
            # API errors
            'requests.exceptions.HTTPError': (ErrorCategory.API, ErrorSeverity.MEDIUM),
            'requests.exceptions.RequestException': (ErrorCategory.API, ErrorSeverity.MEDIUM),
            'HaasApiError': (ErrorCategory.API, ErrorSeverity.MEDIUM),
            
            # Authentication errors
            'AuthenticationError': (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            'PermissionError': (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            
            # Server errors
            'subprocess.CalledProcessError': (ErrorCategory.SERVER_ERROR, ErrorSeverity.HIGH),
            'OSError': (ErrorCategory.SERVER_ERROR, ErrorSeverity.MEDIUM),
            
            # Data errors
            'json.JSONDecodeError': (ErrorCategory.DATA_ERROR, ErrorSeverity.LOW),
            'ValueError': (ErrorCategory.DATA_ERROR, ErrorSeverity.LOW),
            'KeyError': (ErrorCategory.DATA_ERROR, ErrorSeverity.LOW),
            'TypeError': (ErrorCategory.DATA_ERROR, ErrorSeverity.LOW),
            
            # Configuration errors
            'FileNotFoundError': (ErrorCategory.CONFIGURATION, ErrorSeverity.MEDIUM),
            'ConfigurationError': (ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH),
            
            # Resource errors
            'MemoryError': (ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL),
            'DiskSpaceError': (ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL),
        }
        
        # HTTP status code classifications
        self.http_status_classifications = {
            400: (ErrorCategory.API, ErrorSeverity.LOW),
            401: (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            403: (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            404: (ErrorCategory.API, ErrorSeverity.LOW),
            408: (ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM),
            429: (ErrorCategory.API, ErrorSeverity.MEDIUM),
            500: (ErrorCategory.SERVER_ERROR, ErrorSeverity.HIGH),
            502: (ErrorCategory.SERVER_ERROR, ErrorSeverity.HIGH),
            503: (ErrorCategory.SERVER_ERROR, ErrorSeverity.HIGH),
            504: (ErrorCategory.TIMEOUT, ErrorSeverity.HIGH),
        }
    
    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> Tuple[ErrorCategory, ErrorSeverity]:
        """
        Classify an error into category and severity.
        
        Args:
            error: The exception to classify
            context: Additional context information
            
        Returns:
            Tuple of (category, severity)
        """
        error_type = type(error).__name__
        full_error_type = f"{type(error).__module__}.{error_type}"
        
        # Check for specific error types
        for pattern, (category, severity) in self.classification_rules.items():
            if pattern in [error_type, full_error_type]:
                return category, severity
        
        # Check for HTTP status codes in context
        if context and 'http_status' in context:
            status_code = context['http_status']
            if status_code in self.http_status_classifications:
                return self.http_status_classifications[status_code]
        
        # Check error message for specific patterns
        error_message = str(error).lower()
        
        if any(keyword in error_message for keyword in ['connection', 'network', 'unreachable']):
            return ErrorCategory.CONNECTION, ErrorSeverity.HIGH
        
        if any(keyword in error_message for keyword in ['timeout', 'timed out']):
            return ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM
        
        if any(keyword in error_message for keyword in ['authentication', 'unauthorized', 'forbidden']):
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH
        
        if any(keyword in error_message for keyword in ['server error', '500', '502', '503']):
            return ErrorCategory.SERVER_ERROR, ErrorSeverity.HIGH
        
        if '504' in error_message:
            return ErrorCategory.TIMEOUT, ErrorSeverity.HIGH
        
        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

class RetryManager:
    """Manages retry logic with exponential backoff and jitter"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.classifier = ErrorClassifier()
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if an error should trigger a retry.
        
        Args:
            error: The exception that occurred
            attempt: Current attempt number (1-based)
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.config.max_attempts:
            return False
        
        error_type = type(error)
        
        # Check stop conditions
        if self.config.stop_on_exceptions:
            if any(isinstance(error, exc_type) for exc_type in self.config.stop_on_exceptions):
                return False
        
        # Check retry conditions
        if self.config.retry_on_exceptions:
            return any(isinstance(error, exc_type) for exc_type in self.config.retry_on_exceptions)
        
        # Default retry logic based on error classification
        category, severity = self.classifier.classify_error(error)
        
        # Don't retry critical errors or authentication errors
        if severity == ErrorSeverity.CRITICAL:
            return False
        
        if category == ErrorCategory.AUTHENTICATION:
            return False
        
        # Retry connection, timeout, and server errors
        if category in [ErrorCategory.CONNECTION, ErrorCategory.TIMEOUT, ErrorCategory.SERVER_ERROR]:
            return True
        
        # Retry API errors with certain status codes
        if category == ErrorCategory.API:
            error_message = str(error)
            if any(code in error_message for code in ['502', '503', '504', '429']):
                return True
        
        return False
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry attempt.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        if attempt <= 1:
            return 0
        
        # Exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 2))
        
        # Apply maximum delay limit
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            import random
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor
        
        return delay

class ErrorTracker:
    """Tracks and analyzes error patterns"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.error_history: List[ErrorInfo] = []
        self.error_counts: Dict[str, int] = {}
        self.lock = threading.Lock()
    
    def record_error(self, error: Exception, context: Dict[str, Any] = None, retry_count: int = 0) -> ErrorInfo:
        """
        Record an error occurrence.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            retry_count: Number of retry attempts made
            
        Returns:
            ErrorInfo object
        """
        classifier = ErrorClassifier()
        category, severity = classifier.classify_error(error, context)
        
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            error_message=str(error),
            category=category,
            severity=severity,
            timestamp=time.time(),
            context=context or {},
            traceback_info=traceback.format_exc(),
            retry_count=retry_count
        )
        
        with self.lock:
            self.error_history.append(error_info)
            
            # Maintain history size limit
            if len(self.error_history) > self.max_history:
                self.error_history = self.error_history[-self.max_history:]
            
            # Update error counts
            error_key = f"{error_info.category.value}:{error_info.error_type}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        logger.error(f"Error recorded: {error_info.error_type} - {error_info.error_message}")
        
        return error_info
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and patterns"""
        with self.lock:
            if not self.error_history:
                return {'total_errors': 0}
            
            # Calculate statistics
            total_errors = len(self.error_history)
            recent_errors = [e for e in self.error_history if time.time() - e.timestamp < 3600]  # Last hour
            
            # Group by category
            category_counts = {}
            severity_counts = {}
            
            for error in self.error_history:
                category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
                severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            # Most common errors
            most_common = sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_errors': total_errors,
                'recent_errors': len(recent_errors),
                'category_distribution': category_counts,
                'severity_distribution': severity_counts,
                'most_common_errors': most_common,
                'error_rate_per_hour': len(recent_errors)
            }
    
    def get_recent_errors(self, hours: int = 1) -> List[ErrorInfo]:
        """Get errors from the last N hours"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self.lock:
            return [e for e in self.error_history if e.timestamp >= cutoff_time]

def retry_on_error(config: RetryConfig = None):
    """
    Decorator for automatic retry on errors.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = RetryManager(config)
            error_tracker = ErrorTracker()
            
            for attempt in range(1, retry_manager.config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                
                except Exception as e:
                    # Record the error
                    error_info = error_tracker.record_error(
                        e, 
                        context={'function': func.__name__, 'attempt': attempt},
                        retry_count=attempt - 1
                    )
                    
                    # Check if we should retry
                    if not retry_manager.should_retry(e, attempt):
                        logger.error(f"Function {func.__name__} failed after {attempt} attempts: {e}")
                        raise
                    
                    # Calculate delay and wait
                    delay = retry_manager.calculate_delay(attempt)
                    if delay > 0:
                        logger.warning(f"Function {func.__name__} failed (attempt {attempt}), retrying in {delay:.2f}s: {e}")
                        time.sleep(delay)
                    else:
                        logger.warning(f"Function {func.__name__} failed (attempt {attempt}), retrying immediately: {e}")
            
            # This should never be reached due to the loop logic, but just in case
            raise RuntimeError(f"Function {func.__name__} failed after all retry attempts")
        
        return wrapper
    return decorator

@contextmanager
def error_context(context_info: Dict[str, Any], error_tracker: ErrorTracker = None):
    """
    Context manager for error handling with additional context.
    
    Args:
        context_info: Additional context information
        error_tracker: Optional error tracker instance
    """
    if error_tracker is None:
        error_tracker = ErrorTracker()
    
    try:
        yield error_tracker
    except Exception as e:
        error_tracker.record_error(e, context_info)
        raise

class GracefulErrorHandler:
    """Handles errors gracefully with fallback mechanisms"""
    
    def __init__(self):
        self.error_tracker = ErrorTracker()
        self.fallback_handlers: Dict[ErrorCategory, Callable] = {}
    
    def register_fallback_handler(self, category: ErrorCategory, handler: Callable):
        """
        Register a fallback handler for a specific error category.
        
        Args:
            category: Error category
            handler: Fallback handler function
        """
        self.fallback_handlers[category] = handler
        logger.info(f"Registered fallback handler for {category.value} errors")
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None, fallback_result: Any = None) -> Any:
        """
        Handle an error gracefully with fallback mechanisms.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            fallback_result: Default result to return if no fallback handler
            
        Returns:
            Result from fallback handler or fallback_result
        """
        # Record the error
        error_info = self.error_tracker.record_error(error, context)
        
        # Try to use fallback handler
        if error_info.category in self.fallback_handlers:
            try:
                handler = self.fallback_handlers[error_info.category]
                result = handler(error, context)
                logger.info(f"Fallback handler successfully handled {error_info.category.value} error")
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback handler failed: {fallback_error}")
        
        # Return fallback result
        logger.warning(f"Using fallback result for {error_info.category.value} error")
        return fallback_result

def main():
    """Test the error handling system"""
    
    # Test error classification
    print("Testing error classification...")
    classifier = ErrorClassifier()
    
    test_errors = [
        ConnectionError("Connection refused"),
        TimeoutError("Request timed out"),
        ValueError("Invalid value"),
        Exception("Unknown error")
    ]
    
    for error in test_errors:
        category, severity = classifier.classify_error(error)
        print(f"  {type(error).__name__}: {category.value} / {severity.value}")
    
    # Test retry decorator
    print("\nTesting retry decorator...")
    
    @retry_on_error(RetryConfig(max_attempts=3, base_delay=0.1))
    def flaky_function(fail_count: int = 2):
        if not hasattr(flaky_function, 'attempts'):
            flaky_function.attempts = 0
        
        flaky_function.attempts += 1
        
        if flaky_function.attempts <= fail_count:
            raise ConnectionError(f"Simulated failure {flaky_function.attempts}")
        
        return f"Success after {flaky_function.attempts} attempts"
    
    try:
        result = flaky_function(2)
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Failed: {e}")
    
    # Test error tracker
    print("\nTesting error tracker...")
    tracker = ErrorTracker()
    
    # Simulate some errors
    for i in range(5):
        try:
            if i % 2 == 0:
                raise ConnectionError(f"Connection error {i}")
            else:
                raise ValueError(f"Value error {i}")
        except Exception as e:
            tracker.record_error(e, {'iteration': i})
    
    stats = tracker.get_error_statistics()
    print(f"  Error statistics: {stats}")
    
    # Test graceful error handler
    print("\nTesting graceful error handler...")
    handler = GracefulErrorHandler()
    
    # Register fallback handler
    def connection_fallback(error, context):
        return "Fallback connection established"
    
    handler.register_fallback_handler(ErrorCategory.CONNECTION, connection_fallback)
    
    # Test fallback
    try:
        raise ConnectionError("Connection failed")
    except Exception as e:
        result = handler.handle_error(e, {'test': True}, "Default result")
        print(f"  Fallback result: {result}")

if __name__ == "__main__":
    main()