"""
Data models for pyHaasAPI v2

Provides comprehensive data models for all API operations including
lab management, bot operations, account management, and more.
"""

from .lab import LabDetails, LabRecord, LabConfig, StartLabExecutionRequest, LabExecutionUpdate
from .bot import BotDetails, BotRecord, BotConfiguration
from .account import AccountDetails, AccountRecord, AccountBalance
from .script import ScriptRecord, ScriptItem, ScriptParameter
from .market import MarketData, PriceData, CloudMarket
from .backtest import BacktestResult, BacktestRuntimeData, BacktestAnalysis
from .order import OrderDetails, OrderRecord, OrderStatus
from .common import ApiResponse, PaginatedResponse, ErrorResponse

__all__ = [
    # Lab models
    "LabDetails",
    "LabRecord", 
    "LabConfig",
    "StartLabExecutionRequest",
    "LabExecutionUpdate",
    
    # Bot models
    "BotDetails",
    "BotRecord",
    "BotConfiguration",
    
    # Account models
    "AccountDetails",
    "AccountRecord",
    "AccountBalance",
    
    # Script models
    "ScriptRecord",
    "ScriptItem",
    "ScriptParameter",
    
    # Market models
    "MarketData",
    "PriceData",
    "CloudMarket",
    
    # Backtest models
    "BacktestResult",
    "BacktestRuntimeData",
    "BacktestAnalysis",
    
    # Order models
    "OrderDetails",
    "OrderRecord",
    "OrderStatus",
    
    # Common models
    "ApiResponse",
    "PaginatedResponse",
    "ErrorResponse",
]
