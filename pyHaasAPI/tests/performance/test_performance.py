"""
Performance tests for pyHaasAPI components.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI


class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_client_performance(self, mock_async_client):
        """Test AsyncHaasClient performance."""
        # Mock fast response
        mock_async_client.get.return_value = {
            "data": {"test": "value"},
            "status_code": 200
        }
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        # Measure execution time
        start_time = time.time()
        result = await client.get("/test/endpoint")
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert performance threshold (should be very fast with mocked client)
        assert execution_time < 0.1  # 100ms threshold
        assert result["status_code"] == 200
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, mock_async_client):
        """Test performance with concurrent requests."""
        # Mock fast responses
        mock_async_client.get.return_value = {
            "data": {"test": "value"},
            "status_code": 200
        }
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        # Measure concurrent execution time
        start_time = time.time()
        
        # Run 10 concurrent requests
        tasks = [client.get(f"/test/endpoint/{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 0.5  # 500ms threshold for 10 concurrent requests
        assert len(results) == 10
        assert all(result["status_code"] == 200 for result in results)
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_authentication_performance(self, mock_async_client):
        """Test authentication performance."""
        # Mock fast authentication response
        mock_async_client.post.return_value = {
            "data": {"token": "mock_token", "success": True},
            "status_code": 200
        }
        
        auth_manager = AuthenticationManager(
            email="test@example.com",
            password="test_password"
        )
        auth_manager._client = mock_async_client
        
        # Measure authentication time
        start_time = time.time()
        result = await auth_manager.authenticate()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 0.2  # 200ms threshold
        assert result is True
        assert auth_manager.is_authenticated is True
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_lab_api_performance(self, mock_async_client, mock_auth_manager):
        """Test LabAPI performance."""
        # Mock fast responses
        mock_async_client.get.return_value = {
            "data": [{"lab_id": f"lab_{i}", "name": f"Lab {i}"} for i in range(100)],
            "status_code": 200
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Measure large dataset retrieval time
        start_time = time.time()
        labs = await lab_api.get_labs()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 0.3  # 300ms threshold for 100 labs
        assert len(labs) == 100
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_bot_api_performance(self, mock_async_client, mock_auth_manager):
        """Test BotAPI performance."""
        # Mock fast responses
        mock_async_client.get.return_value = {
            "data": [{"bot_id": f"bot_{i}", "name": f"Bot {i}"} for i in range(50)],
            "status_code": 200
        }
        
        bot_api = BotAPI(mock_async_client, mock_auth_manager)
        
        # Measure bot retrieval time
        start_time = time.time()
        bots = await bot_api.get_bots()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 0.2  # 200ms threshold for 50 bots
        assert len(bots) == 50
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, mock_async_client, mock_auth_manager):
        """Test memory usage performance."""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Mock large dataset response
        large_data = [{"id": i, "data": f"item_{i}"} for i in range(1000)]
        mock_async_client.get.return_value = {
            "data": large_data,
            "status_code": 200
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Process large dataset
        start_time = time.time()
        result = await lab_api.get_labs()
        end_time = time.time()
        
        # Check memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        execution_time = end_time - start_time
        
        # Assert performance thresholds
        assert execution_time < 0.5  # 500ms threshold
        assert memory_increase < 10 * 1024 * 1024  # Less than 10MB increase
        assert len(result) == 1000
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_connection_pool_performance(self, mock_async_client):
        """Test connection pool performance."""
        # Mock fast responses
        mock_async_client.get.return_value = {
            "data": {"test": "value"},
            "status_code": 200
        }
        
        client = AsyncHaasClient(host="127.0.0.1", port=8090)
        client._client = mock_async_client
        
        # Measure multiple requests with connection reuse
        start_time = time.time()
        
        # Make 20 sequential requests
        for i in range(20):
            await client.get(f"/test/endpoint/{i}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 1.0  # 1 second threshold for 20 requests
        assert mock_async_client.get.call_count == 20
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_error_handling_performance(self, mock_async_client, mock_auth_manager):
        """Test error handling performance."""
        # Mock error response
        mock_async_client.get.return_value = {
            "error": "Not found",
            "status_code": 404
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Measure error handling time
        start_time = time.time()
        
        try:
            await lab_api.get_lab_details("nonexistent_lab")
        except Exception:
            pass  # Expected to raise exception
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 0.1  # 100ms threshold for error handling
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_retry_performance(self, mock_async_client, mock_auth_manager):
        """Test retry mechanism performance."""
        from aiohttp import ClientError
        
        # Mock first call fails, second succeeds
        mock_async_client.get.side_effect = [
            ClientError("Connection failed"),
            {"data": [{"lab_id": "lab_123"}], "status_code": 200}
        ]
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Measure retry time
        start_time = time.time()
        result = await lab_api.get_labs()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 0.5  # 500ms threshold for retry
        assert len(result) == 1
        assert result[0]["lab_id"] == "lab_123"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_operations_performance(self, mock_async_client, mock_auth_manager):
        """Test batch operations performance."""
        # Mock fast responses for batch operations
        mock_async_client.post.return_value = {
            "data": {"success": True},
            "status_code": 200
        }
        
        lab_api = LabAPI(mock_async_client, mock_auth_manager)
        
        # Measure batch operation time
        start_time = time.time()
        
        # Simulate batch operations
        tasks = []
        for i in range(10):
            task = lab_api.create_lab(
                script_id=f"script_{i}",
                name=f"Lab {i}",
                account_id="account_123",
                market="BTC_USDT"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert performance threshold
        assert execution_time < 1.0  # 1 second threshold for 10 batch operations
        assert len(results) == 10
        assert all(result["success"] is True for result in results)


