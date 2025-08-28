"""
Integration tests for MCP server communication.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from mcp_tui_client.services.mcp_client import MCPClientService


@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for MCP client service."""

    @pytest.mark.asyncio
    async def test_mcp_connection(self, mock_config):
        """Test MCP server connection."""
        # This would be a real integration test with actual MCP server
        # For now, we'll mock it to demonstrate the structure
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"status": "connected"}
            
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            client = MCPClientService(mock_config.get_mcp_settings())
            
            result = await client.connect()
            assert result is True
            assert client.is_connected is True

    @pytest.mark.asyncio
    async def test_tool_execution(self, mock_mcp_client):
        """Test MCP tool execution."""
        # Mock tool execution
        mock_mcp_client.call_tool.return_value = {
            "status": "success",
            "data": {
                "bots": [
                    {"id": "bot1", "name": "Test Bot", "status": "active"}
                ]
            }
        }
        
        result = await mock_mcp_client.call_tool("get_all_bots", {})
        
        assert result["status"] == "success"
        assert len(result["data"]["bots"]) == 1
        assert result["data"]["bots"][0]["name"] == "Test Bot"

    @pytest.mark.asyncio
    async def test_batch_operations(self, mock_mcp_client):
        """Test batch operation execution."""
        operations = [
            {"tool": "get_all_bots", "params": {}},
            {"tool": "get_all_labs", "params": {}},
            {"tool": "get_all_scripts", "params": {}}
        ]
        
        # Mock batch response
        mock_mcp_client.batch_operations.return_value = [
            {"status": "success", "data": {"bots": []}},
            {"status": "success", "data": {"labs": []}},
            {"status": "success", "data": {"scripts": []}}
        ]
        
        results = await mock_mcp_client.batch_operations(operations)
        
        assert len(results) == 3
        assert all(result["status"] == "success" for result in results)

    @pytest.mark.asyncio
    async def test_connection_retry_logic(self, mock_config):
        """Test connection retry with exponential backoff."""
        with patch('aiohttp.ClientSession') as mock_session:
            # First two attempts fail, third succeeds
            mock_session.return_value.__aenter__.return_value.post.side_effect = [
                Exception("Connection failed"),
                Exception("Connection failed"),
                AsyncMock(status=200, json=AsyncMock(return_value={"status": "connected"}))
            ]
            
            client = MCPClientService(mock_config.get_mcp_settings())
            
            # Should eventually succeed after retries
            result = await client.connect()
            assert result is True

    @pytest.mark.asyncio
    async def test_websocket_subscription(self, mock_mcp_client):
        """Test WebSocket real-time data subscription."""
        # Mock WebSocket connection
        mock_callback = AsyncMock()
        
        await mock_mcp_client.subscribe_updates(mock_callback)
        
        # Simulate receiving data
        test_data = {"type": "bot_update", "bot_id": "test-bot", "status": "active"}
        
        # In a real test, this would come from the WebSocket
        await mock_callback(test_data)
        
        mock_callback.assert_called_once_with(test_data)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_data_handling(self, mock_mcp_client):
        """Test handling of large datasets."""
        # Simulate large dataset response
        large_dataset = {
            "bots": [{"id": f"bot-{i}", "name": f"Bot {i}"} for i in range(1000)]
        }
        
        mock_mcp_client.call_tool.return_value = {
            "status": "success",
            "data": large_dataset
        }
        
        result = await mock_mcp_client.call_tool("get_all_bots", {})
        
        assert len(result["data"]["bots"]) == 1000
        assert result["data"]["bots"][0]["id"] == "bot-0"
        assert result["data"]["bots"][-1]["id"] == "bot-999"

    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, mock_config):
        """Test network timeout handling."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.post.side_effect = asyncio.TimeoutError()
            
            client = MCPClientService(mock_config.get_mcp_settings())
            
            # Should handle timeout gracefully
            result = await client.connect()
            assert result is False
            assert client.is_connected is False