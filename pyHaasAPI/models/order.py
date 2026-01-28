"""
Order models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .common import BaseModel


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"


class OrderType(Enum):
    """Order type"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class TimeInForce(Enum):
    """Time in force"""
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


@dataclass
class OrderDetails(BaseModel):
    """Order details"""
    order_id: str = ""
    bot_id: str = ""
    account_id: str = ""
    market: str = ""
    side: str = ""
    amount: float = 0.0
    price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    remaining_amount: float = 0.0
    fees: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class OrderRecord(BaseModel):
    """Order record"""
    order_id: str = ""
    bot_id: str = ""
    account_id: str = ""
    market: str = ""
    side: str = ""
    amount: float = 0.0
    price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class OrderRequest(BaseModel):
    """Order request"""
    bot_id: str = ""
    market: str = ""
    side: str = ""
    amount: float = 0.0
    price: Optional[float] = None
    order_type: str = "LIMIT"


@dataclass
class OrderResponse(BaseModel):
    """Order response"""
    order_id: str = ""
    status: OrderStatus = OrderStatus.PENDING
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OrderHistory(BaseModel):
    """Order history"""
    orders: List[OrderDetails] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 100


@dataclass
class Order(BaseModel):
    """Order model"""
    order_id: str = ""
    bot_id: str = ""
    account_id: str = ""
    market: str = ""
    side: str = ""
    amount: float = 0.0
    price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    remaining_amount: float = 0.0
    fees: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PlaceOrderRequest(BaseModel):
    """Place order request"""
    bot_id: str = ""
    market: str = ""
    side: OrderSide = OrderSide.BUY
    amount: float = 0.0
    price: Optional[float] = None
    order_type: OrderType = OrderType.LIMIT
    time_in_force: TimeInForce = TimeInForce.GTC


@dataclass
class CancelOrderRequest(BaseModel):
    """Cancel order request"""
    order_id: str = ""
    bot_id: str = ""


@dataclass
class OrderHistoryRequest(BaseModel):
    """Order history request"""
    bot_id: str = ""
    page: int = 1
    page_size: int = 100
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filter_params: Optional[Dict[str, Any]] = None
