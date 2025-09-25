"""
Logging configuration settings
"""

from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class LoggingConfig(BaseSettings):
    """Logging configuration settings"""
    
    # Log level
    level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Log format
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        env="LOG_FORMAT"
    )
    
    # Output destinations
    console_enabled: bool = Field(default=True, env="LOG_CONSOLE_ENABLED")
    file_enabled: bool = Field(default=True, env="LOG_FILE_ENABLED")
    
    # File logging
    file_path: str = Field(default="logs/pyhaasapi.log", env="LOG_FILE_PATH")
    file_rotation: str = Field(default="1 day", env="LOG_FILE_ROTATION")
    file_retention: str = Field(default="30 days", env="LOG_FILE_RETENTION")
    file_compression: str = Field(default="gz", env="LOG_FILE_COMPRESSION")
    
    # Request/response logging
    log_requests: bool = Field(default=True, env="LOG_REQUESTS")
    log_responses: bool = Field(default=False, env="LOG_RESPONSES")
    log_request_body: bool = Field(default=False, env="LOG_REQUEST_BODY")
    log_response_body: bool = Field(default=False, env="LOG_RESPONSE_BODY")
    
    # Performance logging
    log_performance: bool = Field(default=True, env="LOG_PERFORMANCE")
    slow_request_threshold: float = Field(default=1.0, env="LOG_SLOW_REQUEST_THRESHOLD")
    
    # Error tracking
    log_errors: bool = Field(default=True, env="LOG_ERRORS")
    log_stack_traces: bool = Field(default=True, env="LOG_STACK_TRACES")
    
    # Module-specific logging
    modules: List[str] = Field(
        default=["pyhaasapi", "aiohttp", "asyncio"],
        env="LOG_MODULES"
    )
    
    # Structured logging
    structured: bool = Field(default=True, env="LOG_STRUCTURED")
    json_format: bool = Field(default=False, env="LOG_JSON_FORMAT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"    
    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        """Validate log level"""
        valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("file_rotation")
    @classmethod
    def validate_rotation(cls, v):
        """Validate file rotation setting"""
        # Basic validation - should be in format like "1 day", "1 week", etc.
        if not v or not isinstance(v, str):
            raise ValueError("File rotation must be a string")
        return v
    
    @field_validator("file_retention")
    @classmethod
    def validate_retention(cls, v):
        """Validate file retention setting"""
        if not v or not isinstance(v, str):
            raise ValueError("File retention must be a string")
        return v
    
    @field_validator("slow_request_threshold")
    @classmethod
    def validate_slow_request_threshold(cls, v):
        """Validate slow request threshold"""
        if v < 0:
            raise ValueError("Slow request threshold must be non-negative")
        return v
    
    @field_validator("modules")
    @classmethod
    def validate_modules(cls, v):
        """Validate log modules"""
        if not isinstance(v, list):
            raise ValueError("Modules must be a list")
        return v
    
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
        
        for module in self.modules:
            if module_name.startswith(module):
                return True
        return False
