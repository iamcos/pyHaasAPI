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
    List,
)

import requests
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.json import pydantic_encoder

from pyHaasAPI.domain import pyHaasAPIExcpetion
from pyHaasAPI.logger import log
from pyHaasAPI.model import (
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
    HaasScriptFolder,
    ScriptRecord,
)
from pyHaasAPI.parameters import (
    LabParameter,
    LabStatus,
    LabConfig,
    LabSettings,
    BacktestStatus,
    LabAlgorithm,
    ParameterRange,
    ScriptParameter,
)


ApiResponseData = TypeVar(
    "ApiResponseData", bound=BaseModel | Collection[BaseModel] | bool | str
)
"""Any response from Haas API should be `pydantic` model or collection of them."""

HaasApiEndpoint = Literal["Labs", "Account", "HaasScript", "Price", "User", "Bot"]
"""Known Haas API endpoints"""


class HaasApiError(pyHaasAPIExcpetion):
    """
    Base Excpetion for pyHaasAPI.
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
    lab_details: LabDetails
) -> LabDetails:
    """Update lab details and verify the update"""
    # Format parameters
    params_list = []
    for param in lab_details.parameters:
        # Convert options to strings
        if isinstance(param, dict):
            options = param.get('O', [])
        else:
            options = param.options
            
        if isinstance(options, (int, float)):
            options = [str(options)]
        elif isinstance(options, (list, tuple)):
            options = [str(opt) for opt in options]
        else:
            options = [str(options)]
            
        # Build parameter dict
        param_dict = {
            "K": param.get('K', '') if isinstance(param, dict) else param.key,
            "T": param.get('T', 3) if isinstance(param, dict) else param.type,
            "O": options,
            "I": param.get('I', True) if isinstance(param, dict) else param.is_enabled,
            "IS": param.get('IS', False) if isinstance(param, dict) else param.is_selected
        }
        params_list.append(param_dict)

    # Send update
    response = executor.execute(
        endpoint="Labs",
        response_type=ApiResponse[LabDetails],
        query_params={
            "channel": "UPDATE_LAB_DETAILS",
            "labId": lab_details.lab_id,
            "config": lab_details.config.model_dump_json(),
            "settings": lab_details.settings.model_dump_json(),
            "name": lab_details.name,
            "type": lab_details.type,
            "parameters": params_list
        }
    )

    if not response or not response.Success:
        log.error(f"Failed to update lab details: {response.Error if response else 'No response'}")
        # Get current state after failed update
        return get_lab_details(executor, lab_details.lab_id)

    # Verify update by getting current details
    updated_details = get_lab_details(executor, lab_details.lab_id)
    return updated_details


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


def clone_lab(executor: SyncExecutor[Authenticated], lab_id: str, new_name: str = None) -> LabDetails:
    """
    Clone an existing lab with all its configuration
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to clone
        new_name: Optional new name for the cloned lab (default: "Clone of {original_name}")
        
    Returns:
        LabDetails object for the newly created lab
        
    Raises:
        HaasApiError: If the API request fails
    """
    # Get the original lab details first
    original_lab = get_lab_details(executor, lab_id)
    
    # Generate new name if not provided
    if not new_name:
        new_name = f"Clone of {original_lab.name}"
    
    return executor.execute(
        endpoint="Labs",
        response_type=LabDetails,
        query_params={
            "channel": "CLONE_LAB",
            "labid": lab_id,
            "name": new_name,
        },
    )


def change_lab_script(executor: SyncExecutor[Authenticated], lab_id: str, script_id: str) -> LabDetails:
    """
    Change the script associated with a lab
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to modify
        script_id: ID of the new script to use
        
    Returns:
        Updated LabDetails object
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Labs",
        response_type=LabDetails,
        query_params={
            "channel": "CHANGE_LAB_SCRIPT",
            "labid": lab_id,
            "scriptid": script_id,
        },
    )


