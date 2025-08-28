"""
Real-Time Market Data Service

Provides real-time market data streaming, price feeds, order book visualization,
and trade history analysis.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import statistics

from ..utils.logging import get_logger
from ..utils.errors import handle_error, ErrorCategory, ErrorSeverity
from .websocket_service import WebSocketService
from .data_cache import DataCacheService


class MarketDataType(Enum):
    """Market data type enumeration"""
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    CANDLES = "candles"
    VOLUME = "volume"
    STATISTICS = "statistics"


class SubscriptionStatus(Enum):
    """Subscription status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class MarketTicker:
    """Market ticker data"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: float
    high_24h: float
    low_24h: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'change': self.change,
            'change_percent': self.change_percent,
            'volume': self.volume,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class OrderBookLevel:
    """Order book price level"""
    price: float
    quantity: float
    orders: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'price': self.price,
            'quantity': self.quantity,
            'orders': self.orders
        }


@dataclass
class OrderBook:
    """Order book data"""
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None
    
    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None
    
    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None
    
    @property
    def spread_percent(self) -> Optional[float]:
        if self.spread and self.best_bid:
            return (self.spread / self.best_bid) * 100
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'bids': [bid.to_dict() for bid in self.bids],
            'asks': [ask.to_dict() for ask in self.asks],
            'best_bid': self.best_bid,
            'best_ask': self.best_ask,
            'spread': self.spread,
            'spread_percent': self.spread_percent,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Trade:
    """Trade data"""
    symbol: str
    price: float
    quantity: float
    side: str  # 'buy' or 'sell'
    timestamp: datetime = field(default_factory=datetime.now)
    trade_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'quantity': self.quantity,
            'side': self.side,
            'timestamp': self.timestamp.isoformat(),
            'trade_id': self.trade_id
        }


@dataclass
class MarketCandle:
    """Market candle/OHLCV data"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: str = "1m"  # 1m, 5m, 15m, 1h, 4h, 1d
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'interval': self.interval
        }


@dataclass
class MarketStatistics:
    """Market statistics"""
    symbol: str
    price_change_24h: float
    price_change_percent_24h: float
    volume_24h: float
    volume_change_24h: float
    high_24h: float
    low_24h: float
    trades_count_24h: int
    volatility: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'price_change_24h': self.price_change_24h,
            'price_change_percent_24h': self.price_change_percent_24h,
            'volume_24h': self.volume_24h,
            'volume_change_24h': self.volume_change_24h,
            'high_24h': self.high_24h,
            'low_24h': self.low_24h,
            'trades_count_24h': self.trades_count_24h,
            'volatility': self.volatility,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MarketSubscription:
    """Market data subscription"""
    symbol: str
    data_type: MarketDataType
    status: SubscriptionStatus = SubscriptionStatus.PENDING
    callback: Optional[Callable] = None
    last_update: Optional[datetime] = None
    error_count: int = 0
    max_errors: int = 5
    
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE
    
    def increment_error(self) -> bool:
        """Increment error count and return True if max errors exceeded"""
        self.error_count += 1
        if self.error_count >= self.max_errors:
            self.status = SubscriptionStatus.ERROR
            return True
        return False


