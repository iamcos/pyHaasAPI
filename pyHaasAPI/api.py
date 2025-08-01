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
    Dict,
    Any,
)

import requests
import urllib.parse
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.json import pydantic_encoder

from pyHaasAPI.domain import pyHaasAPIExcpetion
from pyHaasAPI.logger import log
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
import time


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
        log.debug(f"Raw response from API (LOGIN_WITH_CREDENTIALS): {resp}")
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
        log.debug(f"Raw response from API (LOGIN_WITH_ONE_TIME_CODE): {resp}")
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
        use_post: bool = False
    ) -> ApiResponseData:
        """Execute an API request."""
        match self.state:
            case Authenticated():
                resp = cast(
                    RequestsExecutor[Authenticated], self
                )._execute_authenticated(endpoint, response_type, query_params, use_post)
            case Guest():
                resp = cast(RequestsExecutor[Guest], self)._execute_guest(
                    endpoint, response_type, query_params, use_post
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
        use_post: bool = False
    ) -> ApiResponse[ApiResponseData]:
        """Execute request with authentication."""
        query_params = query_params or {}
        query_params.update({
            "userid": self.state.user_id,
            "interfacekey": self.state.interface_key,
        })
        return self._execute_inner(endpoint, response_type, query_params, use_post)

    def _execute_guest(
        self: RequestsExecutor[Guest],
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
        use_post: bool = False
    ) -> ApiResponse[ApiResponseData]:
        """Execute request without authentication."""
        return self._execute_inner(endpoint, response_type, query_params, use_post)

    def _execute_inner(
        self,
        endpoint: HaasApiEndpoint,
        response_type: Type[ApiResponseData],
        query_params: Optional[dict] = None,
        use_post: bool = False
    ) -> ApiResponse[ApiResponseData]:
        """Internal method to execute the actual HTTP request."""
        url = f"{self.protocol}://{self.host}:{self.port}/{endpoint}API.php"
        log.debug(
            f"[{self.state.__class__.__name__}]: Requesting {url=} with {query_params=}"
        )
        
        # Determine if we need to use POST method
        use_post = query_params.pop("use_post", False) if query_params else False
        if use_post:
            log.debug("Using POST method for request")
        
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

        # Separate channel from query_params for URL
        channel = query_params.pop("channel", None) if query_params else None
        if channel:
            url = f"{url}?channel={channel}"

        # Use POST for specific channels or if explicitly marked
        if use_post or (channel in ["START_LAB_EXECUTION", "EDIT_SETTINGS"]):
            # Manually construct the data string for POST requests
            # This is crucial for cases like EDIT_SETTINGS where 'settings' is already a JSON string
            data_parts = []
            for k, v in query_params.items():
                if k == "settings" and channel == "EDIT_SETTINGS":
                    # 'settings' is already a JSON string, so just URL-encode the key and value
                    data_parts.append(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(v)}")
                elif isinstance(v, (str, int, float, bool, type(None))):
                    data_parts.append(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}")
                else:
                    # For other complex types, dump to JSON string and then URL-encode
                    data_parts.append(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(json.dumps(v, default=self._custom_encoder(by_alias=True)))}")

            data = "&".join(data_parts)
            resp = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        else:
            resp = requests.get(url, params=query_params)
            
        resp.raise_for_status()

        ta = TypeAdapter(ApiResponse[response_type])

        try:
            resp_json = resp.json()
            # Patch for GET_ACCOUNT_DATA missing fields
            if (
                endpoint == "Account"
                and query_params is not None
                and query_params.get("channel") == "GET_ACCOUNT_DATA"
                and isinstance(resp_json, dict)
                and "Data" in resp_json
                and isinstance(resp_json["Data"], dict)
            ):
                data = resp_json["Data"]
                # Add missing required fields with default values
                if "account_id" not in data:
                    data["account_id"] = ""
                if "exchange" not in data:
                    data["exchange"] = ""
                if "type" not in data:
                    data["type"] = ""
                if "wallets" not in data:
                    # If balances are present under 'B', use them as wallets, else empty list
                    data["wallets"] = data.get("B", [])
            try:
                if response_type == HaasBot:
                    log.debug(f"Raw response for HaasBot: {resp_json}")
                return ta.validate_python(resp_json)
            except ValidationError:
                log.error(f"Failed to request: {resp.content}")
                raise
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
            "tradeAmount": req.trade_amount,
            "chartStyle": req.chart_style,
            "orderTemplate": req.order_template,
            "leverage": req.leverage,
            "positionMode": req.position_mode,
            "marginMode": req.margin_mode,
        },
    )

def ensure_lab_config_parameters(
    executor: SyncExecutor[Authenticated],
    lab_id: str,
    config: Optional[LabConfig] = None
) -> LabDetails:
    """
    Ensure a lab has proper config parameters before backtesting.
    
    This function validates and applies the correct config parameters (MP, MG, ME, MR, AR)
    to ensure the lab is ready for backtesting. This is a CRITICAL step that should
    be called before any backtest execution.
    
    ⚠️ **REQUIRED STEP**: This function should be called before `start_lab_execution`
    to ensure proper backtest configuration.
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to configure
        config: Optional LabConfig object. If not provided, uses default intelligent mode config
        
    Returns:
        LabDetails object with updated config parameters
        
    Raises:
        HaasApiError: If the API request fails
        
    Example:
        >>> # Ensure lab has proper config before backtesting
        >>> lab_details = api.ensure_lab_config_parameters(executor, "lab_id")
        >>> # Now safe to start backtest
        >>> api.start_lab_execution(executor, request)
        
    See Also:
        - docs/CONFIG_PARAMETER_FIX_SUMMARY.md for detailed explanation
        - start_lab_execution() for backtest execution
    """
    # Get current lab details
    lab_details = get_lab_details(executor, lab_id)
    
    # Use provided config or default intelligent mode config
    if config is None:
        config = LabConfig(
            max_population=10,    # Max Population
            max_generations=100,  # Max Generations  
            max_elites=3,         # Max Elites
            mix_rate=40.0,        # Mix Rate
            adjust_rate=25.0      # Adjust Rate
        )
    
    # Check if config needs updating
    current_config = lab_details.config
    config_needs_update = (
        current_config.max_population != config.max_population or
        current_config.max_generations != config.max_generations or
        current_config.max_elites != config.max_elites or
        current_config.mix_rate != config.mix_rate or
        current_config.adjust_rate != config.adjust_rate
    )
    
    if config_needs_update:
        log.info(f"🔄 Updating lab config parameters for lab {lab_id}")
        log.info(f"   Current: MP={current_config.max_population}, MG={current_config.max_generations}, ME={current_config.max_elites}, MR={current_config.mix_rate}, AR={current_config.adjust_rate}")
        log.info(f"   Target:  MP={config.max_population}, MG={config.max_generations}, ME={config.max_elites}, MR={config.mix_rate}, AR={config.adjust_rate}")
        
        # Update the lab details with new config
        lab_details.config = config
        updated_lab = update_lab_details(executor, lab_details)
        
        log.info(f"✅ Lab config parameters updated successfully")
        return updated_lab
    else:
        log.info(f"✅ Lab {lab_id} already has correct config parameters")
        return lab_details


