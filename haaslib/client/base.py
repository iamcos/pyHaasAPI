from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar, Generic
from ..types import ApiResponseData, HaasApiEndpoint
from ..models.common import UserState, Guest, Authenticated

State = TypeVar("State", bound=Guest | Authenticated)

class BaseClient(ABC, Generic[State]):
    """Base class for API clients."""
    
    @abstractmethod
    def execute(
        self,
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
    ) -> ApiResponseData:
        """Execute API request."""
        pass

    @abstractmethod
    def authenticate(
        self: "BaseClient[Guest]", 
        email: str, 
        password: str
    ) -> "BaseClient[Authenticated]":
        """Authenticate client."""
        pass 