"""
Main settings configuration for pyHaasAPI v2

Simplified configuration without Pydantic validation.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    """
    Main settings class for pyHaasAPI v2
    
    Simplified configuration without Pydantic validation.
    """
    
    # Global settings
    debug: bool = False
    environment: str = "production"
    version: str = "2.0.0"
    default_server: str = "srv03"
    
    def __post_init__(self):
        """Initialize settings from environment variables"""
        self.debug = os.getenv("PYHAASAPI_DEBUG", "false").lower() == "true"
        self.environment = os.getenv("PYHAASAPI_ENV", "production")
        self.default_server = os.getenv("API_DEFAULT_SERVER", "srv03")
    
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
        return {
            "debug": self.debug,
            "environment": self.environment,
            "version": self.version,
            "default_server": self.default_server
        }
    
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
