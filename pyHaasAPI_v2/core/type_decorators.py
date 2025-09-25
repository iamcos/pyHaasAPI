"""
Type Decorators for pyHaasAPI v2

This module provides decorators for automatic type checking and validation
of functions and methods.
"""

import functools
import inspect
import logging
from typing import (
    Any, Callable, Awaitable, TypeVar, Generic, Union, Optional, 
    get_type_hints, get_origin, get_args
)
from functools import wraps

from .type_validation import TypeValidator, TypeChecker, TypeValidationError
from .type_config import (
    is_type_checking_enabled, is_decorator_validation_enabled,
    is_async_validation_enabled, is_function_excluded
)
from .logging import get_logger

logger = get_logger("type_decorators")

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class TypeChecked:
    """
    Decorator class for type checking.
    
    Provides configurable type checking for functions and methods
    with support for both sync and async functions.
    """

    def __init__(
        self,
        strict: bool = False,
        validate_inputs: bool = True,
        validate_outputs: bool = True,
        log_errors: bool = True,
        raise_on_error: bool = False
    ):
        self.strict = strict
        self.validate_inputs = validate_inputs
        self.validate_outputs = validate_outputs
        self.log_errors = log_errors
        self.raise_on_error = raise_on_error
        self.validator = TypeValidator(strict_mode=strict)

    def __call__(self, func: F) -> F:
        """Apply type checking decorator to function"""
        # Check if type checking is enabled
        if not is_type_checking_enabled() or not is_decorator_validation_enabled():
            return func

        # Check if function is excluded
        if is_function_excluded(func.__name__):
            return func

        # Check if function is async
        if inspect.iscoroutinefunction(func):
            if not is_async_validation_enabled():
                return func
            return self._wrap_async_function(func)
        else:
            return self._wrap_sync_function(func)

    def _wrap_sync_function(self, func: F) -> F:
        """Wrap sync function with type checking"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate inputs
                if self.validate_inputs:
                    result = self.validator.validate_function_args(func, args, kwargs)
                    if not result.is_valid:
                        error_msg = f"Input validation failed for {func.__name__}: {result.error_message}"
                        if self.log_errors:
                            logger.error(error_msg)
                        if self.raise_on_error:
                            raise TypeValidationError(error_msg)

                # Execute function
                return_value = func(*args, **kwargs)

                # Validate outputs
                if self.validate_outputs:
                    result = self.validator.validate_function_return(func, return_value)
                    if not result.is_valid:
                        error_msg = f"Output validation failed for {func.__name__}: {result.error_message}"
                        if self.log_errors:
                            logger.error(error_msg)
                        if self.raise_on_error:
                            raise TypeValidationError(error_msg)

                return return_value

            except Exception as e:
                if isinstance(e, TypeValidationError):
                    raise
                if self.log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                raise

        return wrapper

    def _wrap_async_function(self, func: F) -> F:
        """Wrap async function with type checking"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Validate inputs
                if self.validate_inputs:
                    result = self.validator.validate_function_args(func, args, kwargs)
                    if not result.is_valid:
                        error_msg = f"Input validation failed for {func.__name__}: {result.error_message}"
                        if self.log_errors:
                            logger.error(error_msg)
                        if self.raise_on_error:
                            raise TypeValidationError(error_msg)

                # Execute function
                return_value = await func(*args, **kwargs)

                # Validate outputs
                if self.validate_outputs:
                    result = self.validator.validate_function_return(func, return_value)
                    if not result.is_valid:
                        error_msg = f"Output validation failed for {func.__name__}: {result.error_message}"
                        if self.log_errors:
                            logger.error(error_msg)
                        if self.raise_on_error:
                            raise TypeValidationError(error_msg)

                return return_value

            except Exception as e:
                if isinstance(e, TypeValidationError):
                    raise
                if self.log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                raise

        return wrapper


