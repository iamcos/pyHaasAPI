from enum import Enum
import dataclasses
from typing import (Any, Dict, List, Optional, Generic, Literal, TypeVar, Type, Union, TYPE_CHECKING)
from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal

from pyHaasAPI.domain import Script
from pyHaasAPI.parameters import (
    LabParameter,
    LabStatus,
    LabConfig,
    LabSettings,
    BacktestStatus,
    LabAlgorithm, 
    ScriptParameters,
    ParameterRange,
    ParameterType
)
from pyHaasAPI.models.scripts import ScriptRecord


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Base API response wrapper"""
    Success: bool = Field(default=True)
    Error: str = Field(default="")
    Data: Optional[T] = Field(default=None)

    model_config = ConfigDict(
        populate_by_name=True,
        extra='allow',
        arbitrary_types_allowed=True
    )

    @property
    def success(self) -> bool:
        """Lowercase accessor for Success field"""
        return self.Success

    @property
    def error(self) -> str:
        """Lowercase accessor for Error field"""
        return self.Error

    @property
    def data(self) -> Optional[T]:
        """Lowercase accessor for Data field"""
        return self.Data


class UserDetails(BaseModel):
    user_id: str = Field(alias="UserId")
    interface_secret: str = Field(alias="UserId")
    license_details: Any = Field(alias="LicenseDetails")


class AppLogin(BaseModel):
    error: int = Field(alias="R")
    details: UserDetails = Field(alias="D")


class HaasScriptSettings(BaseModel):
    """Script settings model"""
    model_config = ConfigDict(populate_by_name=True)
    
    bot_id: Optional[str] = Field(alias="botId", default="")
    bot_name: Optional[str] = Field(alias="botName", default="")
    account_id: Optional[str] = Field(alias="accountId", default="")
    market_tag: Optional[str] = Field(alias="marketTag", default="")
    position_mode: int = Field(alias="positionMode", default=0)
    margin_mode: int = Field(alias="marginMode", default=0)
    leverage: float = Field(alias="leverage", default=0.0)
    trade_amount: float = Field(alias="tradeAmount", default=100.0)
    interval: int = Field(alias="interval", default=15)
    chart_style: int = Field(alias="chartStyle", default=300)
    order_template: int = Field(alias="orderTemplate", default=500)
    script_parameters: Optional[Dict[str, Any]] = Field(alias="scriptParameters", default_factory=dict)
    
    @field_validator('bot_id', 'bot_name', 'account_id', 'market_tag', mode='before')
    @classmethod
    def handle_null_strings(cls, v):
        """Convert null to empty string for string fields"""
        return "" if v is None else v
    
    @field_validator('script_parameters', mode='before')
    @classmethod
    def handle_null_dict(cls, v):
        """Convert null to empty dict for script_parameters"""
        return {} if v is None else v


class HaasBot(BaseModel):
    user_id: str = Field(alias="UI")
    bot_id: str = Field(alias="ID")
    bot_name: str = Field(alias="BN")
    script_id: str = Field(alias="SI")
    script_version: int = Field(alias="SV")
    account_id: str = Field(alias="AI")
    market: str = Field(alias="PM")
    execution_id: str = Field(alias="EI")
    is_activated: bool = Field(alias="IA")
    is_paused: bool = Field(alias="IP")
    is_favorite: bool = Field(alias="IF")
    notes: str = Field(alias="NO")
    script_note: str = Field(alias="SN")
    notes_timestamp: int = Field(alias="NT")
    realized_profit: float = Field(alias="RP")
    urealized_profit: float = Field(alias="UP")
    return_on_investment: float = Field(alias="ROI")
    trade_amount_error: bool = Field(alias="TAE")
    account_error: bool = Field(alias="AE")
    script_error: bool = Field(alias="SE")
    update_counter: int = Field(alias="UC")
    chart_interval: int = Field(alias="CI")
    chart_style: int = Field(alias="CS")
    chart_volume: bool = Field(alias="CV")
    is_white_label: bool = Field(alias="IWL")
    master_bot_id: str = Field(alias="MBID")
    followers: int = Field(alias="F")
    settings: HaasScriptSettings = Field(alias="ST", default_factory=HaasScriptSettings)


class HaasScriptItemWithDependencies(BaseModel):
    dependencies: list[str] = Field(alias="D", default_factory=list)
    user_id: str = Field(alias="UID")
    script_id: str = Field(alias="SID")
    script_name: str = Field(alias="SN")
    script_description: str = Field(alias="SD")
    script_type: int = Field(alias="ST")
    script_status: int = Field(alias="SS")
    command_name: str = Field(alias="CN")
    is_command: bool = Field(alias="IC")
    is_valid: bool = Field(alias="IV")
    created_unix: int = Field(alias="CU")
    updated_unix: int = Field(alias="UU")
    folder_id: int = Field(alias="FID")

    @property
    def id(self) -> str:
        return self.script_id

    @property
    def type(self) -> int:
        return self.script_type


PriceDataStyle = Literal[
    "CandleStick",
    "CandleStickHLC",
    "HeikinAshi",
    "OHLC",
    "HLC",
    "CloseLine",
    "Line",
    "Mountain",
]

from enum import IntEnum
from typing import Literal, Optional, List, Dict, Any, Type, Self
from pydantic import BaseModel, Field, ConfigDict, field_validator
import dataclasses

class PositionMode(IntEnum):
    """Position mode enumeration"""
    ONE_WAY = 0
    HEDGE = 1

class MarginMode(IntEnum):
    """Margin mode enumeration"""
    CROSS = 0
    ISOLATED = 1

class ContractType(IntEnum):
    """Contract type enumeration"""
    SPOT = 0
    PERPETUAL = 1
    QUARTERLY = 2
    MONTHLY = 3

class CloudMarket(BaseModel):
    category: str = Field(alias="C")
    price_source: str = Field(alias="PS")
    primary: str = Field(alias="P")
    secondary: str = Field(alias="S")
    contract_type: Optional[str] = Field(alias="CT", default=None)  # PERPETUAL, QUARTERLY, etc.

    def format_market_tag(self, exchange_code: str, contract_type: Optional[str] = None) -> str:
        """
        Format market tag with optional contract type
        
        Args:
            exchange_code: Exchange code (e.g., "BINANCE")
            contract_type: Contract type (e.g., "PERPETUAL", "QUARTERLY")
            
        Returns:
            Formatted market tag (e.g., "BINANCEQUARTERLY_BTC_USD_PERPETUAL")
        """
        base_tag = f"{exchange_code.upper()}_{self.primary.upper()}_{self.secondary.upper()}"
        
        if contract_type:
            return f"{base_tag}_{contract_type.upper()}"
        elif self.contract_type:
            return f"{base_tag}_{self.contract_type.upper()}"
        else:
            return f"{base_tag}_"

    def format_futures_market_tag(self, exchange_code: str, contract_type: str = "PERPETUAL") -> str:
        """
        Format futures market tag specifically for BINANCEQUARTERLY style exchanges
        
        Args:
            exchange_code: Exchange code (e.g., "BINANCEQUARTERLY")
            contract_type: Contract type (e.g., "PERPETUAL", "QUARTERLY")
            
        Returns:
            Formatted futures market tag (e.g., "BINANCEQUARTERLY_BTC_USD_PERPETUAL")
        """
        return f"{exchange_code.upper()}_{self.primary.upper()}_{self.secondary.upper()}_{contract_type.upper()}"


@dataclasses.dataclass
class CreateLabRequest:
    script_id: str
    name: str
    account_id: str
    market: str
    interval: int
    default_price_data_style: PriceDataStyle
    trade_amount: float = 100.0
    chart_style: int = 300
    order_template: int = 500
    leverage: float = 0.0
    position_mode: int = 0
    margin_mode: int = 0

    @classmethod
    def with_generated_name(
        cls: Type[Self],
        script_id: str,
        account_id: str,
        market: CloudMarket,
        exchange_code: str,
        interval: int,
        default_price_data_style: PriceDataStyle,
        contract_type: Optional[str] = None,
    ) -> Self:
        name = f"{interval}_{market.primary}_{market.secondary}_{script_id}_{account_id}"
        
        # Format market tag string with contract type support
        market_tag = market.format_market_tag(exchange_code, contract_type)
        
        return cls(
            script_id=script_id,
            account_id=account_id,
            market=market_tag,
            interval=interval,
            default_price_data_style=default_price_data_style,
            name=name,
        )

    @classmethod
    def with_futures_market(
        cls: Type[Self],
        script_id: str,
        account_id: str,
        market: CloudMarket,
        exchange_code: str,
        interval: int,
        default_price_data_style: PriceDataStyle,
        contract_type: str = "PERPETUAL",
    ) -> Self:
        """
        Create lab request specifically for futures markets (BINANCEQUARTERLY style)
        
        Args:
            script_id: Script ID
            account_id: Account ID
            market: CloudMarket object
            exchange_code: Exchange code (e.g., "BINANCEQUARTERLY")
            interval: Chart interval
            default_price_data_style: Price data style
            contract_type: Contract type ("PERPETUAL" or "QUARTERLY")
        """
        name = f"{interval}_{market.primary}_{market.secondary}_{contract_type}_{script_id}_{account_id}"
        
        # Format futures market tag
        market_tag = market.format_futures_market_tag(exchange_code, contract_type)
        
        return cls(
            script_id=script_id,
            account_id=account_id,
            market=market_tag,
            interval=interval,
            default_price_data_style=default_price_data_style,
            name=name,
        )


class UserAccount(BaseModel):
    user_id: str = Field(alias="UID")
    account_id: str = Field(alias="AID")
    name: str = Field(alias="N")
    exchange_code: str = Field(alias="EC")
    exchange_type: int = Field(alias="ET")
    status: int = Field(alias="S")
    is_simulated: bool = Field(alias="IS")
    is_test_net: bool = Field(alias="IT")
    is_public: bool = Field(alias="PA")
    is_white_label: bool = Field(alias="WL")
    position_mode: int = Field(alias="PM")
    margin_settings: Any = Field(alias="MS")
    version: int = Field(alias="V")


class LabRecord(BaseModel):
    """Model representing a lab record"""
    user_id: str = Field(alias="UID")
    lab_id: str = Field(alias="LID")
    script_id: str = Field(alias="SID")
    name: str = Field(alias="N")
    scheduled_backtests: int = Field(alias="SB")
    completed_backtests: int = Field(alias="CB")
    created_at: int = Field(alias="CA")
    updated_at: int = Field(alias="UA")
    started_at: int = Field(alias="SA")
    running_since: int = Field(alias="RS")
    start_unix: int = Field(alias="SU")
    end_unix: int = Field(alias="EU")
    send_email: bool = Field(alias="SE")
    cancel_reason: str | None = Field(alias="CM", default=None)
    status: LabStatus = Field(alias="S")
    
    class Config:
        populate_by_name = True
        
    @property
    def is_running(self) -> bool:
        """Check if the lab is currently running"""
        return self.status in [LabStatus.QUEUED, LabStatus.RUNNING]

class StartLabExecutionRequest(BaseModel):
    """Request model for starting lab execution"""
    lab_id: str
    start_unix: int = Field(alias="startunix")
    end_unix: int = Field(alias="endunix")
    send_email: bool = Field(alias="sendEmail", default=False)

    class Config:
        populate_by_name = True


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(alias="I")
    next_page_id: int = Field(alias="NP")


class CustomReportWrapper(BaseModel, Generic[T]):
    data: Optional[T] = Field(alias="Custom Report", default=None)

class LabBacktestSummary(BaseModel):
    """Summary of lab backtest results"""
    Orders: Any = Field(default=None)
    Trades: Any = Field(default=None)
    Positions: Any = Field(default=None)
    FeeCosts: float = Field(default=0.0)
    RealizedProfits: float = Field(default=0.0)
    ReturnOnInvestment: float = Field(default=0.0)
    CustomReport: Any = Field(default=None)

BacktestSummary = LabBacktestSummary

class LabBacktestResult(BaseModel):
    record_id: int = Field(alias="RID")
    user_id: str = Field(alias="UID")
    lab_id: str = Field(alias="LID")
    backtest_id: str = Field(alias="BID")
    generation_idx: int = Field(alias="NG")
    population_idx: int = Field(alias="NP")
    status: int = Field(alias="ST")
    settings: HaasScriptSettings = Field(alias="SE")
    parameters: dict[str, str] = Field(alias="P")
    runtime: Any = Field(alias="RT")
    chart: Any = Field(alias="C")
    logs: Any = Field(alias="L")
    summary: LabBacktestSummary = Field(alias="S")


class EditHaasScriptSourceCodeSettings(BaseModel):
    """Settings for editing HaasScript source code"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # Allow arbitrary types
        populate_by_name=True
    )
    
    market_tag: CloudMarket
    leverage: float
    position_mode: int
    trade_amount: float
    order_template: int
    chart_style: int
    interval: int
    script_parameters: ScriptParameters
    bot_name: str
    bot_id: str


