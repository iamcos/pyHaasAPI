"""
Logging configuration settings for pyHaasAPI v2
"""

from typing import Optional, List, Set
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseSettings):
    """Logging configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="LOG_",
    )
    
    # Logging enablement
    console_enabled: bool = Field(default=True, env="LOG_CONSOLE_ENABLED")
    file_enabled: bool = Field(default=True, env="LOG_FILE_ENABLED")
    
    # Log level
    level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # File logging settings
    file_path: str = Field(default="logs/pyhaasapi.log", env="LOG_FILE_PATH")
    file_rotation: str = Field(default="10 MB", env="LOG_FILE_ROTATION")
    file_retention: str = Field(default="30 days", env="LOG_FILE_RETENTION")
    file_compression: Optional[str] = Field(default="gz", env="LOG_FILE_COMPRESSION")
    
    # Request/response logging
    log_requests: bool = Field(default=True, env="LOG_REQUESTS")
    log_responses: bool = Field(default=True, env="LOG_RESPONSES")
    log_request_body: bool = Field(default=False, env="LOG_REQUEST_BODY")
    log_response_body: bool = Field(default=False, env="LOG_RESPONSE_BODY")
    
    # Performance logging
    log_performance: bool = Field(default=True, env="LOG_PERFORMANCE")
    slow_request_threshold: float = Field(default=1.0, env="LOG_SLOW_REQUEST_THRESHOLD")  # seconds
    
    # Error logging
    log_errors: bool = Field(default=True, env="LOG_ERRORS")
    
    # Module filtering
    enabled_modules: Optional[List[str]] = Field(default=None, env="LOG_ENABLED_MODULES")
    disabled_modules: Optional[List[str]] = Field(default=None, env="LOG_DISABLED_MODULES")
    
    # Log format
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name: <20} | {message}",
        env="LOG_FORMAT"
    )
    
    @field_validator("level")
    @classmethod
    def validate_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("slow_request_threshold")
    @classmethod
    def validate_threshold(cls, v):
        """Validate slow request threshold"""
        if v < 0:
            raise ValueError("Slow request threshold must be non-negative")
        return v
    
    def get_log_format(self) -> str:
        """Get log format string"""
        return self.format
    
    def should_log_module(self, module_name: str) -> bool:
        """
        Check if a module should be logged
        
        Args:
            module_name: Name of the module
            
        Returns:
            True if module should be logged, False otherwise
        """
        # If enabled_modules is specified, only log those modules
        if self.enabled_modules:
            return any(module_name.startswith(mod) for mod in self.enabled_modules)
        
        # If disabled_modules is specified, exclude those modules
        if self.disabled_modules:
            return not any(module_name.startswith(mod) for mod in self.disabled_modules)
        
        # Default: log everything
        return True
    
    @property
    def log_file_path(self) -> Path:
        """Get log file path as Path object"""
        return Path(self.file_path)

