"""
Account models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, Field


@dataclass
class AccountDetails:
    """Account details"""
    account_id: str
    name: str
    exchange: str
    account_type: str
    status: str
    balance: float
    margin_mode: str
    position_mode: str
    leverage: float
    created_at: datetime
    updated_at: datetime


class AccountRecord(BaseModel):
    """Account record with proper field aliases for server response"""
    user_id: str = Field(alias="UID", description="User ID")
    account_id: str = Field(alias="AID", description="Account ID")
    name: str = Field(alias="N", description="Account name")
    exchange: str = Field(alias="EC", description="Exchange code")
    exchange_type: int = Field(alias="ET", description="Exchange type")
    status: int = Field(alias="S", description="Account status")
    is_simulated: bool = Field(alias="IS", description="Is simulated account")
    is_testnet: bool = Field(alias="IT", description="Is testnet account")
    is_paper: bool = Field(alias="PA", description="Is paper trading account")
    is_wallet: bool = Field(alias="WL", description="Is wallet account")
    position_mode: int = Field(alias="PM", description="Position mode")
    market_settings: Optional[Dict[str, Any]] = Field(alias="MS", default=None, description="Market settings")
    version: int = Field(alias="V", description="Account version")


@dataclass
class AccountBalance:
    """Account balance"""
    account_id: str
    total_balance: float
    available_balance: float
    used_balance: float
    currency: str
    updated_at: datetime


@dataclass
class AccountSettings:
    """Account settings"""
    account_id: str
    margin_mode: str
    position_mode: str
    leverage: float
    auto_close: bool
    updated_at: datetime


@dataclass
class AccountOrder:
    """Account order"""
    order_id: str
    account_id: str
    market: str
    side: str
    amount: float
    price: float
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class AccountPosition:
    """Account position"""
    position_id: str
    account_id: str
    market: str
    side: str
    size: float
    entry_price: float
    current_price: float
    pnl: float
    created_at: datetime
    updated_at: datetime



