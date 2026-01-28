"""
Market models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from .common import BaseModel


@dataclass
class MarketData(BaseModel):
    """Market data"""
    market: str = ""
    exchange: str = ""
    base_currency: str = ""
    quote_currency: str = ""
    price: float = 0.0
    volume: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PriceData(BaseModel):
    """Price data"""
    timestamp: int = 0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    spread: float = 0.0
    spread_percentage: float = 0.0


@dataclass
class CloudMarket(BaseModel):
    """Cloud market"""
    market: str = ""
    exchange: str = ""
    base_currency: str = ""
    quote_currency: str = ""
    is_active: bool = False
    min_trade_amount: float = 0.0
    max_trade_amount: float = 0.0
    price_precision: int = 0
    amount_precision: int = 0


@dataclass
class MarketInfo(BaseModel):
    """Market information"""
    market: str = ""
    exchange: str = ""
    base_currency: str = ""
    quote_currency: str = ""
    price: float = 0.0
    volume_24h: float = 0.0
    change_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class HistoricalData(BaseModel):
    """Historical market data"""
    market: str = ""
    interval: str = ""
    data: List[PriceData] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)



