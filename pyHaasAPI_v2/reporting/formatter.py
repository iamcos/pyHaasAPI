"""
Flexible report formatter for pyHaasAPI v2

Supports multiple output formats with configurable content and styling.
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from .types import ReportType, ReportFormat, ReportConfig, BotRecommendationConfig
from .models import AnalysisReport, BotRecommendation, LabSummary, BacktestSummary


class ReportFormatter:
    """Flexible report formatter supporting multiple output formats"""
    
    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.bot_config = BotRecommendationConfig()
    
    def format_report(
        self, 
        report: AnalysisReport, 
        output_path: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Format a report in multiple formats
        
        Args:
            report: The analysis report to format
            output_path: Optional base path for output files
            
        Returns:
            Dictionary mapping format names to file paths
        """
        if output_path is None:
            output_path = self.config.output_dir
        
        # Ensure output directory exists
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {}
        
        for format_type in self.config.formats:
            if format_type == ReportFormat.JSON:
                file_path = self._format_json(report, output_path, timestamp)
                results["json"] = file_path
            elif format_type == ReportFormat.CSV:
                file_path = self._format_csv(report, output_path, timestamp)
                results["csv"] = file_path
            elif format_type == ReportFormat.MARKDOWN:
                file_path = self._format_markdown(report, output_path, timestamp)
                results["markdown"] = file_path
            elif format_type == ReportFormat.HTML:
                file_path = self._format_html(report, output_path, timestamp)
                results["html"] = file_path
            elif format_type == ReportFormat.TXT:
                file_path = self._format_txt(report, output_path, timestamp)
                results["txt"] = file_path
        
        return results
    
    def _format_json(self, report: AnalysisReport, output_path: str, timestamp: str) -> str:
        """Format report as JSON"""
        filename = f"{self.config.filename_prefix}_{timestamp}.json"
        file_path = os.path.join(output_path, filename)
        
        # Convert report to dictionary
        report_dict = self._report_to_dict(report)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str, ensure_ascii=False)
        
        return file_path
    
    def _format_csv(self, report: AnalysisReport, output_path: str, timestamp: str) -> str:
        """Format report as CSV"""
        filename = f"{self.config.filename_prefix}_{timestamp}.csv"
        file_path = os.path.join(output_path, filename)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            if self.config.include_bot_recommendations and report.bot_recommendations:
                self._write_bot_recommendations_csv(writer, report.bot_recommendations)
            else:
                self._write_lab_summary_csv(writer, report.lab_summaries)
        
        return file_path
    
    def _format_markdown(self, report: AnalysisReport, output_path: str, timestamp: str) -> str:
        """Format report as Markdown"""
        filename = f"{self.config.filename_prefix}_{timestamp}.md"
        file_path = os.path.join(output_path, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_content(report))
        
        return file_path
    
    def _format_html(self, report: AnalysisReport, output_path: str, timestamp: str) -> str:
        """Format report as HTML"""
        filename = f"{self.config.filename_prefix}_{timestamp}.html"
        file_path = os.path.join(output_path, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_html_content(report))
        
        return file_path
    
    def _format_txt(self, report: AnalysisReport, output_path: str, timestamp: str) -> str:
        """Format report as plain text"""
        filename = f"{self.config.filename_prefix}_{timestamp}.txt"
        file_path = os.path.join(output_path, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_txt_content(report))
        
        return file_path
    
    def _report_to_dict(self, report: AnalysisReport) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            "report_metadata": {
                "report_id": report.report_id,
                "report_type": report.report_type,
                "generated_at": report.generated_at.isoformat(),
                "generated_by": report.generated_by,
                "total_labs_analyzed": report.total_labs_analyzed,
                "total_backtests_analyzed": report.total_backtests_analyzed,
                "analysis_duration": report.analysis_duration
            },
            "lab_summaries": [
                {
                    "lab_id": lab.lab_id,
                    "lab_name": lab.lab_name,
                    "script_name": lab.script_name,
                    "market_tag": lab.market_tag,
                    "total_backtests": lab.total_backtests,
                    "analyzed_backtests": lab.analyzed_backtests,
                    "avg_roi": lab.avg_roi,
                    "max_roi": lab.max_roi,
                    "avg_win_rate": lab.avg_win_rate,
                    "top_backtests": [
                        {
                            "backtest_id": bt.backtest_id,
                            "roi_percentage": bt.roi_percentage,
                            "win_rate": bt.win_rate,
                            "total_trades": bt.total_trades,
                            "profit_factor": bt.profit_factor
                        }
                        for bt in lab.top_backtests
                    ]
                }
                for lab in report.lab_summaries
            ],
            "bot_recommendations": [
                {
                    "lab_id": rec.lab_id,
                    "lab_name": rec.lab_name,
                    "backtest_id": rec.backtest_id,
                    "script_name": rec.script_name,
                    "market_tag": rec.market_tag,
                    "formatted_bot_name": rec.formatted_bot_name,
                    "roi_percentage": rec.roi_percentage,
                    "win_rate": rec.win_rate,
                    "total_trades": rec.total_trades,
                    "max_drawdown": rec.max_drawdown,
                    "profit_factor": rec.profit_factor,
                    "sharpe_ratio": rec.sharpe_ratio,
                    "recommended_trade_amount_usdt": rec.recommended_trade_amount_usdt,
                    "recommended_leverage": rec.recommended_leverage,
                    "risk_level": rec.risk_level,
                    "confidence_score": rec.confidence_score,
                    "priority_score": rec.priority_score
                }
                for rec in report.bot_recommendations
            ],
            "overall_stats": report.overall_stats,
            "config": report.report_config
        }
    
    def _write_bot_recommendations_csv(self, writer, recommendations: List[BotRecommendation]):
        """Write bot recommendations to CSV"""
        # Header
        header = [
            "Lab ID", "Lab Name", "Backtest ID", "Script Name", "Market Tag",
            "Formatted Bot Name", "ROI %", "Win Rate %", "Total Trades",
            "Max Drawdown %", "Profit Factor", "Sharpe Ratio",
            "Trade Amount USDT", "Leverage", "Risk Level", "Confidence Score"
        ]
        writer.writerow(header)
        
        # Data rows
        for rec in recommendations:
            row = [
                rec.lab_id,
                rec.lab_name,
                rec.backtest_id,
                rec.script_name,
                rec.market_tag,
                rec.formatted_bot_name,
                f"{rec.roi_percentage:.2f}",
                f"{rec.win_rate * 100:.1f}",
                rec.total_trades,
                f"{rec.max_drawdown * 100:.2f}",
                f"{rec.profit_factor:.2f}",
                f"{rec.sharpe_ratio:.2f}",
                f"{rec.recommended_trade_amount_usdt:.0f}",
                f"{rec.recommended_leverage:.0f}x",
                rec.risk_level,
                f"{rec.confidence_score:.2f}"
            ]
            writer.writerow(row)
    
    def _write_lab_summary_csv(self, writer, lab_summaries: List[LabSummary]):
        """Write lab summaries to CSV"""
        # Header
        header = [
            "Lab ID", "Lab Name", "Script Name", "Market Tag",
            "Total Backtests", "Analyzed Backtests", "Avg ROI %",
            "Max ROI %", "Avg Win Rate %", "Avg Trades", "Avg Profit Factor"
        ]
        writer.writerow(header)
        
        # Data rows
        for lab in lab_summaries:
            row = [
                lab.lab_id,
                lab.lab_name,
                lab.script_name,
                lab.market_tag,
                lab.total_backtests,
                lab.analyzed_backtests,
                f"{lab.avg_roi:.2f}",
                f"{lab.max_roi:.2f}",
                f"{lab.avg_win_rate * 100:.1f}",
                f"{lab.avg_trades:.0f}",
                f"{lab.avg_profit_factor:.2f}"
            ]
            writer.writerow(row)
    
    def _generate_markdown_content(self, report: AnalysisReport) -> str:
        """Generate Markdown content for the report"""
        content = []
        
        # Header
        content.append(f"# Analysis Report - {report.report_type.title()}")
        content.append(f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**Generated by:** {report.generated_by}")
        content.append("")
        
        # Summary
        content.append("## Summary")
        content.append(f"- **Total Labs Analyzed:** {report.total_labs_analyzed}")
        content.append(f"- **Total Backtests Analyzed:** {report.total_backtests_analyzed}")
        if report.analysis_duration:
            content.append(f"- **Analysis Duration:** {report.analysis_duration:.2f} seconds")
        content.append("")
        
        # Bot Recommendations
        if self.config.include_bot_recommendations and report.bot_recommendations:
            content.append("## Bot Recommendations")
            content.append("")
            
            for i, rec in enumerate(report.bot_recommendations[:self.config.max_recommendations], 1):
                content.append(f"### {i}. {rec.formatted_bot_name}")
                content.append("")
                content.append(f"- **Lab ID:** `{rec.lab_id}`")
                content.append(f"- **Backtest ID:** `{rec.backtest_id}`")
                content.append(f"- **Script:** {rec.script_name}")
                content.append(f"- **Market:** {rec.market_tag}")
                content.append(f"- **ROI:** {rec.roi_percentage:.2f}%")
                content.append(f"- **Win Rate:** {rec.win_rate * 100:.1f}%")
                content.append(f"- **Total Trades:** {rec.total_trades}")
                content.append(f"- **Profit Factor:** {rec.profit_factor:.2f}")
                content.append(f"- **Sharpe Ratio:** {rec.sharpe_ratio:.2f}")
                content.append(f"- **Risk Level:** {rec.risk_level}")
                content.append(f"- **Confidence:** {rec.confidence_score:.2f}")
                content.append(f"- **Recommended Trade Amount:** ${rec.recommended_trade_amount_usdt:.0f} USDT")
                content.append(f"- **Recommended Leverage:** {rec.recommended_leverage:.0f}x")
                content.append("")
        
        # Lab Summaries
        if report.lab_summaries:
            content.append("## Lab Summaries")
            content.append("")
            
            for lab in report.lab_summaries:
                content.append(f"### {lab.lab_name}")
                content.append(f"- **Lab ID:** `{lab.lab_id}`")
                content.append(f"- **Script:** {lab.script_name}")
                content.append(f"- **Market:** {lab.market_tag}")
                content.append(f"- **Total Backtests:** {lab.total_backtests}")
                content.append(f"- **Analyzed Backtests:** {lab.analyzed_backtests}")
                content.append(f"- **Average ROI:** {lab.avg_roi:.2f}%")
                content.append(f"- **Max ROI:** {lab.max_roi:.2f}%")
                content.append(f"- **Average Win Rate:** {lab.avg_win_rate * 100:.1f}%")
                content.append("")
        
        return "\n".join(content)
    
    def _generate_html_content(self, report: AnalysisReport) -> str:
        """Generate HTML content for the report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Analysis Report - {report.report_type.title()}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .recommendation {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 5px 10px; }}
        .high-roi {{ color: #28a745; }}
        .medium-roi {{ color: #ffc107; }}
        .low-roi {{ color: #dc3545; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Analysis Report - {report.report_type.title()}</h1>
        <p><strong>Generated:</strong> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Generated by:</strong> {report.generated_by}</p>
        <p><strong>Total Labs:</strong> {report.total_labs_analyzed} | <strong>Total Backtests:</strong> {report.total_backtests_analyzed}</p>
    </div>
"""
        
        # Bot Recommendations
        if self.config.include_bot_recommendations and report.bot_recommendations:
            html += """
    <div class="section">
        <h2>Bot Recommendations</h2>
"""
            for i, rec in enumerate(report.bot_recommendations[:self.config.max_recommendations], 1):
                roi_class = "high-roi" if rec.roi_percentage > 100 else "medium-roi" if rec.roi_percentage > 50 else "low-roi"
                html += f"""
        <div class="recommendation">
            <h3>{i}. {rec.formatted_bot_name}</h3>
            <div class="metric"><strong>Lab ID:</strong> {rec.lab_id}</div>
            <div class="metric"><strong>Backtest ID:</strong> {rec.backtest_id}</div>
            <div class="metric"><strong>Script:</strong> {rec.script_name}</div>
            <div class="metric"><strong>Market:</strong> {rec.market_tag}</div>
            <div class="metric {roi_class}"><strong>ROI:</strong> {rec.roi_percentage:.2f}%</div>
            <div class="metric"><strong>Win Rate:</strong> {rec.win_rate * 100:.1f}%</div>
            <div class="metric"><strong>Total Trades:</strong> {rec.total_trades}</div>
            <div class="metric"><strong>Profit Factor:</strong> {rec.profit_factor:.2f}</div>
            <div class="metric"><strong>Risk Level:</strong> {rec.risk_level}</div>
            <div class="metric"><strong>Trade Amount:</strong> ${rec.recommended_trade_amount_usdt:.0f} USDT</div>
        </div>
"""
            html += "    </div>"
        
        html += """
</body>
</html>
"""
        return html
    
    def _generate_txt_content(self, report: AnalysisReport) -> str:
        """Generate plain text content for the report"""
        content = []
        
        # Header
        content.append("=" * 60)
        content.append(f"ANALYSIS REPORT - {report.report_type.upper()}")
        content.append("=" * 60)
        content.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Generated by: {report.generated_by}")
        content.append(f"Total Labs: {report.total_labs_analyzed}")
        content.append(f"Total Backtests: {report.total_backtests_analyzed}")
        if report.analysis_duration:
            content.append(f"Analysis Duration: {report.analysis_duration:.2f} seconds")
        content.append("")
        
        # Bot Recommendations
        if self.config.include_bot_recommendations and report.bot_recommendations:
            content.append("BOT RECOMMENDATIONS")
            content.append("-" * 40)
            content.append("")
            
            for i, rec in enumerate(report.bot_recommendations[:self.config.max_recommendations], 1):
                content.append(f"{i}. {rec.formatted_bot_name}")
                content.append(f"   Lab ID: {rec.lab_id}")
                content.append(f"   Backtest ID: {rec.backtest_id}")
                content.append(f"   Script: {rec.script_name}")
                content.append(f"   Market: {rec.market_tag}")
                content.append(f"   ROI: {rec.roi_percentage:.2f}%")
                content.append(f"   Win Rate: {rec.win_rate * 100:.1f}%")
                content.append(f"   Total Trades: {rec.total_trades}")
                content.append(f"   Profit Factor: {rec.profit_factor:.2f}")
                content.append(f"   Risk Level: {rec.risk_level}")
                content.append(f"   Trade Amount: ${rec.recommended_trade_amount_usdt:.0f} USDT")
                content.append("")
        
        return "\n".join(content)

