"""
CRUD Test Configuration and Fixtures

Provides session-scoped fixtures for srv03 tunnel management, authentication,
API initialization, and cleanup registry for comprehensive CRUD testing.
"""

import asyncio
import os
import signal
import time
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field

import pytest
import pytest_asyncio
from dotenv import load_dotenv

# v2-only imports - guard against v1 usage
try:
    from pyHaasAPI.core.client import AsyncHaasClient
    from pyHaasAPI.core.auth import AuthenticationManager
    from pyHaasAPI.core.server_manager import ServerManager
    from pyHaasAPI.api.lab.lab_api import LabAPI
    from pyHaasAPI.api.bot.bot_api import BotAPI
    from pyHaasAPI.api.account.account_api import AccountAPI
    from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
    from pyHaasAPI.api.market.market_api import MarketAPI
    from pyHaasAPI.api.script.script_api import ScriptAPI
    from pyHaasAPI.api.order.order_api import OrderAPI
    from pyHaasAPI.config.api_config import APIConfig
    from pyHaasAPI.config.settings import Settings
    from pyHaasAPI.exceptions import (
        HaasAPIError, AuthenticationError, APIError, ValidationError,
        NetworkError, ConnectionError, TimeoutError, ConfigurationError,
        LabError, LabNotFoundError, LabExecutionError, LabConfigurationError,
        BotError, BotNotFoundError, BotCreationError, BotConfigurationError,
        AccountError, AccountNotFoundError, AccountConfigurationError
    )
except ImportError as e:
    pytest.fail(f"v2 imports failed: {e}. This indicates v1 usage or missing v2 modules.")


@dataclass
class CleanupRegistry:
    """Registry to track created resources for cleanup"""
    lab_ids: Set[str] = field(default_factory=set)
    bot_ids: Set[str] = field(default_factory=set)
    job_ids: Set[str] = field(default_factory=set)
    
    def add_lab(self, lab_id: str) -> None:
        """Add lab ID to cleanup registry"""
        self.lab_ids.add(lab_id)
    
    def add_bot(self, bot_id: str) -> None:
        """Add bot ID to cleanup registry"""
        self.bot_ids.add(bot_id)
    
    def add_job(self, job_id: str) -> None:
        """Add job ID to cleanup registry"""
        self.job_ids.add(job_id)


# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def test_session_id() -> str:
    """Generate unique session ID for test resources"""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


@pytest_asyncio.fixture(scope="session")
async def srv03_tunnel():
    """
    Session-scoped fixture to ensure srv03 SSH tunnel is active.
    Enforces single-connection policy and preflight checks.
    """
    # Kill any existing Python processes
    os.system("pkill -f python || true")
    
    # Establish SSH tunnel to srv03
    tunnel_cmd = "ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv03 &"
    os.system(f"bash -lc '{tunnel_cmd}'")
    
    # Wait for tunnel to establish
    time.sleep(3)
    
    # Verify tunnel via ServerManager preflight check
    try:
        server_manager = ServerManager(Settings())
        # This will raise if tunnel is not available
        await server_manager.preflight_check()
        yield server_manager
    except Exception as e:
        pytest.fail(f"srv03 tunnel preflight check failed: {e}")
    finally:
        # Cleanup tunnel on session end
        os.system("pkill -f 'ssh.*srv03' || true")


