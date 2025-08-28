"""
Configuration Service

Manages application configuration, user preferences, and secure credential storage.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
import keyring
from dotenv import load_dotenv


@dataclass
class MCPConfig:
    """MCP server configuration"""
    host: str = "localhost"
    port: int = 3002
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1000
    use_ssl: bool = False
    api_key: Optional[str] = None
    username: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding sensitive data"""
        data = asdict(self)
        # Remove sensitive fields from serialization
        data.pop('api_key', None)
        return data


@dataclass
class UIPreferences:
    """UI preferences and theme settings"""
    theme: str = "dark"
    show_help_on_startup: bool = True
    auto_refresh_interval: int = 5
    chart_style: str = "ascii"
    panel_layout: str = "default"
    keyboard_shortcuts: Dict[str, str] = None
    
    def __post_init__(self):
        if self.keyboard_shortcuts is None:
            self.keyboard_shortcuts = self._get_default_shortcuts()
    
    def _get_default_shortcuts(self) -> Dict[str, str]:
        """Get default keyboard shortcuts"""
        return {
            "quit": "ctrl+q",
            "help": "ctrl+h",
            "refresh": "ctrl+r",
            "dashboard": "f1",
            "bots": "f2",
            "labs": "f3",
            "scripts": "f4",
            "workflows": "f5",
            "markets": "f6",
            "analytics": "f7",
            "settings": "f8"
        }


