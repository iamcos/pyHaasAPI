from typing import TypeVar, Protocol, Generic, Collection, Any
from pydantic import BaseModel
from dataclasses import dataclass

# Move base types from api.py
class UserState:
    """Base user API Session type."""
    pass

class Guest(UserState):
    """Default user session type."""
    pass

@dataclass
class Authenticated(UserState):
    """Authenticated user session required for most endpoints."""
    user_id: str
    interface_key: str

# Type variables
State = TypeVar("State", bound=Guest | Authenticated)
ApiResponseData = TypeVar("ApiResponseData", bound=BaseModel | Collection[BaseModel] | bool | str)

class SyncExecutor(Protocol, Generic[State]):
    """Protocol defining the executor interface"""
    def execute(
        self,
        endpoint: str,
        response_type: type[ApiResponseData],
        query_params: dict[str, Any],
    ) -> ApiResponseData:
        ...

class HaasApiError(Exception):
    """Base Exception for haaslib."""
    pass 