"""
API configuration settings
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from .logging_config import LoggingConfig


class APIConfig(BaseSettings):
    """API connection and authentication configuration"""
    
    # Pydantic v2 settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Connection settings (mandated tunnel only)
    host: str = Field(default="127.0.0.1", env="API_HOST")
    port: int = Field(default=8090, env="API_PORT") 
    protocol: str = Field(default="http", env="API_PROTOCOL")
    base_url: Optional[str] = Field(default=None, env="API_BASE_URL")
    
    # Authentication
    email: Optional[str] = Field(default=None, env="API_EMAIL")
    password: Optional[str] = Field(default=None, env="API_PASSWORD")
    
    # Connection settings
    timeout: float = Field(default=30.0, env="API_TIMEOUT")
    max_retries: int = Field(default=3, env="API_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="API_RETRY_DELAY")
    retry_backoff_factor: float = Field(default=2.0, env="API_RETRY_BACKOFF")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, env="API_RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="API_RATE_LIMIT_WINDOW")
    
    # SSL/TLS
    verify_ssl: bool = Field(default=True, env="API_VERIFY_SSL")
    ssl_cert_path: Optional[str] = Field(default=None, env="API_SSL_CERT_PATH")
    ssl_key_path: Optional[str] = Field(default=None, env="API_SSL_KEY_PATH")
    
    # Connection pooling
    max_connections: int = Field(default=100, env="API_MAX_CONNECTIONS")
    max_keepalive_connections: int = Field(default=20, env="API_MAX_KEEPALIVE")
    keepalive_timeout: float = Field(default=30.0, env="API_KEEPALIVE_TIMEOUT")
    
    # Logging configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # NOTE: Field-level env bindings are optional; env_nested_delimiter is handled by parent Settings
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate port number"""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value"""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v
    
    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v):
        """Validate max retries"""
        if v < 0:
            raise ValueError("Max retries must be non-negative")
        return v
    
    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v):
        """Validate protocol"""
        valid_protocols = ["http", "https"]
        if v.lower() not in valid_protocols:
            raise ValueError(f"Protocol must be one of: {valid_protocols}")
        return v.lower()
    
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
    
    def get_auth_headers(self) -> dict:
        """Get authentication headers"""
        if not self.is_authenticated:
            return {}
        return {
            "X-Email": self.email,
            "X-Password": self.password
        }
