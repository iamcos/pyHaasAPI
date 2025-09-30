"""
Type Configuration for pyHaasAPI v2

This module provides configuration for type checking and validation
throughout the codebase.
"""

import os
import sys
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .type_definitions import ValidationLevel, ValidationConfig


class TypeCheckingMode(Enum):
    """Type checking modes"""
    DISABLED = "disabled"
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class TypeCheckingConfig:
    """Configuration for type checking"""
    mode: TypeCheckingMode = TypeCheckingMode.BASIC
    enable_runtime_validation: bool = True
    enable_decorator_validation: bool = True
    enable_async_validation: bool = True
    strict_mode: bool = False
    log_validation_errors: bool = True
    raise_on_validation_error: bool = False
    validation_level: ValidationLevel = ValidationLevel.BASIC
    excluded_modules: Set[str] = field(default_factory=set)
    excluded_functions: Set[str] = field(default_factory=set)
    custom_validators: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TypeValidationSettings:
    """Settings for type validation"""
    validate_inputs: bool = True
    validate_outputs: bool = True
    validate_types: bool = True
    validate_ranges: bool = True
    validate_required_fields: bool = True
    validate_enum_values: bool = True
    validate_dataclass_fields: bool = True
    validate_union_types: bool = True
    validate_generic_types: bool = True
    validate_callable_types: bool = True


class TypeConfigManager:
    """
    Manager for type checking configuration.
    
    Provides centralized configuration management for type checking
    and validation throughout the codebase.
    """

    def __init__(self):
        self.config = TypeCheckingConfig()
        self.validation_settings = TypeValidationSettings()
        self._load_from_environment()
        self._load_from_file()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        # Type checking mode
        mode_str = os.getenv('PYHAASAPI_TYPE_CHECKING_MODE', 'basic').lower()
        try:
            self.config.mode = TypeCheckingMode(mode_str)
        except ValueError:
            self.config.mode = TypeCheckingMode.BASIC

        # Runtime validation
        self.config.enable_runtime_validation = os.getenv(
            'PYHAASAPI_ENABLE_RUNTIME_VALIDATION', 'true'
        ).lower() == 'true'

        # Decorator validation
        self.config.enable_decorator_validation = os.getenv(
            'PYHAASAPI_ENABLE_DECORATOR_VALIDATION', 'true'
        ).lower() == 'true'

        # Async validation
        self.config.enable_async_validation = os.getenv(
            'PYHAASAPI_ENABLE_ASYNC_VALIDATION', 'true'
        ).lower() == 'true'

        # Strict mode
        self.config.strict_mode = os.getenv(
            'PYHAASAPI_STRICT_MODE', 'false'
        ).lower() == 'true'

        # Log validation errors
        self.config.log_validation_errors = os.getenv(
            'PYHAASAPI_LOG_VALIDATION_ERRORS', 'true'
        ).lower() == 'true'

        # Raise on validation error
        self.config.raise_on_validation_error = os.getenv(
            'PYHAASAPI_RAISE_ON_VALIDATION_ERROR', 'false'
        ).lower() == 'true'

        # Validation level
        level_str = os.getenv('PYHAASAPI_VALIDATION_LEVEL', 'basic').lower()
        try:
            self.config.validation_level = ValidationLevel(level_str)
        except ValueError:
            self.config.validation_level = ValidationLevel.BASIC

        # Excluded modules
        excluded_modules_str = os.getenv('PYHAASAPI_EXCLUDED_MODULES', '')
        if excluded_modules_str:
            self.config.excluded_modules = set(
                module.strip() for module in excluded_modules_str.split(',')
            )

        # Excluded functions
        excluded_functions_str = os.getenv('PYHAASAPI_EXCLUDED_FUNCTIONS', '')
        if excluded_functions_str:
            self.config.excluded_functions = set(
                func.strip() for func in excluded_functions_str.split(',')
            )

    def _load_from_file(self) -> None:
        """Load configuration from file"""
        config_file = Path('pyhaasapi_type_config.json')
        if config_file.exists():
            try:
                import json
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                self._apply_config_data(config_data)
            except Exception as e:
                print(f"Warning: Failed to load type config from file: {e}")

    def _apply_config_data(self, config_data: Dict[str, Any]) -> None:
        """Apply configuration data"""
        if 'mode' in config_data:
            try:
                self.config.mode = TypeCheckingMode(config_data['mode'])
            except ValueError:
                pass

        if 'enable_runtime_validation' in config_data:
            self.config.enable_runtime_validation = config_data['enable_runtime_validation']

        if 'enable_decorator_validation' in config_data:
            self.config.enable_decorator_validation = config_data['enable_decorator_validation']

        if 'enable_async_validation' in config_data:
            self.config.enable_async_validation = config_data['enable_async_validation']

        if 'strict_mode' in config_data:
            self.config.strict_mode = config_data['strict_mode']

        if 'log_validation_errors' in config_data:
            self.config.log_validation_errors = config_data['log_validation_errors']

        if 'raise_on_validation_error' in config_data:
            self.config.raise_on_validation_error = config_data['raise_on_validation_error']

        if 'validation_level' in config_data:
            try:
                self.config.validation_level = ValidationLevel(config_data['validation_level'])
            except ValueError:
                pass

        if 'excluded_modules' in config_data:
            self.config.excluded_modules = set(config_data['excluded_modules'])

        if 'excluded_functions' in config_data:
            self.config.excluded_functions = set(config_data['excluded_functions'])

        if 'validation_settings' in config_data:
            settings_data = config_data['validation_settings']
            for key, value in settings_data.items():
                if hasattr(self.validation_settings, key):
                    setattr(self.validation_settings, key, value)

    def is_type_checking_enabled(self) -> bool:
        """Check if type checking is enabled"""
        return self.config.mode != TypeCheckingMode.DISABLED

    def is_runtime_validation_enabled(self) -> bool:
        """Check if runtime validation is enabled"""
        return (self.is_type_checking_enabled() and 
                self.config.enable_runtime_validation)

    def is_decorator_validation_enabled(self) -> bool:
        """Check if decorator validation is enabled"""
        return (self.is_type_checking_enabled() and 
                self.config.enable_decorator_validation)

    def is_async_validation_enabled(self) -> bool:
        """Check if async validation is enabled"""
        return (self.is_type_checking_enabled() and 
                self.config.enable_async_validation)

    def is_module_excluded(self, module_name: str) -> bool:
        """Check if module is excluded from type checking"""
        return module_name in self.config.excluded_modules

    def is_function_excluded(self, function_name: str) -> bool:
        """Check if function is excluded from type checking"""
        return function_name in self.config.excluded_functions

    def get_validation_config(self) -> ValidationConfig:
        """Get validation configuration"""
        return ValidationConfig(
            level=self.config.validation_level,
            validate_inputs=self.validation_settings.validate_inputs,
            validate_outputs=self.validation_settings.validate_outputs,
            validate_types=self.validation_settings.validate_types,
            validate_ranges=self.validation_settings.validate_ranges
        )

    def update_config(self, **kwargs) -> None:
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif hasattr(self.validation_settings, key):
                setattr(self.validation_settings, key, value)

    def save_config(self, file_path: Optional[str] = None) -> None:
        """Save configuration to file"""
        if file_path is None:
            file_path = 'pyhaasapi_type_config.json'

        config_data = {
            'mode': self.config.mode.value,
            'enable_runtime_validation': self.config.enable_runtime_validation,
            'enable_decorator_validation': self.config.enable_decorator_validation,
            'enable_async_validation': self.config.enable_async_validation,
            'strict_mode': self.config.strict_mode,
            'log_validation_errors': self.config.log_validation_errors,
            'raise_on_validation_error': self.config.raise_on_validation_error,
            'validation_level': self.config.validation_level.value,
            'excluded_modules': list(self.config.excluded_modules),
            'excluded_functions': list(self.config.excluded_functions),
            'validation_settings': {
                'validate_inputs': self.validation_settings.validate_inputs,
                'validate_outputs': self.validation_settings.validate_outputs,
                'validate_types': self.validation_settings.validate_types,
                'validate_ranges': self.validation_settings.validate_ranges,
                'validate_required_fields': self.validation_settings.validate_required_fields,
                'validate_enum_values': self.validation_settings.validate_enum_values,
                'validate_dataclass_fields': self.validation_settings.validate_dataclass_fields,
                'validate_union_types': self.validation_settings.validate_union_types,
                'validate_generic_types': self.validation_settings.validate_generic_types,
                'validate_callable_types': self.validation_settings.validate_callable_types,
            }
        }

        try:
            import json
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save type config to file: {e}")

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            'mode': self.config.mode.value,
            'runtime_validation_enabled': self.is_runtime_validation_enabled(),
            'decorator_validation_enabled': self.is_decorator_validation_enabled(),
            'async_validation_enabled': self.is_async_validation_enabled(),
            'strict_mode': self.config.strict_mode,
            'validation_level': self.config.validation_level.value,
            'excluded_modules_count': len(self.config.excluded_modules),
            'excluded_functions_count': len(self.config.excluded_functions),
            'validation_settings': {
                'validate_inputs': self.validation_settings.validate_inputs,
                'validate_outputs': self.validation_settings.validate_outputs,
                'validate_types': self.validation_settings.validate_types,
                'validate_ranges': self.validation_settings.validate_ranges,
            }
        }


