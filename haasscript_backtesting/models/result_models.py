"""
Data models for backtest results and analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum


class TradeType(Enum):
    """Types of trades executed during backtesting."""
    ACTION_A = "action_a"
    ACTION_B = "action_b"
    ACTION_C = "action_c"
    ACTION_D = "action_d"


class TradeStatus(Enum):
    """Status of individual trades."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass
class Trade:
    """Individual trade executed during backtesting."""
    trade_id: str
    timestamp: datetime
    trade_type: TradeType
    price: float
    amount: float
    fee: float
    status: TradeStatus
    profit_loss: Optional[float] = None
    duration: Optional[timedelta] = None
    
    @property
    def value(self) -> float:
        """Calculate trade value."""
        return self.price * self.amount
    
    @property
    def net_value(self) -> float:
        """Calculate net trade value after fees."""
        return self.value - self.fee


@dataclass
class PerformanceData:
    """Detailed performance metrics and statistics."""
    initial_balance: float
    final_balance: float
    peak_balance: float
    lowest_balance: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    largest_win: float
    largest_loss: float
    average_win: float
    average_loss: float
    
    # Time-based metrics
    total_time_in_market: timedelta
    average_trade_duration: timedelta
    longest_winning_streak: int
    longest_losing_streak: int
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def profit_factor(self) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = self.winning_trades * self.average_win
        gross_loss = abs(self.losing_trades * self.average_loss)
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')


@dataclass
class ExecutionMetrics:
    """Standard execution performance metrics."""
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: timedelta
    volatility: float
    beta: float
    alpha: float
    
    # Risk metrics
    value_at_risk_95: float
    conditional_var_95: float
    calmar_ratio: float
    
    # Additional metrics
    profit_factor: float
    recovery_factor: float
    payoff_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_duration_days': self.max_drawdown_duration.days,
            'volatility': self.volatility,
            'beta': self.beta,
            'alpha': self.alpha,
            'value_at_risk_95': self.value_at_risk_95,
            'conditional_var_95': self.conditional_var_95,
            'calmar_ratio': self.calmar_ratio,
            'profit_factor': self.profit_factor,
            'recovery_factor': self.recovery_factor,
            'payoff_ratio': self.payoff_ratio,
        }


@dataclass
class ChartData:
    """Chart data for visualization (optional)."""
    timestamps: List[datetime]
    equity_curve: List[float]
    drawdown_curve: List[float]
    trade_markers: List[Dict[str, Any]]
    indicators: Dict[str, List[float]] = field(default_factory=dict)
    
    def add_indicator(self, name: str, values: List[float]) -> None:
        """Add indicator data to chart."""
        self.indicators[name] = values


@dataclass
class ProcessedResults:
    """Complete processed results from a backtest execution."""
    backtest_id: str
    script_id: str
    execution_summary: 'ExecutionSummary'  # Forward reference
    execution_metrics: ExecutionMetrics
    performance_data: PerformanceData
    trade_history: List[Trade]
    chart_data: Optional[ChartData] = None
    
    # Raw data from HaasOnline API
    raw_runtime_data: Dict[str, Any] = field(default_factory=dict)
    raw_logs: List[str] = field(default_factory=list)
    
    # Processing metadata
    processed_at: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    
    @property
    def has_trades(self) -> bool:
        """Check if results contain trade data."""
        return len(self.trade_history) > 0
    
    @property
    def is_profitable(self) -> bool:
        """Check if backtest was profitable."""
        return self.execution_metrics.total_return > 0
    
    def get_trade_summary(self) -> Dict[str, Any]:
        """Get summary of trade statistics."""
        return {
            'total_trades': len(self.trade_history),
            'profitable_trades': len([t for t in self.trade_history if t.profit_loss and t.profit_loss > 0]),
            'total_volume': sum(t.value for t in self.trade_history),
            'total_fees': sum(t.fee for t in self.trade_history),
            'average_trade_size': sum(t.amount for t in self.trade_history) / len(self.trade_history) if self.trade_history else 0,
        }