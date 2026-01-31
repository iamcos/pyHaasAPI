"""
Market models for pyHaasAPI v2
Mapped from hs.trade-market-information.def.lua
"""

from typing import List
from dataclasses import dataclass, field
from .common import BaseModel
from .trade import Trade

@dataclass
class TradeMarket(BaseModel):
    """
    Trade Market Information (TradeMarketContainer)
    Contains metadata about a specific market.
    """
    market: str = ""
    base_currency: str = ""
    quote_currency: str = ""
    contract_name: str = ""
    contract_value: float = 0.0
    underlying_asset: str = ""
    
    # Fees
    makers_fee: float = 0.0
    takers_fee: float = 0.0
    
    # Limits
    minimum_trade_amount: float = 0.0
    minimum_trade_volume: float = 0.0
    calculated_min_trade_amount: float = 0.0
    
    # Labels
    profit_label: str = ""
    amount_label: str = ""
    
    # Enum
    market_type: str = "" # SpotTrading, MarginTrading, LeverageTrading

@dataclass
class MarketData(BaseModel):
    """
    Core market data (PriceMarket)
    Enhanced with dynamic analytics from trades.
    """
    price_source: str = ""
    base_currency: str = ""
    quote_currency: str = ""
    contract_name: str = ""
    
    # Analytics data
    trades: List[Trade] = field(default_factory=list)
    starting_balance: float = 10000.0

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def net_profit(self) -> float:
        return sum(t.net_profit for t in self.trades)

    @property
    def roi(self) -> float:
        if self.starting_balance <= 0 or not self.trades:
            return 0.0
        return (self.net_profit / self.starting_balance) * 100.0

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.is_win)
        return (wins / len(self.trades)) * 100.0

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        return gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

@dataclass
class PriceData(BaseModel):
    """
    Current price data (CurrentPriceResult)
    """
    timestamp: int = 0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    ask: float = 0.0
    bid: float = 0.0
    spread: float = 0.0
    spread_percentage: float = 0.0

@dataclass
class CloudMarket(BaseModel):
    """
    Cloud market data
    """
    market: str = ""
    exchange: str = ""
    base_currency: str = ""
    quote_currency: str = ""
    is_active: bool = True
    min_trade_amount: float = 0.0
    max_trade_amount: float = 0.0
    price_precision: int = 2
    amount_precision: int = 2
    
    # Redundant fields for backward compatibility
    price_source: str = ""
    primary: str = ""
    secondary: str = ""
    contract: str = ""
    market_tag: str = ""

@dataclass
class Orderbook(BaseModel):
    """
    Orderbook information (ResultOf_GetOrderbook)
    """
    ask_prices: List[float] = field(default_factory=list)
    ask_amounts: List[float] = field(default_factory=list)
    bid_prices: List[float] = field(default_factory=list)
    bid_amounts: List[float] = field(default_factory=list)