class CustomReport:
    pass


class GetBacktestResultRequest(BaseModel):
    """Request parameters for getting backtest results"""
    lab_id: str = Field(description="Lab identifier")
    next_page_id: int = Field(description="Page number for pagination")
    page_lenght: int = Field(
        description="Number of results per page",
        default=100  # Providing a default value
    )


class LicenseDetails(BaseModel):
    generated: int = Field(alias="Generated")
    license_name: str = Field(alias="LicenseName")
    valid_until: int = Field(alias="ValidUntill")
    rights: int = Field(alias="Rights")
    enterprise: bool = Field(alias="Enterprise")
    allowed_exchanges: list = Field(alias="AllowedExchanges")
    max_bots: int = Field(alias="MaxBots")
    max_simulated_accounts: int = Field(alias="MaxSimulatedAccounts")
    max_real_accounts: int = Field(alias="MaxRealAccounts")
    max_dashboards: int = Field(alias="MaxDashboards")
    max_backtest_months: int = Field(alias="MaxBacktestMonths")
    max_labs_months: int = Field(alias="MaxLabsMonths")
    max_open_orders: int = Field(alias="MaxOpenOrders")
    rented_signals: dict[str, Any] = Field(alias="RentedSignals")
    rented_strategies: dict[str, Any] = Field(alias="RentedStrategies")
    hire_signals_enabled: bool = Field(alias="HireSignalsEnabled")
    hire_strategies_enabled: bool = Field(alias="HireStrategiesEnabled")
    haas_labs_enabled: bool = Field(alias="HaasLabsEnabled")
    resell_signals_enabled: bool = Field(alias="ResellSignalsEnabled")
    market_details_enabled: bool = Field(alias="MarketDetailsEnabled")
    local_api_enabled: bool = Field(alias="LocalAPIEnabled")
    scripted_exchanges_enabled: bool = Field(alias="ScriptedExchangesEnabled")
    machine_learning_enabled: bool = Field(alias="MachinelearningEnabled")


