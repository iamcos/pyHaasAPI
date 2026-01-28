"""
Logging configuration settings
"""
import os
from dataclasses import dataclass, field
from typing import List
from .env_utils import get_env

@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    
    # Log level
    level: str = field(default_factory=lambda: get_env("LOG_LEVEL", "INFO"))
    
    # Log format
    format: str = field(default_factory=lambda: get_env(
        "LOG_FORMAT",
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    ))
    
    # Output destinations
    console_enabled: bool = field(default_factory=lambda: get_env("LOG_CONSOLE_ENABLED", True, bool))
    file_enabled: bool = field(default_factory=lambda: get_env("LOG_FILE_ENABLED", True, bool))
    
    # File logging
    file_path: str = field(default_factory=lambda: get_env("LOG_FILE_PATH", "logs/pyhaasapi.log"))
    file_rotation: str = field(default_factory=lambda: get_env("LOG_FILE_ROTATION", "1 day"))
    file_retention: str = field(default_factory=lambda: get_env("LOG_FILE_RETENTION", "30 days"))
    file_compression: str = field(default_factory=lambda: get_env("LOG_FILE_COMPRESSION", "gz"))
    
    # Request/response logging
    log_requests: bool = field(default_factory=lambda: get_env("LOG_REQUESTS", True, bool))
    log_responses: bool = field(default_factory=lambda: get_env("LOG_RESPONSES", False, bool))
    log_request_body: bool = field(default_factory=lambda: get_env("LOG_REQUEST_BODY", False, bool))
    log_response_body: bool = field(default_factory=lambda: get_env("LOG_RESPONSE_BODY", False, bool))
    
    # Performance logging
    log_performance: bool = field(default_factory=lambda: get_env("LOG_PERFORMANCE", True, bool))
    slow_request_threshold: float = field(default_factory=lambda: get_env("LOG_SLOW_REQUEST_THRESHOLD", 1.0, float))
    
    # Error tracking
    log_errors: bool = field(default_factory=lambda: get_env("LOG_ERRORS", True, bool))
    log_stack_traces: bool = field(default_factory=lambda: get_env("LOG_STACK_TRACES", True, bool))
    
    # Module-specific logging
    modules: List[str] = field(default_factory=lambda: get_env("LOG_MODULES", ["pyhaasapi", "aiohttp", "asyncio"], list))
    
    # Structured logging
    structured: bool = field(default_factory=lambda: get_env("LOG_STRUCTURED", True, bool))
    json_format: bool = field(default_factory=lambda: get_env("LOG_JSON_FORMAT", False, bool))
    
    def __post_init__(self):
        """Validate configuration"""
        self.validate_level()
        self.validate_rotation()
        self.validate_retention()
        self.validate_slow_request_threshold()
        # Modules is validated by type hint implicitly via helper, but we check list type
        if not isinstance(self.modules, list):
             # basic fallback if get_env failed to allow list casting
             self.modules = []
             
    def validate_level(self):
        valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        self.level = self.level.upper()
        
    def validate_rotation(self):
        if not self.file_rotation or not isinstance(self.file_rotation, str):
            raise ValueError("File rotation must be a string")
            
    def validate_retention(self):
        if not self.file_retention or not isinstance(self.file_retention, str):
            raise ValueError("File retention must be a string")
            
    def validate_slow_request_threshold(self):
        if self.slow_request_threshold < 0:
            raise ValueError("Slow request threshold must be non-negative")
            
    @property
    def is_debug(self) -> bool:
        """Check if debug logging is enabled"""
        return self.level in ["DEBUG", "TRACE"]
    
    @property
    def is_verbose(self) -> bool:
        """Check if verbose logging is enabled"""
        return self.level in ["DEBUG", "TRACE", "INFO"]
    
    def get_log_format(self) -> str:
        """Get log format based on configuration"""
        if self.json_format:
            return '{"time": "{time:YYYY-MM-DD HH:mm:ss}", "level": "{level}", "name": "{name}", "function": "{function}", "line": {line}, "message": "{message}"}'
        return self.format
    
    def should_log_module(self, module_name: str) -> bool:
        """Check if module should be logged"""
        if not self.modules:
            return True
        
        module_name_lower = module_name.lower()
        for module in self.modules:
            if module_name_lower.startswith(module.lower()):
                return True
        return False
