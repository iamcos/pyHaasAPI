"""
Unit tests for configuration management.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from mcp_tui_client.services.config import ConfigurationService


class TestConfigurationService:
    """Test cases for ConfigurationService."""

    def test_default_config_creation(self):
        """Test that default configuration is created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            with patch('mcp_tui_client.services.config.Path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = config_path
                
                config_service = ConfigurationService()
                
                # Should create default config
                assert config_path.exists()
                
                # Check default values
                mcp_settings = config_service.get_mcp_settings()
                assert mcp_settings["host"] == "localhost"
                assert mcp_settings["port"] == 3002
                assert mcp_settings["timeout"] == 30

    def test_load_existing_config(self):
        """Test loading existing configuration file."""
        test_config = {
            "mcp": {
                "host": "custom-host",
                "port": 8080,
                "timeout": 60
            },
            "ui": {
                "theme": "light",
                "auto_refresh_interval": 10
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_path = Path(f.name)
        
        try:
            with patch('mcp_tui_client.services.config.Path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = config_path
                
                config_service = ConfigurationService()
                
                mcp_settings = config_service.get_mcp_settings()
                assert mcp_settings["host"] == "custom-host"
                assert mcp_settings["port"] == 8080
                
                ui_prefs = config_service.get_ui_preferences()
                assert ui_prefs["theme"] == "light"
                assert ui_prefs["auto_refresh_interval"] == 10
        finally:
            config_path.unlink()

    def test_save_config(self):
        """Test saving configuration to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            with patch('mcp_tui_client.services.config.Path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = config_path
                
                config_service = ConfigurationService()
                
                # Modify config
                config_service.config["mcp"]["host"] = "new-host"
                config_service.config["ui"]["theme"] = "custom"
                
                # Save config
                config_service.save_config()
                
                # Verify saved
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                
                assert saved_config["mcp"]["host"] == "new-host"
                assert saved_config["ui"]["theme"] == "custom"

    def test_config_validation(self):
        """Test configuration validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            with patch('mcp_tui_client.services.config.Path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = config_path
                
                config_service = ConfigurationService()
                
                # Test valid config
                valid_config = {
                    "mcp": {
                        "host": "localhost",
                        "port": 3002,
                        "timeout": 30
                    }
                }
                assert config_service.validate_config(valid_config) is True
                
                # Test invalid config (missing required fields)
                invalid_config = {
                    "mcp": {
                        "host": "localhost"
                        # Missing port and timeout
                    }
                }
                assert config_service.validate_config(invalid_config) is False

    def test_environment_variable_override(self):
        """Test that environment variables override config file values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            with patch('mcp_tui_client.services.config.Path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = config_path
                
                with patch.dict('os.environ', {
                    'MCP_HOST': 'env-host',
                    'MCP_PORT': '9999'
                }):
                    config_service = ConfigurationService()
                    
                    mcp_settings = config_service.get_mcp_settings()
                    assert mcp_settings["host"] == "env-host"
                    assert mcp_settings["port"] == 9999

    @pytest.mark.parametrize("invalid_port", [-1, 0, 65536, "invalid"])
    def test_invalid_port_validation(self, invalid_port):
        """Test validation of invalid port values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            
            with patch('mcp_tui_client.services.config.Path.expanduser') as mock_expanduser:
                mock_expanduser.return_value = config_path
                
                config_service = ConfigurationService()
                
                invalid_config = {
                    "mcp": {
                        "host": "localhost",
                        "port": invalid_port,
                        "timeout": 30
                    }
                }
                
                assert config_service.validate_config(invalid_config) is False