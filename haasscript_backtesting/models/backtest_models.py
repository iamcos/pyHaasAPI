"""
Data models for backtest configuration and execution tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum

from .common_models import ResourceUsage


class ExecutionStatusType(Enum):
    """Possible backtest execution statuses."""
    QUEUED = "queued"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class PositionMode(Enum):
    """Position modes for backtesting."""
    LONG_ONLY = 0
    SHORT_ONLY = 1
    LONG_SHORT = 2


@dataclass
class BacktestConfig:
    """Configuration for a backtest execution."""
    script_id: str
    account_id: str
    market_tag: str
    start_time: int  # Unix timestamp
    end_time: int    # Unix timestamp
    interval: int    # Candle interval in minutes
    execution_amount: float
    script_parameters: Dict[str, Any]
    leverage: int = 0
    position_mode: PositionMode = PositionMode.LONG_ONLY
    
    # Optional advanced settings
    slippage: float = 0.0
    commission: float = 0.0
    max_concurrent_positions: int = 1
    
    def validate(self) -> bool:
        """Validate backtest configuration parameters."""
        if self.start_time >= self.end_time:
            return False
        if self.execution_amount <= 0:
            return False
        if self.interval <= 0:
            return False
        return True
    
    @property
    def duration_days(self) -> int:
        """Calculate backtest duration in days."""
        return (self.end_time - self.start_time) // (24 * 3600)





@dataclass
class ExecutionStatus:
    """Current status of a backtest execution."""
    status: ExecutionStatusType
    progress_percentage: float
    current_phase: str
    estimated_completion: Optional[datetime]
    resource_usage: ResourceUsage
    last_update: datetime = field(default_factory=datetime.now)
    
    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status == ExecutionStatusType.RUNNING
    
    @property
    def is_complete(self) -> bool:
        """Check if execution has completed successfully."""
        return self.status == ExecutionStatusType.COMPLETED
    
    @property
    def has_failed(self) -> bool:
        """Check if execution has failed."""
        return self.status == ExecutionStatusType.FAILED


@dataclass
class BacktestExecution:
    """Represents a backtest execution with its current state."""
    backtest_id: str
    script_id: str
    config: BacktestConfig
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    execution_id: Optional[str] = None  # HaasOnline execution ID
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate execution duration."""
        if self.completed_at:
            return self.completed_at - self.started_at
        return datetime.now() - self.started_at
    
    @property
    def can_retry(self) -> bool:
        """Check if execution can be retried."""
        return self.retry_count < self.max_retries and self.status.has_failed


@dataclass
class ExecutionSummary:
    """Summary of backtest execution results."""
    backtest_id: str
    script_name: str
    market_tag: str
    start_date: datetime
    end_date: datetime
    duration: timedelta
    total_trades: int
    success_rate: float
    final_balance: float
    max_drawdown: float
    execution_time: timedelta


@dataclass
class BacktestSummary:
    """Summary of a backtest for history tracking."""
    backtest_id: str
    script_name: str
    market_tag: str
    start_date: datetime
    end_date: datetime
    status: str
    created_at: datetime = field(default_factory=datetime.now)
    duration: Optional[timedelta] = None
    total_trades: Optional[int] = None
    final_balance: Optional[float] = None