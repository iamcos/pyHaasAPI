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
    BacktestRuntimeData,
    BacktestRuntimeResponse,
    BotRuntimeData,
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


@dataclasses.dataclass(frozen=True, slots=True)
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
        print(f"Request URL: {url}")
        print(f"Request Params: {query_params}")
        
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
        if use_post or (channel in ["START_LAB_EXECUTION", "EDIT_SETTINGS", "EXECUTE_QUICKTEST"]):
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
        print(f"Response: {resp.text}")
        print("---END_OF_RESPONSE---")

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
            
            # Handle cases where the API returns a list in the 'Data' field
            if response_type == list[dict] or (isinstance(response_type, type) and issubclass(response_type, List)):
                if isinstance(resp_json, dict) and "Data" in resp_json:
                    return resp_json["Data"]
                else:
                    # If it's supposed to be a list but not in 'Data', return raw or empty list
                    return resp_json # Or return [] if an empty list is preferred on malformed response

            try:
                if response_type == HaasBot:
                    log.debug(f"Raw response for HaasBot: {resp_json}")
                return ta.validate_python(resp_json)
            except ValidationError as e:
                log.error(f"Pydantic validation error: {e}")
                return resp_json
        except Exception as e:
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



def get_haasscript_commands(executor: SyncExecutor[Authenticated]) -> List[Dict[str, Any]]:
    """
    Get all available HaasScript commands and their descriptions.
    
    Args:
        executor: Authenticated executor instance
        
    Returns:
        A list of dictionaries containing all HaasScript commands and their details.
        
    Raises:
        HaasApiError: If the API request fails
    """
    raw_response = executor.execute(
        endpoint="HaasScript",
        response_type=List[Dict[str, Any]],
        query_params={
            "channel": "GET_COMMANDS",
        },
    )
    return raw_response


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


def get_all_scripts(
    executor: SyncExecutor[Authenticated],
) -> List[Dict[str, Any]]:
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