def start_lab_execution(
    executor: SyncExecutor[Authenticated],
    request: StartLabExecutionRequest,
    ensure_config: bool = True,
    config: Optional[LabConfig] = None
) -> dict:
    """
    Start lab execution with specified parameters, using a robust direct POST that matches the browser/curl.
    """
    if ensure_config:
        log.info(f"🔧 Ensuring proper config parameters for lab {request.lab_id} before backtest execution")
        ensure_lab_config_parameters(executor, request.lab_id, config)

    import requests
    lab_id = request.lab_id
    start_unix = request.start_unix
    end_unix = request.end_unix
    interface_key = getattr(executor.state, 'interface_key', None)
    user_id = getattr(executor.state, 'user_id', None)
    url = f"http://{executor.host}:{executor.port}/LabsAPI.php?channel=START_LAB_EXECUTION"
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,pl;q=0.6,de;q=0.5,fr;q=0.4',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': f'http://{executor.host}:{executor.port}',
        'Referer': f'http://{executor.host}:{executor.port}/Labs/{lab_id}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }
    data = f"labid={lab_id}&startunix={start_unix}&endunix={end_unix}&sendemail={str(request.send_email).lower()}&interfacekey={interface_key}&userid={user_id}"
    resp = requests.post(url, headers=headers, data=data)
    resp.raise_for_status()
    return resp.json()


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
    """
    Update lab details and verify the update.
    
    ⚠️ IMPORTANT: This function has been fixed to work correctly with the HaasOnline API.
    
    **Recent Fixes Applied:**
    1. **Parameter Names**: Changed `labId` to `labid` (lowercase) to match server expectations
    2. **Settings Serialization**: Added `by_alias=True` to use camelCase field names (accountId, marketTag, etc.)
    3. **HTTP Method**: Changed from POST to GET method for all requests
    4. **Parameter Format**: Preserved original data types in parameter options (numbers as numbers, strings as strings)
    
    **Usage Notes:**
    - Use this function to update market tags and account IDs after cloning labs
    - The function automatically handles parameter formatting and serialization
    - All settings are preserved and updated correctly
    
    Args:
        executor: Authenticated executor instance
        lab_details: LabDetails object with updated settings and parameters
        
    Returns:
        LabDetails object containing the updated lab configuration
        
    Raises:
        HaasApiError: If the API request fails
        
    Example:
        >>> # Update market tag and account ID after cloning
        >>> lab_details = api.get_lab_details(executor, "lab_id")
        >>> lab_details.settings.market_tag = "BINANCE_ETH_USDT_"
        >>> lab_details.settings.account_id = "account_id"
        >>> updated_lab = api.update_lab_details(executor, lab_details)
        >>> print(f"Updated: {updated_lab.settings.market_tag}")
        
    See Also:
        - docs/LAB_CLONING_DISCOVERY.md for detailed explanation of fixes
        - clone_lab() for the recommended approach to lab cloning
    """
    # Format parameters to match the working example format
    params_list = []
    for param in lab_details.parameters:
        # Convert options to the correct format
        if isinstance(param, dict):
            options = param.get('O', [])
        else:
            options = param.options
            
        # Keep options as they are (don't convert to strings for numbers)
        if isinstance(options, (int, float)):
            options = [options]  # Keep as number
        elif isinstance(options, (list, tuple)):
            # Keep numbers as numbers, strings as strings
            options = [opt for opt in options]
        else:
            options = [options]
            
        # Build parameter dict matching the working example
        param_dict = {
            "K": param.get('K', '') if isinstance(param, dict) else param.key,
            "O": options,
            "I": param.get('I', True) if isinstance(param, dict) else param.is_enabled,
            "IS": param.get('IS', False) if isinstance(param, dict) else param.is_selected
        }
        params_list.append(param_dict)

    # Send update using the correct parameter names and format
    response = executor.execute(
        endpoint="Labs",
        response_type=ApiResponse[LabDetails],
        query_params={
            "channel": "UPDATE_LAB_DETAILS",
            "labid": lab_details.lab_id,  # Changed from labId to labid
            "name": lab_details.name,
            "type": lab_details.type,
            "config": lab_details.config.model_dump_json(by_alias=True),  # Use field aliases (MP, MG, ME, MR, AR)
            "settings": lab_details.settings.model_dump_json(by_alias=True),  # Use camelCase aliases
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
    Clone an existing lab with all settings and parameters preserved.
    
    ⚠️ CRITICAL DISCOVERY: This is the CORRECT approach for lab cloning!
    
    The CLONE_LAB operation automatically preserves ALL settings and parameters
    from the original lab, making it superior to CREATE_LAB + UPDATE_LAB_DETAILS.
    
    ✅ CORRECT APPROACH (this function):
        - Automatically copies ALL settings and parameters
        - No manual parameter updates needed
        - Simple, reliable, and fast
        - No 404 errors
    
    ❌ WRONG APPROACH (CREATE_LAB + UPDATE_LAB_DETAILS):
        - Creates lab with default parameters
        - Requires manual parameter updates (often fails with 404 errors)
        - Complex and error-prone
        - May lose critical settings during updates
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab to clone
        new_name: Optional new name for the cloned lab. If not provided, 
                 a timestamped name will be generated.
        
    Returns:
        LabDetails object for the newly created lab
        
    Raises:
        HaasApiError: If the API request fails
        
    Example:
        >>> # Clone a lab and give it a new name
        >>> cloned_lab = api.clone_lab(executor, "source_lab_id", new_name="BTC_USDT_Clone")
        >>> print(f"Cloned lab ID: {cloned_lab.lab_id}")
    
    See Also:
        - docs/LAB_CLONING_DISCOVERY.md for detailed explanation
        - clone_and_backtest_lab() for full workflow
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


def activate_bot(executor: SyncExecutor[Authenticated], bot_id: str, cleanreports: bool = False) -> HaasBot:
    """
    Activate a bot to start trading
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to activate
        cleanreports: Whether to clean previous reports (default: False)
        
    Returns:
        Updated HaasBot object with activation status
        
    Raises:
        HaasApiError: If the API request fails
    """
    resp = executor.execute(
        endpoint="Bot",
        response_type=object,  # Accept any type
        query_params={
            "channel": "ACTIVATE_BOT",
            "botid": bot_id,
            "cleanreports": cleanreports,
        },
    )
    # If the response is a HaasBot, return it. If it's True, fetch the bot object.
    from pyHaasAPI.model import HaasBot
    if isinstance(resp, HaasBot):
        return resp
    if resp is True:
        return get_bot(executor, bot_id)
    raise HaasApiError(f"Unexpected response from ACTIVATE_BOT: {resp}")


def deactivate_bot(executor: SyncExecutor[Authenticated], bot_id: str, cancelorders: bool = False) -> HaasBot:
    resp = executor.execute(
        endpoint="Bot",
        response_type=object,
        query_params={
            "channel": "DEACTIVATE_BOT",
            "botid": bot_id,
            "cancelorders": cancelorders,
        },
    )
    from pyHaasAPI.model import HaasBot
    if isinstance(resp, HaasBot):
        return resp
    if resp is True:
        return get_bot(executor, bot_id)
    raise HaasApiError(f"Unexpected response from DEACTIVATE_BOT: {resp}")


def pause_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    resp = executor.execute(
        endpoint="Bot",
        response_type=object,
        query_params={
            "channel": "PAUSE_BOT",
            "botid": bot_id,
        },
    )
    from pyHaasAPI.model import HaasBot
    if isinstance(resp, HaasBot):
        return resp
    if resp is True:
        return get_bot(executor, bot_id)
    raise HaasApiError(f"Unexpected response from PAUSE_BOT: {resp}")


def resume_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    resp = executor.execute(
        endpoint="Bot",
        response_type=object,
        query_params={
            "channel": "RESUME_BOT",
            "botid": bot_id,
        },
    )
    from pyHaasAPI.model import HaasBot
    if isinstance(resp, HaasBot):
        return resp
    if resp is True:
        return get_bot(executor, bot_id)
    raise HaasApiError(f"Unexpected response from RESUME_BOT: {resp}")


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
    bot = executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "GET_BOT",
            "botid": bot_id,
        },
    )
    return bot

