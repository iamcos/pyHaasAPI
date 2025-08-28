"""
Utility nodes for workflow system.

This module provides utility nodes for common workflow operations like delays,
conditionals, and notifications.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from ..node_base import WorkflowNode, DataType, ValidationError
from ..node_registry import register_node, NodeCategory


@register_node(
    category=NodeCategory.UTILITY,
    display_name="Delay",
    description="Add a delay to workflow execution",
    icon="⏱️",
    tags=["delay", "wait", "timing"]
)
class DelayNode(WorkflowNode):
    """Node for adding delays to workflow execution."""
    
    _category = NodeCategory.UTILITY
    _display_name = "Delay"
    _description = "Add a delay to workflow execution"
    _icon = "⏱️"
    _tags = ["delay", "wait", "timing"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("input_data", DataType.DICT, False,
                           "Data to pass through after delay", {})
        self.add_input_port("delay_seconds", DataType.INTEGER, False,
                           "Delay duration in seconds")
        
        # Output ports
        self.add_output_port("output_data", DataType.DICT,
                            "Data passed through after delay")
        self.add_output_port("delay_completed", DataType.BOOLEAN,
                            "Indicates delay completion")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "default_delay": 60,  # seconds
            "show_progress": True,
            "interruptible": False
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute delay."""
        try:
            input_data = self.get_input_value("input_data", context)
            delay_seconds = self.get_input_value("delay_seconds", context)
            
            if delay_seconds is None:
                delay_seconds = self.get_parameter("default_delay", 60)
            
            show_progress = self.get_parameter("show_progress", True)
            
            if show_progress:
                context.report_progress(f"Starting delay of {delay_seconds} seconds")
            
            # Perform delay with optional progress reporting
            if show_progress and delay_seconds > 10:
                # Report progress every 10 seconds for long delays
                elapsed = 0
                while elapsed < delay_seconds:
                    sleep_time = min(10, delay_seconds - elapsed)
                    await asyncio.sleep(sleep_time)
                    elapsed += sleep_time
                    
                    progress = (elapsed / delay_seconds) * 100
                    context.report_progress(f"Delay progress: {progress:.1f}% ({elapsed}/{delay_seconds}s)")
            else:
                await asyncio.sleep(delay_seconds)
            
            if show_progress:
                context.report_progress("Delay completed")
            
            return {
                "output_data": input_data,
                "delay_completed": True
            }
            
        except Exception as e:
            return {
                "output_data": {},
                "delay_completed": False
            }


