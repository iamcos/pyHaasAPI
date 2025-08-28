"""
Output nodes for workflow system.

This module provides nodes for outputting reports, alerts, and other data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..node_base import WorkflowNode, DataType, ValidationError
from ..node_registry import register_node, NodeCategory


@register_node(
    category=NodeCategory.OUTPUT,
    display_name="Report Output",
    description="Generate and output reports from workflow data",
    icon="📄",
    tags=["output", "report", "export"]
)
class ReportOutputNode(WorkflowNode):
    """Node for generating and outputting reports."""
    
    _category = NodeCategory.OUTPUT
    _display_name = "Report Output"
    _description = "Generate and output reports from workflow data"
    _icon = "📄"
    _tags = ["output", "report", "export"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("report_data", DataType.DICT, True,
                           "Data to include in report")
        self.add_input_port("report_title", DataType.STRING, False,
                           "Report title", "Workflow Report")
        self.add_input_port("additional_sections", DataType.LIST, False,
                           "Additional report sections", [])
        
        # Output ports
        self.add_output_port("report_content", DataType.STRING,
                            "Generated report content")
        self.add_output_port("report_metadata", DataType.DICT,
                            "Report metadata")
        self.add_output_port("export_status", DataType.STRING,
                            "Export operation status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "report_format": "markdown",  # markdown, html, json, text
            "include_timestamp": True,
            "include_summary": True,
            "export_to_file": False,
            "output_directory": "./reports",
            "filename_template": "report_{timestamp}",
            "template_file": "",
            "sections": [
                "summary",
                "data",
                "analysis",
                "recommendations"
            ]
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute report generation."""
        try:
            report_data = self.get_input_value("report_data", context)
            report_title = self.get_input_value("report_title", context)
            additional_sections = self.get_input_value("additional_sections", context) or []
            
            # Generate report content
            report_content = await self._generate_report(report_data, report_title, additional_sections, context)
            
            # Create report metadata
            report_metadata = self._create_report_metadata(report_data, report_title, context)
            
            # Export to file if requested
            export_status = "generated"
            if self.get_parameter("export_to_file", False):
                export_result = await self._export_to_file(report_content, report_metadata)
                export_status = export_result.get("status", "export_failed")
                report_metadata.update(export_result.get("metadata", {}))
            
            return {
                "report_content": report_content,
                "report_metadata": report_metadata,
                "export_status": export_status
            }
            
        except Exception as e:
            return {
                "report_content": f"Report generation failed: {str(e)}",
                "report_metadata": {"error": str(e)},
                "export_status": f"error: {str(e)}"
            }
    
    async def _generate_report(self, report_data: Dict[str, Any], report_title: str, 
                             additional_sections: List[Dict], context) -> str:
        """Generate report content based on format."""
        report_format = self.get_parameter("report_format", "markdown")
        
        if report_format == "markdown":
            return self._generate_markdown_report(report_data, report_title, additional_sections, context)
        elif report_format == "html":
            return self._generate_html_report(report_data, report_title, additional_sections, context)
        elif report_format == "json":
            return self._generate_json_report(report_data, report_title, additional_sections, context)
        elif report_format == "text":
            return self._generate_text_report(report_data, report_title, additional_sections, context)
        else:
            return self._generate_markdown_report(report_data, report_title, additional_sections, context)
    
    def _generate_markdown_report(self, report_data: Dict[str, Any], report_title: str, 
                                additional_sections: List[Dict], context) -> str:
        """Generate Markdown format report."""
        lines = []
        
        # Title
        lines.append(f"# {report_title}")
        lines.append("")
        
        # Timestamp
        if self.get_parameter("include_timestamp", True):
            lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**Workflow ID:** {context.workflow_id}")
            lines.append("")
        
        # Summary section
        if self.get_parameter("include_summary", True) and "summary" in self.get_parameter("sections", []):
            lines.append("## Summary")
            lines.append("")
            summary = self._generate_summary(report_data)
            lines.extend(summary)
            lines.append("")
        
        # Data section
        if "data" in self.get_parameter("sections", []):
            lines.append("## Data")
            lines.append("")
            
            for key, value in report_data.items():
                lines.append(f"### {key.replace('_', ' ').title()}")
                lines.append("")
                
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        lines.append(f"- **{sub_key}:** {sub_value}")
                elif isinstance(value, list):
                    for item in value:
                        lines.append(f"- {item}")
                else:
                    lines.append(f"{value}")
                
                lines.append("")
        
        # Analysis section
        if "analysis" in self.get_parameter("sections", []):
            lines.append("## Analysis")
            lines.append("")
            analysis = self._generate_analysis(report_data)
            lines.extend(analysis)
            lines.append("")
        
        # Recommendations section
        if "recommendations" in self.get_parameter("sections", []):
            lines.append("## Recommendations")
            lines.append("")
            recommendations = self._generate_recommendations(report_data)
            lines.extend(recommendations)
            lines.append("")
        
        # Additional sections
        for section in additional_sections:
            section_title = section.get("title", "Additional Section")
            section_content = section.get("content", "")
            
            lines.append(f"## {section_title}")
            lines.append("")
            lines.append(section_content)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_html_report(self, report_data: Dict[str, Any], report_title: str, 
                            additional_sections: List[Dict], context) -> str:
        """Generate HTML format report."""
        html_parts = []
        
        # HTML header
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html>")
        html_parts.append("<head>")
        html_parts.append(f"<title>{report_title}</title>")
        html_parts.append("<style>")
        html_parts.append("body { font-family: Arial, sans-serif; margin: 40px; }")
        html_parts.append("h1 { color: #333; }")
        html_parts.append("h2 { color: #666; border-bottom: 1px solid #ccc; }")
        html_parts.append("table { border-collapse: collapse; width: 100%; }")
        html_parts.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html_parts.append("th { background-color: #f2f2f2; }")
        html_parts.append("</style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        
        # Title
        html_parts.append(f"<h1>{report_title}</h1>")
        
        # Timestamp
        if self.get_parameter("include_timestamp", True):
            html_parts.append(f"<p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
            html_parts.append(f"<p><strong>Workflow ID:</strong> {context.workflow_id}</p>")
        
        # Data as table
        if report_data:
            html_parts.append("<h2>Data</h2>")
            html_parts.append("<table>")
            html_parts.append("<tr><th>Key</th><th>Value</th></tr>")
            
            for key, value in report_data.items():
                html_parts.append(f"<tr><td>{key}</td><td>{self._format_value_for_html(value)}</td></tr>")
            
            html_parts.append("</table>")
        
        # Additional sections
        for section in additional_sections:
            section_title = section.get("title", "Additional Section")
            section_content = section.get("content", "")
            
            html_parts.append(f"<h2>{section_title}</h2>")
            html_parts.append(f"<p>{section_content}</p>")
        
        # HTML footer
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)
    
    def _generate_json_report(self, report_data: Dict[str, Any], report_title: str, 
                            additional_sections: List[Dict], context) -> str:
        """Generate JSON format report."""
        report_json = {
            "title": report_title,
            "generated_at": datetime.now().isoformat(),
            "workflow_id": context.workflow_id,
            "data": report_data,
            "additional_sections": additional_sections,
            "metadata": {
                "format": "json",
                "generator": "ReportOutputNode"
            }
        }
        
        return json.dumps(report_json, indent=2, default=str)
    
    def _generate_text_report(self, report_data: Dict[str, Any], report_title: str, 
                            additional_sections: List[Dict], context) -> str:
        """Generate plain text format report."""
        lines = []
        
        # Title
        lines.append(report_title)
        lines.append("=" * len(report_title))
        lines.append("")
        
        # Timestamp
        if self.get_parameter("include_timestamp", True):
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Workflow ID: {context.workflow_id}")
            lines.append("")
        
        # Data
        lines.append("DATA")
        lines.append("-" * 50)
        
        for key, value in report_data.items():
            lines.append(f"{key}: {value}")
        
        lines.append("")
        
        # Additional sections
        for section in additional_sections:
            section_title = section.get("title", "Additional Section")
            section_content = section.get("content", "")
            
            lines.append(section_title.upper())
            lines.append("-" * 50)
            lines.append(section_content)
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_summary(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate summary section."""
        summary_lines = []
        
        # Basic statistics
        summary_lines.append(f"- **Total data points:** {len(report_data)}")
        
        # Look for common metrics
        if "total_return" in report_data:
            summary_lines.append(f"- **Total Return:** {report_data['total_return']:.2%}")
        
        if "win_rate" in report_data:
            summary_lines.append(f"- **Win Rate:** {report_data['win_rate']:.1%}")
        
        if "total_trades" in report_data:
            summary_lines.append(f"- **Total Trades:** {report_data['total_trades']}")
        
        if "max_drawdown" in report_data:
            summary_lines.append(f"- **Max Drawdown:** {report_data['max_drawdown']:.2%}")
        
        return summary_lines
    
    def _generate_analysis(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate analysis section."""
        analysis_lines = []
        
        # Performance analysis
        if "total_return" in report_data:
            total_return = report_data["total_return"]
            if total_return > 0.1:
                analysis_lines.append("- Strong positive performance detected")
            elif total_return > 0:
                analysis_lines.append("- Modest positive performance")
            else:
                analysis_lines.append("- Negative performance - review strategy")
        
        # Risk analysis
        if "max_drawdown" in report_data:
            max_dd = report_data["max_drawdown"]
            if max_dd > 0.2:
                analysis_lines.append("- High drawdown indicates significant risk")
            elif max_dd > 0.1:
                analysis_lines.append("- Moderate drawdown within acceptable range")
            else:
                analysis_lines.append("- Low drawdown indicates good risk management")
        
        return analysis_lines
    
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations section."""
        recommendations = []
        
        # Performance-based recommendations
        if "win_rate" in report_data:
            win_rate = report_data["win_rate"]
            if win_rate < 0.4:
                recommendations.append("- Consider improving entry signal quality")
            elif win_rate > 0.7:
                recommendations.append("- High win rate - consider increasing position sizes")
        
        if "profit_factor" in report_data:
            pf = report_data["profit_factor"]
            if pf < 1.2:
                recommendations.append("- Low profit factor - review exit strategy")
        
        if not recommendations:
            recommendations.append("- Continue monitoring performance")
            recommendations.append("- Regular strategy review recommended")
        
        return recommendations
    
    def _format_value_for_html(self, value: Any) -> str:
        """Format value for HTML display."""
        if isinstance(value, dict):
            return "<br>".join([f"{k}: {v}" for k, v in value.items()])
        elif isinstance(value, list):
            return "<br>".join([str(item) for item in value])
        else:
            return str(value)
    
    def _create_report_metadata(self, report_data: Dict[str, Any], report_title: str, context) -> Dict[str, Any]:
        """Create report metadata."""
        return {
            "title": report_title,
            "generated_at": datetime.now().isoformat(),
            "workflow_id": context.workflow_id,
            "node_id": self.node_id,
            "format": self.get_parameter("report_format", "markdown"),
            "data_points": len(report_data),
            "sections": self.get_parameter("sections", [])
        }
    
    async def _export_to_file(self, report_content: str, report_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Export report to file."""
        try:
            import os
            from pathlib import Path
            
            output_dir = Path(self.get_parameter("output_directory", "./reports"))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename_template = self.get_parameter("filename_template", "report_{timestamp}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filename_template.format(timestamp=timestamp)
            
            # Add extension based on format
            report_format = self.get_parameter("report_format", "markdown")
            extensions = {
                "markdown": ".md",
                "html": ".html",
                "json": ".json",
                "text": ".txt"
            }
            filename += extensions.get(report_format, ".txt")
            
            # Write file
            file_path = output_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            return {
                "status": "exported",
                "metadata": {
                    "file_path": str(file_path),
                    "file_size": len(report_content),
                    "export_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "status": "export_failed",
                "metadata": {
                    "error": str(e)
                }
            }


@register_node(
    category=NodeCategory.OUTPUT,
    display_name="Alert Output",
    description="Generate and send alerts based on workflow data",
    icon="🚨",
    tags=["output", "alert", "notification"]
)
class AlertOutputNode(WorkflowNode):
    """Node for generating and sending alerts."""
    
    _category = NodeCategory.OUTPUT
    _display_name = "Alert Output"
    _description = "Generate and send alerts based on workflow data"
    _icon = "🚨"
    _tags = ["output", "alert", "notification"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("alert_data", DataType.DICT, True,
                           "Data to evaluate for alerts")
        self.add_input_port("alert_conditions", DataType.LIST, False,
                           "Custom alert conditions", [])
        self.add_input_port("severity_override", DataType.STRING, False,
                           "Override alert severity")
        
        # Output ports
        self.add_output_port("alerts_generated", DataType.LIST,
                            "Generated alerts")
        self.add_output_port("alert_count", DataType.INTEGER,
                            "Number of alerts generated")
        self.add_output_port("alert_status", DataType.STRING,
                            "Alert generation status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "alert_rules": [
                {
                    "name": "high_drawdown",
                    "condition": "max_drawdown > 0.15",
                    "severity": "warning",
                    "message": "High drawdown detected: {max_drawdown:.2%}"
                },
                {
                    "name": "negative_return",
                    "condition": "total_return < 0",
                    "severity": "warning",
                    "message": "Negative return detected: {total_return:.2%}"
                },
                {
                    "name": "low_win_rate",
                    "condition": "win_rate < 0.3",
                    "severity": "info",
                    "message": "Low win rate: {win_rate:.1%}"
                }
            ],
            "send_notifications": True,
            "notification_channels": ["console"],
            "alert_cooldown": 300,  # seconds
            "deduplicate_alerts": True
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute alert generation."""
        try:
            alert_data = self.get_input_value("alert_data", context)
            alert_conditions = self.get_input_value("alert_conditions", context) or []
            severity_override = self.get_input_value("severity_override", context)
            
            # Generate alerts based on rules
            generated_alerts = []
            
            # Process built-in alert rules
            alert_rules = self.get_parameter("alert_rules", [])
            for rule in alert_rules:
                alert = self._evaluate_alert_rule(rule, alert_data, severity_override)
                if alert:
                    generated_alerts.append(alert)
            
            # Process custom alert conditions
            for condition in alert_conditions:
                alert = self._evaluate_custom_condition(condition, alert_data, severity_override)
                if alert:
                    generated_alerts.append(alert)
            
            # Deduplicate alerts if requested
            if self.get_parameter("deduplicate_alerts", True):
                generated_alerts = self._deduplicate_alerts(generated_alerts)
            
            # Send notifications if requested
            if self.get_parameter("send_notifications", True) and generated_alerts:
                await self._send_alert_notifications(generated_alerts, context)
            
            alert_status = "success" if generated_alerts else "no_alerts"
            
            return {
                "alerts_generated": generated_alerts,
                "alert_count": len(generated_alerts),
                "alert_status": alert_status
            }
            
        except Exception as e:
            return {
                "alerts_generated": [],
                "alert_count": 0,
                "alert_status": f"error: {str(e)}"
            }
    
    def _evaluate_alert_rule(self, rule: Dict[str, Any], alert_data: Dict[str, Any], 
                           severity_override: Optional[str]) -> Optional[Dict[str, Any]]:
        """Evaluate a single alert rule."""
        try:
            condition = rule.get("condition", "")
            if not condition:
                return None
            
            # Create safe evaluation context
            safe_dict = {
                **alert_data,
                "abs": abs,
                "min": min,
                "max": max,
                "len": len
            }
            
            # Evaluate condition
            result = eval(condition, {"__builtins__": {}}, safe_dict)
            
            if result:
                # Format message with data
                message_template = rule.get("message", "Alert condition met")
                try:
                    message = message_template.format(**alert_data)
                except (KeyError, ValueError):
                    message = message_template
                
                return {
                    "rule_name": rule.get("name", "unknown"),
                    "severity": severity_override or rule.get("severity", "info"),
                    "message": message,
                    "condition": condition,
                    "timestamp": datetime.now().isoformat(),
                    "data": alert_data
                }
            
            return None
            
        except Exception:
            return None
    
    def _evaluate_custom_condition(self, condition: Dict[str, Any], alert_data: Dict[str, Any], 
                                 severity_override: Optional[str]) -> Optional[Dict[str, Any]]:
        """Evaluate a custom alert condition."""
        try:
            condition_expr = condition.get("condition", "")
            if not condition_expr:
                return None
            
            # Create safe evaluation context
            safe_dict = {
                **alert_data,
                "abs": abs,
                "min": min,
                "max": max,
                "len": len
            }
            
            # Evaluate condition
            result = eval(condition_expr, {"__builtins__": {}}, safe_dict)
            
            if result:
                return {
                    "rule_name": condition.get("name", "custom"),
                    "severity": severity_override or condition.get("severity", "info"),
                    "message": condition.get("message", "Custom alert condition met"),
                    "condition": condition_expr,
                    "timestamp": datetime.now().isoformat(),
                    "data": alert_data
                }
            
            return None
            
        except Exception:
            return None
    
    def _deduplicate_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate alerts."""
        seen_alerts = set()
        deduplicated = []
        
        for alert in alerts:
            # Create a key based on rule name and message
            alert_key = (alert.get("rule_name", ""), alert.get("message", ""))
            
            if alert_key not in seen_alerts:
                seen_alerts.add(alert_key)
                deduplicated.append(alert)
        
        return deduplicated
    
    async def _send_alert_notifications(self, alerts: List[Dict[str, Any]], context) -> None:
        """Send alert notifications through configured channels."""
        channels = self.get_parameter("notification_channels", ["console"])
        
        for alert in alerts:
            for channel in channels:
                try:
                    if channel == "console":
                        await self._send_console_alert(alert)
                    # Additional channels could be implemented here
                    
                except Exception as e:
                    context.report_progress(f"Failed to send alert via {channel}: {str(e)}")
    
    async def _send_console_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert to console."""
        severity = alert.get("severity", "info").upper()
        message = alert.get("message", "")
        timestamp = alert.get("timestamp", "")
        
        print(f"ALERT [{severity}] {timestamp}: {message}")
    
    def add_alert_rule(self, name: str, condition: str, severity: str = "info", 
                      message: str = "Alert condition met") -> None:
        """Add a new alert rule."""
        if "alert_rules" not in self.parameters:
            self.parameters["alert_rules"] = []
        
        self.parameters["alert_rules"].append({
            "name": name,
            "condition": condition,
            "severity": severity,
            "message": message
        })
    
    def remove_alert_rule(self, name: str) -> bool:
        """Remove an alert rule by name."""
        alert_rules = self.parameters.get("alert_rules", [])
        
        for i, rule in enumerate(alert_rules):
            if rule.get("name") == name:
                del alert_rules[i]
                return True
        
        return False