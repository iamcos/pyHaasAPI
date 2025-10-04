"""
Integration tests for API components.
"""

import pytest
from unittest.mock import AsyncMock, patch
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI


class TestAPIIntegration:
    """Test API integration functionality."""
    
    @pytest.mark.asyncio
    async def test_lab_api_integration(self, mock_async_client, mock_auth_manager):
        """Test LabAPI integration with client and auth."""
        # Mock successful responses for get_json method with correct field names
        mock_async_client.get_json.return_value = {
            "Success": True,
            "Data": [{
                "labId": "lab_123", 
                "name": "Test Lab",
                "scriptId": "script_123",
                "scriptName": "Test Script",
                "accountId": "account_123",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE"
            }],
            "Error": ""
        }
        
        mock_async_client.post_json.return_value = {
            "Success": True,
            "Data": {
                "labId": "new_lab_456", 
                "name": "New Lab",
                "scriptId": "script_123",
                "scriptName": "Test Script",
                "accountId": "account_123",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "settings": {
                    "accountId": "account_123",
                    "marketTag": "BTC_USDT"
                },
                "config": {}
            },
            "Error": ""
        }
        
        # Create API instance
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Test get labs
        labs = await lab_api.get_labs()
        assert len(labs) == 1
        assert labs[0].lab_id == "lab_123"
        
        # Test create lab
        new_lab = await lab_api.create_lab(
            script_id="script_123",
            name="New Lab",
            account_id="account_123",
            market="BTC_USDT"
        )
        assert new_lab.lab_id == "new_lab_456"
        assert new_lab.name == "New Lab"
    
    @pytest.mark.asyncio
    async def test_bot_api_integration(self, mock_async_client, mock_auth_manager):
        """Test BotAPI integration with client and auth."""
        # Mock successful responses for get_all_bots
        mock_async_client.get_json.return_value = {
            "Success": True,
            "Data": [{
                "botId": "bot_123",
                "botName": "Test Bot",
                "scriptId": "script_123",
                "scriptName": "Test Script",
                "scriptVersion": 1,
                "accountId": "account_123",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "configuration": {
                    "leverage": 20.0,
                    "positionMode": 1,
                    "marginMode": 0,
                    "tradeAmount": 2000.0,
                    "interval": 15,
                    "chartStyle": 300,
                    "orderTemplate": 500
                }
            }],
            "Error": ""
        }
        
        # Mock successful response for create_bot
        mock_async_client.post_json.return_value = {
            "botId": "new_bot_456",
            "botName": "New Bot",
            "scriptId": "script_123",
            "scriptName": "Test Script",
            "scriptVersion": 1,
            "accountId": "account_123",
            "marketTag": "BTC_USDT",
            "status": "ACTIVE",
            "configuration": {
                "leverage": 20.0,
                "positionMode": 1,
                "marginMode": 0,
                "tradeAmount": 2000.0,
                "interval": 15,
                "chartStyle": 300,
                "orderTemplate": 500
            }
        }
        
        # Create API instance
        bot_api = BotAPI(mock_async_client, mock_auth_manager)
        
        # Test get all bots
        bots = await bot_api.get_all_bots()
        assert len(bots) == 1
        assert bots[0].bot_id == "bot_123"
        
        # Test create bot
        new_bot = await bot_api.create_bot(
            bot_name="New Bot",
            script_id="script_123",
            script_type="HaasScript",
            account_id="account_123",
            market="BTC_USDT"
        )
        assert new_bot.bot_id == "new_bot_456"
        assert new_bot.bot_name == "New Bot"
    
    @pytest.mark.asyncio
    async def test_authentication_flow_integration(self, mock_async_client):
        """Test complete authentication flow integration."""
        # Mock authentication responses
        mock_async_client.get_json.return_value = {
            "Success": True,
            "Data": {
                "UserId": "user_456",
                "InterfaceKey": "auth_token_123"
            },
            "Error": "",
            "R": 0  # No one-time code required
        }
        
        # Create mock config
        from pyHaasAPI.config.api_config import APIConfig
        config = APIConfig(
            email="test@example.com",
            password="test_password"
        )
        
        # Create auth manager
        auth_manager = AuthenticationManager(mock_async_client, config)
        
        # Test authentication
        session = await auth_manager.authenticate()
        assert session.user_id == "user_456"
        assert session.interface_key == "auth_token_123"
        assert auth_manager.is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, mock_async_client, mock_auth_manager):
        """Test error handling across API integration."""
        # Mock error response
        mock_async_client.get.return_value = {
            "error": "Not found",
            "status_code": 404
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Test error handling
        with pytest.raises(Exception):  # Should raise appropriate exception
            await lab_api.get_lab_details("nonexistent_lab")
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, mock_async_client, mock_auth_manager):
        """Test concurrent API calls integration."""
        import asyncio
        
        # Mock successful responses
        mock_async_client.get_json.return_value = {
            "Success": True,
            "Data": {
                "labId": "lab_123",
                "name": "Test Lab",
                "scriptId": "script_123",
                "scriptName": "Test Script",
                "accountId": "account_123",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "settings": {
                    "accountId": "account_123",
                    "marketTag": "BTC_USDT"
                },
                "config": {}
            },
            "Error": ""
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Run multiple concurrent calls
        tasks = [
            lab_api.get_lab_details("lab_123"),
            lab_api.get_lab_details("lab_456"),
            lab_api.get_lab_details("lab_789")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All calls should succeed
        assert len(results) == 3
        assert all(result.lab_id == "lab_123" for result in results)
    
    @pytest.mark.asyncio
    async def test_data_flow_integration(self, mock_async_client, mock_auth_manager):
        """Test complete data flow integration."""
        # Mock lab creation response
        mock_async_client.post.return_value = {
            "data": {"lab_id": "new_lab_123", "name": "New Lab"},
            "status_code": 201
        }
        
        # Mock lab execution response
        mock_async_client.post.return_value = {
            "data": {"job_id": "job_456", "status": "started"},
            "status_code": 200
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Create lab
        lab = await lab_api.create_lab(
            script_id="script_123",
            name="New Lab",
            account_id="account_123",
            market="BTC_USDT"
        )
        assert lab["lab_id"] == "new_lab_123"
        
        # Start lab execution
        job = await lab_api.start_lab_execution("new_lab_123")
        assert job["job_id"] == "job_456"
        assert job["status"] == "started"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, mock_async_client, mock_auth_manager):
        """Test rate limiting integration."""
        import asyncio
        
        # Mock rate limit response
        mock_async_client.get.return_value = {
            "error": "Rate limit exceeded",
            "status_code": 429,
            "retry_after": 60
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Test rate limiting
        with pytest.raises(Exception):  # Should handle rate limiting
            await lab_api.get_labs()
    
    @pytest.mark.asyncio
    async def test_timeout_handling_integration(self, mock_async_client, mock_auth_manager):
        """Test timeout handling integration."""
        import asyncio
        
        # Mock timeout
        mock_async_client.get.side_effect = asyncio.TimeoutError("Request timeout")
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Test timeout handling
        with pytest.raises(asyncio.TimeoutError):
            await lab_api.get_labs()
    
    @pytest.mark.asyncio
    async def test_retry_logic_integration(self, mock_async_client, mock_auth_manager):
        """Test retry logic integration."""
        from aiohttp import ClientError
        
        # Mock first call fails, second succeeds
        mock_async_client.get.side_effect = [
            ClientError("Connection failed"),
            {"data": [{"lab_id": "lab_123"}], "status_code": 200}
        ]
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Test retry logic
        labs = await lab_api.get_labs()
        assert len(labs) == 1
        assert labs[0]["lab_id"] == "lab_123"
        assert mock_async_client.get.call_count == 2


