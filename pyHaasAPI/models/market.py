"""
Market models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MarketData:
    """Market data"""
    market: str
    exchange: str
    base_currency: str
    quote_currency: str
    price: float
    volume: float
    timestamp: datetime


@dataclass
class PriceData:
    """Price data"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid: float
    ask: float
    spread: float
    spread_percentage: float


@dataclass
class CloudMarket:
    """Cloud market"""
    market: str
    exchange: str
    base_currency: str
    quote_currency: str
    is_active: bool
    min_trade_amount: float
    max_trade_amount: float
    price_precision: int
    amount_precision: int


@dataclass
class MarketInfo:
    """Market information"""
    market: str
    exchange: str
    base_currency: str
    quote_currency: str
    price: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime


@dataclass
class HistoricalData:
    """Historical market data"""
    market: str
    interval: str
    data: List[PriceData]
    start_time: datetime
    end_time: datetime



