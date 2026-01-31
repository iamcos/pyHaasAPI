
"""
Implicit models for pyHaasAPI v2
Representing tuple-based or semi-structured data from Staging.
"""

from dataclasses import dataclass
from .common import BaseModel

@dataclass
class MarketTrade(BaseModel):
    """
    Represents a single trade from GetLastTrades.
    Format: [price, amount, isBuy?, unix]
    """
    price: float = 0.0
    amount: float = 0.0
    is_buy: bool = False
    timestamp: float = 0.0

@dataclass
class OrderbookRow(BaseModel):
    """
    Represents a single row in the orderbook.
    Format: [price, amount]
    """
    price: float = 0.0
    amount: float = 0.0
