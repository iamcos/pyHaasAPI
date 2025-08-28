"""
Market Data UI Components

Real-time market data visualization components including price feeds,
order book displays, trade history, and market overview.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from decimal import Decimal

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Label, DataTable, ProgressBar
from textual.reactive import reactive
from textual.timer import Timer

from ..components.panels import BasePanel
from ..components.charts import RealTimeChart, CandlestickChart
from ..components.tables import EnhancedDataTable
from ...services.market_data_service import (
    RealTimeMarketDataService, MarketTicker, OrderBook, Trade, 
    MarketCandle, MarketStatistics, MarketDataType
)
from ...services.chart_renderer import ChartConfig, ChartType
from ...utils.logging import get_logger


class PriceFeedPanel(BasePanel):
    """Real-time price feed display panel"""
    
    DEFAULT_CSS = """
    PriceFeedPanel {
        height: auto;
        min-height: 15;
    }
    
    .price-feed-header {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        text-align: center;
    }
    
    .price-item {
        height: 2;
        margin: 0 1;
        border: solid $accent;
        padding: 0 1;
    }
    
    .price-symbol {
        dock: left;
        width: 12;
        text-align: left;
        color: $text;
    }
    
    .price-value {
        dock: left;
        width: 15;
        text-align: right;
        color: $success;
    }
    
    .price-change {
        dock: left;
        width: 12;
        text-align: right;
    }
    
    .price-change-positive {
        color: $success;
    }
    
    .price-change-negative {
        color: $error;
    }
    
    .price-volume {
        dock: right;
        width: 15;
        text-align: right;
        color: $accent;
    }
    """
    
    def __init__(
        self, 
        market_data_service: RealTimeMarketDataService,
        symbols: List[str] = None,
        **kwargs
    ):
        super().__init__(title="Price Feed", **kwargs)
        self.logger = get_logger(__name__)
        self.market_data_service = market_data_service
        self.symbols = symbols or []
        self.subscriptions: Dict[str, str] = {}
        self.tickers: Dict[str, MarketTicker] = {}
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize price feed when mounted"""
        self._setup_price_feed()
        self._start_subscriptions()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        self._stop_subscriptions()
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_price_feed(self) -> None:
        """Set up price feed interface"""
        container = ScrollableContainer()
        
        # Header
        header = Label("Symbol      Price           Change        Volume", 
                      classes="price-feed-header")
        container.mount(header)
        
        # Price items container
        self.price_container = Vertical(id="price-container")
        container.mount(self.price_container)
        
        self.update_content(container)
    
    async def _start_subscriptions(self) -> None:
        """Start market data subscriptions"""
        try:
            for symbol in self.symbols:
                subscription_id = await self.market_data_service.subscribe_ticker(
                    symbol, self._on_ticker_update
                )
                self.subscriptions[symbol] = subscription_id
            
            # Start update timer
            self.update_timer = self.set_interval(1.0, self._update_display)
            
        except Exception as e:
            self.logger.error(f"Error starting price feed subscriptions: {e}")
    
    def _stop_subscriptions(self) -> None:
        """Stop market data subscriptions"""
        try:
            for subscription_id in self.subscriptions.values():
                asyncio.create_task(
                    self.market_data_service.unsubscribe(subscription_id)
                )
            self.subscriptions.clear()
            
        except Exception as e:
            self.logger.error(f"Error stopping price feed subscriptions: {e}")
    
    def _on_ticker_update(self, ticker: MarketTicker) -> None:
        """Handle ticker updates"""
        self.tickers[ticker.symbol] = ticker
    
    def _update_display(self) -> None:
        """Update price feed display"""
        try:
            price_container = self.query_one("#price-container")
            price_container.remove_children()
            
            for symbol in self.symbols:
                ticker = self.tickers.get(symbol)
                if ticker:
                    price_item = self._create_price_item(ticker)
                    price_container.mount(price_item)
                    
        except Exception as e:
            self.logger.error(f"Error updating price feed display: {e}")
    
    def _create_price_item(self, ticker: MarketTicker) -> Container:
        """Create price item widget"""
        item = Horizontal(classes="price-item")
        
        # Symbol
        symbol_label = Label(ticker.symbol, classes="price-symbol")
        item.mount(symbol_label)
        
        # Price
        price_label = Label(f"${ticker.price:.4f}", classes="price-value")
        item.mount(price_label)
        
        # Change
        change_text = f"{ticker.change:+.4f} ({ticker.change_percent:+.2f}%)"
        change_class = "price-change-positive" if ticker.change >= 0 else "price-change-negative"
        change_label = Label(change_text, classes=f"price-change {change_class}")
        item.mount(change_label)
        
        # Volume
        volume_text = f"{ticker.volume:,.0f}"
        volume_label = Label(volume_text, classes="price-volume")
        item.mount(volume_label)
        
        return item
    
    def add_symbol(self, symbol: str) -> None:
        """Add symbol to price feed"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            # Start subscription for new symbol
            asyncio.create_task(self._subscribe_symbol(symbol))
    
    def remove_symbol(self, symbol: str) -> None:
        """Remove symbol from price feed"""
        if symbol in self.symbols:
            self.symbols.remove(symbol)
            # Stop subscription
            if symbol in self.subscriptions:
                subscription_id = self.subscriptions[symbol]
                asyncio.create_task(
                    self.market_data_service.unsubscribe(subscription_id)
                )
                del self.subscriptions[symbol]
            
            if symbol in self.tickers:
                del self.tickers[symbol]
    
    async def _subscribe_symbol(self, symbol: str) -> None:
        """Subscribe to ticker updates for symbol"""
        try:
            subscription_id = await self.market_data_service.subscribe_ticker(
                symbol, self._on_ticker_update
            )
            self.subscriptions[symbol] = subscription_id
        except Exception as e:
            self.logger.error(f"Error subscribing to {symbol}: {e}")


class OrderBookPanel(BasePanel):
    """Order book visualization panel"""
    
    DEFAULT_CSS = """
    OrderBookPanel {
        height: auto;
        min-height: 20;
    }
    
    .orderbook-header {
        dock: top;
        height: 3;
        background: $primary;
        padding: 1;
    }
    
    .orderbook-symbol {
        text-align: center;
        color: $text;
        text-style: bold;
    }
    
    .orderbook-spread {
        text-align: center;
        color: $accent;
    }
    
    .orderbook-content {
        height: 1fr;
    }
    
    .orderbook-side {
        width: 50%;
        border: solid $accent;
        padding: 1;
    }
    
    .orderbook-asks {
        dock: left;
    }
    
    .orderbook-bids {
        dock: right;
    }
    
    .orderbook-level {
        height: 1;
        margin: 0;
    }
    
    .ask-level {
        color: $error;
    }
    
    .bid-level {
        color: $success;
    }
    
    .level-price {
        dock: left;
        width: 12;
        text-align: right;
    }
    
    .level-quantity {
        dock: right;
        width: 10;
        text-align: right;
    }
    
    .level-bar {
        height: 1;
        background: $surface;
    }
    """
    
    def __init__(
        self, 
        market_data_service: RealTimeMarketDataService,
        symbol: str,
        depth: int = 10,
        **kwargs
    ):
        super().__init__(title=f"Order Book - {symbol}", **kwargs)
        self.logger = get_logger(__name__)
        self.market_data_service = market_data_service
        self.symbol = symbol
        self.depth = depth
        self.subscription_id: Optional[str] = None
        self.order_book: Optional[OrderBook] = None
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize order book when mounted"""
        self._setup_order_book()
        self._start_subscription()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        self._stop_subscription()
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_order_book(self) -> None:
        """Set up order book interface"""
        container = Vertical()
        
        # Header with symbol and spread info
        header = Vertical(classes="orderbook-header")
        self.symbol_label = Label(self.symbol, classes="orderbook-symbol")
        self.spread_label = Label("Spread: --", classes="orderbook-spread")
        header.mount(self.symbol_label)
        header.mount(self.spread_label)
        container.mount(header)
        
        # Order book content
        content = Horizontal(classes="orderbook-content")
        
        # Asks (left side)
        asks_container = Vertical(classes="orderbook-side orderbook-asks")
        asks_header = Label("ASKS", classes="orderbook-symbol")
        asks_container.mount(asks_header)
        self.asks_container = Vertical(id="asks-levels")
        asks_container.mount(self.asks_container)
        content.mount(asks_container)
        
        # Bids (right side)
        bids_container = Vertical(classes="orderbook-side orderbook-bids")
        bids_header = Label("BIDS", classes="orderbook-symbol")
        bids_container.mount(bids_header)
        self.bids_container = Vertical(id="bids-levels")
        bids_container.mount(self.bids_container)
        content.mount(bids_container)
        
        container.mount(content)
        self.update_content(container)
    
    async def _start_subscription(self) -> None:
        """Start order book subscription"""
        try:
            self.subscription_id = await self.market_data_service.subscribe_orderbook(
                self.symbol, self.depth, self._on_orderbook_update
            )
            
            # Start update timer
            self.update_timer = self.set_interval(0.5, self._update_display)
            
        except Exception as e:
            self.logger.error(f"Error starting order book subscription: {e}")
    
    def _stop_subscription(self) -> None:
        """Stop order book subscription"""
        try:
            if self.subscription_id:
                asyncio.create_task(
                    self.market_data_service.unsubscribe(self.subscription_id)
                )
                self.subscription_id = None
                
        except Exception as e:
            self.logger.error(f"Error stopping order book subscription: {e}")
    
    def _on_orderbook_update(self, order_book: OrderBook) -> None:
        """Handle order book updates"""
        self.order_book = order_book
    
    def _update_display(self) -> None:
        """Update order book display"""
        try:
            if not self.order_book:
                return
            
            # Update spread info
            if self.order_book.spread:
                spread_text = f"Spread: ${self.order_book.spread:.4f} ({self.order_book.spread_percent:.2f}%)"
                self.spread_label.update(spread_text)
            
            # Update asks
            asks_container = self.query_one("#asks-levels")
            asks_container.remove_children()
            
            max_quantity = max(
                max([ask.quantity for ask in self.order_book.asks], default=0),
                max([bid.quantity for bid in self.order_book.bids], default=0)
            )
            
            for ask in self.order_book.asks[:self.depth]:
                level_widget = self._create_level_widget(ask, max_quantity, "ask")
                asks_container.mount(level_widget)
            
            # Update bids
            bids_container = self.query_one("#bids-levels")
            bids_container.remove_children()
            
            for bid in self.order_book.bids[:self.depth]:
                level_widget = self._create_level_widget(bid, max_quantity, "bid")
                bids_container.mount(level_widget)
                
        except Exception as e:
            self.logger.error(f"Error updating order book display: {e}")
    
    def _create_level_widget(self, level, max_quantity: float, side: str) -> Container:
        """Create order book level widget"""
        level_container = Horizontal(classes=f"orderbook-level {side}-level")
        
        # Price
        price_label = Label(f"${level.price:.4f}", classes="level-price")
        level_container.mount(price_label)
        
        # Quantity bar (visual representation)
        bar_width = int((level.quantity / max_quantity) * 20) if max_quantity > 0 else 0
        bar_text = "█" * bar_width + " " * (20 - bar_width)
        bar_label = Label(bar_text, classes="level-bar")
        level_container.mount(bar_label)
        
        # Quantity
        quantity_label = Label(f"{level.quantity:.2f}", classes="level-quantity")
        level_container.mount(quantity_label)
        
        return level_container


