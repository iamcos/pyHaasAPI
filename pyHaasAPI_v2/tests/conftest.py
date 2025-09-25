"""
Test configuration for pyHaasAPI v2

This module provides pytest configuration, fixtures, and test utilities
for comprehensive testing of all pyHaasAPI v2 components.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import json

# Test configuration
TEST_CONFIG = {
    "host": "127.0.0.1",
    "port": 8090,
    "timeout": 5.0,
    "max_retries": 1,
    "retry_delay": 0.1,
    "verify_ssl": False,
    "enable_caching": False,
    "cache_ttl": 60.0,
    "enable_rate_limiting": False,
    "max_concurrent_requests": 5,
    "log_level": "WARNING",
    "strict_mode": False
}

# Mock data
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
    "status": "active",
    "account_id": "test_account_101",
    "market_tag": "BTC_USDT_PERPETUAL",
    "created_at": "2023-01-01T00:00:00Z"
}

MOCK_BACKTEST_DATA = {
    "backtest_id": "test_backtest_202",
    "lab_id": "test_lab_123",
    "roi_percentage": 150.5,
    "win_rate": 0.65,
    "total_trades": 100,
    "realized_profits_usdt": 1500.0,
    "max_drawdown": 0.1,
    "sharpe_ratio": 1.5
}

MOCK_ACCOUNT_DATA = {
    "account_id": "test_account_101",
    "name": "Test Account",
    "balance": 10000.0,
    "leverage": 20,
    "margin_mode": "cross",
    "position_mode": "hedge"
}

MOCK_SCRIPT_DATA = {
    "script_id": "test_script_456",
    "name": "Test Script",
    "description": "A test script",
    "source_code": "print('Hello, World!')",
    "language": "python"
}

MOCK_MARKET_DATA = {
    "market_tag": "BTC_USDT_PERPETUAL",
    "base_asset": "BTC",
    "quote_asset": "USDT",
    "price": 50000.0,
    "volume": 1000.0,
    "bid": 49999.0,
    "ask": 50001.0
}

MOCK_ORDER_DATA = {
    "order_id": "test_order_303",
    "bot_id": "test_bot_789",
    "side": "buy",
    "amount": 1000.0,
    "price": 50000.0,
    "status": "filled",
    "created_at": "2023-01-01T00:00:00Z"
}


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "async: mark test as async"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add async marker for async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.async)
        
        # Add unit marker for unit tests
        if "test_" in item.name and "integration" not in item.name:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker for integration tests
        if "integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker for performance tests
        if "performance" in item.name:
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker for slow tests
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return TEST_CONFIG.copy()


@pytest.fixture
def mock_async_client():
    """Mock async client for testing"""
    client = AsyncMock()
    client.execute = AsyncMock(return_value={"success": True})
    client.get = AsyncMock(return_value={"data": []})
    client.post = AsyncMock(return_value={"success": True})
    client.put = AsyncMock(return_value={"success": True})
    client.delete = AsyncMock(return_value={"success": True})
    return client


@pytest.fixture
def mock_auth_manager():
    """Mock authentication manager for testing"""
    auth_manager = AsyncMock()
    auth_manager.authenticate = AsyncMock(return_value=True)
    auth_manager.refresh_token = AsyncMock(return_value=True)
    auth_manager.logout = AsyncMock(return_value=None)
    auth_manager.is_authenticated = MagicMock(return_value=True)
    return auth_manager


@pytest.fixture
def mock_lab_api():
    """Mock lab API for testing"""
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
    """Mock bot API for testing"""
    bot_api = AsyncMock()
    bot_api.get_all_bots = AsyncMock(return_value=[MOCK_BOT_DATA])
    bot_api.create_bot = AsyncMock(return_value=MOCK_BOT_DATA)
    bot_api.delete_bot = AsyncMock(return_value=True)
    bot_api.get_bot_details = AsyncMock(return_value=MOCK_BOT_DATA)
    bot_api.activate_bot = AsyncMock(return_value=True)
    bot_api.deactivate_bot = AsyncMock(return_value=True)
    bot_api.pause_bot = AsyncMock(return_value=True)
    bot_api.resume_bot = AsyncMock(return_value=True)
    bot_api.edit_bot_parameter = AsyncMock(return_value=True)
    return bot_api


@pytest.fixture
def mock_account_api():
    """Mock account API for testing"""
    account_api = AsyncMock()
    account_api.get_accounts = AsyncMock(return_value=[MOCK_ACCOUNT_DATA])
    account_api.get_account_data = AsyncMock(return_value=MOCK_ACCOUNT_DATA)
    account_api.get_account_balance = AsyncMock(return_value=10000.0)
    account_api.get_all_account_balances = AsyncMock(return_value=[MOCK_ACCOUNT_DATA])
    account_api.get_margin_settings = AsyncMock(return_value={"leverage": 20})
    account_api.adjust_margin_settings = AsyncMock(return_value=True)
    account_api.set_position_mode = AsyncMock(return_value=True)
    account_api.set_margin_mode = AsyncMock(return_value=True)
    account_api.set_leverage = AsyncMock(return_value=True)
    return account_api


@pytest.fixture
def mock_script_api():
    """Mock script API for testing"""
    script_api = AsyncMock()
    script_api.get_all_scripts = AsyncMock(return_value=[MOCK_SCRIPT_DATA])
    script_api.get_script_record = AsyncMock(return_value=MOCK_SCRIPT_DATA)
    script_api.get_script_item = AsyncMock(return_value=MOCK_SCRIPT_DATA)
    script_api.get_scripts_by_name = AsyncMock(return_value=[MOCK_SCRIPT_DATA])
    script_api.add_script = AsyncMock(return_value=MOCK_SCRIPT_DATA)
    script_api.edit_script = AsyncMock(return_value=True)
    script_api.delete_script = AsyncMock(return_value=True)
    script_api.publish_script = AsyncMock(return_value=True)
    return script_api


@pytest.fixture
def mock_market_api():
    """Mock market API for testing"""
    market_api = AsyncMock()
    market_api.get_trade_markets = AsyncMock(return_value=[MOCK_MARKET_DATA])
    market_api.get_price_data = AsyncMock(return_value=MOCK_MARKET_DATA)
    market_api.get_historical_data = AsyncMock(return_value=[MOCK_MARKET_DATA])
    market_api.get_all_markets = AsyncMock(return_value=[MOCK_MARKET_DATA])
    market_api.validate_market = AsyncMock(return_value=True)
    return market_api


@pytest.fixture
def mock_backtest_api():
    """Mock backtest API for testing"""
    backtest_api = AsyncMock()
    backtest_api.get_backtest_result = AsyncMock(return_value=[MOCK_BACKTEST_DATA])
    backtest_api.get_backtest_runtime = AsyncMock(return_value=MOCK_BACKTEST_DATA)
    backtest_api.get_full_backtest_runtime_data = AsyncMock(return_value=MOCK_BACKTEST_DATA)
    backtest_api.get_backtest_chart = AsyncMock(return_value={"chart_data": []})
    backtest_api.get_backtest_log = AsyncMock(return_value={"log_data": []})
    backtest_api.execute_backtest = AsyncMock(return_value=True)
    backtest_api.get_backtest_history = AsyncMock(return_value=[MOCK_BACKTEST_DATA])
    return backtest_api


@pytest.fixture
def mock_order_api():
    """Mock order API for testing"""
    order_api = AsyncMock()
    order_api.place_order = AsyncMock(return_value=MOCK_ORDER_DATA)
    order_api.cancel_order = AsyncMock(return_value=True)
    order_api.get_order_status = AsyncMock(return_value=MOCK_ORDER_DATA)
    order_api.get_order_history = AsyncMock(return_value=[MOCK_ORDER_DATA])
    order_api.get_all_orders = AsyncMock(return_value=[MOCK_ORDER_DATA])
    order_api.get_account_orders = AsyncMock(return_value=[MOCK_ORDER_DATA])
    order_api.get_bot_orders = AsyncMock(return_value=[MOCK_ORDER_DATA])
    return order_api


@pytest.fixture
def mock_async_client_wrapper(mock_async_client, mock_auth_manager):
    """Mock async client wrapper for testing"""
    from ..core.async_client import AsyncHaasClientWrapper, AsyncClientConfig
    
    config = AsyncClientConfig(
        cache_ttl=60.0,
        enable_caching=False,
        enable_rate_limiting=False,
        max_concurrent_requests=5,
        request_timeout=5.0
    )
    
    wrapper = AsyncHaasClientWrapper(mock_async_client, mock_auth_manager, config)
    wrapper.execute_request = AsyncMock(return_value={"success": True})
    wrapper.execute_batch_requests = AsyncMock(return_value=[{"success": True}])
    wrapper.execute_parallel_requests = AsyncMock(return_value=[{"success": True}])
    wrapper.health_check = AsyncMock(return_value={"status": "healthy"})
    
    return wrapper


@pytest.fixture
def mock_lab_service(mock_lab_api, mock_backtest_api, mock_script_api, mock_account_api):
    """Mock lab service for testing"""
    from ..services.lab import LabService
    
    service = LabService(mock_lab_api, mock_backtest_api, mock_script_api, mock_account_api)
    service.get_all_labs = AsyncMock(return_value=[MOCK_LAB_DATA])
    service.create_lab = AsyncMock(return_value={"success": True, "data": MOCK_LAB_DATA})
    service.delete_lab = AsyncMock(return_value={"success": True})
    service.execute_lab = AsyncMock(return_value={"success": True, "data": {"lab_id": "test_lab_123", "status": "running"}})
    service.get_lab_status = AsyncMock(return_value={"success": True, "data": {"lab_id": "test_lab_123", "status": "completed"}})
    
    return service


@pytest.fixture
def mock_bot_service(mock_bot_api, mock_account_api, mock_backtest_api, mock_market_api, mock_async_client, mock_auth_manager):
    """Mock bot service for testing"""
    from ..services.bot import BotService
    
    service = BotService(mock_bot_api, mock_account_api, mock_backtest_api, mock_market_api, mock_async_client, mock_auth_manager)
    service.get_all_bots = AsyncMock(return_value=[MOCK_BOT_DATA])
    service.create_bot = AsyncMock(return_value={"success": True, "data": MOCK_BOT_DATA})
    service.delete_bot = AsyncMock(return_value={"success": True})
    service.activate_bot = AsyncMock(return_value={"success": True})
    service.deactivate_bot = AsyncMock(return_value={"success": True})
    service.pause_bot = AsyncMock(return_value={"success": True})
    service.resume_bot = AsyncMock(return_value={"success": True})
    
    return service


@pytest.fixture
def mock_analysis_service(mock_lab_api, mock_backtest_api, mock_bot_api, mock_async_client, mock_auth_manager):
    """Mock analysis service for testing"""
    from ..services.analysis import AnalysisService
    
    service = AnalysisService(mock_lab_api, mock_backtest_api, mock_bot_api, mock_async_client, mock_auth_manager)
    service.analyze_lab_comprehensive = AsyncMock(return_value={
        "success": True,
        "lab_id": "test_lab_123",
        "lab_name": "Test Lab",
        "total_backtests": 10,
        "average_roi": 100.0,
        "best_roi": 200.0,
        "average_win_rate": 0.6,
        "top_performers": [MOCK_BACKTEST_DATA]
    })
    service.analyze_bot = AsyncMock(return_value={"success": True, "data": MOCK_BOT_DATA})
    service.analyze_wfo = AsyncMock(return_value={"success": True, "data": {"lab_id": "test_lab_123", "periods": 5}})
    service.get_performance_metrics = AsyncMock(return_value={"success": True, "data": {"total_requests": 100, "success_rate": 0.95}})
    
    return service


@pytest.fixture
def mock_reporting_service():
    """Mock reporting service for testing"""
    from ..services.reporting import ReportingService
    
    service = ReportingService()
    service.generate_analysis_report = AsyncMock(return_value={"report_path": "/tmp/test_report.csv"})
    service.generate_bot_recommendations_report = AsyncMock(return_value={"report_path": "/tmp/test_bot_report.csv"})
    service.generate_wfo_report = AsyncMock(return_value={"report_path": "/tmp/test_wfo_report.csv"})
    service.generate_performance_report = AsyncMock(return_value={"report_path": "/tmp/test_performance_report.csv"})
    
    return service


@pytest.fixture
def mock_data_dumper(mock_async_client_wrapper):
    """Mock data dumper for testing"""
    from ..tools.data_dumper import DataDumper
    
    dumper = DataDumper(mock_async_client_wrapper)
    dumper.dump_data = AsyncMock(return_value={"success": True, "files": ["/tmp/test_dump.json"]})
    dumper.dump_labs = AsyncMock(return_value={"success": True, "files": ["/tmp/labs.json"]})
    dumper.dump_bots = AsyncMock(return_value={"success": True, "files": ["/tmp/bots.json"]})
    dumper.dump_accounts = AsyncMock(return_value={"success": True, "files": ["/tmp/accounts.json"]})
    
    return dumper


@pytest.fixture
def mock_testing_manager(mock_async_client_wrapper):
    """Mock testing manager for testing"""
    from ..tools.testing_manager import TestingManager
    
    manager = TestingManager(mock_async_client_wrapper)
    manager.create_test_data = AsyncMock(return_value={"success": True, "data": {"labs": 1, "bots": 1, "accounts": 1}})
    manager.cleanup_test_data = AsyncMock(return_value={"success": True, "cleaned": {"labs": 1, "bots": 1, "accounts": 1}})
    manager.validate_test_data = AsyncMock(return_value={"success": True, "valid": True})
    manager.isolate_test_data = AsyncMock(return_value={"success": True, "isolated": True})
    
    return manager


# Test utilities
class TestUtils:
    """Utility class for test helpers"""
    
    @staticmethod
    def create_mock_response(data: Any, success: bool = True) -> Dict[str, Any]:
        """Create a mock API response"""
        return {
            "success": success,
            "data": data,
            "error": None if success else "Test error"
        }
    
    @staticmethod
    def create_mock_error_response(error_message: str) -> Dict[str, Any]:
        """Create a mock error response"""
        return {
            "success": False,
            "data": None,
            "error": error_message
        }
    
    @staticmethod
    async def wait_for_async_mock(mock_func, timeout: float = 1.0):
        """Wait for an async mock to be called"""
        import asyncio
        start_time = asyncio.get_event_loop().time()
        while not mock_func.called and (asyncio.get_event_loop().time() - start_time) < timeout:
            await asyncio.sleep(0.01)
        return mock_func.called


@pytest.fixture
def test_utils():
    """Test utilities fixture"""
    return TestUtils


# Performance testing utilities
class PerformanceTestUtils:
    """Utilities for performance testing"""
    
    @staticmethod
    async def measure_execution_time(func, *args, **kwargs):
        """Measure execution time of an async function"""
        import time
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    @staticmethod
    def assert_performance(execution_time: float, max_time: float, operation: str):
        """Assert that an operation completed within the expected time"""
        assert execution_time <= max_time, f"{operation} took {execution_time:.3f}s, expected <= {max_time:.3f}s"


@pytest.fixture
def perf_utils():
    """Performance test utilities fixture"""
    return PerformanceTestUtils
