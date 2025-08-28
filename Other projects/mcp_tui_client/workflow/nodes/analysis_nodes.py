"""
Analysis nodes for workflow system.

This module provides nodes for performance analysis, risk analysis, and reporting.
"""

from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime, timedelta
import statistics
import math

from ..node_base import WorkflowNode, DataType, ValidationError
from ..node_registry import register_node, NodeCategory


@register_node(
    category=NodeCategory.ANALYSIS,
    display_name="Performance Analysis",
    description="Analyze trading performance and generate metrics",
    icon="📊",
    tags=["analysis", "performance", "metrics"]
)
class AnalysisNode(WorkflowNode):
    """Node for general performance analysis."""
    
    _category = NodeCategory.ANALYSIS
    _display_name = "Performance Analysis"
    _description = "Analyze trading performance and generate metrics"
    _icon = "📊"
    _tags = ["analysis", "performance", "metrics"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("backtest_data", DataType.BACKTEST_RESULT, True,
                           "Backtest results to analyze")
        self.add_input_port("analysis_type", DataType.STRING, False,
                           "Type of analysis to perform", "comprehensive")
        self.add_input_port("benchmark_data", DataType.DICT, False,
                           "Benchmark data for comparison")
        
        # Output ports
        self.add_output_port("metrics", DataType.PERFORMANCE_METRICS,
                            "Calculated performance metrics")
        self.add_output_port("charts", DataType.CHART_DATA,
                            "Chart data for visualization")
        self.add_output_port("insights", DataType.LIST,
                            "Generated insights and recommendations")
        self.add_output_port("analysis_report", DataType.DICT,
                            "Complete analysis report")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "risk_free_rate": 0.02,  # 2% annual
            "confidence_level": 0.95,
            "include_charts": True,
            "generate_insights": True,
            "benchmark_comparison": True
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute performance analysis."""
        try:
            backtest_data = self.get_input_value("backtest_data", context)
            analysis_type = self.get_input_value("analysis_type", context)
            benchmark_data = self.get_input_value("benchmark_data", context)
            
            if not backtest_data:
                raise ValueError("Backtest data is required for analysis")
            
            # Extract trade data and equity curve
            trades = backtest_data.get("trades", [])
            equity_curve = backtest_data.get("equity_curve", [])
            
            # Calculate metrics
            metrics = self._calculate_metrics(trades, equity_curve)
            
            # Generate charts if requested
            charts = {}
            if self.get_parameter("include_charts", True):
                charts = self._generate_charts(equity_curve, trades)
            
            # Generate insights if requested
            insights = []
            if self.get_parameter("generate_insights", True):
                insights = self._generate_insights(metrics, trades)
            
            # Benchmark comparison if data provided
            if benchmark_data and self.get_parameter("benchmark_comparison", True):
                benchmark_metrics = self._compare_to_benchmark(metrics, benchmark_data)
                metrics.update(benchmark_metrics)
            
            # Create analysis report
            analysis_report = {
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "trade_count": len(trades),
                "analysis_period": self._get_analysis_period(trades),
                "insights_count": len(insights)
            }
            
            return {
                "metrics": metrics,
                "charts": charts,
                "insights": insights,
                "analysis_report": analysis_report
            }
            
        except Exception as e:
            return {
                "metrics": {},
                "charts": {},
                "insights": [{"type": "error", "message": str(e)}],
                "analysis_report": {"error": str(e)}
            }
    
    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        if not trades or not equity_curve:
            return {}
        
        # Basic trade metrics
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
        
        total_trades = len(trades)
        winning_trades_count = len(winning_trades)
        losing_trades_count = len(losing_trades)
        
        win_rate = winning_trades_count / total_trades if total_trades > 0 else 0
        
        # P&L calculations
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        avg_win = statistics.mean([t.get("pnl", 0) for t in winning_trades]) if winning_trades else 0
        avg_loss = statistics.mean([t.get("pnl", 0) for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(avg_win * winning_trades_count / (avg_loss * losing_trades_count)) if avg_loss != 0 and losing_trades_count > 0 else float('inf')
        
        # Equity curve analysis
        equity_values = [point.get("equity", 0) for point in equity_curve]
        returns = self._calculate_returns(equity_values)
        
        # Risk metrics
        total_return = (equity_values[-1] - equity_values[0]) / equity_values[0] if equity_values[0] != 0 else 0
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        max_drawdown = self._calculate_max_drawdown(equity_values)
        
        # Risk-adjusted returns
        risk_free_rate = self.get_parameter("risk_free_rate", 0.02)
        sharpe_ratio = (total_return - risk_free_rate) / volatility if volatility != 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = [r for r in returns if r < 0]
        downside_deviation = statistics.stdev(downside_returns) if len(downside_returns) > 1 else 0
        sortino_ratio = (total_return - risk_free_rate) / downside_deviation if downside_deviation != 0 else 0
        
        return {
            "total_return": total_return,
            "total_trades": total_trades,
            "winning_trades": winning_trades_count,
            "losing_trades": losing_trades_count,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "total_pnl": total_pnl,
            "max_drawdown": max_drawdown,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        }
    
    def _calculate_returns(self, equity_values: List[float]) -> List[float]:
        """Calculate period returns from equity curve."""
        returns = []
        for i in range(1, len(equity_values)):
            if equity_values[i-1] != 0:
                ret = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                returns.append(ret)
        return returns
    
    def _calculate_max_drawdown(self, equity_values: List[float]) -> float:
        """Calculate maximum drawdown."""
        if not equity_values:
            return 0
        
        peak = equity_values[0]
        max_dd = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak != 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def _generate_charts(self, equity_curve: List[Dict], trades: List[Dict]) -> Dict[str, Any]:
        """Generate chart data for visualization."""
        charts = {}
        
        # Equity curve chart
        if equity_curve:
            charts["equity_curve"] = {
                "type": "line",
                "data": [
                    {
                        "x": point.get("timestamp", ""),
                        "y": point.get("equity", 0)
                    }
                    for point in equity_curve
                ],
                "title": "Equity Curve",
                "x_label": "Time",
                "y_label": "Equity"
            }
        
        # Drawdown chart
        if equity_curve:
            equity_values = [point.get("equity", 0) for point in equity_curve]
            drawdowns = self._calculate_drawdown_series(equity_values)
            
            charts["drawdown"] = {
                "type": "area",
                "data": [
                    {
                        "x": equity_curve[i].get("timestamp", ""),
                        "y": -drawdowns[i]  # Negative for visualization
                    }
                    for i in range(len(drawdowns))
                ],
                "title": "Drawdown",
                "x_label": "Time",
                "y_label": "Drawdown %"
            }
        
        # Trade distribution
        if trades:
            pnl_values = [t.get("pnl", 0) for t in trades]
            charts["trade_distribution"] = {
                "type": "histogram",
                "data": pnl_values,
                "title": "Trade P&L Distribution",
                "x_label": "P&L",
                "y_label": "Frequency"
            }
        
        return charts
    
    def _calculate_drawdown_series(self, equity_values: List[float]) -> List[float]:
        """Calculate drawdown series."""
        drawdowns = []
        peak = equity_values[0] if equity_values else 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak != 0 else 0
            drawdowns.append(drawdown)
        
        return drawdowns
    
    def _generate_insights(self, metrics: Dict[str, Any], trades: List[Dict]) -> List[Dict[str, Any]]:
        """Generate insights and recommendations."""
        insights = []
        
        # Win rate insights
        win_rate = metrics.get("win_rate", 0)
        if win_rate < 0.4:
            insights.append({
                "type": "warning",
                "category": "win_rate",
                "message": f"Low win rate ({win_rate:.1%}). Consider improving entry signals.",
                "recommendation": "Review entry criteria and consider tighter filters."
            })
        elif win_rate > 0.7:
            insights.append({
                "type": "positive",
                "category": "win_rate",
                "message": f"High win rate ({win_rate:.1%}). Good entry signal quality.",
                "recommendation": "Consider increasing position sizes if risk allows."
            })
        
        # Profit factor insights
        profit_factor = metrics.get("profit_factor", 0)
        if profit_factor < 1.2:
            insights.append({
                "type": "warning",
                "category": "profit_factor",
                "message": f"Low profit factor ({profit_factor:.2f}). Strategy may not be profitable long-term.",
                "recommendation": "Improve exit strategy or reduce trading frequency."
            })
        
        # Sharpe ratio insights
        sharpe_ratio = metrics.get("sharpe_ratio", 0)
        if sharpe_ratio < 0.5:
            insights.append({
                "type": "warning",
                "category": "risk_adjusted_return",
                "message": f"Low Sharpe ratio ({sharpe_ratio:.2f}). Poor risk-adjusted returns.",
                "recommendation": "Consider reducing position sizes or improving timing."
            })
        elif sharpe_ratio > 1.0:
            insights.append({
                "type": "positive",
                "category": "risk_adjusted_return",
                "message": f"Good Sharpe ratio ({sharpe_ratio:.2f}). Strong risk-adjusted returns.",
                "recommendation": "Strategy shows good risk management."
            })
        
        # Drawdown insights
        max_drawdown = metrics.get("max_drawdown", 0)
        if max_drawdown > 0.2:
            insights.append({
                "type": "warning",
                "category": "drawdown",
                "message": f"High maximum drawdown ({max_drawdown:.1%}). High risk strategy.",
                "recommendation": "Implement stricter risk management or reduce position sizes."
            })
        
        return insights
    
    def _compare_to_benchmark(self, metrics: Dict[str, Any], benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare performance to benchmark."""
        benchmark_metrics = {}
        
        strategy_return = metrics.get("total_return", 0)
        benchmark_return = benchmark_data.get("total_return", 0)
        
        benchmark_metrics["benchmark_return"] = benchmark_return
        benchmark_metrics["excess_return"] = strategy_return - benchmark_return
        benchmark_metrics["outperformed_benchmark"] = strategy_return > benchmark_return
        
        return benchmark_metrics
    
    def _get_analysis_period(self, trades: List[Dict]) -> Dict[str, Any]:
        """Get analysis period information."""
        if not trades:
            return {}
        
        timestamps = [t.get("timestamp") for t in trades if t.get("timestamp")]
        if not timestamps:
            return {}
        
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        return {
            "start_date": start_time,
            "end_date": end_time,
            "duration_days": (datetime.fromisoformat(end_time.replace('Z', '+00:00')) - 
                            datetime.fromisoformat(start_time.replace('Z', '+00:00'))).days
        }


@register_node(
    category=NodeCategory.ANALYSIS,
    display_name="Performance Analysis",
    description="Detailed performance analysis with advanced metrics",
    icon="📈",
    tags=["performance", "analysis", "advanced", "metrics"]
)
class PerformanceAnalysisNode(AnalysisNode):
    """Extended performance analysis node with advanced metrics."""
    
    _display_name = "Performance Analysis"
    _description = "Detailed performance analysis with advanced metrics"
    _icon = "📈"
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        super()._initialize_parameters()
        self.parameters.update({
            "calculate_var": True,
            "var_confidence": 0.95,
            "rolling_window": 30,
            "calculate_beta": True,
            "monte_carlo_simulations": 1000
        })
    
    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[Dict]) -> Dict[str, Any]:
        """Calculate advanced performance metrics."""
        # Get base metrics
        metrics = super()._calculate_metrics(trades, equity_curve)
        
        if not equity_curve:
            return metrics
        
        equity_values = [point.get("equity", 0) for point in equity_curve]
        returns = self._calculate_returns(equity_values)
        
        # Value at Risk (VaR)
        if self.get_parameter("calculate_var", True) and returns:
            var_confidence = self.get_parameter("var_confidence", 0.95)
            var = self._calculate_var(returns, var_confidence)
            metrics["var_95"] = var
            metrics["cvar_95"] = self._calculate_cvar(returns, var_confidence)
        
        # Rolling metrics
        rolling_window = self.get_parameter("rolling_window", 30)
        if len(returns) >= rolling_window:
            rolling_sharpe = self._calculate_rolling_sharpe(returns, rolling_window)
            metrics["rolling_sharpe_mean"] = statistics.mean(rolling_sharpe)
            metrics["rolling_sharpe_std"] = statistics.stdev(rolling_sharpe) if len(rolling_sharpe) > 1 else 0
        
        # Additional risk metrics
        metrics["skewness"] = self._calculate_skewness(returns) if returns else 0
        metrics["kurtosis"] = self._calculate_kurtosis(returns) if returns else 0
        
        return metrics
    
    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """Calculate Value at Risk."""
        if not returns:
            return 0
        
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return sorted_returns[index] if index < len(sorted_returns) else 0
    
    def _calculate_cvar(self, returns: List[float], confidence: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)."""
        if not returns:
            return 0
        
        var = self._calculate_var(returns, confidence)
        tail_returns = [r for r in returns if r <= var]
        return statistics.mean(tail_returns) if tail_returns else 0
    
    def _calculate_rolling_sharpe(self, returns: List[float], window: int) -> List[float]:
        """Calculate rolling Sharpe ratio."""
        rolling_sharpe = []
        risk_free_rate = self.get_parameter("risk_free_rate", 0.02) / 252  # Daily risk-free rate
        
        for i in range(window, len(returns) + 1):
            window_returns = returns[i-window:i]
            mean_return = statistics.mean(window_returns)
            std_return = statistics.stdev(window_returns) if len(window_returns) > 1 else 0
            
            if std_return != 0:
                sharpe = (mean_return - risk_free_rate) / std_return
                rolling_sharpe.append(sharpe)
        
        return rolling_sharpe
    
    def _calculate_skewness(self, returns: List[float]) -> float:
        """Calculate skewness of returns."""
        if len(returns) < 3:
            return 0
        
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0
        
        skewness = sum(((r - mean_return) / std_return) ** 3 for r in returns) / len(returns)
        return skewness
    
    def _calculate_kurtosis(self, returns: List[float]) -> float:
        """Calculate kurtosis of returns."""
        if len(returns) < 4:
            return 0
        
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        
        if std_return == 0:
            return 0
        
        kurtosis = sum(((r - mean_return) / std_return) ** 4 for r in returns) / len(returns) - 3
        return kurtosis


@register_node(
    category=NodeCategory.ANALYSIS,
    display_name="Risk Analysis",
    description="Comprehensive risk analysis and assessment",
    icon="⚠️",
    tags=["risk", "analysis", "assessment", "var"]
)
class RiskAnalysisNode(WorkflowNode):
    """Node for comprehensive risk analysis."""
    
    _category = NodeCategory.ANALYSIS
    _display_name = "Risk Analysis"
    _description = "Comprehensive risk analysis and assessment"
    _icon = "⚠️"
    _tags = ["risk", "analysis", "assessment", "var"]
    
    def _initialize_ports(self) -> None:
        """Initialize input and output ports."""
        # Input ports
        self.add_input_port("performance_data", DataType.PERFORMANCE_METRICS, True,
                           "Performance data to analyze")
        self.add_input_port("portfolio_data", DataType.DICT, False,
                           "Portfolio composition data")
        self.add_input_port("market_data", DataType.MARKET_DATA, False,
                           "Market data for correlation analysis")
        
        # Output ports
        self.add_output_port("risk_metrics", DataType.DICT,
                            "Calculated risk metrics")
        self.add_output_port("risk_assessment", DataType.DICT,
                            "Risk assessment and recommendations")
        self.add_output_port("risk_alerts", DataType.LIST,
                            "Risk-based alerts and warnings")
    
    def _initialize_parameters(self) -> None:
        """Initialize node parameters."""
        self.parameters = {
            "var_confidence_levels": [0.95, 0.99],
            "stress_test_scenarios": ["market_crash", "volatility_spike", "correlation_breakdown"],
            "risk_tolerance": "moderate",  # conservative, moderate, aggressive
            "alert_thresholds": {
                "max_drawdown": 0.15,
                "var_95": -0.05,
                "volatility": 0.25
            }
        }
    
    async def execute(self, context) -> Dict[str, Any]:
        """Execute risk analysis."""
        try:
            performance_data = self.get_input_value("performance_data", context)
            portfolio_data = self.get_input_value("portfolio_data", context)
            market_data = self.get_input_value("market_data", context)
            
            if not performance_data:
                raise ValueError("Performance data is required for risk analysis")
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(performance_data)
            
            # Perform risk assessment
            risk_assessment = self._assess_risk_level(risk_metrics)
            
            # Generate risk alerts
            risk_alerts = self._generate_risk_alerts(risk_metrics)
            
            # Portfolio risk analysis if data available
            if portfolio_data:
                portfolio_risk = self._analyze_portfolio_risk(portfolio_data, market_data)
                risk_metrics.update(portfolio_risk)
            
            return {
                "risk_metrics": risk_metrics,
                "risk_assessment": risk_assessment,
                "risk_alerts": risk_alerts
            }
            
        except Exception as e:
            return {
                "risk_metrics": {},
                "risk_assessment": {"error": str(e)},
                "risk_alerts": [{"type": "error", "message": str(e)}]
            }
    
    def _calculate_risk_metrics(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics."""
        risk_metrics = {}
        
        # Extract basic risk metrics
        risk_metrics["max_drawdown"] = performance_data.get("max_drawdown", 0)
        risk_metrics["volatility"] = performance_data.get("volatility", 0)
        risk_metrics["var_95"] = performance_data.get("var_95", 0)
        risk_metrics["cvar_95"] = performance_data.get("cvar_95", 0)
        
        # Risk-adjusted return metrics
        risk_metrics["sharpe_ratio"] = performance_data.get("sharpe_ratio", 0)
        risk_metrics["sortino_ratio"] = performance_data.get("sortino_ratio", 0)
        risk_metrics["calmar_ratio"] = performance_data.get("calmar_ratio", 0)
        
        # Additional risk calculations
        total_return = performance_data.get("total_return", 0)
        volatility = performance_data.get("volatility", 0)
        
        # Risk-return ratio
        if volatility != 0:
            risk_metrics["return_volatility_ratio"] = total_return / volatility
        
        # Downside risk metrics
        risk_metrics["downside_deviation"] = self._calculate_downside_deviation(performance_data)
        
        return risk_metrics
    
    def _assess_risk_level(self, risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk level and provide recommendations."""
        risk_tolerance = self.get_parameter("risk_tolerance", "moderate")
        
        # Define risk thresholds based on tolerance
        thresholds = {
            "conservative": {
                "max_drawdown": 0.10,
                "volatility": 0.15,
                "var_95": -0.03
            },
            "moderate": {
                "max_drawdown": 0.20,
                "volatility": 0.25,
                "var_95": -0.05
            },
            "aggressive": {
                "max_drawdown": 0.35,
                "volatility": 0.40,
                "var_95": -0.08
            }
        }
        
        current_thresholds = thresholds.get(risk_tolerance, thresholds["moderate"])
        
        # Assess each risk metric
        assessments = {}
        overall_risk_score = 0
        
        for metric, threshold in current_thresholds.items():
            current_value = abs(risk_metrics.get(metric, 0))
            threshold_value = abs(threshold)
            
            if current_value <= threshold_value * 0.5:
                level = "low"
                score = 1
            elif current_value <= threshold_value:
                level = "moderate"
                score = 2
            elif current_value <= threshold_value * 1.5:
                level = "high"
                score = 3
            else:
                level = "very_high"
                score = 4
            
            assessments[metric] = {
                "level": level,
                "score": score,
                "current_value": current_value,
                "threshold": threshold_value
            }
            overall_risk_score += score
        
        # Overall risk assessment
        avg_score = overall_risk_score / len(current_thresholds)
        if avg_score <= 1.5:
            overall_level = "low"
        elif avg_score <= 2.5:
            overall_level = "moderate"
        elif avg_score <= 3.5:
            overall_level = "high"
        else:
            overall_level = "very_high"
        
        return {
            "overall_risk_level": overall_level,
            "overall_risk_score": avg_score,
            "risk_tolerance": risk_tolerance,
            "metric_assessments": assessments,
            "recommendations": self._generate_risk_recommendations(overall_level, assessments)
        }
    
    def _generate_risk_alerts(self, risk_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate risk-based alerts."""
        alerts = []
        alert_thresholds = self.get_parameter("alert_thresholds", {})
        
        for metric, threshold in alert_thresholds.items():
            current_value = abs(risk_metrics.get(metric, 0))
            threshold_value = abs(threshold)
            
            if current_value > threshold_value:
                severity = "high" if current_value > threshold_value * 1.5 else "medium"
                alerts.append({
                    "type": "risk_threshold_exceeded",
                    "severity": severity,
                    "metric": metric,
                    "current_value": current_value,
                    "threshold": threshold_value,
                    "message": f"{metric.replace('_', ' ').title()} ({current_value:.2%}) exceeds threshold ({threshold_value:.2%})",
                    "timestamp": datetime.now().isoformat()
                })
        
        return alerts
    
    def _generate_risk_recommendations(self, overall_level: str, assessments: Dict) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        if overall_level in ["high", "very_high"]:
            recommendations.append("Consider reducing position sizes to lower overall risk exposure")
            recommendations.append("Implement stricter stop-loss levels")
            recommendations.append("Review and tighten risk management rules")
        
        # Specific recommendations based on individual metrics
        for metric, assessment in assessments.items():
            if assessment["level"] in ["high", "very_high"]:
                if metric == "max_drawdown":
                    recommendations.append("High drawdown detected - consider implementing dynamic position sizing")
                elif metric == "volatility":
                    recommendations.append("High volatility - consider reducing leverage or trading frequency")
                elif metric == "var_95":
                    recommendations.append("High VaR - review portfolio diversification and correlation")
        
        return recommendations
    
    def _calculate_downside_deviation(self, performance_data: Dict[str, Any]) -> float:
        """Calculate downside deviation from performance data."""
        # This would typically require the full return series
        # For now, we'll estimate based on available metrics
        volatility = performance_data.get("volatility", 0)
        skewness = performance_data.get("skewness", 0)
        
        # Rough approximation - in practice, you'd calculate from actual returns
        if skewness < 0:  # Negative skew means more downside risk
            return volatility * (1 + abs(skewness) * 0.5)
        else:
            return volatility * 0.7  # Assume 70% of volatility is downside
    
    def _analyze_portfolio_risk(self, portfolio_data: Dict[str, Any], 
                               market_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze portfolio-level risk metrics."""
        portfolio_risk = {}
        
        # Portfolio concentration risk
        positions = portfolio_data.get("positions", [])
        if positions:
            position_weights = [pos.get("weight", 0) for pos in positions]
            portfolio_risk["concentration_risk"] = max(position_weights) if position_weights else 0
            portfolio_risk["diversification_ratio"] = len([w for w in position_weights if w > 0.01])  # Positions > 1%
        
        # Correlation risk (if market data available)
        if market_data:
            correlations = market_data.get("correlations", {})
            if correlations:
                avg_correlation = statistics.mean(correlations.values()) if correlations else 0
                portfolio_risk["average_correlation"] = avg_correlation
                portfolio_risk["correlation_risk"] = "high" if avg_correlation > 0.7 else "moderate" if avg_correlation > 0.4 else "low"
        
        return portfolio_risk