class TradeHistoryPanel(BasePanel):
    """Trade history display panel"""
    
    DEFAULT_CSS = """
    TradeHistoryPanel {
        height: auto;
        min-height: 15;
    }
    
    .trade-item {
        height: 1;
        margin: 0;
    }
    
    .trade-buy {
        color: $success;
    }
    
    .trade-sell {
        color: $error;
    }
    
    .trade-time {
        dock: left;
        width: 10;
    }
    
    .trade-side {
        dock: left;
        width: 6;
        text-align: center;
    }
    
    .trade-price {
        dock: left;
        width: 12;
        text-align: right;
    }
    
    .trade-quantity {
        dock: right;
        width: 12;
        text-align: right;
    }
    """
    
    def __init__(
        self, 
        market_data_service: RealTimeMarketDataService,
        symbol: str,
        max_trades: int = 50,
        **kwargs
    ):
        super().__init__(title=f"Trade History - {symbol}", **kwargs)
        self.logger = get_logger(__name__)
        self.market_data_service = market_data_service
        self.symbol = symbol
        self.max_trades = max_trades
        self.subscription_id: Optional[str] = None
        self.trades: List[Trade] = []
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize trade history when mounted"""
        self._setup_trade_history()
        self._start_subscription()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        self._stop_subscription()
    
    def _setup_trade_history(self) -> None:
        """Set up trade history interface"""
        container = ScrollableContainer()
        
        # Header
        header = Label("Time      Side   Price        Quantity", classes="trade-header")
        container.mount(header)
        
        # Trades container
        self.trades_container = Vertical(id="trades-container")
        container.mount(self.trades_container)
        
        self.update_content(container)
    
    async def _start_subscription(self) -> None:
        """Start trade subscription"""
        try:
            self.subscription_id = await self.market_data_service.subscribe_trades(
                self.symbol, self._on_trade_update
            )
            
        except Exception as e:
            self.logger.error(f"Error starting trade subscription: {e}")
    
    def _stop_subscription(self) -> None:
        """Stop trade subscription"""
        try:
            if self.subscription_id:
                asyncio.create_task(
                    self.market_data_service.unsubscribe(self.subscription_id)
                )
                self.subscription_id = None
                
        except Exception as e:
            self.logger.error(f"Error stopping trade subscription: {e}")
    
    def _on_trade_update(self, trade: Trade) -> None:
        """Handle trade updates"""
        self.trades.append(trade)
        
        # Keep only recent trades
        if len(self.trades) > self.max_trades:
            self.trades = self.trades[-self.max_trades:]
        
        self._update_display()
    
    def _update_display(self) -> None:
        """Update trade history display"""
        try:
            trades_container = self.query_one("#trades-container")
            trades_container.remove_children()
            
            # Show most recent trades first
            for trade in reversed(self.trades[-20:]):  # Show last 20 trades
                trade_item = self._create_trade_item(trade)
                trades_container.mount(trade_item)
                
        except Exception as e:
            self.logger.error(f"Error updating trade history display: {e}")
    
    def _create_trade_item(self, trade: Trade) -> Container:
        """Create trade item widget"""
        side_class = "trade-buy" if trade.side == "buy" else "trade-sell"
        item = Horizontal(classes=f"trade-item {side_class}")
        
        # Time
        time_str = trade.timestamp.strftime("%H:%M:%S")
        time_label = Label(time_str, classes="trade-time")
        item.mount(time_label)
        
        # Side
        side_label = Label(trade.side.upper(), classes="trade-side")
        item.mount(side_label)
        
        # Price
        price_label = Label(f"${trade.price:.4f}", classes="trade-price")
        item.mount(price_label)
        
        # Quantity
        quantity_label = Label(f"{trade.quantity:.4f}", classes="trade-quantity")
        item.mount(quantity_label)
        
        return item


class MarketOverviewPanel(BasePanel):
    """Market overview with multiple symbols"""
    
    def __init__(
        self, 
        market_data_service: RealTimeMarketDataService,
        symbols: List[str] = None,
        **kwargs
    ):
        super().__init__(title="Market Overview", **kwargs)
        self.logger = get_logger(__name__)
        self.market_data_service = market_data_service
        self.symbols = symbols or []
        self.statistics: Dict[str, MarketStatistics] = {}
        self.update_timer: Optional[Timer] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize market overview when mounted"""
        self._setup_overview()
        self._start_updates()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        if self.update_timer:
            self.update_timer.stop()
    
    def _setup_overview(self) -> None:
        """Set up market overview interface"""
        # Create data table for market overview
        table = EnhancedDataTable(
            title="Market Statistics",
            show_header=True,
            show_row_labels=False
        )
        
        # Add columns
        table.add_column("Symbol", width=12)
        table.add_column("Price", width=12)
        table.add_column("Change %", width=10)
        table.add_column("Volume", width=15)
        table.add_column("High 24h", width=12)
        table.add_column("Low 24h", width=12)
        table.add_column("Volatility", width=10)
        
        self.overview_table = table
        self.update_content(table)
    
    def _start_updates(self) -> None:
        """Start periodic updates"""
        # Add statistics callback
        self.market_data_service.add_data_callback(
            MarketDataType.STATISTICS, self._on_statistics_update
        )
        
        # Start update timer
        self.update_timer = self.set_interval(5.0, self._update_display)
    
    def _on_statistics_update(self, stats: MarketStatistics) -> None:
        """Handle statistics updates"""
        self.statistics[stats.symbol] = stats
    
    def _update_display(self) -> None:
        """Update market overview display"""
        try:
            # Clear existing rows
            self.overview_table.clear()
            
            # Add rows for each symbol
            for symbol in self.symbols:
                stats = self.statistics.get(symbol)
                if stats:
                    # Get current ticker for price
                    ticker = self.market_data_service.get_ticker(symbol)
                    price = f"${ticker.price:.4f}" if ticker else "--"
                    
                    self.overview_table.add_row(
                        symbol,
                        price,
                        f"{stats.price_change_percent_24h:+.2f}%",
                        f"{stats.volume_24h:,.0f}",
                        f"${stats.high_24h:.4f}",
                        f"${stats.low_24h:.4f}",
                        f"{stats.volatility:.2f}%"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error updating market overview: {e}")


class RealTimeChartPanel(BasePanel):
    """Real-time chart panel for market data"""
    
    def __init__(
        self, 
        market_data_service: RealTimeMarketDataService,
        symbol: str,
        chart_type: ChartType = ChartType.CANDLESTICK,
        interval: str = "1m",
        **kwargs
    ):
        super().__init__(title=f"{symbol} - {interval}", **kwargs)
        self.logger = get_logger(__name__)
        self.market_data_service = market_data_service
        self.symbol = symbol
        self.chart_type = chart_type
        self.interval = interval
        self.subscription_id: Optional[str] = None
        self.chart: Optional[RealTimeChart] = None
    
    def compose(self) -> ComposeResult:
        yield from super().compose()
    
    def on_mount(self) -> None:
        """Initialize chart when mounted"""
        self._setup_chart()
        self._start_subscription()
    
    def on_unmount(self) -> None:
        """Cleanup when unmounted"""
        self._stop_subscription()
    
    def _setup_chart(self) -> None:
        """Set up real-time chart"""
        config = ChartConfig(
            width=80,
            height=20,
            title=f"{self.symbol} {self.interval}",
            show_legend=True
        )
        
        self.chart = RealTimeChart(
            title=f"{self.symbol} Chart",
            chart_type=self.chart_type,
            config=config,
            update_interval=1.0,
            max_points=100
        )
        
        self.update_content(self.chart)
    
    async def _start_subscription(self) -> None:
        """Start chart data subscription"""
        try:
            if self.chart_type == ChartType.CANDLESTICK:
                self.subscription_id = await self.market_data_service.subscribe_candles(
                    self.symbol, self.interval, self._on_candle_update
                )
            else:
                self.subscription_id = await self.market_data_service.subscribe_ticker(
                    self.symbol, self._on_ticker_update
                )
                
        except Exception as e:
            self.logger.error(f"Error starting chart subscription: {e}")
    
    def _stop_subscription(self) -> None:
        """Stop chart subscription"""
        try:
            if self.subscription_id:
                asyncio.create_task(
                    self.market_data_service.unsubscribe(self.subscription_id)
                )
                self.subscription_id = None
                
        except Exception as e:
            self.logger.error(f"Error stopping chart subscription: {e}")
    
    def _on_candle_update(self, candle: MarketCandle) -> None:
        """Handle candle updates"""
        if self.chart:
            candle_data = {
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            }
            self.chart.add_real_time_data(candle_data)
    
    def _on_ticker_update(self, ticker: MarketTicker) -> None:
        """Handle ticker updates for line charts"""
        if self.chart and self.chart_type == ChartType.LINE:
            self.chart.add_real_time_data(ticker.price)