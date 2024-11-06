from __future__ import annotations


import dataclasses
import json
import random
from typing import (
    Collection,
    Generic,
    Iterable,
    Literal,
    Optional,
    Protocol,
    Type,
    TypeVar,
    cast,
)

import requests
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.json import pydantic_encoder

from haaslib.domain import HaaslibExcpetion
from haaslib.logger import log
from haaslib.model import (
    AddBotFromLabRequest,
    ApiResponse,
    AuthenticatedSessionResponse,
    CloudMarket,
    CreateBotRequest,
    CreateLabRequest,
    GetBacktestResultRequest,
    HaasBot,
    HaasScriptItemWithDependencies,
    PaginatedResponse,
    StartLabExecutionRequest,
    UserAccount,
    LabBacktestResult,
    LabDetails,
    LabRecord,
    LabExecutionUpdate,
    LabSettings,
    AccountDetails,
    AccountData,
)
from haaslib.parameters import (
    LabParameter,
    LabStatus,
    LabConfig,
    LabSettings,
    BacktestStatus,
    LabAlgorithm
)


ApiResponseData = TypeVar(
    "ApiResponseData", bound=BaseModel | Collection[BaseModel] | bool | str
)
"""Any response from Haas API should be `pydantic` model or collection of them."""

HaasApiEndpoint = Literal["Labs", "Account", "HaasScript", "Price", "User", "Bot"]
"""Known Haas API endpoints"""


class HaasApiError(HaaslibExcpetion):
    """
    Base Excpetion for haaslib.
    """

    pass


@dataclasses.dataclass
class UserState:
    """
    Base user API Session type.
    """

    pass


class Guest(UserState):
    """
    Default user session type.
    """

    pass


@dataclasses.dataclass
class Authenticated(UserState):
    """
    Authenticated user session required for the most of the endpoints.
    """

    user_id: str
    interface_key: str


State = TypeVar("State", bound=Guest | Authenticated)
"""Generic to mark user session typ"""


class SyncExecutor(Protocol, Generic[State]):
    """
    Main protocol for interaction with HaasAPI.
    """

    def execute(
        self,
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
    ) -> ApiResponseData:
        """
        Executes any request to Haas API and serialized it's reponse

        :param endpoint: Actual Haas API endpoint
        :param response_type: Pydantic class for response deserialization
        :param query_params: Endpoint parameters
        :raises HaasApiError: If API returned any error
        :return: API response deserialized into `response_type`
        """
        ...


@dataclasses.dataclass(kw_only=True, frozen=True, slots=True)
class RequestsExecutor(Generic[State]):
    """First implementation of `SyncExecutor` based on `requests` library."""

    host: str
    """ Address of the Haas API."""

    port: int
    """ Port of the Haas API."""

    state: State
    """ User session state."""

    protocol: Literal["http"] = dataclasses.field(default="http")
    """Communication protocol (currently only http is valid)."""

    def authenticate(
        self: RequestsExecutor[Guest], email: str, password: str
    ) -> RequestsExecutor[Authenticated]:
        """
        Creates authenticated session in Haas API

        :param email: Email used to login into Web UI
        :param password: Password used to login into Web UI
        :raises HaasApiError: If credentials are incorrect
        """
        interface_key = "".join(f"{random.randint(0, 100)}" for _ in range(10))
        resp = self._execute_inner(
            "User",
            response_type=dict,
            query_params={
                "channel": "LOGIN_WITH_CREDENTIALS",
                "email": email,
                "password": password,
                "interfaceKey": interface_key,
            },
        )
        if not resp.success:
            raise HaasApiError("Failed to login with credentials")

        resp = self._execute_inner(
            "User",
            response_type=AuthenticatedSessionResponse,
            query_params={
                "channel": "LOGIN_WITH_ONE_TIME_CODE",
                "email": email,
                "pincode": random.randint(100_000, 200_000),
                "interfaceKey": interface_key,
            },
        )
        if not resp.success:
            raise HaasApiError(resp.error or "Failed to login")

        assert resp.data is not None

        state = Authenticated(
            interface_key=interface_key, user_id=resp.data.data.user_id
        )

        return RequestsExecutor(
            host=self.host, port=self.port, state=state, protocol=self.protocol
        )

    def execute(
        self,
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
    ) -> ApiResponseData:
        """Execute an API request."""
        match self.state:
            case Authenticated():
                resp = cast(
                    RequestsExecutor[Authenticated], self
                )._execute_authenticated(endpoint, response_type, query_params)
            case Guest():
                resp = cast(RequestsExecutor[Guest], self)._execute_guest(
                    endpoint, response_type, query_params
                )
            case _:
                raise ValueError(f"Unknown auth state: {self.state}")

        if not resp.success:
            raise HaasApiError(resp.error or "Request failed")

        return resp.data

    def _execute_authenticated(
        self: RequestsExecutor[Authenticated],
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
    ) -> ApiResponse[ApiResponseData]:
        """Execute request with authentication."""
        query_params = query_params or {}
        query_params.update({
            "userid": self.state.user_id,
            "interfacekey": self.state.interface_key,
        })
        return self._execute_inner(endpoint, response_type, query_params)

    def _execute_guest(
        self: RequestsExecutor[Guest],
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
    ) -> ApiResponse[ApiResponseData]:
        """Execute request without authentication."""
        return self._execute_inner(endpoint, response_type, query_params)

    def _execute_inner(
        self,
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
    ) -> ApiResponse[ApiResponseData]:
        """Internal method to execute the actual HTTP request."""
        url = f"{self.protocol}://{self.host}:{self.port}/{endpoint}API.php"
        log.debug(
            f"[{self.state.__class__.__name__}]: Requesting {url=} with {query_params=}"
        )
        if query_params:
            query_params = query_params.copy()
            for key in query_params.keys():
                value = query_params[key]
                if isinstance(value, (str, int, float, bool, type(None))):
                    continue

                if isinstance(value, list):
                    log.debug(f"Converting to JSON string list `{key}` field")
                    query_params[key] = json.dumps(
                        value, default=self._custom_encoder(by_alias=True)
                    )

                if isinstance(value, BaseModel):
                    log.debug(f"Converting to JSON string pydantic `{key}` field")
                    query_params[key] = value.model_dump_json(by_alias=True)

        resp = requests.get(url, params=query_params)
        resp.raise_for_status()

        ta = TypeAdapter(ApiResponse[response_type])

        try:
            return ta.validate_python(resp.json())
        except ValidationError:
            log.error(f"Failed to request: {resp.content}")
            raise

    @staticmethod
    def _custom_encoder(**kwargs):
        """Custom JSON encoder for complex types."""
        def base_encoder(obj):
            if isinstance(obj, BaseModel):
                return obj.model_dump(**kwargs)
            else:
                return pydantic_encoder(obj)
        return base_encoder




