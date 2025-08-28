"""
Portfolio Visualization Components

UI components for portfolio performance tracking, P&L visualization,
risk metrics display, and correlation analysis.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from decimal import Decimal

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Label, DataTable, ProgressBar, TabbedContent, TabPane
from textual.reactive import reactive
from textual.timer import Timer

from ..components.panels import BasePanel
from ..components.charts import PerformanceChart, LineChart, AreaChart, BarChart
from ..components.tables import EnhancedDataTable
from ...services.portfolio_service import (
    PortfolioPerformanceService, Position, Trade, PortfolioSnapshot,
    PerformanceMetrics, RiskMetrics, PositionType
)
from ...services.chart_renderer import ChartConfig, ChartType, DataSeries
from ...utils.logging import get_logger


class PortfolioPnLTracker(BasePanel):
    """Real-time P&L tracking panel"""
    
    DEFAULT_CSS = """
    PortfolioPnLTracker {
        height: auto;
        min-height: 12;
    }
    
    .pnl-summary {
        height: 6;
        border: solid $accent;
        padding: 1;
    }
    
    .pnl-metric {
        height: 2;
        margin: 0 1;
    }
    
    .pnl-label {
        dock: left;
        width: 20;
        color: $text;
    }
    
    .pnl-value {
        dock: right;
        width: 15;
        text-align: right;
    }
    
    .pnl-positive {
        color: $success;
    }
    
    .pnl-negative {
        color: $error;
    }
    
    .pnl-neutral {
        color: $accent;
    }
    
    .pnl-chart {
        height: 1fr;
        margin: 1;
    }
    """
    
    def __init__(
        self, 
        portfolio_service: PortfolioPerformanceService,
        **kwargs
    ):
        super().__init__(title="Portfolio P&L Tracker", **kwargs)
        self.logger = get_logger(__name__)
        self.portfolio_service = portfolio_service
        self.update_timer: Optional[Timer] = None
        
        # Performance data
        self.pnl_history: List[float] = []
        self.value_history: List[float] = []
        self.timestamps: List[datetime] = []
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize P&L tracker when mounted"""
        self._setup_pnl_tracker()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_pnl_tracker(self) -> None:
        """Set up P&L tracker interface"""
        container = Vertical()
        
        # P&L Summary
        summary_container = Vertical(classes="pnl-summary")
        
        # Portfolio Value
        self.portfolio_value_metric = self._create_pnl_metric("Portfolio Value", "$0.00", "neutral")
        summary_container.mount(self.portfolio_value_metric)
        
        # Total P&L
        self.total_pnl_metric = self._create_pnl_metric("Total P&L", "$0.00", "neutral")
        summary_container.mount(self.total_pnl_metric)
        
        # Daily P&L
        self.daily_pnl_metric = self._create_pnl_metric("Daily P&L", "$0.00", "neutral")
        summary_container.mount(self.daily_pnl_metric)
        
        container.mount(summary_container)
        
        # P&L Chart
        chart_config = ChartConfig(
            width=70,
            height=15,
            title="Portfolio Performance",
            show_legend=True
        )
        
        self.pnl_chart = PerformanceChart(
            title="P&L Chart",
            config=chart_config
        )
        
        container.mount(self.pnl_chart)
        self.update_content(container)
    
    def _create_pnl_metric(self, label: str, value: str, value_type: str) -> Container:
        """Create P&L metric widget"""
        metric = Horizontal(classes="pnl-metric")
        
        label_widget = Label(label, classes="pnl-label")
        metric.mount(label_widget)
        
        value_class = f"pnl-value pnl-{value_type}"
        value_widget = Label(value, classes=value_class, id=f"pnl-{label.lower().replace(' ', '-')}")
        metric.mount(value_widget)
        
        return metric
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        # Add performance callback
        self.portfolio_service.add_performance_callback(self._on_performance_update)
        
        # Start update timer
        self.update_timer = self.set_interval(5.0, self._update_display)
    
    def _on_performance_update(self, portfolio_value: float, total_pnl: float) -> None:
        """Handle performance updates"""
        self.value_history.append(portfolio_value)
        self.pnl_history.append(total_pnl)
        self.timestamps.append(datetime.now())
        
        # Keep only recent data
        max_points = 100
        if len(self.value_history) > max_points:
            self.value_history = self.value_history[-max_points:]
            self.pnl_history = self.pnl_history[-max_points:]
            self.timestamps = self.timestamps[-max_points:]
    
    def _update_display(self) -> None:
        """Update P&L display"""
        try:
            # Get current values
            portfolio_value = self.portfolio_service.get_portfolio_value()
            total_pnl = self.portfolio_service.get_total_pnl()
            
            # Calculate daily P&L
            daily_pnl = 0.0
            if len(self.pnl_history) > 1:
                daily_pnl = self.pnl_history[-1] - self.pnl_history[-2]
            
            # Update metrics
            self._update_metric("portfolio-value", f"${portfolio_value:,.2f}", "neutral")
            self._update_metric("total-p&l", f"${total_pnl:+,.2f}", 
                              "positive" if total_pnl >= 0 else "negative")
            self._update_metric("daily-p&l", f"${daily_pnl:+,.2f}", 
                              "positive" if daily_pnl >= 0 else "negative")
            
            # Update chart
            if len(self.pnl_history) > 1:
                # Convert P&L to returns
                initial_value = self.portfolio_service.initial_capital
                returns = [(pnl / initial_value) for pnl in self.pnl_history]
                
                self.pnl_chart.set_performance_data(returns)
                
                # Calculate and display metrics
                metrics = self.pnl_chart.calculate_metrics()
                self.pnl_chart.metrics = metrics
                self.pnl_chart._update_legend()
                
        except Exception as e:
            self.logger.error(f"Error updating P&L display: {e}")
    
    def _update_metric(self, metric_id: str, value: str, value_type: str) -> None:
        """Update metric display"""
        try:
            metric_widget = self.query_one(f"#pnl-{metric_id}", Label)
            metric_widget.update(value)
            
            # Update CSS class for color
            metric_widget.remove_class("pnl-positive", "pnl-negative", "pnl-neutral")
            metric_widget.add_class(f"pnl-{value_type}")
            
        except Exception as e:
            self.logger.error(f"Error updating metric {metric_id}: {e}")


