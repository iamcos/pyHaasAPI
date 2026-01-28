"""
Cache configuration settings
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from .env_utils import get_env

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    
    # Cache enablement
    enabled: bool = field(default_factory=lambda: get_env("CACHE_ENABLED", True, bool))
    
    # Cache directory
    directory: str = field(default_factory=lambda: get_env("CACHE_DIRECTORY", "unified_cache"))
    
    # Cache TTL settings
    default_ttl: int = field(default_factory=lambda: get_env("CACHE_DEFAULT_TTL", 3600, int))  # 1 hour
    backtest_ttl: int = field(default_factory=lambda: get_env("CACHE_BACKTEST_TTL", 86400, int))  # 24 hours
    lab_ttl: int = field(default_factory=lambda: get_env("CACHE_LAB_TTL", 1800, int))  # 30 minutes
    bot_ttl: int = field(default_factory=lambda: get_env("CACHE_BOT_TTL", 300, int))  # 5 minutes
    account_ttl: int = field(default_factory=lambda: get_env("CACHE_ACCOUNT_TTL", 600, int))  # 10 minutes
    market_ttl: int = field(default_factory=lambda: get_env("CACHE_MARKET_TTL", 60, int))  # 1 minute
    
    # Cache size limits
    max_size_mb: int = field(default_factory=lambda: get_env("CACHE_MAX_SIZE_MB", 1024, int))  # 1GB
    max_files: int = field(default_factory=lambda: get_env("CACHE_MAX_FILES", 10000, int))
    
    # Cache cleanup
    cleanup_interval: int = field(default_factory=lambda: get_env("CACHE_CLEANUP_INTERVAL", 3600, int))  # 1 hour
    cleanup_threshold: float = field(default_factory=lambda: get_env("CACHE_CLEANUP_THRESHOLD", 0.8, float))  # 80%
    
    # Cache compression
    compress: bool = field(default_factory=lambda: get_env("CACHE_COMPRESS", True, bool))
    compression_level: int = field(default_factory=lambda: get_env("CACHE_COMPRESSION_LEVEL", 6, int))
    
    # Cache validation
    validate_on_read: bool = field(default_factory=lambda: get_env("CACHE_VALIDATE_ON_READ", True, bool))
    validate_on_write: bool = field(default_factory=lambda: get_env("CACHE_VALIDATE_ON_WRITE", True, bool))
    
    def __post_init__(self):
        """Validate configuration"""
        self.validate_ttl()
        self.validate_max_size()
        self.validate_max_files()
        self.validate_cleanup_threshold()
        self.validate_compression_level()
        
    def validate_ttl(self):
        for v in [self.default_ttl, self.backtest_ttl, self.lab_ttl, self.bot_ttl, self.account_ttl, self.market_ttl]:
            if v < 0:
                raise ValueError("TTL must be non-negative")

    def validate_max_size(self):
        if self.max_size_mb <= 0:
            raise ValueError("Max cache size must be positive")

    def validate_max_files(self):
        if self.max_files <= 0:
            raise ValueError("Max files must be positive")

    def validate_cleanup_threshold(self):
        if not 0.0 <= self.cleanup_threshold <= 1.0:
            raise ValueError("Cleanup threshold must be between 0.0 and 1.0")

    def validate_compression_level(self):
        if not 1 <= self.compression_level <= 9:
            raise ValueError("Compression level must be between 1 and 9")

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
