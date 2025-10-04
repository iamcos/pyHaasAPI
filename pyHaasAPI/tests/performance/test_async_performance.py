"""
Performance tests for async operations and rate limiting.
Tests the performance characteristics of the pyHaasAPI library.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from pyHaasAPI.core.client import AsyncHaasClient, RateLimiter, RetryHandler
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.models.lab import LabDetails
from pyHaasAPI.models.bot import BotDetails
from pyHaasAPI.models.common import PaginatedResponse


class TestAsyncPerformance:
    """Test async operation performance."""
    
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
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, mock_client, mock_auth_manager):
        """Test performance of concurrent requests."""
        lab_api = LabAPI(mock_client, mock_auth_manager)
        
        # Mock response
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
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        mock_client.get.return_value = mock_response
        
        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        
        for concurrency in concurrency_levels:
            start_time = time.perf_counter()
            
            # Create tasks
            tasks = [
                lab_api.get_lab_details(f"lab{i}")
                for i in range(concurrency)
            ]
            
            # Execute concurrently
            results = await asyncio.gather(*tasks)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            print(f"\nConcurrency {concurrency}: {duration:.4f}s")
            
            # Verify results
            assert len(results) == concurrency
            for result in results:
                assert isinstance(result, LabDetails)
                assert result.lab_id == "lab123"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self):
        """Test rate limiting performance."""
        # Test different rate limits
        rate_limits = [
            (10, 1),   # 10 requests per second
            (50, 1),  # 50 requests per second
            (100, 1), # 100 requests per second
        ]
        
        for max_requests, time_window in rate_limits:
            limiter = RateLimiter(max_requests, time_window)
            
            start_time = time.perf_counter()
            
            # Make requests up to the limit
            for _ in range(max_requests):
                await limiter.acquire()
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            print(f"\nRate limit {max_requests}/{time_window}s: {duration:.4f}s")
            
            # Should complete quickly for the limit
            assert duration < 0.1  # Should be very fast
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_retry_handler_performance(self):
        """Test retry handler performance."""
        handler = RetryHandler(max_retries=3, base_delay=0.01, max_delay=0.1)
        
        start_time = time.perf_counter()
        
        # Test delay calculation performance
        for attempt in range(10):
            delay = handler._calculate_delay(attempt)
            assert delay >= 0.01
            assert delay <= 0.1
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        print(f"\nRetry handler delay calculation: {duration:.4f}s")
        
        # Should be very fast
        assert duration < 0.01
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_authentication_performance(self, mock_client):
        """Test authentication performance."""
        # Mock authentication response
        auth_response = {
            "success": True,
            "data": {
                "userId": "user123",
                "interfaceKey": "key456"
            }
        }
        
        mock_client.post.return_value = auth_response
        
        # Test multiple authentication cycles
        num_cycles = 10
        start_time = time.perf_counter()
        
        for _ in range(num_cycles):
            auth_manager = AuthenticationManager(
                client=mock_client,
                email="test@example.com",
                password="password123"
            )
            
            await auth_manager.login()
            await auth_manager.logout()
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        print(f"\nAuthentication cycles ({num_cycles}): {duration:.4f}s")
        
        # Should be reasonably fast
        assert duration < 1.0  # Should complete within 1 second
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_lab_api_performance(self, mock_client, mock_auth_manager):
        """Test LabAPI performance."""
        lab_api = LabAPI(mock_client, mock_auth_manager)
        
        # Mock responses
        lab_response = {
            "success": True,
            "data": {
                "labId": "lab123",
                "name": "Test Lab",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        labs_response = {
            "success": True,
            "data": {
                "items": [
                    {
                        "labId": f"lab{i}",
                        "name": f"Test Lab {i}",
                        "scriptId": "script456",
                        "scriptName": "Test Script",
                        "accountId": "account789",
                        "marketTag": "BTC_USDT",
                        "status": "ACTIVE",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "backtestCount": 5
                    }
                    for i in range(100)
                ],
                "totalCount": 100,
                "page": 1,
                "pageSize": 100,
                "totalPages": 1,
                "hasNext": False,
                "hasPrevious": False
            }
        }
        
        mock_client.get.side_effect = [lab_response, labs_response]
        
        # Test individual lab retrieval
        start_time = time.perf_counter()
        lab = await lab_api.get_lab_details("lab123")
        end_time = time.perf_counter()
        
        individual_duration = end_time - start_time
        print(f"\nIndividual lab retrieval: {individual_duration:.4f}s")
        
        # Test labs listing
        start_time = time.perf_counter()
        labs = await lab_api.get_labs()
        end_time = time.perf_counter()
        
        listing_duration = end_time - start_time
        print(f"\nLabs listing (100 items): {listing_duration:.4f}s")
        
        # Verify results
        assert isinstance(lab, LabDetails)
        assert lab.lab_id == "lab123"
        
        assert isinstance(labs, PaginatedResponse)
        assert len(labs.items) == 100
        assert labs.total_count == 100
        
        # Performance assertions
        assert individual_duration < 0.1  # Should be very fast
        assert listing_duration < 0.5  # Should be reasonably fast
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_bot_api_performance(self, mock_client, mock_auth_manager):
        """Test BotAPI performance."""
        bot_api = BotAPI(mock_client, mock_auth_manager)
        
        # Mock responses
        bot_response = {
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
                "status": "ACTIVE",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        bots_response = {
            "success": True,
            "data": {
                "items": [
                    {
                        "botId": f"bot{i}",
                        "botName": f"Test Bot {i}",
                        "scriptId": "script456",
                        "scriptName": "Test Script",
                        "accountId": "account789",
                        "marketTag": "BTC_USDT",
                        "status": "ACTIVE",
                        "createdAt": "2024-01-01T00:00:00Z"
                    }
                    for i in range(50)
                ],
                "totalCount": 50,
                "page": 1,
                "pageSize": 50,
                "totalPages": 1,
                "hasNext": False,
                "hasPrevious": False
            }
        }
        
        mock_client.get.side_effect = [bot_response, bots_response]
        
        # Test individual bot retrieval
        start_time = time.perf_counter()
        bot = await bot_api.get_bot_details("bot123")
        end_time = time.perf_counter()
        
        individual_duration = end_time - start_time
        print(f"\nIndividual bot retrieval: {individual_duration:.4f}s")
        
        # Test bots listing
        start_time = time.perf_counter()
        bots = await bot_api.get_bots()
        end_time = time.perf_counter()
        
        listing_duration = end_time - start_time
        print(f"\nBots listing (50 items): {listing_duration:.4f}s")
        
        # Verify results
        assert isinstance(bot, BotDetails)
        assert bot.bot_id == "bot123"
        
        assert isinstance(bots, PaginatedResponse)
        assert len(bots.items) == 50
        assert bots.total_count == 50
        
        # Performance assertions
        assert individual_duration < 0.1  # Should be very fast
        assert listing_duration < 0.3  # Should be reasonably fast
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_mixed_operations_performance(self, mock_client, mock_auth_manager):
        """Test performance of mixed API operations."""
        lab_api = LabAPI(mock_client, mock_auth_manager)
        bot_api = BotAPI(mock_client, mock_auth_manager)
        
        # Mock responses
        lab_response = {
            "success": True,
            "data": {
                "labId": "lab123",
                "name": "Test Lab",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        bot_response = {
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
                "status": "ACTIVE",
                "createdAt": "2024-01-01T00:00:00Z"
            }
        }
        
        mock_client.get.side_effect = [lab_response, bot_response]
        
        # Test mixed operations
        start_time = time.perf_counter()
        
        # Execute mixed operations concurrently
        tasks = [
            lab_api.get_lab_details("lab123"),
            bot_api.get_bot_details("bot123"),
            lab_api.get_lab_details("lab456"),
            bot_api.get_bot_details("bot456"),
        ]
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        print(f"\nMixed operations (4 concurrent): {duration:.4f}s")
        
        # Verify results
        assert len(results) == 4
        assert isinstance(results[0], LabDetails)
        assert isinstance(results[1], BotDetails)
        assert isinstance(results[2], LabDetails)
        assert isinstance(results[3], BotDetails)
        
        # Performance assertion
        assert duration < 0.2  # Should be reasonably fast


class TestMemoryPerformance:
    """Test memory usage performance."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        # Create large dataset
        large_dataset = [
            {
                "labId": f"lab{i}",
                "name": f"Test Lab {i}",
                "scriptId": "script456",
                "scriptName": "Test Script",
                "accountId": "account789",
                "marketTag": "BTC_USDT",
                "status": "ACTIVE",
                "createdAt": "2024-01-01T00:00:00Z",
                "backtestCount": 5
            }
            for i in range(1000)
        ]
        
        start_time = time.perf_counter()
        
        # Process large dataset
        processed_data = []
        for item in large_dataset:
            processed_data.append({
                "id": item["labId"],
                "name": item["name"],
                "status": item["status"]
            })
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        print(f"\nLarge dataset processing (1000 items): {duration:.4f}s")
        
        # Verify results
        assert len(processed_data) == 1000
        assert processed_data[0]["id"] == "lab0"
        assert processed_data[999]["id"] == "lab999"
        
        # Performance assertion
        assert duration < 0.1  # Should be very fast
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_efficient_processing(self):
        """Test memory-efficient processing."""
        # Test generator-based processing
        def data_generator(size):
            for i in range(size):
                yield {
                    "id": f"item{i}",
                    "data": f"data{i}",
                    "timestamp": time.time()
                }
        
        start_time = time.perf_counter()
        
        # Process data efficiently
        processed_count = 0
        for item in data_generator(1000):
            processed_count += 1
            # Simulate processing
            _ = item["id"] + item["data"]
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        print(f"\nMemory-efficient processing (1000 items): {duration:.4f}s")
        
        # Verify results
        assert processed_count == 1000
        
        # Performance assertion
        assert duration < 0.1  # Should be very fast

