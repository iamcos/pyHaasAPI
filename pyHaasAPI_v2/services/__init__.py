"""
Services module for pyHaasAPI v2

This module provides business logic services for different aspects of the system.
"""

from .lab import LabService, LabAnalysisResult, LabExecutionResult, LabValidationResult
from .bot import BotService, BotCreationResult, MassBotCreationResult, BotValidationResult
from .analysis import AnalysisService, BacktestPerformance, LabAnalysisResult, AnalysisReport
from .reporting import ReportingService, ReportType, ReportFormat, ReportConfig, ReportResult

__all__ = [
    # Lab Service
    "LabService",
    "LabAnalysisResult", 
    "LabExecutionResult",
    "LabValidationResult",
    
    # Bot Service
    "BotService",
    "BotCreationResult",
    "MassBotCreationResult",
    "BotValidationResult",
    
    # Analysis Service
    "AnalysisService",
    "BacktestPerformance",
    "LabAnalysisResult",
    "AnalysisReport",
    
    # Reporting Service
    "ReportingService",
    "ReportType",
    "ReportFormat", 
    "ReportConfig",
    "ReportResult",
]