class PositionsPanel(BasePanel):
    """Current positions display panel"""
    
    DEFAULT_CSS = """
    PositionsPanel {
        height: auto;
        min-height: 15;
    }
    
    .positions-table {
        height: 1fr;
        border: solid $accent;
    }
    """
    
    def __init__(
        self, 
        portfolio_service: PortfolioPerformanceService,
        **kwargs
    ):
        super().__init__(title="Current Positions", **kwargs)
        self.logger = get_logger(__name__)
        self.portfolio_service = portfolio_service
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize positions panel when mounted"""
        self._setup_positions_table()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_positions_table(self) -> None:
        """Set up positions table"""
        self.positions_table = EnhancedDataTable(
            title="Positions",
            show_header=True,
            show_row_labels=False,
            classes="positions-table"
        )
        
        # Add columns
        self.positions_table.add_column("Symbol", width=12)
        self.positions_table.add_column("Type", width=8)
        self.positions_table.add_column("Quantity", width=12)
        self.positions_table.add_column("Entry Price", width=12)
        self.positions_table.add_column("Current Price", width=12)
        self.positions_table.add_column("Market Value", width=15)
        self.positions_table.add_column("Unrealized P&L", width=15)
        self.positions_table.add_column("Return %", width=10)
        
        self.update_content(self.positions_table)
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        # Add position callback
        self.portfolio_service.add_position_callback(self._on_position_update)
        
        # Start update timer
        self.update_timer = self.set_interval(2.0, self._update_display)
    
    def _on_position_update(self, data: Any, action: str) -> None:
        """Handle position updates"""
        # Trigger display update
        self._update_display()
    
    def _update_display(self) -> None:
        """Update positions display"""
        try:
            # Clear existing rows
            self.positions_table.clear()
            
            # Get current positions
            positions = self.portfolio_service.get_positions()
            
            for position in positions:
                # Format values
                position_type = position.position_type.value.upper()
                quantity_str = f"{position.quantity:+.4f}"
                entry_price_str = f"${position.entry_price:.4f}"
                current_price_str = f"${position.current_price:.4f}"
                market_value_str = f"${position.market_value:,.2f}"
                
                # Color code P&L
                pnl_str = f"${position.unrealized_pnl:+,.2f}"
                return_str = f"{position.return_percent:+.2f}%"
                
                self.positions_table.add_row(
                    position.symbol,
                    position_type,
                    quantity_str,
                    entry_price_str,
                    current_price_str,
                    market_value_str,
                    pnl_str,
                    return_str
                )
                
        except Exception as e:
            self.logger.error(f"Error updating positions display: {e}")


class PerformanceMetricsPanel(BasePanel):
    """Performance metrics dashboard"""
    
    DEFAULT_CSS = """
    PerformanceMetricsPanel {
        height: auto;
        min-height: 20;
    }
    
    .metrics-grid {
        height: 1fr;
    }
    
    .metrics-section {
        height: 1fr;
        border: solid $accent;
        margin: 1;
        padding: 1;
    }
    
    .metric-item {
        height: 1;
        margin: 0;
    }
    
    .metric-label {
        dock: left;
        width: 20;
        color: $text;
    }
    
    .metric-value {
        dock: right;
        width: 12;
        text-align: right;
        color: $accent;
    }
    """
    
    def __init__(
        self, 
        portfolio_service: PortfolioPerformanceService,
        **kwargs
    ):
        super().__init__(title="Performance Metrics", **kwargs)
        self.logger = get_logger(__name__)
        self.portfolio_service = portfolio_service
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize metrics panel when mounted"""
        self._setup_metrics_display()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_metrics_display(self) -> None:
        """Set up metrics display"""
        container = Horizontal(classes="metrics-grid")
        
        # Return Metrics
        returns_section = Vertical(classes="metrics-section")
        returns_title = Label("Return Metrics", classes="section-title")
        returns_section.mount(returns_title)
        
        self.total_return_metric = self._create_metric("Total Return", "0.00%")
        self.annual_return_metric = self._create_metric("Annualized Return", "0.00%")
        returns_section.mount(self.total_return_metric)
        returns_section.mount(self.annual_return_metric)
        
        container.mount(returns_section)
        
        # Risk Metrics
        risk_section = Vertical(classes="metrics-section")
        risk_title = Label("Risk Metrics", classes="section-title")
        risk_section.mount(risk_title)
        
        self.volatility_metric = self._create_metric("Volatility", "0.00%")
        self.max_drawdown_metric = self._create_metric("Max Drawdown", "0.00%")
        self.sharpe_ratio_metric = self._create_metric("Sharpe Ratio", "0.00")
        risk_section.mount(self.volatility_metric)
        risk_section.mount(self.max_drawdown_metric)
        risk_section.mount(self.sharpe_ratio_metric)
        
        container.mount(risk_section)
        
        # Trade Metrics
        trade_section = Vertical(classes="metrics-section")
        trade_title = Label("Trade Metrics", classes="section-title")
        trade_section.mount(trade_title)
        
        self.win_rate_metric = self._create_metric("Win Rate", "0.00%")
        self.profit_factor_metric = self._create_metric("Profit Factor", "0.00")
        self.total_trades_metric = self._create_metric("Total Trades", "0")
        trade_section.mount(self.win_rate_metric)
        trade_section.mount(self.profit_factor_metric)
        trade_section.mount(self.total_trades_metric)
        
        container.mount(trade_section)
        
        self.update_content(container)
    
    def _create_metric(self, label: str, value: str) -> Container:
        """Create metric widget"""
        metric = Horizontal(classes="metric-item")
        
        label_widget = Label(label, classes="metric-label")
        metric.mount(label_widget)
        
        value_widget = Label(value, classes="metric-value", 
                           id=f"metric-{label.lower().replace(' ', '-')}")
        metric.mount(value_widget)
        
        return metric
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        self.update_timer = self.set_interval(10.0, self._update_metrics)
    
    def _update_metrics(self) -> None:
        """Update performance metrics"""
        try:
            # Calculate metrics
            metrics = self.portfolio_service.calculate_performance_metrics()
            
            # Update display
            self._update_metric_value("total-return", f"{metrics.total_return:.2%}")
            self._update_metric_value("annualized-return", f"{metrics.annualized_return:.2%}")
            self._update_metric_value("volatility", f"{metrics.volatility:.2%}")
            self._update_metric_value("max-drawdown", f"{metrics.max_drawdown:.2%}")
            self._update_metric_value("sharpe-ratio", f"{metrics.sharpe_ratio:.2f}")
            self._update_metric_value("win-rate", f"{metrics.win_rate:.2%}")
            self._update_metric_value("profit-factor", f"{metrics.profit_factor:.2f}")
            self._update_metric_value("total-trades", f"{metrics.total_trades}")
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    def _update_metric_value(self, metric_id: str, value: str) -> None:
        """Update metric value"""
        try:
            metric_widget = self.query_one(f"#metric-{metric_id}", Label)
            metric_widget.update(value)
        except Exception as e:
            self.logger.error(f"Error updating metric {metric_id}: {e}")


