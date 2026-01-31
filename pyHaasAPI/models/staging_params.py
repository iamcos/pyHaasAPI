"""
Staging Optional Parameter shapes auto-generated from all .def.lua files.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .common import BaseModel

@dataclass
class APOParams(BaseModel):
    ma_type: str = ""

@dataclass
class AbsolutePriceChangeParams(BaseModel):
    amount: float = 0.0
    target_price: float = 0.0
    position_id: str = ""

@dataclass
class AddParams(BaseModel):
    input2: float = 0.0

@dataclass
class AdjustTimestampParams(BaseModel):
    unix: float = 0.0
    add_seconds: float = 0.0
    add_minutes: float = 0.0
    add_hours: float = 0.0
    add_days: float = 0.0
    add_months: float = 0.0
    add_years: float = 0.0

@dataclass
class AdjustVPositionParams(BaseModel):
    position_id: str = ""

@dataclass
class AmountCurrencyParams(BaseModel):
    market: str = ""

@dataclass
class AmountDecimalsParams(BaseModel):
    market: str = ""
    amount: float = 0.0

@dataclass
class AmountLabelParams(BaseModel):
    market: str = ""

@dataclass
class AmountStepParams(BaseModel):
    market: str = ""

@dataclass
class AquaParams(BaseModel):
    opacity: float = 0.0

@dataclass
class ArrayAnyParams(BaseModel):
    value: float = 0.0

@dataclass
class ArrayContainsParams(BaseModel):
    value: float = 0.0

@dataclass
class ArrayFilterParams(BaseModel):
    filter_type: str = ""

@dataclass
class ArrayFindParams(BaseModel):
    filter_type: str = ""

@dataclass
class ArrayLastParams(BaseModel):
    offset: float = 0.0

@dataclass
class ArraySortParams(BaseModel):
    descend_valueing: bool = False

@dataclass
class ArraySumParams(BaseModel):
    key: str = ""

@dataclass
class AskPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class AverageParams(BaseModel):
    input2: float = 0.0

@dataclass
class Average2Params(BaseModel):
    period: float = 0.0

@dataclass
class AverageCandleSizeParams(BaseModel):
    market: str = ""

@dataclass
class AverageEnterPriceParams(BaseModel):
    position_id: str = ""
    include_closed: bool = False

@dataclass
class AverageExitPriceParams(BaseModel):
    position_id: str = ""

@dataclass
class AverageOrderbookSpreadParams(BaseModel):
    market: str = ""

@dataclass
class BBANDSParams(BaseModel):
    ma_type: str = ""

@dataclass
class BalanceParams(BaseModel):
    account_id: str = ""
    coin: str = ""
    market: str = ""

@dataclass
class BalanceAmountParams(BaseModel):
    account_id: str = ""
    coin: str = ""
    market: str = ""

@dataclass
class BaseCurrencyParams(BaseModel):
    market: str = ""

@dataclass
class BidPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class BlackParams(BaseModel):
    opacity: float = 0.0

@dataclass
class BlueParams(BaseModel):
    opacity: float = 0.0

@dataclass
class BoolToSignalParams(BaseModel):
    is_long: bool = False
    is_short: bool = False
    is_exit: bool = False
    is_none: bool = False

@dataclass
class BuyPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class CC_BBandsStopLossParams(BaseModel):
    ma_period: float = 0.0
    dev_mult: float = 0.0
    ma_type: str = ""
    position_id: str = ""

@dataclass
class CC_CVOLB_LBParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_CryptoIndexSlotParams(BaseModel):
    stop_loss: float = 0.0
    trailing_stop: float = 0.0
    take_over_wallet: bool = False

@dataclass
class CC_EMAMA_LBParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_EasyAdaptiveRSIParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_EasyForceIndexParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_EasyHullMAParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_EasyMVOParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class CC_EasyMassIndexParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_EasySTCParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_EasySmoothRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class CC_EasyTDParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_EasyTSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class CC_EasyTrendMAParams(BaseModel):
    ma_type: str = ""

@dataclass
class CC_EasyVolumeRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class CC_HullMAParams(BaseModel):
    source: List[float] = field(default_factory=list)

@dataclass
class CC_MVOParams(BaseModel):
    high: List[float] = field(default_factory=list)
    low: List[float] = field(default_factory=list)
    close: List[float] = field(default_factory=list)
    volume: List[float] = field(default_factory=list)
    fast_period: float = 0.0
    fast_ma_type: float = 0.0
    slow_period: float = 0.0
    slow_ma_type: float = 0.0
    stoch_fast_k: float = 0.0
    stoch_slow_k: float = 0.0
    stoch_slow_d: float = 0.0

@dataclass
class CC_MadHatterBBandsParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class CC_MadHatterMACDParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class CC_MadHatterRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class CC_MarketMakingSlotParams(BaseModel):
    stop_loss_percentage: float = 0.0
    stop_loss_cool_down: float = 0.0
    reset: bool = False
    note: str = ""

@dataclass
class CC_PRO_LBParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_ProfitTrailerParams(BaseModel):
    trail_mode: str = ""
    max_rebounds: float = 0.0
    position_id: str = ""

@dataclass
class CC_SQZMOM_LBParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_ScalperChannel_LBParams(BaseModel):
    interval: float = 0.0

@dataclass
class CC_WRPCParams(BaseModel):
    interval: float = 0.0

@dataclass
class CDLParams(BaseModel):
    penetration: float = 0.0

@dataclass
class CancelAllOrdersParams(BaseModel):
    position_id: str = ""

@dataclass
class ChandelierExitLongParams(BaseModel):
    depth: float = 0.0
    multiplier: float = 0.0

@dataclass
class ChandelierExitShortParams(BaseModel):
    depth: float = 0.0
    multiplier: float = 0.0

@dataclass
class ChartAddAxisLabelParams(BaseModel):
    color: str = ""
    text_color: str = ""

@dataclass
class ChartSetAxisOptionsParams(BaseModel):
    low: float = 0.0
    high: float = 0.0
    visible: bool = False
    type: str = ""

@dataclass
class ChartSetOptionsParams(BaseModel):
    title: str = ""
    height: float = 0.0
    style: str = ""

@dataclass
class ClosePricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class CloseVPositionParams(BaseModel):
    position_id: str = ""

@dataclass
class ColorParams(BaseModel):
    a: float = 0.0

@dataclass
class ContractNameParams(BaseModel):
    market: str = ""

@dataclass
class ContractValueParams(BaseModel):
    market: str = ""

@dataclass
class CountParams(BaseModel):
    value: float = 0.0

@dataclass
class CreateMarketParams(BaseModel):
    price_source: str = ""
    base_currency: str = ""
    quote_currency: str = ""
    contract_name: str = ""

@dataclass
class CreatePositionParams(BaseModel):
    market: str = ""
    leverage: float = 0.0
    position_id: str = ""

@dataclass
class CreateTimestampParams(BaseModel):
    year: float = 0.0
    month: float = 0.0
    day: float = 0.0
    hour: float = 0.0
    minute: float = 0.0
    second: float = 0.0

@dataclass
class CurrentDateParams(BaseModel):
    unix: float = 0.0

@dataclass
class CurrentDayParams(BaseModel):
    unix: float = 0.0

@dataclass
class CurrentHourParams(BaseModel):
    unix: float = 0.0

@dataclass
class CurrentMinuteParams(BaseModel):
    unix: float = 0.0

@dataclass
class CurrentMonthParams(BaseModel):
    unix: float = 0.0

@dataclass
class CurrentPriceParams(BaseModel):
    market: str = ""

@dataclass
class CurrentSecondParams(BaseModel):
    unix: float = 0.0

@dataclass
class CurrentWeekParams(BaseModel):
    unix: float = 0.0

@dataclass
class CurrentYearParams(BaseModel):
    unix: float = 0.0

@dataclass
class CustomReportParams(BaseModel):
    group: str = ""
    display_value: bool = False

@dataclass
class CyanParams(BaseModel):
    opacity: float = 0.0

@dataclass
class DarkGrayParams(BaseModel):
    opacity: float = 0.0

@dataclass
class DarkGreenParams(BaseModel):
    opacity: float = 0.0

@dataclass
class DeactivateAfterEnterOrderParams(BaseModel):
    position_count: float = 0.0

@dataclass
class DeactivateAfterExitOrderParams(BaseModel):
    position_count: float = 0.0

@dataclass
class DeactivateAfterXOrdersParams(BaseModel):
    count: float = 0.0

@dataclass
class DeactivateAfterXPositionsParams(BaseModel):
    count: float = 0.0

@dataclass
class DeactivateBotParams(BaseModel):
    reason: str = ""
    cancel_open_orders: bool = False

@dataclass
class DefineEasyIndicatorParametersParams(BaseModel):
    chart_index: float = 0.0

@dataclass
class DefineOutputParams(BaseModel):
    value: float = 0.0
    description: str = ""
    output_suggestions: str = ""

@dataclass
class DefineOutputIndexParams(BaseModel):
    output_suggestions: str = ""

@dataclass
class DefineParameterParams(BaseModel):
    input_suggestions: str = ""

@dataclass
class DeltaParams(BaseModel):
    input2: float = 0.0

@dataclass
class DoBuyParams(BaseModel):
    note: str = ""
    count: float = 0.0

@dataclass
class DoExitPositionParams(BaseModel):
    note: str = ""
    count: float = 0.0

@dataclass
class DoFlipPositionParams(BaseModel):
    note: str = ""

@dataclass
class DoLongParams(BaseModel):
    note: str = ""
    count: float = 0.0

@dataclass
class DoSellParams(BaseModel):
    note: str = ""
    count: float = 0.0

@dataclass
class DoShortParams(BaseModel):
    note: str = ""
    count: float = 0.0

@dataclass
class DoSignalParams(BaseModel):
    note: str = ""

@dataclass
class DynamicStopLossParams(BaseModel):
    depth: float = 0.0
    position_id: str = ""
    direction: str = ""

@dataclass
class DynamicTakeProfitParams(BaseModel):
    depth: float = 0.0
    position_id: str = ""
    direction: str = ""

@dataclass
class EasyABANDSParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyADOSCParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyAOParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyAPOParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyAROONParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyAROONOSCParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyAliceParams(BaseModel):
    interval: float = 0.0

@dataclass
class EasyBBANDSParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyBBANDSBParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyBBANDSWParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyBOPParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyCCIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyCDLParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyCMOParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyCOPPOCKParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyCRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyDMIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyDONCHIANParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyDPOParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyDXParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyDynamicLongShortLevelsParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyFIBONACCIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyFastRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyFixedLongShortLevelsParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyICHIMOKUParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyIMIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyKELTNERParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyKRIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyKSTParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyLINEARREGParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyMAParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyMACDParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyMFIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyMOMParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyOBVParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyPPOParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyROCParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasySARParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasySSTOCHParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasySTOCHParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasySTOCHFParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasySTOCHRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasySlowRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyTRIXParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyTSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyUDRSIParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyULTOSCParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyWILLRParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EasyZLMAParams(BaseModel):
    name: str = ""
    interval: float = 0.0

@dataclass
class EnableHighSpeedUpdatesParams(BaseModel):
    update_on_filled_orders: bool = False

@dataclass
class FeeParams(BaseModel):
    market: str = ""

@dataclass
class FinalizeParams(BaseModel):
    callback: float = 0.0

@dataclass
class FormatDateTimeParams(BaseModel):
    unix: float = 0.0
    date_delimiter: str = ""
    date_time_delimiter: str = ""
    time_delimiter: str = ""
    include_seconds: bool = False
    include_time: bool = False
    include_year: bool = False

@dataclass
class FuchsiaParams(BaseModel):
    opacity: float = 0.0

@dataclass
class GetAccountMarketsParams(BaseModel):
    account_id: str = ""

@dataclass
class GetAllFilledOrdersParams(BaseModel):
    position_id: str = ""

@dataclass
class GetAllOpenOrdersParams(BaseModel):
    position_id: str = ""

@dataclass
class GetBodyHighPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class GetBodyLowPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class GetBotProfitParams(BaseModel):
    market: str = ""
    include_unrealized: bool = False

@dataclass
class GetBotROIParams(BaseModel):
    market: str = ""

@dataclass
class GetCurrentProfitParams(BaseModel):
    direction: str = ""
    market: str = ""

@dataclass
class GetCurrentROIParams(BaseModel):
    direction: str = ""
    market: str = ""

@dataclass
class GetHighParams(BaseModel):
    offset: float = 0.0

@dataclass
class GetLastTradesParams(BaseModel):
    depth: float = 0.0
    market: str = ""

@dataclass
class GetLeverageParams(BaseModel):
    market: str = ""
    account_id: str = ""

@dataclass
class GetLowParams(BaseModel):
    offset: float = 0.0

@dataclass
class GetMarginModeParams(BaseModel):
    market: str = ""
    account_id: str = ""

@dataclass
class GetMaxLeverageParams(BaseModel):
    market: str = ""

@dataclass
class GetOrderFilledAmountParams(BaseModel):
    after_fees: bool = False

@dataclass
class GetOrderOpenTimeParams(BaseModel):
    in_seconds: bool = False

@dataclass
class GetOrderbookParams(BaseModel):
    market: str = ""

@dataclass
class GetOrderbookAskParams(BaseModel):
    market: str = ""

@dataclass
class GetOrderbookBidParams(BaseModel):
    market: str = ""

@dataclass
class GetPositionAmountParams(BaseModel):
    position_id: str = ""

@dataclass
class GetPositionDirectionParams(BaseModel):
    position_id: str = ""

@dataclass
class GetPositionEnterPriceParams(BaseModel):
    position_id: str = ""
    include_closed: bool = False

@dataclass
class GetPositionMarketParams(BaseModel):
    position_id: str = ""

@dataclass
class GetPositionModeParams(BaseModel):
    account_id: str = ""
    market: str = ""

@dataclass
class GetPositionProfitParams(BaseModel):
    position_id: str = ""
    target_price: float = 0.0

@dataclass
class GetPositionROIParams(BaseModel):
    position_id: str = ""
    target_price: float = 0.0

@dataclass
class GetSuperSignalParams(BaseModel):
    center_position: float = 0.0
    buy_level: float = 0.0
    sell_level: float = 0.0

@dataclass
class GetThresholdSignalParams(BaseModel):
    swing: float = 0.0

@dataclass
class GetTimerParams(BaseModel):
    key: str = ""

@dataclass
class GetTradingReportParams(BaseModel):
    market: str = ""

@dataclass
class GetVolumeParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class GoldParams(BaseModel):
    opacity: float = 0.0

@dataclass
class GrabParams(BaseModel):
    count: float = 0.0

@dataclass
class GrayParams(BaseModel):
    opacity: float = 0.0

@dataclass
class GreenParams(BaseModel):
    opacity: float = 0.0

@dataclass
class GrowingTrailingStopLossParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class HLCPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class HLPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class HNCParams(BaseModel):
    size: float = 0.0
    value: float = 0.0

@dataclass
class HeikenClosePricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class HeikinOpenPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""

@dataclass
class HighPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class IndicatorContainerParams(BaseModel):
    signals: List[float] = field(default_factory=list)

@dataclass
class InputParams(BaseModel):
    default_value: float = 0.0
    tooltip: str = ""
    group: str = ""

@dataclass
class InputAccountParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputAccountMarketParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputButtonParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputCdlTypesParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputConstantParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputIntervalParams(BaseModel):
    default_value: float = 0.0
    tooltip: str = ""
    group: str = ""

@dataclass
class InputLrTypesParams(BaseModel):
    default_value: str = ""
    tooltip: str = ""
    group: str = ""

@dataclass
class InputMaTypesParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputMarketParams(BaseModel):
    default_value: str = ""
    tooltip: str = ""
    group: str = ""

@dataclass
class InputOptionsParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputOrderTypeParams(BaseModel):
    default_value: str = ""
    tooltip: str = ""
    group: str = ""

@dataclass
class InputPriceSourceParams(BaseModel):
    default_value: str = ""
    tooltip: str = ""
    group: str = ""

@dataclass
class InputPriceSourceMarketParams(BaseModel):
    default_value: str = ""
    type: str = ""
    tooltip: str = ""
    group: str = ""

@dataclass
class InputSignalManagementParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputSignalTypesParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputSourcePriceParams(BaseModel):
    tooltip: str = ""
    group: str = ""

@dataclass
class InputTableOptionsParams(BaseModel):
    title: str = ""
    rows: float = 0.0
    max_rows: float = 0.0
    group: str = ""

@dataclass
class InsuranceContainerParams(BaseModel):
    signals: List[float] = field(default_factory=list)

@dataclass
class IsAnyOrderFinishedParams(BaseModel):
    position_id: str = ""

@dataclass
class IsAnyOrderOpenParams(BaseModel):
    position_id: str = ""

@dataclass
class IsMarginModeSupportedParams(BaseModel):
    account_id: str = ""

@dataclass
class IsPositionClosedParams(BaseModel):
    position_id: str = ""

@dataclass
class IsPositionModeSupportedParams(BaseModel):
    account_id: str = ""

@dataclass
class IsTradeAmountEnoughParams(BaseModel):
    log_warning: bool = False

@dataclass
class KAMAParams(BaseModel):
    fastest: float = 0.0
    slowest: float = 0.0

@dataclass
class KAMA2Params(BaseModel):
    fastest: float = 0.0
    slowest: float = 0.0

@dataclass
class KELTNERParams(BaseModel):
    atr_period: float = 0.0
    multiplier: float = 0.0

@dataclass
class LINEARREGParams(BaseModel):
    type: str = ""

@dataclass
class LastBuyTradesCommandParams(BaseModel):
    seconds_back: float = 0.0
    market: str = ""

@dataclass
class LastLongProfitParams(BaseModel):
    position_id: str = ""

@dataclass
class LastSellTradesCommandParams(BaseModel):
    seconds_back: float = 0.0
    market: str = ""

@dataclass
class LastShortProfitParams(BaseModel):
    position_id: str = ""

@dataclass
class LastTradesSentimentParams(BaseModel):
    market: str = ""

@dataclass
class LineOptionsParams(BaseModel):
    color: str = ""
    style: str = ""
    deco: str = ""
    width: float = 0.0
    offset: float = 0.0
    side: str = ""
    id: str = ""
    behind: bool = False
    ignore_on_axis: bool = False
    draw_trailing_line: bool = False

@dataclass
class LnParams(BaseModel):
    input2: float = 0.0

@dataclass
class LoadParams(BaseModel):
    default_value: float = 0.0

@dataclass
class LogParams(BaseModel):
    color: str = ""

@dataclass
class LongAmountParams(BaseModel):
    market: str = ""

@dataclass
class LowPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class MAVPParams(BaseModel):
    ma_type: str = ""

@dataclass
class MakersFeeParams(BaseModel):
    market: str = ""

@dataclass
class MarginToTradeAmountParams(BaseModel):
    market: str = ""

@dataclass
class MarkCandleParams(BaseModel):
    depth: float = 0.0

@dataclass
class MarketTypeParams(BaseModel):
    market: str = ""

@dataclass
class MaroonParams(BaseModel):
    opacity: float = 0.0

@dataclass
class MaxExitLongAmountParams(BaseModel):
    market: str = ""

@dataclass
class MaxExitShortAmountParams(BaseModel):
    market: str = ""

@dataclass
class MaxLongAmountParams(BaseModel):
    market: str = ""

@dataclass
class MaxShortAmountParams(BaseModel):
    market: str = ""

@dataclass
class MinimumTradeAmountParams(BaseModel):
    market: str = ""
    price: float = 0.0

@dataclass
class NeverEnterWithALossParams(BaseModel):
    accepted_loss: float = 0.0
    target_price: float = 0.0

@dataclass
class NeverExitWithLossParams(BaseModel):
    accepted_loss: float = 0.0
    target_price: float = 0.0
    position_id: str = ""

@dataclass
class OCPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class OHLCPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class OliveParams(BaseModel):
    opacity: float = 0.0

@dataclass
class OpenPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class OrangeParams(BaseModel):
    opacity: float = 0.0

@dataclass
class OrderOncePerBarParams(BaseModel):
    interval: float = 0.0
    position_id: str = ""

@dataclass
class OrderbookSentimentParams(BaseModel):
    market: str = ""

@dataclass
class OvercomeDoubleFeeCostsParams(BaseModel):
    target_price: float = 0.0
    position_id: str = ""

@dataclass
class OvercomeFeeCostsParams(BaseModel):
    target_price: float = 0.0
    position_id: str = ""

@dataclass
class ParseCsvParams(BaseModel):
    has_headers: bool = False
    column_delimiter: str = ""
    row_delimiter: str = ""

@dataclass
class PercentageChangeParams(BaseModel):
    input2: float = 0.0

@dataclass
class PercentagePriceChangeParams(BaseModel):
    percentage: float = 0.0
    target_price: float = 0.0
    position_id: str = ""

@dataclass
class PlaceBuyOrderParams(BaseModel):
    market: str = ""
    type: str = ""
    note: str = ""
    position_id: str = ""
    timeout: float = 0.0
    trigger_price: float = 0.0
    reduce_only: bool = False
    hidden_order: bool = False

@dataclass
class PlaceCancelledOrderParams(BaseModel):
    price: float = 0.0

@dataclass
class PlaceExitLongOrderParams(BaseModel):
    market: str = ""
    type: str = ""
    note: str = ""
    position_id: str = ""
    timeout: float = 0.0
    trigger_price: float = 0.0
    reduce_only: bool = False
    hidden_order: bool = False

@dataclass
class PlaceExitPositionOrderParams(BaseModel):
    position_id: str = ""
    price: float = 0.0
    type: str = ""
    note: str = ""
    timeout: float = 0.0

@dataclass
class PlaceExitShortOrderParams(BaseModel):
    market: str = ""
    type: str = ""
    note: str = ""
    position_id: str = ""
    timeout: float = 0.0
    trigger_price: float = 0.0
    reduce_only: bool = False
    hidden_order: bool = False

@dataclass
class PlaceGoLongOrderParams(BaseModel):
    market: str = ""
    type: str = ""
    note: str = ""
    position_id: str = ""
    timeout: float = 0.0
    trigger_price: float = 0.0
    reduce_only: bool = False
    hidden_order: bool = False

@dataclass
class PlaceGoShortOrderParams(BaseModel):
    market: str = ""
    type: str = ""
    note: str = ""
    position_id: str = ""
    timeout: float = 0.0
    trigger_price: float = 0.0
    reduce_only: bool = False
    hidden_order: bool = False

@dataclass
class PlaceSellOrderParams(BaseModel):
    market: str = ""
    type: str = ""
    note: str = ""
    position_id: str = ""
    timeout: float = 0.0
    trigger_price: float = 0.0
    reduce_only: bool = False
    hidden_order: bool = False

@dataclass
class PlotParams(BaseModel):
    color_or_options: float = 0.0

@dataclass
class PlotBBandsChartParams(BaseModel):
    lower: float = 0.0

@dataclass
class PlotBarsParams(BaseModel):
    base_value: float = 0.0
    fill_color: str = ""

@dataclass
class PlotCircleParams(BaseModel):
    fill_color: str = ""

@dataclass
class PlotDoubleColorParams(BaseModel):
    fill_color: str = ""

@dataclass
class PlotHistogramParams(BaseModel):
    fill_raising_bars: bool = False

@dataclass
class PlotHistogramSignalsParams(BaseModel):
    short_signal: float = 0.0
    long_signal: float = 0.0

@dataclass
class PlotHorizontalLineParams(BaseModel):
    line_decoration: str = ""
    side: str = ""
    id: str = ""

@dataclass
class PlotHorizontalZoneParams(BaseModel):
    side: str = ""

@dataclass
class PlotPriceParams(BaseModel):
    interval: float = 0.0
    style: str = ""
    up_color: str = ""
    up_fill: bool = False
    down_color: str = ""
    down_fill: bool = False
    mark_color: str = ""
    mark_fill: bool = False

@dataclass
class PlotShapeParams(BaseModel):
    chart_id: float = 0.0
    shape: str = ""
    color: str = ""
    size: float = 0.0
    above_candle: bool = False
    text: str = ""
    text_color: str = ""
    offset: float = 0.0

@dataclass
class PlotShapesParams(BaseModel):
    fill_color: str = ""

@dataclass
class PlotVerticalLineParams(BaseModel):
    line_decoration: str = ""

@dataclass
class PlotVolumeParams(BaseModel):
    up_color: str = ""
    down_color: str = ""
    up_fill: bool = False
    down_fill: bool = False
    side: str = ""

@dataclass
class PositionContainerParams(BaseModel):
    position_id: str = ""
    include_closed: bool = False

@dataclass
class PriceDecimalsParams(BaseModel):
    market: str = ""
    price: float = 0.0

@dataclass
class PriceStepParams(BaseModel):
    market: str = ""

@dataclass
class PricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class ProfitCurrencyParams(BaseModel):
    market: str = ""

@dataclass
class ProfitLabelParams(BaseModel):
    market: str = ""

@dataclass
class PurpleParams(BaseModel):
    opacity: float = 0.0

@dataclass
class QuoteCurrencyParams(BaseModel):
    market: str = ""

@dataclass
class QuoteDecimalsParams(BaseModel):
    market: str = ""
    price: float = 0.0

@dataclass
class QuoteStepParams(BaseModel):
    market: str = ""

@dataclass
class RandomParams(BaseModel):
    min: float = 0.0
    max: float = 0.0

@dataclass
class RangeParams(BaseModel):
    count: float = 0.0

@dataclass
class RedParams(BaseModel):
    opacity: float = 0.0

@dataclass
class SafetyContainerParams(BaseModel):
    signals: List[float] = field(default_factory=list)

@dataclass
class SellPricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class SetBotRoiBaseValueParams(BaseModel):
    market: str = ""

@dataclass
class SetFeeParams(BaseModel):
    market: str = ""

@dataclass
class SetLeverageParams(BaseModel):
    market: str = ""
    account_id: str = ""

@dataclass
class SetMarginModeParams(BaseModel):
    market: str = ""
    account_id: str = ""

@dataclass
class SetPositionModeParams(BaseModel):
    account_id: str = ""
    market: str = ""

@dataclass
class ShortAmountParams(BaseModel):
    market: str = ""

@dataclass
class ShrinkingTrailingStopLossParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class SignalMapperParams(BaseModel):
    reverse: bool = False
    map_long_to: str = ""
    map_short_to: str = ""
    map_exit_to: str = ""
    map_none_to: str = ""

@dataclass
class SignalPropertiesParams(BaseModel):
    use_long: bool = False
    use_short: bool = False
    use_exit: bool = False
    weight: float = 0.0
    delay: float = 0.0

@dataclass
class SkyBlueParams(BaseModel):
    opacity: float = 0.0

@dataclass
class SourceManagerParams(BaseModel):
    interval: float = 0.0
    cap: float = 0.0
    initial_values: List[float] = field(default_factory=list)

@dataclass
class SourcePricesParams(BaseModel):
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""
    hlc_style: bool = False

@dataclass
class StartTimerParams(BaseModel):
    key: str = ""

@dataclass
class StopLossParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class StopLossCooldownParams(BaseModel):
    position_id: str = ""

@dataclass
class StopLossROIParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class StopTimerParams(BaseModel):
    key: str = ""

@dataclass
class StringContainsParams(BaseModel):
    ignore_case: bool = False

@dataclass
class StringIndexOfParams(BaseModel):
    ignore_case: bool = False

@dataclass
class StringJoinParams(BaseModel):
    separator: str = ""

@dataclass
class SumParams(BaseModel):
    input2: float = 0.0

@dataclass
class TakeProfitParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class TakeProfitROIParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class TakersFeeParams(BaseModel):
    market: str = ""

@dataclass
class TealParams(BaseModel):
    opacity: float = 0.0

@dataclass
class TradeBotContainerParams(BaseModel):
    safety_signal: bool = False
    indicator_signal: str = ""
    insurance_signal: bool = False

@dataclass
class TradeMarketContainerParams(BaseModel):
    market: str = ""

@dataclass
class TradeOncePerBarParams(BaseModel):
    interval: float = 0.0
    position_id: str = ""

@dataclass
class TradeOnlySidewaysParams(BaseModel):
    threshold: float = 0.0
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""

@dataclass
class TradeOnlyTrendingParams(BaseModel):
    threshold: float = 0.0
    interval: float = 0.0
    full_candles: bool = False
    market: str = ""

@dataclass
class TrailingArmStopLossParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class TrailingStopLossParams(BaseModel):
    position_id: str = ""
    direction: str = ""

@dataclass
class UnderlyingAssetParams(BaseModel):
    market: str = ""

@dataclass
class UserPositionContainerParams(BaseModel):
    account_id: str = ""
    market: str = ""
    leverage: float = 0.0
    direction: str = ""

@dataclass
class WaitAfterOrderParams(BaseModel):
    position_id: str = ""

@dataclass
class WaitAfterTradeParams(BaseModel):
    position_id: str = ""

@dataclass
class WalletAmountParams(BaseModel):
    account_id: str = ""
    coin: str = ""
    market: str = ""

@dataclass
class WhiteParams(BaseModel):
    opacity: float = 0.0

@dataclass
class YellowParams(BaseModel):
    opacity: float = 0.0

@dataclass
class ZLMAParams(BaseModel):
    ma_type: str = ""
    ma_period1: float = 0.0
    ma_period2: float = 0.0
