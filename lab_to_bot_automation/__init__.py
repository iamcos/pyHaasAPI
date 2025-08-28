#!/usr/bin/env python3
"""
Lab to Bot Automation Package
=============================

Fully autonomous system that analyzes lab backtests and converts
the best performing ones into live trading bots.

This package provides:
- WFO Analyzer: Advanced Walk Forward Optimization analysis
- Account Manager: Automated account creation and management
- Bot Creation Engine: Automated bot deployment system
- Main Orchestrator: Complete automation workflow

Author: AI Assistant
Version: 1.0
"""

from .wfo_analyzer import WFOAnalyzer, WFOConfig, WFOMetrics, BotRecommendation
from .account_manager import AccountManager, AccountConfig, AccountInfo
from .bot_creation_engine import BotCreationEngine, BotCreationConfig, BotDeploymentResult, DeploymentReport
from .automation import LabToBotAutomation, AutomationConfig

__version__ = "1.0.0"
__author__ = "AI Assistant"
__description__ = "Fully autonomous HaasOnline Lab to Bot automation system"

__all__ = [
    # WFO Analyzer
    "WFOAnalyzer",
    "WFOConfig",
    "WFOMetrics",
    "BotRecommendation",

    # Account Manager
    "AccountManager",
    "AccountConfig",
    "AccountInfo",

    # Bot Creation Engine
    "BotCreationEngine",
    "BotCreationConfig",
    "BotDeploymentResult",
    "DeploymentReport",
    
    # Main Automation
    "LabToBotAutomation",
    "AutomationConfig"
]

