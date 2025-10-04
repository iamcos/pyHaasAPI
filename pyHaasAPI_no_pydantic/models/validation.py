"""
Custom validation framework for pyHaasAPI_no_pydantic

Replaces Pydantic validators with custom validation logic
that provides better performance and clearer error messages.
"""

from typing import Any, Type, List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Validation error information"""
    field: str
    value: Any
    message: str
    code: str = "validation_error"


class Validator:
    """Custom validation framework"""
    
    @staticmethod
    def validate_positive_int(value: int, field_name: str) -> int:
        """Validate positive integer"""
        if not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
        if value <= 0:
            raise ValueError(f"{field_name} must be positive")
        return value
    
    @staticmethod
    def validate_non_negative_int(value: int, field_name: str) -> int:
        """Validate non-negative integer"""
        if not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative")
        return value
    
    @staticmethod
    def validate_positive_float(value: float, field_name: str) -> float:
        """Validate positive float"""
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number")
        if value <= 0:
            raise ValueError(f"{field_name} must be positive")
        return float(value)
    
    @staticmethod
    def validate_non_negative_float(value: float, field_name: str) -> float:
        """Validate non-negative float"""
        if not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number")
        if value < 0:
            raise ValueError(f"{field_name} must be non-negative")
        return float(value)
    
    @staticmethod
    def validate_string(value: str, field_name: str, min_length: int = 1) -> str:
        """Validate string"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        if len(value.strip()) < min_length:
            raise ValueError(f"{field_name} must be at least {min_length} characters")
        return value.strip()
    
    @staticmethod
    def validate_enum(value: str, field_name: str, valid_values: List[str]) -> str:
        """Validate enum value"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        if value.upper() not in [v.upper() for v in valid_values]:
            raise ValueError(f"{field_name} must be one of: {valid_values}")
        return value.upper()
    
    @staticmethod
    def validate_boolean(value: Any, field_name: str) -> bool:
        """Validate boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        if isinstance(value, int):
            return bool(value)
        raise ValueError(f"{field_name} must be a boolean")
    
    @staticmethod
    def validate_datetime(value: Any, field_name: str) -> Any:
        """Validate datetime"""
        if value is None:
            return None
        if hasattr(value, 'isoformat'):  # datetime object
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"{field_name} must be a valid datetime")
        raise ValueError(f"{field_name} must be a datetime")
    
    @staticmethod
    def validate_uuid(value: str, field_name: str) -> str:
        """Validate UUID format"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, value.lower()):
            raise ValueError(f"{field_name} must be a valid UUID")
        return value.lower()
    
    @staticmethod
    def validate_email(value: str, field_name: str) -> str:
        """Validate email format"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError(f"{field_name} must be a valid email address")
        return value.lower()
    
    @staticmethod
    def validate_url(value: str, field_name: str) -> str:
        """Validate URL format"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, value):
            raise ValueError(f"{field_name} must be a valid URL")
        return value
    
    @staticmethod
    def validate_range(value: Union[int, float], field_name: str, min_val: float = None, max_val: float = None) -> Union[int, float]:
        """Validate value is within range"""
        if min_val is not None and value < min_val:
            raise ValueError(f"{field_name} must be >= {min_val}")
        if max_val is not None and value > max_val:
            raise ValueError(f"{field_name} must be <= {max_val}")
        return value
    
    @staticmethod
    def validate_list_length(value: List[Any], field_name: str, min_length: int = 0, max_length: int = None) -> List[Any]:
        """Validate list length"""
        if not isinstance(value, list):
            raise ValueError(f"{field_name} must be a list")
        if len(value) < min_length:
            raise ValueError(f"{field_name} must have at least {min_length} items")
        if max_length is not None and len(value) > max_length:
            raise ValueError(f"{field_name} must have at most {max_length} items")
        return value
    
    @staticmethod
    def validate_dict_keys(value: Dict[str, Any], field_name: str, required_keys: List[str] = None, allowed_keys: List[str] = None) -> Dict[str, Any]:
        """Validate dictionary keys"""
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a dictionary")
        
        if required_keys:
            missing_keys = [key for key in required_keys if key not in value]
            if missing_keys:
                raise ValueError(f"{field_name} missing required keys: {missing_keys}")
        
        if allowed_keys:
            invalid_keys = [key for key in value.keys() if key not in allowed_keys]
            if invalid_keys:
                raise ValueError(f"{field_name} contains invalid keys: {invalid_keys}")
        
        return value


# Convenience functions for common validations
def positive_int(value: int, field_name: str) -> int:
    """Validate positive integer"""
    return Validator.validate_positive_int(value, field_name)


def non_negative_int(value: int, field_name: str) -> int:
    """Validate non-negative integer"""
    return Validator.validate_non_negative_int(value, field_name)


def positive_float(value: float, field_name: str) -> float:
    """Validate positive float"""
    return Validator.validate_positive_float(value, field_name)


def non_negative_float(value: float, field_name: str) -> float:
    """Validate non-negative float"""
    return Validator.validate_non_negative_float(value, field_name)


def non_empty_string(value: str, field_name: str) -> str:
    """Validate non-empty string"""
    return Validator.validate_string(value, field_name, min_length=1)


def enum_value(value: str, field_name: str, valid_values: List[str]) -> str:
    """Validate enum value"""
    return Validator.validate_enum(value, field_name, valid_values)


def boolean_value(value: Any, field_name: str) -> bool:
    """Validate boolean"""
    return Validator.validate_boolean(value, field_name)


def datetime_value(value: Any, field_name: str) -> Any:
    """Validate datetime"""
    return Validator.validate_datetime(value, field_name)


def uuid_value(value: str, field_name: str) -> str:
    """Validate UUID"""
    return Validator.validate_uuid(value, field_name)


def email_value(value: str, field_name: str) -> str:
    """Validate email"""
    return Validator.validate_email(value, field_name)


def url_value(value: str, field_name: str) -> str:
    """Validate URL"""
    return Validator.validate_url(value, field_name)


def range_value(value: Union[int, float], field_name: str, min_val: float = None, max_val: float = None) -> Union[int, float]:
    """Validate range"""
    return Validator.validate_range(value, field_name, min_val, max_val)


def list_length(value: List[Any], field_name: str, min_length: int = 0, max_length: int = None) -> List[Any]:
    """Validate list length"""
    return Validator.validate_list_length(value, field_name, min_length, max_length)


def dict_keys(value: Dict[str, Any], field_name: str, required_keys: List[str] = None, allowed_keys: List[str] = None) -> Dict[str, Any]:
    """Validate dictionary keys"""
    return Validator.validate_dict_keys(value, field_name, required_keys, allowed_keys)



