#!/usr/bin/env python3
"""
Real-Time Data Visualization Demo

Comprehensive demonstration of the real-time data visualization and charts system
including market data, portfolio performance, and alert management.
"""

import asyncio
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, TabbedContent, TabPane
from textual.timer import Timer

# Import services
from ..services.market_data_service import RealTimeMarketDataService, MarketTicker, OrderBook, Trade
from ..services.portfolio_service import PortfolioPerformanceService, Position, PositionType
from ..services.alert_service import AlertService, AlertType, AlertPriority, AlertCondition, NotificationMethod

# Import UI components
from ..ui.components.market_data import (
    PriceFeedPanel, OrderBookPanel, TradeHistoryPanel, 
    MarketOverviewPanel, RealTimeChartPanel
)
from ..ui.components.portfolio import (
    PortfolioPnLTracker, PositionsPanel, PerformanceMetricsPanel,
    DrawdownAnalysisPanel, CorrelationAnalysisPanel, PortfolioDashboard
)
from ..ui.components.alerts import AlertDashboard
from ..ui.components.charts import (
    EnhancedASCIIChart, LineChart, CandlestickChart, PerformanceChart, RealTimeChart
)
from ..services.chart_renderer import ChartConfig, ChartType, DataSeries


class VisualizationDemo(App):
    """Comprehensive visualization demo application"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .demo-container {
        height: 1fr;
        padding: 1;
    }
    
    .demo-panel {
        height: 1fr;
        margin: 1;
        border: solid $primary;
    }
    
    .controls {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    .status-bar {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """
    
    TITLE = "Real-Time Data Visualization Demo"
    
    def __init__(self):
        super().__init__()
        
        # Services
        self.market_data_service = RealTimeMarketDataService()
        self.portfolio_service = PortfolioPerformanceService(initial_capital=100000.0)
        self.alert_service = AlertService()
        
        # Demo data
        self.demo_symbols = ["BTCUSD", "ETHUSD", "ADAUSD", "SOLUSD", "DOTUSD"]
        self.demo_running = False
        self.demo_timer: Timer = None
        
        # Mock data generators
        self.price_data = {symbol: 100.0 + random.uniform(-20, 20) for symbol in self.demo_symbols}
        self.volume_data = {symbol: random.uniform(10000, 100000) for symbol in self.demo_symbols}
    
    def compose(self) -> ComposeResult:
        """Compose the demo application"""
        yield Header()
        
        with TabbedContent():
            # Market Data Tab
            with TabPane("Market Data", id="market-tab"):
                yield self._create_market_data_demo()
            
            # Portfolio Tab
            with TabPane("Portfolio", id="portfolio-tab"):
                yield self._create_portfolio_demo()
            
            # Charts Tab
            with TabPane("Charts", id="charts-tab"):
                yield self._create_charts_demo()
            
            # Alerts Tab
            with TabPane("Alerts", id="alerts-tab"):
                yield self._create_alerts_demo()
            
            # Performance Tab
            with TabPane("Performance", id="performance-tab"):
                yield self._create_performance_demo()
        
        # Controls
        with Container(classes="controls"):
            yield Button("Start Demo", id="start-demo", variant="success")
            yield Button("Stop Demo", id="stop-demo", variant="error")
            yield Button("Add Position", id="add-position", variant="primary")
            yield Button("Create Alert", id="create-alert", variant="warning")
            yield Button("Generate Data", id="generate-data", variant="default")
        
        # Status bar
        yield Static("Demo ready - Click 'Start Demo' to begin", classes="status-bar", id="status")
        
        yield Footer()
    
    def _create_market_data_demo(self) -> Container:
        """Create market data demonstration"""
        container = Vertical(classes="demo-container")
        
        # Price feed
        price_feed = PriceFeedPanel(
            self.market_data_service,
            symbols=self.demo_symbols[:3]  # Show first 3 symbols
        )
        container.mount(price_feed)
        
        # Market overview and order book side by side
        market_row = Horizontal()
        
        market_overview = MarketOverviewPanel(
            self.market_data_service,
            symbols=self.demo_symbols
        )
        market_row.mount(market_overview)
        
        order_book = OrderBookPanel(
            self.market_data_service,
            symbol=self.demo_symbols[0]  # BTCUSD
        )
        market_row.mount(order_book)
        
        container.mount(market_row)
        
        # Trade history
        trade_history = TradeHistoryPanel(
            self.market_data_service,
            symbol=self.demo_symbols[0]
        )
        container.mount(trade_history)
        
        return container
    
    def _create_portfolio_demo(self) -> Container:
        """Create portfolio demonstration"""
        return PortfolioDashboard(self.portfolio_service)
    
    def _create_charts_demo(self) -> Container:
        """Create charts demonstration"""
        container = Vertical(classes="demo-container")
        
        # Real-time charts row
        charts_row = Horizontal()
        
        # Real-time line chart
        line_chart = RealTimeChart(
            title="BTC Price",
            chart_type=ChartType.LINE,
            config=ChartConfig(width=40, height=15, title="BTC/USD Live"),
            update_interval=1.0,
            max_points=50
        )
        charts_row.mount(line_chart)
        
        # Real-time candlestick chart
        candle_chart = RealTimeChart(
            title="ETH Candles",
            chart_type=ChartType.CANDLESTICK,
            config=ChartConfig(width=40, height=15, title="ETH/USD Candles"),
            update_interval=2.0,
            max_points=30
        )
        charts_row.mount(candle_chart)
        
        container.mount(charts_row)
        
        # Performance chart
        performance_chart = PerformanceChart(
            title="Portfolio Performance",
            config=ChartConfig(width=80, height=18, title="Strategy Performance")
        )
        container.mount(performance_chart)
        
        # Store references for updates
        self.demo_line_chart = line_chart
        self.demo_candle_chart = candle_chart
        self.demo_performance_chart = performance_chart
        
        return container
    
    def _create_alerts_demo(self) -> Container:
        """Create alerts demonstration"""
        return AlertDashboard(self.alert_service)
    
    def _create_performance_demo(self) -> Container:
        """Create performance analysis demonstration"""
        container = Vertical(classes="demo-container")
        
        # Performance metrics and drawdown analysis
        metrics_row = Horizontal()
        
        performance_metrics = PerformanceMetricsPanel(self.portfolio_service)
        metrics_row.mount(performance_metrics)
        
        drawdown_analysis = DrawdownAnalysisPanel(self.portfolio_service)
        metrics_row.mount(drawdown_analysis)
        
        container.mount(metrics_row)
        
        # Correlation analysis
        correlation_analysis = CorrelationAnalysisPanel(self.portfolio_service)
        container.mount(correlation_analysis)
        
        return container
    
    async def on_mount(self) -> None:
        """Initialize demo when mounted"""
        await self._initialize_services()
        await self._setup_demo_data()
    
    async def _initialize_services(self) -> None:
        """Initialize all services"""
        try:
            await self.market_data_service.start()
            await self.portfolio_service.start()
            await self.alert_service.start()
            
            self._update_status("Services initialized successfully")
            
        except Exception as e:
            self._update_status(f"Error initializing services: {e}")
    
    async def _setup_demo_data(self) -> None:
        """Set up initial demo data"""
        try:
            # Create some demo positions
            await self._create_demo_positions()
            
            # Create demo alerts
            await self._create_demo_alerts()
            
            self._update_status("Demo data setup complete")
            
        except Exception as e:
            self._update_status(f"Error setting up demo data: {e}")
    
    async def _create_demo_positions(self) -> None:
        """Create demo portfolio positions"""
        try:
            # Add some positions
            self.portfolio_service.add_position(
                symbol="BTCUSD",
                quantity=0.5,
                entry_price=45000.0,
                position_type=PositionType.LONG,
                strategy_id="trend_following"
            )
            
            self.portfolio_service.add_position(
                symbol="ETHUSD",
                quantity=2.0,
                entry_price=3000.0,
                position_type=PositionType.LONG,
                strategy_id="mean_reversion"
            )
            
            self.portfolio_service.add_position(
                symbol="ADAUSD",
                quantity=1000.0,
                entry_price=0.5,
                position_type=PositionType.SHORT,
                strategy_id="momentum"
            )
            
        except Exception as e:
            self._update_status(f"Error creating demo positions: {e}")
    
    async def _create_demo_alerts(self) -> None:
        """Create demo alerts"""
        try:
            # Price alert for BTC
            self.alert_service.create_alert(
                name="BTC High Price Alert",
                alert_type=AlertType.PRICE_ABOVE,
                condition=AlertCondition(field="price", operator="gt", value=50000.0),
                symbol="BTCUSD",
                priority=AlertPriority.HIGH,
                notification_methods=[NotificationMethod.VISUAL, NotificationMethod.AUDIO]
            )
            
            # Drawdown alert
            self.alert_service.create_alert(
                name="Portfolio Drawdown Alert",
                alert_type=AlertType.DRAWDOWN_LIMIT,
                condition=AlertCondition(field="drawdown", operator="gt", value=0.05),  # 5% drawdown
                priority=AlertPriority.CRITICAL,
                notification_methods=[NotificationMethod.VISUAL, NotificationMethod.LOG]
            )
            
            # Volume spike alert
            self.alert_service.create_alert(
                name="ETH Volume Spike",
                alert_type=AlertType.VOLUME_SPIKE,
                condition=AlertCondition(field="volume", operator="gt", value=50000.0),
                symbol="ETHUSD",
                priority=AlertPriority.MEDIUM,
                notification_methods=[NotificationMethod.VISUAL]
            )
            
        except Exception as e:
            self._update_status(f"Error creating demo alerts: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "start-demo":
            await self._start_demo()
        elif event.button.id == "stop-demo":
            await self._stop_demo()
        elif event.button.id == "add-position":
            await self._add_random_position()
        elif event.button.id == "create-alert":
            await self._create_random_alert()
        elif event.button.id == "generate-data":
            await self._generate_market_data()
    
    async def _start_demo(self) -> None:
        """Start the demo"""
        try:
            if self.demo_running:
                return
            
            self.demo_running = True
            self.demo_timer = self.set_interval(1.0, self._update_demo_data)
            
            self._update_status("Demo started - Real-time data simulation active")
            
        except Exception as e:
            self._update_status(f"Error starting demo: {e}")
    
    async def _stop_demo(self) -> None:
        """Stop the demo"""
        try:
            self.demo_running = False
            
            if self.demo_timer:
                self.demo_timer.stop()
                self.demo_timer = None
            
            self._update_status("Demo stopped")
            
        except Exception as e:
            self._update_status(f"Error stopping demo: {e}")
    
    def _update_demo_data(self) -> None:
        """Update demo data (called by timer)"""
        try:
            # Update market data
            self._update_market_prices()
            
            # Update portfolio positions
            self._update_position_prices()
            
            # Update charts
            self._update_demo_charts()
            
            # Check alerts
            self._update_alert_data()
            
        except Exception as e:
            self._update_status(f"Error updating demo data: {e}")
    
    def _update_market_prices(self) -> None:
        """Update market prices with random walk"""
        for symbol in self.demo_symbols:
            # Random walk price movement
            change_pct = random.uniform(-0.02, 0.02)  # ±2% change
            self.price_data[symbol] *= (1 + change_pct)
            
            # Volume variation
            volume_change = random.uniform(-0.1, 0.1)  # ±10% volume change
            self.volume_data[symbol] *= (1 + volume_change)
            
            # Update market data service
            market_data = {
                'price': self.price_data[symbol],
                'volume': self.volume_data[symbol],
                'change': self.price_data[symbol] * change_pct,
                'change_percent': change_pct * 100
            }
            
            self.market_data_service.update_market_data(symbol, market_data)
    
    def _update_position_prices(self) -> None:
        """Update position prices"""
        price_updates = {}
        for symbol in self.demo_symbols:
            price_updates[symbol] = self.price_data[symbol]
        
        self.portfolio_service.update_position_prices(price_updates)
    
    def _update_demo_charts(self) -> None:
        """Update demo charts with new data"""
        try:
            # Update line chart with BTC price
            if hasattr(self, 'demo_line_chart'):
                btc_price = self.price_data.get("BTCUSD", 45000)
                self.demo_line_chart.add_real_time_data(btc_price)
            
            # Update candlestick chart with ETH data
            if hasattr(self, 'demo_candle_chart'):
                eth_price = self.price_data.get("ETHUSD", 3000)
                
                # Generate OHLCV data
                open_price = eth_price * random.uniform(0.995, 1.005)
                close_price = eth_price
                high_price = max(open_price, close_price) * random.uniform(1.0, 1.01)
                low_price = min(open_price, close_price) * random.uniform(0.99, 1.0)
                volume = self.volume_data.get("ETHUSD", 50000)
                
                candle_data = {
                    'timestamp': datetime.now(),
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                }
                
                self.demo_candle_chart.add_real_time_data(candle_data)
            
            # Update performance chart
            if hasattr(self, 'demo_performance_chart'):
                portfolio_value = self.portfolio_service.get_portfolio_value()
                total_return = (portfolio_value / self.portfolio_service.initial_capital) - 1
                
                # Add to performance chart (simplified)
                if not hasattr(self, 'performance_returns'):
                    self.performance_returns = []
                
                self.performance_returns.append(total_return)
                
                # Keep only recent data
                if len(self.performance_returns) > 100:
                    self.performance_returns = self.performance_returns[-100:]
                
                self.demo_performance_chart.set_performance_data(self.performance_returns)
                
        except Exception as e:
            self._update_status(f"Error updating charts: {e}")
    
    def _update_alert_data(self) -> None:
        """Update alert service with current data"""
        try:
            # Update market data for alerts
            for symbol in self.demo_symbols:
                market_data = {
                    'price': self.price_data[symbol],
                    'volume': self.volume_data[symbol]
                }
                self.alert_service.update_market_data(symbol, market_data)
            
            # Update portfolio data for alerts
            portfolio_value = self.portfolio_service.get_portfolio_value()
            total_pnl = self.portfolio_service.get_total_pnl()
            
            # Calculate drawdown (simplified)
            if not hasattr(self, 'peak_value'):
                self.peak_value = portfolio_value
            
            if portfolio_value > self.peak_value:
                self.peak_value = portfolio_value
            
            drawdown = (self.peak_value - portfolio_value) / self.peak_value if self.peak_value > 0 else 0
            
            portfolio_data = {
                'portfolio_value': portfolio_value,
                'pnl': total_pnl,
                'drawdown': drawdown,
                'return_percent': ((portfolio_value / self.portfolio_service.initial_capital) - 1) * 100
            }
            
            self.alert_service.update_portfolio_data(portfolio_data)
            
        except Exception as e:
            self._update_status(f"Error updating alert data: {e}")
    
    async def _add_random_position(self) -> None:
        """Add a random position"""
        try:
            symbol = random.choice(self.demo_symbols)
            quantity = random.uniform(0.1, 5.0)
            entry_price = self.price_data[symbol]
            position_type = random.choice([PositionType.LONG, PositionType.SHORT])
            strategy_id = random.choice(["trend_following", "mean_reversion", "momentum", "arbitrage"])
            
            self.portfolio_service.add_position(
                symbol=symbol,
                quantity=quantity,
                entry_price=entry_price,
                position_type=position_type,
                strategy_id=strategy_id
            )
            
            self._update_status(f"Added {position_type.value} position: {quantity:.2f} {symbol} @ {entry_price:.2f}")
            
        except Exception as e:
            self._update_status(f"Error adding position: {e}")
    
    async def _create_random_alert(self) -> None:
        """Create a random alert"""
        try:
            symbol = random.choice(self.demo_symbols)
            current_price = self.price_data[symbol]
            
            # Create price alert above or below current price
            if random.choice([True, False]):
                # Price above alert
                threshold = current_price * random.uniform(1.05, 1.15)  # 5-15% above
                alert_type = AlertType.PRICE_ABOVE
                operator = "gt"
                name = f"{symbol} High Price Alert"
            else:
                # Price below alert
                threshold = current_price * random.uniform(0.85, 0.95)  # 5-15% below
                alert_type = AlertType.PRICE_BELOW
                operator = "lt"
                name = f"{symbol} Low Price Alert"
            
            condition = AlertCondition(field="price", operator=operator, value=threshold)
            priority = random.choice(list(AlertPriority))
            
            alert_id = self.alert_service.create_alert(
                name=name,
                alert_type=alert_type,
                condition=condition,
                symbol=symbol,
                priority=priority,
                notification_methods=[NotificationMethod.VISUAL]
            )
            
            self._update_status(f"Created alert: {name} (threshold: {threshold:.2f})")
            
        except Exception as e:
            self._update_status(f"Error creating alert: {e}")
    
    async def _generate_market_data(self) -> None:
        """Generate batch market data"""
        try:
            # Generate historical data for charts
            for symbol in self.demo_symbols:
                base_price = self.price_data[symbol]
                
                # Generate 50 historical points
                historical_data = []
                price = base_price * 0.9  # Start 10% lower
                
                for i in range(50):
                    change = random.uniform(-0.02, 0.02)
                    price *= (1 + change)
                    historical_data.append(price)
                
                # Update current price to last historical point
                self.price_data[symbol] = historical_data[-1]
            
            self._update_status("Generated historical market data")
            
        except Exception as e:
            self._update_status(f"Error generating market data: {e}")
    
    def _update_status(self, message: str) -> None:
        """Update status bar"""
        try:
            status_bar = self.query_one("#status", Static)
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_bar.update(f"[{timestamp}] {message}")
        except Exception:
            pass  # Ignore status update errors
    
    async def on_unmount(self) -> None:
        """Cleanup when unmounting"""
        try:
            await self._stop_demo()
            
            # Stop services
            await self.market_data_service.stop()
            await self.portfolio_service.stop()
            await self.alert_service.stop()
            
        except Exception as e:
            self._update_status(f"Error during cleanup: {e}")


def main():
    """Run the visualization demo"""
    app = VisualizationDemo()
    app.run()


if __name__ == "__main__":
    main()