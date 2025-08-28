"""
Unit tests for WebSocket Real-Time Service
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from mcp_tui_client.services.websocket_service import (
    WebSocketService, WebSocketConfig, WebSocketState, MessageType, Subscription
)
from mcp_tui_client.utils.errors import ConnectionError


class TestWebSocketConfig:
    """Test WebSocket configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = WebSocketConfig()
        assert config.host == "localhost"
        assert config.port == 3003
        assert config.path == "/ws"
        assert config.use_ssl is False
        assert config.url == "ws://localhost:3003/ws"
    
    def test_ssl_config(self):
        """Test SSL configuration"""
        config = WebSocketConfig(use_ssl=True)
        assert config.url == "wss://localhost:3003/ws"
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = WebSocketConfig(
            host="example.com",
            port=8080,
            path="/websocket",
            use_ssl=True
        )
        assert config.url == "wss://example.com:8080/websocket"


class TestWebSocketService:
    """Test WebSocket service functionality"""
    
    @pytest.fixture
    def config(self):
        """WebSocket configuration fixture"""
        return WebSocketConfig(
            host="localhost",
            port=3003,
            reconnect_interval=1,
            max_reconnect_attempts=3,
            heartbeat_interval=5
        )
    
    @pytest.fixture
    def service(self, config):
        """WebSocket service fixture"""
        return WebSocketService(config)
    
    def test_initialization(self, service, config):
        """Test service initialization"""
        assert service.config == config
        assert service.state == WebSocketState.DISCONNECTED
        assert not service.is_connected
        assert service.websocket is None
        assert len(service._subscriptions) == 0
    
    def test_connection_info(self, service):
        """Test connection info property"""
        info = service.connection_info
        assert info["state"] == "disconnected"
        assert info["url"] == "ws://localhost:3003/ws"
        assert info["total_messages_received"] == 0
        assert info["total_messages_sent"] == 0
        assert info["subscription_count"] == 0
    
    def test_connection_callbacks(self, service):
        """Test connection state callbacks"""
        callback_calls = []
        
        def callback(state):
            callback_calls.append(state)
        
        service.add_connection_callback(callback)
        service._notify_connection_state_change(WebSocketState.CONNECTING)
        service._notify_connection_state_change(WebSocketState.CONNECTED)
        
        assert len(callback_calls) == 2
        assert callback_calls[0] == WebSocketState.CONNECTING
        assert callback_calls[1] == WebSocketState.CONNECTED
        
        # Test callback removal
        service.remove_connection_callback(callback)
        service._notify_connection_state_change(WebSocketState.DISCONNECTED)
        assert len(callback_calls) == 2  # No new calls
    
    @pytest.mark.asyncio
    async def test_connect_success(self, service):
        """Test successful WebSocket connection"""
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        
        async def mock_connect_func(*args, **kwargs):
            return mock_websocket
        
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=mock_connect_func) as mock_connect:
            with patch.object(service, '_start_background_tasks') as mock_start_tasks:
                with patch.object(service, '_resubscribe_all') as mock_resubscribe:
                    result = await service.connect()
                    
                    assert result is True
                    assert service.is_connected
                    assert service.state == WebSocketState.CONNECTED
                    assert service.websocket == mock_websocket
                    
                    mock_connect.assert_called_once()
                    mock_start_tasks.assert_called_once()
                    mock_resubscribe.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self, service):
        """Test WebSocket connection failure"""
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=Exception("Connection failed")):
            with pytest.raises(ConnectionError):
                await service.connect()
            
            assert not service.is_connected
            assert service.state == WebSocketState.FAILED
            assert service.websocket is None
    
    @pytest.mark.asyncio
    async def test_disconnect(self, service):
        """Test WebSocket disconnection"""
        # Set up connected state
        mock_websocket = AsyncMock()
        service.websocket = mock_websocket
        service.state = WebSocketState.CONNECTED
        
        with patch.object(service, '_stop_background_tasks') as mock_stop_tasks:
            await service.disconnect()
            
            assert service.state == WebSocketState.DISCONNECTED
            assert service.websocket is None
            mock_websocket.close.assert_called_once()
            mock_stop_tasks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message(self, service):
        """Test sending WebSocket message"""
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        service.websocket = mock_websocket
        service.state = WebSocketState.CONNECTED
        
        message = {"type": "test", "data": "hello"}
        await service._send_message(message)
        
        expected_json = json.dumps(message)
        mock_websocket.send.assert_called_once_with(expected_json)
        assert service.stats.total_messages_sent == 1
    
    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, service):
        """Test sending message when not connected"""
        message = {"type": "test"}
        
        with pytest.raises(ConnectionError):
            await service._send_message(message)
    
    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self, service):
        """Test handling heartbeat message"""
        initial_health = service._connection_health_score
        
        heartbeat_data = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat()
        }
        
        await service._handle_message(heartbeat_data)
        
        assert service._last_heartbeat_received is not None
        assert service._connection_health_score >= initial_health
    
    @pytest.mark.asyncio
    async def test_handle_subscription_ack(self, service):
        """Test handling subscription acknowledgment"""
        subscription_id = "test_sub_123"
        service._pending_subscriptions.add(subscription_id)
        
        ack_data = {
            "type": "subscription_ack",
            "subscription_id": subscription_id
        }
        
        await service._handle_message(ack_data)
        
        assert subscription_id not in service._pending_subscriptions
    
    @pytest.mark.asyncio
    async def test_handle_subscription_error(self, service):
        """Test handling subscription error"""
        subscription_id = "test_sub_123"
        service._pending_subscriptions.add(subscription_id)
        
        # Create a test subscription
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.MARKET_DATA,
            parameters={"symbols": ["BTC_USD"]},
            callback=Mock()
        )
        service._subscriptions[subscription_id] = subscription
        
        error_data = {
            "type": "subscription_error",
            "subscription_id": subscription_id,
            "error": "Invalid symbol"
        }
        
        await service._handle_message(error_data)
        
        assert subscription_id not in service._pending_subscriptions
        assert not service._subscriptions[subscription_id].active
    
    @pytest.mark.asyncio
    async def test_subscribe_market_data(self, service):
        """Test market data subscription"""
        callback = Mock()
        symbols = ["BTC_USD", "ETH_USD"]
        
        # Mock connected state
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        service.state = WebSocketState.CONNECTED
        service.websocket = mock_websocket
        
        with patch.object(service, '_send_subscription_request') as mock_send:
            subscription_id = await service.subscribe_market_data(symbols, callback)
            
            assert subscription_id.startswith("market_data_")
            assert subscription_id in service._subscriptions
            
            subscription = service._subscriptions[subscription_id]
            assert subscription.message_type == MessageType.MARKET_DATA
            assert subscription.parameters["symbols"] == symbols
            assert subscription.callback == callback
            assert subscription.active
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_subscribe_bot_updates(self, service):
        """Test bot updates subscription"""
        callback = Mock()
        bot_ids = ["bot_1", "bot_2"]
        
        # Mock connected state
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        service.state = WebSocketState.CONNECTED
        service.websocket = mock_websocket
        
        with patch.object(service, '_send_subscription_request') as mock_send:
            subscription_id = await service.subscribe_bot_updates(bot_ids, callback)
            
            assert subscription_id.startswith("bot_updates_")
            assert subscription_id in service._subscriptions
            
            subscription = service._subscriptions[subscription_id]
            assert subscription.message_type == MessageType.BOT_UPDATE
            assert subscription.parameters["bot_ids"] == bot_ids
            assert subscription.callback == callback
    
    @pytest.mark.asyncio
    async def test_subscribe_lab_updates(self, service):
        """Test lab updates subscription"""
        callback = Mock()
        lab_ids = ["lab_1", "lab_2"]
        
        # Mock connected state
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        service.state = WebSocketState.CONNECTED
        service.websocket = mock_websocket
        
        with patch.object(service, '_send_subscription_request') as mock_send:
            subscription_id = await service.subscribe_lab_updates(lab_ids, callback)
            
            assert subscription_id.startswith("lab_updates_")
            assert subscription_id in service._subscriptions
            
            subscription = service._subscriptions[subscription_id]
            assert subscription.message_type == MessageType.LAB_UPDATE
            assert subscription.parameters["lab_ids"] == lab_ids
    
    @pytest.mark.asyncio
    async def test_subscribe_system_status(self, service):
        """Test system status subscription"""
        callback = Mock()
        
        # Mock connected state
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        service.state = WebSocketState.CONNECTED
        service.websocket = mock_websocket
        
        with patch.object(service, '_send_subscription_request') as mock_send:
            subscription_id = await service.subscribe_system_status(callback)
            
            assert subscription_id.startswith("system_status_")
            assert subscription_id in service._subscriptions
            
            subscription = service._subscriptions[subscription_id]
            assert subscription.message_type == MessageType.SYSTEM_STATUS
            assert subscription.parameters == {}
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, service):
        """Test unsubscribing from data stream"""
        # Create a test subscription
        subscription_id = "test_sub_123"
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.MARKET_DATA,
            parameters={"symbols": ["BTC_USD"]},
            callback=Mock()
        )
        service._subscriptions[subscription_id] = subscription
        
        # Mock connected state
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        service.state = WebSocketState.CONNECTED
        service.websocket = mock_websocket
        
        with patch.object(service, '_send_message') as mock_send:
            result = await service.unsubscribe(subscription_id)
            
            assert result is True
            assert subscription_id not in service._subscriptions
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, service):
        """Test unsubscribing from non-existent subscription"""
        result = await service.unsubscribe("nonexistent_sub")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_route_message_to_subscription(self, service):
        """Test routing message to subscription callback"""
        callback = Mock()
        subscription_id = "test_sub_123"
        
        # Create subscription
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.MARKET_DATA,
            parameters={"symbols": ["BTC_USD"]},
            callback=callback
        )
        service._subscriptions[subscription_id] = subscription
        
        # Test message
        message_data = {
            "type": "market_data",
            "subscription_id": subscription_id,
            "data": {"symbol": "BTC_USD", "price": 50000}
        }
        
        await service._route_message(MessageType.MARKET_DATA, message_data)
        
        # Verify callback was called
        callback.assert_called_once_with(message_data)
        assert subscription.message_count == 1
        assert subscription.last_message_at is not None
    
    def test_add_remove_message_handler(self, service):
        """Test adding and removing global message handlers"""
        handler = Mock()
        
        service.add_message_handler(MessageType.MARKET_DATA, handler)
        assert handler in service._message_handlers[MessageType.MARKET_DATA]
        
        service.remove_message_handler(MessageType.MARKET_DATA, handler)
        assert handler not in service._message_handlers[MessageType.MARKET_DATA]
    
    def test_get_subscriptions(self, service):
        """Test getting subscription information"""
        # Create test subscription
        subscription_id = "test_sub_123"
        subscription = Subscription(
            subscription_id=subscription_id,
            message_type=MessageType.MARKET_DATA,
            parameters={"symbols": ["BTC_USD"]},
            callback=Mock()
        )
        subscription.message_count = 5
        subscription.last_message_at = datetime.now()
        service._subscriptions[subscription_id] = subscription
        
        subscriptions_info = service.get_subscriptions()
        
        assert subscription_id in subscriptions_info
        sub_info = subscriptions_info[subscription_id]
        assert sub_info["message_type"] == "market_data"
        assert sub_info["parameters"] == {"symbols": ["BTC_USD"]}
        assert sub_info["message_count"] == 5
        assert sub_info["active"] is True
    
    @pytest.mark.asyncio
    async def test_context_manager(self, service):
        """Test async context manager functionality"""
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        
        async def mock_connect_func(*args, **kwargs):
            return mock_websocket
        
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=mock_connect_func):
            with patch.object(service, '_start_background_tasks'):
                with patch.object(service, '_resubscribe_all'):
                    async with service as ws_service:
                        assert ws_service.is_connected
                        assert ws_service.state == WebSocketState.CONNECTED
                    
                    # Should be disconnected after exiting context
                    assert ws_service.state == WebSocketState.DISCONNECTED
    
    @pytest.mark.asyncio
    async def test_call_handler_sync(self, service):
        """Test calling synchronous handler"""
        handler = Mock()
        data = {"test": "data"}
        
        await service._call_handler(handler, data)
        handler.assert_called_once_with(data)
    
    @pytest.mark.asyncio
    async def test_call_handler_async(self, service):
        """Test calling asynchronous handler"""
        handler = AsyncMock()
        data = {"test": "data"}
        
        await service._call_handler(handler, data)
        handler.assert_called_once_with(data)
    
    @pytest.mark.asyncio
    async def test_wait_for_subscription_ack(self, service):
        """Test waiting for subscription acknowledgment"""
        subscription_id = "test_sub_123"
        service._pending_subscriptions.add(subscription_id)
        
        # Remove from pending after a short delay
        async def remove_pending():
            await asyncio.sleep(0.1)
            service._pending_subscriptions.remove(subscription_id)
        
        # Start removal task
        asyncio.create_task(remove_pending())
        
        # Wait for acknowledgment
        await service._wait_for_subscription_ack(subscription_id)
        
        # Should complete without timeout
        assert subscription_id not in service._pending_subscriptions


