"""
Report configuration settings
"""
import os
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum
from .env_utils import get_env

class ReportType(str, Enum):
    """Report type enumeration"""
    SHORT = "short"
    LONG = "long"
    BOT_RECOMMENDATIONS = "bot_recommendations"
    LAB_ANALYSIS = "lab_analysis"
    COMPARISON = "comparison"
    SUMMARY = "summary"

class ReportFormat(str, Enum):
    """Report format enumeration"""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    TXT = "txt"

@dataclass
class ReportConfig:
    """Report configuration settings"""
    
    # Default report settings
    default_format: ReportFormat = field(default_factory=lambda: ReportFormat.JSON) # env handled in post_init
    default_type: ReportType = field(default_factory=lambda: ReportType.SHORT) # env handled in post_init
    
    # Output directory
    output_directory: str = field(default_factory=lambda: get_env("REPORT_OUTPUT_DIRECTORY", "reports"))
    
    # Report content
    include_bot_recommendations: bool = field(default_factory=lambda: get_env("REPORT_INCLUDE_BOT_RECOMMENDATIONS", True, bool))
    include_performance_metrics: bool = field(default_factory=lambda: get_env("REPORT_INCLUDE_PERFORMANCE_METRICS", True, bool))
    include_risk_analysis: bool = field(default_factory=lambda: get_env("REPORT_INCLUDE_RISK_ANALYSIS", True, bool))
    include_detailed_breakdown: bool = field(default_factory=lambda: get_env("REPORT_INCLUDE_DETAILED_BREAKDOWN", False, bool))
    
    # Bot recommendation format
    bot_recommendation_format: str = field(default_factory=lambda: get_env(
        "REPORT_BOT_RECOMMENDATION_FORMAT",
        "Lab ID: {lab_id}, Backtest ID: {backtest_id}, Script: {script_name}, Market: {market_tag}, ROI: {roi}%, Win Rate: {win_rate}%, Trades: {trades}, Profit Factor: {profit_factor}, Sharpe: {sharpe_ratio}, Max DD: {max_drawdown}%, Risk: {risk_level}, Confidence: {confidence_score}%, Trade Amount: ${trade_amount}, Leverage: {leverage}x, Margin: {margin_mode}, Position: {position_mode}, Bot Name: {bot_name}"
    ))
    
    # Performance metrics to include
    performance_metrics: List[str] = field(default_factory=lambda: get_env(
        "REPORT_PERFORMANCE_METRICS",
        ["roi_percentage", "win_rate", "total_trades", "profit_factor", "sharpe_ratio", "max_drawdown"],
        list
    ))
    
    # Risk metrics to include
    risk_metrics: List[str] = field(default_factory=lambda: get_env(
        "REPORT_RISK_METRICS",
        ["max_drawdown", "risk_level", "confidence_score"],
        list
    ))
    
    # Bot configuration to include
    bot_config_metrics: List[str] = field(default_factory=lambda: get_env(
        "REPORT_BOT_CONFIG_METRICS",
        ["trade_amount", "leverage", "margin_mode", "position_mode"],
        list
    ))
    
    # Filtering and sorting
    sort_by: str = field(default_factory=lambda: get_env("REPORT_SORT_BY", "roi_percentage"))
    sort_order: str = field(default_factory=lambda: get_env("REPORT_SORT_ORDER", "desc"))
    max_results: int = field(default_factory=lambda: get_env("REPORT_MAX_RESULTS", 50, int))
    
    # File naming
    filename_template: str = field(default_factory=lambda: get_env(
        "REPORT_FILENAME_TEMPLATE",
        "{report_type}_{timestamp}_{lab_id}.{format}"
    ))
    timestamp_format: str = field(default_factory=lambda: get_env("REPORT_TIMESTAMP_FORMAT", "%Y%m%d_%H%M%S"))
    
    # CSV specific settings
    csv_delimiter: str = field(default_factory=lambda: get_env("REPORT_CSV_DELIMITER", ","))
    csv_quote_char: str = field(default_factory=lambda: get_env("REPORT_CSV_QUOTE_CHAR", '"'))
    csv_include_headers: bool = field(default_factory=lambda: get_env("REPORT_CSV_INCLUDE_HEADERS", True, bool))
    
    # HTML specific settings
    html_template: str = field(default_factory=lambda: get_env("REPORT_HTML_TEMPLATE", "default"))
    html_include_css: bool = field(default_factory=lambda: get_env("REPORT_HTML_INCLUDE_CSS", True, bool))
    html_include_js: bool = field(default_factory=lambda: get_env("REPORT_HTML_INCLUDE_JS", False, bool))
    
    # Markdown specific settings
    markdown_include_toc: bool = field(default_factory=lambda: get_env("REPORT_MARKDOWN_INCLUDE_TOC", True, bool))
    markdown_include_metadata: bool = field(default_factory=lambda: get_env("REPORT_MARKDOWN_INCLUDE_METADATA", True, bool))
    
    # JSON specific settings
    json_pretty_print: bool = field(default_factory=lambda: get_env("REPORT_JSON_PRETTY_PRINT", True, bool))
    json_include_metadata: bool = field(default_factory=lambda: get_env("REPORT_JSON_INCLUDE_METADATA", True, bool))
    
    def __post_init__(self):
        """Validate configuration"""
        
        # Manually handle Enum parsing from env which might differ from default values
        fmt_str = get_env("REPORT_DEFAULT_FORMAT")
        if fmt_str:
            self.default_format = self._parse_format(fmt_str)
            
        type_str = get_env("REPORT_DEFAULT_TYPE")
        if type_str:
            self.default_type = self._parse_type(type_str)

        self.validate_sort_by()
        self.validate_sort_order()
        self.validate_max_results()
        self.validate_csv_delimiter()
        self.validate_csv_quote_char()
        
    def _parse_format(self, v):
        if isinstance(v, str):
            try:
                return ReportFormat(v.lower())
            except ValueError:
                raise ValueError(f"Invalid report format: {v}. Valid formats: {[f.value for f in ReportFormat]}")
        return v
    
    def _parse_type(self, v):
        if isinstance(v, str):
            try:
                return ReportType(v.lower())
            except ValueError:
                raise ValueError(f"Invalid report type: {v}. Valid types: {[t.value for t in ReportType]}")
        return v

    def validate_sort_by(self):
        valid_fields = [
            "roi_percentage", "win_rate", "total_trades", "profit_factor", 
            "sharpe_ratio", "max_drawdown", "risk_level", "confidence_score"
        ]
        if self.sort_by not in valid_fields:
            # We allow it, but maybe warn? The original only raised ValueError.
            raise ValueError(f"Sort field must be one of: {valid_fields}")

    def validate_sort_order(self):
        valid_orders = ["asc", "desc"]
        if self.sort_order.lower() not in valid_orders:
            raise ValueError(f"Sort order must be one of: {valid_orders}")
        self.sort_order = self.sort_order.lower()

    def validate_max_results(self):
        if self.max_results <= 0:
            raise ValueError("Max results must be positive")

    def validate_csv_delimiter(self):
        if len(self.csv_delimiter) != 1:
            raise ValueError("CSV delimiter must be a single character")

    def validate_csv_quote_char(self):
        if len(self.csv_quote_char) != 1:
            raise ValueError("CSV quote character must be a single character")
    
    def get_filename(self, report_type: str, lab_id: str, format: str) -> str:
        """Generate filename using template"""
        from datetime import datetime
        timestamp = datetime.now().strftime(self.timestamp_format)
        
        try:
            return self.filename_template.format(
                report_type=report_type,
                timestamp=timestamp,
                lab_id=lab_id,
                format=format
            )
        except KeyError:
            # Fallback to simple naming
            return f"{report_type}_{timestamp}_{lab_id}.{format}"
    
    def get_bot_recommendation_text(self, **kwargs) -> str:
        """Generate bot recommendation text using template"""
        try:
            return self.bot_recommendation_format.format(**kwargs)
        except KeyError as e:
            # Fallback to simple format
            return f"Bot: {kwargs.get('script_name', 'Unknown')} - ROI: {kwargs.get('roi', 0)}%"
    
    def get_report_metrics(self) -> Dict[str, List[str]]:
        """Get all report metrics organized by category"""
        return {
            "performance": self.performance_metrics,
            "risk": self.risk_metrics,
            "bot_config": self.bot_config_metrics,
        }
    
    def should_include_section(self, section: str) -> bool:
        """Check if section should be included in report"""
        section_map = {
            "bot_recommendations": self.include_bot_recommendations,
            "performance_metrics": self.include_performance_metrics,
            "risk_analysis": self.include_risk_analysis,
            "detailed_breakdown": self.include_detailed_breakdown,
        }
        return section_map.get(section, True)