class AuthenticatedSessionResponseData(BaseModel):
    user_id: str = Field(alias="UserId")
    username: Any = Field(alias="Username")
    interface_secret: str = Field(alias="InterfaceSecret")
    user_rights: int = Field(alias="UserRights")
    is_affiliate: bool = Field(alias="IsAffiliate")
    is_product_seller: bool = Field(alias="IsProductSeller")
    license_details: LicenseDetails = Field(alias="LicenseDetails")
    support_hash: Any = Field(alias="SupportHash")


class AuthenticatedSessionResponse(BaseModel):
    data: AuthenticatedSessionResponseData = Field(alias="D")


@dataclasses.dataclass
class CreateBotRequest:
    bot_name: str
    script: Script | HaasScriptItemWithDependencies
    account_id: str
    market: CloudMarket
    leverage: int = dataclasses.field(default=0)
    interval: int = dataclasses.field(default=15)
    chartstyle: int = dataclasses.field(default=301)


class EnumDecimalType(BaseModel):
    # Define the fields for EnumDecimalType here
    pass


class CloudTradeContract(BaseModel):
    # Define the fields for CloudTradeContract here
    pass


class CloudTradeMarket(BaseModel):
    normalized_primary: str = Field(alias="NormalizedPrimary")
    normalized_secondary: str = Field(alias="NormalizedSecondary")
    normalized_margin_currency: str = Field(alias="NormalizedMarginCurrency")
    exchange_symbol: str = Field(alias="ES")
    web_socket_symbol: str = Field(alias="WS")
    exchange_value: int = Field(alias="EV")
    price_step: float = Field(alias="PSP")
    price_decimals: int = Field(alias="PD")
    amount_step: float = Field(alias="ASP")
    amount_decimals: int = Field(alias="AD")
    price_decimal_type: EnumDecimalType = Field(alias="PDT")
    amount_decimal_type: EnumDecimalType = Field(alias="ADT")
    makers_fee: float = Field(alias="MF")
    takers_fee: float = Field(alias="TF")
    minimum_trade_amount: float = Field(alias="MTA")
    minimum_trade_volume: float = Field(alias="MTV")
    maximum_trade_amount: float = Field(alias="MXTA")
    maximum_trade_volume: float = Field(alias="MXTV")
    is_open: bool = Field(alias="IO")
    is_margin: bool = Field(alias="IM")
    contract_details: CloudTradeContract = Field(alias="CD")
    margin_currency: str = Field(alias="MarginCurrency")
    amount_label: str = Field(alias="AmountLabel")
    profit_label: str = Field(alias="ProfitLabel")
    price_source: str = Field(alias="PS")
    primary: str = Field(alias="P")
    secondary: str = Field(alias="S")
    contract_name: str = Field(alias="C")
    short_name: str = Field(alias="ShortName")
    wallet_tag: str = Field(alias="WalletTag")


