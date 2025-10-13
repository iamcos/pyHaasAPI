"""
Exception hierarchy for pyHaasAPI v2

Provides comprehensive exception handling with proper error categorization
and context information for better debugging and error recovery.
"""

from .base import HaasAPIError
from .auth import AuthenticationError, InvalidCredentialsError, SessionExpiredError, OneTimeCodeError
from .api import APIError, APIRequestError, APIResponseError, APIRateLimitError, APITimeoutError, APIServerError, APIClientError
from .validation import ValidationError
from .network import NetworkError, ConnectionError, TimeoutError, DNSResolutionError, SSLVerificationError
from .config import ConfigurationError
from .cache import CacheError
from .analysis import AnalysisError
from .finetune import FinetuneError
from .account import AccountError, AccountNotFoundError, AccountConfigurationError, AccountBalanceError, AccountPermissionError
from .script import ScriptError, ScriptNotFoundError, ScriptCreationError, ScriptConfigurationError, ScriptExecutionError, ScriptValidationError
from .market import MarketError, MarketNotFoundError, PriceDataError, MarketDataError, ExchangeError
from .backtest import BacktestError, BacktestNotFoundError, BacktestExecutionError, BacktestConfigurationError, BacktestDataError
from .order import OrderError, OrderNotFoundError, OrderExecutionError, OrderValidationError, OrderCancellationError
from .data_dumper import DataDumperError, DataDumperConfigurationError, DataDumperExportError, DataDumperImportError
from .testing import TestingError, TestingConfigurationError, TestingExecutionError, TestingValidationError
from .bot import BotError, BotCreationError, BotConfigurationError, BotNotFoundError, BotActivationError, BotDeactivationError, BotParameterError
from .lab import LabError, LabNotFoundError, LabExecutionError, LabConfigurationError, LabScriptError, LabParameterError
from .server import ServerError, ServerConnectionError, ServerAuthenticationError, ServerTimeoutError, ServerUnavailableError, ServerConfigurationError
from .orchestration import OrchestrationError, ProjectExecutionError, ServerCoordinationError, WorkflowError, ConfigurationError, ResourceError

__all__ = [
    "HaasAPIError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "SessionExpiredError", 
    "OneTimeCodeError", 
    "APIError",
    "APIRequestError",
    "APIResponseError", 
    "APIRateLimitError",
    "APITimeoutError", 
    "APIServerError",
    "APIClientError",
    "ValidationError",
    "NetworkError",
    "ConnectionError",
    "TimeoutError",
    "DNSResolutionError",
    "SSLVerificationError",
    "ConfigurationError",
    "CacheError",
    "AnalysisError",
    "FinetuneError",
    "AccountError",
    "AccountNotFoundError",
    "AccountConfigurationError",
    "AccountBalanceError",
    "AccountPermissionError",
    "ScriptError",
    "ScriptNotFoundError",
    "ScriptCreationError",
    "ScriptConfigurationError",
    "ScriptExecutionError",
    "ScriptValidationError",
    "MarketError",
    "MarketNotFoundError",
    "PriceDataError",
    "MarketDataError",
    "ExchangeError",
    "BacktestError",
    "BacktestNotFoundError",
    "BacktestExecutionError",
    "BacktestConfigurationError",
    "BacktestDataError",
    "OrderError",
    "OrderNotFoundError",
    "OrderExecutionError",
    "OrderValidationError",
    "OrderCancellationError",
    "DataDumperError",
    "DataDumperConfigurationError",
    "DataDumperExportError",
    "DataDumperImportError",
    "TestingError",
    "TestingConfigurationError",
    "TestingExecutionError",
    "TestingValidationError",
    "BotError",
    "BotCreationError",
    "BotConfigurationError",
    "BotNotFoundError",
    "BotActivationError",
    "BotDeactivationError",
    "BotParameterError",
    "LabError",
    "LabNotFoundError",
    "LabExecutionError", 
    "LabConfigurationError",
    "LabScriptError",
    "LabParameterError",
    "ServerError",
    "ServerConnectionError",
    "ServerAuthenticationError",
    "ServerTimeoutError",
    "ServerUnavailableError",
    "ServerConfigurationError",
    "OrchestrationError",
    "ProjectExecutionError",
    "ServerCoordinationError",
    "WorkflowError",
    "ConfigurationError",
    "ResourceError",
]