def edit_bot_parameter(executor: SyncExecutor[Authenticated], bot: HaasBot) -> HaasBot:
    """
    Edits the parameters and settings of an existing bot, including script-specific parameters.

    This function utilizes the 'EDIT_SETTINGS' channel to update various bot configurations,
    such as trade amount, leverage, and custom script parameters.

    Args:
        executor: Authenticated executor instance.
        bot: The HaasBot object with updated settings and parameters.
             Ensure that `bot.settings.script_parameters` is correctly populated
             with the desired script-specific parameter changes.

    Returns:
        The updated HaasBot object as returned by the API.

    Raises:
        HaasApiError: If the API request fails or the update is unsuccessful.
    """
    return executor.execute(
        endpoint="Bot",
        response_type=HaasBot,
        query_params={
            "channel": "EDIT_SETTINGS",
            "botid": bot.bot_id,
            "scriptid": bot.script_id,
            "settings": bot.settings.model_dump_json(by_alias=True),
        },
        use_post=True,
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


def get_account_data(executor: SyncExecutor[Authenticated], account_id: str) -> AccountData:
    """
    Get account data including exchange information.

    Args:
        executor: Authenticated executor instance
        account_id: ID of the account

    Returns:
        AccountData object
    """
    raw_response = executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "GET_ACCOUNT_DATA",
            "accountid": account_id,
            "userid": getattr(executor.state, 'user_id', None),
            "interfacekey": getattr(executor.state, 'interface_key', None),
        },
    )

    # Extract data from the raw response
    data = raw_response.get("Data", {})

    # Manually construct AccountData object
    account_data = AccountData(
        account_id=account_id, # Use the account_id from the input
        exchange="", # Exchange is not directly in this response, set to empty string
        type="", # Type is not directly in this response, set to empty string
        wallets=data.get("B", []) # Balances are under 'B'
    )
    return account_data


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


