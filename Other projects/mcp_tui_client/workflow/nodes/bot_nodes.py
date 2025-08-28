"""
Bot operation nodes for workflow system.

This module provides nodes for bot creation, deployment, and monitoring.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from ..node_base import WorkflowNode, DataType, ValidationError
from ..node_registry import register_node, NodeCategory


@register_node(
    category=NodeCategory.TRADING,
    display_name="Bot Management",
    description="Create and manage trading bots",
    icon="🤖",
    tags=["bot", "trading", "management"]
)
class BotNode(WorkflowNode):
    """Node for creating and managing trading bots."""
    
    _category = NodeCategory.TRADING
    _display_name = "Bot Management"
    _description = "Create and manage trading bots"
    _icon = "🤖"
    _tags = ["bot", "trading", "management"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("action", DataType.STRING, True,
                           "Bot action (create, start, stop, delete)")
        self.add_input_port("bot_config", DataType.BOT_CONFIG, False,
                           "Bot configuration for creation")
        self.add_input_port("bot_id", DataType.STRING, False,
                           "Bot ID for existing bot operations")
        self.add_input_port("lab_results", DataType.BACKTEST_RESULT, False,
                           "Lab results to base bot on")
        
        # Output ports
        self.add_output_port("bot_id", DataType.STRING,
                            "Bot ID")
        self.add_output_port("bot_status", DataType.STRING,
                            "Bot status")
        self.add_output_port("operation_result", DataType.DICT,
                            "Operation result details")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "auto_start": True,
            "safety_checks": True,
            "timeout": 60,  # seconds
            "confirm_destructive": True
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute bot operation."""
        try:
            action = self.get_input_value("action", context).lower()
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            if action == "create":
                return await self._create_bot(context, mcp_client)
            elif action == "start":
                return await self._start_bot(context, mcp_client)
            elif action == "stop":
                return await self._stop_bot(context, mcp_client)
            elif action == "delete":
                return await self._delete_bot(context, mcp_client)
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except Exception as e:
            return {
                "bot_id": None,
                "bot_status": "error",
                "operation_result": {"error": str(e)}
            }
    
    async def _create_bot(self, context, mcp_client) -> Dict[str, Any]:
        """Create a new bot."""
        bot_config = self.get_input_value("bot_config", context)
        lab_results = self.get_input_value("lab_results", context)
        
        if not bot_config and not lab_results:
            raise ValueError("Either bot_config or lab_results must be provided")
        
        # If lab results provided, create bot from lab
        if lab_results:
            lab_id = lab_results.get("lab_id")
            if not lab_id:
                raise ValueError("Lab results must contain lab_id")
            
            result = await mcp_client.call_tool("create_bot_from_lab", {
                "lab_id": lab_id,
                "auto_start": self.get_parameter("auto_start", True)
            })
        else:
            # Create bot from configuration
            result = await mcp_client.call_tool("create_bot", {
                "config": bot_config,
                "auto_start": self.get_parameter("auto_start", True)
            })
        
        if result.get("success"):
            bot_id = result.get("bot_id")
            return {
                "bot_id": bot_id,
                "bot_status": "created",
                "operation_result": result
            }
        else:
            raise RuntimeError(f"Bot creation failed: {result.get('error')}")
    
    async def _start_bot(self, context, mcp_client) -> Dict[str, Any]:
        """Start an existing bot."""
        bot_id = self.get_input_value("bot_id", context)
        if not bot_id:
            raise ValueError("bot_id is required for start action")
        
        # Safety checks if enabled
        if self.get_parameter("safety_checks", True):
            status_result = await mcp_client.call_tool("get_bot_status", {"bot_id": bot_id})
            if status_result.get("status") == "running":
                return {
                    "bot_id": bot_id,
                    "bot_status": "already_running",
                    "operation_result": {"message": "Bot is already running"}
                }
        
        result = await mcp_client.call_tool("start_bot", {"bot_id": bot_id})
        
        if result.get("success"):
            return {
                "bot_id": bot_id,
                "bot_status": "started",
                "operation_result": result
            }
        else:
            raise RuntimeError(f"Bot start failed: {result.get('error')}")
    
    async def _stop_bot(self, context, mcp_client) -> Dict[str, Any]:
        """Stop an existing bot."""
        bot_id = self.get_input_value("bot_id", context)
        if not bot_id:
            raise ValueError("bot_id is required for stop action")
        
        result = await mcp_client.call_tool("stop_bot", {"bot_id": bot_id})
        
        if result.get("success"):
            return {
                "bot_id": bot_id,
                "bot_status": "stopped",
                "operation_result": result
            }
        else:
            raise RuntimeError(f"Bot stop failed: {result.get('error')}")
    
    async def _delete_bot(self, context, mcp_client) -> Dict[str, Any]:
        """Delete an existing bot."""
        bot_id = self.get_input_value("bot_id", context)
        if not bot_id:
            raise ValueError("bot_id is required for delete action")
        
        # Confirmation for destructive action
        if self.get_parameter("confirm_destructive", True):
            # In a real implementation, this might prompt the user
            # For now, we'll just log the action
            context.report_progress(f"Deleting bot {bot_id}")
        
        result = await mcp_client.call_tool("delete_bot", {"bot_id": bot_id})
        
        if result.get("success"):
            return {
                "bot_id": bot_id,
                "bot_status": "deleted",
                "operation_result": result
            }
        else:
            raise RuntimeError(f"Bot deletion failed: {result.get('error')}")


