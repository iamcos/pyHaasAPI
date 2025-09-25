"""
Lab Service module for pyHaasAPI v2.

This module provides business logic for lab management.
"""

from .lab_service import LabService, LabAnalysisResult, LabExecutionResult, LabValidationResult

__all__ = ["LabService", "LabAnalysisResult", "LabExecutionResult", "LabValidationResult"]