def rename_account(executor: SyncExecutor[Authenticated], account_id: str, new_name: str) -> bool:
    """
    Rename an account
    
    Args:
        executor: Authenticated executor instance
        account_id: ID of the account to rename
        new_name: New name for the account
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=bool,
        query_params={
            "channel": "RENAME_ACCOUNT",
            "accountid": account_id,
            "name": new_name,
        },
    )


def deposit_funds(executor: SyncExecutor[Authenticated], account_id: str, currency: str, wallet_id: str, amount: float) -> bool:
    """
    Deposit funds to an account
    
    Args:
        executor: Authenticated executor instance
        account_id: ID of the account to deposit to
        currency: Currency to deposit (e.g., "USDC", "BTC")
        wallet_id: Wallet ID for the currency
        amount: Amount to deposit
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=bool,
        query_params={
            "channel": "DEPOSIT_FUNDS",
            "accountid": account_id,
            "currency": currency,
            "walletid": wallet_id,
            "amount": amount,
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
        endpoint="Labs",
        response_type=LabDetails,
        query_params={
            "channel": "UPDATE_LAB_DETAILS",
            "labId": lab_id,
            "config": lab_details.config.model_dump_json(),
            "settings": lab_details.settings.model_dump_json(),
            "name": lab_details.name,
            "type": lab_details.type,
            "parameters": [p.model_dump(by_alias=True) if hasattr(p, 'model_dump') else p for p in parameters]
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


def get_all_orders(executor: SyncExecutor[Authenticated]) -> list[dict]:
    """
    Get all orders for all accounts.
    Returns a list of dicts, each with 'AID' and 'I' (orders).
    """
    response = executor.execute(
        endpoint="Account",
        response_type=list[dict],
        query_params={
            "channel": "GET_ALL_ORDERS",
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )
    return response


def get_all_positions(executor: SyncExecutor[Authenticated]) -> list[dict]:
    """
    Get all positions for all accounts.
    Returns a list of dicts, each with 'AID' and 'I' (positions).
    """
    response = executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "GET_ALL_POSITIONS",
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )
    return response.get("Data", [])


def get_bot_runtime_logbook(executor: SyncExecutor[Authenticated], bot_id: str, next_page_id: int = -1, page_length: int = 250) -> list[str]:
    """
    Get the runtime logbook for a running bot.

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        next_page_id: For pagination, default -1 (start)
        page_length: Number of log entries to fetch

    Returns:
        List of log entries as strings
    """
    response = executor.execute(
        endpoint="Bot",
        response_type=dict,  # Accept dict to handle {'I': [...], 'NP': ...}
        query_params={
            "channel": "GET_RUNTIME_LOGBOOK",
            "botid": bot_id,
            "nextpageid": next_page_id,
            "pagelength": page_length,
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )
    # Extract the 'I' key (list of log entries)
    return response.get('I', []) if isinstance(response, dict) else []


def get_bot_runtime(executor: SyncExecutor[Authenticated], bot_id: str) -> dict:
    """
    Get the full runtime report for a running bot.

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot

    Returns:
        Dictionary with runtime info (positions, orders, performance, etc.)
    """
    retries = 5
    delay = 2  # seconds
    for i in range(retries):
        try:
            response = executor.execute(
                endpoint="Bot",
                response_type=dict,
                query_params={
                    "channel": "GET_RUNTIME",
                    "botid": bot_id,
                    "interfacekey": getattr(executor.state, 'interface_key', None),
                    "userid": getattr(executor.state, 'user_id', None),
                },
            )
            if response:
                return response
        except HaasApiError as e:
            log.warning(f"Attempt {i+1}/{retries}: HaasApiError getting bot runtime for {bot_id}: {e}")
        except Exception as e:
            log.error(f"Attempt {i+1}/{retries}: Unexpected error getting bot runtime for {bot_id}: {e}", exc_info=True)
        time.sleep(delay)
    raise HaasApiError(f"Failed to get bot runtime for {bot_id} after {retries} attempts.")

def get_bot_script_parameters(executor: SyncExecutor[Authenticated], bot_id: str) -> Dict[str, Any]:
    """
    Retrieves the script parameters for a given bot from its runtime details.

    Args:
        executor: Authenticated executor instance.
        bot_id: ID of the bot.

    Returns:
        A dictionary of script parameters.

    Raises:
        HaasApiError: If the API request fails or parameters cannot be extracted.
    """
    runtime_details = get_bot_runtime(executor, bot_id)
    if not runtime_details or "InputFields" not in runtime_details:
        raise HaasApiError(f"No script parameters (InputFields) found in runtime for bot {bot_id}.")
    return runtime_details["InputFields"]

def _transform_script_parameters(user_params: Dict[str, Any], api_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms user-provided script parameters to match the API's expected format and types.
    
    Args:
        user_params: Dictionary of user-provided parameters (simplified names, string values).
        api_params: Dictionary of parameters from GET_RUNTIME (full keys, type info).
        
    Returns:
        A dictionary with full API keys and correctly typed values.
    """
    transformed_params = {}
    for user_key, user_value in user_params.items():
        found_match = False
        for api_param_key, api_param_details in api_params.items():
            if api_param_details.get("N") == user_key: # Match by simplified name
                full_key = api_param_details.get("K")
                param_type = api_param_details.get("T")
                
                transformed_value = user_value
                if param_type == 0: # Numeric type
                    try:
                        transformed_value = float(user_value)
                        if transformed_value.is_integer():
                            transformed_value = int(transformed_value)
                    except ValueError:
                        log.warning(f"Could not convert '{user_value}' to number for parameter '{user_key}'. Keeping as is.")
                elif param_type == 2: # Boolean type
                    if isinstance(user_value, str):
                        transformed_value = user_value.lower() == "true"
                
                transformed_params[full_key] = transformed_value
                found_match = True
                break
        if not found_match:
            log.warning(f"No matching API parameter found for user parameter '{user_key}'. Skipping transformation.")
            # If no match, include it as is, but log a warning
            transformed_params[user_key] = user_value
            
    return transformed_params


def edit_bot_settings(
    executor: SyncExecutor[Authenticated],
    bot_id: str,
    script_id: str,
    settings: HaasScriptSettings
) -> HaasBot:
    """
    Edit the settings of an existing bot.

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot to edit.
        script_id: ID of the script associated with the bot.
        settings: HaasScriptSettings object containing the updated settings.

    Returns:
        The updated HaasBot object.

    Raises:
        HaasApiError: If the API request fails.
    """
    # Fetch current script parameters to get the full keys and types
    current_script_parameters = get_bot_script_parameters(executor, bot_id)
    
    # Transform the provided settings.script_parameters
    transformed_script_parameters = _transform_script_parameters(
        settings.script_parameters, current_script_parameters
    )
    
    # Update the settings object with the transformed parameters
    settings.script_parameters = transformed_script_parameters

    log.debug(f"Attempting to edit bot settings for bot {bot_id} with settings: {settings.model_dump_json(by_alias=True)}")
    resp_data = executor.execute(
        endpoint="Bot",
        response_type=dict, # Expect a dict to manually extract the HaasBot
        query_params={
            "channel": "EDIT_SETTINGS",
            "botid": bot_id,
            "scriptid": script_id,
            "settings": settings.model_dump_json(by_alias=True), # Serialize settings to JSON string
        },
        use_post=True,
    )
    # The API returns a dict, but we want to return a HaasBot object
    # The HaasBot object can be constructed from the 'H' key in the response data
    if "H" in resp_data:
        return HaasBot.model_validate(resp_data["H"])
    raise HaasApiError(f"Failed to parse HaasBot from response: {resp_data}")


def get_bot_script_parameters(executor: SyncExecutor[Authenticated], bot_id: str) -> Dict[str, Any]:
    """
    Get the script parameters (InputFields) for a specific bot.

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot.

    Returns:
        A dictionary containing the script parameters.

    Raises:
        HaasApiError: If the API request fails or InputFields are not found.
    """
    runtime_data = get_bot_runtime(executor, bot_id)
    if "InputFields" in runtime_data:
        return runtime_data["InputFields"]
    else:
        raise HaasApiError(f"InputFields not found for bot {bot_id} in runtime data.")

def get_history_status(executor: SyncExecutor[Authenticated]) -> dict:
    """
    Get the historical data status for all markets.
    Returns a dict keyed by market symbol.
    """
    response = executor.execute(
        endpoint="Setup",
        response_type=dict,
        query_params={
            "channel": "GET_HISTORY_STATUS",
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )
    # The response is already the raw API response, so we need to extract Data from it
    if isinstance(response, dict) and "Data" in response:
        return response["Data"]
    return response

def is_script_execution(
    executor: SyncExecutor[Authenticated],
    script_id: str
) -> dict:
    """
    Checks if a script is currently executing.

    Args:
        executor: Authenticated executor instance.
        script_id: ID of the script to check.

    Returns:
        A dictionary containing the execution status.
    """
    return executor.execute(
        endpoint="Backtest",
        response_type=dict,
        query_params={
            "channel": "IS_SCRIPT_EXECUTION",
            "scriptid": script_id,
        },
    )

def set_history_depth(executor: SyncExecutor[Authenticated], market: str, months: int) -> bool:
    """
    Set the history depth for a specific market.
    
    Args:
        executor: Authenticated executor instance
        market: Market symbol (e.g., "BINANCE_BTC_USDT_")
        months: Number of months of history to sync
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    # Use raw request to avoid validation issues
    import requests
    url = f"http://{executor.host}:{executor.port}/SetupAPI.php"
    params = {
        "channel": "SET_HISTORY_DEPTH",
        "market": market,
        "monthdepth": months,
        "interfacekey": executor.state.interface_key,
        "userid": executor.state.user_id,
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("Success", False) is True
    except Exception:
        return False


def add_simulated_account(
    executor: SyncExecutor[Authenticated],
    name: str,
    driver_code: str,
    driver_type: int
) -> dict:
    """
    Add a new simulated account.
    
    Args:
        executor: Authenticated executor instance
        name: Name for the new simulated account
        driver_code: Exchange driver code (e.g., 'BINANCEQUARTERLY')
        driver_type: Driver type as integer (e.g., 2)
    Returns:
        Dictionary with new account data
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "ADD_SIMULATED_ACCOUNT",
            "name": name,
            "drivercode": driver_code,
            "drivertype": driver_type,
        },
    )


def test_account(
    executor: SyncExecutor[Authenticated],
    driver_code: str,
    driver_type: int,
    version: int,
    public_key: str,
    private_key: str,
    extra_key: str = ""
) -> dict:
    """
    Test exchange account credentials.
    
    Args:
        executor: Authenticated executor instance
        driver_code: Exchange driver code (e.g., 'BYBITSPOT')
        driver_type: Driver type as integer (e.g., 0)
        version: API version (e.g., 5)
        public_key: Public API key
        private_key: Private API key
        extra_key: Extra key (optional, defaults to empty string)
    Returns:
        Dictionary with test results
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "TEST_ACCOUNT",
            "drivercode": driver_code,
            "drivertype": driver_type,
            "version": version,
            "publickey": public_key,
            "privatekey": private_key,
            "extrakey": extra_key,
        },
    )


def delete_account(executor: SyncExecutor[Authenticated], account_id: str) -> bool:
    """
    Delete an account.
    
    Args:
        executor: Authenticated executor instance
        account_id: ID of the account to delete
    Returns:
        True if successful, False otherwise
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=bool,
        query_params={
            "channel": "DELETE_ACCOUNT",
            "accountid": account_id,
        },
    )


def clone_and_backtest_lab(
    executor: SyncExecutor[Authenticated],
    source_lab_id: str,
    new_lab_name: str,
    market_tag: str,
    account_id: str,
    start_unix: int,
    end_unix: int,
    config: Optional[LabConfig] = None,
    send_email: bool = False
) -> Dict[str, Any]:
    """
    Complete workflow: Clone a lab, update market/account, ensure config, and start backtest.
    
    This function provides a complete, production-ready pipeline that handles:
    1. ✅ Cloning the source lab with all settings preserved
    2. ✅ Updating market tag and account ID for the new market
    3. ✅ Ensuring proper config parameters (MP, MG, ME, MR, AR)
    4. ✅ Starting the backtest with validation
    
    This is the RECOMMENDED approach for bulk lab creation and backtesting.
    
    Args:
        executor: Authenticated executor instance
        source_lab_id: ID of the source lab to clone
        new_lab_name: Name for the new cloned lab
        market_tag: Market tag (e.g., "BINANCE_BTC_USDT_")
        account_id: Account ID to use for the lab
        start_unix: Backtest start time (Unix timestamp)
        end_unix: Backtest end time (Unix timestamp)
        config: Optional LabConfig. If None, uses default intelligent mode config
        send_email: Whether to send email notifications
        
    Returns:
        Dictionary containing:
        - success: bool - Whether the operation was successful
        - lab_id: str - ID of the created lab
        - lab_name: str - Name of the created lab
        - market_tag: str - Market tag that was set
        - account_id: str - Account ID that was set
        - config_applied: LabConfig - Config that was applied
        - backtest_started: bool - Whether backtest was started
        - error: str - Error message if any
        
    Raises:
        HaasApiError: If any API request fails
        
    Example:
        >>> # Complete workflow for cloning and backtesting
        >>> result = api.clone_and_backtest_lab(
        ...     executor=executor,
        ...     source_lab_id="example_lab_id",
        ...     new_lab_name="BTC_USDT_Backtest",
        ...     market_tag="BINANCE_BTC_USDT_",
        ...     account_id="account_id",
        ...     start_unix=1744009200,  # April 7th 2025 13:00
        ...     end_unix=1752994800,    # End time
        ...     config=LabConfig(max_population=10, max_generations=100, max_elites=3, mix_rate=40.0, adjust_rate=25.0)
        ... )
        >>> 
        >>> if result['success']:
        ...     print(f"✅ Lab created: {result['lab_name']}")
        ...     print(f"✅ Backtest started: {result['backtest_started']}")
        ... else:
        ...     print(f"❌ Failed: {result['error']}")
        
    See Also:
        - docs/LAB_CLONING_DISCOVERY.md for detailed explanation
        - docs/CONFIG_PARAMETER_FIX_SUMMARY.md for config parameter details
    """
    try:
        log.info(f"🚀 Starting complete lab cloning and backtesting workflow")
        log.info(f"   Source Lab: {source_lab_id}")
        log.info(f"   New Name: {new_lab_name}")
        log.info(f"   Market: {market_tag}")
        log.info(f"   Account: {account_id}")
        
        # Step 1: Clone the lab
        log.info(f"📋 Step 1: Cloning lab...")
        cloned_lab = clone_lab(executor, source_lab_id, new_lab_name)
        log.info(f"✅ Lab cloned successfully: {cloned_lab.lab_id}")
        
        # Step 2: Update market tag and account ID
        log.info(f"🔄 Step 2: Updating market and account...")
        lab_details = get_lab_details(executor, cloned_lab.lab_id)
        lab_details.settings.market_tag = market_tag
        lab_details.settings.account_id = account_id
        updated_lab = update_lab_details(executor, lab_details)
        log.info(f"✅ Market and account updated: {market_tag} / {account_id}")
        
        # Step 3: Ensure proper config parameters
        log.info(f"🔧 Step 3: Ensuring config parameters...")
        config_applied = ensure_lab_config_parameters(executor, cloned_lab.lab_id, config)
        log.info(f"✅ Config parameters verified/updated")
        
        # Step 4: Start backtest
        log.info(f"🚀 Step 4: Starting backtest...")
        backtest_request = StartLabExecutionRequest(
            lab_id=cloned_lab.lab_id,
            start_unix=start_unix,
            end_unix=end_unix,
            send_email=send_email
        )
        
        # Use ensure_config=False since we already ensured it
        execution_result = start_lab_execution(executor, backtest_request, ensure_config=False)
        log.info(f"✅ Backtest started successfully")
        
        return {
            "success": True,
            "lab_id": cloned_lab.lab_id,
            "lab_name": cloned_lab.name,
            "market_tag": market_tag,
            "account_id": account_id,
            "config_applied": config_applied.config,
            "backtest_started": True,
            "execution_status": execution_result.status,
            "error": None
        }
        
    except Exception as e:
        error_msg = f"Failed in lab cloning and backtesting workflow: {str(e)}"
        log.error(f"❌ {error_msg}")
        return {
            "success": False,
            "lab_id": None,
            "lab_name": new_lab_name,
            "market_tag": market_tag,
            "account_id": account_id,
            "config_applied": None,
            "backtest_started": False,
            "execution_status": None,
            "error": error_msg
        }


def bulk_clone_and_backtest_labs(
    executor: SyncExecutor[Authenticated],
    source_lab_id: str,
    market_configs: List[Dict[str, str]],
    start_unix: int,
    end_unix: int,
    config: Optional[LabConfig] = None,
    send_email: bool = False,
    delay_between_labs: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Bulk clone and backtest labs for multiple markets.
    
    This function provides a production-ready bulk workflow that handles multiple markets
    with proper error handling and progress tracking.
    
    Args:
        executor: Authenticated executor instance
        source_lab_id: ID of the source lab to clone
        market_configs: List of dicts with 'name', 'market_tag', and 'account_id'
        start_unix: Backtest start time (Unix timestamp)
        end_unix: Backtest end time (Unix timestamp)
        config: Optional LabConfig. If None, uses default intelligent mode config
        send_email: Whether to send email notifications
        delay_between_labs: Delay between lab creations (seconds)
        
    Returns:
        List of result dictionaries from clone_and_backtest_lab
        
    Example:
        >>> # Bulk workflow for multiple markets
        >>> market_configs = [
        ...     {"name": "BTC_USDT_Backtest", "market_tag": "BINANCE_BTC_USDT_", "account_id": "account1"},
        ...     {"name": "ETH_USDT_Backtest", "market_tag": "BINANCE_ETH_USDT_", "account_id": "account1"},
        ...     {"name": "SOL_USDT_Backtest", "market_tag": "BINANCE_SOL_USDT_", "account_id": "account1"}
        ... ]
        >>> 
        >>> results = api.bulk_clone_and_backtest_labs(
        ...     executor=executor,
        ...     source_lab_id="example_lab_id",
        ...     market_configs=market_configs,
        ...     start_unix=1744009200,
        ...     end_unix=1752994800
        ... )
        >>> 
        >>> # Process results
        >>> successful = [r for r in results if r['success']]
        >>> failed = [r for r in results if not r['success']]
        >>> print(f"✅ Successful: {len(successful)}")
        >>> print(f"❌ Failed: {len(failed)}")
    
    See Also:
        - docs/BULK_LAB_CREATION_TUTORIAL.md for a user-friendly guide
        - clone_and_backtest_lab() for single-market workflow
    """
    log.info(f"🚀 Starting bulk lab cloning and backtesting workflow")
    log.info(f"   Source Lab: {source_lab_id}")
    log.info(f"   Markets: {len(market_configs)}")
    log.info(f"   Start Time: {start_unix}")
    log.info(f"   End Time: {end_unix}")
    
    results = []
    
    for i, market_config in enumerate(market_configs, 1):
        log.info(f"\n📋 Processing market {i}/{len(market_configs)}: {market_config['name']}")
        
        try:
            result = clone_and_backtest_lab(
                executor=executor,
                source_lab_id=source_lab_id,
                new_lab_name=market_config['name'],
                market_tag=market_config['market_tag'],
                account_id=market_config['account_id'],
                start_unix=start_unix,
                end_unix=end_unix,
                config=config,
                send_email=send_email
            )
            
            results.append(result)
            
            if result['success']:
                log.info(f"✅ Success: {market_config['name']} (Lab: {result['lab_id']})")
            else:
                log.error(f"❌ Failed: {market_config['name']} - {result['error']}")
                
        except Exception as e:
            error_result = {
                "success": False,
                "lab_id": None,
                "lab_name": market_config['name'],
                "market_tag": market_config['market_tag'],
                "account_id": market_config['account_id'],
                "config_applied": None,
                "backtest_started": False,
                "execution_status": None,
                "error": f"Exception in bulk workflow: {str(e)}"
            }
            results.append(error_result)
            log.error(f"❌ Exception for {market_config['name']}: {str(e)}")
        
        # Delay between labs to avoid rate limits
        if i < len(market_configs):
            log.info(f"⏳ Waiting {delay_between_labs}s before next lab...")
            time.sleep(delay_between_labs)
    
    # Summary
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    log.info(f"\n📊 Bulk Workflow Summary:")
    log.info(f"   ✅ Successful: {len(successful)}/{len(market_configs)}")
    log.info(f"   ❌ Failed: {len(failed)}/{len(market_configs)}")
    
    if failed:
        log.info(f"   Failed markets:")
        for result in failed:
            log.info(f"     - {result['lab_name']}: {result['error']}")
    
    return results


def ensure_history_synced(
    executor: SyncExecutor[Authenticated],
    market: str,
    months: int = 12
) -> bool:
    """
    Ensure that the specified market has sufficient history depth before backtesting.
    If the current history depth is less than the requested months, set it automatically.

    Args:
        executor: Authenticated executor instance
        market: Market tag (e.g., "BINANCE_BTC_USDT_")
        months: Minimum months of history required (default: 12)

    Returns:
        True if history is already sufficient or was set successfully, False otherwise

    Example:
        >>> ensure_history_synced(executor, "BINANCE_BTC_USDT_", months=12)
    """
    try:
        history_status = get_history_status(executor)
        info = history_status.get(market)
        if info and info.get("months", 0) >= months:
            return True
        return set_history_depth(executor, market, months)
    except Exception as e:
        log.error(f"Failed to ensure history sync for {market}: {e}")
        return False


def get_chart(
    executor: SyncExecutor[Authenticated],
    market: str,
    interval: int = 15,
    style: int = 301
) -> dict:
    """
    Get chart data for a specific market and interval (triggers history sync if not present).

    Args:
        executor: Authenticated executor instance
        market: Market tag (e.g., "BINANCE_BTC_USDT_")
        interval: Chart interval (default: 15)
        style: Chart style (default: 301)

    Returns:
        Chart data dictionary

    Example:
        >>> get_chart(executor, "BINANCE_BTC_USDT_", interval=15, style=301)
    """
    return executor.execute(
        endpoint="Price",
        response_type=dict,
        query_params={
            "channel": "GET_CHART",
            "market": market,
            "interval": interval,
            "style": style
        }
    )


def ensure_market_history_ready(
    executor: SyncExecutor[Authenticated],
    market: str,
    months: int = 36,
    poll_interval: int = 5,
    timeout: int = 300
) -> bool:
    """
    Ensure a market is in the history sync list, synched, and set to the desired history depth.
    Triggers sync if needed, waits for Status 3, and sets history depth.

    Args:
        executor: Authenticated executor instance
        market: Market tag (e.g., "BINANCE_BTC_USDT_")
        months: Desired history depth (default: 36)
        poll_interval: Polling interval in seconds (default: 5)
        timeout: Max wait time in seconds (default: 300)

    Returns:
        True if market is synched and set to desired depth, False otherwise

    Example:
        >>> ensure_market_history_ready(executor, "BINANCE_BTC_USDT_", months=36)
    """
    try:
        # Trigger GET_CHART to initiate sync
        try:
            get_chart(executor, market, interval=15, style=301)
        except Exception:
            pass  # Ignore errors, just want to trigger sync
        waited = 0
        info = None
        while True:
            history_status = get_history_status(executor)
            info = history_status.get(market)
            if info and info.get("Status") == 3:
                break
            time.sleep(poll_interval)
            waited += poll_interval
            if waited >= timeout:
                return False
        # Set history depth
        return set_history_depth(executor, market, months)
    except Exception as e:
        log.error(f"Failed to ensure market history ready for {market}: {e}")
        return False

def app_login(
    executor: SyncExecutor[Authenticated],
    app_id: str,
    app_secret: str
) -> dict:
    """
    Log in to the app using app_id and app_secret.
    Args:
        executor: Authenticated executor instance
        app_id: Application ID
        app_secret: Application secret
    Returns:
        Login response dictionary
    Example:
        >>> app_login(executor, "my_app_id", "my_secret")
    """
    return executor.execute(
        endpoint="User",
        response_type=dict,
        query_params={
            "channel": "APP_LOGIN",
            "app_id": app_id,
            "app_secret": app_secret
        }
    )

def check_token(
    executor: SyncExecutor[Authenticated],
    token: str
) -> bool:
    """
    Check if a user token is valid.
    Args:
        executor: Authenticated executor instance
        token: User token
    Returns:
        True if token is valid, False otherwise
    Example:
        >>> check_token(executor, "token123")
    """
    resp = executor.execute(
        endpoint="User",
        response_type=dict,
        query_params={
            "channel": "CHECK_TOKEN",
            "token": token
        }
    )
    return resp.get("valid", False)

def logout(
    executor: SyncExecutor[Authenticated]
) -> bool:
    """
    Log out the current user session.
    Args:
        executor: Authenticated executor instance
    Returns:
        True if logout was successful, False otherwise
    Example:
        >>> logout(executor)
    """
    resp = executor.execute(
        endpoint="User",
        response_type=dict,
        query_params={
            "channel": "LOGOUT"
        }
    )
    return resp.get("Success", False)

def is_device_approved(
    executor: SyncExecutor[Authenticated],
    device_id: str
) -> bool:
    """
    Check if a device is approved for the user.
    Args:
        executor: Authenticated executor instance
        device_id: Device identifier
    Returns:
        True if device is approved, False otherwise
    Example:
        >>> is_device_approved(executor, "device123")
    """
    resp = executor.execute(
        endpoint="User",
        response_type=dict,
        query_params={
            "channel": "IS_DEVICE_APPROVED",
            "deviceid": device_id
        }
    )
    return resp.get("approved", False)

def get_trade_markets(executor, exchange_code):
    from pyHaasAPI.price import PriceAPI
    return PriceAPI(executor).get_trade_markets(exchange_code)

def get_market_price_info(
    executor: SyncExecutor[Authenticated],
    market: str
) -> dict:
    """
    Get detailed market price info (Tools - Market View in web UI).

    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BITMEX_XBT_USD_XBTUSD")

    Returns:
        Market price info dictionary

    Raises:
        HaasApiError: If the API request fails
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    return executor.execute(
        endpoint="Interface",
        response_type=dict,
        query_params={
            "channel": "MARKET_PRICE_INFO",
            "market": market,
            "interfacekey": interface_key,
            "userid": user_id,
        },
    )


def get_market_ta_info(
    executor: SyncExecutor[Authenticated],
    market: str
) -> dict:
    """
    Get technical analysis info for a market (Tools - Market Intelligence in web UI).

    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BITMEX_XBT_USD_XBTUSD")

    Returns:
        Market TA info dictionary

    Raises:
        HaasApiError: If the API request fails
    """
    user_id = executor.state.user_id
    interface_key = executor.state.interface_key
    return executor.execute(
        endpoint="Interface",
        response_type=dict,
        query_params={
            "channel": "MARKET_TA_INFO",
            "market": market,
            "interfacekey": interface_key,
            "userid": user_id,
        },
    )

def add_bot_from_lab_with_futures(
    executor: SyncExecutor[Authenticated],
    lab_id: str,
    backtest_id: str,
    bot_name: str,
    account_id: str,
    market: str,
    leverage: float = 0.0,
    position_mode: int = 0,
    margin_mode: int = 0,
) -> dict:
    """
    Add a bot from lab results with futures market support.
    
    This function supports the new futures market format like:
    - BINANCEQUARTERLY_BTC_USD_PERPETUAL
    - BINANCEQUARTERLY_BTC_USD_QUARTERLY
    
    Args:
        executor: Authenticated executor instance
        lab_id: Lab ID
        backtest_id: Backtest ID
        bot_name: Name for the bot
        account_id: Account ID
        market: Market tag (supports PERPETUAL/QUARTERLY format)
        leverage: Leverage setting (e.g., 50.0 for 50x)
        position_mode: Position mode (0=ONE_WAY, 1=HEDGE)
        margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
        
    Returns:
        Dictionary with bot creation results
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=dict,
        query_params={
            "channel": "ADD_BOT_FROM_LABS",
            "labid": lab_id,
            "backtestid": backtest_id,
            "botname": bot_name,
            "accountid": account_id,
            "market": market,
            "leverage": leverage,
        },
        use_post=True,
    )

def adjust_margin_settings(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
    position_mode: int | None = None,
    margin_mode: int | None = None,
    leverage: float | None = None,
) -> dict:
    """
    Adjust margin settings for an account/market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        position_mode: Position mode (0=ONE-WAY, 1=HEDGE) or None to keep current
        margin_mode: Margin mode (0=CROSS, 1=ISOLATED) or None to keep current
        leverage: Leverage value (e.g., 50.0 for 50x) or None to keep current
        
    Returns:
        Dictionary with updated settings: {"PM": 0, "SMM": 0, "LL": 50.0, "SL": 50.0}
        
    Raises:
        HaasApiError: If the API request fails
    """
    query_params = {
        "channel": "ADJUST_MARGIN_SETTINGS",
        "accountid": account_id,
        "market": market,
    }
    
    if position_mode is not None:
        query_params["positionmode"] = position_mode
    if margin_mode is not None:
        query_params["marginmode"] = margin_mode
    if leverage is not None:
        query_params["leverage"] = leverage
        
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params=query_params,
    )

def set_position_mode(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
    position_mode: int,
) -> bool:
    """
    Set position mode for an account/market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        position_mode: Position mode (0=ONE-WAY, 1=HEDGE)
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    try:
        # Get current settings first
        current_settings = get_margin_settings(executor, account_id, market)
        
        # Update with new position mode, keeping other settings
        result = adjust_margin_settings(
            executor, 
            account_id, 
            market, 
            position_mode=position_mode,
            margin_mode=current_settings.get("SMM", 0),
            leverage=current_settings.get("LL", 0.0)
        )
        return result.get("PM") == position_mode
    except Exception as e:
        from loguru import logger
        logger.error(f"Failed to set position mode: {e}")
        return False

def set_margin_mode(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
    margin_mode: int,
) -> bool:
    """
    Set margin mode for an account/market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    try:
        # Get current settings first
        current_settings = get_margin_settings(executor, account_id, market)
        
        # Update with new margin mode, keeping other settings
        result = adjust_margin_settings(
            executor, 
            account_id, 
            market, 
            position_mode=current_settings.get("PM", 0),
            margin_mode=margin_mode,
            leverage=current_settings.get("LL", 0.0)
        )
        return result.get("SMM") == margin_mode
    except Exception as e:
        from loguru import logger
        logger.error(f"Failed to set margin mode: {e}")
        return False

def set_leverage(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
    leverage: float,
) -> bool:
    """
    Set leverage for an account/market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        leverage: Leverage value (e.g., 50.0 for 50x)
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    try:
        # Get current settings first
        current_settings = get_margin_settings(executor, account_id, market)
        
        # Update with new leverage, keeping other settings
        result = adjust_margin_settings(
            executor, 
            account_id, 
            market, 
            position_mode=current_settings.get("PM", 0),
            margin_mode=current_settings.get("SMM", 0),
            leverage=leverage
        )
        return result.get("LL") == leverage
    except Exception as e:
        from loguru import logger
        logger.error(f"Failed to set leverage: {e}")
        return False

def get_margin_settings(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
) -> dict:
    """
    Get margin settings (position mode, margin mode, leverage) for a specific market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        
    Returns:
        Dictionary with margin settings: {"PM": 0, "SMM": 0, "LL": 50.0, "SL": 50.0}
        - PM: Position Mode (0=ONE-WAY, 1=HEDGE)
        - SMM: Secondary Margin Mode (0=CROSS, 1=ISOLATED)
        - LL: Long Leverage
        - SL: Short Leverage
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "GET_MARGIN_SETTINGS",
            "accountid": account_id,
            "market": market,
        },
    )

