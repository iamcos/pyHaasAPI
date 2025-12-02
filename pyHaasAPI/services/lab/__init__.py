"""
Lab Service module for pyHaasAPI v2.

This module provides business logic for lab management.
"""

try:
    from .lab_service import LabService, LabAnalysisResult, LabExecutionResult, LabValidationResult
except ImportError:
    LabService = None
    LabAnalysisResult = None
    LabExecutionResult = None
    LabValidationResult = None

__all__ = ["LabService", "LabAnalysisResult", "LabExecutionResult", "LabValidationResult"]