def get_backtest_runtime(executor: SyncExecutor[Authenticated], lab_id: str, backtest_id: str) -> dict:
    """
    Get detailed runtime information for a specific backtest
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab
        backtest_id: ID of the specific backtest
        
    Returns:
        Runtime information dictionary
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Labs",
        response_type=dict,
        query_params={
            "channel": "GET_BACKTEST_RUNTIME",
            "labid": lab_id,
            "backtestid": backtest_id,
        },
    )


def get_backtest_chart(executor: SyncExecutor[Authenticated], lab_id: str, backtest_id: str) -> dict:
    """
    Get chart data for a specific backtest
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab
        backtest_id: ID of the specific backtest
        
    Returns:
        Chart data dictionary
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Labs",
        response_type=dict,
        query_params={
            "channel": "GET_BACKTEST_CHART",
            "labid": lab_id,
            "backtestid": backtest_id,
        },
    )


def get_backtest_log(executor: SyncExecutor[Authenticated], lab_id: str, backtest_id: str) -> list[str]:
    """
    Get execution log for a specific backtest
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab
        backtest_id: ID of the specific backtest
        
    Returns:
        List of log entries as strings
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Labs",
        response_type=list[str],
        query_params={
            "channel": "GET_BACKTEST_LOG",
            "labid": lab_id,
            "backtestid": backtest_id,
        },
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


def activate_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    """
    Activate a bot to start trading
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to activate
        
    Returns:
        Updated HaasBot object with activation status
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "ACTIVATE_BOT",
            "botid": bot_id,
        },
    )


def deactivate_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    """
    Deactivate a bot to stop trading
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to deactivate
        
    Returns:
        Updated HaasBot object with deactivation status
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "DEACTIVATE_BOT",
            "botid": bot_id,
        },
    )


def pause_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    """
    Pause a bot's execution (temporarily stop trading)
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to pause
        
    Returns:
        Updated HaasBot object with pause status
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "PAUSE_BOT",
            "botid": bot_id,
        },
    )


def resume_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    """
    Resume a paused bot's execution
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to resume
        
    Returns:
        Updated HaasBot object with resume status
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "RESUME_BOT",
            "botid": bot_id,
        },
    )


def get_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    """
    Get detailed information about a specific bot
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to get details for
        
    Returns:
        HaasBot object with complete bot information
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "GET_BOT",
            "botid": bot_id,
        },
    )


def deactivate_all_bots(executor: SyncExecutor[Authenticated]) -> list[HaasBot]:
    """
    Deactivate all bots for the authenticated user
    
    Args:
        executor: Authenticated executor instance
        
    Returns:
        List of updated HaasBot objects
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=list[HaasBot],
        query_params={
            "channel": "DEACTIVATE_ALL_BOTS",
        },
    )


def get_bot_orders(executor: SyncExecutor[Authenticated], bot_id: str) -> list[dict]:
    """
    Get all open orders for a specific bot
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to get orders for
        
    Returns:
        List of order dictionaries
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=list[dict],
        query_params={
            "channel": "GET_BOT_ORDERS",
            "botid": bot_id,
        },
    )


def get_bot_positions(executor: SyncExecutor[Authenticated], bot_id: str) -> list[dict]:
    """
    Get all positions for a specific bot
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to get positions for
        
    Returns:
        List of position dictionaries
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=list[dict],
        query_params={
            "channel": "GET_BOT_POSITIONS",
            "botid": bot_id,
        },
    )


def cancel_bot_order(executor: SyncExecutor[Authenticated], bot_id: str, order_id: str) -> dict:
    """
    Cancel a specific order for a bot
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        order_id: ID of the order to cancel
        
    Returns:
        Cancellation result dictionary
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=dict,
        query_params={
            "channel": "CANCEL_BOT_ORDER",
            "botid": bot_id,
            "orderid": order_id,
        },
    )


def cancel_all_bot_orders(executor: SyncExecutor[Authenticated], bot_id: str) -> dict:
    """
    Cancel all orders for a specific bot
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to cancel all orders for
        
    Returns:
        Cancellation result dictionary
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=dict,
        query_params={
            "channel": "CANCEL_ALL_BOT_ORDERS",
            "botid": bot_id,
        },
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
    all_scripts = get_all_scripts(executor)
    
    if case_sensitive:
        matching_scripts = [
            script for script in all_scripts 
            if name_pattern in script.script_name
        ]
    else:
        matching_scripts = [
            script for script in all_scripts 
            if name_pattern.lower() in script.script_name.lower()
        ]
    
    return matching_scripts


def get_script_item(executor: SyncExecutor[Authenticated], script_id: str) -> HaasScriptItemWithDependencies:
    """
    Get detailed information about a specific script
    
    Args:
        executor: Authenticated executor instance
        script_id: ID of the script to get details for
        
    Returns:
        HaasScriptItemWithDependencies object with complete script information
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="HaasScript",
        response_type=HaasScriptItemWithDependencies,
        query_params={
            "channel": "GET_SCRIPT_ITEM",
            "scriptid": script_id,
        },
    )