class DrawdownAnalysisPanel(BasePanel):
    """Drawdown analysis panel"""
    
    def __init__(
        self, 
        portfolio_service: PortfolioPerformanceService,
        **kwargs
    ):
        super().__init__(title="Drawdown Analysis", **kwargs)
        self.logger = get_logger(__name__)
        self.portfolio_service = portfolio_service
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize drawdown analysis when mounted"""
        self._setup_drawdown_analysis()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_drawdown_analysis(self) -> None:
        """Set up drawdown analysis interface"""
        container = Vertical()
        
        # Drawdown chart
        chart_config = ChartConfig(
            width=70,
            height=15,
            title="Drawdown Chart",
            show_legend=False
        )
        
        self.drawdown_chart = AreaChart(
            title="Portfolio Drawdown",
            config=chart_config,
            fill_char="▓"
        )
        
        container.mount(self.drawdown_chart)
        
        # Drawdown periods table
        self.drawdown_table = EnhancedDataTable(
            title="Drawdown Periods",
            show_header=True,
            show_row_labels=False
        )
        
        self.drawdown_table.add_column("Start Date", width=12)
        self.drawdown_table.add_column("End Date", width=12)
        self.drawdown_table.add_column("Duration (Days)", width=15)
        self.drawdown_table.add_column("Depth %", width=10)
        self.drawdown_table.add_column("Peak Value", width=15)
        self.drawdown_table.add_column("Trough Value", width=15)
        
        container.mount(self.drawdown_table)
        self.update_content(container)
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        self.update_timer = self.set_interval(30.0, self._update_drawdown_analysis)
    
    def _update_drawdown_analysis(self) -> None:
        """Update drawdown analysis"""
        try:
            # Get portfolio history
            history = self.portfolio_service.get_portfolio_history(90)  # Last 90 days
            
            if len(history) > 1:
                # Calculate drawdown series
                drawdown_data = []
                peak_value = history[0].total_value
                
                for snapshot in history:
                    if snapshot.total_value > peak_value:
                        peak_value = snapshot.total_value
                    
                    drawdown = (peak_value - snapshot.total_value) / peak_value
                    drawdown_data.append(-drawdown * 100)  # Negative for visualization
                
                # Update chart
                self.drawdown_chart.set_area_data(drawdown_data, "Drawdown %")
            
            # Update drawdown periods table
            drawdown_periods = self.portfolio_service.get_drawdown_periods()
            
            self.drawdown_table.clear()
            for period in drawdown_periods[-10:]:  # Show last 10 periods
                self.drawdown_table.add_row(
                    period['start_date'].strftime("%Y-%m-%d"),
                    period['end_date'].strftime("%Y-%m-%d"),
                    str(period['duration_days']),
                    f"{period['depth_percent']:.2f}%",
                    f"${period['peak_value']:,.2f}",
                    f"${period['trough_value']:,.2f}"
                )
                
        except Exception as e:
            self.logger.error(f"Error updating drawdown analysis: {e}")


class CorrelationAnalysisPanel(BasePanel):
    """Strategy correlation analysis panel"""
    
    def __init__(
        self, 
        portfolio_service: PortfolioPerformanceService,
        **kwargs
    ):
        super().__init__(title="Strategy Correlation", **kwargs)
        self.logger = get_logger(__name__)
        self.portfolio_service = portfolio_service
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize correlation analysis when mounted"""
        self._setup_correlation_analysis()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_correlation_analysis(self) -> None:
        """Set up correlation analysis interface"""
        container = Vertical()
        
        # Correlation matrix table
        self.correlation_table = EnhancedDataTable(
            title="Strategy Correlation Matrix",
            show_header=True,
            show_row_labels=True
        )
        
        container.mount(self.correlation_table)
        
        # Risk metrics
        self.risk_table = EnhancedDataTable(
            title="Risk Metrics",
            show_header=True,
            show_row_labels=False
        )
        
        self.risk_table.add_column("Metric", width=20)
        self.risk_table.add_column("Value", width=15)
        self.risk_table.add_column("Description", width=40)
        
        container.mount(self.risk_table)
        self.update_content(container)
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        self.update_timer = self.set_interval(60.0, self._update_correlation_analysis)
    
    def _update_correlation_analysis(self) -> None:
        """Update correlation analysis"""
        try:
            # Calculate strategy correlation
            correlation_matrix = self.portfolio_service.calculate_strategy_correlation()
            
            if correlation_matrix:
                # Update correlation table
                strategies = list(correlation_matrix.keys())
                
                # Clear and rebuild table
                self.correlation_table.clear()
                
                # Add columns for each strategy
                for strategy in strategies:
                    self.correlation_table.add_column(strategy, width=12)
                
                # Add rows
                for strategy1 in strategies:
                    row_data = []
                    for strategy2 in strategies:
                        correlation = correlation_matrix[strategy1][strategy2]
                        row_data.append(f"{correlation:.3f}")
                    
                    self.correlation_table.add_row(*row_data, label=strategy1)
            
            # Calculate and display risk metrics
            risk_metrics = self.portfolio_service.calculate_risk_metrics()
            
            self.risk_table.clear()
            
            risk_descriptions = {
                'value_at_risk_95': '95% Value at Risk - potential loss in worst 5% of cases',
                'value_at_risk_99': '99% Value at Risk - potential loss in worst 1% of cases',
                'expected_shortfall_95': 'Expected Shortfall - average loss beyond VaR',
                'beta': 'Beta vs benchmark - sensitivity to market movements',
                'correlation_to_benchmark': 'Correlation to benchmark',
                'tracking_error': 'Tracking error vs benchmark',
                'downside_deviation': 'Downside deviation - volatility of negative returns'
            }
            
            for metric, value in risk_metrics.to_dict().items():
                if metric in risk_descriptions:
                    if 'ratio' in metric or 'correlation' in metric or 'beta' in metric:
                        value_str = f"{value:.3f}"
                    elif 'var' in metric or 'shortfall' in metric or 'deviation' in metric:
                        value_str = f"{value:.2%}"
                    else:
                        value_str = f"{value:.4f}"
                    
                    self.risk_table.add_row(
                        metric.replace('_', ' ').title(),
                        value_str,
                        risk_descriptions[metric]
                    )
                    
        except Exception as e:
            self.logger.error(f"Error updating correlation analysis: {e}")


