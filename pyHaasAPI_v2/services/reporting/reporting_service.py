"""
Reporting Service for pyHaasAPI v2

Provides business logic for report generation with multiple output formats
and configurable content as requested by the user.
"""

import json
import csv
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ...services.analysis import AnalysisReport, BacktestPerformance, LabAnalysisResult
from ...services.bot import BotCreationResult, MassBotCreationResult, BotValidationResult
from ...exceptions import AnalysisError
from ...core.logging import get_logger


class ReportType(Enum):
    """Report type definitions"""
    SHORT = "short"
    LONG = "long"
    BOT_RECOMMENDATIONS = "bot_recommendations"
    LAB_ANALYSIS = "lab_analysis"
    COMPARISON = "comparison"
    SUMMARY = "summary"
    WFO_ANALYSIS = "wfo_analysis"


class ReportFormat(Enum):
    """Report format definitions"""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    TXT = "txt"


@dataclass
class ReportConfig:
    """Report configuration"""
    report_type: ReportType
    format: ReportFormat
    include_bot_recommendations: bool = True
    include_performance_metrics: bool = True
    include_risk_metrics: bool = True
    include_recommendations: bool = True
    sort_by: str = "roe"  # roi, roe, winrate, profit, trades
    filter_min_roi: Optional[float] = None
    filter_min_winrate: Optional[float] = None
    filter_min_trades: Optional[int] = None
    max_results: Optional[int] = None
    output_directory: str = "reports"
    filename_template: str = "{report_type}_{timestamp}"


@dataclass
class ReportResult:
    """Result of report generation"""
    report_path: str
    report_type: ReportType
    format: ReportFormat
    total_items: int
    generated_at: datetime
    success: bool
    error_message: Optional[str] = None


