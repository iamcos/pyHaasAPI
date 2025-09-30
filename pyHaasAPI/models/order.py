"""
Order models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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
class OrderDetails:
    """Order details"""
    order_id: str
    bot_id: str
    account_id: str
    market: str
    side: str
    amount: float
    price: float
    status: OrderStatus
    filled_amount: float
    remaining_amount: float
    fees: float
    created_at: datetime
    updated_at: datetime


@dataclass
class OrderRecord:
    """Order record"""
    order_id: str
    bot_id: str
    account_id: str
    market: str
    side: str
    amount: float
    price: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


@dataclass
class OrderRequest:
    """Order request"""
    bot_id: str
    market: str
    side: str
    amount: float
    price: Optional[float] = None
    order_type: str = "LIMIT"


@dataclass
class OrderResponse:
    """Order response"""
    order_id: str
    status: OrderStatus
    message: str
    created_at: datetime


@dataclass
class OrderHistory:
    """Order history"""
    orders: List[OrderDetails]
    total_count: int
    page: int
    page_size: int


@dataclass
class Order:
    """Order model"""
    order_id: str
    bot_id: str
    account_id: str
    market: str
    side: str
    amount: float
    price: float
    status: OrderStatus
    filled_amount: float
    remaining_amount: float
    fees: float
    created_at: datetime
    updated_at: datetime


@dataclass
class PlaceOrderRequest:
    """Place order request"""
    bot_id: str
    market: str
    side: OrderSide
    amount: float
    price: Optional[float] = None
    order_type: OrderType = OrderType.LIMIT
    time_in_force: TimeInForce = TimeInForce.GTC


@dataclass
class CancelOrderRequest:
    """Cancel order request"""
    order_id: str
    bot_id: str


@dataclass
class OrderHistoryRequest:
    """Order history request"""
    bot_id: str
    page: int = 1
    page_size: int = 100
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filter_params: Optional[Dict[str, Any]] = None
