"""
Flexible reporting system for pyHaasAPI v2

Provides multiple output formats and flexible report generation
with bot recommendations including stats, lab id, backtest id, and more.
"""

from .formatter import ReportFormatter
from .types import ReportType, ReportFormat, ReportConfig
from .models import (
    AnalysisReport,
    BotRecommendation,
    LabSummary,
    BacktestSummary
)

__all__ = [
    "ReportFormatter",
    "ReportType",
    "ReportFormat", 
    "ReportConfig",
    "AnalysisReport",
    "BotRecommendation",
    "LabSummary",
    "BacktestSummary"
]

