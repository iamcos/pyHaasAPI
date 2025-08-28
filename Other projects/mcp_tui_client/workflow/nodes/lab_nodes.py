"""
Lab operation nodes for workflow system.

This module provides nodes for lab creation, backtesting, and parameter optimization.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta

from ..node_base import WorkflowNode, DataType, ValidationError
from ..node_registry import register_node, NodeCategory


@register_node(
    category=NodeCategory.TRADING,
    display_name="Lab Creation",
    description="Create and configure a new trading lab",
    icon="🧪",
    tags=["lab", "backtest", "creation"]
)
class LabNode(WorkflowNode):
    """Node for creating and managing trading labs."""
    
    _category = NodeCategory.TRADING
    _display_name = "Lab Creation"
    _description = "Create and configure a new trading lab"
    _icon = "🧪"
    _tags = ["lab", "backtest", "creation"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("trading_pair", DataType.STRING, True, 
                           "Trading pair (e.g., BTC_USDT)")
        self.add_input_port("script_id", DataType.STRING, True,
                           "HaasScript ID to use")
        self.add_input_port("account_id", DataType.STRING, True,
                           "Account ID for backtesting")
        self.add_input_port("parameters", DataType.DICT, False,
                           "Script parameters", {})
        self.add_input_port("start_date", DataType.STRING, False,
                           "Backtest start date (ISO format)")
        self.add_input_port("end_date", DataType.STRING, False,
                           "Backtest end date (ISO format)")
        
        # Output ports
        self.add_output_port("lab_id", DataType.STRING,
                            "Created lab ID")
        self.add_output_port("lab_config", DataType.DICT,
                            "Lab configuration")
        self.add_output_port("status", DataType.STRING,
                            "Creation status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "auto_start": True,
            "history_depth": 30,  # days
            "leverage": 1.0,
            "fee_percentage": 0.1,
            "timeout": 300  # seconds
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute lab creation."""
        try:
            # Get input values
            trading_pair = self.get_input_value("trading_pair", context)
            script_id = self.get_input_value("script_id", context)
            account_id = self.get_input_value("account_id", context)
            parameters = self.get_input_value("parameters", context) or {}
            start_date = self.get_input_value("start_date", context)
            end_date = self.get_input_value("end_date", context)
            
            # Get MCP client from context
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available in execution context")
            
            # Prepare lab configuration
            lab_config = {
                "name": f"Lab_{trading_pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "trading_pair": trading_pair,
                "script_id": script_id,
                "account_id": account_id,
                "parameters": parameters,
                "leverage": self.get_parameter("leverage", 1.0),
                "fee_percentage": self.get_parameter("fee_percentage", 0.1),
                "history_depth": self.get_parameter("history_depth", 30)
            }
            
            # Set date range if provided
            if start_date:
                lab_config["start_date"] = start_date
            if end_date:
                lab_config["end_date"] = end_date
            
            # Create lab via MCP
            result = await mcp_client.call_tool("create_lab", lab_config)
            
            if result.get("success"):
                lab_id = result.get("lab_id")
                
                # Auto-start if configured
                if self.get_parameter("auto_start", True):
                    await mcp_client.call_tool("start_lab", {"lab_id": lab_id})
                
                return {
                    "lab_id": lab_id,
                    "lab_config": lab_config,
                    "status": "created"
                }
            else:
                raise RuntimeError(f"Lab creation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            return {
                "lab_id": None,
                "lab_config": {},
                "status": f"error: {str(e)}"
            }
    
    def _validate_parameters(self) -> List[ValidationError]:
        """Validate node parameters."""
        errors = []
        
        leverage = self.get_parameter("leverage", 1.0)
        if not isinstance(leverage, (int, float)) or leverage <= 0:
            errors.append(ValidationError(
                node_id=self.node_id,
                message="Leverage must be a positive number",
                error_type="invalid_parameter"
            ))
        
        fee_percentage = self.get_parameter("fee_percentage", 0.1)
        if not isinstance(fee_percentage, (int, float)) or fee_percentage < 0:
            errors.append(ValidationError(
                node_id=self.node_id,
                message="Fee percentage must be non-negative",
                error_type="invalid_parameter"
            ))
        
        return errors


