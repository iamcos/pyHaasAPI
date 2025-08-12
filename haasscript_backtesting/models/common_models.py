"""
Common data models shared across the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(Enum):
    """Log levels for system logging."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Individual log entry from system operations."""
    timestamp: datetime
    level: LogLevel
    message: str
    component: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'component': self.component,
            'context': self.context
        }


@dataclass
class ResourceUsage:
    """System resource usage metrics."""
    cpu_percent: float
    memory_mb: float
    disk_io_mb: float
    network_io_mb: float
    active_connections: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource usage to dictionary."""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'disk_io_mb': self.disk_io_mb,
            'network_io_mb': self.network_io_mb,
            'active_connections': self.active_connections,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class BacktestSummary:
    """Summary information for backtest history."""
    backtest_id: str
    script_name: str
    market_tag: str
    start_date: datetime
    end_date: datetime
    status: str
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            'backtest_id': self.backtest_id,
            'script_name': self.script_name,
            'market_tag': self.market_tag,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'status': self.status,
            'total_return': self.total_return,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ValidationResult:
    """Result of validation operations."""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add an error to the result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the result."""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str):
        """Add a suggestion to the result."""
        self.suggestions.append(suggestion)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'suggestions': self.suggestions
        }


@dataclass
class DebugResult:
    """Result of debug operations."""
    success: bool
    execution_time_ms: float
    memory_usage_mb: float
    output_logs: list[str] = field(default_factory=list)
    error_logs: list[str] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    def add_output_log(self, log: str):
        """Add an output log entry."""
        self.output_logs.append(log)
    
    def add_error_log(self, log: str):
        """Add an error log entry."""
        self.error_logs.append(log)
        self.success = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert debug result to dictionary."""
        return {
            'success': self.success,
            'execution_time_ms': self.execution_time_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'output_logs': self.output_logs,
            'error_logs': self.error_logs,
            'debug_info': self.debug_info
        }


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    uptime: float  # seconds
    active_backtests: int
    queued_backtests: int
    resource_usage: ResourceUsage
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    
    @property
    def is_healthy(self) -> bool:
        """Check if system is in healthy state."""
        return self.status == 'healthy'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health status to dictionary."""
        return {
            'status': self.status,
            'uptime': self.uptime,
            'active_backtests': self.active_backtests,
            'queued_backtests': self.queued_backtests,
            'resource_usage': self.resource_usage.to_dict(),
            'last_error': self.last_error,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None
        }