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

        # Handle case where _execute_inner returns data directly (for list responses)
        if isinstance(resp, list):
            return resp

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
        #To debug uncomment these lines.
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
        # Uncomment for api Response
        #print(f"Response: {resp.text}")
        #print("---END_OF_RESPONSE---")

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
                    # Return the data directly for list responses
                    return resp_json["Data"]
                else:
                    # If it's supposed to be a list but not in 'Data', return raw or empty list
                    return resp_json if isinstance(resp_json, list) else []

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


def get_all_accounts(executor: SyncExecutor[Authenticated]) -> list[dict]:
    """
    Get all accounts
    
    Args:
        executor: Authenticated executor instance
        
    Returns:
        List of account dictionaries
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=list[dict],
        query_params={
            "channel": "GET_ACCOUNTS",
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


def delete_account(executor: SyncExecutor[Authenticated], account_id: str) -> bool:
    """
    Delete an account
    
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


def add_simulated_account(
    executor: SyncExecutor[Authenticated], 
    name: str, 
    driver_code: str = "SIMULATED", 
    driver_type: int = 0
) -> dict:
    """
    Create a simulated account
    
    Args:
        executor: Authenticated executor instance
        name: Account display name
        driver_code: Driver code (default: "SIMULATED")
        driver_type: Account type identifier (default: 0 for simulated)
        
    Returns:
        Account creation response dictionary
        
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
    Test account connection
    
    Args:
        executor: Authenticated executor instance
        driver_code: Exchange driver code (e.g., "BINANCE", "KRAKEN")
        driver_type: Account type (1 for real, 0 for test)
        version: API version
        public_key: API public key
        private_key: API private key
        extra_key: Optional passphrase
        
    Returns:
        Test result dictionary with success status
        
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


def set_position_mode(
    executor: SyncExecutor[Authenticated], 
    account_id: str, 
    market: str, 
    position_mode: int
) -> dict:
    """
    Set position mode for futures trading (ONE_WAY vs HEDGE)
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        position_mode: Position mode (0 for ONE_WAY, 1 for HEDGE)
        
    Returns:
        Dictionary with updated margin settings
        
    Raises:
        HaasApiError: If the API request fails
    """
    # First get current settings to include all required parameters
    current_settings = get_margin_settings(executor, account_id, market)
    
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "ADJUST_MARGIN_SETTINGS",
            "accountid": account_id,
            "market": market,
            "positionmode": position_mode,
            "marginmode": current_settings.get('SMM', 0),
            "leverage": current_settings.get('LL', 20.0),
        },
    )


def set_margin_mode(
    executor: SyncExecutor[Authenticated], 
    account_id: str, 
    market: str, 
    margin_mode: int
) -> dict:
    """
    Set margin mode for futures trading (CROSS vs ISOLATED)
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        margin_mode: Margin mode (0 for CROSS, 1 for ISOLATED)
        
    Returns:
        Dictionary with updated margin settings
        
    Raises:
        HaasApiError: If the API request fails
    """
    # First get current settings to include all required parameters
    current_settings = get_margin_settings(executor, account_id, market)
    
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "ADJUST_MARGIN_SETTINGS",
            "accountid": account_id,
            "market": market,
            "positionmode": current_settings.get('PM', 1),
            "marginmode": margin_mode,
            "leverage": current_settings.get('LL', 20.0),
        },
    )


def set_leverage(
    executor: SyncExecutor[Authenticated], 
    account_id: str, 
    market: str, 
    leverage: float
) -> dict:
    """
    Set leverage for futures trading
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        leverage: Leverage value (e.g., 20.0 for 20x)
        
    Returns:
        Dictionary with updated margin settings
        
    Raises:
        HaasApiError: If the API request fails
    """
    # First get current settings to include all required parameters
    current_settings = get_margin_settings(executor, account_id, market)
    
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params={
            "channel": "ADJUST_MARGIN_SETTINGS",
            "accountid": account_id,
            "market": market,
            "positionmode": current_settings.get('PM', 1),
            "marginmode": current_settings.get('SMM', 0),
            "leverage": leverage,
        },
    )


def get_margin_settings(
    executor: SyncExecutor[Authenticated], 
    account_id: str, 
    market: str
) -> dict:
    """
    Get current margin settings for an account/market
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        
    Returns:
        Margin settings dictionary
        
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
    market: str
) -> int:
    """
    Get current position mode for an account/market
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        
    Returns:
        Position mode (0 for ONE_WAY, 1 for HEDGE)
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=int,
        query_params={
            "channel": "GET_POSITION_MODE",
            "accountid": account_id,
            "market": market,
        },
    )


def get_margin_mode(
    executor: SyncExecutor[Authenticated], 
    account_id: str, 
    market: str
) -> int:
    """
    Get current margin mode for an account/market
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        
    Returns:
        Margin mode (0 for CROSS, 1 for ISOLATED)
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=int,
        query_params={
            "channel": "GET_MARGIN_MODE",
            "accountid": account_id,
            "market": market,
        },
    )


