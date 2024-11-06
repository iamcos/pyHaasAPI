from dataclasses import dataclass
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Base API response model."""
    success: bool = Field(alias="Success")
    error: Optional[str] = Field(alias="Error")
    data: Optional[T] = Field(alias="Data")

@dataclass
class UserState:
    """Base user API Session type."""
    pass

class Guest(UserState):
    """Default user session type."""
    pass

@dataclass
class Authenticated(UserState):
    """Authenticated user session."""
    user_id: str
    interface_key: str 