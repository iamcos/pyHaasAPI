"""
Cache configuration settings
"""

from typing import Optional
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class CacheConfig(BaseSettings):
    """Cache configuration settings"""
    
    # Cache enablement
    enabled: bool = Field(default=True, env="CACHE_ENABLED")
    
    # Cache directory
    directory: str = Field(default="unified_cache", env="CACHE_DIRECTORY")
    
    # Cache TTL settings
    default_ttl: int = Field(default=3600, env="CACHE_DEFAULT_TTL")  # 1 hour
    backtest_ttl: int = Field(default=86400, env="CACHE_BACKTEST_TTL")  # 24 hours
    lab_ttl: int = Field(default=1800, env="CACHE_LAB_TTL")  # 30 minutes
    bot_ttl: int = Field(default=300, env="CACHE_BOT_TTL")  # 5 minutes
    account_ttl: int = Field(default=600, env="CACHE_ACCOUNT_TTL")  # 10 minutes
    market_ttl: int = Field(default=60, env="CACHE_MARKET_TTL")  # 1 minute
    
    # Cache size limits
    max_size_mb: int = Field(default=1024, env="CACHE_MAX_SIZE_MB")  # 1GB
    max_files: int = Field(default=10000, env="CACHE_MAX_FILES")
    
    # Cache cleanup
    cleanup_interval: int = Field(default=3600, env="CACHE_CLEANUP_INTERVAL")  # 1 hour
    cleanup_threshold: float = Field(default=0.8, env="CACHE_CLEANUP_THRESHOLD")  # 80%
    
    # Cache compression
    compress: bool = Field(default=True, env="CACHE_COMPRESS")
    compression_level: int = Field(default=6, env="CACHE_COMPRESSION_LEVEL")
    
    # Cache validation
    validate_on_read: bool = Field(default=True, env="CACHE_VALIDATE_ON_READ")
    validate_on_write: bool = Field(default=True, env="CACHE_VALIDATE_ON_WRITE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"    
    @field_validator("default_ttl", "backtest_ttl", "lab_ttl", "bot_ttl", "account_ttl", "market_ttl")
    @classmethod
    def validate_ttl(cls, v):
        """Validate TTL values"""
        if v < 0:
            raise ValueError("TTL must be non-negative")
        return v
    
    @field_validator("max_size_mb")
    @classmethod
    def validate_max_size(cls, v):
        """Validate max cache size"""
        if v <= 0:
            raise ValueError("Max cache size must be positive")
        return v
    
    @field_validator("max_files")
    @classmethod
    def validate_max_files(cls, v):
        """Validate max files"""
        if v <= 0:
            raise ValueError("Max files must be positive")
        return v
    
    @field_validator("cleanup_threshold")
    @classmethod
    def validate_cleanup_threshold(cls, v):
        """Validate cleanup threshold"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Cleanup threshold must be between 0.0 and 1.0")
        return v
    
    @field_validator("compression_level")
    @classmethod
    def validate_compression_level(cls, v):
        """Validate compression level"""
        if not 1 <= v <= 9:
            raise ValueError("Compression level must be between 1 and 9")
        return v
    
    @property
    def cache_path(self) -> Path:
        """Get cache directory path"""
        return Path(self.directory)
    
    @property
    def backtest_cache_path(self) -> Path:
        """Get backtest cache path"""
        return self.cache_path / "backtests"
    
    @property
    def lab_cache_path(self) -> Path:
        """Get lab cache path"""
        return self.cache_path / "labs"
    
    @property
    def bot_cache_path(self) -> Path:
        """Get bot cache path"""
        return self.cache_path / "bots"
    
    @property
    def account_cache_path(self) -> Path:
        """Get account cache path"""
        return self.cache_path / "accounts"
    
    @property
    def market_cache_path(self) -> Path:
        """Get market cache path"""
        return self.cache_path / "markets"
    
    @property
    def reports_cache_path(self) -> Path:
        """Get reports cache path"""
        return self.cache_path / "reports"
    
    def get_ttl(self, cache_type: str) -> int:
        """Get TTL for specific cache type"""
        ttl_map = {
            "backtest": self.backtest_ttl,
            "lab": self.lab_ttl,
            "bot": self.bot_ttl,
            "account": self.account_ttl,
            "market": self.market_ttl,
        }
        return ttl_map.get(cache_type, self.default_ttl)
