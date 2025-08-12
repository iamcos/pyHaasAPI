"""
Analysis module for pyHaasAPI

This module provides comprehensive analysis tools for HaasOnline backtesting results,
including trade-level data extraction, performance analysis, and debugging utilities.
"""

from .extraction import BacktestDataExtractor, TradeData, BacktestSummary
from .heuristics import HeuristicsAnalyzer, AnalysisResult
from .performance import PerformanceAnalyzer, PerformanceMetrics

__all__ = [
    'BacktestDataExtractor',
    'TradeData', 
    'BacktestSummary',
    'HeuristicsAnalyzer',
    'AnalysisResult',
    'PerformanceAnalyzer',
    'PerformanceMetrics'
]