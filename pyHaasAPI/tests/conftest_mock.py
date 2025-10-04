"""
pytest configuration and fixtures for pyHaasAPI tests.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List
import os
from pathlib import Path

# Test data constants
MOCK_LAB_DATA = {
    "lab_id": "test_lab_123",
    "name": "Test Lab",
    "script_id": "test_script_456",
    "status": "completed",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T01:00:00Z"
}

MOCK_BOT_DATA = {
    "bot_id": "test_bot_789",
    "name": "Test Bot",
    "script_id": "test_script_456",
    "account_id": "test_account_123",
    "status": "active",
    "created_at": "2023-01-01T00:00:00Z"
}

MOCK_BACKTEST_DATA = {
    "backtest_id": "test_backtest_456",
    "lab_id": "test_lab_123",
    "generation_idx": 1,
    "population_idx": 1,
    "roi_percentage": 150.5,
    "win_rate": 0.65,
    "total_trades": 100,
    "max_drawdown": 0.15
}

MOCK_ACCOUNT_DATA = {
    "account_id": "test_account_123",
    "name": "Test Account",
    "balance": 10000.0,
    "currency": "USDT",
    "status": "active"
}

MOCK_SCRIPT_DATA = {
    "script_id": "test_script_456",
    "name": "Test Script",
    "description": "A test trading script",
    "version": "1.0.0",
    "status": "active"
}

MOCK_MARKET_DATA = {
    "market_tag": "BTC_USDT_PERPETUAL",
    "exchange": "binance",
    "base_currency": "BTC",
    "quote_currency": "USDT",
    "status": "active"
}

MOCK_ORDER_DATA = {
    "order_id": "test_order_123",
    "bot_id": "test_bot_789",
    "side": "buy",
    "order_type": "market",
    "quantity": 0.1,
    "price": 50000.0,
    "status": "filled"
}

# Custom pytest markers
pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "asyncio: Async tests")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add async marker for async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # Add unit marker for unit tests
        if "test_" in item.name and "integration" not in item.name:
            item.add_marker(pytest.mark.unit)

# Fixtures
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def mock_async_client():
    """Mock async HTTP client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def mock_auth_manager():
    """Mock authentication manager."""
    auth_manager = AsyncMock()
    auth_manager.authenticate = AsyncMock(return_value=True)
    auth_manager.is_authenticated = True
    auth_manager.get_token = MagicMock(return_value="mock_token")
    return auth_manager

@pytest.fixture
def mock_lab_api():
    """Mock lab API."""
    lab_api = AsyncMock()
    lab_api.get_labs = AsyncMock(return_value=[MOCK_LAB_DATA])
    lab_api.create_lab = AsyncMock(return_value=MOCK_LAB_DATA)
    lab_api.delete_lab = AsyncMock(return_value=True)
    lab_api.get_lab_details = AsyncMock(return_value=MOCK_LAB_DATA)
    lab_api.update_lab_details = AsyncMock(return_value=True)
    lab_api.start_lab_execution = AsyncMock(return_value=True)
    lab_api.cancel_lab_execution = AsyncMock(return_value=True)
    lab_api.get_lab_execution_update = AsyncMock(return_value={"status": "completed"})
    return lab_api

@pytest.fixture
def mock_bot_api():
    """Mock bot API."""
    bot_api = AsyncMock()
    bot_api.get_bots = AsyncMock(return_value=[MOCK_BOT_DATA])
    bot_api.create_bot = AsyncMock(return_value=MOCK_BOT_DATA)
    bot_api.delete_bot = AsyncMock(return_value=True)
    bot_api.get_bot_details = AsyncMock(return_value=MOCK_BOT_DATA)
    bot_api.update_bot_parameters = AsyncMock(return_value=True)
    bot_api.activate_bot = AsyncMock(return_value=True)
    bot_api.deactivate_bot = AsyncMock(return_value=True)
    return bot_api

@pytest.fixture
def mock_account_api():
    """Mock account API."""
    account_api = AsyncMock()
    account_api.get_accounts = AsyncMock(return_value=[MOCK_ACCOUNT_DATA])
    account_api.get_account_details = AsyncMock(return_value=MOCK_ACCOUNT_DATA)
    account_api.get_account_balance = AsyncMock(return_value={"balance": 10000.0})
    return account_api

@pytest.fixture
def mock_script_api():
    """Mock script API."""
    script_api = AsyncMock()
    script_api.get_scripts = AsyncMock(return_value=[MOCK_SCRIPT_DATA])
    script_api.get_script_details = AsyncMock(return_value=MOCK_SCRIPT_DATA)
    return script_api

