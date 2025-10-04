"""
Real API pytest configuration and fixtures for pyHaasAPI tests.

CRITICAL: These tests use REAL server connections via SSH tunnels to srv03.
No mocks, no fake data - only real API calls to actual HaasOnline servers.
"""

import pytest
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import real API modules - use direct imports to avoid version issues
try:
    from pyHaasAPI_v1.core.server_manager import ServerManager
    from pyHaasAPI import api
except ImportError as e:
    print(f"Warning: Could not import pyHaasAPI_v1 modules: {e}")
    # Fallback to basic imports
    ServerManager = None
    api = None


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def server_connection():
    """Establish real SSH tunnel connection to srv03 for all tests."""
    server_manager = ServerManager()
    
    # Connect to srv03 as specified in .cursorrules
    connection_status = await server_manager.connect_to_server("srv03")
    
    if not connection_status.connected:
        pytest.skip(f"Could not connect to srv03: {connection_status.error}")
    
    yield connection_status
    
    # Cleanup: disconnect from server
    await server_manager.disconnect()


@pytest.fixture(scope="session")
async def authenticated_executor(server_connection):
    """Create authenticated API executor using real server connection."""
    # Create API connection through SSH tunnel
    haas_api = api.RequestsExecutor(
        host='127.0.0.1',
        port=server_connection.local_port,
        state=api.Guest()
    )
    
    # Authenticate with real credentials
    executor = haas_api.authenticate(
        os.getenv('API_EMAIL'), 
        os.getenv('API_PASSWORD')
    )
    
    yield executor


@pytest.fixture(scope="session")
async def real_labs(authenticated_executor):
    """Get real labs from the server for testing."""
    labs = api.get_labs(authenticated_executor)
    return labs


@pytest.fixture(scope="session")
async def real_accounts(authenticated_executor):
    """Get real accounts from the server for testing."""
    accounts = api.get_accounts(authenticated_executor)
    return accounts


@pytest.fixture(scope="session")
async def real_scripts(authenticated_executor):
    """Get real scripts from the server for testing."""
    scripts = api.get_all_scripts(authenticated_executor)
    return scripts


@pytest.fixture(scope="session")
async def real_markets(authenticated_executor):
    """Get real markets from the server for testing."""
    markets = api.get_trade_markets(authenticated_executor)
    return markets


@pytest.fixture(scope="session")
async def real_bots(authenticated_executor):
    """Get real bots from the server for testing."""
    bots = api.get_all_bots(authenticated_executor)
    return bots


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow
pytest.mark.asyncio = pytest.mark.asyncio


# Configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "asyncio: Async tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add asyncio marker to async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
        
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add unit marker to unit tests
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add performance marker to performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
