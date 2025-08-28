"""
Pytest configuration and shared fixtures for MCP TUI Client tests.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Generator

from mcp_tui_client.services.config import ConfigurationService
from mcp_tui_client.services.mcp_client import MCPClientService


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config() -> ConfigurationService:
    """Mock configuration service for testing."""
    config = MagicMock(spec=ConfigurationService)
    config.get_mcp_settings.return_value = {
        "host": "localhost",
        "port": 3002,
        "timeout": 30,
        "retry_attempts": 3,
        "use_ssl": False
    }
    config.get_ui_preferences.return_value = {
        "theme": "dark",
        "auto_refresh_interval": 5,
        "show_help_on_startup": True
    }
    return config


@pytest.fixture
async def mock_mcp_client() -> AsyncGenerator[MCPClientService, None]:
    """Mock MCP client service for testing."""
    client = AsyncMock(spec=MCPClientService)
    client.connect.return_value = True
    client.is_connected = True
    client.call_tool.return_value = {"status": "success", "data": {}}
    yield client


@pytest.fixture
def sample_bot_data() -> dict:
    """Sample bot data for testing."""
    return {
        "bot_id": "test-bot-123",
        "name": "Test Bot",
        "status": "active",
        "account_id": "test-account",
        "script_id": "test-script",
        "performance": {
            "total_return": 15.5,
            "win_rate": 0.65,
            "total_trades": 42
        }
    }


@pytest.fixture
def sample_lab_data() -> dict:
    """Sample lab data for testing."""
    return {
        "lab_id": "test-lab-456",
        "name": "Test Lab",
        "status": "completed",
        "script_id": "test-script",
        "backtest_results": {
            "total_return": 12.3,
            "sharpe_ratio": 1.45,
            "max_drawdown": -8.2,
            "total_trades": 156
        }
    }


@pytest.fixture
def sample_market_data() -> dict:
    """Sample market data for testing."""
    return {
        "symbol": "BTC_USD",
        "price": 45000.0,
        "volume": 1234567.89,
        "change_24h": 2.5,
        "high_24h": 46000.0,
        "low_24h": 44000.0
    }


@pytest.fixture
def sample_workflow_data() -> dict:
    """Sample workflow data for testing."""
    return {
        "workflow_id": "test-workflow-789",
        "name": "Test Workflow",
        "nodes": [
            {
                "node_id": "lab-1",
                "type": "lab",
                "parameters": {
                    "trading_pair": "BTC_USD",
                    "script_id": "test-script"
                }
            },
            {
                "node_id": "analysis-1",
                "type": "analysis",
                "parameters": {
                    "analysis_type": "performance"
                }
            }
        ],
        "connections": [
            {
                "from_node": "lab-1",
                "from_port": "backtest_results",
                "to_node": "analysis-1",
                "to_port": "backtest_data"
            }
        ]
    }


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.network = pytest.mark.network