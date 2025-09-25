"""
Account models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


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


@dataclass
class AccountRecord:
    """Account record"""
    account_id: str
    name: str
    exchange: str
    account_type: str
    status: str
    created_at: datetime
    updated_at: datetime


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