def add_script(executor: SyncExecutor[Authenticated], script_name: str, script_content: str, description: str = "", script_type: int = 0) -> HaasScriptItemWithDependencies:
    """
    Upload a new script to the HaasOnline server
    
    Args:
        executor: Authenticated executor instance
        script_name: Name for the new script
        script_content: The script source code
        description: Description of the script (optional)
        script_type: Type of script (default: 0 for HaasScript)
        
    Returns:
        HaasScriptItemWithDependencies object for the newly created script
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="HaasScript",
        response_type=HaasScriptItemWithDependencies,
        query_params={
            "channel": "ADD_SCRIPT",
            "name": script_name,
            "script": script_content,
            "description": description,
            "type": script_type,
        },
    )


def edit_script(executor: SyncExecutor[Authenticated], script_id: str, script_name: str = None, script_content: str = None, description: str = "") -> HaasScriptItemWithDependencies | dict | None:
    """
    Edit an existing script
    
    Args:
        executor: Authenticated executor instance
        script_id: ID of the script to edit
        script_name: New name for the script (optional)
        script_content: New script content (optional)
        description: Description for the script (optional)
        
    Returns:
        Updated HaasScriptItemWithDependencies object, or raw dict if partial response
        
    Raises:
        HaasApiError: If the API request fails
    """
    query_params = {
        "channel": "EDIT_SCRIPT",
        "scriptid": script_id,
        "description": description,
    }
    if script_name:
        query_params["name"] = script_name
    if script_content:
        query_params["script"] = script_content
    try:
        return executor.execute(
            endpoint="HaasScript",
            response_type=HaasScriptItemWithDependencies,
            query_params=query_params,
        )
    except ValidationError as ve:
        import logging
        logging.warning(f"Partial response from edit_script: {ve}")
        # Try to get the raw response for logging
        try:
            import requests
            resp = requests.get(f"http://{executor.host}:{executor.port}/HaasScriptAPI.php", params=query_params)
            return resp.json()
        except Exception:
            return None


def delete_script(executor: SyncExecutor[Authenticated], script_id: str) -> bool:
    """
    Delete a script
    
    Args:
        executor: Authenticated executor instance
        script_id: ID of the script to delete
        
    Returns:
        True if deletion was successful
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="HaasScript",
        response_type=bool,
        query_params={
            "channel": "DELETE_SCRIPT",
            "scriptid": script_id,
        },
    )


def publish_script(executor: SyncExecutor[Authenticated], script_id: str) -> bool:
    """
    Publish a script to make it public
    
    Args:
        executor: Authenticated executor instance
        script_id: ID of the script to publish
        
    Returns:
        True if publication was successful
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="HaasScript",
        response_type=bool,
        query_params={
            "channel": "PUBLISH_SCRIPT",
            "scriptid": script_id,
        },
    )


def get_account_data(
    executor: SyncExecutor[Authenticated],
    account_id: str
) -> AccountData:
    """
    Get detailed information about an account including its exchange
    
    Args:
        executor: Authenticated executor instance
        account_id: ID of the account to get data for
        
    Returns:
        AccountData object with account details
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=AccountData,
        query_params={
            "channel": "GET_ACCOUNT_DATA",
            "accountid": account_id,
        },
    )


def get_account_balance(executor: SyncExecutor[Authenticated], account_id: str) -> dict:
    """
    Get balance information for a specific account
    
    Args:
        executor: Authenticated executor instance
        account_id: ID of the account to get balance for
        
    Returns:
        Balance information dictionary
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "GET_BALANCE",
            "accountid": account_id,
        },
    )


def get_all_account_balances(executor: SyncExecutor[Authenticated]) -> list[dict]:
    """
    Get balance information for all accounts
    
    Args:
        executor: Authenticated executor instance
        
    Returns:
        List of balance dictionaries for all accounts
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=list[dict],
        query_params={
            "channel": "GET_ALL_BALANCES",
        },
    )