class TestSubscription:
    """Test Subscription data class"""
    
    def test_subscription_creation(self):
        """Test subscription creation"""
        callback = Mock()
        subscription = Subscription(
            subscription_id="test_123",
            message_type=MessageType.MARKET_DATA,
            parameters={"symbols": ["BTC_USD"]},
            callback=callback
        )
        
        assert subscription.subscription_id == "test_123"
        assert subscription.message_type == MessageType.MARKET_DATA
        assert subscription.parameters == {"symbols": ["BTC_USD"]}
        assert subscription.callback == callback
        assert subscription.active is True
        assert subscription.message_count == 0
        assert subscription.last_message_at is None
        assert isinstance(subscription.created_at, datetime)


class TestMessageType:
    """Test MessageType enum"""
    
    def test_message_types(self):
        """Test all message types are defined"""
        expected_types = [
            "market_data", "bot_update", "lab_update", "system_status",
            "error", "heartbeat", "subscription_ack", "subscription_error"
        ]
        
        for expected_type in expected_types:
            assert hasattr(MessageType, expected_type.upper())
            assert MessageType(expected_type).value == expected_type


class TestWebSocketState:
    """Test WebSocketState enum"""
    
    def test_websocket_states(self):
        """Test all WebSocket states are defined"""
        expected_states = [
            "disconnected", "connecting", "connected", "reconnecting", "failed"
        ]
        
        for expected_state in expected_states:
            assert hasattr(WebSocketState, expected_state.upper())
            assert WebSocketState(expected_state).value == expected_state