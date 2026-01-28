"""
API configuration settings
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict
from .env_utils import get_env
from .logging_config import LoggingConfig

@dataclass
class APIConfig:
    """API connection and authentication configuration"""
    
    # Connection settings
    host: str = field(default_factory=lambda: get_env("API_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: get_env("API_PORT", 8090, int))
    protocol: str = field(default_factory=lambda: get_env("API_PROTOCOL", "http"))
    base_url: Optional[str] = field(default_factory=lambda: get_env("API_BASE_URL", None))
    server_name: Optional[str] = None
    
    # Authentication
    email: Optional[str] = field(default_factory=lambda: get_env("API_EMAIL", None))
    password: Optional[str] = field(default_factory=lambda: get_env("API_PASSWORD", None))
    
    # Connection settings
    timeout: float = field(default_factory=lambda: get_env("API_TIMEOUT", 30.0, float))
    max_retries: int = field(default_factory=lambda: get_env("API_MAX_RETRIES", 3, int))
    retry_delay: float = field(default_factory=lambda: get_env("API_RETRY_DELAY", 1.0, float))
    retry_backoff_factor: float = field(default_factory=lambda: get_env("API_RETRY_BACKOFF", 2.0, float))
    
    # Rate limiting
    rate_limit_requests: int = field(default_factory=lambda: get_env("API_RATE_LIMIT_REQUESTS", 100, int))
    rate_limit_window: int = field(default_factory=lambda: get_env("API_RATE_LIMIT_WINDOW", 60, int))
    
    # SSL/TLS
    verify_ssl: bool = field(default_factory=lambda: get_env("API_VERIFY_SSL", True, bool))
    ssl_cert_path: Optional[str] = field(default_factory=lambda: get_env("API_SSL_CERT_PATH", None))
    ssl_key_path: Optional[str] = field(default_factory=lambda: get_env("API_SSL_KEY_PATH", None))
    
    # Connection pooling
    max_connections: int = field(default_factory=lambda: get_env("API_MAX_CONNECTIONS", 100, int))
    max_keepalive_connections: int = field(default_factory=lambda: get_env("API_MAX_KEEPALIVE", 20, int))
    keepalive_timeout: float = field(default_factory=lambda: get_env("API_KEEPALIVE_TIMEOUT", 30.0, float))
    
    # Logging configuration
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def __post_init__(self):
        """Validate configuration"""
        self.validate_port()
        self.validate_timeout()
        self.validate_max_retries()
        self.validate_protocol()
        # Logging config is initialized in default_factory, no need to validate here if it validates itself
        
    def validate_port(self):
        if not 1 <= self.port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
            
    def validate_timeout(self):
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
            
    def validate_max_retries(self):
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
            
    def validate_protocol(self):
        valid_protocols = ["http", "https"]
        if self.protocol.lower() not in valid_protocols:
            raise ValueError(f"Protocol must be one of: {valid_protocols}")
        self.protocol = self.protocol.lower()

    @property
    def full_url(self) -> str:
        """Get full API URL"""
        if self.base_url:
            return self.base_url
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authentication credentials are provided"""
        return bool(self.email and self.password)
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.is_authenticated:
            return {}
        return {
            "X-Email": self.email or "",
            "X-Password": self.password or ""
        }
