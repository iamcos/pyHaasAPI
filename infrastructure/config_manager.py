#!/usr/bin/env python3
"""
Configuration Management System

This module provides centralized configuration management for the distributed
trading bot testing automation system, handling server configurations,
lab settings, and system parameters.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigFormat(Enum):
    """Supported configuration file formats"""
    JSON = "json"
    YAML = "yaml"

@dataclass
class LabConfig:
    """Configuration for lab backtesting"""
    max_population: int = 50
    max_generations: int = 100
    max_elites: int = 3
    mix_rate: float = 40.0
    adjust_rate: float = 25.0
    max_runtime: int = 0  # 0 = unlimited
    auto_restart: int = 0

@dataclass
class AccountSettings:
    """Account management settings"""
    naming_schema: str = "4{AA-DV}-10k"
    initial_balance: float = 10000.0
    test_account_names: List[str] = None
    accounts_per_server: int = 100
    
    def __post_init__(self):
        if self.test_account_names is None:
            self.test_account_names = ["для тестов 10к"]

@dataclass
class MLAnalysisConfig:
    """Machine learning analysis configuration"""
    gemini_cli_path: str = "/usr/local/bin/gemini"
    analysis_models: List[str] = None
    local_processing: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.analysis_models is None:
            self.analysis_models = [
                "parameter_optimization",
                "pattern_recognition", 
                "performance_prediction"
            ]
        
        if self.local_processing is None:
            self.local_processing = {
                "use_m1_acceleration": True,
                "max_memory_gb": 32,
                "parallel_workers": 8
            }

@dataclass
class SystemConfig:
    """Main system configuration"""
    servers: Dict[str, Dict[str, Any]]
    default_lab_config: LabConfig
    account_settings: AccountSettings
    ml_analysis: MLAnalysisConfig
    logging_level: str = "INFO"
    data_directory: str = "./data"
    results_directory: str = "./results"
    backup_directory: str = "./backups"

class ConfigManager:
    """Main configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config: Optional[SystemConfig] = None
        self.config_format = ConfigFormat.JSON
        
        if config_file:
            self.load_config(config_file)
        else:
            self.config = self._create_default_config()
    
    def load_config(self, config_file: str):
        """
        Load configuration from file.
        
        Args:
            config_file: Path to configuration file
        """
        if not os.path.exists(config_file):
            logger.error(f"Configuration file not found: {config_file}")
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        # Determine file format
        if config_file.endswith('.yaml') or config_file.endswith('.yml'):
            self.config_format = ConfigFormat.YAML
        else:
            self.config_format = ConfigFormat.JSON
        
        try:
            with open(config_file, 'r') as f:
                if self.config_format == ConfigFormat.YAML:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            self.config = self._parse_config_data(config_data)
            self.config_file = config_file
            
            logger.info(f"Configuration loaded from {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
            raise
    
    def save_config(self, config_file: Optional[str] = None):
        """
        Save configuration to file.
        
        Args:
            config_file: Optional path to save configuration (uses loaded file if not specified)
        """
        if not self.config:
            logger.error("No configuration to save")
            return
        
        save_file = config_file or self.config_file
        if not save_file:
            logger.error("No configuration file specified")
            return
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_file), exist_ok=True)
            
            # Convert config to dictionary
            config_dict = self._config_to_dict(self.config)
            
            with open(save_file, 'w') as f:
                if self.config_format == ConfigFormat.YAML:
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {save_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {save_file}: {e}")
            raise
    
    def get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific server"""
        if not self.config or not self.config.servers:
            return None
        
        return self.config.servers.get(server_id)
    
    def get_all_server_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all server configurations"""
        if not self.config or not self.config.servers:
            return {}
        
        return self.config.servers.copy()
    
    def add_server_config(self, server_id: str, server_config: Dict[str, Any]):
        """Add or update server configuration"""
        if not self.config:
            self.config = self._create_default_config()
        
        self.config.servers[server_id] = server_config
        logger.info(f"Added/updated server configuration for {server_id}")
    
    def remove_server_config(self, server_id: str) -> bool:
        """Remove server configuration"""
        if not self.config or not self.config.servers:
            return False
        
        if server_id in self.config.servers:
            del self.config.servers[server_id]
            logger.info(f"Removed server configuration for {server_id}")
            return True
        
        return False
    
    def get_lab_config(self) -> LabConfig:
        """Get default lab configuration"""
        if not self.config:
            return LabConfig()
        
        return self.config.default_lab_config
    
    def update_lab_config(self, **kwargs):
        """Update lab configuration parameters"""
        if not self.config:
            self.config = self._create_default_config()
        
        for key, value in kwargs.items():
            if hasattr(self.config.default_lab_config, key):
                setattr(self.config.default_lab_config, key, value)
                logger.info(f"Updated lab config: {key} = {value}")
            else:
                logger.warning(f"Unknown lab config parameter: {key}")
    
    def get_account_settings(self) -> AccountSettings:
        """Get account management settings"""
        if not self.config:
            return AccountSettings()
        
        return self.config.account_settings
    
    def update_account_settings(self, **kwargs):
        """Update account settings"""
        if not self.config:
            self.config = self._create_default_config()
        
        for key, value in kwargs.items():
            if hasattr(self.config.account_settings, key):
                setattr(self.config.account_settings, key, value)
                logger.info(f"Updated account settings: {key} = {value}")
            else:
                logger.warning(f"Unknown account settings parameter: {key}")
    
    def get_ml_analysis_config(self) -> MLAnalysisConfig:
        """Get ML analysis configuration"""
        if not self.config:
            return MLAnalysisConfig()
        
        return self.config.ml_analysis
    
    def update_ml_analysis_config(self, **kwargs):
        """Update ML analysis configuration"""
        if not self.config:
            self.config = self._create_default_config()
        
        for key, value in kwargs.items():
            if hasattr(self.config.ml_analysis, key):
                setattr(self.config.ml_analysis, key, value)
                logger.info(f"Updated ML analysis config: {key} = {value}")
            else:
                logger.warning(f"Unknown ML analysis config parameter: {key}")
    
    def get_system_directories(self) -> Dict[str, str]:
        """Get system directory paths"""
        if not self.config:
            config = self._create_default_config()
        else:
            config = self.config
        
        return {
            'data': config.data_directory,
            'results': config.results_directory,
            'backup': config.backup_directory
        }
    
    def ensure_directories_exist(self):
        """Create system directories if they don't exist"""
        directories = self.get_system_directories()
        
        for dir_type, dir_path in directories.items():
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Ensured {dir_type} directory exists: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to create {dir_type} directory {dir_path}: {e}")
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of issues.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []
        
        if not self.config:
            issues.append("No configuration loaded")
            return issues
        
        # Validate servers
        if not self.config.servers:
            issues.append("No servers configured")
        else:
            for server_id, server_config in self.config.servers.items():
                # Check required fields
                required_fields = ['host', 'api_ports', 'max_population', 'max_concurrent_tasks', 'role']
                for field in required_fields:
                    if field not in server_config:
                        issues.append(f"Server {server_id} missing required field: {field}")
                
                # Validate port numbers
                if 'api_ports' in server_config:
                    for port in server_config['api_ports']:
                        if not isinstance(port, int) or port < 1 or port > 65535:
                            issues.append(f"Server {server_id} has invalid port: {port}")
                
                # Validate role
                if 'role' in server_config:
                    valid_roles = ['backtest', 'development', 'mixed']
                    if server_config['role'] not in valid_roles:
                        issues.append(f"Server {server_id} has invalid role: {server_config['role']}")
        
        # Validate lab config
        lab_config = self.config.default_lab_config
        if lab_config.max_population <= 0:
            issues.append("Lab max_population must be positive")
        if lab_config.max_generations <= 0:
            issues.append("Lab max_generations must be positive")
        if lab_config.max_elites < 0:
            issues.append("Lab max_elites cannot be negative")
        if not (0 <= lab_config.mix_rate <= 100):
            issues.append("Lab mix_rate must be between 0 and 100")
        if not (0 <= lab_config.adjust_rate <= 100):
            issues.append("Lab adjust_rate must be between 0 and 100")
        
        # Validate account settings
        account_settings = self.config.account_settings
        if account_settings.initial_balance <= 0:
            issues.append("Account initial_balance must be positive")
        if account_settings.accounts_per_server <= 0:
            issues.append("Account accounts_per_server must be positive")
        
        return issues
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a backup of the current configuration.
        
        Args:
            backup_name: Optional backup name (uses timestamp if not provided)
            
        Returns:
            Path to backup file
        """
        if not self.config:
            raise ValueError("No configuration to backup")
        
        if not backup_name:
            from datetime import datetime
            backup_name = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.config.backup_directory
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"{backup_name}.json")
        
        # Save current config as backup
        original_file = self.config_file
        self.save_config(backup_file)
        self.config_file = original_file  # Restore original file path
        
        logger.info(f"Configuration backup created: {backup_file}")
        return backup_file
    
    def restore_from_backup(self, backup_file: str):
        """
        Restore configuration from backup.
        
        Args:
            backup_file: Path to backup file
        """
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Create backup of current config before restoring
        if self.config:
            self.create_backup("pre_restore_backup")
        
        # Load backup
        self.load_config(backup_file)
        logger.info(f"Configuration restored from backup: {backup_file}")
    
    def _create_default_config(self) -> SystemConfig:
        """Create default system configuration"""
        default_servers = {
            "srv01": {
                "host": "srv01",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 50,
                "max_concurrent_tasks": 5,
                "role": "backtest",
                "ssh_user": "root"
            },
            "srv02": {
                "host": "srv02",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 30,
                "max_concurrent_tasks": 3,
                "role": "mixed",
                "ssh_user": "root"
            },
            "srv03": {
                "host": "srv03",
                "ssh_port": 22,
                "api_ports": [8090, 8092],
                "max_population": 20,
                "max_concurrent_tasks": 2,
                "role": "development",
                "ssh_user": "root"
            }
        }
        
        return SystemConfig(
            servers=default_servers,
            default_lab_config=LabConfig(),
            account_settings=AccountSettings(),
            ml_analysis=MLAnalysisConfig()
        )
    
    def _parse_config_data(self, config_data: Dict[str, Any]) -> SystemConfig:
        """Parse configuration data into SystemConfig object"""
        # Parse lab config
        lab_config_data = config_data.get('default_lab_config', {})
        lab_config = LabConfig(**lab_config_data)
        
        # Parse account settings
        account_settings_data = config_data.get('account_settings', {})
        account_settings = AccountSettings(**account_settings_data)
        
        # Parse ML analysis config
        ml_analysis_data = config_data.get('ml_analysis', {})
        ml_analysis = MLAnalysisConfig(**ml_analysis_data)
        
        return SystemConfig(
            servers=config_data.get('servers', {}),
            default_lab_config=lab_config,
            account_settings=account_settings,
            ml_analysis=ml_analysis,
            logging_level=config_data.get('logging_level', 'INFO'),
            data_directory=config_data.get('data_directory', './data'),
            results_directory=config_data.get('results_directory', './results'),
            backup_directory=config_data.get('backup_directory', './backups')
        )
    
    def _config_to_dict(self, config: SystemConfig) -> Dict[str, Any]:
        """Convert SystemConfig object to dictionary"""
        return {
            'servers': config.servers,
            'default_lab_config': asdict(config.default_lab_config),
            'account_settings': asdict(config.account_settings),
            'ml_analysis': asdict(config.ml_analysis),
            'logging_level': config.logging_level,
            'data_directory': config.data_directory,
            'results_directory': config.results_directory,
            'backup_directory': config.backup_directory
        }

def main():
    """Test the configuration manager"""
    # Test creating default config
    print("Creating default configuration...")
    config_manager = ConfigManager()
    
    # Save default config
    config_manager.save_config('test_config.json')
    print("Default configuration saved to test_config.json")
    
    # Test loading config
    print("\nLoading configuration...")
    config_manager2 = ConfigManager('test_config.json')
    
    # Test validation
    print("\nValidating configuration...")
    issues = config_manager2.validate_config()
    if issues:
        print("Validation issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid!")
    
    # Test updating configuration
    print("\nUpdating lab configuration...")
    config_manager2.update_lab_config(max_population=75, max_generations=150)
    
    # Test adding server
    print("\nAdding new server...")
    config_manager2.add_server_config('srv04', {
        'host': 'srv04',
        'ssh_port': 22,
        'api_ports': [8090, 8092],
        'max_population': 40,
        'max_concurrent_tasks': 4,
        'role': 'backtest',
        'ssh_user': 'root'
    })
    
    # Create backup
    print("\nCreating backup...")
    backup_file = config_manager2.create_backup()
    print(f"Backup created: {backup_file}")
    
    # Ensure directories exist
    print("\nEnsuring directories exist...")
    config_manager2.ensure_directories_exist()
    
    # Get system info
    print("\nSystem configuration summary:")
    print(f"  Servers: {len(config_manager2.get_all_server_configs())}")
    print(f"  Lab max population: {config_manager2.get_lab_config().max_population}")
    print(f"  Account initial balance: {config_manager2.get_account_settings().initial_balance}")
    print(f"  Directories: {config_manager2.get_system_directories()}")

if __name__ == "__main__":
    main()