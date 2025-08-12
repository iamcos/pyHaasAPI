"""
Request models for HaasOnline API endpoints.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class ScriptRecordRequest:
    """Request model for GET_SCRIPT_RECORD endpoint."""
    script_id: str


@dataclass
class DebugTestRequest:
    """Request model for EXECUTE_DEBUGTEST endpoint."""
    script_id: str
    script_content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class QuickTestRequest:
    """Request model for EXECUTE_QUICKTEST endpoint."""
    script_id: str
    account_id: str
    market_tag: str
    interval: int
    script_content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    execution_amount: float = 1.0
    leverage: int = 0
    position_mode: int = 0


@dataclass
class BacktestRequest:
    """Request model for EXECUTE_BACKTEST endpoint."""
    script_id: str
    account_id: str
    market_tag: str
    start_time: int  # Unix timestamp
    end_time: int    # Unix timestamp
    interval: int
    execution_amount: float
    script_content: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    leverage: int = 0
    position_mode: int = 0
    margin_mode: int = 0


@dataclass
class ExecutionUpdateRequest:
    """Request model for GET_EXECUTION_UPDATE endpoint."""
    execution_id: str


@dataclass
class BacktestRuntimeRequest:
    """Request model for GET_BACKTEST_RUNTIME endpoint."""
    backtest_id: str


@dataclass
class BacktestLogsRequest:
    """Request model for GET_BACKTEST_LOGS endpoint."""
    backtest_id: str
    start_index: int = 0
    count: int = 100


@dataclass
class BacktestChartRequest:
    """Request model for GET_BACKTEST_CHART_PARTITION endpoint."""
    backtest_id: str
    partition_index: int = 0


@dataclass
class BacktestHistoryRequest:
    """Request model for GET_BACKTEST_HISTORY endpoint."""
    start_time: Optional[int] = None  # Unix timestamp
    end_time: Optional[int] = None    # Unix timestamp
    limit: int = 50


@dataclass
class ArchiveBacktestRequest:
    """Request model for ARCHIVE_BACKTEST endpoint."""
    backtest_id: str
    archive_name: Optional[str] = None


@dataclass
class DeleteBacktestRequest:
    """Request model for DELETE_BACKTEST endpoint."""
    backtest_id: str


@dataclass
class ExecutionBacktestsRequest:
    """Request model for EXECUTION_BACKTESTS endpoint."""
    include_completed: bool = False
    include_failed: bool = False