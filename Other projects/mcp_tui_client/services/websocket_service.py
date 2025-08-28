"""
WebSocket Real-Time Service

Service for real-time data streaming from the MCP server, handling market data updates,
bot status changes, and other real-time events with automatic reconnection and subscription management.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..utils.errors import (
    ConnectionError, APIError, ErrorCategory, ErrorSeverity, 
    ErrorContext, handle_error, error_handler
)
from ..utils.logging import get_logger, get_performance_logger, timer


class WebSocketState(Enum):
    """WebSocket connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class MessageType(Enum):
    """WebSocket message types"""
    MARKET_DATA = "market_data"
    BOT_UPDATE = "bot_update"
    LAB_UPDATE = "lab_update"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SUBSCRIPTION_ACK = "subscription_ack"
    SUBSCRIPTION_ERROR = "subscription_error"


@dataclass
class WebSocketConfig:
    """WebSocket service configuration"""
    host: str = "localhost"
    port: int = 3003
    path: str = "/ws"
    use_ssl: bool = False
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30
    message_queue_size: int = 1000
    subscription_timeout: int = 10
    
    @property
    def url(self) -> str:
        protocol = "wss" if self.use_ssl else "ws"
        return f"{protocol}://{self.host}:{self.port}{self.path}"


@dataclass
class Subscription:
    """Represents a data subscription"""
    subscription_id: str
    message_type: MessageType
    parameters: Dict[str, Any]
    callback: Callable[[Dict[str, Any]], None]
    created_at: datetime = field(default_factory=datetime.now)
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    active: bool = True


@dataclass
class ConnectionStats:
    """WebSocket connection statistics"""
    connected_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    total_messages_received: int = 0
    total_messages_sent: int = 0
    reconnection_attempts: int = 0
    subscription_count: int = 0
    average_latency: float = 0.0
    latency_measurements: List[float] = field(default_factory=list)
    
    def add_latency_measurement(self, latency: float) -> None:
        """Add latency measurement to statistics"""
        self.latency_measurements.append(latency)
        if len(self.latency_measurements) > 100:  # Keep only last 100 measurements
            self.latency_measurements.pop(0)
        self.average_latency = sum(self.latency_measurements) / len(self.latency_measurements)


