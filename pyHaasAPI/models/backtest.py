"""
Backtest models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BacktestResult:
    """Backtest result"""
    backtest_id: str
    lab_id: str
    status: int
    generation_idx: int
    population_idx: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit: float
    total_fees: float
    roi: float
    parameters: Dict[str, Any]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class BacktestRuntimeData:
    """Backtest runtime data"""
    backtest_id: str
    lab_id: str
    script_name: str
    market_tag: str
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    pc_value: float
    avg_profit_per_trade: float
    profit_factor: float
    sharpe_ratio: float
    starting_balance: float
    final_balance: float
    peak_balance: float
    trades: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


@dataclass
class BacktestAnalysis:
    """Backtest analysis"""
    backtest_id: str
    lab_id: str
    generation_idx: Optional[int]
    population_idx: Optional[int]
    market_tag: str
    script_id: str
    script_name: str
    roi_percentage: float
    calculated_roi_percentage: float
    roi_difference: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    pc_value: float
    avg_profit_per_trade: float
    profit_factor: float
    sharpe_ratio: float
    starting_balance: float
    final_balance: float
    peak_balance: float
    analysis_timestamp: str
    parameter_values: Optional[Dict[str, str]] = None


@dataclass
class BacktestChart:
    """Backtest chart data"""
    backtest_id: str
    chart_data: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]
    created_at: datetime


@dataclass
class BacktestLog:
    """Backtest execution log"""
    backtest_id: str
    log_entries: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


@dataclass
class ExecuteBacktestRequest:
    """Execute backtest request"""
    lab_id: str
    script_id: str
    market: str
    parameters: Dict[str, Any]
    start_date: datetime
    end_date: datetime
    initial_balance: float = 10000.0
    leverage: float = 1.0
    fees: float = 0.001


@dataclass
class BacktestHistoryRequest:
    """Backtest history request"""
    lab_id: str
    page: int = 1
    page_size: int = 100
    sort_by: str = "roi"
    sort_order: str = "desc"
    filter_params: Optional[Dict[str, Any]] = None


@dataclass
class EditBacktestTagRequest:
    """Edit backtest tag request"""
    backtest_id: str
    tag: str


@dataclass
class ArchiveBacktestRequest:
    """Archive backtest request"""
    backtest_id: str
    archive: bool = True


@dataclass
class BacktestExecutionResult:
    """Backtest execution result"""
    backtest_id: str
    status: str
    message: str
    created_at: datetime
    estimated_duration: Optional[int] = None


@dataclass
class BacktestValidationResult:
    """Backtest validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
