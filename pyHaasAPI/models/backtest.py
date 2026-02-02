"""
Backtest models for pyHaasAPI v2
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from .common import BaseModel
from .trade import Trade


@dataclass
class BacktestResult(BaseModel):
    """Backtest result"""
    backtest_id: str = ""
    log_id: str = ""
    lab_id: str = ""
    status: int = 0
    generation_idx: int = 0
    population_idx: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    
    # Summary Metrics (can be populated from API or computed)
    roi: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    total_fees: float = 0.0
    net_profit: float = 0.0
    max_drawdown: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def compute_metrics(self) -> None:
        """Compute metrics from trades list if available."""
        if not self.trades:
            return
        self.total_trades = len(self.trades)
        self.winning_trades = sum(1 for t in self.trades if t.is_win)
        self.losing_trades = self.total_trades - self.winning_trades
        self.win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        self.total_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        self.total_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        self.total_fees = sum(t.fees for t in self.trades)
        self.net_profit = sum(t.net_profit for t in self.trades)
        self.roi = (self.net_profit / self.starting_balance * 100) if self.starting_balance > 0 else 0.0
    
    @property
    def starting_balance(self) -> float:
        return self.settings.get("initial_balance", 10000.0)


@dataclass
class BacktestRuntimeData(BaseModel):
    """Backtest runtime data"""
    backtest_id: str = ""
    log_id: str = ""
    lab_id: str = ""
    script_name: str = ""
    market_tag: str = ""
    pc_value: float = 0.0
    sharpe_ratio: float = 0.0
    starting_balance: float = 0.0
    trades: List[Trade] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        winning = sum(1 for t in self.trades if t.is_win)
        return (winning / len(self.trades)) * 100.0

    @property
    def roi_percentage(self) -> float:
        if self.starting_balance <= 0 or not self.trades:
            return 0.0
        net_profit = sum(t.net_profit for t in self.trades)
        return (net_profit / self.starting_balance) * 100.0

    @property
    def realized_profits_usdt(self) -> float:
        return sum(t.net_profit for t in self.trades)

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        return gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    @property
    def avg_profit_per_trade(self) -> float:
        return self.realized_profits_usdt / len(self.trades) if self.trades else 0.0

    @property
    def max_drawdown(self) -> float:
        if not self.trades:
            return 0.0
        balance = self.starting_balance
        peak = self.starting_balance
        mdd = 0.0
        for t in self.trades:
            balance += t.net_profit
            peak = max(peak, balance)
            drawdown = (peak - balance) / peak if peak > 0 else 0.0
            mdd = max(mdd, drawdown)
        return mdd * 100.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BacktestAnalysis(BaseModel):
    """Backtest analysis"""
    backtest_id: str = ""
    log_id: str = ""
    lab_id: str = ""
    generation_idx: Optional[int] = None
    population_idx: Optional[int] = None
    market_tag: str = ""
    script_id: str = ""
    script_name: str = ""
    analysis_timestamp: str = ""
    parameter_values: Optional[Dict[str, str]] = None
    trades: List[Trade] = field(default_factory=list)

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        winning = sum(1 for t in self.trades if t.is_win)
        return (winning / len(self.trades)) * 100.0

    @property
    def roi_percentage(self) -> float:
        if self.starting_balance <= 0 or not self.trades:
            return 0.0
        net_profit = sum(t.net_profit for t in self.trades)
        return (net_profit / self.starting_balance) * 100.0

    @property
    def realized_profits_usdt(self) -> float:
        return sum(t.net_profit for t in self.trades)

    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.profit_loss for t in self.trades if t.profit_loss > 0)
        gross_loss = abs(sum(t.profit_loss for t in self.trades if t.profit_loss < 0))
        return gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

    @property
    def avg_profit_per_trade(self) -> float:
        return self.realized_profits_usdt / len(self.trades) if self.trades else 0.0

    @property
    def max_drawdown(self) -> float:
        if not self.trades:
            return 0.0
        balance = self.starting_balance
        peak = self.starting_balance
        mdd = 0.0
        for t in self.trades:
            balance += t.net_profit
            peak = max(peak, balance)
            drawdown = (peak - balance) / peak if peak > 0 else 0.0
            mdd = max(mdd, drawdown)
        return mdd * 100.0

    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        winning = sum(1 for t in self.trades if t.is_win)
        return (winning / len(self.trades)) * 100.0

    @property
    def roi_percentage(self) -> float:
        if self.starting_balance <= 0 or not self.trades:
            return 0.0
        net_profit = sum(t.net_profit for t in self.trades)
        return (net_profit / self.starting_balance) * 100.0


@dataclass
class BacktestChart(BaseModel):
    """Backtest chart data"""
    backtest_id: str = ""
    log_id: str = ""
    chart_data: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    drawdown_curve: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BacktestLog(BaseModel):
    """Backtest execution log"""
    backtest_id: str = ""
    log_id: str = ""
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
    log_id: str = ""
    tag: str = ""


@dataclass
class ArchiveBacktestRequest(BaseModel):
    """Archive backtest request"""
    backtest_id: str = ""
    log_id: str = ""
    archive: bool = True


@dataclass
class BacktestExecutionResult(BaseModel):
    """Backtest execution result"""
    backtest_id: str = ""
    log_id: str = ""
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
