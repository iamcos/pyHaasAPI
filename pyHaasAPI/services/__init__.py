"""
Services module for pyHaasAPI v2

This module provides business logic services for different aspects of the system.
"""

# Optional service imports - services may not all be available
try:
    from .lab import LabService, LabAnalysisResult, LabExecutionResult, LabValidationResult
except ImportError:
    LabService = LabAnalysisResult = LabExecutionResult = LabValidationResult = None

try:
    from .bot import BotService, BotCreationResult, MassBotCreationResult, BotValidationResult
except ImportError:
    BotService = BotCreationResult = MassBotCreationResult = BotValidationResult = None

try:
    from .analysis import AnalysisService, BacktestPerformance, LabAnalysisResult, AnalysisReport
except ImportError:
    AnalysisService = BacktestPerformance = LabAnalysisResult = AnalysisReport = None

try:
    from .reporting import ReportingService, ReportType, ReportFormat, ReportConfig, ReportResult
except ImportError:
    ReportingService = ReportType = ReportFormat = ReportConfig = ReportResult = None

try:
    from .server_content_manager import ServerContentManager, SnapshotResult
except ImportError:
    ServerContentManager = SnapshotResult = None

try:
    from .account_manager import AccountManager, AccountAssignmentState
except ImportError:
    AccountManager = AccountAssignmentState = None

try:
    from .bot_naming_service import BotNamingService, BotNamingContext
except ImportError:
    BotNamingService = BotNamingContext = None

try:
    from .bot_deployment_service import BotDeploymentService
except ImportError:
    BotDeploymentService = None

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

    # Server content
    "ServerContentManager",
    "SnapshotResult",
    
    # Account Management
    "AccountManager",
    "AccountAssignmentState",
    
    # Bot Naming
    "BotNamingService",
    "BotNamingContext",
    
    # Bot Deployment
    "BotDeploymentService",
]