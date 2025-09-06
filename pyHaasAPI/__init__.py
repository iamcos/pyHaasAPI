import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from pyHaasAPI.types import (UserState, Guest, Authenticated, HaasApiError, SyncExecutor)
from pyHaasAPI.parameters import (LabParameter, LabStatus, LabConfig, LabSettings, BacktestStatus, LabAlgorithm)
from pyHaasAPI.model import (ApiResponse, LabDetails)
from .market_manager import MarketManager
from .lab_manager import LabManager, LabConfig, LabSettings
from .parameter_handler import ParameterHandler

# Import new analysis functionality
from .analysis import (
    BacktestAnalysis, BotCreationResult, LabAnalysisResult,
    UnifiedCacheManager, HaasAnalyzer
)

# Import CLI functionality
from .cli import simple_cli_main

__all__ = [
    "SyncExecutor", "Guest", "Authenticated", "HaasApiError", 
    "ApiResponse", "LabStatus", "BacktestStatus", "LabConfig", 
    "LabSettings", "LabDetails", "MarketManager", "LabManager", 
    "ParameterHandler",
    # New analysis functionality
    "BacktestAnalysis", "BotCreationResult", "LabAnalysisResult",
    "UnifiedCacheManager", "HaasAnalyzer",
    # CLI functionality
    "simple_cli_main"
]
