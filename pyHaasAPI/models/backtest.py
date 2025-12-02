"""
Backtest models for pyHaasAPI v2

Stub models for backtest-related data structures.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class BacktestResult:
    """Backtest result model"""
    backtest_id: str = ""
    lab_id: str = ""
    status: int = 0
    generation_idx: int = 0
    population_idx: int = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_fees: float = 0.0
    roi: float = 0.0
    parameters: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class BacktestRuntimeData:
    """Backtest runtime data model"""
    backtest_id: str = ""
    lab_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestChart:
    """Backtest chart data model"""
    backtest_id: str = ""
    chart_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestLog:
    """Backtest log model"""
    backtest_id: str = ""
    log_entries: List[str] = field(default_factory=list)


@dataclass
class ExecuteBacktestRequest:
    """Execute backtest request model"""
    lab_id: str = ""
    script_id: str = ""
    market: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestHistoryRequest:
    """Backtest history request model"""
    market: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class EditBacktestTagRequest:
    """Edit backtest tag request model"""
    backtest_id: str = ""
    tag: str = ""


@dataclass
class ArchiveBacktestRequest:
    """Archive backtest request model"""
    backtest_id: str = ""
    archive_result: bool = False


@dataclass
class BacktestExecutionResult:
    """Backtest execution result model"""
    success: bool = False
    backtest_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class BacktestValidationResult:
    """Backtest validation result model"""
    valid: bool = False
    errors: List[str] = field(default_factory=list)


@dataclass
class BacktestAnalysis:
    """Backtest analysis model"""
    backtest_id: str = ""
    analysis_data: Dict[str, Any] = field(default_factory=dict)

