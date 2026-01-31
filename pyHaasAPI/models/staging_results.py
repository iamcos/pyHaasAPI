"""
Staging Result models auto-generated from all .def.lua files.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .common import BaseModel

@dataclass
class ABANDSResult(BaseModel):
    upper: List[float] = field(default_factory=list)
    middle: List[float] = field(default_factory=list)
    lower: List[float] = field(default_factory=list)

@dataclass
class AROONResult(BaseModel):
    aroon_dn: List[float] = field(default_factory=list)
    aroon_up: List[float] = field(default_factory=list)

@dataclass
class BBANDSResult(BaseModel):
    upper: List[float] = field(default_factory=list)
    middle: List[float] = field(default_factory=list)
    lower: List[float] = field(default_factory=list)

@dataclass
class BalanceResult(BaseModel):
    available: float = 0.0
    locked: float = 0.0
    total: float = 0.0
    number: float = 0.0

@dataclass
class CompareResult(BaseModel):
    is_above: bool = False
    is_equal: bool = False
    is_below: bool = False
    boolean: float = 0.0

@dataclass
class CurrentPriceResult(BaseModel):
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    ask: float = 0.0
    bid: float = 0.0
    number: float = 0.0

@dataclass
class DONCHIANResult(BaseModel):
    upper: List[float] = field(default_factory=list)
    middle: List[float] = field(default_factory=list)
    lower: List[float] = field(default_factory=list)

@dataclass
class DefineEasyIndicatorParametersResult(BaseModel):
    chart_index: float = 0.0
    interval: float = 0.0
    number: float = 0.0

@dataclass
class FastRSIResult(BaseModel):
    rsi: List[float] = field(default_factory=list)
    fast_rsi: List[float] = field(default_factory=list)

@dataclass
class GetOrderbookResult(BaseModel):
    ask_prices: List[float] = field(default_factory=list)
    ask_amounts: List[float] = field(default_factory=list)
    bid_prices: List[float] = field(default_factory=list)
    bid_amounts: List[float] = field(default_factory=list)

@dataclass
class GetTradingReportResult(BaseModel):
    max_draw_down_prc: float = 0.0
    max_draw_down: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    win_percentage: float = 0.0
    profit_ratio: float = 0.0
    profit_factor: float = 0.0
    cpc_index: float = 0.0
    tail_ratio: float = 0.0
    common_sense_ratio: float = 0.0
    outlier_win_ratio: float = 0.0
    outlier_loss_ratio: float = 0.0
    profit_margin_ratio: float = 0.0
    biggest_win: float = 0.0
    biggest_loss: float = 0.0
    highest_point_in_profit: float = 0.0
    lowest_point_in_profit: float = 0.0
    total_margin_used: float = 0.0
    average_margin: float = 0.0
    average_profit: float = 0.0
    closed_positions: float = 0.0
    profitable_positions: float = 0.0
    losing_positions: float = 0.0
    executed_orders: float = 0.0
    completed_orders: float = 0.0
    number: float = 0.0

@dataclass
class HT_PHASORResult(BaseModel):
    in_phase_out: List[float] = field(default_factory=list)
    quadrature_out: List[float] = field(default_factory=list)

@dataclass
class HT_SINEResult(BaseModel):
    sine: List[float] = field(default_factory=list)
    lead_sine: List[float] = field(default_factory=list)

@dataclass
class ICHIMOKUResult(BaseModel):
    conversion: List[float] = field(default_factory=list)
    base: List[float] = field(default_factory=list)
    span_a: List[float] = field(default_factory=list)
    span_b: List[float] = field(default_factory=list)

@dataclass
class IndicatorContainerResult(BaseModel):
    unanimous_signal: str = ""
    consensus_signal: str = ""
    enum: float = 0.0

@dataclass
class KELTNERResult(BaseModel):
    upper: List[float] = field(default_factory=list)
    middle: List[float] = field(default_factory=list)
    lower: List[float] = field(default_factory=list)

@dataclass
class KSTResult(BaseModel):
    kst: List[float] = field(default_factory=list)
    signal: List[float] = field(default_factory=list)

@dataclass
class MACDResult(BaseModel):
    macd: List[float] = field(default_factory=list)
    signal: List[float] = field(default_factory=list)
    hist: List[float] = field(default_factory=list)

@dataclass
class MACDEXTResult(BaseModel):
    macd: List[float] = field(default_factory=list)
    signal: List[float] = field(default_factory=list)
    hist: List[float] = field(default_factory=list)

@dataclass
class MACDFIXResult(BaseModel):
    macd: List[float] = field(default_factory=list)
    signal: List[float] = field(default_factory=list)
    hist: List[float] = field(default_factory=list)

@dataclass
class MAMAResult(BaseModel):
    mama: List[float] = field(default_factory=list)
    fama: List[float] = field(default_factory=list)

@dataclass
class OrderContainerResult(BaseModel):
    price: float = 0.0
    executed_amount: float = 0.0
    filled_amount: float = 0.0
    is_open: bool = False
    is_filled: bool = False
    is_cancelled: bool = False
    fee_costs: float = 0.0
    fee_currency: float = 0.0
    open_time: float = 0.0
    position_id: str = ""
    order_id: str = ""
    is_enter_order: bool = False
    is_exit_order: bool = False
    trigger_price: float = 0.0
    is_buy_order: bool = False
    is_sell_order: bool = False
    number: float = 0.0
    boolean: float = 0.0
    string: float = 0.0

@dataclass
class PositionContainerResult(BaseModel):
    position_id: str = ""
    market: str = ""
    is_long: bool = False
    is_short: bool = False
    enter_price: float = 0.0
    amount: float = 0.0
    profit: float = 0.0
    roi: float = 0.0
    open_time: float = 0.0
    updated_time: float = 0.0
    close_time: float = 0.0
    string: float = 0.0
    boolean: float = 0.0
    number: float = 0.0

@dataclass
class PositionToBoolResult(BaseModel):
    is_long: bool = False
    is_short: bool = False
    is_none: bool = False
    boolean: float = 0.0

@dataclass
class STOCHResult(BaseModel):
    slow_k: List[float] = field(default_factory=list)
    slow_d: List[float] = field(default_factory=list)

@dataclass
class STOCHFResult(BaseModel):
    fast_k: List[float] = field(default_factory=list)
    fast_d: List[float] = field(default_factory=list)

@dataclass
class STOCHRSIResult(BaseModel):
    fast_k: List[float] = field(default_factory=list)
    fast_d: List[float] = field(default_factory=list)

@dataclass
class SignalToBoolResult(BaseModel):
    is_long: bool = False
    is_short: bool = False
    is_exit: bool = False
    is_none: bool = False
    boolean: float = 0.0

@dataclass
class SlowRSIResult(BaseModel):
    rsi: List[float] = field(default_factory=list)
    slow_rsi: List[float] = field(default_factory=list)

@dataclass
class TradeMarketContainerResult(BaseModel):
    base_currency: str = ""
    quote_currency: str = ""
    contract_name: str = ""
    contract_value: float = 0.0
    makers_fee: float = 0.0
    takers_fee: float = 0.0
    underlying_asset: str = ""
    minimum_trade_amount: float = 0.0
    minimum_trade_volume: float = 0.0
    calculated_min_trade_amount: float = 0.0
    profit_label: str = ""
    amount_label: str = ""
    market_type: str = ""
    string: float = 0.0
    number: float = 0.0
    enum: float = 0.0

@dataclass
class UserPositionContainerResult(BaseModel):
    market: str = ""
    is_long: bool = False
    is_short: bool = False
    enter_price: float = 0.0
    amount: float = 0.0
    profit: float = 0.0
    roi: float = 0.0
    string: float = 0.0
    boolean: float = 0.0
    number: float = 0.0

@dataclass
class ZLMAResult(BaseModel):
    ma1: List[float] = field(default_factory=list)
    ma2: List[float] = field(default_factory=list)
