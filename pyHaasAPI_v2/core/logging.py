"""
Structured logging system for pyHaasAPI v2

Provides comprehensive logging with loguru, including request/response logging,
performance monitoring, and error tracking.
"""

import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from contextlib import asynccontextmanager
from functools import wraps

from loguru import logger
from loguru._logger import Logger

from ..config.logging_config import LoggingConfig
from ..exceptions import ConfigurationError


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """
    Setup structured logging with loguru
    
    Args:
        config: Logging configuration. If None, uses default config.
    """
    if config is None:
        from ..config import LoggingConfig
        config = LoggingConfig()
    
    # Remove default handler
    logger.remove()
    
    # Console logging
    if config.console_enabled:
        logger.add(
            sys.stdout,
            level=config.level,
            format=config.get_log_format(),
            filter=lambda record: config.should_log_module(record["name"]),
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    # File logging
    if config.file_enabled:
        # Ensure log directory exists
        log_path = Path(config.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            config.file_path,
            level=config.level,
            format=config.get_log_format(),
            filter=lambda record: config.should_log_module(record["name"]),
            rotation=config.file_rotation,
            retention=config.file_retention,
            compression=config.file_compression,
            backtrace=True,
            diagnose=True
        )
    
    # Configure loguru settings
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout if config.console_enabled else None,
                "level": config.level,
                "format": config.get_log_format(),
                "colorize": config.console_enabled,
            }
        ]
    )


def get_logger(name: str) -> Logger:
    """
    Get logger instance for a module
    
    Args:
        name: Module name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)


class RequestLogger:
    """Request/response logging utility"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.logger = get_logger("request")
    
    def log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        **kwargs
    ) -> None:
        """Log outgoing request"""
        if not self.config.log_requests:
            return
        
        log_data = {
            "type": "request",
            "method": method,
            "url": url,
            "headers": self._sanitize_headers(headers) if headers else None,
        }
        
        if self.config.log_request_body and body is not None:
            log_data["body"] = self._sanitize_body(body)
        
        self.logger.info("API Request", extra=log_data)
    
    def log_response(
        self,
        method: str,
        url: str,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        duration: Optional[float] = None,
        **kwargs
    ) -> None:
        """Log incoming response"""
        if not self.config.log_responses:
            return
        
        log_data = {
            "type": "response",
            "method": method,
            "url": url,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2) if duration else None,
        }
        
        if self.config.log_response_body and body is not None:
            log_data["body"] = self._sanitize_body(body)
        
        # Log level based on status code
        if status_code >= 500:
            self.logger.error("API Response", extra=log_data)
        elif status_code >= 400:
            self.logger.warning("API Response", extra=log_data)
        else:
            self.logger.info("API Response", extra=log_data)
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize headers by removing sensitive information"""
        sensitive_headers = {"authorization", "x-api-key", "x-auth-token", "cookie"}
        return {
            k: "***" if k.lower() in sensitive_headers else v
            for k, v in headers.items()
        }
    
    def _sanitize_body(self, body: Any) -> Any:
        """Sanitize request/response body"""
        if isinstance(body, (dict, list)):
            return self._remove_sensitive_fields(body)
        return str(body)[:1000]  # Truncate long strings
    
    def _remove_sensitive_fields(self, data: Any) -> Any:
        """Remove sensitive fields from data"""
        if isinstance(data, dict):
            sensitive_fields = {"password", "token", "secret", "key", "auth"}
            return {
                k: "***" if any(sensitive in k.lower() for sensitive in sensitive_fields) else v
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._remove_sensitive_fields(item) for item in data]
        return data


class PerformanceLogger:
    """Performance monitoring utility"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.logger = get_logger("performance")
    
    @asynccontextmanager
    async def measure_operation(self, operation_name: str, **context):
        """Context manager for measuring operation performance"""
        start_time = time.time()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            log_data = {
                "operation": operation_name,
                "duration_ms": round(duration * 1000, 2),
                "context": context,
            }
            
            if duration > self.config.slow_request_threshold:
                self.logger.warning(f"Slow operation: {operation_name}", extra=log_data)
            else:
                self.logger.info(f"Operation completed: {operation_name}", extra=log_data)
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: Union[int, float],
        unit: str = "ms",
        **context
    ) -> None:
        """Log a performance metric"""
        if not self.config.log_performance:
            return
        
        log_data = {
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "context": context,
        }
        
        self.logger.info(f"Performance metric: {metric_name}", extra=log_data)


class ErrorLogger:
    """Error tracking and logging utility"""
    
    def __init__(self, config: LoggingConfig):
        self.config = config
        self.logger = get_logger("error")
    
    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log an error with context"""
        if not self.config.log_errors:
            return
        
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }
        
        if self.config.log_stack_traces:
            import traceback
            log_data["stack_trace"] = traceback.format_exc()
        
        self.logger.error(f"Error occurred: {type(error).__name__}", extra=log_data)
    
    def log_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log a warning with context"""
        log_data = {
            "warning_message": message,
            "context": context or {},
        }
        
        self.logger.warning(f"Warning: {message}", extra=log_data)


def log_function_call(func):
    """Decorator to log function calls"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__}", extra={"args": str(args)[:200], "kwargs": str(kwargs)[:200]})
        
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__}", extra={"args": str(args)[:200], "kwargs": str(kwargs)[:200]})
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class LoggingManager:
    """Centralized logging management"""
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        if config is None:
            from ..config import LoggingConfig
            config = LoggingConfig()
        
        self.config = config
        self.request_logger = RequestLogger(config)
        self.performance_logger = PerformanceLogger(config)
        self.error_logger = ErrorLogger(config)
    
    def get_logger(self, name: str) -> Logger:
        """Get logger for a module"""
        return get_logger(name)
    
    def setup(self) -> None:
        """Setup logging system"""
        setup_logging(self.config)
    
    def log_request(self, **kwargs) -> None:
        """Log API request"""
        self.request_logger.log_request(**kwargs)
    
    def log_response(self, **kwargs) -> None:
        """Log API response"""
        self.request_logger.log_response(**kwargs)
    
    def log_error(self, error: Exception, **kwargs) -> None:
        """Log error"""
        self.error_logger.log_error(error, **kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning"""
        self.error_logger.log_warning(message, **kwargs)
    
    async def measure_operation(self, operation_name: str, **context):
        """Measure operation performance"""
        return self.performance_logger.measure_operation(operation_name, **context)


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """Get global logging manager instance"""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def initialize_logging(config: Optional[LoggingConfig] = None) -> LoggingManager:
    """Initialize logging system"""
    global _logging_manager
    _logging_manager = LoggingManager(config)
    _logging_manager.setup()
    return _logging_manager