@register_node(
    category=NodeCategory.UTILITY,
    display_name="Conditional",
    description="Execute conditional logic in workflows",
    icon="🔀",
    tags=["conditional", "logic", "branching"]
)
class ConditionalNode(WorkflowNode):
    """Node for conditional logic and branching."""
    
    _category = NodeCategory.UTILITY
    _display_name = "Conditional"
    _description = "Execute conditional logic in workflows"
    _icon = "🔀"
    _tags = ["conditional", "logic", "branching"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("condition_value", DataType.DICT, True,
                           "Value to evaluate condition against")
        self.add_input_port("true_data", DataType.DICT, False,
                           "Data to output if condition is true", {})
        self.add_input_port("false_data", DataType.DICT, False,
                           "Data to output if condition is false", {})
        
        # Output ports
        self.add_output_port("output_data", DataType.DICT,
                            "Conditional output data")
        self.add_output_port("condition_result", DataType.BOOLEAN,
                            "Result of condition evaluation")
        self.add_output_port("branch_taken", DataType.STRING,
                            "Which branch was taken (true/false)")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "condition_type": "threshold",  # threshold, comparison, custom
            "operator": "greater_than",  # greater_than, less_than, equals, not_equals
            "threshold_value": 0,
            "field_path": "value",  # Path to field in condition_value dict
            "custom_condition": ""  # Custom Python expression
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute conditional logic."""
        try:
            condition_value = self.get_input_value("condition_value", context)
            true_data = self.get_input_value("true_data", context)
            false_data = self.get_input_value("false_data", context)
            
            # Evaluate condition
            condition_result = self._evaluate_condition(condition_value)
            
            # Select output data based on condition
            if condition_result:
                output_data = true_data
                branch_taken = "true"
            else:
                output_data = false_data
                branch_taken = "false"
            
            context.report_progress(f"Condition evaluated to {condition_result}, taking {branch_taken} branch")
            
            return {
                "output_data": output_data,
                "condition_result": condition_result,
                "branch_taken": branch_taken
            }
            
        except Exception as e:
            return {
                "output_data": {},
                "condition_result": False,
                "branch_taken": "error"
            }
    
    def _evaluate_condition(self, condition_value: Dict[str, Any]) -> bool:
        """Evaluate the condition based on parameters."""
        condition_type = self.get_parameter("condition_type", "threshold")
        
        if condition_type == "threshold":
            return self._evaluate_threshold_condition(condition_value)
        elif condition_type == "comparison":
            return self._evaluate_comparison_condition(condition_value)
        elif condition_type == "custom":
            return self._evaluate_custom_condition(condition_value)
        else:
            return False
    
    def _evaluate_threshold_condition(self, condition_value: Dict[str, Any]) -> bool:
        """Evaluate threshold-based condition."""
        field_path = self.get_parameter("field_path", "value")
        operator = self.get_parameter("operator", "greater_than")
        threshold = self.get_parameter("threshold_value", 0)
        
        # Extract value from nested dict using field path
        value = self._get_nested_value(condition_value, field_path)
        
        if value is None:
            return False
        
        try:
            value = float(value)
            threshold = float(threshold)
            
            if operator == "greater_than":
                return value > threshold
            elif operator == "less_than":
                return value < threshold
            elif operator == "equals":
                return abs(value - threshold) < 1e-10  # Float comparison
            elif operator == "not_equals":
                return abs(value - threshold) >= 1e-10
            elif operator == "greater_equal":
                return value >= threshold
            elif operator == "less_equal":
                return value <= threshold
            else:
                return False
                
        except (ValueError, TypeError):
            return False
    
    def _evaluate_comparison_condition(self, condition_value: Dict[str, Any]) -> bool:
        """Evaluate comparison condition between two values."""
        # This could be extended to compare two different fields
        return self._evaluate_threshold_condition(condition_value)
    
    def _evaluate_custom_condition(self, condition_value: Dict[str, Any]) -> bool:
        """Evaluate custom Python condition (with safety restrictions)."""
        custom_condition = self.get_parameter("custom_condition", "")
        
        if not custom_condition:
            return False
        
        try:
            # Create safe evaluation context
            safe_dict = {
                "data": condition_value,
                "abs": abs,
                "min": min,
                "max": max,
                "len": len,
                "sum": sum,
                "any": any,
                "all": all
            }
            
            # Evaluate condition (restricted to safe operations)
            result = eval(custom_condition, {"__builtins__": {}}, safe_dict)
            return bool(result)
            
        except Exception:
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _validate_parameters(self) -> List[ValidationError]:
        """Validate node parameters."""
        errors = []
        
        condition_type = self.get_parameter("condition_type", "threshold")
        valid_types = ["threshold", "comparison", "custom"]
        
        if condition_type not in valid_types:
            errors.append(ValidationError(
                node_id=self.node_id,
                message=f"Condition type must be one of: {valid_types}",
                error_type="invalid_parameter"
            ))
        
        operator = self.get_parameter("operator", "greater_than")
        valid_operators = ["greater_than", "less_than", "equals", "not_equals", "greater_equal", "less_equal"]
        
        if operator not in valid_operators:
            errors.append(ValidationError(
                node_id=self.node_id,
                message=f"Operator must be one of: {valid_operators}",
                error_type="invalid_parameter"
            ))
        
        return errors


@register_node(
    category=NodeCategory.OUTPUT,
    display_name="Notification",
    description="Send notifications and alerts",
    icon="🔔",
    tags=["notification", "alert", "message"]
)
class NotificationNode(WorkflowNode):
    """Node for sending notifications and alerts."""
    
    _category = NodeCategory.OUTPUT
    _display_name = "Notification"
    _description = "Send notifications and alerts"
    _icon = "🔔"
    _tags = ["notification", "alert", "message"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("message", DataType.STRING, True,
                           "Message to send")
        self.add_input_port("data", DataType.DICT, False,
                           "Additional data to include", {})
        self.add_input_port("severity", DataType.STRING, False,
                           "Message severity (info, warning, error)", "info")
        
        # Output ports
        self.add_output_port("notification_sent", DataType.BOOLEAN,
                            "Whether notification was sent successfully")
        self.add_output_port("notification_id", DataType.STRING,
                            "Notification ID if applicable")
        self.add_output_port("send_status", DataType.STRING,
                            "Send operation status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "notification_channels": ["console"],  # console, email, webhook, slack
            "include_timestamp": True,
            "include_workflow_info": True,
            "webhook_url": "",
            "email_recipients": [],
            "slack_channel": "",
            "format_template": "{timestamp} [{severity}] {message}"
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute notification sending."""
        try:
            message = self.get_input_value("message", context)
            data = self.get_input_value("data", context)
            severity = self.get_input_value("severity", context)
            
            # Format message
            formatted_message = self._format_message(message, severity, data, context)
            
            # Send notifications through configured channels
            channels = self.get_parameter("notification_channels", ["console"])
            send_results = {}
            
            for channel in channels:
                try:
                    if channel == "console":
                        result = await self._send_console_notification(formatted_message, severity)
                    elif channel == "webhook":
                        result = await self._send_webhook_notification(formatted_message, data, severity)
                    elif channel == "email":
                        result = await self._send_email_notification(formatted_message, data, severity)
                    elif channel == "slack":
                        result = await self._send_slack_notification(formatted_message, data, severity)
                    else:
                        result = {"success": False, "error": f"Unknown channel: {channel}"}
                    
                    send_results[channel] = result
                    
                except Exception as e:
                    send_results[channel] = {"success": False, "error": str(e)}
            
            # Determine overall success
            successful_sends = [r for r in send_results.values() if r.get("success", False)]
            notification_sent = len(successful_sends) > 0
            
            # Generate notification ID
            notification_id = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(message) % 10000}"
            
            return {
                "notification_sent": notification_sent,
                "notification_id": notification_id,
                "send_status": "success" if notification_sent else "failed",
                "channel_results": send_results
            }
            
        except Exception as e:
            return {
                "notification_sent": False,
                "notification_id": "",
                "send_status": f"error: {str(e)}"
            }
    
    def _format_message(self, message: str, severity: str, data: Dict[str, Any], context) -> str:
        """Format notification message."""
        format_template = self.get_parameter("format_template", "{timestamp} [{severity}] {message}")
        
        format_vars = {
            "message": message,
            "severity": severity.upper(),
            "timestamp": datetime.now().isoformat() if self.get_parameter("include_timestamp", True) else "",
            "workflow_id": context.workflow_id if self.get_parameter("include_workflow_info", True) else "",
            "node_id": self.node_id if self.get_parameter("include_workflow_info", True) else ""
        }
        
        # Add data fields to format variables
        if isinstance(data, dict):
            for key, value in data.items():
                format_vars[f"data_{key}"] = str(value)
        
        try:
            return format_template.format(**format_vars)
        except KeyError:
            # Fallback to simple format if template has missing keys
            return f"[{severity.upper()}] {message}"
    
    async def _send_console_notification(self, message: str, severity: str) -> Dict[str, Any]:
        """Send notification to console."""
        try:
            # In a real implementation, this would use the logging system
            print(f"NOTIFICATION: {message}")
            return {"success": True, "channel": "console"}
        except Exception as e:
            return {"success": False, "error": str(e), "channel": "console"}
    
    async def _send_webhook_notification(self, message: str, data: Dict[str, Any], severity: str) -> Dict[str, Any]:
        """Send notification via webhook."""
        webhook_url = self.get_parameter("webhook_url", "")
        
        if not webhook_url:
            return {"success": False, "error": "No webhook URL configured", "channel": "webhook"}
        
        try:
            # In a real implementation, this would make an HTTP request
            payload = {
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            # Simulate webhook call
            await asyncio.sleep(0.1)  # Simulate network delay
            
            return {"success": True, "channel": "webhook", "payload": payload}
            
        except Exception as e:
            return {"success": False, "error": str(e), "channel": "webhook"}
    
    async def _send_email_notification(self, message: str, data: Dict[str, Any], severity: str) -> Dict[str, Any]:
        """Send notification via email."""
        recipients = self.get_parameter("email_recipients", [])
        
        if not recipients:
            return {"success": False, "error": "No email recipients configured", "channel": "email"}
        
        try:
            # In a real implementation, this would send actual emails
            email_data = {
                "to": recipients,
                "subject": f"Workflow Notification [{severity.upper()}]",
                "body": message,
                "data": data
            }
            
            # Simulate email sending
            await asyncio.sleep(0.2)  # Simulate email sending delay
            
            return {"success": True, "channel": "email", "recipients": len(recipients)}
            
        except Exception as e:
            return {"success": False, "error": str(e), "channel": "email"}
    
    async def _send_slack_notification(self, message: str, data: Dict[str, Any], severity: str) -> Dict[str, Any]:
        """Send notification to Slack."""
        slack_channel = self.get_parameter("slack_channel", "")
        
        if not slack_channel:
            return {"success": False, "error": "No Slack channel configured", "channel": "slack"}
        
        try:
            # In a real implementation, this would use Slack API
            slack_payload = {
                "channel": slack_channel,
                "text": message,
                "attachments": [
                    {
                        "color": self._get_slack_color(severity),
                        "fields": [
                            {"title": key, "value": str(value), "short": True}
                            for key, value in data.items()
                        ] if data else []
                    }
                ]
            }
            
            # Simulate Slack API call
            await asyncio.sleep(0.15)  # Simulate API delay
            
            return {"success": True, "channel": "slack", "slack_channel": slack_channel}
            
        except Exception as e:
            return {"success": False, "error": str(e), "channel": "slack"}
    
    def _get_slack_color(self, severity: str) -> str:
        """Get Slack color based on severity."""
        color_map = {
            "info": "good",
            "warning": "warning", 
            "error": "danger"
        }
        return color_map.get(severity.lower(), "good")