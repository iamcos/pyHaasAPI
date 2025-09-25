"""
Main settings configuration for pyHaasAPI v2

Central configuration management using Pydantic with environment variable support.
"""

import os
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path

from .api_config import APIConfig
from .cache_config import CacheConfig
from .logging_config import LoggingConfig
from .analysis_config import AnalysisConfig
from .bot_config import BotConfig
from .report_config import ReportConfig


class Settings(BaseSettings):
    """
    Main settings class for pyHaasAPI v2
    
    Combines all configuration sections and provides environment variable support.
    """
    
    # API Configuration
    api: APIConfig = Field(default_factory=APIConfig)
    
    # Cache Configuration
    cache: CacheConfig = Field(default_factory=CacheConfig)
    
    # Logging Configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Analysis Configuration
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    
    # Bot Configuration
    bot: BotConfig = Field(default_factory=BotConfig)
    
    # Report Configuration
    report: ReportConfig = Field(default_factory=ReportConfig)
    
    # Global settings
    debug: bool = Field(default=False, env="PYHAASAPI_DEBUG")
    environment: str = Field(default="production", env="PYHAASAPI_ENV")
    version: str = Field(default="2.0.0")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        env_nested_delimiter = "__"
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_envs = ["development", "staging", "production", "testing"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"
    
    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.debug or self.is_development
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return self.dict()
    
    def save_to_file(self, file_path: str) -> None:
        """Save settings to file"""
        import json
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "Settings":
        """Load settings from file"""
        import json
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def get_env_var(self, key: str, default: Any = None) -> Any:
        """Get environment variable with fallback"""
        return os.getenv(key, default)
    
    def set_env_var(self, key: str, value: str) -> None:
        """Set environment variable"""
        os.environ[key] = value


# Global settings instance
settings = Settings()
