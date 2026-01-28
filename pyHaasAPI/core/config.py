"""
Configuration management for pyHaasAPI v2

Provides centralized configuration with environment variable support,
validation, and type safety using standard Python dataclasses.
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Application settings with environment variable support"""
    
    # API Configuration
    api_host: str = field(default="127.0.0.1")
    api_port: int = field(default=8090)
    api_email: Optional[str] = field(default=None)
    api_password: Optional[str] = field(default=None)
    
    # Connection Settings
    connection_timeout: int = field(default=30)
    request_timeout: int = field(default=60)
    max_retries: int = field(default=3)
    retry_delay: float = field(default=1.0)
    
    # Cache Configuration
    cache_enabled: bool = field(default=True)
    cache_dir: str = field(default="unified_cache")
    cache_ttl: int = field(default=3600)  # 1 hour
    
    # Logging Configuration
    log_level: str = field(default="INFO")
    log_file: Optional[str] = field(default=None)
    log_format: str = field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Analysis Configuration
    default_top_count: int = field(default=5)
    max_backtests_per_lab: int = field(default=1000)
    analysis_timeout: int = field(default=300)  # 5 minutes
    
    # Bot Configuration
    default_trade_amount_usdt: float = field(default=2000.0)
    default_leverage: float = field(default=20.0)
    default_margin_mode: str = field(default="CROSS")
    default_position_mode: str = field(default="HEDGE")
    
    # Report Configuration
    report_output_dir: str = field(default="reports")
    report_formats: List[str] = field(default_factory=lambda: ["json", "csv"])
    include_bot_recommendations: bool = field(default=True)
    
    # Performance Configuration
    enable_async: bool = field(default=True)
    max_concurrent_requests: int = field(default=10)
    connection_pool_size: int = field(default=20)
    
    def __post_init__(self):
        """Load from environment variables and validate"""
        # API Configuration
        self.api_host = os.getenv("API_HOST", self.api_host)
        self.api_port = int(os.getenv("API_PORT", str(self.api_port)))
        self.api_email = os.getenv("API_EMAIL", self.api_email)
        self.api_password = os.getenv("API_PASSWORD", self.api_password)
        
        # Connection Settings
        self.connection_timeout = int(os.getenv("CONNECTION_TIMEOUT", str(self.connection_timeout)))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", str(self.request_timeout)))
        self.max_retries = int(os.getenv("MAX_RETRIES", str(self.max_retries)))
        self.retry_delay = float(os.getenv("RETRY_DELAY", str(self.retry_delay)))
        
        # Cache Configuration
        self.cache_enabled = os.getenv("CACHE_ENABLED", str(self.cache_enabled)).lower() == "true"
        self.cache_dir = os.getenv("CACHE_DIR", self.cache_dir)
        self.cache_ttl = int(os.getenv("CACHE_TTL", str(self.cache_ttl)))
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", self.log_level).upper()
        self.log_file = os.getenv("LOG_FILE", self.log_file)
        self.log_format = os.getenv("LOG_FORMAT", self.log_format)
        
        # Analysis Configuration
        self.default_top_count = int(os.getenv("DEFAULT_TOP_COUNT", str(self.default_top_count)))
        self.max_backtests_per_lab = int(os.getenv("MAX_BACKTESTS_PER_LAB", str(self.max_backtests_per_lab)))
        self.analysis_timeout = int(os.getenv("ANALYSIS_TIMEOUT", str(self.analysis_timeout)))
        
        # Bot Configuration
        self.default_trade_amount_usdt = float(os.getenv("DEFAULT_TRADE_AMOUNT_USDT", str(self.default_trade_amount_usdt)))
        self.default_leverage = float(os.getenv("DEFAULT_LEVERAGE", str(self.default_leverage)))
        self.default_margin_mode = os.getenv("DEFAULT_MARGIN_MODE", self.default_margin_mode).upper()
        self.default_position_mode = os.getenv("DEFAULT_POSITION_MODE", self.default_position_mode).upper()
        
        # Report Configuration
        self.report_output_dir = os.getenv("REPORT_OUTPUT_DIR", self.report_output_dir)
        formats_env = os.getenv("REPORT_FORMATS")
        if formats_env:
            self.report_formats = [f.strip().lower() for f in formats_env.split(",")]
            
        self.include_bot_recommendations = os.getenv("INCLUDE_BOT_RECOMMENDATIONS", str(self.include_bot_recommendations)).lower() == "true"
        
        # Performance Configuration
        self.enable_async = os.getenv("ENABLE_ASYNC", str(self.enable_async)).lower() == "true"
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", str(self.max_concurrent_requests)))
        self.connection_pool_size = int(os.getenv("CONNECTION_POOL_SIZE", str(self.connection_pool_size)))

        # Validation
        self.validate()

    def validate(self):
        """Validate settings"""
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_log_levels:
            raise ValueError(f'log_level must be one of {valid_log_levels}')
            
        valid_formats = ['json', 'csv', 'markdown', 'html', 'txt']
        for format_type in self.report_formats:
            if format_type not in valid_formats:
                 # Warn or default? Let's error to match previous behavior strictness
                 raise ValueError(f'Invalid report format: {format_type}. Must be one of {valid_formats}')
        
        valid_margin_modes = ['CROSS', 'ISOLATED']
        if self.default_margin_mode not in valid_margin_modes:
            raise ValueError(f'margin_mode must be one of {valid_margin_modes}')
            
        valid_position_modes = ['HEDGE', 'ONE_WAY']
        if self.default_position_mode not in valid_position_modes:
            raise ValueError(f'position_mode must be one of {valid_position_modes}')


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment"""
    global settings
    settings = Settings()
    return settings