@register_node(
    category=NodeCategory.TRADING,
    display_name="Bot Deployment",
    description="Deploy bot from lab results with validation",
    icon="🚀",
    tags=["bot", "deployment", "validation"]
)
class BotDeploymentNode(WorkflowNode):
    """Node for deploying bots from lab results with validation."""
    
    _category = NodeCategory.TRADING
    _display_name = "Bot Deployment"
    _description = "Deploy bot from lab results with validation"
    _icon = "🚀"
    _tags = ["bot", "deployment", "validation"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("lab_results", DataType.BACKTEST_RESULT, True,
                           "Lab results to deploy")
        self.add_input_port("performance_metrics", DataType.PERFORMANCE_METRICS, False,
                           "Performance metrics for validation")
        self.add_input_port("deployment_config", DataType.DICT, False,
                           "Deployment configuration", {})
        
        # Output ports
        self.add_output_port("bot_id", DataType.STRING,
                            "Deployed bot ID")
        self.add_output_port("deployment_status", DataType.STRING,
                            "Deployment status")
        self.add_output_port("validation_results", DataType.DICT,
                            "Validation results")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "min_total_return": 0.05,  # 5%
            "max_drawdown": 0.20,  # 20%
            "min_sharpe_ratio": 0.5,
            "min_win_rate": 0.4,  # 40%
            "validate_before_deploy": True,
            "auto_start": True,
            "paper_trading": False
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute bot deployment."""
        try:
            lab_results = self.get_input_value("lab_results", context)
            performance_metrics = self.get_input_value("performance_metrics", context)
            deployment_config = self.get_input_value("deployment_config", context) or {}
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            # Validate performance if enabled
            validation_results = {}
            if self.get_parameter("validate_before_deploy", True):
                validation_results = self._validate_performance(performance_metrics)
                
                if not validation_results.get("passed", False):
                    return {
                        "bot_id": None,
                        "deployment_status": "validation_failed",
                        "validation_results": validation_results
                    }
            
            # Prepare deployment configuration
            deploy_config = {
                "lab_id": lab_results.get("lab_id"),
                "auto_start": self.get_parameter("auto_start", True),
                "paper_trading": self.get_parameter("paper_trading", False),
                **deployment_config
            }
            
            # Deploy bot
            result = await mcp_client.call_tool("deploy_bot_from_lab", deploy_config)
            
            if result.get("success"):
                return {
                    "bot_id": result.get("bot_id"),
                    "deployment_status": "deployed",
                    "validation_results": validation_results
                }
            else:
                raise RuntimeError(f"Deployment failed: {result.get('error')}")
                
        except Exception as e:
            return {
                "bot_id": None,
                "deployment_status": f"error: {str(e)}",
                "validation_results": {}
            }
    
    def _validate_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance metrics against thresholds."""
        if not metrics:
            return {"passed": False, "reason": "No performance metrics provided"}
        
        validation_results = {
            "passed": True,
            "checks": [],
            "warnings": []
        }
        
        # Check total return
        total_return = metrics.get("total_return", 0)
        min_return = self.get_parameter("min_total_return", 0.05)
        check_result = {
            "metric": "total_return",
            "value": total_return,
            "threshold": min_return,
            "passed": total_return >= min_return
        }
        validation_results["checks"].append(check_result)
        if not check_result["passed"]:
            validation_results["passed"] = False
        
        # Check maximum drawdown
        max_drawdown = abs(metrics.get("max_drawdown", 0))
        max_dd_threshold = self.get_parameter("max_drawdown", 0.20)
        check_result = {
            "metric": "max_drawdown",
            "value": max_drawdown,
            "threshold": max_dd_threshold,
            "passed": max_drawdown <= max_dd_threshold
        }
        validation_results["checks"].append(check_result)
        if not check_result["passed"]:
            validation_results["passed"] = False
        
        # Check Sharpe ratio
        sharpe_ratio = metrics.get("sharpe_ratio", 0)
        min_sharpe = self.get_parameter("min_sharpe_ratio", 0.5)
        check_result = {
            "metric": "sharpe_ratio",
            "value": sharpe_ratio,
            "threshold": min_sharpe,
            "passed": sharpe_ratio >= min_sharpe
        }
        validation_results["checks"].append(check_result)
        if not check_result["passed"]:
            validation_results["warnings"].append(f"Low Sharpe ratio: {sharpe_ratio:.2f}")
        
        # Check win rate
        win_rate = metrics.get("win_rate", 0)
        min_win_rate = self.get_parameter("min_win_rate", 0.4)
        check_result = {
            "metric": "win_rate",
            "value": win_rate,
            "threshold": min_win_rate,
            "passed": win_rate >= min_win_rate
        }
        validation_results["checks"].append(check_result)
        if not check_result["passed"]:
            validation_results["warnings"].append(f"Low win rate: {win_rate:.1%}")
        
        return validation_results


@register_node(
    category=NodeCategory.TRADING,
    display_name="Bot Monitoring",
    description="Monitor bot performance and status",
    icon="📈",
    tags=["bot", "monitoring", "performance"]
)
class BotMonitoringNode(WorkflowNode):
    """Node for monitoring bot performance and status."""
    
    _category = NodeCategory.TRADING
    _display_name = "Bot Monitoring"
    _description = "Monitor bot performance and status"
    _icon = "📈"
    _tags = ["bot", "monitoring", "performance"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("bot_id", DataType.STRING, True,
                           "Bot ID to monitor")
        self.add_input_port("monitoring_duration", DataType.INTEGER, False,
                           "Monitoring duration in seconds", 300)
        
        # Output ports
        self.add_output_port("bot_status", DataType.STRING,
                            "Current bot status")
        self.add_output_port("performance_data", DataType.DICT,
                            "Performance data")
        self.add_output_port("alerts", DataType.LIST,
                            "Generated alerts")
        self.add_output_port("monitoring_summary", DataType.DICT,
                            "Monitoring summary")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "poll_interval": 30,  # seconds
            "alert_on_stop": True,
            "alert_on_error": True,
            "performance_alert_threshold": -0.05,  # -5%
            "collect_trade_data": True
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute bot monitoring."""
        try:
            bot_id = self.get_input_value("bot_id", context)
            duration = self.get_input_value("monitoring_duration", context)
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            poll_interval = self.get_parameter("poll_interval", 30)
            alerts = []
            performance_history = []
            
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=duration)
            
            while datetime.now() < end_time:
                # Get bot status
                status_result = await mcp_client.call_tool("get_bot_status", {"bot_id": bot_id})
                current_status = status_result.get("status", "unknown")
                
                # Get performance data
                perf_result = await mcp_client.call_tool("get_bot_performance", {"bot_id": bot_id})
                performance_data = perf_result.get("performance", {})
                
                # Record performance history
                performance_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "status": current_status,
                    "performance": performance_data
                })
                
                # Check for alerts
                new_alerts = self._check_alerts(current_status, performance_data, bot_id)
                alerts.extend(new_alerts)
                
                # Report progress
                elapsed = (datetime.now() - start_time).total_seconds()
                progress = (elapsed / duration) * 100
                context.report_progress(f"Monitoring bot {bot_id}: {progress:.1f}% complete")
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
            
            # Generate monitoring summary
            summary = self._generate_summary(performance_history, alerts)
            
            return {
                "bot_status": current_status,
                "performance_data": performance_data,
                "alerts": alerts,
                "monitoring_summary": summary
            }
            
        except Exception as e:
            return {
                "bot_status": "error",
                "performance_data": {},
                "alerts": [{"type": "error", "message": str(e)}],
                "monitoring_summary": {}
            }
    
    def _check_alerts(self, status: str, performance: Dict[str, Any], bot_id: str) -> List[Dict[str, Any]]:
        """Check for alert conditions."""
        alerts = []
        
        # Status alerts
        if self.get_parameter("alert_on_stop", True) and status == "stopped":
            alerts.append({
                "type": "status",
                "severity": "warning",
                "message": f"Bot {bot_id} has stopped",
                "timestamp": datetime.now().isoformat()
            })
        
        if self.get_parameter("alert_on_error", True) and status == "error":
            alerts.append({
                "type": "status",
                "severity": "error",
                "message": f"Bot {bot_id} encountered an error",
                "timestamp": datetime.now().isoformat()
            })
        
        # Performance alerts
        current_return = performance.get("total_return", 0)
        threshold = self.get_parameter("performance_alert_threshold", -0.05)
        
        if current_return < threshold:
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"Bot {bot_id} performance below threshold: {current_return:.2%}",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _generate_summary(self, performance_history: List[Dict], alerts: List[Dict]) -> Dict[str, Any]:
        """Generate monitoring summary."""
        if not performance_history:
            return {}
        
        # Calculate summary statistics
        returns = [p.get("performance", {}).get("total_return", 0) for p in performance_history]
        statuses = [p.get("status", "unknown") for p in performance_history]
        
        summary = {
            "monitoring_duration": len(performance_history) * self.get_parameter("poll_interval", 30),
            "data_points": len(performance_history),
            "final_return": returns[-1] if returns else 0,
            "max_return": max(returns) if returns else 0,
            "min_return": min(returns) if returns else 0,
            "status_changes": len(set(statuses)),
            "alert_count": len(alerts),
            "alert_types": list(set(alert.get("type", "unknown") for alert in alerts))
        }
        
        return summary