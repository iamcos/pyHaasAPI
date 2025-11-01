"""
Analysis module for pyHaasAPI v2

This module provides comprehensive analysis tools for backtest analysis,
including advanced metrics computation, data extraction, and performance analysis.

Based on the excellent v1 implementation with enhanced functionality.
"""

from .metrics import (
    RunMetrics,
    compute_metrics,
    calculate_risk_score,
    calculate_stability_score,
    calculate_composite_score
)

from .extraction import (
    BacktestDataExtractor,
    BacktestSummary,
    TradeData
)

from .wfo import (
    WFOMode,
    WFOPeriod,
    WFOResult,
    WFOConfig,
    WFOAnalysisResult,
    WFOAnalyzer
)

from .robustness import (
    DrawdownEvent,
    DrawdownAnalysis,
    TimePeriodAnalysis,
    RobustnessMetrics,
    StrategyRobustnessAnalyzer
)

__all__ = [
    # Metrics
    'RunMetrics',
    'compute_metrics',
    'calculate_risk_score',
    'calculate_stability_score',
    'calculate_composite_score',
    
    # Data Extraction
    'BacktestDataExtractor',
    'BacktestSummary',
    'TradeData',
    
    # Walk Forward Optimization
    'WFOMode',
    'WFOPeriod',
    'WFOResult',
    'WFOConfig',
    'WFOAnalysisResult',
    'WFOAnalyzer',
    
    # Robustness Analysis
    'DrawdownEvent',
    'DrawdownAnalysis',
    'TimePeriodAnalysis',
    'RobustnessMetrics',
    'StrategyRobustnessAnalyzer',
]