@pytest.fixture
def mock_market_api():
    """Mock market API."""
    market_api = AsyncMock()
    market_api.get_markets = AsyncMock(return_value=[MOCK_MARKET_DATA])
    market_api.get_market_details = AsyncMock(return_value=MOCK_MARKET_DATA)
    market_api.get_price_data = AsyncMock(return_value={"price": 50000.0})
    return market_api

@pytest.fixture
def mock_backtest_api():
    """Mock backtest API."""
    backtest_api = AsyncMock()
    backtest_api.get_backtests = AsyncMock(return_value=[MOCK_BACKTEST_DATA])
    backtest_api.get_backtest_details = AsyncMock(return_value=MOCK_BACKTEST_DATA)
    backtest_api.execute_backtest = AsyncMock(return_value=MOCK_BACKTEST_DATA)
    return backtest_api

@pytest.fixture
def mock_order_api():
    """Mock order API."""
    order_api = AsyncMock()
    order_api.get_orders = AsyncMock(return_value=[MOCK_ORDER_DATA])
    order_api.create_order = AsyncMock(return_value=MOCK_ORDER_DATA)
    order_api.cancel_order = AsyncMock(return_value=True)
    return order_api

@pytest.fixture
def mock_async_client_wrapper():
    """Mock async client wrapper."""
    wrapper = AsyncMock()
    wrapper.client = mock_async_client()
    wrapper.auth_manager = mock_auth_manager()
    return wrapper

@pytest.fixture
def mock_lab_service():
    """Mock lab service."""
    service = AsyncMock()
    service.create_optimized_lab = AsyncMock(return_value=MOCK_LAB_DATA)
    service.run_parameter_optimization = AsyncMock(return_value={"best_params": {}})
    service.get_optimization_results = AsyncMock(return_value={"results": []})
    return service

@pytest.fixture
def mock_bot_service():
    """Mock bot service."""
    service = AsyncMock()
    service.create_bots_from_lab = AsyncMock(return_value=[MOCK_BOT_DATA])
    service.analyze_bot_performance = AsyncMock(return_value={"performance": {}})
    service.manage_bot_lifecycle = AsyncMock(return_value=True)
    return service

@pytest.fixture
def mock_analysis_service():
    """Mock analysis service."""
    service = AsyncMock()
    service.analyze_lab_comprehensive = AsyncMock(return_value={"analysis": {}})
    service.extract_best_parameters = AsyncMock(return_value={"params": {}})
    service.generate_analysis_report = AsyncMock(return_value={"report": {}})
    return service

@pytest.fixture
def mock_reporting_service():
    """Mock reporting service."""
    service = AsyncMock()
    service.generate_report = AsyncMock(return_value={"report": {}})
    service.export_report = AsyncMock(return_value="report.csv")
    return service

@pytest.fixture
def mock_data_dumper():
    """Mock data dumper."""
    dumper = AsyncMock()
    dumper.dump_data = AsyncMock(return_value=True)
    dumper.load_data = AsyncMock(return_value={})
    return dumper

@pytest.fixture
def mock_testing_manager():
    """Mock testing manager."""
    manager = AsyncMock()
    manager.run_tests = AsyncMock(return_value={"results": []})
    manager.generate_report = AsyncMock(return_value={"report": {}})
    return manager

class TestUtils:
    """Utility class for test helpers."""
    
    @staticmethod
    def create_mock_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
        """Create a mock API response."""
        return {
            "data": data,
            "status_code": status_code,
            "success": status_code < 400
        }
    
    @staticmethod
    def create_mock_error_response(error_message: str, error_code: int = 400) -> Dict[str, Any]:
        """Create a mock error response."""
        return {
            "error": error_message,
            "error_code": error_code,
            "success": False
        }
    
    @staticmethod
    def assert_valid_lab_data(data: Dict[str, Any]) -> None:
        """Assert that lab data has required fields."""
        required_fields = ["lab_id", "name", "script_id", "status"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    @staticmethod
    def assert_valid_bot_data(data: Dict[str, Any]) -> None:
        """Assert that bot data has required fields."""
        required_fields = ["bot_id", "name", "script_id", "account_id", "status"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    @staticmethod
    def assert_valid_backtest_data(data: Dict[str, Any]) -> None:
        """Assert that backtest data has required fields."""
        required_fields = ["backtest_id", "lab_id", "roi_percentage", "win_rate"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

class PerformanceTestUtils:
    """Utility class for performance testing."""
    
    @staticmethod
    async def measure_execution_time(func, *args, **kwargs):
        """Measure execution time of an async function."""
        import time
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    def assert_performance_threshold(execution_time: float, max_time: float):
        """Assert that execution time is within threshold."""
        assert execution_time <= max_time, f"Execution time {execution_time:.2f}s exceeds threshold {max_time}s"