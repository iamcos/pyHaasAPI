"""
Analysis module for pyHaasAPI

This module provides comprehensive analysis tools for HaasOnline backtesting results,
including trade-level data extraction, performance analysis, and debugging utilities.
"""

from .extraction import BacktestDataExtractor, TradeData, BacktestSummary
from .models import BacktestAnalysis, BotCreationResult, LabAnalysisResult
from .cache import UnifiedCacheManager
from .analyzer import HaasAnalyzer
from .wfo import WFOAnalyzer, WFOConfig, WFOMode, WFOResult, WFOAnalysisResult
from .robustness import StrategyRobustnessAnalyzer, RobustnessMetrics, DrawdownAnalysis, TimePeriodAnalysis
from .backtest_manager import BacktestManager, BacktestJob, WFOJob
from .live_bot_validator import LiveBotValidator, LiveBotValidationJob, LiveBotValidationReport, BotRecommendation

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
    
    # Walk Forward Optimization
    'WFOAnalyzer',
    'WFOConfig',
    'WFOMode',
    'WFOResult',
    'WFOAnalysisResult',
    
    # Strategy Robustness Analysis
    'StrategyRobustnessAnalyzer',
    'RobustnessMetrics',
    'DrawdownAnalysis',
    'TimePeriodAnalysis',
    
    # Backtest Management
    'BacktestManager',
    'BacktestJob',
    'WFOJob',
    
    # Live Bot Validation
    'LiveBotValidator',
    'LiveBotValidationJob',
    'LiveBotValidationReport',
    'BotRecommendation',
    
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