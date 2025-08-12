"""
Response models for HaasOnline API endpoints.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ScriptRecordResponse:
    """Response model for GET_SCRIPT_RECORD endpoint."""
    script_id: str
    name: str
    content: str
    script_type: int
    parameters: Dict[str, Any]
    created_at: datetime
    modified_at: datetime
    compile_logs: List[str]
    is_valid: bool
    error_message: Optional[str] = None


@dataclass
class CompilationError:
    """Compilation error details."""
    line_number: int
    column: int
    error_type: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class DebugTestResponse:
    """Response model for EXECUTE_DEBUGTEST endpoint."""
    success: bool
    compilation_logs: List[str]
    errors: List[CompilationError]
    warnings: List[str]
    execution_time_ms: int
    memory_usage_mb: float
    is_valid: bool
    error_message: Optional[str] = None


@dataclass
class TradeResult:
    """Individual trade result."""
    timestamp: datetime
    action: str  # Action type (e.g., "ACTION_A" or "ACTION_B")
    price: float
    amount: float
    fee: float
    profit_loss: float
    balance_after: float


@dataclass
class QuickTestResponse:
    """Response model for EXECUTE_QUICKTEST endpoint."""
    success: bool
    execution_id: str
    trades: List[TradeResult]
    final_balance: float
    total_profit_loss: float
    execution_logs: List[str]
    runtime_data: Dict[str, Any]
    execution_time_ms: int
    error_message: Optional[str] = None


@dataclass
class BacktestResponse:
    """Response model for EXECUTE_BACKTEST endpoint."""
    success: bool
    backtest_id: str
    execution_id: str
    status: ExecutionStatus
    estimated_completion_time: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class ExecutionProgress:
    """Execution progress information."""
    percentage: float
    current_phase: str
    processed_candles: int
    total_candles: int
    estimated_remaining_seconds: int
    current_timestamp: datetime


@dataclass
class ResourceUsage:
    """Resource usage information."""
    cpu_percentage: float
    memory_mb: float
    disk_io_mb: float
    network_io_mb: float


@dataclass
class ExecutionUpdateResponse:
    """Response model for GET_EXECUTION_UPDATE endpoint."""
    execution_id: str
    backtest_id: str
    status: ExecutionStatus
    progress: ExecutionProgress
    resource_usage: ResourceUsage
    started_at: datetime
    last_update: datetime
    error_message: Optional[str] = None


@dataclass
class ExecutionMetrics:
    """Execution performance metrics."""
    total_return: float
    total_return_percentage: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percentage: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_duration_minutes: float
    avg_winning_trade: float
    avg_losing_trade: float
    largest_winning_trade: float
    largest_losing_trade: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float


@dataclass
class BacktestRuntimeResponse:
    """Response model for GET_BACKTEST_RUNTIME endpoint."""
    backtest_id: str
    execution_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: int
    trades: List[TradeResult]
    metrics: ExecutionMetrics
    final_balance: float
    initial_balance: float
    runtime_data: Dict[str, Any]
    chart_data: Optional[Dict[str, Any]] = None


@dataclass
class LogEntry:
    """Log entry model."""
    timestamp: datetime
    level: LogLevel
    message: str
    context: Dict[str, Any]


@dataclass
class BacktestLogsResponse:
    """Response model for GET_BACKTEST_LOGS endpoint."""
    backtest_id: str
    logs: List[LogEntry]
    total_count: int
    has_more: bool


@dataclass
class ChartDataPoint:
    """Chart data point."""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    indicators: Dict[str, float]


@dataclass
class BacktestChartResponse:
    """Response model for GET_BACKTEST_CHART_PARTITION endpoint."""
    backtest_id: str
    partition_index: int
    data_points: List[ChartDataPoint]
    total_partitions: int
    has_more: bool


@dataclass
class BacktestSummary:
    """Backtest summary for history."""
    backtest_id: str
    script_id: str
    script_name: str
    market_tag: str
    start_time: datetime
    end_time: datetime
    status: ExecutionStatus
    total_return: float
    max_drawdown: float
    total_trades: int
    created_at: datetime
    archived: bool


@dataclass
class BacktestHistoryResponse:
    """Response model for GET_BACKTEST_HISTORY endpoint."""
    backtests: List[BacktestSummary]
    total_count: int
    has_more: bool


@dataclass
class ArchiveBacktestResponse:
    """Response model for ARCHIVE_BACKTEST endpoint."""
    success: bool
    backtest_id: str
    archive_id: str
    archive_name: str
    archived_at: datetime
    error_message: Optional[str] = None


@dataclass
class DeleteBacktestResponse:
    """Response model for DELETE_BACKTEST endpoint."""
    success: bool
    backtest_id: str
    deleted_at: datetime
    error_message: Optional[str] = None


@dataclass
class RunningBacktest:
    """Running backtest information."""
    backtest_id: str
    execution_id: str
    script_name: str
    market_tag: str
    status: ExecutionStatus
    progress_percentage: float
    started_at: datetime
    estimated_completion: Optional[datetime]


@dataclass
class ExecutionBacktestsResponse:
    """Response model for EXECUTION_BACKTESTS endpoint."""
    running_backtests: List[RunningBacktest]
    completed_backtests: List[RunningBacktest]
    failed_backtests: List[RunningBacktest]
    total_count: int