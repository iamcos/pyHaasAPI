"""
Trade-related data models for pyHaasAPI v2

Provides standardized data models for completed trades.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from .common import BaseModel

@dataclass
class Trade(BaseModel):
    """
    Standardized Trade record.
    Represents a completed trade (entry + exit) or a single trade execution depending on context.
    """
    trade_id: str = ""
    bot_id: str = ""
    
    # Timing
    timestamp: int = 0  # Unix timestamp (ms or s depending on source, normalized usually)
    entry_time: int = 0
    exit_time: int = 0
    duration_seconds: int = 0
    
    # Price & Quantity
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    
    # Financials
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    fees: float = 0.0
    net_profit: float = 0.0
    
    # Metadata
    pair: str = ""   # e.g. "BTC/USDT"
    side: str = ""   # "LONG" or "SHORT"
    details: str = "" # Extra info
    
    @property
    def is_win(self) -> bool:
        return self.profit_loss > 0

    @property
    def datetime_entry(self) -> Optional[datetime]:
        if self.entry_time > 0:
            return datetime.fromtimestamp(self.entry_time) if self.entry_time < 2e10 else datetime.fromtimestamp(self.entry_time/1000)
        return None
