"""
Integration tests for WebSocket service with MCP client
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from mcp_tui_client.services.websocket_service import (
    WebSocketService, WebSocketConfig, WebSocketState, MessageType
)
from mcp_tui_client.services.mcp_client import MCPClientService, MCPConfig


class TestWebSocketMCPIntegration:
    """Test WebSocket service integration with MCP client"""
    
    @pytest.fixture
    def websocket_config(self):
        """WebSocket configuration fixture"""
        return WebSocketConfig(
            host="localhost",
            port=3003,
            reconnect_interval=1,
            max_reconnect_attempts=2,
            heartbeat_interval=5
        )
    
    @pytest.fixture
    def mcp_config(self):
        """MCP configuration fixture"""
        return MCPConfig(
            host="localhost",
            port=3002,
            timeout=10,
            retry_attempts=2
        )
    
    @pytest.fixture
    def websocket_service(self, websocket_config):
        """WebSocket service fixture"""
        return WebSocketService(websocket_config)
    
    @pytest.fixture
    def mcp_client(self, mcp_config):
        """MCP client fixture"""
        return MCPClientService(mcp_config)
    
    @pytest.mark.asyncio
    async def test_websocket_market_data_subscription(self, websocket_service):
        """Test market data subscription and message handling"""
        received_messages = []
        
        def market_data_callback(message):
            received_messages.append(message)
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        
        async def mock_connect_func(*args, **kwargs):
            return mock_websocket
        
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=mock_connect_func):
            with patch.object(websocket_service, '_start_background_tasks'):
                with patch.object(websocket_service, '_resubscribe_all'):
                    # Connect to WebSocket
                    await websocket_service.connect()
                    assert websocket_service.is_connected
                    
                    # Subscribe to market data
                    with patch.object(websocket_service, '_send_subscription_request'):
                        subscription_id = await websocket_service.subscribe_market_data(
                            ["BTC_USD", "ETH_USD"], 
                            market_data_callback
                        )
                        
                        assert subscription_id in websocket_service._subscriptions
                        
                        # Simulate receiving market data message
                        market_data_message = {
                            "type": "market_data",
                            "subscription_id": subscription_id,
                            "data": {
                                "symbol": "BTC_USD",
                                "price": 50000.0,
                                "volume": 1.5,
                                "timestamp": "2024-01-01T12:00:00Z"
                            }
                        }
                        
                        # Route message to subscription
                        await websocket_service._route_message(MessageType.MARKET_DATA, market_data_message)
                        
                        # Verify callback was called
                        assert len(received_messages) == 1
                        assert received_messages[0] == market_data_message
                        
                        # Verify subscription stats
                        subscription = websocket_service._subscriptions[subscription_id]
                        assert subscription.message_count == 1
                        assert subscription.last_message_at is not None
    
    @pytest.mark.asyncio
    async def test_websocket_bot_updates_subscription(self, websocket_service):
        """Test bot updates subscription and message handling"""
        received_updates = []
        
        def bot_update_callback(message):
            received_updates.append(message)
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        
        async def mock_connect_func(*args, **kwargs):
            return mock_websocket
        
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=mock_connect_func):
            with patch.object(websocket_service, '_start_background_tasks'):
                with patch.object(websocket_service, '_resubscribe_all'):
                    # Connect to WebSocket
                    await websocket_service.connect()
                    
                    # Subscribe to bot updates
                    with patch.object(websocket_service, '_send_subscription_request'):
                        subscription_id = await websocket_service.subscribe_bot_updates(
                            ["bot_123", "bot_456"], 
                            bot_update_callback
                        )
                        
                        # Simulate bot status update
                        bot_update_message = {
                            "type": "bot_update",
                            "subscription_id": subscription_id,
                            "data": {
                                "bot_id": "bot_123",
                                "status": "running",
                                "pnl": 150.75,
                                "positions": 3,
                                "last_trade": "2024-01-01T12:00:00Z"
                            }
                        }
                        
                        # Route message to subscription
                        await websocket_service._route_message(MessageType.BOT_UPDATE, bot_update_message)
                        
                        # Verify callback was called
                        assert len(received_updates) == 1
                        assert received_updates[0] == bot_update_message
    
    @pytest.mark.asyncio
    async def test_websocket_connection_recovery(self, websocket_service):
        """Test WebSocket connection recovery and resubscription"""
        # Mock WebSocket connection that fails initially
        connection_attempts = 0
        
        async def mock_connect_func(*args, **kwargs):
            nonlocal connection_attempts
            connection_attempts += 1
            if connection_attempts == 1:
                raise Exception("Connection failed")
            
            mock_websocket = AsyncMock()
            mock_websocket.closed = False
            return mock_websocket
        
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=mock_connect_func):
            with patch.object(websocket_service, '_start_background_tasks'):
                with patch.object(websocket_service, '_resubscribe_all') as mock_resubscribe:
                    # First connection attempt should fail
                    with pytest.raises(Exception):
                        await websocket_service.connect()
                    
                    assert websocket_service.state == WebSocketState.FAILED
                    
                    # Second connection attempt should succeed
                    await websocket_service.connect()
                    assert websocket_service.is_connected
                    assert websocket_service.state == WebSocketState.CONNECTED
                    
                    # Verify resubscription was called
                    mock_resubscribe.assert_called()
    
    @pytest.mark.asyncio
    async def test_websocket_multiple_subscriptions(self, websocket_service):
        """Test handling multiple concurrent subscriptions"""
        market_messages = []
        bot_messages = []
        system_messages = []
        
        def market_callback(msg):
            market_messages.append(msg)
        
        def bot_callback(msg):
            bot_messages.append(msg)
        
        def system_callback(msg):
            system_messages.append(msg)
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        
        async def mock_connect_func(*args, **kwargs):
            return mock_websocket
        
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=mock_connect_func):
            with patch.object(websocket_service, '_start_background_tasks'):
                with patch.object(websocket_service, '_resubscribe_all'):
                    # Connect to WebSocket
                    await websocket_service.connect()
                    
                    # Create multiple subscriptions
                    with patch.object(websocket_service, '_send_subscription_request'):
                        market_sub_id = await websocket_service.subscribe_market_data(
                            ["BTC_USD"], market_callback
                        )
                        bot_sub_id = await websocket_service.subscribe_bot_updates(
                            ["bot_123"], bot_callback
                        )
                        system_sub_id = await websocket_service.subscribe_system_status(
                            system_callback
                        )
                        
                        # Verify all subscriptions are active
                        assert len(websocket_service._subscriptions) == 3
                        assert all(sub.active for sub in websocket_service._subscriptions.values())
                        
                        # Send messages to each subscription
                        market_msg = {
                            "type": "market_data",
                            "subscription_id": market_sub_id,
                            "data": {"symbol": "BTC_USD", "price": 50000}
                        }
                        
                        bot_msg = {
                            "type": "bot_update", 
                            "subscription_id": bot_sub_id,
                            "data": {"bot_id": "bot_123", "status": "running"}
                        }
                        
                        system_msg = {
                            "type": "system_status",
                            "subscription_id": system_sub_id,
                            "data": {"cpu_usage": 45.2, "memory_usage": 67.8}
                        }
                        
                        # Route messages
                        await websocket_service._route_message(MessageType.MARKET_DATA, market_msg)
                        await websocket_service._route_message(MessageType.BOT_UPDATE, bot_msg)
                        await websocket_service._route_message(MessageType.SYSTEM_STATUS, system_msg)
                        
                        # Verify each callback received its message
                        assert len(market_messages) == 1
                        assert len(bot_messages) == 1
                        assert len(system_messages) == 1
                        
                        assert market_messages[0] == market_msg
                        assert bot_messages[0] == bot_msg
                        assert system_messages[0] == system_msg
    
    @pytest.mark.asyncio
    async def test_websocket_subscription_cleanup(self, websocket_service):
        """Test proper cleanup of subscriptions"""
        callback = Mock()
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.closed = False
        
        async def mock_connect_func(*args, **kwargs):
            return mock_websocket
        
        with patch('mcp_tui_client.services.websocket_service.websockets.connect', side_effect=mock_connect_func):
            with patch.object(websocket_service, '_start_background_tasks'):
                with patch.object(websocket_service, '_resubscribe_all'):
                    # Connect and create subscription
                    await websocket_service.connect()
                    
                    with patch.object(websocket_service, '_send_subscription_request'):
                        subscription_id = await websocket_service.subscribe_market_data(
                            ["BTC_USD"], callback
                        )
                        
                        assert subscription_id in websocket_service._subscriptions
                        assert websocket_service._subscriptions[subscription_id].active
                        
                        # Unsubscribe
                        with patch.object(websocket_service, '_send_message'):
                            result = await websocket_service.unsubscribe(subscription_id)
                            
                            assert result is True
                            assert subscription_id not in websocket_service._subscriptions
                    
                    # Disconnect and verify cleanup
                    await websocket_service.disconnect()
                    assert websocket_service.state == WebSocketState.DISCONNECTED
                    assert not websocket_service.is_connected
    
    @pytest.mark.asyncio
    async def test_websocket_heartbeat_handling(self, websocket_service):
        """Test heartbeat message handling"""
        initial_health = websocket_service._connection_health_score
        
        # Simulate heartbeat message
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        await websocket_service._handle_message(heartbeat_message)
        
        # Verify heartbeat was processed
        assert websocket_service._last_heartbeat_received is not None
        assert websocket_service._connection_health_score >= initial_health
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, websocket_service):
        """Test error message handling"""
        error_messages = []
        
        def error_callback(msg):
            error_messages.append(msg)
        
        # Add error message handler
        websocket_service.add_message_handler(MessageType.ERROR, error_callback)
        
        # Simulate error message
        error_message = {
            "type": "error",
            "error_code": "SUBSCRIPTION_FAILED",
            "message": "Invalid subscription parameters",
            "details": {"subscription_id": "invalid_sub_123"}
        }
        
        await websocket_service._route_message(MessageType.ERROR, error_message)
        
        # Verify error handler was called
        assert len(error_messages) == 1
        assert error_messages[0] == error_message