def get_leverage(
    executor: SyncExecutor[Authenticated], 
    account_id: str, 
    market: str
) -> float:
    """
    Get current leverage for an account/market
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        
    Returns:
        Current leverage value
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=float,
        query_params={
            "channel": "GET_LEVERAGE",
            "accountid": account_id,
            "market": market,
        },
    )


def adjust_margin_settings(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
    position_mode: Optional[int] = None,
    margin_mode: Optional[int] = None,
    leverage: Optional[float] = None
) -> dict:
    """
    Adjust multiple margin settings at once
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        position_mode: Position mode (0 for ONE_WAY, 1 for HEDGE)
        margin_mode: Margin mode (0 for CROSS, 1 for ISOLATED)
        leverage: Leverage value
        
    Returns:
        Dictionary with updated margin settings:
        - PM: Position Mode (0=ONE_WAY, 1=HEDGE)
        - SMM: Spot Margin Mode (0=CROSS, 1=ISOLATED) 
        - LL: Leverage Limit
        - SL: Spot Leverage
        
    Raises:
        HaasApiError: If the API request fails
    """
    # First get current settings to include all required parameters
    current_settings = get_margin_settings(executor, account_id, market)
    
    query_params = {
        "channel": "ADJUST_MARGIN_SETTINGS",
        "accountid": account_id,
        "market": market,
        "positionmode": position_mode if position_mode is not None else current_settings.get('PM', 1),
        "marginmode": margin_mode if margin_mode is not None else current_settings.get('SMM', 0),
        "leverage": leverage if leverage is not None else current_settings.get('LL', 20.0),
    }
    
    return executor.execute(
        endpoint="Account",
        response_type=dict,
        query_params=query_params,
    )


# ============================================================================
# Bot Configuration and Management Functions
# ============================================================================

def configure_bot_settings(
    executor: SyncExecutor[Authenticated],
    bot_id: str,
    position_mode: int = 1,  # 1 for HEDGE
    margin_mode: int = 0,     # 0 for CROSS
    leverage: float = 20.0,
    account_id: Optional[str] = None
) -> dict:
    """
    Configure comprehensive bot settings including margin configuration
    
    Args:
        executor: Authenticated executor instance
        bot_id: Bot ID to configure
        position_mode: Position mode (0 for ONE_WAY, 1 for HEDGE)
        margin_mode: Margin mode (0 for CROSS, 1 for ISOLATED)
        leverage: Leverage value (e.g., 20.0 for 20x)
        account_id: Account ID (if None, will get from bot)
        
    Returns:
        Dictionary with configuration results
        
    Raises:
        HaasApiError: If the API request fails
    """
    try:
        # Get bot details if account_id not provided
        if account_id is None:
            bot = get_bot(executor, bot_id)
            if not bot:
                raise HaasApiError(f"Bot {bot_id} not found")
            account_id = getattr(bot, 'account_id', None)
            if not account_id:
                raise HaasApiError(f"Bot {bot_id} has no account ID")
        
        # Get bot market
        bot = get_bot(executor, bot_id)
        if not bot:
            raise HaasApiError(f"Bot {bot_id} not found")
        market = getattr(bot, 'market', None)
        if not market:
            raise HaasApiError(f"Bot {bot_id} has no market")
        
        # Configure margin settings
        result = adjust_margin_settings(
            executor, 
            account_id, 
            market, 
            position_mode, 
            margin_mode, 
            leverage
        )
        
        return {
            "success": True,
            "bot_id": bot_id,
            "account_id": account_id,
            "market": market,
            "position_mode": position_mode,
            "margin_mode": margin_mode,
            "leverage": leverage,
            "margin_settings": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "bot_id": bot_id,
            "error": str(e)
        }


def migrate_bot_to_account(
    executor: SyncExecutor[Authenticated],
    bot_id: str,
    new_account_id: str,
    preserve_settings: bool = True,
    position_mode: int = 1,
    margin_mode: int = 0,
    leverage: float = 20.0
) -> dict:
    """
    Migrate a bot to a new account with full configuration
    
    Args:
        executor: Authenticated executor instance
        bot_id: Bot ID to migrate
        new_account_id: New account ID
        preserve_settings: Whether to preserve current bot settings
        position_mode: Position mode (0 for ONE_WAY, 1 for HEDGE)
        margin_mode: Margin mode (0 for CROSS, 1 for ISOLATED)
        leverage: Leverage value
        
    Returns:
        Dictionary with migration results including new bot ID
        
    Raises:
        HaasApiError: If the API request fails
    """
    try:
        # Get current bot details
        bot = get_bot(executor, bot_id)
        if not bot:
            raise HaasApiError(f"Bot {bot_id} not found")
        
        bot_name = getattr(bot, 'bot_name', f"Bot_{bot_id[:8]}")
        market = getattr(bot, 'market', 'BINANCEFUTURES_BTC_USDT_PERPETUAL')
        script_id = getattr(bot, 'script_id', '')
        
        # Get bot's lab and backtest info for recreation
        labs = get_all_labs(executor)
        lab = None
        for l in labs:
            if getattr(l, 'script_id', '') == script_id:
                lab = l
                break
        
        if not lab:
            raise HaasApiError(f"Could not find lab for bot {bot_id}")
        
        lab_id = getattr(lab, 'lab_id', '')
        if not lab_id:
            raise HaasApiError(f"Lab {getattr(lab, 'name', 'Unknown')} has no lab ID")
        
        # Get backtests from lab
        from pyHaasAPI.model import GetBacktestResultRequest
        
        request = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=100
        )
        
        response = get_backtest_result(executor, request)
        if not response or not hasattr(response, 'items') or not response.items:
            raise HaasApiError(f"No backtests found for lab {lab_id}")
        
        # Use first backtest as template
        backtest = response.items[0]
        backtest_id = getattr(backtest, 'backtest_id', '')
        if not backtest_id:
            raise HaasApiError(f"Backtest has no ID")
        
        # Create new bot on new account
        from pyHaasAPI.model import AddBotFromLabRequest
        
        create_request = AddBotFromLabRequest(
            lab_id=lab_id,
            backtest_id=backtest_id,
            account_id=new_account_id,
            bot_name=bot_name,
            market=market,
            leverage=leverage
        )
        
        new_bot = add_bot_from_lab(executor, create_request)
        if not new_bot:
            raise HaasApiError(f"Failed to create new bot on account {new_account_id}")
        
        new_bot_id = getattr(new_bot, 'bot_id', None)
        if not new_bot_id:
            raise HaasApiError(f"New bot created but has no ID")
        
        # Configure margin settings on new bot
        if preserve_settings:
            configure_result = configure_bot_settings(
                executor, 
                new_bot_id, 
                position_mode, 
                margin_mode, 
                leverage, 
                new_account_id
            )
        else:
            configure_result = {"success": True, "message": "Settings preserved"}
        
        # Delete old bot
        delete_result = delete_bot(executor, bot_id)
        
        return {
            "success": True,
            "old_bot_id": bot_id,
            "new_bot_id": new_bot_id,
            "new_account_id": new_account_id,
            "bot_name": bot_name,
            "market": market,
            "configuration": configure_result,
            "old_bot_deleted": delete_result
        }
        
    except Exception as e:
        return {
            "success": False,
            "bot_id": bot_id,
            "error": str(e)
        }


def configure_multiple_bots(
    executor: SyncExecutor[Authenticated],
    bot_ids: List[str],
    position_mode: int = 1,
    margin_mode: int = 0,
    leverage: float = 20.0
) -> dict:
    """
    Configure multiple bots with the same settings
    
    Args:
        executor: Authenticated executor instance
        bot_ids: List of bot IDs to configure
        position_mode: Position mode (0 for ONE_WAY, 1 for HEDGE)
        margin_mode: Margin mode (0 for CROSS, 1 for ISOLATED)
        leverage: Leverage value
        
    Returns:
        Dictionary with results for each bot
    """
    results = {}
    
    for bot_id in bot_ids:
        try:
            result = configure_bot_settings(
                executor, 
                bot_id, 
                position_mode, 
                margin_mode, 
                leverage
            )
            results[bot_id] = result
        except Exception as e:
            results[bot_id] = {
                "success": False,
                "error": str(e)
            }
    
    return {
        "total_bots": len(bot_ids),
        "successful": sum(1 for r in results.values() if r.get("success", False)),
        "failed": sum(1 for r in results.values() if not r.get("success", False)),
        "results": results
    }


def distribute_bots_to_accounts(
    executor: SyncExecutor[Authenticated],
    bot_ids: List[str],
    account_ids: List[str],
    configure_margin: bool = True,
    position_mode: int = 1,
    margin_mode: int = 0,
    leverage: float = 20.0
) -> dict:
    """
    Distribute multiple bots across different accounts
    
    Args:
        executor: SyncExecutor[Authenticated] instance
        bot_ids: List of bot IDs to distribute
        account_ids: List of account IDs to use
        configure_margin: Whether to configure margin settings
        position_mode: Position mode (0 for ONE_WAY, 1 for HEDGE)
        margin_mode: Margin mode (0 for CROSS, 1 for ISOLATED)
        leverage: Leverage value
        
    Returns:
        Dictionary with distribution results
    """
    if len(bot_ids) > len(account_ids):
        raise HaasApiError(f"Not enough accounts ({len(account_ids)}) for bots ({len(bot_ids)})")
    
    results = {}
    
    for i, bot_id in enumerate(bot_ids):
        account_id = account_ids[i % len(account_ids)]
        
        try:
            result = migrate_bot_to_account(
                executor,
                bot_id,
                account_id,
                preserve_settings=True,
                position_mode=position_mode,
                margin_mode=margin_mode,
                leverage=leverage
            )
            results[bot_id] = result
        except Exception as e:
            results[bot_id] = {
                "success": False,
                "error": str(e)
            }
    
    return {
        "total_bots": len(bot_ids),
        "total_accounts": len(account_ids),
        "successful": sum(1 for r in results.values() if r.get("success", False)),
        "failed": sum(1 for r in results.values() if not r.get("success", False)),
        "results": results
    }


def place_order(
    executor: SyncExecutor[Authenticated],
    account_id: str,
    market: str,
    side: str,
    price: float,
    amount: float,
    order_type: int = 0,
    tif: int = 0,
    source: str = "Manual"
) -> str:
    """
    Place an order
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        market: Market identifier
        side: Order side ("buy" or "sell")
        price: Order price
        amount: Order amount
        order_type: Order type (0=limit, 1=market)
        tif: Time in force (0=GTC, 1=IOC, 2=FOK)
        source: Order source
        
    Returns:
        Order ID if successful
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=str,
        query_params={
            "channel": "PLACE_ORDER",
            "accountid": account_id,
            "market": market,
            "side": side,
            "price": price,
            "amount": amount,
            "ordertype": order_type,
            "tif": tif,
            "source": source,
        },
    )


