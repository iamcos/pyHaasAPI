"""
Backtest models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from .common import BaseModel


@dataclass
class BacktestResult(BaseModel):
    """Backtest result"""
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
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BacktestRuntimeData(BaseModel):
    """Backtest runtime data"""
    backtest_id: str = ""
    lab_id: str = ""
    script_name: str = ""
    market_tag: str = ""
    roi_percentage: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    max_drawdown: float = 0.0
    realized_profits_usdt: float = 0.0
    pc_value: float = 0.0
    avg_profit_per_trade: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    starting_balance: float = 0.0
    final_balance: float = 0.0
    peak_balance: float = 0.0
    trades: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BacktestAnalysis(BaseModel):
    """Backtest analysis"""
    backtest_id: str = ""
    lab_id: str = ""
    generation_idx: Optional[int] = None
    population_idx: Optional[int] = None
    market_tag: str = ""
    script_id: str = ""
    script_name: str = ""
    roi_percentage: float = 0.0
    calculated_roi_percentage: float = 0.0
    roi_difference: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    max_drawdown: float = 0.0
    realized_profits_usdt: float = 0.0
    pc_value: float = 0.0
    avg_profit_per_trade: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    starting_balance: float = 0.0
    final_balance: float = 0.0
    peak_balance: float = 0.0
    analysis_timestamp: str = ""
    parameter_values: Optional[Dict[str, str]] = None


@dataclass
class BacktestChart(BaseModel):
    """Backtest chart data"""
    backtest_id: str = ""
    chart_data: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    drawdown_curve: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BacktestLog(BaseModel):
    """Backtest execution log"""
    backtest_id: str = ""
    log_entries: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecuteBacktestRequest(BaseModel):
    """Execute backtest request"""
    lab_id: str = ""
    script_id: str = ""
    market: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    initial_balance: float = 10000.0
    leverage: float = 1.0
    fees: float = 0.001


@dataclass
class BacktestHistoryRequest(BaseModel):
    """Backtest history request"""
    lab_id: str = ""
    page: int = 1
    page_size: int = 100
    sort_by: str = "roi"
    sort_order: str = "desc"
    filter_params: Optional[Dict[str, Any]] = None


@dataclass
class EditBacktestTagRequest(BaseModel):
    """Edit backtest tag request"""
    backtest_id: str = ""
    tag: str = ""


@dataclass
class ArchiveBacktestRequest(BaseModel):
    """Archive backtest request"""
    backtest_id: str = ""
    archive: bool = True


@dataclass
class BacktestExecutionResult(BaseModel):
    """Backtest execution result"""
    backtest_id: str = ""
    status: str = ""
    message: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    estimated_duration: Optional[int] = None


@dataclass
class BacktestValidationResult(BaseModel):
    """Backtest validation result"""
    is_valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
