"""
Central configuration manager for the HaasScript Backtesting System.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from .system_config import SystemConfig
from .haasonline_config import HaasOnlineConfig
from .database_config import DatabaseConfig


class ConfigManager:
    """Central configuration manager that handles all system configurations."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files. Defaults to 'config'.
        """
        self.config_dir = Path(config_dir or 'config')
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._system_config: Optional[SystemConfig] = None
        self._haasonline_config: Optional[HaasOnlineConfig] = None
        self._database_config: Optional[DatabaseConfig] = None
        
        self.logger = logging.getLogger(__name__)
    
    @property
    def system(self) -> SystemConfig:
        """Get system configuration, loading if necessary."""
        if self._system_config is None:
            self._system_config = self._load_system_config()
        return self._system_config
    
    @property
    def haasonline(self) -> HaasOnlineConfig:
        """Get HaasOnline configuration, loading if necessary."""
        if self._haasonline_config is None:
            self._haasonline_config = self._load_haasonline_config()
        return self._haasonline_config
    
    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration, loading if necessary."""
        if self._database_config is None:
            self._database_config = self._load_database_config()
        return self._database_config
    
    def _load_system_config(self) -> SystemConfig:
        """Load system configuration from file or environment."""
        config_file = self.config_dir / 'system.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Create config from file data
                config = SystemConfig()
                self._update_config_from_dict(config, config_data)
                
                self.logger.info(f"Loaded system configuration from {config_file}")
                return config
            except Exception as e:
                self.logger.warning(f"Failed to load system config from file: {e}")
        
        # Fall back to environment variables
        config = SystemConfig.from_env()
        self.logger.info("Loaded system configuration from environment variables")
        return config
    
    def _load_haasonline_config(self) -> HaasOnlineConfig:
        """Load HaasOnline configuration from file or environment."""
        config_file = self.config_dir / 'haasonline.json'
        
        if config_file.exists():
            try:
                config = HaasOnlineConfig.from_file(str(config_file))
                self.logger.info(f"Loaded HaasOnline configuration from {config_file}")
                return config
            except Exception as e:
                self.logger.warning(f"Failed to load HaasOnline config from file: {e}")
        
        # Fall back to environment variables
        try:
            config = HaasOnlineConfig.from_env()
            self.logger.info("Loaded HaasOnline configuration from environment variables")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load HaasOnline configuration: {e}")
            raise
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration from file or environment."""
        config_file = self.config_dir / 'database.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Create config from file data
                config = DatabaseConfig()
                self._update_config_from_dict(config, config_data)
                
                self.logger.info(f"Loaded database configuration from {config_file}")
                return config
            except Exception as e:
                self.logger.warning(f"Failed to load database config from file: {e}")
        
        # Fall back to environment variables
        config = DatabaseConfig.from_env()
        self.logger.info("Loaded database configuration from environment variables")
        return config
    
    def _update_config_from_dict(self, config: Any, config_data: Dict[str, Any]) -> None:
        """Update configuration object from dictionary data."""
        for key, value in config_data.items():
            if hasattr(config, key):
                if isinstance(value, dict) and hasattr(getattr(config, key), '__dict__'):
                    # Recursively update nested configuration objects
                    self._update_config_from_dict(getattr(config, key), value)
                else:
                    setattr(config, key, value)
    
    def save_system_config(self) -> None:
        """Save current system configuration to file."""
        if self._system_config is None:
            return
        
        config_file = self.config_dir / 'system.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(self._system_config.to_dict(), f, indent=2)
            self.logger.info(f"Saved system configuration to {config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save system configuration: {e}")
    
    def save_haasonline_config(self, include_secrets: bool = False) -> None:
        """Save current HaasOnline configuration to file."""
        if self._haasonline_config is None:
            return
        
        config_file = self.config_dir / 'haasonline.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(self._haasonline_config.to_dict(include_secrets=include_secrets), f, indent=2)
            self.logger.info(f"Saved HaasOnline configuration to {config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save HaasOnline configuration: {e}")
    
    def save_database_config(self, include_passwords: bool = False) -> None:
        """Save current database configuration to file."""
        if self._database_config is None:
            return
        
        config_file = self.config_dir / 'database.json'
        try:
            with open(config_file, 'w') as f:
                json.dump(self._database_config.to_dict(include_passwords=include_passwords), f, indent=2)
            self.logger.info(f"Saved database configuration to {config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save database configuration: {e}")
    
    def reload_all(self) -> None:
        """Reload all configurations from files/environment."""
        self._system_config = None
        self._haasonline_config = None
        self._database_config = None
        
        # Access properties to trigger reload
        _ = self.system
        _ = self.haasonline
        _ = self.database
        
        self.logger.info("Reloaded all configurations")
    
    def validate_all(self) -> Dict[str, bool]:
        """Validate all configurations and return status."""
        results = {}
        
        try:
            self.system._validate_config()
            results['system'] = True
        except Exception as e:
            self.logger.error(f"System configuration validation failed: {e}")
            results['system'] = False
        
        try:
            self.haasonline._validate_config()
            results['haasonline'] = True
        except Exception as e:
            self.logger.error(f"HaasOnline configuration validation failed: {e}")
            results['haasonline'] = False
        
        try:
            self.database.__post_init__()  # Triggers validation
            results['database'] = True
        except Exception as e:
            self.logger.error(f"Database configuration validation failed: {e}")
            results['database'] = False
        
        return results
    
    def get_all_configs(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Get all configurations as a single dictionary."""
        return {
            'system': self.system.to_dict(),
            'haasonline': self.haasonline.to_dict(include_secrets=include_secrets),
            'database': self.database.to_dict(include_passwords=include_secrets),
        }
    
    def create_sample_configs(self) -> None:
        """Create sample configuration files for reference."""
        sample_dir = self.config_dir / 'samples'
        sample_dir.mkdir(exist_ok=True)
        
        # Create sample system config
        sample_system = SystemConfig()
        with open(sample_dir / 'system.json.sample', 'w') as f:
            json.dump(sample_system.to_dict(), f, indent=2)
        
        # Create sample database config
        sample_database = DatabaseConfig()
        with open(sample_dir / 'database.json.sample', 'w') as f:
            json.dump(sample_database.to_dict(include_passwords=True), f, indent=2)
        
        # Create sample HaasOnline config (without real credentials)
        sample_haasonline_data = {
            "server_url": "https://your-haasonline-server.com/",
            "api_key": "your-api-key-here",
            "api_secret": "your-api-secret-here",
            "username": "optional-username",
            "password": "optional-password"
        }
        with open(sample_dir / 'haasonline.json.sample', 'w') as f:
            json.dump(sample_haasonline_data, f, indent=2)
        
        self.logger.info(f"Created sample configuration files in {sample_dir}")


# Global configuration manager instance
config_manager = ConfigManager()