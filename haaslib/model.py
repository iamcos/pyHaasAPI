from enum import Enum
import dataclasses
from typing import Any, Dict, List, Optional, Generic, Literal, TypeVar, Type, Union
from typing_extensions import Self
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

from haaslib.domain import MarketTag, Script

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Base API response wrapper"""
    Success: bool
    Error: str
    Data: T

    @property
    def success(self) -> bool:
        """Lowercase accessor for Success field"""
        return self.Success

    @property
    def error(self) -> str:
        """Lowercase accessor for Error field"""
        return self.Error

    @property
    def data(self) -> T:
        """Lowercase accessor for Data field"""
        return self.Data


class UserDetails(BaseModel):
    user_id: str = Field(alias="UserId")
    interface_secret: str = Field(alias="UserId")
    license_details: Any = Field(alias="LicenseDetails")


class AppLogin(BaseModel):
    error: int = Field(alias="R")
    details: UserDetails = Field(alias="D")


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


class HaasScriptItemWithDependencies(BaseModel):
    dependencies: list[str] = Field(alias="D")
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


@dataclasses.dataclass
class CreateLabRequest:
    script_id: str
    name: str
    account_id: str
    market: MarketTag
    interval: int
    default_price_data_style: PriceDataStyle

    @classmethod
    def with_generated_name(
        cls: Type[Self],
        script_id: str,
        account_id: str,
        market: MarketTag,
        interval: int,
        default_price_data_style: PriceDataStyle,
    ) -> Self:
        name = f"{interval}_{market.tag}_{script_id}_{account_id}"
        return cls(
            script_id=script_id,
            account_id=account_id,
            market=market,
            interval=interval,
            default_price_data_style=default_price_data_style,
            name=name,
        )


class UserAccount(BaseModel):
    user_id: str = Field(alias="UID")
    account_id: str = Field(alias="AID")
    name: str = Field(alias="N")
    exchnage_code: str = Field(alias="EC")
    exchange_type: int = Field(alias="ET")
    status: int = Field(alias="S")
    is_simulated: bool = Field(alias="IS")
    is_test_net: bool = Field(alias="IT")
    is_public: bool = Field(alias="PA")
    is_white_label: bool = Field(alias="WL")
    position_mode: int = Field(alias="PM")
    margin_settings: Any = Field(alias="MS")
    version: int = Field(alias="V")


@dataclasses.dataclass
class UserLabConfig:
    """Configuration for lab updates - using dataclass to match reference exactly"""
    MaxPopulation: int = Field(alias="MP")
    MaxGenerations: int = Field(alias="MG")
    MaxElites: int = Field(alias="ME")
    MixRate: float = Field(alias="MR")
    AdjustRate: float = Field(alias="AR")

    def to_api_dict(self) -> dict:
        """Convert to API-compatible dictionary"""
        return {
            "MP": self.MaxPopulation,
            "MG": self.MaxGenerations,
            "ME": self.MaxElites,
            "MR": self.MixRate,
            "AR": self.AdjustRate
        }


class ScriptParameters(BaseModel):
    pass


class HaasScriptSettings(BaseModel):
    bot_id: Optional[str] = Field(alias="botId")
    bot_name: Optional[str] = Field(alias="botName")
    account_id: Optional[str] = Field(alias="accountId")
    market_tag: Optional[str] = Field(alias="marketTag")
    position_mode: int = Field(alias="positionMode")
    margin_mode: int = Field(alias="marginMode")
    leverage: float = Field(alias="leverage")
    trade_amount: float = Field(alias="tradeAmount")
    interval: int = Field(alias="interval")
    chart_style: int = Field(alias="chartStyle")
    order_template: int = Field(alias="orderTemplate")
    script_parameters: Optional[ScriptParameters] = Field(alias="scriptParameters")


UserLabParameterOption = str | int | float | bool


class UserLabParameter(BaseModel):
    key: str = Field(alias="K")
    input_field_type: int = Field(alias="T")
    options: list[UserLabParameterOption] = Field(alias="O")
    is_enabled: bool = Field(alias="I")
    is_specific: bool = Field(alias="IS")


class LabStatus(int, Enum):
    """Lab execution status"""
    CREATED = 0
    QUEUED = 1
    RUNNING = 2
    COMPLETED = 3
    CANCELLED = 4

    def __eq__(self, other):
        if isinstance(other, (LabStatus, int)):
            return self.value == other
        return False


class UserLabDetails(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=False,
        validate_assignment=True
    )
    user_lab_config: UserLabConfig = Field(alias="C")
    haas_script_settings: HaasScriptSettings = Field(alias="ST")
    parameters: list[UserLabParameter] = Field(alias="P")
    user_id: str = Field(alias="UID")
    lab_id: str = Field(alias="LID")
    script_id: str = Field(alias="SID")
    name: str = Field(alias="N")
    algorithm: int = Field(alias="T")
    status: LabStatus = Field(alias="S")  # Changed from int to LabStatus
    scheduled_backtests: int = Field(alias="SB")
    complete_backtests: int = Field(alias="CB")
    created_at: int = Field(alias="CA")
    updated_at: int = Field(alias="UA")
    started_at: int = Field(alias="SA")
    running_since: int = Field(alias="RS")
    start_unix: int = Field(alias="SU")
    end_unix: int = Field(alias="EU")
    send_email: bool = Field(alias="SE")
    cancel_reason: Any = Field(alias="CM")


class UserLabRecord(BaseModel):
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

    @property
    def is_running(self) -> bool:
        """Check if the lab is currently running"""
        return self.running_since > 0

class StartLabExecutionRequest(BaseModel):
    """Request model for starting lab execution"""
    lab_id: str
    start_unix: int = Field(alias="startunix")
    end_unix: int = Field(alias="endunix")
    send_email: bool = Field(alias="sendEmail", default=False)

    class Config:
        populate_by_name = True


class CloudMarket(BaseModel):
    category: str = Field(alias="C")
    price_source: str = Field(alias="PS")
    primary: str = Field(alias="P")
    secondary: str = Field(alias="S")

    def as_market_tag(self) -> MarketTag:
        return MarketTag(
            f"{self.price_source}_{self.primary}_{self.secondary}_{self.category}"
        )


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(alias="I")
    next_page_id: int = Field(alias="NP")


class CustomReportWrapper(BaseModel, Generic[T]):
    data: Optional[T] = Field(alias="Custom Report", default=None)


class UserLabsBacktestSummary(BaseModel, Generic[T]):
    orders: int = Field(alias="O")
    trades: int = Field(alias="T")
    positions: int = Field(alias="P")
    fee_costs: dict[str, float] = Field(alias="FC")
    realized_profits: dict[str, float] = Field(alias="RP")
    return_on_investment: list[float] = Field(alias="ROI")
    custom_report: CustomReportWrapper[T] = Field(alias="CR")


class UserLabBacktestResult(BaseModel):
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
    summary: UserLabsBacktestSummary = Field(alias="S")


class EditHaasScriptSourceCodeSettings(BaseModel):
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
    market: CloudMarket
    leverage: int = 0


class LabConfiguration(BaseModel):
    """Lab configuration settings"""
    max_positions: int = Field(alias="MP")
    max_global: int = Field(alias="MG")
    max_errors: int = Field(alias="ME")
    max_risk: float = Field(alias="MR", default=0.0)
    auto_restart: float = Field(alias="AR", default=0.0)

class LabSettings(BaseModel):
    """Lab settings model"""
    botId: str = ""
    botName: str = ""
    accountId: str
    marketTag: str
    positionMode: int = 0
    marginMode: int = 0
    leverage: float = 0.0
    tradeAmount: float = 100.0
    interval: int = 15
    chartStyle: int = 300
    orderTemplate: int = 500
    scriptParameters: Dict[str, Any] = {}

class ScriptParameter(BaseModel):
    """Script parameter definition"""
    key: str = Field(alias="K")
    type: int = Field(alias="T")
    options: list[str] = Field(alias="O")
    is_input: bool = Field(alias="I")
    is_secret: bool = Field(alias="IS")


class BacktestStatus(Enum):
    """Status of a lab backtest"""
    QUEUED = 0
    EXECUTING = 1
    CANCELLED = 2
    DONE = 3

class LabAlgorithm(Enum):
    """Lab optimization algorithm types"""
    BRUTE_FORCE = 0
    INTELLIGENT = 1
    RANDOM = 2
    CLUSTER = 3

# Then base models
class LabParameter(BaseModel):
    """Lab parameter configuration"""
    key: str = Field(alias="Key")
    type: str = Field(alias="Type")
    options: List[Any] = Field(alias="Options")
    is_enabled: bool = Field(alias="IsEnabled")
    is_specific: bool = Field(alias="IsSpecific")

class LabConfig(BaseModel):
    """Lab configuration - matches API response exactly"""
    MP: int  # MaxPopulation
    MG: int  # MaxGenerations
    ME: int  # MaxElites
    MR: float  # MixRate
    AR: float  # AdjustRate

    class Config:
        populate_by_name = True

class LabDetails(BaseModel):
    """Lab details response model"""
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        allow_population_by_field_name=True  # Allow both original and alias names
    )
    
    # Keep original field names but add aliases for API mapping
    config: LabConfig = Field(alias="C")
    settings: LabSettings = Field(alias="ST")
    parameters: List[Dict[str, Any]] = Field(alias="P")
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
    send_email: bool = Field(alias="SE", default=False)
    comment: Optional[str] = Field(alias="CM", default=None)


class LabExecutionUpdate(BaseModel):
    """Model for lab execution status updates"""
    status: LabStatus = Field(alias="S")
    progress: float = Field(alias="P")
    message: str | None = Field(alias="M", default=None)
    error: str | None = Field(alias="E", default=None)
    execution_time: int = Field(alias="T", default=0)

# First, define the summary model
class LabBacktestSummary(BaseModel):
    """Summary of lab backtest results"""
    Orders: Any = Field(default=None)
    Trades: Any = Field(default=None)
    Positions: Any = Field(default=None)
    FeeCosts: float = Field(default=0.0)
    RealizedProfits: float = Field(default=0.0)
    ReturnOnInvestment: float = Field(default=0.0)
    CustomReport: Any = Field(default=None)

# Then use it in the result model
class LabBacktestResult(BaseModel):
    """Lab backtest execution result"""
    record_id: str = Field(alias="RecordId")
    user_id: str = Field(alias="UserId")
    lab_id: str = Field(alias="LabId")
    backtest_id: str = Field(alias="BacktestId")
    no_generation: int = Field(alias="NoGeneration")
    no_population: int = Field(alias="NoPopulation")
    status: BacktestStatus = Field(alias="Status")
    settings: Any = Field(alias="Settings")
    parameters: Any = Field(alias="Parameters")
    runtime: Any = Field(alias="Runtime")
    chart: Any = Field(alias="Chart")
    logs: List[Any] = Field(alias="Logs")
    summary: LabBacktestSummary = Field(alias="Summary")
    service_id: str = Field(alias="ServiceId")
    is_elite: bool = Field(alias="IsElite")

class ParameterType(Enum):
    """Types of parameters supported by HaasScript"""
    INTEGER = 0
    DECIMAL = 1
    BOOLEAN = 2
    STRING = 3
    SELECTION = 4  # For list-based selections

class ParameterRange:
    """Represents a range or list of values for a parameter"""
    def __init__(
        self,
        start: Union[int, float, None] = None,
        end: Union[int, float, None] = None,
        step: Union[int, float, None] = None,
        decimals: int = 0,
        selection_values: List[Union[str, int, float, bool]] = None
    ):
        self.start = start
        self.end = end
        self.step = step
        self.decimals = decimals
        self.selection_values = selection_values or []
        
    def generate_values(self) -> List[Union[int, float, str, bool]]:
        """Generate all possible values for this parameter"""
        if self.selection_values:
            return self.selection_values
            
        if None in (self.start, self.end, self.step):
            return []
            
        values = []
        current = self.start
        while current <= self.end:
            if self.decimals > 0:
                values.append(round(current, self.decimals))
            else:
                values.append(int(current))
            current += self.step
        return values

class LabParameter:
    """Represents a lab parameter with its configuration"""
    def __init__(
        self,
        name: str,
        param_type: ParameterType,
        current_value: Union[int, float, bool, str],
        range_config: Optional[ParameterRange] = None,
        is_enabled: bool = True,
        is_specific: bool = False,
        description: str = ""
    ):
        self.name = name
        self.param_type = param_type
        self.current_value = current_value
        self.range_config = range_config
        self.is_enabled = is_enabled
        self.is_specific = is_specific
        self.description = description
        
    @property
    def possible_values(self) -> List[Union[int, float, bool, str]]:
        """Get all possible values for this parameter"""
        if self.param_type == ParameterType.BOOLEAN:
            return [True, False]
        elif self.range_config:
            return self.range_config.generate_values()
        return [self.current_value]  # Return current value if no range defined

class UserLabSettings(BaseModel):
    """Settings for lab updates"""
    bot_id: str = Field(alias="BotId", default="")
    bot_name: str = Field(alias="BotName", default="")
    account_id: str = Field(alias="AccountId", default="")
    market_tag: str = Field(alias="MarketTag", default="")
    position_mode: int = Field(alias="PositionMode", default=0)
    margin_mode: int = Field(alias="MarginMode", default=0)
    leverage: float = Field(alias="Leverage", default=0.0)
    trade_amount: float = Field(alias="TradeAmount", default=100.0)
    interval: int = Field(alias="Interval", default=15)
    chart_style: int = Field(alias="ChartStyle", default=300)
    order_template: int = Field(alias="OrderTemplate", default=500)
    script_parameters: Dict[str, Any] = Field(alias="ScriptParameters", default_factory=dict)

class LabConfigurationState(BaseModel):
    """Represents the "C" field in lab details"""
    MP: int
    MG: int
    ME: int
    MR: float
    AR: float

class LabSettingsState(BaseModel):
    """Represents the "ST" field in lab details"""
    bot_id: str = Field(alias="botId", default="")
    bot_name: str = Field(alias="botName", default="")
    account_id: str = Field(alias="accountId", default="")
    market_tag: str = Field(alias="marketTag", default="")
    position_mode: int = Field(alias="positionMode", default=0)
    margin_mode: int = Field(alias="marginMode", default=0)
    leverage: float = Field(alias="leverage", default=0.0)
    trade_amount: float = Field(alias="tradeAmount", default=100.0)
    interval: int = Field(alias="interval", default=15)
    chart_style: int = Field(alias="chartStyle", default=300)
    order_template: int = Field(alias="orderTemplate", default=500)
    script_parameters: Dict[str, Any] = Field(alias="scriptParameters", default_factory=dict)


