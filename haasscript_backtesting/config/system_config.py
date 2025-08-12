"""
System-wide configuration settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from pathlib import Path


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 100
    backup_count: int = 5
    console_output: bool = True


@dataclass
class ExecutionConfig:
    """Execution and performance configuration."""
    max_concurrent_backtests: int = 5
    default_timeout_seconds: int = 3600  # 1 hour
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    resource_monitoring_interval: int = 60  # seconds
    cleanup_interval_hours: int = 24


@dataclass
class CacheConfig:
    """Caching configuration settings."""
    enabled: bool = True
    ttl_seconds: int = 3600  # 1 hour
    max_size_mb: int = 500
    cache_directory: str = ".cache"


@dataclass
class SecurityConfig:
    """Security and authentication settings."""
    api_key_encryption: bool = True
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    require_https: bool = True
    allowed_hosts: list = field(default_factory=list)


@dataclass
class SystemConfig:
    """Main system configuration container."""
    # Environment settings
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Component configurations
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Directory paths
    data_directory: str = "data"
    logs_directory: str = "logs"
    temp_directory: str = "temp"
    
    # Feature flags
    enable_mcp_server: bool = True
    enable_rag_system: bool = True
    enable_optimization: bool = True
    enable_monitoring: bool = True
    
    def __post_init__(self):
        """Initialize configuration after creation."""
        self._create_directories()
        self._validate_config()
    
    def _create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_directory,
            self.logs_directory, 
            self.temp_directory,
            self.cache.cache_directory
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self) -> None:
        """Validate configuration settings."""
        if self.execution.max_concurrent_backtests <= 0:
            raise ValueError("max_concurrent_backtests must be positive")
        
        if self.execution.default_timeout_seconds <= 0:
            raise ValueError("default_timeout_seconds must be positive")
        
        if self.cache.max_size_mb <= 0:
            raise ValueError("cache max_size_mb must be positive")
    
    @classmethod
    def from_env(cls) -> 'SystemConfig':
        """Create configuration from environment variables."""
        config = cls()
        
        # Override with environment variables
        config.environment = os.getenv('HAAS_ENVIRONMENT', config.environment)
        config.debug = os.getenv('HAAS_DEBUG', 'false').lower() == 'true'
        
        # Execution settings
        if max_concurrent := os.getenv('HAAS_MAX_CONCURRENT_BACKTESTS'):
            config.execution.max_concurrent_backtests = int(max_concurrent)
        
        if timeout := os.getenv('HAAS_DEFAULT_TIMEOUT'):
            config.execution.default_timeout_seconds = int(timeout)
        
        # Logging settings
        config.logging.level = os.getenv('HAAS_LOG_LEVEL', config.logging.level)
        config.logging.file_path = os.getenv('HAAS_LOG_FILE', config.logging.file_path)
        
        # Directory paths
        config.data_directory = os.getenv('HAAS_DATA_DIR', config.data_directory)
        config.logs_directory = os.getenv('HAAS_LOGS_DIR', config.logs_directory)
        config.temp_directory = os.getenv('HAAS_TEMP_DIR', config.temp_directory)
        
        # Feature flags
        config.enable_mcp_server = os.getenv('HAAS_ENABLE_MCP', 'true').lower() == 'true'
        config.enable_rag_system = os.getenv('HAAS_ENABLE_RAG', 'true').lower() == 'true'
        config.enable_optimization = os.getenv('HAAS_ENABLE_OPTIMIZATION', 'true').lower() == 'true'
        config.enable_monitoring = os.getenv('HAAS_ENABLE_MONITORING', 'true').lower() == 'true'
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_file_size_mb': self.logging.max_file_size_mb,
                'backup_count': self.logging.backup_count,
                'console_output': self.logging.console_output,
            },
            'execution': {
                'max_concurrent_backtests': self.execution.max_concurrent_backtests,
                'default_timeout_seconds': self.execution.default_timeout_seconds,
                'retry_attempts': self.execution.retry_attempts,
                'retry_delay_seconds': self.execution.retry_delay_seconds,
                'resource_monitoring_interval': self.execution.resource_monitoring_interval,
                'cleanup_interval_hours': self.execution.cleanup_interval_hours,
            },
            'cache': {
                'enabled': self.cache.enabled,
                'ttl_seconds': self.cache.ttl_seconds,
                'max_size_mb': self.cache.max_size_mb,
                'cache_directory': self.cache.cache_directory,
            },
            'security': {
                'api_key_encryption': self.security.api_key_encryption,
                'session_timeout_minutes': self.security.session_timeout_minutes,
                'max_login_attempts': self.security.max_login_attempts,
                'require_https': self.security.require_https,
                'allowed_hosts': self.security.allowed_hosts,
            },
            'directories': {
                'data': self.data_directory,
                'logs': self.logs_directory,
                'temp': self.temp_directory,
            },
            'features': {
                'mcp_server': self.enable_mcp_server,
                'rag_system': self.enable_rag_system,
                'optimization': self.enable_optimization,
                'monitoring': self.enable_monitoring,
            }
        }