# Global configuration manager
type_config_manager = TypeConfigManager()


def get_type_config() -> TypeCheckingConfig:
    """Get type checking configuration"""
    return type_config_manager.config


def get_validation_settings() -> TypeValidationSettings:
    """Get validation settings"""
    return type_config_manager.validation_settings


def is_type_checking_enabled() -> bool:
    """Check if type checking is enabled"""
    return type_config_manager.is_type_checking_enabled()


def is_runtime_validation_enabled() -> bool:
    """Check if runtime validation is enabled"""
    return type_config_manager.is_runtime_validation_enabled()


def is_decorator_validation_enabled() -> bool:
    """Check if decorator validation is enabled"""
    return type_config_manager.is_decorator_validation_enabled()


def is_async_validation_enabled() -> bool:
    """Check if async validation is enabled"""
    return type_config_manager.is_async_validation_enabled()


def is_module_excluded(module_name: str) -> bool:
    """Check if module is excluded from type checking"""
    return type_config_manager.is_module_excluded(module_name)


def is_function_excluded(function_name: str) -> bool:
    """Check if function is excluded from type checking"""
    return type_config_manager.is_function_excluded(function_name)


def update_type_config(**kwargs) -> None:
    """Update type configuration"""
    type_config_manager.update_config(**kwargs)


def save_type_config(file_path: Optional[str] = None) -> None:
    """Save type configuration to file"""
    type_config_manager.save_config(file_path)


def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary"""
    return type_config_manager.get_config_summary()
