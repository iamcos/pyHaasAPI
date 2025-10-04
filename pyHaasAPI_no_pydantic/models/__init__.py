"""
Data models for pyHaasAPI_no_pydantic

Provides dataclass-based data models with custom validation,
replacing Pydantic with better performance and simpler code.
"""

from .base import BaseModel, ValidationMixin, SerializationMixin
from .lab import (
    LabDetails,
    LabRecord, 
    LabConfig,
    LabSettings,
    StartLabExecutionRequest,
    LabExecutionUpdate,
    LabParameter,
)
from .validation import Validator, ValidationError

__all__ = [
    # Base models
    "BaseModel",
    "ValidationMixin",
    "SerializationMixin",
    
    # Lab models
    "LabDetails",
    "LabRecord",
    "LabConfig", 
    "LabSettings",
    "StartLabExecutionRequest",
    "LabExecutionUpdate",
    "LabParameter",
    
    # Validation
    "Validator",
    "ValidationError",
]