class RealTimeMarketDataService:
    """Real-time market data service"""
    
    def __init__(self, mcp_client=None, websocket_service: WebSocketService = None):
        self.mcp_client = mcp_client
        self.websocket_service = websocket_service
        self.logger = get_logger(__name__)
        
        # Data cache
        self.cache = DataCacheService()
        
        # Subscriptions
        self.subscriptions: Dict[str, MarketSubscription] = {}
        self.active_symbols: Set[str] = set()
        
        # Data storage
        self.tickers: Dict[str, MarketTicker] = {}
        self.order_books: Dict[str, OrderBook] = {}
        self.recent_trades: Dict[str, List[Trade]] = {}
        self.candles: Dict[str, Dict[str, List[MarketCandle]]] = {}  # symbol -> interval -> candles
        self.statistics: Dict[str, MarketStatistics] = {}
        
        # Configuration
        self.max_trades_per_symbol = 100
        self.max_candles_per_interval = 1000
        self.update_intervals = {
            MarketDataType.TICKER: 1.0,
            MarketDataType.ORDERBOOK: 0.5,
            MarketDataType.TRADES: 0.1,
            MarketDataType.CANDLES: 60.0,
            MarketDataType.STATISTICS: 300.0
        }
        
        # Callbacks
        self.data_callbacks: Dict[MarketDataType, List[Callable]] = {
            data_type: [] for data_type in MarketDataType
        }
        
        # Background tasks
        self.update_tasks: Dict[str, asyncio.Task] = {}
        self.running = False
    
    async def start(self) -> None:
        """Start the market data service"""
        try:
            self.running = True
            
            # Initialize WebSocket connection if available
            if self.websocket_service:
                await self.websocket_service.connect()
                self.websocket_service.add_message_handler(self._handle_websocket_message)
            
            # Start background update tasks
            await self._start_background_tasks()
            
            self.logger.info("Real-time market data service started")
            
        except Exception as e:
            self.logger.error(f"Failed to start market data service: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the market data service"""
        try:
            self.running = False
            
            # Cancel all subscriptions
            for subscription in self.subscriptions.values():
                subscription.status = SubscriptionStatus.CANCELLED
            
            # Stop background tasks
            for task in self.update_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self.update_tasks:
                await asyncio.gather(*self.update_tasks.values(), return_exceptions=True)
            
            self.update_tasks.clear()
            
            # Disconnect WebSocket
            if self.websocket_service:
                await self.websocket_service.disconnect()
            
            self.logger.info("Real-time market data service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping market data service: {e}")
    
    async def subscribe_ticker(
        self, 
        symbol: str, 
        callback: Optional[Callable[[MarketTicker], None]] = None
    ) -> str:
        """Subscribe to ticker updates for a symbol"""
        subscription_id = f"ticker_{symbol}"
        
        subscription = MarketSubscription(
            symbol=symbol,
            data_type=MarketDataType.TICKER,
            callback=callback
        )
        
        self.subscriptions[subscription_id] = subscription
        self.active_symbols.add(symbol)
        
        # Start ticker updates
        await self._start_ticker_updates(symbol)
        
        subscription.status = SubscriptionStatus.ACTIVE
        self.logger.info(f"Subscribed to ticker updates for {symbol}")
        
        return subscription_id
    
    async def subscribe_orderbook(
        self, 
        symbol: str, 
        depth: int = 10,
        callback: Optional[Callable[[OrderBook], None]] = None
    ) -> str:
        """Subscribe to order book updates for a symbol"""
        subscription_id = f"orderbook_{symbol}_{depth}"
        
        subscription = MarketSubscription(
            symbol=symbol,
            data_type=MarketDataType.ORDERBOOK,
            callback=callback
        )
        
        self.subscriptions[subscription_id] = subscription
        self.active_symbols.add(symbol)
        
        # Start order book updates
        await self._start_orderbook_updates(symbol, depth)
        
        subscription.status = SubscriptionStatus.ACTIVE
        self.logger.info(f"Subscribed to order book updates for {symbol} (depth: {depth})")
        
        return subscription_id
    
    async def subscribe_trades(
        self, 
        symbol: str,
        callback: Optional[Callable[[Trade], None]] = None
    ) -> str:
        """Subscribe to trade updates for a symbol"""
        subscription_id = f"trades_{symbol}"
        
        subscription = MarketSubscription(
            symbol=symbol,
            data_type=MarketDataType.TRADES,
            callback=callback
        )
        
        self.subscriptions[subscription_id] = subscription
        self.active_symbols.add(symbol)
        
        # Initialize trades list
        if symbol not in self.recent_trades:
            self.recent_trades[symbol] = []
        
        # Start trade updates
        await self._start_trade_updates(symbol)
        
        subscription.status = SubscriptionStatus.ACTIVE
        self.logger.info(f"Subscribed to trade updates for {symbol}")
        
        return subscription_id
    
    async def subscribe_candles(
        self, 
        symbol: str, 
        interval: str = "1m",
        callback: Optional[Callable[[MarketCandle], None]] = None
    ) -> str:
        """Subscribe to candle/OHLCV updates for a symbol"""
        subscription_id = f"candles_{symbol}_{interval}"
        
        subscription = MarketSubscription(
            symbol=symbol,
            data_type=MarketDataType.CANDLES,
            callback=callback
        )
        
        self.subscriptions[subscription_id] = subscription
        self.active_symbols.add(symbol)
        
        # Initialize candles storage
        if symbol not in self.candles:
            self.candles[symbol] = {}
        if interval not in self.candles[symbol]:
            self.candles[symbol][interval] = []
        
        # Start candle updates
        await self._start_candle_updates(symbol, interval)
        
        subscription.status = SubscriptionStatus.ACTIVE
        self.logger.info(f"Subscribed to candle updates for {symbol} ({interval})")
        
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from market data updates"""
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                subscription.status = SubscriptionStatus.CANCELLED
                
                # Stop related update task
                if subscription_id in self.update_tasks:
                    task = self.update_tasks[subscription_id]
                    if not task.done():
                        task.cancel()
                    del self.update_tasks[subscription_id]
                
                del self.subscriptions[subscription_id]
                
                self.logger.info(f"Unsubscribed from {subscription_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from {subscription_id}: {e}")
            return False
    
    def get_ticker(self, symbol: str) -> Optional[MarketTicker]:
        """Get latest ticker data for symbol"""
        return self.tickers.get(symbol)
    
    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get latest order book for symbol"""
        return self.order_books.get(symbol)
    
    def get_recent_trades(self, symbol: str, limit: int = 50) -> List[Trade]:
        """Get recent trades for symbol"""
        trades = self.recent_trades.get(symbol, [])
        return trades[-limit:] if trades else []
    
    def get_candles(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[MarketCandle]:
        """Get recent candles for symbol and interval"""
        if symbol in self.candles and interval in self.candles[symbol]:
            candles = self.candles[symbol][interval]
            return candles[-limit:] if candles else []
        return []
    
    def get_statistics(self, symbol: str) -> Optional[MarketStatistics]:
        """Get market statistics for symbol"""
        return self.statistics.get(symbol)
    
    def get_active_symbols(self) -> List[str]:
        """Get list of actively subscribed symbols"""
        return list(self.active_symbols)
    
    def get_subscription_status(self, subscription_id: str) -> Optional[SubscriptionStatus]:
        """Get subscription status"""
        subscription = self.subscriptions.get(subscription_id)
        return subscription.status if subscription else None
    
    def add_data_callback(self, data_type: MarketDataType, callback: Callable) -> None:
        """Add callback for specific data type"""
        self.data_callbacks[data_type].append(callback)
    
    def remove_data_callback(self, data_type: MarketDataType, callback: Callable) -> None:
        """Remove callback for specific data type"""
        if callback in self.data_callbacks[data_type]:
            self.data_callbacks[data_type].remove(callback)
    
    async def _start_background_tasks(self) -> None:
        """Start background update tasks"""
        # Statistics update task
        self.update_tasks['statistics'] = asyncio.create_task(
            self._statistics_update_loop()
        )
    
    async def _start_ticker_updates(self, symbol: str) -> None:
        """Start ticker updates for symbol"""
        task_id = f"ticker_{symbol}"
        if task_id not in self.update_tasks:
            self.update_tasks[task_id] = asyncio.create_task(
                self._ticker_update_loop(symbol)
            )
    
    async def _start_orderbook_updates(self, symbol: str, depth: int) -> None:
        """Start order book updates for symbol"""
        task_id = f"orderbook_{symbol}_{depth}"
        if task_id not in self.update_tasks:
            self.update_tasks[task_id] = asyncio.create_task(
                self._orderbook_update_loop(symbol, depth)
            )
    
    async def _start_trade_updates(self, symbol: str) -> None:
        """Start trade updates for symbol"""
        task_id = f"trades_{symbol}"
        if task_id not in self.update_tasks:
            self.update_tasks[task_id] = asyncio.create_task(
                self._trade_update_loop(symbol)
            )
    
    async def _start_candle_updates(self, symbol: str, interval: str) -> None:
        """Start candle updates for symbol"""
        task_id = f"candles_{symbol}_{interval}"
        if task_id not in self.update_tasks:
            self.update_tasks[task_id] = asyncio.create_task(
                self._candle_update_loop(symbol, interval)
            )
    
    async def _ticker_update_loop(self, symbol: str) -> None:
        """Background loop for ticker updates"""
        while self.running:
            try:
                # Fetch ticker data from MCP client
                if self.mcp_client:
                    ticker_data = await self._fetch_ticker_data(symbol)
                    if ticker_data:
                        ticker = MarketTicker(**ticker_data)
                        self.tickers[symbol] = ticker
                        
                        # Notify callbacks
                        await self._notify_ticker_callbacks(ticker)
                
                await asyncio.sleep(self.update_intervals[MarketDataType.TICKER])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in ticker update loop for {symbol}: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _orderbook_update_loop(self, symbol: str, depth: int) -> None:
        """Background loop for order book updates"""
        while self.running:
            try:
                # Fetch order book data from MCP client
                if self.mcp_client:
                    orderbook_data = await self._fetch_orderbook_data(symbol, depth)
                    if orderbook_data:
                        # Parse order book data
                        bids = [OrderBookLevel(**bid) for bid in orderbook_data.get('bids', [])]
                        asks = [OrderBookLevel(**ask) for ask in orderbook_data.get('asks', [])]
                        
                        orderbook = OrderBook(
                            symbol=symbol,
                            bids=bids,
                            asks=asks
                        )
                        
                        self.order_books[symbol] = orderbook
                        
                        # Notify callbacks
                        await self._notify_orderbook_callbacks(orderbook)
                
                await asyncio.sleep(self.update_intervals[MarketDataType.ORDERBOOK])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in order book update loop for {symbol}: {e}")
                await asyncio.sleep(5)
    
    async def _trade_update_loop(self, symbol: str) -> None:
        """Background loop for trade updates"""
        while self.running:
            try:
                # Fetch recent trades from MCP client
                if self.mcp_client:
                    trades_data = await self._fetch_trades_data(symbol)
                    if trades_data:
                        for trade_data in trades_data:
                            trade = Trade(**trade_data)
                            
                            # Add to recent trades
                            if symbol not in self.recent_trades:
                                self.recent_trades[symbol] = []
                            
                            self.recent_trades[symbol].append(trade)
                            
                            # Keep only recent trades
                            if len(self.recent_trades[symbol]) > self.max_trades_per_symbol:
                                self.recent_trades[symbol] = self.recent_trades[symbol][-self.max_trades_per_symbol:]
                            
                            # Notify callbacks
                            await self._notify_trade_callbacks(trade)
                
                await asyncio.sleep(self.update_intervals[MarketDataType.TRADES])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in trade update loop for {symbol}: {e}")
                await asyncio.sleep(5)
    
    async def _candle_update_loop(self, symbol: str, interval: str) -> None:
        """Background loop for candle updates"""
        while self.running:
            try:
                # Fetch candle data from MCP client
                if self.mcp_client:
                    candle_data = await self._fetch_candle_data(symbol, interval)
                    if candle_data:
                        candle = MarketCandle(**candle_data)
                        
                        # Add to candles storage
                        if symbol not in self.candles:
                            self.candles[symbol] = {}
                        if interval not in self.candles[symbol]:
                            self.candles[symbol][interval] = []
                        
                        self.candles[symbol][interval].append(candle)
                        
                        # Keep only recent candles
                        if len(self.candles[symbol][interval]) > self.max_candles_per_interval:
                            self.candles[symbol][interval] = self.candles[symbol][interval][-self.max_candles_per_interval:]
                        
                        # Notify callbacks
                        await self._notify_candle_callbacks(candle)
                
                await asyncio.sleep(self.update_intervals[MarketDataType.CANDLES])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in candle update loop for {symbol}: {e}")
                await asyncio.sleep(60)  # Longer wait for candle errors
    
    async def _statistics_update_loop(self) -> None:
        """Background loop for statistics updates"""
        while self.running:
            try:
                # Calculate statistics for all active symbols
                for symbol in self.active_symbols:
                    stats = await self._calculate_statistics(symbol)
                    if stats:
                        self.statistics[symbol] = stats
                        
                        # Notify callbacks
                        await self._notify_statistics_callbacks(stats)
                
                await asyncio.sleep(self.update_intervals[MarketDataType.STATISTICS])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in statistics update loop: {e}")
                await asyncio.sleep(60)
    
    async def _fetch_ticker_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch ticker data from MCP client"""
        try:
            if not self.mcp_client:
                return None
            
            # This would call the actual MCP client method
            # For now, return mock data
            import random
            base_price = 100 + random.uniform(-10, 10)
            change = random.uniform(-5, 5)
            
            return {
                'symbol': symbol,
                'price': base_price,
                'change': change,
                'change_percent': (change / base_price) * 100,
                'volume': random.uniform(10000, 100000),
                'high_24h': base_price + random.uniform(0, 5),
                'low_24h': base_price - random.uniform(0, 5)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching ticker data for {symbol}: {e}")
            return None
    
    async def _fetch_orderbook_data(self, symbol: str, depth: int) -> Optional[Dict[str, Any]]:
        """Fetch order book data from MCP client"""
        try:
            if not self.mcp_client:
                return None
            
            # Mock order book data
            import random
            base_price = 100 + random.uniform(-10, 10)
            
            bids = []
            asks = []
            
            for i in range(depth):
                bid_price = base_price - (i + 1) * 0.01
                ask_price = base_price + (i + 1) * 0.01
                
                bids.append({
                    'price': bid_price,
                    'quantity': random.uniform(1, 100),
                    'orders': random.randint(1, 10)
                })
                
                asks.append({
                    'price': ask_price,
                    'quantity': random.uniform(1, 100),
                    'orders': random.randint(1, 10)
                })
            
            return {
                'bids': bids,
                'asks': asks
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching order book data for {symbol}: {e}")
            return None
    
    async def _fetch_trades_data(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch recent trades data from MCP client"""
        try:
            if not self.mcp_client:
                return None
            
            # Mock trades data
            import random
            trades = []
            
            for _ in range(random.randint(1, 5)):
                trades.append({
                    'symbol': symbol,
                    'price': 100 + random.uniform(-10, 10),
                    'quantity': random.uniform(0.1, 10),
                    'side': random.choice(['buy', 'sell']),
                    'trade_id': f"trade_{random.randint(1000, 9999)}"
                })
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Error fetching trades data for {symbol}: {e}")
            return None
    
    async def _fetch_candle_data(self, symbol: str, interval: str) -> Optional[Dict[str, Any]]:
        """Fetch candle data from MCP client"""
        try:
            if not self.mcp_client:
                return None
            
            # Mock candle data
            import random
            base_price = 100 + random.uniform(-10, 10)
            change = random.uniform(-2, 2)
            
            open_price = base_price
            close_price = base_price + change
            high_price = max(open_price, close_price) + random.uniform(0, 1)
            low_price = min(open_price, close_price) - random.uniform(0, 1)
            
            return {
                'symbol': symbol,
                'timestamp': datetime.now(),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': random.uniform(1000, 10000),
                'interval': interval
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching candle data for {symbol}: {e}")
            return None
    
    async def _calculate_statistics(self, symbol: str) -> Optional[MarketStatistics]:
        """Calculate market statistics for symbol"""
        try:
            # Get recent data
            ticker = self.tickers.get(symbol)
            recent_trades = self.recent_trades.get(symbol, [])
            candles_1h = self.get_candles(symbol, "1h", 24)  # Last 24 hours
            
            if not ticker:
                return None
            
            # Calculate 24h statistics
            price_change_24h = ticker.change
            price_change_percent_24h = ticker.change_percent
            volume_24h = ticker.volume
            high_24h = ticker.high_24h
            low_24h = ticker.low_24h
            
            # Calculate volatility from recent candles
            volatility = 0.0
            if len(candles_1h) > 1:
                returns = []
                for i in range(1, len(candles_1h)):
                    ret = (candles_1h[i].close / candles_1h[i-1].close) - 1
                    returns.append(ret)
                
                if returns:
                    volatility = statistics.stdev(returns) * 100  # Convert to percentage
            
            # Count trades
            trades_count_24h = len([t for t in recent_trades 
                                  if (datetime.now() - t.timestamp).total_seconds() < 86400])
            
            # Volume change (mock calculation)
            volume_change_24h = random.uniform(-20, 20)  # Mock data
            
            return MarketStatistics(
                symbol=symbol,
                price_change_24h=price_change_24h,
                price_change_percent_24h=price_change_percent_24h,
                volume_24h=volume_24h,
                volume_change_24h=volume_change_24h,
                high_24h=high_24h,
                low_24h=low_24h,
                trades_count_24h=trades_count_24h,
                volatility=volatility
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics for {symbol}: {e}")
            return None
    
    async def _notify_ticker_callbacks(self, ticker: MarketTicker) -> None:
        """Notify ticker callbacks"""
        try:
            # Subscription-specific callbacks
            subscription_id = f"ticker_{ticker.symbol}"
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                if subscription.callback:
                    await self._safe_callback(subscription.callback, ticker)
            
            # Global callbacks
            for callback in self.data_callbacks[MarketDataType.TICKER]:
                await self._safe_callback(callback, ticker)
                
        except Exception as e:
            self.logger.error(f"Error notifying ticker callbacks: {e}")
    
    async def _notify_orderbook_callbacks(self, orderbook: OrderBook) -> None:
        """Notify order book callbacks"""
        try:
            # Find matching subscriptions
            for sub_id, subscription in self.subscriptions.items():
                if (subscription.data_type == MarketDataType.ORDERBOOK and 
                    subscription.symbol == orderbook.symbol and
                    subscription.callback):
                    await self._safe_callback(subscription.callback, orderbook)
            
            # Global callbacks
            for callback in self.data_callbacks[MarketDataType.ORDERBOOK]:
                await self._safe_callback(callback, orderbook)
                
        except Exception as e:
            self.logger.error(f"Error notifying order book callbacks: {e}")
    
    async def _notify_trade_callbacks(self, trade: Trade) -> None:
        """Notify trade callbacks"""
        try:
            subscription_id = f"trades_{trade.symbol}"
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                if subscription.callback:
                    await self._safe_callback(subscription.callback, trade)
            
            # Global callbacks
            for callback in self.data_callbacks[MarketDataType.TRADES]:
                await self._safe_callback(callback, trade)
                
        except Exception as e:
            self.logger.error(f"Error notifying trade callbacks: {e}")
    
    async def _notify_candle_callbacks(self, candle: MarketCandle) -> None:
        """Notify candle callbacks"""
        try:
            subscription_id = f"candles_{candle.symbol}_{candle.interval}"
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                if subscription.callback:
                    await self._safe_callback(subscription.callback, candle)
            
            # Global callbacks
            for callback in self.data_callbacks[MarketDataType.CANDLES]:
                await self._safe_callback(callback, candle)
                
        except Exception as e:
            self.logger.error(f"Error notifying candle callbacks: {e}")
    
    async def _notify_statistics_callbacks(self, stats: MarketStatistics) -> None:
        """Notify statistics callbacks"""
        try:
            # Global callbacks
            for callback in self.data_callbacks[MarketDataType.STATISTICS]:
                await self._safe_callback(callback, stats)
                
        except Exception as e:
            self.logger.error(f"Error notifying statistics callbacks: {e}")
    
    async def _safe_callback(self, callback: Callable, data: Any) -> None:
        """Safely execute callback"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            self.logger.error(f"Error in callback execution: {e}")
    
    async def _handle_websocket_message(self, message: Dict[str, Any]) -> None:
        """Handle WebSocket messages"""
        try:
            msg_type = message.get('type')
            symbol = message.get('symbol')
            
            if msg_type == 'ticker' and symbol:
                ticker_data = message.get('data', {})
                ticker_data['symbol'] = symbol
                ticker = MarketTicker(**ticker_data)
                self.tickers[symbol] = ticker
                await self._notify_ticker_callbacks(ticker)
            
            elif msg_type == 'orderbook' and symbol:
                orderbook_data = message.get('data', {})
                bids = [OrderBookLevel(**bid) for bid in orderbook_data.get('bids', [])]
                asks = [OrderBookLevel(**ask) for ask in orderbook_data.get('asks', [])]
                
                orderbook = OrderBook(symbol=symbol, bids=bids, asks=asks)
                self.order_books[symbol] = orderbook
                await self._notify_orderbook_callbacks(orderbook)
            
            elif msg_type == 'trade' and symbol:
                trade_data = message.get('data', {})
                trade_data['symbol'] = symbol
                trade = Trade(**trade_data)
                
                if symbol not in self.recent_trades:
                    self.recent_trades[symbol] = []
                self.recent_trades[symbol].append(trade)
                
                await self._notify_trade_callbacks(trade)
                
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'running': self.running,
            'active_symbols': list(self.active_symbols),
            'subscriptions': len(self.subscriptions),
            'active_tasks': len(self.update_tasks),
            'cached_tickers': len(self.tickers),
            'cached_orderbooks': len(self.order_books),
            'cached_trades': sum(len(trades) for trades in self.recent_trades.values()),
            'websocket_connected': self.websocket_service.is_connected() if self.websocket_service else False
        }