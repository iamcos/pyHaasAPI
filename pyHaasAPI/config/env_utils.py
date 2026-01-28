
import os
from typing import Any, Type, TypeVar, Optional, List

T = TypeVar("T")

def get_env(key: str, default: Any = None, cast: Type[T] = str) -> T:
    """
    Get environment variable with type casting and default value.
    
    Args:
        key: Environment variable key
        default: Default value if key not found
        cast: Type to cast the value to (str, int, float, bool, list)
        
    Returns:
        The environment variable value cast to the specified type, or default.
    """
    value = os.getenv(key)
    if value is None:
        return default
    
    if cast == bool:
        return value.lower() in ("true", "1", "t", "y", "yes", "on")
    
    if cast == list:
        # Assumes comma-separated list
        return [item.strip() for item in value.split(",") if item.strip()]
        
    try:
        return cast(value)
    except (ValueError, TypeError):
        return default
