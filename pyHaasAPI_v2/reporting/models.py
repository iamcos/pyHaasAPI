"""
Data models for the flexible reporting system
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class BacktestSummary:
    """Summary of a backtest for reporting"""
    backtest_id: str
    lab_id: str
    generation_idx: Optional[int] = None
    population_idx: Optional[int] = None
    market_tag: str = ""
    script_id: str = ""
    script_name: str = ""
    
    # Performance metrics
    roi_percentage: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    max_drawdown: float = 0.0
    realized_profits_usdt: float = 0.0
    pc_value: float = 0.0
    avg_profit_per_trade: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Additional metrics
    analysis_timestamp: str = ""
    duration_days: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class LabSummary:
    """Summary of a lab for reporting"""
    lab_id: str
    lab_name: str
    script_id: str
    script_name: str
    market_tag: str
    status: str = ""
    total_backtests: int = 0
    analyzed_backtests: int = 0
    
    # Aggregated metrics
    avg_roi: float = 0.0
    max_roi: float = 0.0
    min_roi: float = 0.0
    avg_win_rate: float = 0.0
    avg_trades: float = 0.0
    avg_profit_factor: float = 0.0
    
    # Top performers
    top_backtests: List[BacktestSummary] = field(default_factory=list)
    
    # Analysis metadata
    analysis_timestamp: str = ""
    analysis_duration: Optional[float] = None


@dataclass
class BotRecommendation:
    """Bot creation recommendation with detailed stats"""
    # Identifiers
    lab_id: str
    lab_name: str
    backtest_id: str
    script_id: str
    script_name: str
    market_tag: str
    
    # Performance stats
    roi_percentage: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    realized_profits_usdt: float
    profit_factor: float
    sharpe_ratio: float
    
    # Bot configuration
    recommended_trade_amount_usdt: float = 2000.0
    recommended_leverage: float = 20.0
    recommended_margin_mode: str = "CROSS"
    recommended_position_mode: str = "HEDGE"
    
    # Bot naming
    formatted_bot_name: str = ""
    generation_info: str = ""  # e.g., "pop/gen" format
    
    # Risk assessment
    risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    confidence_score: float = 0.0  # 0.0 to 1.0
    
    # Additional metadata
    recommendation_timestamp: str = ""
    priority_score: float = 0.0  # For ranking recommendations


@dataclass
class AnalysisReport:
    """Complete analysis report with multiple sections"""
    # Report metadata
    report_id: str
    report_type: str
    generated_at: datetime
    generated_by: str = "pyHaasAPI v2"
    
    # Analysis summary
    total_labs_analyzed: int = 0
    total_backtests_analyzed: int = 0
    analysis_duration: Optional[float] = None
    
    # Lab summaries
    lab_summaries: List[LabSummary] = field(default_factory=list)
    
    # Bot recommendations
    bot_recommendations: List[BotRecommendation] = field(default_factory=list)
    
    # Aggregated statistics
    overall_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Configuration used
    report_config: Dict[str, Any] = field(default_factory=dict)
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonReport:
    """Report for comparing multiple labs or backtests"""
    report_id: str
    generated_at: datetime
    
    # Comparison data
    comparison_type: str  # "labs", "backtests", "strategies"
    items_compared: List[Dict[str, Any]] = field(default_factory=list)
    
    # Comparison metrics
    comparison_metrics: Dict[str, List[float]] = field(default_factory=dict)
    
    # Rankings
    rankings: Dict[str, List[str]] = field(default_factory=dict)
    
    # Recommendations
    best_performers: List[Dict[str, Any]] = field(default_factory=list)
    worst_performers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Statistical analysis
    statistical_summary: Dict[str, Any] = field(default_factory=dict)