class TypeValidated:
    """
    Decorator for type validation with custom validation logic.
    
    Allows custom validation functions to be applied to function
    arguments and return values.
    """

    def __init__(
        self,
        input_validator: Optional[Callable[[Any], bool]] = None,
        output_validator: Optional[Callable[[Any], bool]] = None,
        error_message: Optional[str] = None
    ):
        self.input_validator = input_validator
        self.output_validator = output_validator
        self.error_message = error_message or "Validation failed"

    def __call__(self, func: F) -> F:
        """Apply type validation decorator to function"""
        # Check if type checking is enabled
        if not is_type_checking_enabled() or not is_decorator_validation_enabled():
            return func

        # Check if function is excluded
        if is_function_excluded(func.__name__):
            return func

        # Check if function is async
        if inspect.iscoroutinefunction(func):
            if not is_async_validation_enabled():
                return func
            return self._wrap_async_function(func)
        else:
            return self._wrap_sync_function(func)

    def _wrap_sync_function(self, func: F) -> F:
        """Wrap sync function with custom validation"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate inputs
            if self.input_validator:
                for arg in args:
                    if not self.input_validator(arg):
                        error_msg = f"Input validation failed for {func.__name__}: {self.error_message}"
                        logger.error(error_msg)
                        raise TypeValidationError(error_msg)
                
                for value in kwargs.values():
                    if not self.input_validator(value):
                        error_msg = f"Input validation failed for {func.__name__}: {self.error_message}"
                        logger.error(error_msg)
                        raise TypeValidationError(error_msg)

            # Execute function
            return_value = func(*args, **kwargs)

            # Validate outputs
            if self.output_validator:
                if not self.output_validator(return_value):
                    error_msg = f"Output validation failed for {func.__name__}: {self.error_message}"
                    logger.error(error_msg)
                    raise TypeValidationError(error_msg)

            return return_value

        return wrapper

    def _wrap_async_function(self, func: F) -> F:
        """Wrap async function with custom validation"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Validate inputs
            if self.input_validator:
                for arg in args:
                    if not self.input_validator(arg):
                        error_msg = f"Input validation failed for {func.__name__}: {self.error_message}"
                        logger.error(error_msg)
                        raise TypeValidationError(error_msg)
                
                for value in kwargs.values():
                    if not self.input_validator(value):
                        error_msg = f"Input validation failed for {func.__name__}: {self.error_message}"
                        logger.error(error_msg)
                        raise TypeValidationError(error_msg)

            # Execute function
            return_value = await func(*args, **kwargs)

            # Validate outputs
            if self.output_validator:
                if not self.output_validator(return_value):
                    error_msg = f"Output validation failed for {func.__name__}: {self.error_message}"
                    logger.error(error_msg)
                    raise TypeValidationError(error_msg)

            return return_value

        return wrapper


class TypeConverted:
    """
    Decorator for automatic type conversion.
    
    Automatically converts function arguments and return values
    to the expected types based on type hints.
    """

    def __init__(
        self,
        convert_inputs: bool = True,
        convert_outputs: bool = True,
        strict_conversion: bool = False
    ):
        self.convert_inputs = convert_inputs
        self.convert_outputs = convert_outputs
        self.strict_conversion = strict_conversion

    def __call__(self, func: F) -> F:
        """Apply type conversion decorator to function"""
        # Check if type checking is enabled
        if not is_type_checking_enabled() or not is_decorator_validation_enabled():
            return func

        # Check if function is excluded
        if is_function_excluded(func.__name__):
            return func

        # Check if function is async
        if inspect.iscoroutinefunction(func):
            if not is_async_validation_enabled():
                return func
            return self._wrap_async_function(func)
        else:
            return self._wrap_sync_function(func)

    def _wrap_sync_function(self, func: F) -> F:
        """Wrap sync function with type conversion"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Convert inputs
            if self.convert_inputs:
                converted_args = self._convert_args(func, args)
                converted_kwargs = self._convert_kwargs(func, kwargs)
            else:
                converted_args = args
                converted_kwargs = kwargs

            # Execute function
            return_value = func(*converted_args, **converted_kwargs)

            # Convert outputs
            if self.convert_outputs:
                return_value = self._convert_return_value(func, return_value)

            return return_value

        return wrapper

    def _wrap_async_function(self, func: F) -> F:
        """Wrap async function with type conversion"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Convert inputs
            if self.convert_inputs:
                converted_args = self._convert_args(func, args)
                converted_kwargs = self._convert_kwargs(func, kwargs)
            else:
                converted_args = args
                converted_kwargs = kwargs

            # Execute function
            return_value = await func(*converted_args, **converted_kwargs)

            # Convert outputs
            if self.convert_outputs:
                return_value = self._convert_return_value(func, return_value)

            return return_value

        return wrapper

    def _convert_args(self, func: Callable, args: tuple) -> tuple:
        """Convert function arguments"""
        try:
            hints = get_type_hints(func)
            if not hints:
                return args

            sig = inspect.signature(func)
            bound_args = sig.bind(*args)
            bound_args.apply_defaults()

            converted_args = []
            for param_name, param_value in bound_args.arguments.items():
                if param_name in hints:
                    expected_type = hints[param_name]
                    converted_value = self._convert_value(param_value, expected_type)
                    converted_args.append(converted_value)
                else:
                    converted_args.append(param_value)

            return tuple(converted_args)
        except Exception as e:
            logger.warning(f"Failed to convert arguments for {func.__name__}: {e}")
            return args

    def _convert_kwargs(self, func: Callable, kwargs: dict) -> dict:
        """Convert function keyword arguments"""
        try:
            hints = get_type_hints(func)
            if not hints:
                return kwargs

            converted_kwargs = {}
            for key, value in kwargs.items():
                if key in hints:
                    expected_type = hints[key]
                    converted_value = self._convert_value(value, expected_type)
                    converted_kwargs[key] = converted_value
                else:
                    converted_kwargs[key] = value

            return converted_kwargs
        except Exception as e:
            logger.warning(f"Failed to convert kwargs for {func.__name__}: {e}")
            return kwargs

    def _convert_return_value(self, func: Callable, return_value: Any) -> Any:
        """Convert function return value"""
        try:
            hints = get_type_hints(func)
            if 'return' not in hints:
                return return_value

            expected_type = hints['return']
            return self._convert_value(return_value, expected_type)
        except Exception as e:
            logger.warning(f"Failed to convert return value for {func.__name__}: {e}")
            return return_value

    def _convert_value(self, value: Any, expected_type: type) -> Any:
        """Convert a value to expected type"""
        try:
            # Handle None values
            if value is None:
                return value

            # Handle direct type conversion
            if isinstance(value, expected_type):
                return value

            # Handle Union types
            if hasattr(expected_type, '__origin__') and expected_type.__origin__ is Union:
                for arg in expected_type.__args__:
                    try:
                        return self._convert_value(value, arg)
                    except (TypeError, ValueError):
                        continue
                raise TypeError(f"Cannot convert {type(value)} to {expected_type}")

            # Handle generic types
            origin = get_origin(expected_type)
            if origin is not None:
                return self._convert_generic_value(value, expected_type, origin)

            # Handle basic type conversions
            if expected_type is str:
                return str(value)
            elif expected_type is int:
                return int(value)
            elif expected_type is float:
                return float(value)
            elif expected_type is bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)

            # Handle enum types
            if hasattr(expected_type, '__members__'):
                if isinstance(value, expected_type):
                    return value
                elif isinstance(value, str):
                    return expected_type(value)
                else:
                    raise TypeError(f"Cannot convert {type(value)} to {expected_type}")

            # Handle dataclass types
            if hasattr(expected_type, '__dataclass_fields__'):
                if isinstance(value, expected_type):
                    return value
                elif isinstance(value, dict):
                    return expected_type(**value)
                else:
                    raise TypeError(f"Cannot convert {type(value)} to {expected_type}")

            raise TypeError(f"No conversion available from {type(value)} to {expected_type}")

        except Exception as e:
            if self.strict_conversion:
                raise
            logger.warning(f"Type conversion failed: {e}")
            return value

    def _convert_generic_value(self, value: Any, expected_type: type, origin: type) -> Any:
        """Convert generic type values"""
        args = get_args(expected_type)

        if origin is list or origin is List:
            if isinstance(value, (list, tuple)):
                if args:
                    return [self._convert_value(item, args[0]) for item in value]
                return list(value)
            else:
                if args:
                    return [self._convert_value(value, args[0])]
                return [value]

        elif origin is dict or origin is Dict:
            if isinstance(value, dict):
                if args:
                    key_type, value_type = args
                    return {
                        self._convert_value(k, key_type): self._convert_value(v, value_type)
                        for k, v in value.items()
                    }
                return value
            else:
                raise TypeError(f"Cannot convert {type(value)} to dict")

        elif origin is tuple or origin is Tuple:
            if isinstance(value, (list, tuple)):
                if args:
                    if len(args) == 2 and args[1] is Ellipsis:
                        # Tuple[T, ...]
                        return tuple(self._convert_value(item, args[0]) for item in value)
                    else:
                        # Tuple[T1, T2, ...]
                        if len(value) != len(args):
                            raise ValueError(f"Expected {len(args)} items, got {len(value)}")
                        return tuple(self._convert_value(item, arg) for item, arg in zip(value, args))
                return tuple(value)
            else:
                if args:
                    return (self._convert_value(value, args[0]),)
                return (value,)

        return value