@dataclasses.dataclass
class AddBotFromLabRequest:
    lab_id: str
    backtest_id: str
    bot_name: str
    account_id: str
    market: str  # Changed from CloudMarket to str
    leverage: int = 0


class LabDetails(BaseModel):
    """Lab details from GET_LAB_DETAILS"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra='allow'  # Allow extra fields
    )
    
    parameters: List[Dict[str, Any]] = Field(alias="P", default_factory=list)
    config: LabConfig = Field(alias="C")
    settings: HaasScriptSettings = Field(alias="ST")
    user_id: str = Field(alias="UID")
    lab_id: str = Field(alias="LID")
    script_id: str = Field(alias="SID")
    name: str = Field(alias="N")
    type: int = Field(alias="T")
    status: LabStatus = Field(alias="S")
    scheduled_backtests: int = Field(alias="SB")
    completed_backtests: int = Field(alias="CB")
    created_at: int = Field(alias="CA")
    updated_at: int = Field(alias="UA")
    started_at: int = Field(alias="SA")
    running_since: int = Field(alias="RS")
    start_unix: int = Field(alias="SU")
    end_unix: int = Field(alias="EU")
    send_email: bool = Field(alias="SE")
    cancel_message: Optional[str] = Field(alias="CM", default=None)

    @property
    def is_running(self) -> bool:
        """Check if lab is currently running"""
        return self.status in [LabStatus.QUEUED, LabStatus.RUNNING]


class LabExecutionUpdate(BaseModel):
    """Model for lab execution status updates"""
    status: LabStatus = Field(alias="S")
    progress: float = Field(alias="P")
    message: str | None = Field(alias="M", default=None)
    error: str | None = Field(alias="E", default=None)
    execution_time: int = Field(alias="T", default=0)

# First, define the summary model


# Then use it in the result model

class AccountDetails(BaseModel):
    account_id: str
    exchange: str
    account_type: str
    # ... other fields as needed ...

class AccountData(BaseModel):
    """Account data including exchange information"""
    account_id: str
    exchange: str
    type: str
    wallets: List[dict]  # We can define a proper Wallet model if needed
    # Add other fields as needed based on the API response


class BacktestRecord(BaseModel):
    """Model representing a backtest record"""
    record_id: int = Field(alias="RID")
    user_id: str = Field(alias="UID")
    lab_id: str = Field(alias="LID")
    backtest_id: str = Field(alias="BID")
    generation_idx: int = Field(alias="NG")
    population_idx: int = Field(alias="NP")
    status: int = Field(alias="ST")
    settings: HaasScriptSettings = Field(alias="SE")
    parameters: dict[str, str] = Field(alias="P")
    runtime: Any = Field(alias="RT")
    chart: Any = Field(alias="C")
    logs: Any = Field(alias="L")
    summary: LabBacktestSummary = Field(alias="S")


class HaasScriptFolder(BaseModel):
    folder_id: int = Field(alias="FID")
    name: str = Field(alias="FN")
    parent_id: int = Field(alias="PID")
    created_unix: int = Field(alias="CU")
    updated_unix: int = Field(alias="UU")


class AddSimulatedAccountRequest(BaseModel):
    name: str = Field(alias="name")
    driver_code: str = Field(alias="drivercode")
    driver_type: int = Field(alias="drivertype", default=2) # 2 for simulated


# --- NEW MODELS FOR RUNTIME DATA --- #

class InputFieldDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    T: int = Field(description="Parameter Type (matches ParameterType enum)")
    ST: int = Field(description="Sub-Type")
    G: str = Field(description="Group name for the parameter")
    K: str = Field(description="Full parameter key")
    EK: str = Field(description="Extended Key - numerical prefix of the key")
    N: str = Field(description="Human-readable Name of the parameter")
    TT: str = Field(description="Tooltip or description for the parameter")
    V: Any = Field(description="The actual value used for this parameter")
    D: Any = Field(description="Default value for the parameter")
    O: Optional[Dict[str, str]] = Field(None, description="Options for SELECTION types")
    MIN: float = Field(description="Minimum value for numerical parameters")
    MAX: float = Field(description="Maximum value for numerical parameters")

class OrderInPosition(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    id: str
    eid: str
    ot: int # Open Time
    ct: int # Close Time
    to: int # Trade Order
    d: int  # Direction
    t: int  # Type
    p: float # Price
    tp: float # Take Profit
    ep: float # Entry Price
    a: float # Amount
    af: float # Amount Filled
    fe: float # Fee
    fc: str # Fee Currency
    m: float # Margin
    pr: float # Profit/Loss
    r: float # Rate
    cr: int # Custom Report
    n: str # Note

class PositionDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    pg: str # Position Group ID
    g: str  # Group ID
    ac: str # Account ID
    ma: str # Market Tag
    le: float # Leverage
    d: int # Direction
    mt: int # Market Type
    pl: str # Profit/Loss Currency
    al: str # Asset Label
    pd: int # Price Decimals
    ad: int # Amount Decimals
    ot: int # Open Time
    ct: int # Close Time
    ic: bool # Is Closed
    ap: float # Average Price
    t: float # Trade Amount
    av: float # Average Volume
    io: float # Initial Order
    eno: List[OrderInPosition] = Field(default_factory=list) # Entry Orders
    exo: List[OrderInPosition] = Field(default_factory=list) # Exit Orders
    cp: float # Current Profit
    fe: float # Fee
    rp: float # Realized Profit
    up: float # Unrealized Profit
    roi: float # ROI
    hpip: float # Highest Price in Position
    lpip: float # Lowest Price in Position

class ReportDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    AID: str
    M: str
    AL: str
    ML: str
    PL: str
    F: Dict[str, Any] # Fee details
    PR: Dict[str, Any] # Profit/Return details
    O: Dict[str, Any] # Order details
    P: Dict[str, Any] # Position details
    T: Dict[str, Any] # Trade statistics

class ChartDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    Guid: str
    Interval: int
    Charts: Dict[str, Any]
    Colors: Dict[str, str]
    IsLastPartition: bool
    Status: int

class BacktestRuntimeData(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='allow')
    Chart: ChartDetails
    CompilerErrors: List[Any]
    Reports: Dict[str, ReportDetails]
    CustomReport: Dict[str, Any]
    ScriptNote: str
    TrackedOrderLimit: int
    OpenOrders: List[Any]
    FailedOrders: List[Any]
    ManagedLongPosition: PositionDetail
    ManagedShortPosition: PositionDetail
    UnmanagedPositions: List[PositionDetail]
    FinishedPositions: List[PositionDetail]
    InputFields: Dict[str, InputFieldDetail]
    ScriptMemory: Dict[str, Any]
    LocalMemory: Dict[str, Any]
    RedisKeys: List[Any]
    Files: Dict[str, Any]
    LogId: str
    LogCount: int
    ExecutionLog: List[str]
    UserId: str
    BotId: str
    BotName: str
    ScriptId: str
    ScriptName: str
    Activated: bool
    Paused: bool
    IsWhiteLabel: bool
    ActivatedSince: int
    DeactivatedSince: int
    DeactivatedReason: str
    AccountId: str
    PriceMarket: str
    Leverage: float
    MarginMode: int
    PositionMode: int
    TradeAmount: float
    OrderTemplate: int
    DefaultInterval: int
    DefaultChartType: int
    HideTradeAmountSettings: bool
    HideOrderSettings: bool
    OrderPersistenceEnabled: bool
    OrderPersistenceLimit: int
    EnableHighSpeedUpdates: bool
    UpdateAfterCompletedOrder: bool
    IndicatorContainerLogs: bool
    IsScriptOk: bool
    TradeAmountError: bool
    ScriptTradeAmountError: bool
    UpdateCounter: int
    IsSpotSupported: bool
    IsMarginSupported: bool
    IsLeverageSupported: bool
    IsManagedTrading: bool
    IsOneDirection: bool
    IsMultiMarket: bool
    IsRemoteSignalBased: bool
    IsWebHookBased: bool
    WebHookSignalId: str
    IsTAUsed: bool
    Timestamp: int
    MinuteTimestamp: int
    LastUpdateTimestamp: int

class BotRuntimeData(BacktestRuntimeData):
    """Bot runtime data has a very similar structure to backtest runtime data"""
    pass