@register_node(
    category=NodeCategory.TRADING,
    display_name="Backtest Execution",
    description="Execute backtest and wait for results",
    icon="📊",
    tags=["backtest", "execution", "results"]
)
class BacktestNode(WorkflowNode):
    """Node for executing backtests and retrieving results."""
    
    _category = NodeCategory.TRADING
    _display_name = "Backtest Execution"
    _description = "Execute backtest and wait for results"
    _icon = "📊"
    _tags = ["backtest", "execution", "results"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("lab_id", DataType.STRING, True,
                           "Lab ID to execute")
        self.add_input_port("wait_for_completion", DataType.BOOLEAN, False,
                           "Wait for backtest completion", True)
        
        # Output ports
        self.add_output_port("backtest_results", DataType.BACKTEST_RESULT,
                            "Backtest results")
        self.add_output_port("performance_metrics", DataType.PERFORMANCE_METRICS,
                            "Performance metrics")
        self.add_output_port("trade_log", DataType.TRADE_LOG,
                            "Trade execution log")
        self.add_output_port("execution_status", DataType.STRING,
                            "Execution status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "timeout": 1800,  # 30 minutes
            "poll_interval": 10,  # seconds
            "include_trade_log": True,
            "calculate_metrics": True
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute backtest."""
        try:
            lab_id = self.get_input_value("lab_id", context)
            wait_for_completion = self.get_input_value("wait_for_completion", context)
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            # Start backtest
            start_result = await mcp_client.call_tool("start_backtest", {"lab_id": lab_id})
            
            if not start_result.get("success"):
                raise RuntimeError(f"Failed to start backtest: {start_result.get('error')}")
            
            if not wait_for_completion:
                return {
                    "backtest_results": None,
                    "performance_metrics": None,
                    "trade_log": None,
                    "execution_status": "started"
                }
            
            # Wait for completion
            timeout = self.get_parameter("timeout", 1800)
            poll_interval = self.get_parameter("poll_interval", 10)
            start_time = datetime.now()
            
            while (datetime.now() - start_time).total_seconds() < timeout:
                status_result = await mcp_client.call_tool("get_lab_status", {"lab_id": lab_id})
                
                if status_result.get("status") == "completed":
                    # Get results
                    results = await mcp_client.call_tool("get_backtest_results", {"lab_id": lab_id})
                    
                    output = {
                        "backtest_results": results,
                        "execution_status": "completed"
                    }
                    
                    # Calculate performance metrics if requested
                    if self.get_parameter("calculate_metrics", True):
                        metrics = await self._calculate_performance_metrics(results, mcp_client)
                        output["performance_metrics"] = metrics
                    
                    # Get trade log if requested
                    if self.get_parameter("include_trade_log", True):
                        trade_log = await mcp_client.call_tool("get_trade_log", {"lab_id": lab_id})
                        output["trade_log"] = trade_log
                    
                    return output
                
                elif status_result.get("status") == "failed":
                    raise RuntimeError(f"Backtest failed: {status_result.get('error')}")
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
            
            # Timeout reached
            return {
                "backtest_results": None,
                "performance_metrics": None,
                "trade_log": None,
                "execution_status": "timeout"
            }
            
        except Exception as e:
            return {
                "backtest_results": None,
                "performance_metrics": None,
                "trade_log": None,
                "execution_status": f"error: {str(e)}"
            }
    
    async def _calculate_performance_metrics(self, results: Dict[str, Any], 
                                           mcp_client) -> Dict[str, Any]:
        """Calculate performance metrics from backtest results."""
        try:
            metrics_result = await mcp_client.call_tool("calculate_performance_metrics", {
                "backtest_results": results
            })
            return metrics_result.get("metrics", {})
        except Exception:
            return {}


@register_node(
    category=NodeCategory.TRADING,
    display_name="Parameter Optimization",
    description="Optimize script parameters using various algorithms",
    icon="🎯",
    tags=["optimization", "parameters", "genetic", "pso"]
)
class ParameterOptimizationNode(WorkflowNode):
    """Node for parameter optimization."""
    
    _category = NodeCategory.TRADING
    _display_name = "Parameter Optimization"
    _description = "Optimize script parameters using various algorithms"
    _icon = "🎯"
    _tags = ["optimization", "parameters", "genetic", "pso"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("lab_id", DataType.STRING, True,
                           "Lab ID to optimize")
        self.add_input_port("parameter_ranges", DataType.DICT, True,
                           "Parameter ranges for optimization")
        self.add_input_port("optimization_target", DataType.STRING, False,
                           "Optimization target metric", "total_return")
        
        # Output ports
        self.add_output_port("best_parameters", DataType.DICT,
                            "Best parameter set found")
        self.add_output_port("best_performance", DataType.PERFORMANCE_METRICS,
                            "Performance of best parameters")
        self.add_output_port("optimization_history", DataType.LIST,
                            "Optimization history")
        self.add_output_port("optimization_status", DataType.STRING,
                            "Optimization status")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "algorithm": "genetic",  # genetic, pso, random, grid
            "population_size": 20,
            "generations": 10,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "timeout": 3600,  # 1 hour
            "parallel_evaluations": 4
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute parameter optimization."""
        try:
            lab_id = self.get_input_value("lab_id", context)
            parameter_ranges = self.get_input_value("parameter_ranges", context)
            optimization_target = self.get_input_value("optimization_target", context)
            
            mcp_client = context.execution_state.get("mcp_client")
            if not mcp_client:
                raise RuntimeError("MCP client not available")
            
            # Prepare optimization configuration
            optimization_config = {
                "lab_id": lab_id,
                "parameter_ranges": parameter_ranges,
                "optimization_target": optimization_target,
                "algorithm": self.get_parameter("algorithm", "genetic"),
                "population_size": self.get_parameter("population_size", 20),
                "generations": self.get_parameter("generations", 10),
                "mutation_rate": self.get_parameter("mutation_rate", 0.1),
                "crossover_rate": self.get_parameter("crossover_rate", 0.8),
                "parallel_evaluations": self.get_parameter("parallel_evaluations", 4)
            }
            
            # Start optimization
            result = await mcp_client.call_tool("start_parameter_optimization", optimization_config)
            
            if not result.get("success"):
                raise RuntimeError(f"Failed to start optimization: {result.get('error')}")
            
            optimization_id = result.get("optimization_id")
            
            # Wait for completion
            timeout = self.get_parameter("timeout", 3600)
            start_time = datetime.now()
            
            while (datetime.now() - start_time).total_seconds() < timeout:
                status_result = await mcp_client.call_tool("get_optimization_status", {
                    "optimization_id": optimization_id
                })
                
                if status_result.get("status") == "completed":
                    # Get optimization results
                    results = await mcp_client.call_tool("get_optimization_results", {
                        "optimization_id": optimization_id
                    })
                    
                    return {
                        "best_parameters": results.get("best_parameters", {}),
                        "best_performance": results.get("best_performance", {}),
                        "optimization_history": results.get("history", []),
                        "optimization_status": "completed"
                    }
                
                elif status_result.get("status") == "failed":
                    raise RuntimeError(f"Optimization failed: {status_result.get('error')}")
                
                # Report progress
                progress = status_result.get("progress", 0)
                context.report_progress(f"Optimization progress: {progress:.1f}%")
                
                await asyncio.sleep(30)  # Check every 30 seconds
            
            # Timeout reached
            return {
                "best_parameters": {},
                "best_performance": {},
                "optimization_history": [],
                "optimization_status": "timeout"
            }
            
        except Exception as e:
            return {
                "best_parameters": {},
                "best_performance": {},
                "optimization_history": [],
                "optimization_status": f"error: {str(e)}"
            }
    
    def _validate_parameters(self) -> List[ValidationError]:
        """Validate node parameters."""
        errors = []
        
        algorithm = self.get_parameter("algorithm", "genetic")
        valid_algorithms = ["genetic", "pso", "random", "grid"]
        if algorithm not in valid_algorithms:
            errors.append(ValidationError(
                node_id=self.node_id,
                message=f"Algorithm must be one of: {valid_algorithms}",
                error_type="invalid_parameter"
            ))
        
        population_size = self.get_parameter("population_size", 20)
        if not isinstance(population_size, int) or population_size < 1:
            errors.append(ValidationError(
                node_id=self.node_id,
                message="Population size must be a positive integer",
                error_type="invalid_parameter"
            ))
        
        return errors