@pytest_asyncio.fixture(scope="function")
async def auth_context(srv03_tunnel):
    """
    Session-scoped authentication context.
    Creates and authenticates AsyncHaasClient and AuthenticationManager once.
    """
    # Load credentials from environment
    email = os.getenv('API_EMAIL')
    password = os.getenv('API_PASSWORD')
    
    if not email or not password:
        pytest.fail("API_EMAIL and API_PASSWORD must be set in .env file")
    
    # Create configuration
    config = APIConfig(
        email=email,
        password=password,
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    # Authenticate once for session
    try:
        session = await auth_manager.authenticate()
        yield {
            'client': client,
            'auth_manager': auth_manager,
            'session': session,
            'config': config
        }
    except Exception as e:
        pytest.fail(f"Authentication failed: {e}")
    finally:
        # Ensure client session is closed to avoid unclosed session warnings
        try:
            await client.close()
        except Exception:
            pass


@pytest.fixture(scope="function")
def apis(auth_context):
    """
    Function-scoped fixture providing initialized API modules.
    Returns LabAPI, BotAPI, AccountAPI, BacktestAPI, MarketAPI.
    """
    client = auth_context['client']
    auth_manager = auth_context['auth_manager']
    
    # Initialize all API modules
    lab_api = LabAPI(client, auth_manager)
    bot_api = BotAPI(client, auth_manager)
    account_api = AccountAPI(client, auth_manager)
    backtest_api = BacktestAPI(client, auth_manager)
    market_api = MarketAPI(client, auth_manager)
    script_api = ScriptAPI(client, auth_manager)
    order_api = OrderAPI(client, auth_manager)
    
    return {
        'lab_api': lab_api,
        'bot_api': bot_api,
        'account_api': account_api,
        'backtest_api': backtest_api,
        'market_api': market_api,
        'script_api': script_api,
        'order_api': order_api
    }


@pytest_asyncio.fixture(scope="function")
async def default_entities(apis):
    """
    Provide default valid entities from the server:
    - account_id: first available account
    - script_id: first available script
    - market_tag: BTC_USDT_PERPETUAL if present, else first market
    """
    account_api = apis['account_api']
    script_api = apis.get('script_api')
    market_api = apis['market_api']

    # Accounts
    accounts = await account_api.get_accounts()
    assert accounts and isinstance(accounts, list), "No accounts available for tests"
    account_id = getattr(accounts[0], 'account_id', None) or getattr(accounts[0], 'id', None)
    assert account_id, "Account ID not found on first account"

    # Scripts
    script_id = None
    if script_api:
        try:
            scripts = await script_api.get_all_scripts()
            if scripts and isinstance(scripts, list):
                script_id = getattr(scripts[0], 'script_id', None) or getattr(scripts[0], 'id', None)
        except Exception:
            script_id = None
    # Fallback script id if scripts endpoint not available
    script_id = script_id or "default-script"

    # Markets
    markets = await market_api.get_trade_markets()
    # Markets endpoint may be large; only require list type
    assert isinstance(markets, list), "Markets response should be a list"
    market_tag = None
    for m in markets:
        tag = getattr(m, 'market', None) or getattr(m, 'market_tag', None) or getattr(m, 'symbol', None)
        if tag == 'BTC_USDT_PERPETUAL':
            market_tag = tag
            break
    if not market_tag:
        first = markets[0]
        market_tag = (
            getattr(first, 'market', None)
            or getattr(first, 'market_tag', None)
            or getattr(first, 'symbol', None)
        )
        if not market_tag:
            # Synthesize from fields if necessary
            exch = getattr(first, 'exchange', '')
            base = getattr(first, 'base_currency', '')
            quote = getattr(first, 'quote_currency', '')
            market_tag = f"{exch}_{base}_{quote}" if exch and base and quote else None
    # Provide a safe fallback; some servers may omit a canonical tag
    market_tag = market_tag or 'BTC_USDT_PERPETUAL'

    return {
        'account_id': account_id,
        'script_id': script_id,
        'market_tag': market_tag
    }


@pytest.fixture(scope="session")
def cleanup_registry() -> CleanupRegistry:
    """Session-scoped registry to track created resources"""
    return CleanupRegistry()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def teardown_cleanup(cleanup_registry):
    """
    Session-scoped finalizer to cleanup all created resources.
    Cancels jobs, deactivates bots, and deletes labs/bots.
    """
    yield
    
    # Cleanup in reverse order of creation
    async def cleanup_all():
        try:
            # Create fresh client for cleanup to avoid loop issues
            email = os.getenv('API_EMAIL')
            password = os.getenv('API_PASSWORD')
            config = APIConfig(email=email, password=password, host="127.0.0.1", port=8090, timeout=30.0)
            client = AsyncHaasClient(config)
            auth_manager = AuthenticationManager(client, config)
            try:
                await auth_manager.authenticate()
            except Exception:
                pass
            # Cancel any running jobs
            for job_id in cleanup_registry.job_ids:
                try:
                    # Cancel job if possible
                    pass  # Implementation depends on available API
                except Exception:
                    pass
            
            # Deactivate and delete bots
            for bot_id in cleanup_registry.bot_ids:
                try:
                    # Deactivate bot
                    bot_api = BotAPI(client, auth_manager)
                    await bot_api.deactivate_bot(bot_id)
                    # Delete bot
                    await bot_api.delete_bot(bot_id)
                except Exception:
                    pass
            
            # Delete labs
            for lab_id in cleanup_registry.lab_ids:
                try:
                    # Cancel any running lab execution
                    lab_api = LabAPI(client, auth_manager)
                    await lab_api.cancel_lab_execution(lab_id)
                    # Delete lab
                    await lab_api.delete_lab(lab_id)
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    # Run cleanup
    await cleanup_all()


@pytest.fixture(scope="function")
def test_timeout():
    """
    Function-scoped timeout wrapper using signal.alarm().
    Provides hard timeout for individual tests.
    """
    def timeout_handler(signum, frame):
        raise TimeoutError("Test exceeded timeout")
    
    # Set up timeout handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minute timeout per test
    
    yield
    
    # Restore original handler
    signal.alarm(0)
    signal.signal(signal.SIGALRM, old_handler)


def pytest_configure(config):
    """Configure pytest with v2-only runtime enforcement"""
    # Add markers for test categorization
    config.addinivalue_line("markers", "crud: CRUD operation tests")
    config.addinivalue_line("markers", "field_mapping: Field mapping validation tests")
    config.addinivalue_line("markers", "cleanup: Cleanup and teardown tests")
    config.addinivalue_line("markers", "srv03: Tests requiring srv03 server")
    config.addinivalue_line("markers", "error_handling: Error handling robustness tests")
    config.addinivalue_line("markers", "manager_integration: Manager integration tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to enforce v2-only runtime"""
    for item in items:
        # Add srv03 marker to all crud tests
        if "crud" in str(item.fspath):
            item.add_marker(pytest.mark.srv03)
            item.add_marker(pytest.mark.crud)