def get_account_orders(executor: SyncExecutor[Authenticated], account_id: str) -> dict:
    """
    Get open orders for an account. Returns the raw response dict (with 'I' key for orders).
    """
    return executor.execute(
        endpoint="Account",
        response_type=object,
        query_params={
            "channel": "GET_ORDERS",
            "accountid": account_id,
            "userid": executor.state.user_id,
            "interfacekey": executor.state.interface_key,
        }
    )


def get_account_positions(executor: SyncExecutor[Authenticated], account_id: str) -> dict:
    """
    Get open positions for an account. Returns the raw response dict (with 'I' key for positions).
    """
    return executor.execute(
        endpoint="Account",
        response_type=object,
        query_params={
            "channel": "GET_POSITIONS",
            "accountid": account_id,
            "userid": executor.state.user_id,
            "interfacekey": executor.state.interface_key,
        }
    )


def get_account_trades(executor: SyncExecutor[Authenticated], account_id: str) -> list[dict]:
    """
    Get trade history for a specific account
    
    Args:
        executor: Authenticated executor instance
        account_id: ID of the account to get trades for
        
    Returns:
        List of trade dictionaries
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=list[dict],
        query_params={
            "channel": "GET_TRADES",
            "accountid": account_id,
        },
    )


def update_lab_parameters(
    executor: SyncExecutor[Authenticated],
    lab_id: str,
    parameters: List[ScriptParameter]
) -> LabDetails:
    """
    Update lab parameters with new values/ranges
    
    :param executor: API executor
    :param lab_id: ID of lab to update
    :param parameters: List of parameters with updated values/ranges
    :return: Updated lab details
    """
    # Get current lab details
    lab_details = get_lab_details(executor, lab_id)
    
    # Create update request
    return executor.execute(
        endpoint="LabsAPI",
        response_type=LabDetails,
        query_params={
            "channel": "UPDATE_LAB_DETAILS",
            "labId": lab_id,
            "config": lab_details.config.model_dump_json(),
            "settings": lab_details.settings.model_dump_json(),
            "name": lab_details.name,
            "type": lab_details.type,
            "parameters": [p.model_dump(by_alias=True) for p in parameters]
        }
    )


def get_all_markets(executor: SyncExecutor[Authenticated]) -> list[CloudMarket]:
    """
    Get all available markets
    
    Args:
        executor: Authenticated executor instance
        
    Returns:
        List of CloudMarket objects
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Price",
        response_type=list[CloudMarket],
        query_params={
            "channel": "MARKETLIST",
        },
    )


def get_market_price(executor: SyncExecutor[Authenticated], market: str) -> dict:
    """
    Get current price for a specific market
    
    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BINANCE_BTC_USDT")
        
    Returns:
        Price information dictionary
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Price",
        response_type=dict,
        query_params={
            "channel": "PRICE",
            "market": market,
        },
    )


def get_order_book(executor: SyncExecutor[Authenticated], market: str, depth: int = 20) -> dict:
    """
    Get order book for a specific market
    
    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BINANCE_BTC_USDT")
        depth: Number of order book levels to retrieve (default: 20)
        
    Returns:
        Order book dictionary with bids and asks
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Price",
        response_type=dict,
        query_params={
            "channel": "ORDERBOOK",
            "market": market,
            "depth": depth,
        },
    )


def get_last_trades(executor: SyncExecutor[Authenticated], market: str, limit: int = 100) -> list[dict]:
    """
    Get recent trades for a specific market
    
    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BINANCE_BTC_USDT")
        limit: Number of trades to retrieve (default: 100)
        
    Returns:
        List of trade dictionaries
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Price",
        response_type=list[dict],
        query_params={
            "channel": "LASTTRADES",
            "market": market,
            "limit": limit,
        },
    )


def get_market_snapshot(executor: SyncExecutor[Authenticated], market: str) -> dict:
    """
    Get market snapshot with current price, volume, and other metrics
    
    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BINANCE_BTC_USDT")
        
    Returns:
        Market snapshot dictionary
        
    Raises:
        HaasApiError: If the API request fails
    """
    # Extract pricesource from market string (e.g., "BINANCE_BTC_USDT_" -> "BINANCE")
    pricesource = market.split('_')[0] if '_' in market else market
    
    return executor.execute(
        endpoint="Price",
        response_type=dict,
        query_params={
            "channel": "SNAPSHOT",
            "market": market,
            "pricesource": pricesource,
        },
    )


def get_script_record(executor: SyncExecutor[Authenticated], script_id: str) -> ScriptRecord:
    """
    Fetch the full script record (including compile logs and all fields) for a given script ID.
    
    Args:
        executor: Authenticated executor instance
        script_id: Script ID to retrieve
        
    Returns:
        ScriptRecord object with complete script information
        
    Raises:
        HaasApiError: If the API request fails
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    return executor.execute(
        endpoint="HaasScript",
        response_type=ScriptRecord,
        query_params={
            "channel": "GET_SCRIPT_RECORD",
            "scriptid": script_id,
            "interfacekey": interface_key,
            "userid": user_id,
        },
    )


