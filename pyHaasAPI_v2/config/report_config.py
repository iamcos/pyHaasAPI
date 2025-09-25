"""
Report configuration settings
"""

from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from enum import Enum


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


class ReportConfig(BaseSettings):
    """Report configuration settings"""
    
    # Default report settings
    default_format: ReportFormat = Field(default=ReportFormat.JSON, env="REPORT_DEFAULT_FORMAT")
    default_type: ReportType = Field(default=ReportType.SHORT, env="REPORT_DEFAULT_TYPE")
    
    # Output directory
    output_directory: str = Field(default="reports", env="REPORT_OUTPUT_DIRECTORY")
    
    # Report content
    include_bot_recommendations: bool = Field(default=True, env="REPORT_INCLUDE_BOT_RECOMMENDATIONS")
    include_performance_metrics: bool = Field(default=True, env="REPORT_INCLUDE_PERFORMANCE_METRICS")
    include_risk_analysis: bool = Field(default=True, env="REPORT_INCLUDE_RISK_ANALYSIS")
    include_detailed_breakdown: bool = Field(default=False, env="REPORT_INCLUDE_DETAILED_BREAKDOWN")
    
    # Bot recommendation format
    bot_recommendation_format: str = Field(
        default="Lab ID: {lab_id}, Backtest ID: {backtest_id}, Script: {script_name}, Market: {market_tag}, ROI: {roi}%, Win Rate: {win_rate}%, Trades: {trades}, Profit Factor: {profit_factor}, Sharpe: {sharpe_ratio}, Max DD: {max_drawdown}%, Risk: {risk_level}, Confidence: {confidence_score}%, Trade Amount: ${trade_amount}, Leverage: {leverage}x, Margin: {margin_mode}, Position: {position_mode}, Bot Name: {bot_name}",
        env="REPORT_BOT_RECOMMENDATION_FORMAT"
    )
    
    # Performance metrics to include
    performance_metrics: List[str] = Field(
        default=["roi_percentage", "win_rate", "total_trades", "profit_factor", "sharpe_ratio", "max_drawdown"],
        env="REPORT_PERFORMANCE_METRICS"
    )
    
    # Risk metrics to include
    risk_metrics: List[str] = Field(
        default=["max_drawdown", "risk_level", "confidence_score"],
        env="REPORT_RISK_METRICS"
    )
    
    # Bot configuration to include
    bot_config_metrics: List[str] = Field(
        default=["trade_amount", "leverage", "margin_mode", "position_mode"],
        env="REPORT_BOT_CONFIG_METRICS"
    )
    
    # Filtering and sorting
    sort_by: str = Field(default="roi_percentage", env="REPORT_SORT_BY")
    sort_order: str = Field(default="desc", env="REPORT_SORT_ORDER")
    max_results: int = Field(default=50, env="REPORT_MAX_RESULTS")
    
    # File naming
    filename_template: str = Field(
        default="{report_type}_{timestamp}_{lab_id}.{format}",
        env="REPORT_FILENAME_TEMPLATE"
    )
    timestamp_format: str = Field(default="%Y%m%d_%H%M%S", env="REPORT_TIMESTAMP_FORMAT")
    
    # CSV specific settings
    csv_delimiter: str = Field(default=",", env="REPORT_CSV_DELIMITER")
    csv_quote_char: str = Field(default='"', env="REPORT_CSV_QUOTE_CHAR")
    csv_include_headers: bool = Field(default=True, env="REPORT_CSV_INCLUDE_HEADERS")
    
    # HTML specific settings
    html_template: str = Field(default="default", env="REPORT_HTML_TEMPLATE")
    html_include_css: bool = Field(default=True, env="REPORT_HTML_INCLUDE_CSS")
    html_include_js: bool = Field(default=False, env="REPORT_HTML_INCLUDE_JS")
    
    # Markdown specific settings
    markdown_include_toc: bool = Field(default=True, env="REPORT_MARKDOWN_INCLUDE_TOC")
    markdown_include_metadata: bool = Field(default=True, env="REPORT_MARKDOWN_INCLUDE_METADATA")
    
    # JSON specific settings
    json_pretty_print: bool = Field(default=True, env="REPORT_JSON_PRETTY_PRINT")
    json_include_metadata: bool = Field(default=True, env="REPORT_JSON_INCLUDE_METADATA")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"    
    @field_validator("default_format")
    @classmethod
    def validate_format(cls, v):
        """Validate report format"""
        if isinstance(v, str):
            try:
                return ReportFormat(v.lower())
            except ValueError:
                raise ValueError(f"Invalid report format: {v}. Valid formats: {[f.value for f in ReportFormat]}")
        return v
    
    @field_validator("default_type")
    @classmethod
    def validate_type(cls, v):
        """Validate report type"""
        if isinstance(v, str):
            try:
                return ReportType(v.lower())
            except ValueError:
                raise ValueError(f"Invalid report type: {v}. Valid types: {[t.value for t in ReportType]}")
        return v
    
    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v):
        """Validate sort field"""
        valid_fields = [
            "roi_percentage", "win_rate", "total_trades", "profit_factor", 
            "sharpe_ratio", "max_drawdown", "risk_level", "confidence_score"
        ]
        if v not in valid_fields:
            raise ValueError(f"Sort field must be one of: {valid_fields}")
        return v
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v):
        """Validate sort order"""
        valid_orders = ["asc", "desc"]
        if v.lower() not in valid_orders:
            raise ValueError(f"Sort order must be one of: {valid_orders}")
        return v.lower()
    
    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v):
        """Validate max results"""
        if v <= 0:
            raise ValueError("Max results must be positive")
        return v
    
    @field_validator("csv_delimiter")
    @classmethod
    def validate_csv_delimiter(cls, v):
        """Validate CSV delimiter"""
        if len(v) != 1:
            raise ValueError("CSV delimiter must be a single character")
        return v
    
    @field_validator("csv_quote_char")
    @classmethod
    def validate_csv_quote_char(cls, v):
        """Validate CSV quote character"""
        if len(v) != 1:
            raise ValueError("CSV quote character must be a single character")
        return v
    
    @field_validator("performance_metrics", "risk_metrics", "bot_config_metrics")
    @classmethod
    def validate_metrics_lists(cls, v):
        """Validate metrics lists"""
        if not isinstance(v, list):
            raise ValueError("Metrics must be a list")
        return v
    
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
