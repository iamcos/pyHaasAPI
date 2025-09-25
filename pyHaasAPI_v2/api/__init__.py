"""
API modules for pyHaasAPI v2

Domain-separated API modules for different aspects of the HaasOnline API.
"""

from .lab import LabAPI
from .bot import BotAPI
from .account import AccountAPI
from .script import ScriptAPI
from .market import MarketAPI
from .backtest import BacktestAPI
from .order import OrderAPI

__all__ = [
    "LabAPI",
    "BotAPI",
    "AccountAPI", 
    "ScriptAPI",
    "MarketAPI",
    "BacktestAPI",
    "OrderAPI",
]