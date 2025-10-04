"""
API layer for pyHaasAPI_no_pydantic

Provides consolidated API functionality for all lab operations,
eliminating code duplication by providing single implementations
of all lab-related functions found across the codebase.
"""

from .lab_api import LabAPI
from .client import APIClient
from .exceptions import (
    LabAPIError,
    LabNotFoundError,
    LabExecutionError,
    LabConfigurationError,
    APIConnectionError,
    APIResponseError,
)

__all__ = [
    # API classes
    "LabAPI",
    "APIClient",
    
    # Exceptions
    "LabAPIError",
    "LabNotFoundError",
    "LabExecutionError",
    "LabConfigurationError",
    "APIConnectionError",
    "APIResponseError",
]



