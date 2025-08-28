#!/usr/bin/env python3
"""
WebSocket Service Example

This example demonstrates how to use the WebSocket service to subscribe to
real-time market data and bot updates from the MCP server.
"""

import asyncio
import logging
from typing import Dict, Any

from mcp_tui_client.services.websocket_service import (
    WebSocketService, WebSocketConfig, WebSocketState, MessageType
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketExample:
    """Example WebSocket client implementation"""
    
    def __init__(self):
        # Configure WebSocket service
        self.config = WebSocketConfig(
            host="localhost",
            port=3003,
            path="/ws",
            use_ssl=False,
            reconnect_interval=5,
            max_reconnect_attempts=10,
            heartbeat_interval=30
        )
        
        self.websocket_service = WebSocketService(self.config)
        self.subscription_ids = []
        
        # Add connection state callback
        self.websocket_service.add_connection_callback(self.on_connection_state_change)
    
    def on_connection_state_change(self, state: WebSocketState) -> None:
        """Handle WebSocket connection state changes"""
        logger.info(f"WebSocket connection state changed to: {state.value}")
        
        if state == WebSocketState.CONNECTED:
            logger.info("WebSocket connected successfully!")
        elif state == WebSocketState.FAILED:
            logger.error("WebSocket connection failed!")
        elif state == WebSocketState.RECONNECTING:
            logger.info("WebSocket reconnecting...")
    
    def on_market_data(self, message: Dict[str, Any]) -> None:
        """Handle market data updates"""
        data = message.get("data", {})
        symbol = data.get("symbol", "Unknown")
        price = data.get("price", 0)
        volume = data.get("volume", 0)
        timestamp = data.get("timestamp", "")
        
        logger.info(f"Market Data - {symbol}: ${price:,.2f} (Volume: {volume:.4f}) at {timestamp}")
    
    def on_bot_update(self, message: Dict[str, Any]) -> None:
        """Handle bot status updates"""
        data = message.get("data", {})
        bot_id = data.get("bot_id", "Unknown")
        status = data.get("status", "Unknown")
        pnl = data.get("pnl", 0)
        positions = data.get("positions", 0)
        
        logger.info(f"Bot Update - {bot_id}: {status} (P&L: ${pnl:,.2f}, Positions: {positions})")
    
    def on_lab_update(self, message: Dict[str, Any]) -> None:
        """Handle lab execution updates"""
        data = message.get("data", {})
        lab_id = data.get("lab_id", "Unknown")
        status = data.get("status", "Unknown")
        progress = data.get("progress", 0)
        
        logger.info(f"Lab Update - {lab_id}: {status} ({progress:.1f}% complete)")
    
    def on_system_status(self, message: Dict[str, Any]) -> None:
        """Handle system status updates"""
        data = message.get("data", {})
        cpu_usage = data.get("cpu_usage", 0)
        memory_usage = data.get("memory_usage", 0)
        active_connections = data.get("active_connections", 0)
        
        logger.info(f"System Status - CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%, Connections: {active_connections}")
    
    def on_error(self, message: Dict[str, Any]) -> None:
        """Handle error messages"""
        error_code = message.get("error_code", "UNKNOWN")
        error_message = message.get("message", "Unknown error")
        details = message.get("details", {})
        
        logger.error(f"WebSocket Error - {error_code}: {error_message}")
        if details:
            logger.error(f"Error details: {details}")
    
    async def setup_subscriptions(self) -> None:
        """Set up WebSocket subscriptions"""
        try:
            # Subscribe to market data for popular trading pairs
            market_subscription_id = await self.websocket_service.subscribe_market_data(
                symbols=["BTC_USD", "ETH_USD", "ADA_USD", "DOT_USD"],
                callback=self.on_market_data
            )
            self.subscription_ids.append(market_subscription_id)
            logger.info(f"Subscribed to market data: {market_subscription_id}")
            
            # Subscribe to bot updates for all bots
            bot_subscription_id = await self.websocket_service.subscribe_bot_updates(
                bot_ids=["*"],  # Subscribe to all bots
                callback=self.on_bot_update
            )
            self.subscription_ids.append(bot_subscription_id)
            logger.info(f"Subscribed to bot updates: {bot_subscription_id}")
            
            # Subscribe to lab updates for all labs
            lab_subscription_id = await self.websocket_service.subscribe_lab_updates(
                lab_ids=["*"],  # Subscribe to all labs
                callback=self.on_lab_update
            )
            self.subscription_ids.append(lab_subscription_id)
            logger.info(f"Subscribed to lab updates: {lab_subscription_id}")
            
            # Subscribe to system status updates
            system_subscription_id = await self.websocket_service.subscribe_system_status(
                callback=self.on_system_status
            )
            self.subscription_ids.append(system_subscription_id)
            logger.info(f"Subscribed to system status: {system_subscription_id}")
            
            # Add global error handler
            self.websocket_service.add_message_handler(MessageType.ERROR, self.on_error)
            
            logger.info(f"Set up {len(self.subscription_ids)} subscriptions successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up subscriptions: {e}")
            raise
    
    async def cleanup_subscriptions(self) -> None:
        """Clean up WebSocket subscriptions"""
        logger.info("Cleaning up subscriptions...")
        
        for subscription_id in self.subscription_ids:
            try:
                success = await self.websocket_service.unsubscribe(subscription_id)
                if success:
                    logger.info(f"Unsubscribed from: {subscription_id}")
                else:
                    logger.warning(f"Failed to unsubscribe from: {subscription_id}")
            except Exception as e:
                logger.error(f"Error unsubscribing from {subscription_id}: {e}")
        
        self.subscription_ids.clear()
    
    async def print_connection_info(self) -> None:
        """Print WebSocket connection information"""
        info = self.websocket_service.connection_info
        
        logger.info("=== WebSocket Connection Info ===")
        logger.info(f"State: {info['state']}")
        logger.info(f"URL: {info['url']}")
        logger.info(f"Connected at: {info['connected_at']}")
        logger.info(f"Messages received: {info['total_messages_received']}")
        logger.info(f"Messages sent: {info['total_messages_sent']}")
        logger.info(f"Active subscriptions: {info['active_subscriptions']}")
        logger.info(f"Average latency: {info['average_latency']:.2f}ms")
        logger.info(f"Connection health: {info['connection_health_score']:.2f}")
        logger.info("================================")
    
    async def run(self, duration: int = 60) -> None:
        """Run the WebSocket example for specified duration"""
        logger.info(f"Starting WebSocket example for {duration} seconds...")
        
        try:
            # Connect to WebSocket server
            logger.info("Connecting to WebSocket server...")
            await self.websocket_service.connect()
            
            # Set up subscriptions
            await self.setup_subscriptions()
            
            # Print initial connection info
            await self.print_connection_info()
            
            # Run for specified duration
            logger.info(f"Listening for messages for {duration} seconds...")
            await asyncio.sleep(duration)
            
            # Print final connection info
            await self.print_connection_info()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise
        finally:
            # Clean up
            await self.cleanup_subscriptions()
            await self.websocket_service.disconnect()
            logger.info("WebSocket example completed")


async def main():
    """Main function"""
    example = WebSocketExample()
    
    try:
        # Run example for 60 seconds (or until interrupted)
        await example.run(duration=60)
    except KeyboardInterrupt:
        logger.info("Example interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run the example
    exit_code = asyncio.run(main())
    exit(exit_code)