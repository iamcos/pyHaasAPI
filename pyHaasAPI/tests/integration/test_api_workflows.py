"""
Integration tests for complete API workflows.
Tests the full API functionality from authentication to bot management.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.models.lab import LabDetails, LabSettings, LabConfig, StartLabExecutionRequest
from pyHaasAPI.models.bot import BotDetails, BotConfiguration
from pyHaasAPI.models.common import ApiResponse, PaginatedResponse


class TestCompleteLabWorkflow:
    """Test complete lab management workflow."""
    
    @pytest.fixture
    async def mock_client(self):
        """Create mock AsyncHaasClient."""
        client = AsyncMock(spec=AsyncHaasClient)
        return client
    
    @pytest.fixture
    async def mock_auth_manager(self):
        """Create mock AuthenticationManager."""
        auth = AsyncMock(spec=AuthenticationManager)
        auth.get_headers.return_value = {"Authorization": "Bearer token123"}
        return auth
    
    @pytest.fixture
    async def lab_api(self, mock_client, mock_auth_manager):
        """Create LabAPI instance."""
        return LabAPI(mock_client, mock_auth_manager)
    
    @pytest.fixture
    async def bot_api(self, mock_client, mock_auth_manager):
        """Create BotAPI instance."""
        return BotAPI(mock_client, mock_auth_manager)
    
    @pytest.mark.asyncio
    async def test_complete_lab_lifecycle(self, lab_api, mock_client, mock_auth_manager):
        """Test complete lab lifecycle from creation to execution."""
        # Step 1: Create lab
        create_response = {
            "success": True,
            "data": {
                "labId": "lab123",
                "name": "Test Lab",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "createdAt": datetime.now().isoformat()
            }
        }
        mock_client.post.return_value = create_response
        
        lab = await lab_api.create_lab(
            script_id="script456",
            name="Test Lab",
            account_id="account789",
            market="BTC_USDT"
        )
        
        assert lab.lab_id == "lab123"
        assert lab.name == "Test Lab"
        assert lab.status == "ACTIVE"
        
        # Step 2: Get lab details
        details_response = {
            "success": True,
            "data": {
                "labId": "lab123",
                "name": "Test Lab",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "settings": {
                    "accountId": "account789",
                    "marketTag": "BTC_USDT",
                    "interval": 1,
                    "tradeAmount": 100.0,
                    "chartStyle": 300,
                    "orderTemplate": 500,
                    "leverage": 20.0,
                    "positionMode": 1,
                    "marginMode": 0
                },
                "config": {
                    "maxParallel": 10,
                    "maxGenerations": 30,
                    "maxEpochs": 3,
                    "maxRuntime": 0,
                    "autoRestart": 0
                },
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            }
        }
        mock_client.get.return_value = details_response
        
        lab_details = await lab_api.get_lab_details("lab123")
        
        assert lab_details.lab_id == "lab123"
        assert lab_details.settings is not None
        assert lab_details.config is not None
        
        # Step 3: Start lab execution
        execution_response = {
            "success": True,
            "data": {
                "jobId": "job123",
                "status": "STARTED",
                "message": "Lab execution started"
            }
        }
        mock_client.post.return_value = execution_response
        
        request = StartLabExecutionRequest(
            lab_id="lab123",
            start_unix=int(datetime.now().timestamp()),
            end_unix=int(datetime.now().timestamp()) + 86400,
            send_email=False
        )
        
        result = await lab_api.start_lab_execution(request)
        
        assert result["success"] is True
        assert result["data"]["jobId"] == "job123"
        assert result["data"]["status"] == "STARTED"
    
    @pytest.mark.asyncio
    async def test_lab_cloning_workflow(self, lab_api, mock_client, mock_auth_manager):
        """Test lab cloning workflow."""
        # Mock clone response
        clone_response = {
            "success": True,
            "data": {
                "labId": "lab456",
                "name": "Cloned Lab",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "createdAt": datetime.now().isoformat()
            }
        }
        mock_client.post.return_value = clone_response
        
        cloned_lab = await lab_api.clone_lab("lab123", "Cloned Lab")
        
        assert cloned_lab.lab_id == "lab456"
        assert cloned_lab.name == "Cloned Lab"
        assert cloned_lab.status == "ACTIVE"
    
    @pytest.mark.asyncio
    async def test_lab_deletion_workflow(self, lab_api, mock_client, mock_auth_manager):
        """Test lab deletion workflow."""
        # Mock deletion response
        delete_response = {
            "success": True,
            "message": "Lab deleted successfully"
        }
        mock_client.delete.return_value = delete_response
        
        result = await lab_api.delete_lab("lab123")
        
        assert result["success"] is True
        assert result["message"] == "Lab deleted successfully"


class TestCompleteBotWorkflow:
    """Test complete bot management workflow."""
    
    @pytest.fixture
    async def mock_client(self):
        """Create mock AsyncHaasClient."""
        client = AsyncMock(spec=AsyncHaasClient)
        return client
    
    @pytest.fixture
    async def mock_auth_manager(self):
        """Create mock AuthenticationManager."""
        auth = AsyncMock(spec=AuthenticationManager)
        auth.get_headers.return_value = {"Authorization": "Bearer token123"}
        return auth
    
    @pytest.fixture
    async def bot_api(self, mock_client, mock_auth_manager):
        """Create BotAPI instance."""
        return BotAPI(mock_client, mock_auth_manager)
    
    @pytest.mark.asyncio
    async def test_complete_bot_lifecycle(self, bot_api, mock_client, mock_auth_manager):
        """Test complete bot lifecycle from creation to activation."""
        # Step 1: Create bot
        create_response = {
            "success": True,
            "data": {
                "botId": "bot123",
                "botName": "Test Bot",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "INACTIVE",
                "createdAt": datetime.now().isoformat()
            }
        }
        mock_client.post.return_value = create_response
        
        bot = await bot_api.create_bot(
            script_id="script456",
            bot_name="Test Bot",
            account_id="account789",
            market="BTC_USDT"
        )
        
        assert bot.bot_id == "bot123"
        assert bot.bot_name == "Test Bot"
        assert bot.status == "INACTIVE"
        
        # Step 2: Get bot details
        details_response = {
            "success": True,
            "data": {
                "botId": "bot123",
                "botName": "Test Bot",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "scriptVersion": 1,
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "configuration": {
                    "leverage": 20.0,
                    "positionMode": 1,
                    "marginMode": 0,
                    "tradeAmount": 2000.0,
                    "interval": 1,
                    "chartStyle": 300,
                    "orderTemplate": 500
                },
                "status": "INACTIVE",
                "createdAt": datetime.now().isoformat()
            }
        }
        mock_client.get.return_value = details_response
        
        bot_details = await bot_api.get_bot_details("bot123")
        
        assert bot_details.bot_id == "bot123"
        assert bot_details.configuration is not None
        assert bot_details.configuration.leverage == 20.0
        
        # Step 3: Activate bot
        activation_response = {
            "success": True,
            "message": "Bot activated successfully"
        }
        mock_client.post.return_value = activation_response
        
        result = await bot_api.activate_bot("bot123")
        
        assert result["success"] is True
        assert result["message"] == "Bot activated successfully"
    
    @pytest.mark.asyncio
    async def test_bot_parameter_update_workflow(self, bot_api, mock_client, mock_auth_manager):
        """Test bot parameter update workflow."""
        # Mock parameter update response
        update_response = {
            "success": True,
            "message": "Bot parameters updated successfully"
        }
        mock_client.put.return_value = update_response
        
        result = await bot_api.update_bot_parameter(
            bot_id="bot123",
            parameter_name="leverage",
            value=25.0
        )
        
        assert result["success"] is True
        assert result["message"] == "Bot parameters updated successfully"
    
    @pytest.mark.asyncio
    async def test_bot_deactivation_workflow(self, bot_api, mock_client, mock_auth_manager):
        """Test bot deactivation workflow."""
        # Mock deactivation response
        deactivation_response = {
            "success": True,
            "message": "Bot deactivated successfully"
        }
        mock_client.post.return_value = deactivation_response
        
        result = await bot_api.deactivate_bot("bot123")
        
        assert result["success"] is True
        assert result["message"] == "Bot deactivated successfully"
    
    @pytest.mark.asyncio
    async def test_bot_deletion_workflow(self, bot_api, mock_client, mock_auth_manager):
        """Test bot deletion workflow."""
        # Mock deletion response
        delete_response = {
            "success": True,
            "message": "Bot deleted successfully"
        }
        mock_client.delete.return_value = delete_response
        
        result = await bot_api.delete_bot("bot123")
        
        assert result["success"] is True
        assert result["message"] == "Bot deleted successfully"


class TestAuthenticationWorkflow:
    """Test complete authentication workflow."""
    
    @pytest.fixture
    async def mock_client(self):
        """Create mock AsyncHaasClient."""
        client = AsyncMock(spec=AsyncHaasClient)
        return client
    
    @pytest.mark.asyncio
    async def test_complete_authentication_flow(self, mock_client):
        """Test complete authentication flow."""
        # Mock authentication responses
        auth_response = {
            "success": True,
            "data": {
                "userId": "user123",
                "interfaceKey": "key456"
            }
        }
        
        mock_client.post.return_value = auth_response
        
        # Create auth manager
        auth_manager = AuthenticationManager(
            client=mock_client,
            email="test@example.com",
            password="password123"
        )
        
        # Test login
        await auth_manager.login()
        
        assert auth_manager.is_authenticated() is True
        assert auth_manager.session is not None
        assert auth_manager.session.user_id == "user123"
        assert auth_manager.session.interface_key == "key456"
        
        # Test getting headers
        headers = await auth_manager.get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer key456"
        
        # Test logout
        await auth_manager.logout()
        assert auth_manager.is_authenticated() is False
        assert auth_manager.session is None


class TestErrorHandlingWorkflow:
    """Test error handling in API workflows."""
    
    @pytest.fixture
    async def mock_client(self):
        """Create mock AsyncHaasClient."""
        client = AsyncMock(spec=AsyncHaasClient)
        return client
    
    @pytest.fixture
    async def mock_auth_manager(self):
        """Create mock AuthenticationManager."""
        auth = AsyncMock(spec=AuthenticationManager)
        auth.get_headers.return_value = {"Authorization": "Bearer token123"}
        return auth
    
    @pytest.fixture
    async def lab_api(self, mock_client, mock_auth_manager):
        """Create LabAPI instance."""
        return LabAPI(mock_client, mock_auth_manager)
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, lab_api, mock_auth_manager):
        """Test authentication error handling."""
        # Mock authentication failure
        mock_auth_manager.get_headers.side_effect = Exception("Authentication failed")
        
        with pytest.raises(Exception, match="Authentication failed"):
            await lab_api.get_lab_details("lab123")
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, lab_api, mock_client, mock_auth_manager):
        """Test network error handling."""
        # Mock network error
        mock_client.get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Network error"):
            await lab_api.get_lab_details("lab123")
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, lab_api, mock_client, mock_auth_manager):
        """Test API error handling."""
        # Mock API error response
        error_response = {
            "success": False,
            "error": "Lab not found"
        }
        mock_client.get.return_value = error_response
        
        with pytest.raises(Exception):  # Should raise LabNotFoundError
            await lab_api.get_lab_details("nonexistent_lab")


class TestConcurrentOperations:
    """Test concurrent API operations."""
    
    @pytest.fixture
    async def mock_client(self):
        """Create mock AsyncHaasClient."""
        client = AsyncMock(spec=AsyncHaasClient)
        return client
    
    @pytest.fixture
    async def mock_auth_manager(self):
        """Create mock AuthenticationManager."""
        auth = AsyncMock(spec=AuthenticationManager)
        auth.get_headers.return_value = {"Authorization": "Bearer token123"}
        return auth
    
    @pytest.fixture
    async def lab_api(self, mock_client, mock_auth_manager):
        """Create LabAPI instance."""
        return LabAPI(mock_client, mock_auth_manager)
    
    @pytest.mark.asyncio
    async def test_concurrent_lab_operations(self, lab_api, mock_client, mock_auth_manager):
        """Test concurrent lab operations."""
        # Mock responses for multiple labs
        lab_responses = [
            {
                "success": True,
                "data": {
                    "labId": f"lab{i}",
                    "name": f"Test Lab {i}",
                    "scriptId": "script456",
                    "scriptName": "Test Script",
                    "accountId": "account789",
                    "marketTag": "BTC_USDT",
                    "status": "ACTIVE",
                    "createdAt": datetime.now().isoformat()
                }
            }
            for i in range(5)
        ]
        
        mock_client.get.side_effect = lab_responses
        
        # Create concurrent tasks
        tasks = [
            lab_api.get_lab_details(f"lab{i}")
            for i in range(5)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify results
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.lab_id == f"lab{i}"
            assert result.name == f"Test Lab {i}"
            assert result.status == "ACTIVE"
    
    @pytest.mark.asyncio
    async def test_concurrent_bot_operations(self, mock_client, mock_auth_manager):
        """Test concurrent bot operations."""
        from pyHaasAPI.api.bot.bot_api import BotAPI
        
        bot_api = BotAPI(mock_client, mock_auth_manager)
        
        # Mock responses for multiple bots
        bot_responses = [
            {
                "success": True,
                "data": {
                    "botId": f"bot{i}",
                    "botName": f"Test Bot {i}",
                    "scriptId": "script456",
                    "scriptName": "Test Script",
                    "accountId": "account789",
                    "marketTag": "BTC_USDT",
                    "status": "ACTIVE",
                    "createdAt": datetime.now().isoformat()
                }
            }
            for i in range(5)
        ]
        
        mock_client.get.side_effect = bot_responses
        
        # Create concurrent tasks
        tasks = [
            bot_api.get_bot_details(f"bot{i}")
            for i in range(5)
        ]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify results
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.bot_id == f"bot{i}"
            assert result.bot_name == f"Test Bot {i}"
            assert result.status == "ACTIVE"


