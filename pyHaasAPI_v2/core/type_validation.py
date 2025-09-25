"""
Type Validation for pyHaasAPI v2

This module provides comprehensive type validation and type checking utilities
for ensuring type safety throughout the codebase.
"""

import inspect
import typing
from typing import (
    Any, Type, TypeVar, Generic, Union, Optional, List, Dict, Tuple, 
    Callable, Awaitable, get_type_hints, get_origin, get_args
)
from functools import wraps
from dataclasses import dataclass, is_dataclass
from enum import Enum
import logging

from .logging import get_logger

logger = get_logger("type_validation")

T = TypeVar('T')


@dataclass
class ValidationResult:
    """Result of type validation"""
    is_valid: bool
    error_message: Optional[str] = None
    validated_value: Any = None


class TypeValidationError(Exception):
    """Exception raised when type validation fails"""
    pass


class TypeValidator:
    """
    Comprehensive type validator for runtime type checking.
    
    Provides runtime type validation for function arguments, return values,
    and data structures with detailed error reporting.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.logger = get_logger("type_validator")

    def validate_type(self, value: Any, expected_type: Type[T]) -> ValidationResult:
        """
        Validate a value against an expected type.
        
        Args:
            value: The value to validate
            expected_type: The expected type
            
        Returns:
            ValidationResult with validation details
        """
        try:
            if self._is_valid_type(value, expected_type):
                return ValidationResult(is_valid=True, validated_value=value)
            else:
                error_msg = f"Expected {expected_type.__name__}, got {type(value).__name__}"
                return ValidationResult(is_valid=False, error_message=error_msg)
        except Exception as e:
            return ValidationResult(is_valid=False, error_message=str(e))

    def _is_valid_type(self, value: Any, expected_type: Type[T]) -> bool:
        """Check if value matches expected type"""
        # Handle None values
        if value is None:
            return expected_type is type(None) or get_origin(expected_type) is Union and type(None) in get_args(expected_type)
        
        # Handle direct type matches
        if isinstance(value, expected_type):
            return True
        
        # Handle generic types
        origin = get_origin(expected_type)
        if origin is not None:
            return self._validate_generic_type(value, expected_type, origin)
        
        # Handle Union types
        if hasattr(expected_type, '__origin__') and expected_type.__origin__ is Union:
            return any(self._is_valid_type(value, arg) for arg in expected_type.__args__)
        
        # Handle Optional types
        if hasattr(expected_type, '__origin__') and expected_type.__origin__ is Union:
            args = expected_type.__args__
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return self._is_valid_type(value, non_none_type)
        
        # Handle callable types
        if expected_type is Callable:
            return callable(value)
        
        # Handle dataclass types
        if is_dataclass(expected_type):
            return isinstance(value, expected_type)
        
        # Handle enum types
        if issubclass(expected_type, Enum):
            return isinstance(value, expected_type)
        
        return False

    def _validate_generic_type(self, value: Any, expected_type: Type[T], origin: Type) -> bool:
        """Validate generic types like List, Dict, etc."""
        args = get_args(expected_type)
        
        if origin is list or origin is List:
            if not isinstance(value, list):
                return False
            if args and self.strict_mode:
                return all(self._is_valid_type(item, args[0]) for item in value)
            return True
        
        elif origin is dict or origin is Dict:
            if not isinstance(value, dict):
                return False
            if args and self.strict_mode:
                key_type, value_type = args
                return all(
                    self._is_valid_type(k, key_type) and self._is_valid_type(v, value_type)
                    for k, v in value.items()
                )
            return True
        
        elif origin is tuple or origin is Tuple:
            if not isinstance(value, tuple):
                return False
            if args and self.strict_mode:
                if len(args) == 2 and args[1] is Ellipsis:
                    # Tuple[T, ...]
                    return all(self._is_valid_type(item, args[0]) for item in value)
                else:
                    # Tuple[T1, T2, ...]
                    if len(value) != len(args):
                        return False
                    return all(self._is_valid_type(item, arg) for item, arg in zip(value, args))
            return True
        
        elif origin is set or origin is set:
            if not isinstance(value, set):
                return False
            if args and self.strict_mode:
                return all(self._is_valid_type(item, args[0]) for item in value)
            return True
        
        return False

    def validate_function_args(self, func: Callable, args: tuple, kwargs: dict) -> ValidationResult:
        """
        Validate function arguments against type hints.
        
        Args:
            func: The function to validate
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            ValidationResult with validation details
        """
        try:
            # Get type hints
            hints = get_type_hints(func)
            if not hints:
                return ValidationResult(is_valid=True)
            
            # Get function signature
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each argument
            for param_name, param_value in bound_args.arguments.items():
                if param_name in hints:
                    expected_type = hints[param_name]
                    result = self.validate_type(param_value, expected_type)
                    if not result.is_valid:
                        error_msg = f"Argument '{param_name}': {result.error_message}"
                        return ValidationResult(is_valid=False, error_message=error_msg)
            
            return ValidationResult(is_valid=True)
        except Exception as e:
            return ValidationResult(is_valid=False, error_message=str(e))

    def validate_function_return(self, func: Callable, return_value: Any) -> ValidationResult:
        """
        Validate function return value against type hints.
        
        Args:
            func: The function to validate
            return_value: The return value
            
        Returns:
            ValidationResult with validation details
        """
        try:
            # Get type hints
            hints = get_type_hints(func)
            if 'return' not in hints:
                return ValidationResult(is_valid=True)
            
            expected_type = hints['return']
            return self.validate_type(return_value, expected_type)
        except Exception as e:
            return ValidationResult(is_valid=False, error_message=str(e))


class TypeChecker:
    """
    Type checker for runtime type validation.
    
    Provides decorators and utilities for automatic type checking
    of functions and methods.
    """

    def __init__(self, validator: Optional[TypeValidator] = None):
        self.validator = validator or TypeValidator()
        self.logger = get_logger("type_checker")

    def check_types(self, func: Callable) -> Callable:
        """
        Decorator to check function argument and return types.
        
        Args:
            func: The function to decorate
            
        Returns:
            Decorated function with type checking
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate arguments
            result = self.validator.validate_function_args(func, args, kwargs)
            if not result.is_valid:
                error_msg = f"Type validation failed for {func.__name__}: {result.error_message}"
                self.logger.error(error_msg)
                if self.validator.strict_mode:
                    raise TypeValidationError(error_msg)
            
            # Execute function
            return_value = func(*args, **kwargs)
            
            # Validate return value
            result = self.validator.validate_function_return(func, return_value)
            if not result.is_valid:
                error_msg = f"Return type validation failed for {func.__name__}: {result.error_message}"
                self.logger.error(error_msg)
                if self.validator.strict_mode:
                    raise TypeValidationError(error_msg)
            
            return return_value
        
        return wrapper

    def check_async_types(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        """
        Decorator to check async function argument and return types.
        
        Args:
            func: The async function to decorate
            
        Returns:
            Decorated async function with type checking
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Validate arguments
            result = self.validator.validate_function_args(func, args, kwargs)
            if not result.is_valid:
                error_msg = f"Type validation failed for {func.__name__}: {result.error_message}"
                self.logger.error(error_msg)
                if self.validator.strict_mode:
                    raise TypeValidationError(error_msg)
            
            # Execute function
            return_value = await func(*args, **kwargs)
            
            # Validate return value
            result = self.validator.validate_function_return(func, return_value)
            if not result.is_valid:
                error_msg = f"Return type validation failed for {func.__name__}: {result.error_message}"
                self.logger.error(error_msg)
                if self.validator.strict_mode:
                    raise TypeValidationError(error_msg)
            
            return return_value
        
        return wrapper


class TypeGuard:
    """
    Type guard utilities for runtime type checking.
    
    Provides type guard functions for common type checking patterns.
    """

    @staticmethod
    def is_list_of_type(value: Any, item_type: Type[T]) -> bool:
        """Check if value is a list of specific type"""
        if not isinstance(value, list):
            return False
        return all(isinstance(item, item_type) for item in value)

    @staticmethod
    def is_dict_of_types(value: Any, key_type: Type, value_type: Type) -> bool:
        """Check if value is a dict with specific key and value types"""
        if not isinstance(value, dict):
            return False
        return all(
            isinstance(k, key_type) and isinstance(v, value_type)
            for k, v in value.items()
        )

    @staticmethod
    def is_optional_type(value: Any, base_type: Type[T]) -> bool:
        """Check if value is optional (None or base_type)"""
        return value is None or isinstance(value, base_type)

    @staticmethod
    def is_union_type(value: Any, types: Tuple[Type, ...]) -> bool:
        """Check if value is one of the union types"""
        return any(isinstance(value, t) for t in types)

    @staticmethod
    def is_callable_with_signature(value: Any, expected_signature: inspect.Signature) -> bool:
        """Check if value is callable with expected signature"""
        if not callable(value):
            return False
        try:
            actual_signature = inspect.signature(value)
            return actual_signature == expected_signature
        except ValueError:
            return False


class TypeConverter:
    """
    Type converter for safe type conversions.
    
    Provides safe type conversion utilities with validation.
    """

    def __init__(self, validator: Optional[TypeValidator] = None):
        self.validator = validator or TypeValidator()
        self.logger = get_logger("type_converter")

    def convert_to_type(self, value: Any, target_type: Type[T]) -> T:
        """
        Convert value to target type with validation.
        
        Args:
            value: The value to convert
            target_type: The target type
            
        Returns:
            Converted value
            
        Raises:
            TypeValidationError: If conversion fails
        """
        try:
            # Check if already correct type
            if self.validator._is_valid_type(value, target_type):
                return value
            
            # Handle None values
            if value is None:
                if target_type is type(None):
                    return value
                elif get_origin(target_type) is Union and type(None) in get_args(target_type):
                    return value
                else:
                    raise TypeValidationError(f"Cannot convert None to {target_type.__name__}")
            
            # Handle string conversions
            if target_type is str:
                return str(value)
            
            # Handle numeric conversions
            if target_type is int:
                return int(value)
            elif target_type is float:
                return float(value)
            elif target_type is bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            
            # Handle list conversions
            if get_origin(target_type) is list or target_type is list:
                if isinstance(value, (list, tuple)):
                    return list(value)
                else:
                    return [value]
            
            # Handle dict conversions
            if get_origin(target_type) is dict or target_type is dict:
                if isinstance(value, dict):
                    return value
                else:
                    raise TypeValidationError(f"Cannot convert {type(value).__name__} to dict")
            
            # Handle enum conversions
            if issubclass(target_type, Enum):
                if isinstance(value, target_type):
                    return value
                elif isinstance(value, str):
                    return target_type(value)
                else:
                    raise TypeValidationError(f"Cannot convert {type(value).__name__} to {target_type.__name__}")
            
            # Handle dataclass conversions
            if is_dataclass(target_type):
                if isinstance(value, target_type):
                    return value
                elif isinstance(value, dict):
                    return target_type(**value)
                else:
                    raise TypeValidationError(f"Cannot convert {type(value).__name__} to {target_type.__name__}")
            
            raise TypeValidationError(f"No conversion available from {type(value).__name__} to {target_type.__name__}")
            
        except Exception as e:
            if isinstance(e, TypeValidationError):
                raise
            raise TypeValidationError(f"Conversion failed: {e}")

    def safe_convert(self, value: Any, target_type: Type[T], default: Optional[T] = None) -> Optional[T]:
        """
        Safely convert value to target type with fallback.
        
        Args:
            value: The value to convert
            target_type: The target type
            default: Default value if conversion fails
            
        Returns:
            Converted value or default
        """
        try:
            return self.convert_to_type(value, target_type)
        except TypeValidationError:
            return default


# Global instances
default_validator = TypeValidator()
default_checker = TypeChecker(default_validator)
default_converter = TypeConverter(default_validator)

# Convenience decorators
def type_check(func: Callable) -> Callable:
    """Decorator for type checking"""
    return default_checker.check_types(func)

def async_type_check(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator for async type checking"""
    return default_checker.check_async_types(func)

# Convenience functions
def validate_type(value: Any, expected_type: Type[T]) -> ValidationResult:
    """Validate a value against an expected type"""
    return default_validator.validate_type(value, expected_type)

def convert_to_type(value: Any, target_type: Type[T]) -> T:
    """Convert value to target type"""
    return default_converter.convert_to_type(value, target_type)

def safe_convert(value: Any, target_type: Type[T], default: Optional[T] = None) -> Optional[T]:
    """Safely convert value to target type"""
    return default_converter.safe_convert(value, target_type, default)