class WebSocketService:
    """Real-time data streaming service using WebSockets"""
    
    def __init__(self, config: WebSocketConfig):
        self.config = config
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.state = WebSocketState.DISCONNECTED
        self.stats = ConnectionStats()
        
        # Logging
        self.logger = get_logger(__name__, {"component": "websocket_service"})
        self.perf_logger = get_performance_logger(__name__)
        
        # Connection management
        self._connection_lock = asyncio.Lock()
        self._reconnect_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_handler_task: Optional[asyncio.Task] = None
        
        # Subscription management
        self._subscriptions: Dict[str, Subscription] = {}
        self._subscription_lock = asyncio.Lock()
        self._pending_subscriptions: Set[str] = set()
        
        # Message handling
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.message_queue_size)
        self._message_handlers: Dict[MessageType, List[Callable[[Dict[str, Any]], None]]] = {
            message_type: [] for message_type in MessageType
        }
        
        # Connection callbacks
        self._connection_callbacks: List[Callable[[WebSocketState], None]] = []
        
        # Health monitoring
        self._last_heartbeat_sent: Optional[datetime] = None
        self._last_heartbeat_received: Optional[datetime] = None
        self._connection_health_score: float = 1.0
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return (
            self.state == WebSocketState.CONNECTED and 
            self.websocket is not None and 
            not self.websocket.closed
        )
    
    @property
    def connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "state": self.state.value,
            "url": self.config.url,
            "connected_at": self.stats.connected_at.isoformat() if self.stats.connected_at else None,
            "total_messages_received": self.stats.total_messages_received,
            "total_messages_sent": self.stats.total_messages_sent,
            "subscription_count": len(self._subscriptions),
            "active_subscriptions": len([s for s in self._subscriptions.values() if s.active]),
            "average_latency": self.stats.average_latency,
            "connection_health_score": self._connection_health_score,
            "reconnection_attempts": self.stats.reconnection_attempts
        }
    
    def add_connection_callback(self, callback: Callable[[WebSocketState], None]) -> None:
        """Add connection state change callback"""
        self._connection_callbacks.append(callback)
    
    def remove_connection_callback(self, callback: Callable[[WebSocketState], None]) -> None:
        """Remove connection state change callback"""
        if callback in self._connection_callbacks:
            self._connection_callbacks.remove(callback)
    
    def _notify_connection_state_change(self, new_state: WebSocketState) -> None:
        """Notify all callbacks of connection state change"""
        old_state = self.state
        self.state = new_state
        
        self.logger.info(f"WebSocket state changed: {old_state.value} -> {new_state.value}")
        
        for callback in self._connection_callbacks:
            try:
                callback(new_state)
            except Exception as e:
                self.logger.error(f"Error in connection callback: {e}")
    
    @error_handler(category=ErrorCategory.CONNECTION, severity=ErrorSeverity.HIGH)
    async def connect(self) -> bool:
        """Connect to WebSocket server with retry logic"""
        async with self._connection_lock:
            if self.is_connected:
                return True
            
            self._notify_connection_state_change(WebSocketState.CONNECTING)
            
            try:
                # Connect to WebSocket server
                self.websocket = await websockets.connect(
                    self.config.url,
                    ping_interval=self.config.heartbeat_interval,
                    ping_timeout=10,
                    close_timeout=10
                )
                
                # Connection successful
                self.stats.connected_at = datetime.now()
                self.stats.reconnection_attempts = 0
                self._connection_health_score = 1.0
                
                self._notify_connection_state_change(WebSocketState.CONNECTED)
                
                # Start background tasks
                await self._start_background_tasks()
                
                # Resubscribe to existing subscriptions
                await self._resubscribe_all()
                
                self.logger.info(f"Successfully connected to WebSocket server at {self.config.url}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to connect to WebSocket server: {e}")
                self._notify_connection_state_change(WebSocketState.FAILED)
                
                if self.websocket:
                    await self.websocket.close()
                    self.websocket = None
                
                # Start auto-reconnection
                if not self._reconnect_task:
                    self._reconnect_task = asyncio.create_task(self._auto_reconnect())
                
                raise ConnectionError(f"Failed to connect to WebSocket server: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket server and cleanup resources"""
        async with self._connection_lock:
            self._notify_connection_state_change(WebSocketState.DISCONNECTED)
            
            # Cancel background tasks
            await self._stop_background_tasks()
            
            # Close WebSocket connection
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            # Clear subscriptions
            async with self._subscription_lock:
                for subscription in self._subscriptions.values():
                    subscription.active = False
            
            self.logger.info("Disconnected from WebSocket server")
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks for message handling and health monitoring"""
        # Start message handler
        if not self._message_handler_task:
            self._message_handler_task = asyncio.create_task(self._message_handler())
        
        # Start heartbeat monitoring
        if not self._heartbeat_task:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
    
    async def _stop_background_tasks(self) -> None:
        """Stop all background tasks"""
        tasks = [
            self._reconnect_task,
            self._heartbeat_task,
            self._message_handler_task
        ]
        
        for task in tasks:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._reconnect_task = None
        self._heartbeat_task = None
        self._message_handler_task = None
    
    async def _auto_reconnect(self) -> None:
        """Automatic reconnection with exponential backoff"""
        attempt = 0
        base_delay = self.config.reconnect_interval
        
        while (
            self.state != WebSocketState.CONNECTED and 
            attempt < self.config.max_reconnect_attempts
        ):
            try:
                self._notify_connection_state_change(WebSocketState.RECONNECTING)
                
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), 60)  # Max 60 seconds
                self.logger.info(f"Attempting reconnection in {delay} seconds (attempt {attempt + 1})")
                await asyncio.sleep(delay)
                
                attempt += 1
                self.stats.reconnection_attempts += 1
                
                if await self.connect():
                    self.logger.info("Reconnection successful")
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Reconnection attempt {attempt} failed: {e}")
                continue
        
        if attempt >= self.config.max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached, giving up")
            self._notify_connection_state_change(WebSocketState.FAILED)
        
        self._reconnect_task = None
    
    async def _message_handler(self) -> None:
        """Handle incoming WebSocket messages"""
        while self.is_connected:
            try:
                # Receive message with timeout
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=self.config.heartbeat_interval + 10
                )
                
                self.stats.total_messages_received += 1
                self.stats.last_message_at = datetime.now()
                
                # Parse message
                try:
                    data = json.loads(message)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Received invalid JSON message: {e}")
                    continue
                
                # Handle message
                await self._handle_message(data)
                
            except asyncio.TimeoutError:
                self.logger.warning("WebSocket message timeout")
                self._connection_health_score *= 0.9  # Reduce health score
                if self._connection_health_score < 0.5:
                    self.logger.error("Connection health degraded, triggering reconnection")
                    await self._trigger_reconnection()
                    break
                    
            except ConnectionClosed:
                self.logger.info("WebSocket connection closed")
                await self._trigger_reconnection()
                break
                
            except WebSocketException as e:
                self.logger.error(f"WebSocket error: {e}")
                await self._trigger_reconnection()
                break
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                self.logger.error(f"Unexpected error in message handler: {e}")
                continue
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle parsed WebSocket message"""
        try:
            message_type_str = data.get("type", "unknown")
            
            # Convert string to MessageType enum
            try:
                message_type = MessageType(message_type_str)
            except ValueError:
                self.logger.warning(f"Unknown message type: {message_type_str}")
                return
            
            # Handle heartbeat messages
            if message_type == MessageType.HEARTBEAT:
                self._last_heartbeat_received = datetime.now()
                self._connection_health_score = min(self._connection_health_score + 0.1, 1.0)
                return
            
            # Handle subscription acknowledgments
            if message_type == MessageType.SUBSCRIPTION_ACK:
                await self._handle_subscription_ack(data)
                return
            
            if message_type == MessageType.SUBSCRIPTION_ERROR:
                await self._handle_subscription_error(data)
                return
            
            # Route message to appropriate handlers
            await self._route_message(message_type, data)
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _route_message(self, message_type: MessageType, data: Dict[str, Any]) -> None:
        """Route message to appropriate handlers and subscriptions"""
        # Call global message handlers
        for handler in self._message_handlers.get(message_type, []):
            try:
                await asyncio.create_task(self._call_handler(handler, data))
            except Exception as e:
                self.logger.error(f"Error in message handler: {e}")
        
        # Call subscription-specific handlers
        subscription_id = data.get("subscription_id")
        if subscription_id and subscription_id in self._subscriptions:
            subscription = self._subscriptions[subscription_id]
            if subscription.active and subscription.message_type == message_type:
                try:
                    subscription.last_message_at = datetime.now()
                    subscription.message_count += 1
                    await asyncio.create_task(self._call_handler(subscription.callback, data))
                except Exception as e:
                    self.logger.error(f"Error in subscription callback: {e}")
    
    async def _call_handler(self, handler: Callable, data: Dict[str, Any]) -> None:
        """Call message handler, supporting both sync and async handlers"""
        if asyncio.iscoroutinefunction(handler):
            await handler(data)
        else:
            handler(data)
    
    async def _handle_subscription_ack(self, data: Dict[str, Any]) -> None:
        """Handle subscription acknowledgment"""
        subscription_id = data.get("subscription_id")
        if subscription_id in self._pending_subscriptions:
            self._pending_subscriptions.remove(subscription_id)
            self.logger.debug(f"Subscription acknowledged: {subscription_id}")
    
    async def _handle_subscription_error(self, data: Dict[str, Any]) -> None:
        """Handle subscription error"""
        subscription_id = data.get("subscription_id")
        error_message = data.get("error", "Unknown subscription error")
        
        if subscription_id in self._pending_subscriptions:
            self._pending_subscriptions.remove(subscription_id)
        
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id].active = False
        
        self.logger.error(f"Subscription error for {subscription_id}: {error_message}")
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor connection health with heartbeat messages"""
        while self.is_connected:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                
                if self.is_connected:
                    # Send heartbeat
                    await self._send_heartbeat()
                    
                    # Check if we've received recent heartbeats
                    if self._last_heartbeat_received:
                        time_since_heartbeat = datetime.now() - self._last_heartbeat_received
                        if time_since_heartbeat > timedelta(seconds=self.config.heartbeat_interval * 2):
                            self.logger.warning("No heartbeat received, connection may be stale")
                            self._connection_health_score *= 0.8
                            
                            if self._connection_health_score < 0.3:
                                await self._trigger_reconnection()
                                break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat monitor: {e}")
    
    async def _send_heartbeat(self) -> None:
        """Send heartbeat message"""
        if self.is_connected:
            heartbeat_message = {
                "type": MessageType.HEARTBEAT.value,
                "timestamp": datetime.now().isoformat()
            }
            await self._send_message(heartbeat_message)
            self._last_heartbeat_sent = datetime.now()
    
    async def _trigger_reconnection(self) -> None:
        """Trigger reconnection process"""
        if not self._reconnect_task:
            self._notify_connection_state_change(WebSocketState.FAILED)
            self._reconnect_task = asyncio.create_task(self._auto_reconnect())
    
    async def _send_message(self, message: Dict[str, Any]) -> None:
        """Send message to WebSocket server"""
        if not self.is_connected:
            raise ConnectionError("WebSocket not connected")
        
        try:
            message_json = json.dumps(message)
            await self.websocket.send(message_json)
            self.stats.total_messages_sent += 1
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise
    
    # Subscription Management Methods
    
    async def subscribe_market_data(
        self, 
        symbols: List[str], 
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to market data updates for specified symbols"""
        subscription_id = f"market_data_{int(time.time() * 1000)}"
        
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.MARKET_DATA,
            parameters={"symbols": symbols},
            callback=callback
        )
        
        return await self._create_subscription(subscription)
    
    async def subscribe_bot_updates(
        self, 
        bot_ids: List[str], 
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to bot status updates for specified bots"""
        subscription_id = f"bot_updates_{int(time.time() * 1000)}"
        
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.BOT_UPDATE,
            parameters={"bot_ids": bot_ids},
            callback=callback
        )
        
        return await self._create_subscription(subscription)
    
    async def subscribe_lab_updates(
        self, 
        lab_ids: List[str], 
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to lab execution updates for specified labs"""
        subscription_id = f"lab_updates_{int(time.time() * 1000)}"
        
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.LAB_UPDATE,
            parameters={"lab_ids": lab_ids},
            callback=callback
        )
        
        return await self._create_subscription(subscription)
    
    async def subscribe_system_status(
        self, 
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """Subscribe to system status updates"""
        subscription_id = f"system_status_{int(time.time() * 1000)}"
        
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.SYSTEM_STATUS,
            parameters={},
            callback=callback
        )
        
        return await self._create_subscription(subscription)
    
    async def _create_subscription(self, subscription: Subscription) -> str:
        """Create and register a new subscription"""
        async with self._subscription_lock:
            # Store subscription
            self._subscriptions[subscription.subscription_id] = subscription
            self._pending_subscriptions.add(subscription.subscription_id)
            
            # Send subscription request if connected
            if self.is_connected:
                await self._send_subscription_request(subscription)
            
            self.logger.info(f"Created subscription: {subscription.subscription_id}")
            return subscription.subscription_id
    
    async def _send_subscription_request(self, subscription: Subscription) -> None:
        """Send subscription request to server"""
        message = {
            "type": "subscribe",
            "subscription_id": subscription.subscription_id,
            "message_type": subscription.message_type.value,
            "parameters": subscription.parameters
        }
        
        await self._send_message(message)
        
        # Wait for acknowledgment with timeout
        try:
            await asyncio.wait_for(
                self._wait_for_subscription_ack(subscription.subscription_id),
                timeout=self.config.subscription_timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Subscription timeout: {subscription.subscription_id}")
            subscription.active = False
    
    async def _wait_for_subscription_ack(self, subscription_id: str) -> None:
        """Wait for subscription acknowledgment"""
        while subscription_id in self._pending_subscriptions:
            await asyncio.sleep(0.1)
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from a data stream"""
        async with self._subscription_lock:
            if subscription_id not in self._subscriptions:
                return False
            
            subscription = self._subscriptions[subscription_id]
            subscription.active = False
            
            # Send unsubscribe request if connected
            if self.is_connected:
                message = {
                    "type": "unsubscribe",
                    "subscription_id": subscription_id
                }
                try:
                    await self._send_message(message)
                except Exception as e:
                    self.logger.error(f"Failed to send unsubscribe request: {e}")
            
            # Remove subscription
            del self._subscriptions[subscription_id]
            
            self.logger.info(f"Unsubscribed: {subscription_id}")
            return True
    
    async def _resubscribe_all(self) -> None:
        """Resubscribe to all active subscriptions after reconnection"""
        async with self._subscription_lock:
            for subscription in self._subscriptions.values():
                if subscription.active:
                    try:
                        await self._send_subscription_request(subscription)
                    except Exception as e:
                        self.logger.error(f"Failed to resubscribe {subscription.subscription_id}: {e}")
                        subscription.active = False
    
    def add_message_handler(
        self, 
        message_type: MessageType, 
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Add global message handler for a specific message type"""
        self._message_handlers[message_type].append(handler)
    
    def remove_message_handler(
        self, 
        message_type: MessageType, 
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Remove global message handler"""
        if handler in self._message_handlers[message_type]:
            self._message_handlers[message_type].remove(handler)
    
    def get_subscriptions(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all subscriptions"""
        return {
            sub_id: {
                "message_type": sub.message_type.value,
                "parameters": sub.parameters,
                "created_at": sub.created_at.isoformat(),
                "last_message_at": sub.last_message_at.isoformat() if sub.last_message_at else None,
                "message_count": sub.message_count,
                "active": sub.active
            }
            for sub_id, sub in self._subscriptions.items()
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()