def get_position_mode(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
) -> int:
    """
    Get current position mode for an account/market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        
    Returns:
        Position mode (0=ONE-WAY, 1=HEDGE)
        
    Raises:
        HaasApiError: If the API request fails
    """
    settings = get_margin_settings(executor, account_id, market)
    return settings.get("PM", 0)  # PM = Position Mode

def get_margin_mode(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
) -> int:
    """
    Get current margin mode for an account/market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        
    Returns:
        Margin mode (0=CROSS, 1=ISOLATED)
        
    Raises:
        HaasApiError: If the API request fails
    """
    settings = get_margin_settings(executor, account_id, market)
    return settings.get("SMM", 0)  # SMM = Secondary Margin Mode

def get_leverage(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
) -> float:
    """
    Get current leverage for an account/market.
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market tag
        
    Returns:
        Leverage value (e.g., 50.0 for 50x)
        
    Raises:
        HaasApiError: If the API request fails
    """
    settings = get_margin_settings(executor, account_id, market)
    return settings.get("LL", 0.0)  # LL = Long Leverage

def get_futures_markets(
    executor: SyncExecutor[Authenticated],
    exchange_code: str = "BINANCEQUARTERLY",
) -> List[dict]:
    """
    Get available futures markets for a specific exchange.
    
    Args:
        executor: Authenticated executor instance
        exchange_code: Exchange code (e.g., "BINANCEQUARTERLY")
        
    Returns:
        List of futures markets with contract types
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Price",
        response_type=List[dict],
        query_params={
            "channel": "FUTURES_MARKETS",
            "pricesource": exchange_code,
        },
    )

def create_futures_lab(
    executor: SyncExecutor[Authenticated],
    script_id: str,
    account_id: str,
    market: str,
    exchange_code: str = "BINANCEQUARTERLY",
    contract_type: str = "PERPETUAL",
    interval: int = 1,
    leverage: float = 0.0,
    position_mode: int = 0,
    margin_mode: int = 0,
) -> dict:
    """
    Create a lab specifically for futures trading.
    
    Args:
        executor: Authenticated executor instance
        script_id: Script ID
        account_id: Account ID
        market: Market object or string
        exchange_code: Exchange code (e.g., "BINANCEQUARTERLY")
        contract_type: Contract type ("PERPETUAL" or "QUARTERLY")
        interval: Chart interval
        leverage: Leverage setting
        position_mode: Position mode (0=ONE_WAY, 1=HEDGE)
        margin_mode: Margin mode (0=CROSS, 1=ISOLATED)
        
    Returns:
        Dictionary with lab creation results
        
    Raises:
        HaasApiError: If the API request fails
    """
    from pyHaasAPI.model import CreateLabRequest, CloudMarket, PriceDataStyle
    
    # Handle market input
    if isinstance(market, str):
        # Parse market string to create CloudMarket object
        parts = market.split('_')
        if len(parts) >= 2:
            primary = parts[0]
            secondary = parts[1]
            market_obj = CloudMarket(
                category="FUTURES",
                price_source=exchange_code,
                primary=primary,
                secondary=secondary,
                contract_type=contract_type
            )
        else:
            raise ValueError(f"Invalid market format: {market}")
    else:
        market_obj = market
    
    # Create lab request
    lab_request = CreateLabRequest.with_futures_market(
        script_id=script_id,
        account_id=account_id,
        market=market_obj,
        exchange_code=exchange_code,
        interval=interval,
        default_price_data_style=PriceDataStyle.CandleStick,
        contract_type=contract_type,
    )
    
    # Add futures-specific settings
    lab_request.leverage = leverage
    lab_request.position_mode = position_mode
    lab_request.margin_mode = margin_mode
    
    return create_lab(executor, lab_request)

def get_bot_closed_positions(executor: SyncExecutor[Authenticated], bot_id: str) -> list[dict]:
    """
    Get closed positions for a bot.

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot

    Returns:
        List of closed position dictionaries
    """
    response = executor.execute(
        endpoint="Bot",
        response_type=dict,
        query_params={
            "channel": "GET_RUNTIME_CLOSED_POSITIONS",
            "botid": bot_id,
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )
    return response.get("Data", [])


def get_comprehensive_bot(executor: SyncExecutor[Authenticated], bot_id: str) -> dict:
    """
    Get a comprehensive bot object combining all data sources.
    This mimics what the web interface does by combining:
    - GET_BOT (basic info)
    - GET_RUNTIME (runtime data + parameters)
    - GET_RUNTIME_LOGBOOK (logs)
    - GET_RUNTIME_CLOSED_POSITIONS (closed positions)

    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot

    Returns:
        Comprehensive bot dictionary with all available data
    """
    try:
        # Get basic bot info
        basic_bot = get_bot(executor, bot_id)
        
        # Get runtime data (includes script parameters)
        runtime_data = get_bot_runtime(executor, bot_id)
        
        # Get recent logs
        logs = get_bot_runtime_logbook(executor, bot_id, page_length=50)
        
        # Get closed positions
        closed_positions = get_bot_closed_positions(executor, bot_id)
        
        # Combine all data
        comprehensive_bot = {
            "basic_info": basic_bot.model_dump() if hasattr(basic_bot, 'model_dump') else basic_bot,
            "runtime_data": runtime_data,
            "recent_logs": logs,
            "closed_positions": closed_positions,
            "script_parameters": runtime_data.get("InputFields", {}),
            "bot_id": bot_id
        }
        
        return comprehensive_bot
        
    except Exception as e:
        log.error(f"Failed to get comprehensive bot data for {bot_id}: {e}")
        raise HaasApiError(f"Failed to get comprehensive bot data: {e}")


def edit_bot_parameter_by_name(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    parameter_name: str, 
    new_value: Any
) -> HaasBot:
    """
    Edit a single bot parameter by its human-readable name.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        parameter_name: Human-readable parameter name (e.g., "Stop Loss (%)")
        new_value: New value for the parameter
        
    Returns:
        Updated HaasBot object
        
    Raises:
        HaasApiError: If parameter not found or update fails
    """
    # Get current bot and parameters
    bot = get_bot(executor, bot_id)
    script_params = get_bot_script_parameters(executor, bot_id)
    
    # Find parameter by name
    param_key = None
    param_details = None
    
    for key, details in script_params.items():
        if isinstance(details, dict) and details.get("N") == parameter_name:
            param_key = key
            param_details = details
            break
    
    if not param_key:
        available_params = [details.get("N", "Unknown") for details in script_params.values() 
                          if isinstance(details, dict)]
        raise HaasApiError(f"Parameter '{parameter_name}' not found. Available parameters: {available_params}")
    
    # Validate value against constraints
    param_type = param_details.get("T")
    min_val = param_details.get("MIN")
    max_val = param_details.get("MAX")
    
    # Type conversion and validation
    try:
        if param_type == 0:  # Numeric
            new_value = float(new_value)
            if min_val is not None and new_value < min_val:
                raise ValueError(f"Value {new_value} is below minimum {min_val}")
            if max_val is not None and new_value > max_val:
                raise ValueError(f"Value {new_value} is above maximum {max_val}")
        elif param_type == 2:  # Boolean
            if isinstance(new_value, str):
                new_value = new_value.lower() == "true"
        elif param_type == 3:  # Options/Enum
            options = param_details.get("O", {})
            if new_value not in options:
                raise ValueError(f"Value '{new_value}' not in available options: {list(options.keys())}")
    except ValueError as e:
        raise HaasApiError(f"Parameter validation failed: {e}")
    
    # Update the parameter in the bot's settings
    if not bot.settings.script_parameters:
        bot.settings.script_parameters = {}
    
    # Use the full key for the update
    full_key = param_details.get("K", param_key)
    bot.settings.script_parameters[full_key] = new_value
    
    # Apply the update
    return edit_bot_parameter(executor, bot)


def edit_bot_parameters_by_group(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    group_name: str, 
    parameters: Dict[str, Any]
) -> HaasBot:
    """
    Edit multiple bot parameters that belong to the same group.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        group_name: Name of the parameter group (e.g., "MadHatter BBands")
        parameters: Dictionary of parameter names to new values
        
    Returns:
        Updated HaasBot object
        
    Raises:
        HaasApiError: If group not found or any parameter update fails
    """
    # Get current bot and parameters
    bot = get_bot(executor, bot_id)
    script_params = get_bot_script_parameters(executor, bot_id)
    
    # Find all parameters in the group
    group_params = {}
    for key, details in script_params.items():
        if isinstance(details, dict) and details.get("G") == group_name:
            param_name = details.get("N")
            if param_name in parameters:
                group_params[key] = details
    
    if not group_params:
        available_groups = set(details.get("G", "") for details in script_params.values() 
                             if isinstance(details, dict))
        raise HaasApiError(f"Group '{group_name}' not found. Available groups: {list(available_groups)}")
    
    # Update each parameter
    if not bot.settings.script_parameters:
        bot.settings.script_parameters = {}
    
    for param_key, param_details in group_params.items():
        param_name = param_details.get("N")
        new_value = parameters[param_name]
        
        # Validate value
        param_type = param_details.get("T")
        min_val = param_details.get("MIN")
        max_val = param_details.get("MAX")
        
        try:
            if param_type == 0:  # Numeric
                new_value = float(new_value)
                if min_val is not None and new_value < min_val:
                    raise ValueError(f"Parameter '{param_name}': value {new_value} is below minimum {min_val}")
                if max_val is not None and new_value > max_val:
                    raise ValueError(f"Parameter '{param_name}': value {new_value} is above maximum {max_val}")
            elif param_type == 2:  # Boolean
                if isinstance(new_value, str):
                    new_value = new_value.lower() == "true"
            elif param_type == 3:  # Options/Enum
                options = param_details.get("O", {})
                if new_value not in options:
                    raise ValueError(f"Parameter '{param_name}': value '{new_value}' not in available options: {list(options.keys())}")
        except ValueError as e:
            raise HaasApiError(f"Parameter validation failed: {e}")
        
        # Use the full key for the update
        full_key = param_details.get("K", param_key)
        bot.settings.script_parameters[full_key] = new_value
    
    # Apply all updates
    return edit_bot_parameter(executor, bot)


def validate_bot_parameters(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    parameters: Dict[str, Any]
) -> Dict[str, List[str]]:
    """
    Validate parameter values against their constraints without applying changes.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        parameters: Dictionary of parameter names to values to validate
        
    Returns:
        Dictionary with 'valid' and 'invalid' parameter lists
    """
    script_params = get_bot_script_parameters(executor, bot_id)
    
    valid_params = []
    invalid_params = []
    
    for param_name, new_value in parameters.items():
        # Find parameter by name
        param_details = None
        for key, details in script_params.items():
            if isinstance(details, dict) and details.get("N") == param_name:
                param_details = details
                break
        
        if not param_details:
            invalid_params.append(f"Parameter '{param_name}' not found")
            continue
        
        # Validate value
        param_type = param_details.get("T")
        min_val = param_details.get("MIN")
        max_val = param_details.get("MAX")
        
        try:
            if param_type == 0:  # Numeric
                new_value = float(new_value)
                if min_val is not None and new_value < min_val:
                    invalid_params.append(f"'{param_name}': value {new_value} is below minimum {min_val}")
                    continue
                if max_val is not None and new_value > max_val:
                    invalid_params.append(f"'{param_name}': value {new_value} is above maximum {max_val}")
                    continue
            elif param_type == 2:  # Boolean
                if isinstance(new_value, str):
                    new_value = new_value.lower() == "true"
            elif param_type == 3:  # Options/Enum
                options = param_details.get("O", {})
                if new_value not in options:
                    invalid_params.append(f"'{param_name}': value '{new_value}' not in available options: {list(options.keys())}")
                    continue
            
            valid_params.append(param_name)
            
        except ValueError as e:
            invalid_params.append(f"'{param_name}': {e}")
    
    return {
        "valid": valid_params,
        "invalid": invalid_params
    }


def get_bot_parameter_groups(executor: SyncExecutor[Authenticated], bot_id: str) -> Dict[str, List[str]]:
    """
    Get all parameter groups and their parameters for a bot.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        
    Returns:
        Dictionary mapping group names to lists of parameter names
    """
    script_params = get_bot_script_parameters(executor, bot_id)
    
    groups = {}
    for key, details in script_params.items():
        if isinstance(details, dict):
            group_name = details.get("G", "Ungrouped")
            param_name = details.get("N", "Unknown")
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(param_name)
    
    return groups


































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































