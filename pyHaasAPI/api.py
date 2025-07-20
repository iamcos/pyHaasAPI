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
        
        # Determine if we need to use POST method
        use_post = False
        if query_params and query_params.get("channel") == "START_LAB_EXECUTION":
            use_post = True
            log.debug("Using POST method for START_LAB_EXECUTION")
        
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

        # Use POST for START_LAB_EXECUTION, GET for everything else
        if use_post:
            # Convert query params to form data for POST
            form_data = {}
            for k, v in query_params.items():
                if isinstance(v, (str, int, float, bool, type(None))):
                    form_data[k] = str(v) if not isinstance(v, str) else v
                else:
                    form_data[k] = json.dumps(v, default=self._custom_encoder(by_alias=True))
            
            resp = requests.post(url, data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        else:
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
) -> LabDetails:
    """
    Start lab execution with specified parameters.
    
    ⚠️ IMPORTANT: This function uses POST method with form-encoded data as required by the API.
    
    🔧 **NEW FEATURE**: Automatic config parameter validation and correction.
    When `ensure_config=True` (default), this function will automatically ensure
    the lab has proper config parameters before starting the backtest.
    
    Args:
        executor: Authenticated executor instance
        request: StartLabExecutionRequest object with lab_id, start_unix, end_unix, and send_email
        ensure_config: If True, automatically ensure proper config parameters before execution
        config: Optional LabConfig to apply if ensure_config=True. If None, uses default intelligent mode config
        
    Returns:
        LabDetails object containing the updated lab configuration with execution status
        
    Raises:
        HaasApiError: If the API request fails
        
    Example:
        >>> # Start backtest with automatic config validation (recommended)
        >>> start_unix = 1744009200  # April 7th 2025 13:00 UTC
        >>> end_unix = 1752994800    # End time
        >>> request = StartLabExecutionRequest(
        ...     lab_id="lab_id",
        ...     start_unix=start_unix,
        ...     end_unix=end_unix,
        ...     send_email=False
        ... )
        >>> result = api.start_lab_execution(executor, request)  # ensure_config=True by default
        >>> print(f"Lab status: {result.status}")
        
        >>> # Start backtest without config validation (advanced users only)
        >>> result = api.start_lab_execution(executor, request, ensure_config=False)
        
        >>> # Start backtest with custom config
        >>> custom_config = LabConfig(max_population=20, max_generations=200, max_elites=5, mix_rate=50.0, adjust_rate=30.0)
        >>> result = api.start_lab_execution(executor, request, config=custom_config)
    """
    # Ensure proper config parameters if requested
    if ensure_config:
        log.info(f"🔧 Ensuring proper config parameters for lab {request.lab_id} before backtest execution")
        ensure_lab_config_parameters(executor, request.lab_id, config)
    
    # Use POST method with form-encoded data as shown in Chrome inspector
    return executor.execute(
        endpoint="Labs",
        response_type=LabDetails,
        query_params={
            "channel": "START_LAB_EXECUTION",
            "labid": request.lab_id,  # Changed from labId to labid
            "startunix": request.start_unix,
            "endunix": request.end_unix,
            "sendemail": request.send_email  # Changed from sendEmail to sendemail
        }
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
        >>> # Clone a lab with all settings preserved
        >>> original_lab = api.get_lab_details(executor, "original_lab_id")
        >>> cloned_lab = api.clone_lab(executor, "original_lab_id", "My_Cloned_Lab")
        >>> print(f"Cloned: {cloned_lab.name} with {len(cloned_lab.parameters)} parameters")
        
    See Also:
        - docs/LAB_CLONING_DISCOVERY.md for detailed explanation
        - examples/lab_cloner.py for production-ready implementation
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
        response_type=dict,
        query_params={
            "channel": "GET_ALL_ORDERS",
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )
    return response.get("Data", [])


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
    return executor.execute(
        endpoint="Bot",
        response_type=dict,
        query_params={
            "channel": "GET_RUNTIME",
            "botid": bot_id,
            "interfacekey": getattr(executor.state, 'interface_key', None),
            "userid": getattr(executor.state, 'user_id', None),
        },
    )


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
            import time
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

