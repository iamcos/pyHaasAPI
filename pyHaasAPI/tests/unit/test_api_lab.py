"""
Unit tests for LabAPI functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.models.lab import LabDetails, LabRecord, LabConfig, LabSettings, StartLabExecutionRequest, LabExecutionUpdate
from pyHaasAPI.exceptions import LabError, LabNotFoundError, LabExecutionError


class TestLabAPI:
    """Test LabAPI functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock AsyncHaasClient."""
        return AsyncMock(spec=AsyncHaasClient)
    
    @pytest.fixture
    def mock_auth_manager(self):
        """Create mock AuthenticationManager."""
        return AsyncMock(spec=AuthenticationManager)
    
    @pytest.fixture
    def lab_api(self, mock_client, mock_auth_manager):
        """Create LabAPI instance with mocked dependencies."""
        return LabAPI(mock_client, mock_auth_manager)
    
    @pytest.mark.asyncio
    async def test_lab_api_initialization(self, mock_client, mock_auth_manager):
        """Test LabAPI initialization."""
        lab_api = LabAPI(mock_client, mock_auth_manager)
        
        assert lab_api.client is mock_client
        assert lab_api.auth_manager is mock_auth_manager
        assert lab_api.logger is not None
    
    @pytest.mark.asyncio
    async def test_create_lab_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab creation."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
            "success": True,
            "data": {
                "labId": "lab123",
                "name": "Test Lab",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            }
        }
        
        mock_client.post.return_value = mock_response
        
        result = await lab_api.create_lab(
            script_id="script456",
            name="Test Lab",
            account_id="account789",
            market="BTC_USDT"
        )
        
        assert isinstance(result, LabDetails)
        assert result.lab_id == "lab123"
        assert result.name == "Test Lab"
        assert result.script_id == "script456"
        assert result.status == "ACTIVE"
        
        mock_client.post.assert_called_once()
        mock_auth_manager.get_headers.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_lab_failure(self, lab_api, mock_client, mock_auth_manager):
        """Test lab creation failure."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API error response
        mock_response = {
            "success": False,
            "error": "Script not found"
        }
        
        mock_client.post.return_value = mock_response
        
        with pytest.raises(LabError):
            await lab_api.create_lab(
                script_id="invalid_script",
                name="Test Lab",
                account_id="account789",
                market="BTC_USDT"
            )
    
    @pytest.mark.asyncio
    async def test_get_lab_details_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab details retrieval."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
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
        
        mock_client.get.return_value = mock_response
        
        result = await lab_api.get_lab_details("lab123")
        
        assert isinstance(result, LabDetails)
        assert result.lab_id == "lab123"
        assert result.name == "Test Lab"
        assert result.settings is not None
        assert result.config is not None
        
        mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_lab_details_not_found(self, lab_api, mock_client, mock_auth_manager):
        """Test lab details retrieval when lab not found."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API error response
        mock_response = {
            "success": False,
            "error": "Lab not found"
        }
        
        mock_client.get.return_value = mock_response
        
        with pytest.raises(LabNotFoundError):
            await lab_api.get_lab_details("nonexistent_lab")
    
    @pytest.mark.asyncio
    async def test_get_labs_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful labs listing."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
            "success": True,
            "data": {
                "items": [
                    {
                        "labId": "lab123",
                        "name": "Test Lab 1",
                        "scriptId": "script456",
                        "scriptName": "Test Script",
                        "accountId": "account789",
                        "marketTag": "BTC_USDT",
                        "status": "ACTIVE",
                        "createdAt": datetime.now().isoformat(),
                        "backtestCount": 5
                    },
                    {
                        "labId": "lab456",
                        "name": "Test Lab 2",
                        "scriptId": "script789",
                        "scriptName": "Another Script",
                        "accountId": "account012",
                        "marketTag": "ETH_USDT",
                        "status": "COMPLETED",
                        "createdAt": datetime.now().isoformat(),
                        "backtestCount": 10
                    }
                ],
                "totalCount": 2,
                "page": 1,
                "pageSize": 10,
                "totalPages": 1,
                "hasNext": False,
                "hasPrevious": False
            }
        }
        
        mock_client.get.return_value = mock_response
        
        result = await lab_api.get_labs()
        
        assert len(result.items) == 2
        assert result.total_count == 2
        assert result.page == 1
        assert result.total_pages == 1
        assert not result.has_next
        assert not result.has_previous
        
        # Check first lab
        lab1 = result.items[0]
        assert lab1.lab_id == "lab123"
        assert lab1.name == "Test Lab 1"
        assert lab1.status == "ACTIVE"
        assert lab1.backtest_count == 5
        
        # Check second lab
        lab2 = result.items[1]
        assert lab2.lab_id == "lab456"
        assert lab2.name == "Test Lab 2"
        assert lab2.status == "COMPLETED"
        assert lab2.backtest_count == 10
    
    @pytest.mark.asyncio
    async def test_update_lab_details_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab details update."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
            "success": True,
            "data": {
                "labId": "lab123",
                "name": "Updated Lab",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "updatedAt": datetime.now().isoformat()
            }
        }
        
        mock_client.put.return_value = mock_response
        
        # Create lab details for update
        lab_details = LabDetails(
            lab_id="lab123",
            name="Updated Lab",
            script_id="script456",
            script_name="Test Script",
            settings=LabSettings(account_id="account789", market_tag="BTC_USDT"),
            config=LabConfig(),
            status="ACTIVE",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await lab_api.update_lab_details("lab123", lab_details)
        
        assert isinstance(result, LabDetails)
        assert result.name == "Updated Lab"
        
        mock_client.put.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_lab_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab deletion."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
            "success": True,
            "message": "Lab deleted successfully"
        }
        
        mock_client.delete.return_value = mock_response
        
        result = await lab_api.delete_lab("lab123")
        
        assert result["success"] is True
        assert result["message"] == "Lab deleted successfully"
        
        mock_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_lab_execution_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab execution start."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
            "success": True,
            "data": {
                "jobId": "job123",
                "status": "STARTED",
                "message": "Lab execution started"
            }
        }
        
        mock_client.post.return_value = mock_response
        
        # Create execution request
        request = StartLabExecutionRequest(
            lab_id="lab123",
            start_unix=int(datetime.now().timestamp()),
            end_unix=int(datetime.now().timestamp()) + 86400,  # 24 hours later
            send_email=False
        )
        
        result = await lab_api.start_lab_execution(request)
        
        assert result["success"] is True
        assert result["data"]["jobId"] == "job123"
        assert result["data"]["status"] == "STARTED"
        
        mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_lab_execution_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab execution cancellation."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
            "success": True,
            "message": "Lab execution cancelled"
        }
        
        mock_client.post.return_value = mock_response
        
        result = await lab_api.cancel_lab_execution("lab123")
        
        assert result["success"] is True
        assert result["message"] == "Lab execution cancelled"
        
        mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_lab_execution_update_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab execution status update."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
            "success": True,
            "data": {
                "labId": "lab123",
                "status": "RUNNING",
                "progress": 50,
                "currentGeneration": 1,
                "totalGenerations": 10,
                "currentEpoch": 1,
                "totalEpochs": 3,
                "completedBacktests": 5,
                "totalBacktests": 50
            }
        }
        
        mock_client.get.return_value = mock_response
        
        result = await lab_api.get_lab_execution_update("lab123")
        
        assert isinstance(result, LabExecutionUpdate)
        assert result.lab_id == "lab123"
        assert result.status == "RUNNING"
        assert result.progress == 50
        assert result.current_generation == 1
        assert result.total_generations == 10
        assert result.completed_backtests == 5
        assert result.total_backtests == 50
        
        mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clone_lab_success(self, lab_api, mock_client, mock_auth_manager):
        """Test successful lab cloning."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock API response
        mock_response = {
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
        
        mock_client.post.return_value = mock_response
        
        result = await lab_api.clone_lab("lab123", "Cloned Lab")
        
        assert isinstance(result, LabDetails)
        assert result.lab_id == "lab456"
        assert result.name == "Cloned Lab"
        assert result.status == "ACTIVE"
        
        mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lab_api_error_handling(self, lab_api, mock_client, mock_auth_manager):
        """Test error handling in LabAPI."""
        # Mock authentication failure
        mock_auth_manager.get_headers.side_effect = Exception("Authentication failed")
        
        with pytest.raises(Exception):
            await lab_api.get_lab_details("lab123")
    
    @pytest.mark.asyncio
    async def test_lab_api_network_error(self, lab_api, mock_client, mock_auth_manager):
        """Test network error handling."""
        # Mock authentication
        mock_auth_manager.get_headers.return_value = {"Authorization": "Bearer token123"}
        
        # Mock network error
        mock_client.get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            await lab_api.get_lab_details("lab123")