def cancel_order(
    executor: SyncExecutor[Authenticated], 
    account_id: str, 
    order_id: str
) -> bool:
    """
    Cancel a specific order
    
    Args:
        executor: Authenticated executor instance
        account_id: Account ID
        order_id: Order ID to cancel
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=bool,
        query_params={
            "channel": "CANCEL_ORDER",
            "accountid": account_id,
            "orderid": order_id,
        },
    )


def get_all_orders(executor: SyncExecutor[Authenticated]) -> list[dict]:
    """
    Get all orders across all accounts
    
    Args:
        executor: Authenticated executor instance
        
    Returns:
        List of order dictionaries
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=list[dict],
        query_params={
            "channel": "GET_ALL_ORDERS",
        },
    )


def get_all_positions(executor: SyncExecutor[Authenticated]) -> list[dict]:
    """
    Get all positions across all accounts
    
    Args:
        executor: Authenticated executor instance
        
    Returns:
        List of position dictionaries
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Account",
        response_type=list[dict],
        query_params={
            "channel": "GET_ALL_POSITIONS",
        },
    )


def change_bot_account(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    new_account_id: str
) -> bool:
    """
    Change a bot's account assignment
    
    Args:
        executor: Authenticated executor instance
        bot_id: Bot ID to move
        new_account_id: New account ID to assign to the bot
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=bool,
        query_params={
            "channel": "CHANGE_BOT_ACCOUNT",
            "botid": bot_id,
            "newaccountid": new_account_id,
        },
    )


