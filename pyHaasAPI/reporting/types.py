"""
Report types and enums for the flexible reporting system
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


class ReportType(Enum):
    """Types of reports that can be generated"""
    SHORT = "short"           # Brief summary with key metrics
    LONG = "long"             # Detailed analysis with full metrics
    BOT_RECOMMENDATIONS = "bot_recommendations"  # Bot creation recommendations
    LAB_ANALYSIS = "lab_analysis"                # Lab performance analysis
    COMPARISON = "comparison"  # Compare multiple labs/backtests
    SUMMARY = "summary"       # High-level overview


class ReportFormat(Enum):
    """Output formats for reports"""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    TXT = "txt"


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    report_type: ReportType = ReportType.SHORT
    formats: List[ReportFormat] = None
    include_bot_recommendations: bool = True
    include_detailed_metrics: bool = False
    include_charts: bool = False
    max_recommendations: int = 10
    sort_by: str = "roi"  # roi, win_rate, profit_factor, sharpe_ratio
    sort_descending: bool = True
    filter_min_roi: Optional[float] = None
    filter_min_win_rate: Optional[float] = None
    filter_min_trades: Optional[int] = None
    output_dir: str = "reports"
    filename_prefix: str = "analysis_report"
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = [ReportFormat.JSON, ReportFormat.CSV]


@dataclass
class BotRecommendationConfig:
    """Configuration for bot recommendations"""
    include_stats: bool = True
    include_lab_id: bool = True
    include_backtest_id: bool = True
    include_script_name: bool = True
    include_market_tag: bool = True
    include_performance_metrics: bool = True
    include_risk_metrics: bool = True
    include_trade_amount: bool = True
    include_account_assignment: bool = True
    format_bot_name: bool = True  # Format: "LabName - ScriptName - ROI pop/gen WR%"
    
    # Bot configuration defaults
    default_trade_amount_usdt: float = 2000.0
    default_leverage: float = 20.0
    default_margin_mode: str = "CROSS"
    default_position_mode: str = "HEDGE"