def create_lab(executor: SyncExecutor[Authenticated], req: CreateLabRequest) -> LabDetails:
    """
    Create a new lab"""
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
    1.  **Parameter Names**: Changed `labId` to `labid` (lowercase) to match server expectations
    2.  **Settings Serialization**: Added `by_alias=True` to use camelCase field names (accountId, marketTag, etc.)
    3.  **HTTP Method**: Changed from POST to GET method for all requests
    4.  **Parameter Format**: Preserved original data types in parameter options (numbers as numbers, strings as strings)
    
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
        - docs/LAB_CLONING_DISCOVERY.md for detailed explanation
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

    # Send update using POST with form data (like the working curl example)
    import requests
    import json
    
    # Prepare form data exactly like the working curl example
    form_data = {
        'labid': lab_details.lab_id,
        'name': lab_details.name,
        'type': str(lab_details.type),
        'config': json.dumps({
            "MP": lab_details.config.max_population,
            "MG": lab_details.config.max_generations, 
            "ME": lab_details.config.max_elites,
            "MR": lab_details.config.mix_rate,
            "AR": lab_details.config.adjust_rate
        }),
        'settings': json.dumps({
            "botId": lab_details.settings.bot_id,
            "botName": lab_details.settings.bot_name,
            "accountId": lab_details.settings.account_id,
            "marketTag": lab_details.settings.market_tag,
            "leverage": lab_details.settings.leverage,
            "positionMode": lab_details.settings.position_mode,
            "marginMode": lab_details.settings.margin_mode,
            "interval": lab_details.settings.interval,
            "chartStyle": lab_details.settings.chart_style,
            "tradeAmount": lab_details.settings.trade_amount,
            "orderTemplate": lab_details.settings.order_template,
            "scriptParameters": lab_details.settings.script_parameters or {}
        }),
        'parameters': json.dumps(params_list),
        'interfacekey': executor.state.interface_key,
        'userid': executor.state.user_id
    }
    
    # Make direct POST request to avoid URL length limits
    url = f"http://{executor.host}:{executor.port}/LabsAPI.php?channel=UPDATE_LAB_DETAILS"
    
    try:
        response = requests.post(url, data=form_data, headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        response.raise_for_status()
        response_data = response.json()
        
        if not response_data.get('Success', False):
            log.error(f"Failed to update lab details: {response_data.get('Error', 'Unknown error')}")
            return get_lab_details(executor, lab_details.lab_id)
            
    except Exception as e:
        log.error(f"Error making POST request: {e}")
        return get_lab_details(executor, lab_details.lab_id)

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
        response_type=bool,
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
    """
    Get all labs for the authenticated user"""
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

# New access point for structured backtest runtime data
def get_full_backtest_runtime_data(executor: SyncExecutor[Authenticated], lab_id: str, backtest_id: str) -> BacktestRuntimeData:
    """
    Get detailed runtime information for a specific backtest as a structured object.
    
    This function retrieves comprehensive backtest runtime data including:
    - Chart information and status
    - Compiler errors and warnings
    - Trading reports with performance metrics
    - Account and market information
    - Position and order data
    - Script execution details
    
    Args:
        executor: Authenticated executor instance
        lab_id: ID of the lab containing the backtest
        backtest_id: ID of the specific backtest to retrieve
        
    Returns:
        BacktestRuntimeData object with complete runtime information
        
    Raises:
        HaasApiError: If the API request fails
        ValidationError: If the response data cannot be parsed into expected structure

    Note:
        The HaasOnline API returns data directly (not wrapped in a Data envelope).
        Report keys follow the pattern: {AccountId}_{PriceMarket}
        Example: "6bccabce-9bbe-42a3-a6ee-0cc4bf1e0cbe_BINANCEFUTURES_UNI_USDT_PERPETUAL"

    Example:
        >>> runtime_data = get_full_backtest_runtime_data(executor, "lab123", "bt456")
        >>> print(f"Account: {runtime_data.AccountId}")
        >>> print(f"Market: {runtime_data.PriceMarket}")
        >>> reports = runtime_data.Reports
        >>> for key, report in reports.items():
        ...     print(f"Report {key}: {report.P.C} trades")
    """
    try:
        raw_response = get_backtest_runtime(executor, lab_id, backtest_id)

        # CRITICAL: The API response is direct data, not wrapped in {"Success": ..., "Data": ...}
        # This was the root cause of all backtest retrieval failures
        data_content = raw_response

        # Parse the data into our structured BacktestRuntimeData model
        return BacktestRuntimeData.model_validate(data_content)

    except Exception as e:
        # Re-raise with more context for debugging
        raise HaasApiError(f"Failed to get full backtest runtime data for {backtest_id}: {e}") from e

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

# New access point for structured bot runtime data
def get_full_bot_runtime_data(executor: SyncExecutor[Authenticated], bot_id: str) -> HaasBot:
    """
    Get detailed runtime information for a specific bot as a structured object.
    
    Args:
        executor: Authenticated executor instance
        bot_id: ID of the bot
        
    Returns:
        HaasBot object with complete bot information
        
    Raises:
        HaasApiError: If the API request fails
    """
    return get_bot(executor, bot_id)

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


def edit_script(executor: SyncExecutor[Authenticated], script_id: str, script_name: str = None, script_content: str = None, description: str = "", settings: Optional[dict] = None) -> HaasScriptItemWithDependencies | dict | None:
    """
    Edit an existing script
    
    Args:
        executor: Authenticated executor instance
        script_id: ID of the script to edit
        script_name: New name for the script (optional)
        script_content: New script content (optional)
        description: Description for the script (optional)
        settings: Optional dictionary of script settings to update along with source code.
        
    Returns:
        Updated HaasScriptItemWithDependencies object, or raw dict if partial response
        
    Raises:
        HaasApiError: If the API request fails
    """
    if script_content:
        # If script content is provided, use the EDIT_SCRIPT_SOURCECODE channel
        # Default settings to an empty dict if not provided
        settings = settings if settings is not None else {}
        return edit_script_sourcecode(executor, script_id, script_content, settings)
    else:
        # If only name or description are updated, use the original EDIT_SCRIPT channel
        query_params = {
            "channel": "EDIT_SCRIPT",
            "scriptid": script_id,
            "description": description,
        }
        if script_name:
            query_params["name"] = script_name
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


def execute_debug_test(
    executor: SyncExecutor[Authenticated],
    script_id: str,
    script_type: int,
    settings: HaasScriptSettings
) -> list[str]:
    """
    Executes a debug test for a given script and returns the log output.

    Args:
        executor: Authenticated executor instance.
        script_id: The ID of the script to debug.
        script_type: The type of the script (e.g., 0 for trading script).
        settings: HaasScriptSettings object containing the bot's settings for the debug test.

    Returns:
        A list of strings representing the debug log output.

    Raises:
        HaasApiError: If the API request fails.
    """
    return executor.execute(
        endpoint="Backtest",
        response_type=list[str],
        query_params={
            "channel": "EXECUTE_DEBUGTEST",
            "scriptid": script_id,
            "scripttype": script_type,
            "settings": settings.model_dump_json(by_alias=True),
        },
        use_post=True
    )


def execute_quicktest(
    executor: SyncExecutor[Authenticated],
    backtest_id: str,
    script_id: str,
    settings: HaasScriptSettings
) -> dict:
    """
    Executes a quicktest for a given script and returns the result.

    Args:
        executor: Authenticated executor instance.
        backtest_id: The ID of the backtest.
        script_id: The ID of the script to quicktest.
        settings: HaasScriptSettings object containing the bot's settings for the quicktest.

    Returns:
        A dictionary containing the result of the quicktest.

    Raises:
        HaasApiError: If the API request fails.
    """
    return executor.execute(
        endpoint="Backtest",
        response_type=dict,
        query_params={
            "channel": "EXECUTE_QUICKTEST",
            "backtestid": backtest_id,
            "scriptid": script_id,
            "settings": settings.model_dump_json(by_alias=True),
        },
        use_post=True
    )


def edit_script_sourcecode(
    executor: SyncExecutor[Authenticated],
    script_id: str,
    sourcecode: str,
    settings: dict
) -> dict:
    """
    Updates the source code and settings of a script, mimicking the WebEditor save.
    
    Args:
        executor: Authenticated executor instance
        script_id: ID of the script to edit
        sourcecode: The new source code for the script
        settings: A dictionary containing script settings (e.g., accountId, marketTag)
        
    Returns:
        A dictionary containing the result of the compilation.
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="HaasScript",
        response_type=dict,
        query_params={
            "channel": "EDIT_SCRIPT_SOURCECODE",
            "scriptid": script_id,
            "sourcecode": sourcecode,
            "settings": json.dumps(settings),
        },
        use_post=True
    )


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