"""
Analysis module for pyHaasAPI

This module provides comprehensive analysis tools for HaasOnline backtesting results,
including trade-level data extraction, performance analysis, and debugging utilities.
"""

from .extraction import BacktestDataExtractor, TradeData, BacktestSummary
from .models import BacktestAnalysis, BotCreationResult, LabAnalysisResult
from .cache import UnifiedCacheManager
from .analyzer import HaasAnalyzer

# Legacy imports (if they exist)
try:
    from .heuristics import HeuristicsAnalyzer, AnalysisResult
    from .performance import PerformanceAnalyzer, PerformanceMetrics
    _legacy_imports = True
except ImportError:
    _legacy_imports = False

__all__ = [
    # New comprehensive analysis
    'BacktestAnalysis',
    'BotCreationResult', 
    'LabAnalysisResult',
    'UnifiedCacheManager',
    'HaasAnalyzer',
    
    # Legacy extraction
    'BacktestDataExtractor',
    'TradeData', 
    'BacktestSummary',
]

# Add legacy imports if available
if _legacy_imports:
    __all__.extend([
        'HeuristicsAnalyzer',
        'AnalysisResult',
        'PerformanceAnalyzer',
        'PerformanceMetrics'
    ])