def get_all_scripts(
    executor: SyncExecutor[Authenticated],
) -> list[HaasScriptItemWithDependencies]:
    """
    Retrieves information about all script items for an authenticated user.

    :param executor: Executor for Haas API interaction
    :raises HaasApiError: If something goes wrong (Not found yet)
    :return: List with all available scripts
    """
    return executor.execute(
        endpoint="HaasScript",
        response_type=list[HaasScriptItemWithDependencies],
        query_params={"channel": "GET_ALL_SCRIPT_ITEMS"},
    )


def get_accounts(executor: SyncExecutor[Authenticated]) -> list[UserAccount]:
    """
    Retrieves information about user accounts for an authenticated user.

    :param executor: Executor for Haas API interaction
    :raises HaasApiError: If something goes wrong (Not found yet)
    :return: List with all available user accounts
    """
    return executor.execute(
        endpoint="Account",
        response_type=list[UserAccount],
        query_params={"channel": "GET_ACCOUNTS"},
    )


def create_lab(executor: SyncExecutor[Authenticated], req: CreateLabRequest) -> LabDetails:
    """Create a new lab"""
    return executor.execute(
        endpoint="Labs",
        response_type=LabDetails,  # This is correct - executor handles ApiResponse wrapper
        query_params={
            "channel": "CREATE_LAB",
            "scriptId": req.script_id,
            "name": req.name,
            "accountId": req.account_id,
            "market": req.market,
            "interval": req.interval,
            "style": req.default_price_data_style,
        },
    )

def start_lab_execution(
    executor: SyncExecutor[Authenticated],
    request: StartLabExecutionRequest,
) -> LabDetails:
    """Start lab execution with specified parameters"""
    return executor.execute(
        endpoint="Labs",
        response_type=LabDetails,
        query_params={
            "channel": "START_LAB_EXECUTION",
            "labId": request.lab_id,
            "startunix": request.start_unix,
            "endunix": request.end_unix,
            "sendEmail": request.send_email
        },
    )


