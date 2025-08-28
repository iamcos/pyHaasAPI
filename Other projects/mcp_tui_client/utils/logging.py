"""
Logging utilities for MCP TUI Client

Provides structured logging setup and configuration with JSON format support.
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime
import traceback


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Set up structured logging for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_format: Use JSON format for structured logging
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
        context: Global context to add to all log messages
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if json_format:
        console_formatter = JSONFormatter()
        file_formatter = JSONFormatter()
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add context filter if provided
    if context:
        console_handler.addFilter(ContextFilter(context))
    
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Add context filter if provided
        if context:
            file_handler.addFilter(ContextFilter(context))
        
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels to reduce noise
    logging.getLogger("textual").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)


class StructuredLogger:
    """Structured logger with context support and performance tracking"""
    
    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def with_context(self, **kwargs) -> 'StructuredLogger':
        """Add context to logger"""
        new_context = {**self.context, **kwargs}
        return StructuredLogger(self.logger.name, new_context)
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """Log message with context"""
        # Merge context with additional kwargs
        log_context = {**self.context, **kwargs}
        
        # Create log record with extra fields
        extra = {f"ctx_{k}": v for k, v in log_context.items()}
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback"""
        log_context = {**self.context, **kwargs}
        extra = {f"ctx_{k}": v for k, v in log_context.items()}
        self.logger.exception(message, extra=extra)


class PerformanceLogger:
    """Logger for performance monitoring and metrics"""
    
    def __init__(self, name: str):
        self.logger = StructuredLogger(f"{name}.performance")
        self._timers: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation"""
        import time
        self._timers[operation] = time.time()
        self.logger.debug(f"Started timing: {operation}")
    
    def end_timer(self, operation: str, **context) -> float:
        """End timing an operation and log duration"""
        import time
        if operation not in self._timers:
            self.logger.warning(f"Timer not found for operation: {operation}")
            return 0.0
        
        duration = time.time() - self._timers[operation]
        del self._timers[operation]
        
        self.logger.info(
            f"Operation completed: {operation}",
            duration_ms=duration * 1000,
            operation=operation,
            **context
        )
        
        return duration
    
    def log_metric(self, metric_name: str, value: Union[int, float], **context) -> None:
        """Log a performance metric"""
        self.logger.info(
            f"Metric: {metric_name}",
            metric_name=metric_name,
            metric_value=value,
            **context
        )
    
    def log_counter(self, counter_name: str, increment: int = 1, **context) -> None:
        """Log a counter increment"""
        self.logger.info(
            f"Counter: {counter_name}",
            counter_name=counter_name,
            increment=increment,
            **context
        )


class AuditLogger:
    """Logger for audit trail and security events"""
    
    def __init__(self, name: str):
        self.logger = StructuredLogger(f"{name}.audit")
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str = "success",
        **context
    ) -> None:
        """Log user action for audit trail"""
        self.logger.info(
            f"User action: {action}",
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            event_type="user_action",
            **context
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        **context
    ) -> None:
        """Log security event"""
        self.logger.warning(
            f"Security event: {event_type}",
            event_type=event_type,
            severity=severity,
            description=description,
            security_event=True,
            **context
        )
    
    def log_system_event(
        self,
        event_type: str,
        description: str,
        **context
    ) -> None:
        """Log system event"""
        self.logger.info(
            f"System event: {event_type}",
            event_type=event_type,
            description=description,
            system_event=True,
            **context
        )


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name, context)


def get_performance_logger(name: str) -> PerformanceLogger:
    """Get a performance logger instance"""
    return PerformanceLogger(name)


def get_audit_logger(name: str) -> AuditLogger:
    """Get an audit logger instance"""
    return AuditLogger(name)


# Context manager for timing operations
class timer:
    """Context manager for timing operations"""
    
    def __init__(self, logger: PerformanceLogger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
    
    def __enter__(self):
        self.logger.start_timer(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = self.logger.end_timer(self.operation, **self.context)
        if exc_type:
            self.logger.logger.error(
                f"Operation failed: {self.operation}",
                duration_ms=duration * 1000,
                operation=self.operation,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                **self.context
            )