class ConfigurationService:
    """Manages application configuration and user preferences"""
    
    # Keyring service name for secure credential storage
    KEYRING_SERVICE = "mcp-tui-client"
    
    def __init__(self, config_path: Optional[str] = None):
        # Load environment variables from .env file if present
        load_dotenv()
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".mcp-tui" / "config.json"
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
        self.logger = logging.getLogger(__name__)
        
        # Apply environment variable overrides
        self._apply_env_overrides()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Failed to load config from {self.config_path}: {e}")
            return self._get_default_config()
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            logging.error(f"Failed to save config to {self.config_path}: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        mcp_config = MCPConfig()
        ui_prefs = UIPreferences()
        
        return {
            "mcp": mcp_config.to_dict(),
            "ui": asdict(ui_prefs),
            "logging": {
                "level": "INFO",
                "file_path": str(Path.home() / ".mcp-tui" / "logs" / "app.log"),
                "max_file_size": 10 * 1024 * 1024,  # 10MB
                "backup_count": 5
            },
            "cache": {
                "enabled": True,
                "max_size": 1000,
                "ttl_seconds": 300
            },
            "security": {
                "use_keyring": True,
                "encrypt_config": False
            },
            "version": "0.1.0"
        }
    
    def get_mcp_settings(self) -> MCPConfig:
        """Get MCP connection settings with secure credentials"""
        mcp_config = self.config.get("mcp", {})
        
        # Create MCPConfig instance
        config = MCPConfig(**mcp_config)
        
        # Load secure credentials from keyring if available
        if self.config.get("security", {}).get("use_keyring", True):
            try:
                # Try to get API key from keyring
                api_key = keyring.get_password(self.KEYRING_SERVICE, "mcp_api_key")
                if api_key:
                    config.api_key = api_key
                
                # Try to get username from keyring
                username = keyring.get_password(self.KEYRING_SERVICE, "mcp_username")
                if username:
                    config.username = username
                    
            except Exception as e:
                self.logger.warning(f"Failed to retrieve credentials from keyring: {e}")
        
        return config
    
    def get_ui_preferences(self) -> UIPreferences:
        """Get UI preferences and themes"""
        ui_config = self.config.get("ui", {})
        return UIPreferences(**ui_config)
    
    def get_log_level(self) -> str:
        """Get logging level"""
        return self.config.get("logging", {}).get("level", "INFO")
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get("logging", {})
    
    def set_log_level(self, level: str) -> None:
        """Set logging level"""
        self.config.setdefault("logging", {})["level"] = level
        self.save_config()
    
    def set_ui_preferences(self, ui_prefs: Dict[str, Any]) -> None:
        """Set UI preferences from dictionary"""
        self.config["ui"] = ui_prefs
        self.save_config()
    
    def update_mcp_settings(self, mcp_config: MCPConfig) -> None:
        """Update MCP settings with secure credential storage"""
        # Store non-sensitive config in file
        self.config["mcp"] = mcp_config.to_dict()
        
        # Store sensitive credentials in keyring if enabled
        if self.config.get("security", {}).get("use_keyring", True):
            try:
                if mcp_config.api_key:
                    keyring.set_password(self.KEYRING_SERVICE, "mcp_api_key", mcp_config.api_key)
                
                if mcp_config.username:
                    keyring.set_password(self.KEYRING_SERVICE, "mcp_username", mcp_config.username)
                    
            except Exception as e:
                self.logger.error(f"Failed to store credentials in keyring: {e}")
        
        self.save_config()
    
    def update_ui_preferences(self, ui_prefs: UIPreferences) -> None:
        """Update UI preferences"""
        self.config["ui"] = asdict(ui_prefs)
        self.save_config()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting by key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a specific setting by key"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = self._get_default_config()
        self.save_config()
        self.logger.info("Configuration reset to defaults")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration"""
        env_mappings = {
            "MCP_TUI_HOST": "mcp.host",
            "MCP_TUI_PORT": "mcp.port",
            "MCP_TUI_TIMEOUT": "mcp.timeout",
            "MCP_TUI_RETRY_ATTEMPTS": "mcp.retry_attempts",
            "MCP_TUI_RETRY_DELAY": "mcp.retry_delay",
            "MCP_TUI_USE_SSL": "mcp.use_ssl",
            "MCP_TUI_USERNAME": "mcp.username",
            "MCP_TUI_THEME": "ui.theme",
            "MCP_TUI_LOG_LEVEL": "logging.level",
            "MCP_TUI_AUTO_REFRESH": "ui.auto_refresh_interval",
            "MCP_TUI_CHART_STYLE": "ui.chart_style",
            "MCP_TUI_PANEL_LAYOUT": "ui.panel_layout"
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(env_value, config_path)
                self.set_setting(config_path, converted_value)
                self.logger.debug(f"Applied environment override: {env_var} -> {config_path}")
        
        # Handle API key from environment
        api_key = os.getenv("MCP_TUI_API_KEY")
        if api_key and self.config.get("security", {}).get("use_keyring", True):
            try:
                keyring.set_password(self.KEYRING_SERVICE, "mcp_api_key", api_key)
                self.logger.debug("Stored API key from environment to keyring")
            except Exception as e:
                self.logger.warning(f"Failed to store API key from environment: {e}")
    
    def _convert_env_value(self, value: str, config_path: str) -> Union[str, int, bool, float]:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if config_path.endswith(('.use_ssl', '.show_help_on_startup')):
            return value.lower() in ('true', '1', 'yes', 'on')
        
        # Integer conversion
        if config_path.endswith(('.port', '.timeout', '.retry_attempts', '.retry_delay', 
                               '.auto_refresh_interval', '.max_file_size', '.backup_count')):
            try:
                return int(value)
            except ValueError:
                self.logger.warning(f"Invalid integer value for {config_path}: {value}")
                return value
        
        # Float conversion for numeric settings
        if config_path.endswith('.system_load'):
            try:
                return float(value)
            except ValueError:
                self.logger.warning(f"Invalid float value for {config_path}: {value}")
                return value
        
        # Default to string
        return value
    
    def store_credential(self, key: str, value: str) -> bool:
        """Store a credential securely using keyring"""
        if not self.config.get("security", {}).get("use_keyring", True):
            self.logger.warning("Keyring storage is disabled")
            return False
        
        try:
            keyring.set_password(self.KEYRING_SERVICE, key, value)
            self.logger.debug(f"Stored credential: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store credential {key}: {e}")
            return False
    
    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential securely using keyring"""
        if not self.config.get("security", {}).get("use_keyring", True):
            return None
        
        try:
            credential = keyring.get_password(self.KEYRING_SERVICE, key)
            if credential:
                self.logger.debug(f"Retrieved credential: {key}")
            return credential
        except Exception as e:
            self.logger.error(f"Failed to retrieve credential {key}: {e}")
            return None
    
    def delete_credential(self, key: str) -> bool:
        """Delete a credential from keyring"""
        if not self.config.get("security", {}).get("use_keyring", True):
            return False
        
        try:
            keyring.delete_password(self.KEYRING_SERVICE, key)
            self.logger.debug(f"Deleted credential: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete credential {key}: {e}")
            return False
    
    def list_stored_credentials(self) -> list[str]:
        """List all stored credential keys (for management purposes)"""
        # Note: keyring doesn't provide a direct way to list all keys
        # This is a basic implementation that tracks known credential types
        known_credentials = ["mcp_api_key", "mcp_username", "mcp_password"]
        stored_credentials = []
        
        for cred in known_credentials:
            if self.get_credential(cred):
                stored_credentials.append(cred)
        
        return stored_credentials
    
    def validate_configuration(self) -> Dict[str, list[str]]:
        """Validate current configuration and return any issues"""
        issues = {
            "errors": [],
            "warnings": []
        }
        
        # Validate MCP configuration
        mcp_config = self.get_mcp_settings()
        
        if not mcp_config.host:
            issues["errors"].append("MCP host is required")
        
        if mcp_config.port <= 0 or mcp_config.port > 65535:
            issues["errors"].append("MCP port must be between 1 and 65535")
        
        if mcp_config.timeout <= 0:
            issues["errors"].append("MCP timeout must be positive")
        
        if mcp_config.retry_attempts < 0:
            issues["errors"].append("MCP retry attempts cannot be negative")
        
        # Validate UI preferences
        ui_prefs = self.get_ui_preferences()
        
        if ui_prefs.theme not in ["dark", "light", "auto"]:
            issues["warnings"].append(f"Unknown theme '{ui_prefs.theme}', using default")
        
        if ui_prefs.auto_refresh_interval < 1:
            issues["warnings"].append("Auto refresh interval should be at least 1 second")
        
        # Validate logging configuration
        log_config = self.get_log_config()
        log_path = Path(log_config.get("file_path", ""))
        
        if not log_path.parent.exists():
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues["warnings"].append(f"Cannot create log directory: {e}")
        
        return issues
    
    def export_config(self, export_path: str, include_credentials: bool = False) -> bool:
        """Export configuration to a file"""
        try:
            export_data = self.config.copy()
            
            if include_credentials:
                # Add credentials to export (use with caution)
                credentials = {}
                for cred_key in self.list_stored_credentials():
                    credentials[cred_key] = self.get_credential(cred_key)
                export_data["credentials"] = credentials
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Configuration exported to {export_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: str, merge: bool = True) -> bool:
        """Import configuration from a file"""
        try:
            with open(import_path, 'r') as f:
                imported_config = json.load(f)
            
            # Handle credentials separately
            if "credentials" in imported_config:
                credentials = imported_config.pop("credentials")
                for key, value in credentials.items():
                    if value:  # Only store non-empty credentials
                        self.store_credential(key, value)
            
            if merge:
                # Merge with existing configuration
                self._deep_merge(self.config, imported_config)
            else:
                # Replace entire configuration
                self.config = imported_config
            
            self.save_config()
            self.logger.info(f"Configuration imported from {import_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dictionary into target dictionary"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value