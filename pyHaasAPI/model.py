from enum import Enum
import dataclasses
from typing import Any, Dict, List, Optional, Generic, Literal, TypeVar, Type, Union
from typing_extensions import Self
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

from pyHaasAPI.domain import Script
from pyHaasAPI.parameters import (
    LabParameter,
    LabStatus,
    LabConfig,
    LabSettings,
    BacktestStatus,
    LabAlgorithm, 
    ScriptParameters
    
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

class CloudMarket(BaseModel):
    category: str = Field(alias="C")
    price_source: str = Field(alias="PS")
    primary: str = Field(alias="P")
    secondary: str = Field(alias="S")

    def format_market_tag(self, exchange_code: str) -> str:
        return f"{exchange_code}_{self.primary}_{self.secondary}_"


@dataclasses.dataclass
class CreateLabRequest:
    script_id: str
    name: str
    account_id: str
    market: str
    interval: int
    default_price_data_style: PriceDataStyle

    @classmethod
    def with_generated_name(
        cls: Type[Self],
        script_id: str,
        account_id: str,
        market: CloudMarket,
        exchange_code: str,
        interval: int,
        default_price_data_style: PriceDataStyle,
    ) -> Self:
        name = f"{interval}_{market.primary}_{market.secondary}_{script_id}_{account_id}"
        
        # Format market tag string
        market_tag = f"{exchange_code.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
        
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




class HaasScriptSettings(BaseModel):
    """Script settings model"""
    model_config = ConfigDict(populate_by_name=True)
    
    bot_id: str = Field(alias="botId")
    bot_name: str = Field(alias="botName")
    account_id: str = Field(alias="accountId")
    market_tag: str = Field(alias="marketTag")
    position_mode: int = Field(alias="positionMode")
    margin_mode: int = Field(alias="marginMode")
    leverage: float = Field(alias="leverage")
    trade_amount: float = Field(alias="tradeAmount")
    interval: int = Field(alias="interval")
    chart_style: int = Field(alias="chartStyle")
    order_template: int = Field(alias="orderTemplate")
    script_parameters: dict = Field(alias="scriptParameters")







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
        return self.running_since > 0

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
    market: CloudMarket
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
    settings: LabSettings = Field(alias="ST")
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
    cancel_message: Optional[str] = Field(alias="CM")

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