class PortfolioDashboard(BasePanel):
    """Comprehensive portfolio dashboard"""
    
    def __init__(
        self, 
        portfolio_service: PortfolioPerformanceService,
        **kwargs
    ):
        super().__init__(title="Portfolio Dashboard", **kwargs)
        self.logger = get_logger(__name__)
        self.portfolio_service = portfolio_service
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize portfolio dashboard when mounted"""
        self._setup_dashboard()
    
    def _setup_dashboard(self) -> None:
        """Set up portfolio dashboard with tabs"""
        dashboard = TabbedContent()
        
        # P&L Tracking Tab
        with dashboard.add_pane("pnl", "P&L Tracking"):
            pnl_tracker = PortfolioPnLTracker(self.portfolio_service)
            yield pnl_tracker
        
        # Positions Tab
        with dashboard.add_pane("positions", "Positions"):
            positions_panel = PositionsPanel(self.portfolio_service)
            yield positions_panel
        
        # Performance Tab
        with dashboard.add_pane("performance", "Performance"):
            performance_panel = PerformanceMetricsPanel(self.portfolio_service)
            yield performance_panel
        
        # Risk Analysis Tab
        with dashboard.add_pane("risk", "Risk Analysis"):
            container = Vertical()
            
            drawdown_panel = DrawdownAnalysisPanel(self.portfolio_service)
            container.mount(drawdown_panel)
            
            correlation_panel = CorrelationAnalysisPanel(self.portfolio_service)
            container.mount(correlation_panel)
            
            yield container
        
        self.update_content(dashboard)