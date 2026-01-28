"""
Account models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from .common import BaseModel


@dataclass
class AccountDetails(BaseModel):
    """Account details"""
    account_id: str = ""
    name: str = ""
    exchange: str = ""
    account_type: str = ""
    status: str = ""
    balance: float = 0.0
    margin_mode: str = ""
    position_mode: str = ""
    leverage: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountRecord(BaseModel):
    """Account record with proper field aliases for server response"""
    user_id: str = ""
    account_id: str = ""
    name: str = ""
    exchange: str = ""
    exchange_type: int = 0
    status: int = 0
    is_simulated: bool = False
    is_testnet: bool = False
    is_paper: bool = False
    is_wallet: bool = False
    position_mode: int = 0
    market_settings: Optional[Dict[str, Any]] = None
    version: int = 0


@dataclass
class AccountBalance(BaseModel):
    """Account balance"""
    account_id: str = ""
    total_balance: float = 0.0
    available_balance: float = 0.0
    used_balance: float = 0.0
    currency: str = ""
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountSettings(BaseModel):
    """Account settings"""
    account_id: str = ""
    margin_mode: str = ""
    position_mode: str = ""
    leverage: float = 0.0
    auto_close: bool = False
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountOrder(BaseModel):
    """Account order"""
    order_id: str = ""
    account_id: str = ""
    market: str = ""
    side: str = ""
    amount: float = 0.0
    price: float = 0.0
    status: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccountPosition(BaseModel):
    """Account position"""
    position_id: str = ""
    account_id: str = ""
    market: str = ""
    side: str = ""
    size: float = 0.0
    entry_price: float = 0.0
    current_price: float = 0.0
    pnl: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)



