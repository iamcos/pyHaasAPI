"""
HaasOnline API configuration and credentials management.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from urllib.parse import urlparse


@dataclass
class APIEndpoints:
    """HaasOnline API endpoint configurations."""
    # Script management endpoints
    get_script_record: str = "GetScriptRecord"
    execute_debugtest: str = "ExecuteDebugtest"
    execute_quicktest: str = "ExecuteQuicktest"
    
    # Backtest execution endpoints
    execute_backtest: str = "ExecuteBacktest"
    get_execution_update: str = "GetExecutionUpdate"
    execution_backtests: str = "ExecutionBacktests"
    
    # Results retrieval endpoints
    get_backtest_runtime: str = "GetBacktestRuntime"
    get_backtest_logs: str = "GetBacktestLogs"
    get_backtest_chart_partition: str = "GetBacktestChartPartition"
    
    # History management endpoints
    get_backtest_history: str = "GetBacktestHistory"
    archive_backtest: str = "ArchiveBacktest"
    delete_backtest: str = "DeleteBacktest"


@dataclass
class ConnectionConfig:
    """Connection configuration for HaasOnline API."""
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 5
    connection_pool_size: int = 10
    keep_alive: bool = True
    verify_ssl: bool = True


@dataclass
class RateLimitConfig:
    """Rate limiting configuration for API requests."""
    requests_per_second: int = 10
    burst_limit: int = 50
    backoff_factor: float = 1.5
    max_backoff_seconds: int = 300


@dataclass
class HaasOnlineConfig:
    """Configuration for HaasOnline API integration."""
    # Connection details
    server_url: str
    api_key: str
    api_secret: str
    
    # Optional authentication
    username: Optional[str] = None
    password: Optional[str] = None
    
    # API configuration
    endpoints: APIEndpoints = field(default_factory=APIEndpoints)
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    
    # Server-specific settings
    server_version: Optional[str] = None
    supported_features: list = field(default_factory=list)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
        self._normalize_server_url()
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.server_url:
            raise ValueError("server_url is required")
        
        if not self.api_key:
            raise ValueError("api_key is required")
        
        if not self.api_secret:
            raise ValueError("api_secret is required")
        
        # Validate URL format
        try:
            parsed = urlparse(self.server_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid server_url format")
        except Exception as e:
            raise ValueError(f"Invalid server_url: {e}")
        
        # Validate rate limiting
        if self.rate_limit.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        
        if self.connection.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
    
    def _normalize_server_url(self) -> None:
        """Normalize server URL format."""
        if not self.server_url.endswith('/'):
            self.server_url += '/'
        
        # Ensure HTTPS in production
        if not self.server_url.startswith(('http://', 'https://')):
            self.server_url = 'https://' + self.server_url
    
    @classmethod
    def from_env(cls) -> 'HaasOnlineConfig':
        """Create configuration from environment variables."""
        server_url = os.getenv('HAAS_SERVER_URL')
        api_key = os.getenv('HAAS_API_KEY')
        api_secret = os.getenv('HAAS_API_SECRET')
        
        if not all([server_url, api_key, api_secret]):
            raise ValueError("HAAS_SERVER_URL, HAAS_API_KEY, and HAAS_API_SECRET environment variables are required")
        
        config = cls(
            server_url=server_url,
            api_key=api_key,
            api_secret=api_secret,
            username=os.getenv('HAAS_USERNAME'),
            password=os.getenv('HAAS_PASSWORD'),
        )
        
        # Override connection settings from environment
        if timeout := os.getenv('HAAS_TIMEOUT'):
            config.connection.timeout_seconds = int(timeout)
        
        if max_retries := os.getenv('HAAS_MAX_RETRIES'):
            config.connection.max_retries = int(max_retries)
        
        if pool_size := os.getenv('HAAS_POOL_SIZE'):
            config.connection.connection_pool_size = int(pool_size)
        
        # Override rate limiting from environment
        if rps := os.getenv('HAAS_REQUESTS_PER_SECOND'):
            config.rate_limit.requests_per_second = int(rps)
        
        if burst := os.getenv('HAAS_BURST_LIMIT'):
            config.rate_limit.burst_limit = int(burst)
        
        return config
    
    @classmethod
    def from_file(cls, config_path: str) -> 'HaasOnlineConfig':
        """Load configuration from JSON file."""
        import json
        from pathlib import Path
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        return cls(**config_data)
    
    def get_api_url(self, endpoint: str) -> str:
        """Construct full API URL for an endpoint."""
        return f"{self.server_url}api/v1/{endpoint}"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers for API requests."""
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key,
            'X-API-Secret': self.api_secret,
        }
        
        if self.username:
            headers['X-Username'] = self.username
        
        return headers
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        config_dict = {
            'server_url': self.server_url,
            'username': self.username,
            'server_version': self.server_version,
            'supported_features': self.supported_features,
            'connection': {
                'timeout_seconds': self.connection.timeout_seconds,
                'max_retries': self.connection.max_retries,
                'retry_delay_seconds': self.connection.retry_delay_seconds,
                'connection_pool_size': self.connection.connection_pool_size,
                'keep_alive': self.connection.keep_alive,
                'verify_ssl': self.connection.verify_ssl,
            },
            'rate_limit': {
                'requests_per_second': self.rate_limit.requests_per_second,
                'burst_limit': self.rate_limit.burst_limit,
                'backoff_factor': self.rate_limit.backoff_factor,
                'max_backoff_seconds': self.rate_limit.max_backoff_seconds,
            }
        }
        
        if include_secrets:
            config_dict.update({
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                'password': self.password,
            })
        else:
            config_dict.update({
                'api_key': '***' if self.api_key else None,
                'api_secret': '***' if self.api_secret else None,
                'password': '***' if self.password else None,
            })
        
        return config_dict
    
    def test_connection(self) -> bool:
        """Test connection to HaasOnline server."""
        # This would be implemented with actual HTTP request
        # For now, just validate configuration
        try:
            self._validate_config()
            return True
        except Exception:
            return False