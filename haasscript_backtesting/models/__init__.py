"""
Data models for the HaasScript Backtesting System.

This module contains all the core data structures used throughout the system,
including script definitions, backtest configurations, execution tracking, and results.
"""

from .script_models import HaasScript, ScriptCapabilities, DebugResult, ValidationResult, QuickTestResult, ScriptType
from .backtest_models import BacktestConfig, BacktestExecution, ExecutionStatus, ExecutionSummary, ExecutionStatusType, PositionMode
from .result_models import ProcessedResults, ExecutionMetrics, Trade, PerformanceData, ChartData, TradeType, TradeStatus
from .optimization_models import SweepConfig, SweepExecution, OptimizationResults, RankedResults
from .common_models import ResourceUsage, LogEntry, BacktestSummary

__all__ = [
    # Script models
    "HaasScript",
    "ScriptCapabilities", 
    "DebugResult",
    "ValidationResult",
    "QuickTestResult",
    "ScriptType",
    
    # Backtest models
    "BacktestConfig",
    "BacktestExecution",
    "ExecutionStatus",
    "ExecutionSummary",
    "ExecutionStatusType",
    "PositionMode",
    
    # Result models
    "ProcessedResults",
    "ExecutionMetrics",
    "Trade",
    "PerformanceData", 
    "ChartData",
    "TradeType",
    "TradeStatus",
    
    # Optimization models
    "SweepConfig",
    "SweepExecution",
    "OptimizationResults",
    "RankedResults",
    
    # Common models
    "ResourceUsage",
    "LogEntry",
    "BacktestSummary",
]