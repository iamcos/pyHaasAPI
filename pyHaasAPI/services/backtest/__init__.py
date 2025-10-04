"""
Backtest Services for pyHaasAPI

This module provides unified backtest functionality including longest backtest discovery,
execution, and monitoring to eliminate code duplication across the codebase.
"""

from .backtest_service import (
    BacktestService,
    CutoffDiscoveryResult,
    BacktestExecutionResult,
    BacktestProgress
)

__all__ = [
    'BacktestService',
    'CutoffDiscoveryResult', 
    'BacktestExecutionResult',
    'BacktestProgress'
]