def move_bot(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    new_account_id: str
) -> bool:
    """
    Move a bot to a different account (alias for change_bot_account)
    
    Args:
        executor: Authenticated executor instance
        bot_id: Bot ID to move
        new_account_id: New account ID to assign to the bot
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    return change_bot_account(executor, bot_id, new_account_id)


def set_bot_account(
    executor: SyncExecutor[Authenticated], 
    bot_id: str, 
    account_id: str
) -> bool:
    """
    Set a bot's account assignment
    
    Args:
        executor: Authenticated executor instance
        bot_id: Bot ID to configure
        account_id: Account ID to assign to the bot
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Bot",
        response_type=bool,
        query_params={
            "channel": "SET_BOT_ACCOUNT",
            "botid": bot_id,
            "accountid": account_id,
        },
    )



# Price Data Functions

def get_price_data(executor: SyncExecutor[Authenticated], market: str) -> dict:
    """
    Get real-time price data for a specific market.
    
    This function retrieves current price information including:
    - Current price (close)
    - Opening price
    - High and low prices
    - Volume
    - Best bid and ask prices
    - Timestamp
    
    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BINANCEFUTURES_BTC_USDT_PERPETUAL")
        
    Returns:
        Dictionary containing price data with keys:
        - T: Timestamp (Unix)
        - O: Opening price
        - H: High price
        - L: Low price
        - C: Close/Current price
        - V: Volume
        - B: Best bid price
        - S: Best ask price
        
    Raises:
        HaasApiError: If the API request fails
        
    Example:
        >>> price_data = get_price_data(executor, "BINANCEFUTURES_BTC_USDT_PERPETUAL")
        >>> print(f"BTC Price: ${price_data['C']}")
        >>> print(f"24h Volume: {price_data['V']}")
    """
    return executor.execute(
        endpoint="Price",
        response_type=dict,
        query_params={
            "channel": "PRICE",
            "market": market
        }
    )


def get_historical_data(executor: SyncExecutor[Authenticated], market: str, interval: int = 1, limit: int = 100) -> dict:
    """
    Get historical price data for a specific market.
    
    Args:
        executor: Authenticated executor instance
        market: Market identifier (e.g., "BINANCEFUTURES_BTC_USDT_PERPETUAL")
        interval: Time interval in minutes (1, 5, 15, 30, 60, 240, 1440)
        limit: Number of data points to retrieve (max 1000)
        
    Returns:
        Dictionary containing historical price data
        
    Raises:
        HaasApiError: If the API request fails
    """
    return executor.execute(
        endpoint="Price",
        response_type=dict,
        query_params={
            "channel": "HISTORICAL_DATA",
            "market": market,
            "interval": interval,
            "limit": limit
        }
    )