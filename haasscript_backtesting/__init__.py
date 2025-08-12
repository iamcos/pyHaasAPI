"""
HaasScript Backtesting System

A comprehensive platform for direct HaasScript backtesting, optimization, and analysis.
Provides an alternative to lab-based testing with enhanced debugging and parameter optimization capabilities.
"""

__version__ = "1.0.0"
__author__ = "HaasScript Backtesting Team"

from .models import HaasScript, BacktestConfig, BacktestExecution, ProcessedResults
from .config import SystemConfig, HaasOnlineConfig
from .script_manager import ScriptManager
from .backtest_manager import BacktestManager
from .results_manager import ResultsManager

__all__ = [
    "HaasScript",
    "BacktestConfig", 
    "BacktestExecution",
    "ProcessedResults",
    "SystemConfig",
    "HaasOnlineConfig",
    "ScriptManager",
    "BacktestManager",
    "ResultsManager",
]