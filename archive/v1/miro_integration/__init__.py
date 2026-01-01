"""
Miro Integration Module for pyHaasAPI

This module provides comprehensive integration with Miro boards for:
- Real-time lab progression monitoring
- Interactive bot deployment management
- Automated reporting and analytics
- Visual performance tracking

Key Components:
- MiroClient: Core API client for Miro interactions
- LabMonitor: Real-time lab monitoring with Miro updates
- BotDeploymentCenter: Interactive bot deployment interface
- ReportGenerator: Automated report generation for Miro boards
- DashboardManager: Centralized dashboard management
"""

from .client import MiroClient
from .lab_monitor import LabMonitor
from .bot_deployment import BotDeploymentCenter
from .report_generator import ReportGenerator
from .dashboard_manager import DashboardManager

__all__ = [
    'MiroClient',
    'LabMonitor', 
    'BotDeploymentCenter',
    'ReportGenerator',
    'DashboardManager'
]
