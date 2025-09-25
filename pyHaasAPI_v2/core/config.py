"""
Configuration management for pyHaasAPI v2

Provides centralized configuration with environment variable support,
validation, and type safety using Pydantic.
"""

import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    api_host: str = Field(default="127.0.0.1", env="API_HOST")
    api_port: int = Field(default=8090, env="API_PORT")
    api_email: Optional[str] = Field(default=None, env="API_EMAIL")
    api_password: Optional[str] = Field(default=None, env="API_PASSWORD")
    
    # Connection Settings
    connection_timeout: int = Field(default=30, env="CONNECTION_TIMEOUT")
    request_timeout: int = Field(default=60, env="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: float = Field(default=1.0, env="RETRY_DELAY")
    
    # Cache Configuration
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_dir: str = Field(default="unified_cache", env="CACHE_DIR")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # Analysis Configuration
    default_top_count: int = Field(default=5, env="DEFAULT_TOP_COUNT")
    max_backtests_per_lab: int = Field(default=1000, env="MAX_BACKTESTS_PER_LAB")
    analysis_timeout: int = Field(default=300, env="ANALYSIS_TIMEOUT")  # 5 minutes
    
    # Bot Configuration
    default_trade_amount_usdt: float = Field(default=2000.0, env="DEFAULT_TRADE_AMOUNT_USDT")
    default_leverage: float = Field(default=20.0, env="DEFAULT_LEVERAGE")
    default_margin_mode: str = Field(default="CROSS", env="DEFAULT_MARGIN_MODE")
    default_position_mode: str = Field(default="HEDGE", env="DEFAULT_POSITION_MODE")
    
    # Report Configuration
    report_output_dir: str = Field(default="reports", env="REPORT_OUTPUT_DIR")
    report_formats: List[str] = Field(default=["json", "csv"], env="REPORT_FORMATS")
    include_bot_recommendations: bool = Field(default=True, env="INCLUDE_BOT_RECOMMENDATIONS")
    
    # Performance Configuration
    enable_async: bool = Field(default=True, env="ENABLE_ASYNC")
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    connection_pool_size: int = Field(default=20, env="CONNECTION_POOL_SIZE")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()
    
    @field_validator('report_formats')
    @classmethod
    def validate_report_formats(cls, v):
        valid_formats = ['json', 'csv', 'markdown', 'html', 'txt']
        for format_type in v:
            if format_type.lower() not in valid_formats:
                raise ValueError(f'Invalid report format: {format_type}. Must be one of {valid_formats}')
        return [f.lower() for f in v]
    
    @field_validator('default_margin_mode')
    @classmethod
    def validate_margin_mode(cls, v):
        valid_modes = ['CROSS', 'ISOLATED']
        if v.upper() not in valid_modes:
            raise ValueError(f'margin_mode must be one of {valid_modes}')
        return v.upper()
    
    @field_validator('default_position_mode')
    @classmethod
    def validate_position_mode(cls, v):
        valid_modes = ['HEDGE', 'ONE_WAY']
        if v.upper() not in valid_modes:
            raise ValueError(f'position_mode must be one of {valid_modes}')
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


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

