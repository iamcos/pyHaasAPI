"""
Data models for pyHaasAPI v2

Provides comprehensive data models for all API operations including
lab management, bot operations, account management, and more.
"""

from .lab import LabDetails, LabRecord, LabConfig, StartLabExecutionRequest, LabExecutionUpdate
from .bot import BotDetails, BotRecord, BotConfiguration
from .account import AccountDetails, AccountRecord, AccountBalance
from .script import ScriptRecord, ScriptItem, ScriptParameter
from .position import Position, UserPosition
from .wallet import Wallet, WalletBalance
from .market import MarketData, PriceData, TradeMarket, Orderbook
from .backtest import BacktestResult, BacktestRuntimeData, BacktestAnalysis
from .order import OrderDetails, OrderRecord, OrderStatus
from .trade import Trade
from .enums import *
from .staging_results import *
from .staging_params import *
from .implicit import *
from .common import ApiResponse, PaginatedResponse, ErrorResponse

__all__ = [
    # Enums
    "ShapeType", "AxisType", "LineStyle", "PlotType",
    "ArrayFilterTypesEnum", "CandlePatternEnum", "DataTypesEnum",
    "MarginModeEnum", "MovingAveragesEnum", "OrderTypesEnum",
    "ParameterTypeEnum", "PositionEnum", "PositionModeEnum",
    "SignalEnum", "SignalTypesEnum", "SourcePriceTypesEnum",
    "TradingEnum", "TradingLrEnum",

    # Technical Analysis
    "ABANDSResult", "AROONResult", "BBANDSResult", "DONCHIANResult",
    "FastRSIResult", "HT_PHASORResult", "HT_SINEResult", "ICHIMOKUResult",
    "KELTNERResult", "KSTResult", "MACDResult", "MACDEXTResult",
    "MACDFIXResult", "MAMAResult", "STOCHResult", "STOCHFResult",
    "STOCHRSIResult", "SlowRSIResult", "ZLMAResult",

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
    "TradeMarket",
    "Orderbook",
    
    # Analysis models
    "TradingReport",
    
    # Backtest models
    "BacktestResult",
    "BacktestRuntimeData",
    "BacktestAnalysis",
    
    # Order models
    "OrderDetails",
    "OrderRecord",
    "OrderStatus",
    
    # Trade models
    "Trade",
    
    # Position models
    "Position",
    "UserPosition",
    
    # Wallet models
    "Wallet",
    "WalletBalance",

    
    # Common models
    "ApiResponse",
    "PaginatedResponse",
    "ErrorResponse",
]