# Convenience decorators
def type_checked(
    strict: bool = False,
    validate_inputs: bool = True,
    validate_outputs: bool = True,
    log_errors: bool = True,
    raise_on_error: bool = False
) -> Callable[[F], F]:
    """Decorator for type checking"""
    return TypeChecked(
        strict=strict,
        validate_inputs=validate_inputs,
        validate_outputs=validate_outputs,
        log_errors=log_errors,
        raise_on_error=raise_on_error
    )


def type_validated(
    input_validator: Optional[Callable[[Any], bool]] = None,
    output_validator: Optional[Callable[[Any], bool]] = None,
    error_message: Optional[str] = None
) -> Callable[[F], F]:
    """Decorator for custom type validation"""
    return TypeValidated(
        input_validator=input_validator,
        output_validator=output_validator,
        error_message=error_message
    )


def type_converted(
    convert_inputs: bool = True,
    convert_outputs: bool = True,
    strict_conversion: bool = False
) -> Callable[[F], F]:
    """Decorator for automatic type conversion"""
    return TypeConverted(
        convert_inputs=convert_inputs,
        convert_outputs=convert_outputs,
        strict_conversion=strict_conversion
    )


# Shorthand decorators
def strict_type_checked(func: F) -> F:
    """Strict type checking decorator"""
    return TypeChecked(strict=True, raise_on_error=True)(func)


def lenient_type_checked(func: F) -> F:
    """Lenient type checking decorator"""
    return TypeChecked(strict=False, log_errors=False, raise_on_error=False)(func)


def auto_convert(func: F) -> F:
    """Automatic type conversion decorator"""
    return TypeConverted(convert_inputs=True, convert_outputs=True)(func)