def get_lab_details(
    executor: SyncExecutor[Authenticated], 
    lab_id: str
) -> LabDetails:
    """
    Get details for a specific lab
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to get details for
        
    Returns:
        LabDetails object containing the lab configuration
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Labs",
        response_type=LabDetails,
        query_params={
            "channel": "GET_LAB_DETAILS",
            "labid": lab_id,
        },
    )


def update_lab_details(
    executor: SyncExecutor[Authenticated],
    lab_id: str,
    config: LabConfig,
    settings: LabSettings,
    name: str,
    lab_type: str,
) -> LabDetails:
    """Updates lab details
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to update
        config: Lab configuration settings
        settings: Lab execution settings
        name: Name of the lab
        lab_type: Type of the lab
        
    Returns:
        Updated lab details
    """
    return executor.execute(
        endpoint="Labs",
        response_type=LabDetails,
        query_params={
            "channel": "UPDATE_LAB_DETAILS",
            "labId": lab_id,
            "config": config.model_dump(by_alias=True),
            "settings": settings.model_dump(by_alias=True),
            "name": name,
            "type": lab_type,
        },
    )


def cancel_lab_execution(
    executor: SyncExecutor[Authenticated],
    lab_id: str
) -> None:
    """
    Cancel a running lab execution.
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to cancel
        
    Raises:
        HaasApiError: If the API request fails
    """
    executor.execute(
        endpoint="Labs",
        response_type=None,
        query_params={
            "channel": "CANCEL_LAB_EXECUTION",
            "labId": lab_id,
        },
    )


def get_lab_execution_update(
    executor: SyncExecutor[Authenticated],
    lab_id: str
) -> LabExecutionUpdate:
    """
    Get current execution status of a lab.
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to get status for
        
    Returns:
        LabExecutionUpdate object containing current execution status
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Labs",
        response_type=LabExecutionUpdate,
        query_params={
            "channel": "GET_LAB_EXECUTION_UPDATE",
            "labId": lab_id,
        },
    )


def get_backtest_result(
    executor: SyncExecutor[Authenticated], 
    req: GetBacktestResultRequest
) -> PaginatedResponse[LabBacktestResult]:
    """Retrieves the backtest result for a specific lab"""
    return executor.execute(
        endpoint="Labs",
        response_type=PaginatedResponse[LabBacktestResult],
        query_params={
            "channel": "GET_BACKTEST_RESULT_PAGE",
            "labid": req.lab_id,
            "nextpageid": req.next_page_id,
            "pagelength": req.page_lenght,
        },
    )


def get_all_labs(executor: SyncExecutor[Authenticated]) -> list[LabRecord]:
    """Get all labs for the authenticated user"""
    return executor.execute(
        endpoint="Labs",
        response_type=list[LabRecord],
        query_params={
            "channel": "GET_LABS",
        },
    )


def delete_lab(executor: SyncExecutor[Authenticated], lab_id: str):
    """
    Removes Lab with given id

    :param executor: Executor for Haas API interaction
    :raises HaasApiError: Not found yet
    """
    return executor.execute(
        endpoint="Labs",
        response_type=bool,
        query_params={"channel": "DELETE_LAB", "labid": lab_id},
    )


def add_bot(executor: SyncExecutor[Authenticated], req: CreateBotRequest) -> HaasBot:
    """
    Creates new bot

    :param executor: Executor for Haas API interaction
    :param req: Details of bot creation
    :return: Created bot details
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "ADD_BOT",
            "botname": req.bot_name,
            "scriptid": req.script.id,
            "scripttype": req.script.type,
            "accountid": req.account_id,
            "market": req.market,
            "leverage": req.leverage,
            "interval": req.interval,
            "chartstyle": req.chartstyle,
        },
    )


def add_bot_from_lab(
    executor: SyncExecutor[Authenticated], req: AddBotFromLabRequest
) -> HaasBot:
    """
    Creates new bot from given lab's backtest

    :param executor: Executor for Haas API interaction
    :param req: Details of bot creation
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "ADD_BOT_FROM_LABS",
            "labid": req.lab_id,
            "backtestid": req.backtest_id,
            "botname": req.bot_name,
            "accountid": req.account_id,
            "market": req.market,
            "leverage": req.leverage,
        },
    )


def delete_bot(executor: SyncExecutor[Authenticated], bot_id: str):
    return executor.execute(
        endpoint="Bot",
        response_type=str,
        query_params={"channel": "DELETE_BOT", "botid": bot_id},
    )


def get_all_bots(executor: SyncExecutor[Authenticated]) -> list[HaasBot]:
    return executor.execute(
        endpoint="Bot",
        response_type=list[HaasBot],
        query_params={"channel": "GET_BOTS"},
    )


def get_scripts_by_name(
    executor: SyncExecutor[Authenticated], 
    name_pattern: str,
    case_sensitive: bool = False
) -> list[HaasScriptItemWithDependencies]:
    """
    Retrieves scripts that match the given name pattern.

    :param executor: Executor for Haas API interaction
    :param name_pattern: String pattern to match in script names
    :param case_sensitive: Whether to perform case-sensitive matching (default: False)
    :return: List of matching scripts
    """
    scripts = get_all_scripts(executor)
    
    if not case_sensitive:
        name_pattern = name_pattern.lower()
        return [s for s in scripts if name_pattern in s.script_name.lower()]
    
    return [s for s in scripts if name_pattern in s.script_name]


def get_account_data(
    executor: SyncExecutor[Authenticated],
    account_id: str
) -> AccountData:
    """Get detailed information about an account including its exchange"""
    return executor.execute(
        endpoint="Account",
        response_type=AccountData,
        query_params={
            "channel": "GET_ACCOUNT_DATA",
            "accountid": account_id
        }
    )

