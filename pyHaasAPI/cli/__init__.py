"""
CLI module for pyHaasAPI v2

This module provides command-line interfaces for all pyHaasAPI v2 operations
using the new async architecture and type-safe components.
"""

from .base import BaseCLI, CLIConfig
from .main import main, create_parser
from .unified_cli import UnifiedCLI, create_parser as create_unified_parser, main as unified_main
from .lab_cli import LabCLI
from .bot_cli import BotCLI
from .analysis_cli import AnalysisCLI
from .account_cli import AccountCLI
from .script_cli import ScriptCLI
from .market_cli import MarketCLI
from .backtest_cli import BacktestCLI
from .order_cli import OrderCLI
from .consolidated_cli import ConsolidatedCLI

__all__ = [
    "BaseCLI",
    "CLIConfig",
    "main",
    "create_parser",
    "UnifiedCLI",
    "create_unified_parser",
    "unified_main",
    "LabCLI",
    "BotCLI",
    "AnalysisCLI",
    "AccountCLI",
    "ScriptCLI",
    "MarketCLI",
    "BacktestCLI",
    "OrderCLI",
    "ConsolidatedCLI",
]