def get_all_script_folders(
    executor: SyncExecutor[Authenticated],
) -> list[HaasScriptFolder]:
    """
    Retrieves all script folders for the authenticated user.

    :param executor: Executor for Haas API interaction
    :raises HaasApiError: If something goes wrong
    :return: List with all available script folders
    """
    return executor.execute(
        endpoint="HaasScript",
        response_type=list[HaasScriptFolder],
        query_params={"channel": "GET_ALL_SCRIPT_FOLDERS"},
    )


def create_script_folder(
    executor: SyncExecutor[Authenticated],
    foldername: str,
    parentid: int = -1
) -> HaasScriptFolder:
    """
    Create a new script folder.
    :param executor: Authenticated executor
    :param foldername: Name of the folder
    :param parentid: Parent folder ID (-1 for root)
    :return: HaasScriptFolder object
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    return executor.execute(
        endpoint="HaasScript",
        response_type=HaasScriptFolder,
        query_params={
            "channel": "CREATE_FOLDER",
            "foldername": foldername,
            "parentid": parentid,
            "interfacekey": interface_key,
            "userid": user_id,
        }
    )

def move_script_to_folder(
    executor: SyncExecutor[Authenticated],
    script_id: str,
    folder_id: int
) -> bool:
    """
    Move a script to a different folder.
    :param executor: Authenticated executor
    :param script_id: Script ID to move
    :param folder_id: Target folder ID
    :return: True if successful
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    return executor.execute(
        endpoint="HaasScript",
        response_type=bool,
        query_params={
            "channel": "MOVE_SCRIPT_TO_FOLDER",
            "scriptid": script_id,
            "folderid": folder_id,
            "interfacekey": interface_key,
            "userid": user_id,
        }
    )


def place_order(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
    side: str,  # "buy" or "sell"
    price: float,
    amount: float,
    order_type: int = 0,  # 0=limit, 1=market
    tif: int = 0,         # 0=GTC
    source: str = "Manual"
) -> str:
    """
    Place an order via TradingAPI.
    Returns the order ID if successful.
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    order_obj = {
        "RID": "",
        "UID": "",
        "AID": account_id,
        "M": market,
        "T": 0 if side == "buy" else 1,
        "D": 1 if side == "buy" else -1,
        "P": price,
        "TP": 0,
        "TT": order_type,
        "A": amount,
        "TIF": tif,
        "S": source,
        "N": "",
        "F": None
    }
    return executor.execute(
        endpoint="Trading",
        response_type=str,
        query_params={
            "channel": "PLACE_ORDER",
            "order": json.dumps(order_obj),
            "interfacekey": interface_key,
            "userid": user_id,
        }
    )


def cancel_order(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    order_id: str
) -> bool:
    """
    Cancel an order by order ID.
    Returns True if successful.
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    return executor.execute(
        endpoint="Trading",
        response_type=bool,
        query_params={
            "channel": "CANCEL_ORDER",
            "accountid": account_id,
            "orderid": order_id,
            "interfacekey": interface_key,
            "userid": user_id,
        }
    )


def get_all_orders(
    executor: SyncExecutor[Authenticated]
) -> list[dict]:
    """
    Get all open orders for all accounts.
    Returns a list of dicts, each with 'AID' and 'I' (orders).
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    return executor.execute(
        endpoint="Account",
        response_type=object,  # Accepts list[dict] or object for flexibility
        query_params={
            "channel": "GET_ALL_ORDERS",
            "interfacekey": interface_key,
            "userid": user_id,
        }
    )