class ReportingService:
    """
    Reporting Service for generating flexible reports
    
    Provides multiple output formats (JSON, CSV, Markdown, HTML, TXT) with
    configurable content including bot recommendations, performance metrics,
    and risk analysis as requested by the user.
    """
    
    def __init__(self):
        self.logger = get_logger("reporting_service")
    
    async def generate_analysis_report(
        self,
        analysis_results: List[LabAnalysisResult],
        config: ReportConfig
    ) -> ReportResult:
        """
        Generate analysis report with multiple output formats
        
        Args:
            analysis_results: List of analysis results to include
            config: Report configuration
            
        Returns:
            Path to generated report file
        """
        try:
            self.logger.info(f"Generating {config.report_type.value} report in {config.format.value} format")
            
            # Filter and sort results
            filtered_results = self._filter_analysis_results(analysis_results, config)
            sorted_results = self._sort_analysis_results(filtered_results, config.sort_by)
            
            # Limit results if specified
            if config.max_results:
                sorted_results = sorted_results[:config.max_results]
            
            # Generate report content
            if config.format == ReportFormat.JSON:
                content = self._generate_json_report(sorted_results, config)
            elif config.format == ReportFormat.CSV:
                content = self._generate_csv_report(sorted_results, config)
            elif config.format == ReportFormat.MARKDOWN:
                content = self._generate_markdown_report(sorted_results, config)
            elif config.format == ReportFormat.HTML:
                content = self._generate_html_report(sorted_results, config)
            elif config.format == ReportFormat.TXT:
                content = self._generate_txt_report(sorted_results, config)
            else:
                raise ValueError(f"Unsupported report format: {config.format}")
            
            # Save report to file
            report_path = self._save_report(content, config)
            
            self.logger.info(f"Report generated successfully: {report_path}")
            return ReportResult(
                report_path=report_path,
                report_type=config.report_type,
                format=config.format,
                total_items=len(sorted_results),
                generated_at=datetime.now(),
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate analysis report: {e}")
            raise AnalysisError(f"Failed to generate analysis report: {e}")
    
    async def generate_bot_recommendations_report(
        self,
        recommendations: List[Dict[str, Any]],
        config: ReportConfig
    ) -> ReportResult:
        """
        Generate bot recommendations report with user-requested format
        
        Args:
            recommendations: List of bot recommendations
            config: Report configuration
            
        Returns:
            Path to generated report file
        """
        try:
            self.logger.info(f"Generating bot recommendations report in {config.format.value} format")
            
            # Filter recommendations
            filtered_recommendations = self._filter_bot_recommendations(recommendations, config)
            
            # Generate report content
            if config.format == ReportFormat.JSON:
                content = self._generate_bot_recommendations_json(filtered_recommendations, config)
            elif config.format == ReportFormat.CSV:
                content = self._generate_bot_recommendations_csv(filtered_recommendations, config)
            elif config.format == ReportFormat.MARKDOWN:
                content = self._generate_bot_recommendations_markdown(filtered_recommendations, config)
            elif config.format == ReportFormat.HTML:
                content = self._generate_bot_recommendations_html(filtered_recommendations, config)
            elif config.format == ReportFormat.TXT:
                content = self._generate_bot_recommendations_txt(filtered_recommendations, config)
            else:
                raise ValueError(f"Unsupported report format: {config.format}")
            
            # Save report to file
            report_path = self._save_report(content, config)
            
            self.logger.info(f"Bot recommendations report generated successfully: {report_path}")
            return ReportResult(
                report_path=report_path,
                report_type=config.report_type,
                format=config.format,
                total_items=len(filtered_recommendations),
                generated_at=datetime.now(),
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate bot recommendations report: {e}")
            raise AnalysisError(f"Failed to generate bot recommendations report: {e}")
    
    def _filter_analysis_results(
        self,
        results: List[LabAnalysisResult],
        config: ReportConfig
    ) -> List[LabAnalysisResult]:
        """Filter analysis results based on configuration"""
        filtered = []
        
        for result in results:
            if config.filter_min_roi and result.average_roi < config.filter_min_roi:
                continue
            if config.filter_min_winrate and result.average_win_rate < config.filter_min_winrate:
                continue
            if config.filter_min_trades and result.total_trades < config.filter_min_trades:
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _sort_analysis_results(
        self,
        results: List[LabAnalysisResult],
        sort_by: str
    ) -> List[LabAnalysisResult]:
        """Sort analysis results based on specified criteria"""
        if sort_by == "roi":
            return sorted(results, key=lambda x: x.average_roi, reverse=True)
        elif sort_by == "roe":
            return sorted(results, key=lambda x: x.average_roi, reverse=True)  # Same as ROI for now
        elif sort_by == "winrate":
            return sorted(results, key=lambda x: x.average_win_rate, reverse=True)
        elif sort_by == "profit":
            return sorted(results, key=lambda x: x.total_trades, reverse=True)  # Using trades as proxy
        elif sort_by == "trades":
            return sorted(results, key=lambda x: x.total_trades, reverse=True)
        else:
            return results
    
    def _filter_bot_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        config: ReportConfig
    ) -> List[Dict[str, Any]]:
        """Filter bot recommendations based on configuration"""
        filtered = []
        
        for rec in recommendations:
            if config.filter_min_roi and rec.roi_percentage < config.filter_min_roi:
                continue
            if config.filter_min_winrate and rec.win_rate < config.filter_min_winrate:
                continue
            if config.filter_min_trades and rec.total_trades < config.filter_min_trades:
                continue
            
            filtered.append(rec)
        
        return filtered
    
    def _generate_json_report(
        self,
        results: List[LabAnalysisResult],
        config: ReportConfig
    ) -> str:
        """Generate JSON report"""
        report_data = {
            "report_type": config.report_type.value,
            "format": config.format.value,
            "generated_at": datetime.now().isoformat(),
            "total_results": len(results),
            "results": []
        }
        
        for result in results:
            result_data = {
                "lab_id": result.lab_id,
                "lab_name": result.lab_name,
                "total_backtests": result.total_backtests,
                "analyzed_backtests": result.analyzed_backtests,
                "average_roi": result.average_roi,
                "best_roi": result.best_roi,
                "average_win_rate": result.average_win_rate,
                "best_win_rate": result.best_win_rate,
                "total_trades": result.total_trades,
                "analysis_timestamp": result.analysis_timestamp.isoformat()
            }
            
            if config.include_recommendations:
                result_data["recommendations"] = result.recommendations
            
            if config.include_bot_recommendations and result.top_performers:
                result_data["top_performers"] = result.top_performers[:5]  # Top 5
            
            report_data["results"].append(result_data)
        
        return json.dumps(report_data, indent=2)
    
    def _generate_csv_report(
        self,
        results: List[LabAnalysisResult],
        config: ReportConfig
    ) -> str:
        """Generate CSV report"""
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = [
            "Lab ID", "Lab Name", "Total Backtests", "Analyzed Backtests",
            "Average ROI", "Best ROI", "Average Win Rate", "Best Win Rate",
            "Total Trades", "Analysis Timestamp"
        ]
        
        if config.include_recommendations:
            header.append("Recommendations")
        
        writer.writerow(header)
        
        # Write data
        for result in results:
            row = [
                result.lab_id,
                result.lab_name,
                result.total_backtests,
                result.analyzed_backtests,
                result.average_roi,
                result.best_roi,
                result.average_win_rate,
                result.best_win_rate,
                result.total_trades,
                result.analysis_timestamp.isoformat()
            ]
            
            if config.include_recommendations:
                row.append("; ".join(result.recommendations))
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _generate_markdown_report(
        self,
        results: List[LabAnalysisResult],
        config: ReportConfig
    ) -> str:
        """Generate Markdown report"""
        content = []
        
        # Header
        content.append(f"# {config.report_type.value.title()} Analysis Report")
        content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**Total Results:** {len(results)}")
        content.append("")
        
        # Summary table
        content.append("## Summary")
        content.append("| Lab Name | Avg ROI | Best ROI | Win Rate | Trades |")
        content.append("|----------|---------|----------|----------|--------|")
        
        for result in results:
            content.append(
                f"| {result.lab_name} | {result.average_roi:.1f}% | "
                f"{result.best_roi:.1f}% | {result.average_win_rate:.1f}% | "
                f"{result.total_trades} |"
            )
        
        content.append("")
        
        return "\n".join(content)
    
    def _generate_html_report(
        self,
        results: List[LabAnalysisResult],
        config: ReportConfig
    ) -> str:
        """Generate HTML report"""
        content = []
        
        content.append("<!DOCTYPE html>")
        content.append("<html>")
        content.append("<head>")
        content.append("<title>Analysis Report</title>")
        content.append("<style>")
        content.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        content.append("table { border-collapse: collapse; width: 100%; }")
        content.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        content.append("th { background-color: #f2f2f2; }")
        content.append("</style>")
        content.append("</head>")
        content.append("<body>")
        
        content.append(f"<h1>{config.report_type.value.title()} Analysis Report</h1>")
        content.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        content.append(f"<p><strong>Total Results:</strong> {len(results)}</p>")
        
        # Summary table
        content.append("<h2>Summary</h2>")
        content.append("<table>")
        content.append("<tr><th>Lab Name</th><th>Avg ROI</th><th>Best ROI</th><th>Win Rate</th><th>Trades</th></tr>")
        
        for result in results:
            content.append(
                f"<tr><td>{result.lab_name}</td><td>{result.average_roi:.1f}%</td>"
                f"<td>{result.best_roi:.1f}%</td><td>{result.average_win_rate:.1f}%</td>"
                f"<td>{result.total_trades}</td></tr>"
            )
        
        content.append("</table>")
        
        content.append("</body>")
        content.append("</html>")
        
        return "\n".join(content)
    
    def _generate_txt_report(
        self,
        results: List[LabAnalysisResult],
        config: ReportConfig
    ) -> str:
        """Generate plain text report"""
        content = []
        
        content.append(f"{config.report_type.value.title()} Analysis Report")
        content.append("=" * 50)
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Total Results: {len(results)}")
        content.append("")
        
        for i, result in enumerate(results, 1):
            content.append(f"{i}. {result.lab_name}")
            content.append(f"   Lab ID: {result.lab_id}")
            content.append(f"   Average ROI: {result.average_roi:.1f}%")
            content.append(f"   Best ROI: {result.best_roi:.1f}%")
            content.append(f"   Win Rate: {result.average_win_rate:.1f}%")
            content.append(f"   Total Trades: {result.total_trades}")
            content.append("")
        
        return "\n".join(content)
    
    def _generate_bot_recommendations_json(
        self,
        recommendations: List[Dict[str, Any]],
        config: ReportConfig
    ) -> str:
        """Generate bot recommendations JSON report"""
        report_data = {
            "report_type": "bot_recommendations",
            "format": config.format.value,
            "generated_at": datetime.now().isoformat(),
            "total_recommendations": len(recommendations),
            "recommendations": []
        }
        
        for rec in recommendations:
            rec_data = {
                "lab_id": rec.lab_id,
                "lab_name": rec.lab_name,
                "backtest_id": rec.backtest_id,
                "script_name": rec.script_name,
                "market_tag": rec.market_tag,
                "roi_percentage": rec.roi_percentage,
                "win_rate": rec.win_rate,
                "total_trades": rec.total_trades,
                "max_drawdown": rec.max_drawdown,
                "profit_factor": rec.profit_factor,
                "sharpe_ratio": rec.sharpe_ratio,
                "confidence_score": rec.confidence_score,
                "formatted_bot_name": rec.formatted_bot_name,
                "recommendation_reason": rec.recommendation_reason
            }
            
            if config.include_bot_recommendations:
                rec_data["bot_configuration"] = {
                    "leverage": rec.recommended_config.leverage,
                    "position_mode": rec.recommended_config.position_mode,
                    "margin_mode": rec.recommended_config.margin_mode,
                    "trade_amount": rec.recommended_config.trade_amount,
                    "interval": rec.recommended_config.interval
                }
            
            report_data["recommendations"].append(rec_data)
        
        return json.dumps(report_data, indent=2)
    
    def _generate_bot_recommendations_csv(
        self,
        recommendations: List[Dict[str, Any]],
        config: ReportConfig
    ) -> str:
        """Generate bot recommendations CSV report"""
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        header = [
            "Lab ID", "Lab Name", "Backtest ID", "Script Name", "Market Tag",
            "ROI %", "Win Rate %", "Total Trades", "Max Drawdown %",
            "Profit Factor", "Sharpe Ratio", "Confidence Score",
            "Formatted Bot Name", "Recommendation Reason"
        ]
        
        if config.include_bot_recommendations:
            header.extend([
                "Leverage", "Position Mode", "Margin Mode", "Trade Amount", "Interval"
            ])
        
        writer.writerow(header)
        
        # Write data
        for rec in recommendations:
            row = [
                rec.lab_id,
                rec.lab_name,
                rec.backtest_id,
                rec.script_name,
                rec.market_tag,
                rec.roi_percentage,
                rec.win_rate,
                rec.total_trades,
                rec.max_drawdown,
                rec.profit_factor,
                rec.sharpe_ratio,
                rec.confidence_score,
                rec.formatted_bot_name,
                rec.recommendation_reason
            ]
            
            if config.include_bot_recommendations:
                row.extend([
                    rec.recommended_config.leverage,
                    rec.recommended_config.position_mode,
                    rec.recommended_config.margin_mode,
                    rec.recommended_config.trade_amount,
                    rec.recommended_config.interval
                ])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def _generate_bot_recommendations_markdown(
        self,
        recommendations: List[Dict[str, Any]],
        config: ReportConfig
    ) -> str:
        """Generate bot recommendations Markdown report"""
        content = []
        
        content.append("# Bot Recommendations Report")
        content.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**Total Recommendations:** {len(recommendations)}")
        content.append("")
        
        # Summary table
        content.append("## Summary")
        content.append("| Bot Name | ROI | Win Rate | Trades | Confidence |")
        content.append("|----------|-----|----------|--------|------------|")
        
        for rec in recommendations:
            content.append(
                f"| {rec.formatted_bot_name} | {rec.roi_percentage:.1f}% | "
                f"{rec.win_rate:.1f}% | {rec.total_trades} | {rec.confidence_score:.2f} |"
            )
        
        content.append("")
        
        return "\n".join(content)
    
    def _generate_bot_recommendations_html(
        self,
        recommendations: List[Dict[str, Any]],
        config: ReportConfig
    ) -> str:
        """Generate bot recommendations HTML report"""
        content = []
        
        content.append("<!DOCTYPE html>")
        content.append("<html>")
        content.append("<head>")
        content.append("<title>Bot Recommendations Report</title>")
        content.append("<style>")
        content.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        content.append("table { border-collapse: collapse; width: 100%; }")
        content.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        content.append("th { background-color: #f2f2f2; }")
        content.append("</style>")
        content.append("</head>")
        content.append("<body>")
        
        content.append("<h1>Bot Recommendations Report</h1>")
        content.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        content.append(f"<p><strong>Total Recommendations:</strong> {len(recommendations)}</p>")
        
        # Summary table
        content.append("<h2>Summary</h2>")
        content.append("<table>")
        content.append("<tr><th>Bot Name</th><th>ROI</th><th>Win Rate</th><th>Trades</th><th>Confidence</th></tr>")
        
        for rec in recommendations:
            content.append(
                f"<tr><td>{rec.formatted_bot_name}</td><td>{rec.roi_percentage:.1f}%</td>"
                f"<td>{rec.win_rate:.1f}%</td><td>{rec.total_trades}</td>"
                f"<td>{rec.confidence_score:.2f}</td></tr>"
            )
        
        content.append("</table>")
        
        content.append("</body>")
        content.append("</html>")
        
        return "\n".join(content)
    
    def _generate_bot_recommendations_txt(
        self,
        recommendations: List[Dict[str, Any]],
        config: ReportConfig
    ) -> str:
        """Generate bot recommendations plain text report"""
        content = []
        
        content.append("Bot Recommendations Report")
        content.append("=" * 50)
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Total Recommendations: {len(recommendations)}")
        content.append("")
        
        for i, rec in enumerate(recommendations, 1):
            content.append(f"{i}. {rec.formatted_bot_name}")
            content.append(f"   Lab ID: {rec.lab_id}")
            content.append(f"   Backtest ID: {rec.backtest_id}")
            content.append(f"   ROI: {rec.roi_percentage:.1f}%")
            content.append(f"   Win Rate: {rec.win_rate:.1f}%")
            content.append(f"   Total Trades: {rec.total_trades}")
            content.append(f"   Confidence Score: {rec.confidence_score:.2f}")
            content.append(f"   Reason: {rec.recommendation_reason}")
            content.append("")
        
        return "\n".join(content)
    
    def _save_report(self, content: str, config: ReportConfig) -> str:
        """Save report to file"""
        # Create output directory
        output_dir = Path(config.output_directory)
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = config.filename_template.format(
            report_type=config.report_type.value,
            timestamp=timestamp
        )
        
        # Add file extension
        if config.format == ReportFormat.JSON:
            filename += ".json"
        elif config.format == ReportFormat.CSV:
            filename += ".csv"
        elif config.format == ReportFormat.MARKDOWN:
            filename += ".md"
        elif config.format == ReportFormat.HTML:
            filename += ".html"
        elif config.format == ReportFormat.TXT:
            filename += ".txt"
        
        # Save file
        report_path = output_dir / filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(report_path)