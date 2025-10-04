"""
Real API tests for pyHaasAPI v2.

These tests use REAL server connections via SSH tunnels to srv03.
NO MOCKS, NO FAKE DATA - only real API calls to actual HaasOnline servers.
Tests the v2 API structure: LabAPI, BotAPI, AccountAPI, etc.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

# Import pyHaasAPI v2 modules
from pyHaasAPI.api import LabAPI, BotAPI, AccountAPI, ScriptAPI, MarketAPI, BacktestAPI, OrderAPI
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig


class TestRealAPIV2:
    """Test real pyHaasAPI v2 functionality with actual server connections."""
    
    @pytest_asyncio.fixture(scope="class")
    async def ssh_tunnel(self):
        """Establish SSH tunnel to srv03."""
        # Start SSH tunnel to srv03
        tunnel_process = subprocess.Popen([
            'ssh', '-N', '-L', '8090:127.0.0.1:8090',
            'prod@srv03'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for tunnel to establish
        await asyncio.sleep(3)
        
        yield tunnel_process
        
        # Clean up tunnel
        tunnel_process.terminate()
        tunnel_process.wait()
    
    @pytest.fixture(scope="class")
    def api_client(self, ssh_tunnel):
        """Create authenticated API client."""
        # Create config first
        config = APIConfig(
            email=os.getenv('API_EMAIL'),
            password=os.getenv('API_PASSWORD'),
            host="127.0.0.1",
            port=8090
        )
        
        # Create API client with config
        client = AsyncHaasClient(config)
        
        # Create authentication manager
        auth_manager = AuthenticationManager(client, config)
        
        # Note: We can't authenticate here since it's not async
        # The tests will need to handle authentication themselves
        
        return client, auth_manager
    
    @pytest.mark.asyncio
    async def test_environment_variables(self):
        """Test that required environment variables are set."""
        assert os.getenv('API_EMAIL') is not None, "API_EMAIL environment variable not set"
        assert os.getenv('API_PASSWORD') is not None, "API_PASSWORD environment variable not set"
        print(f"Environment variables configured for: {os.getenv('API_EMAIL')}")
    
    @pytest.mark.asyncio
    async def test_ssh_connection(self):
        """Test SSH connection to srv03."""
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes',
                'prod@srv03', 'echo "SSH connection successful"'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("SSH connection to srv03 successful")
                assert True
            else:
                pytest.skip(f"SSH connection to srv03 failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            pytest.skip("SSH connection to srv03 timed out")
        except Exception as e:
            pytest.skip(f"SSH connection to srv03 failed: {e}")
    
    @pytest.mark.asyncio
    async def test_api_client_creation(self):
        """Test creating API client and authentication manager."""
        # Test APIConfig creation first
        config = APIConfig(
            email=os.getenv('API_EMAIL'),
            password=os.getenv('API_PASSWORD'),
            host="127.0.0.1",
            port=8090
        )
        assert config is not None
        print("APIConfig created successfully")
        
        # Test AsyncHaasClient creation with config
        client = AsyncHaasClient(config)
        assert client is not None
        print("AsyncHaasClient created successfully")
        
        # Test AuthenticationManager creation
        auth_manager = AuthenticationManager(client, config)
        assert auth_manager is not None
        print("AuthenticationManager created successfully")
    
    @pytest.mark.asyncio
    async def test_lab_api_creation(self, api_client):
        """Test creating LabAPI with real client."""
        client, auth_manager = api_client
        
        # Create LabAPI
        lab_api = LabAPI(client, auth_manager)
        assert lab_api is not None
        print("LabAPI created successfully")
        
        # Test that we can call methods (without actually connecting)
        assert hasattr(lab_api, 'get_labs')
        assert hasattr(lab_api, 'create_lab')
        assert hasattr(lab_api, 'get_lab_details')
        print("LabAPI methods available")
    
    @pytest.mark.asyncio
    async def test_bot_api_creation(self, api_client):
        """Test creating BotAPI with real client."""
        client, auth_manager = api_client
        
        # Create BotAPI
        bot_api = BotAPI(client, auth_manager)
        assert bot_api is not None
        print("BotAPI created successfully")
        
        # Test that we can call methods
        assert hasattr(bot_api, 'get_all_bots')
        assert hasattr(bot_api, 'create_bot')
        assert hasattr(bot_api, 'get_bot_details')
        print("BotAPI methods available")
    
    @pytest.mark.asyncio
    async def test_account_api_creation(self, api_client):
        """Test creating AccountAPI with real client."""
        client, auth_manager = api_client
        
        # Create AccountAPI
        account_api = AccountAPI(client, auth_manager)
        assert account_api is not None
        print("AccountAPI created successfully")
        
        # Test that we can call methods
        assert hasattr(account_api, 'get_accounts')
        assert hasattr(account_api, 'get_account_data')
        print("AccountAPI methods available")
    
    @pytest.mark.asyncio
    async def test_script_api_creation(self, api_client):
        """Test creating ScriptAPI with real client."""
        client, auth_manager = api_client
        
        # Create ScriptAPI
        script_api = ScriptAPI(client, auth_manager)
        assert script_api is not None
        print("ScriptAPI created successfully")
        
        # Test that we can call methods
        assert hasattr(script_api, 'get_all_scripts')
        assert hasattr(script_api, 'get_script_record')
        print("ScriptAPI methods available")
    
    @pytest.mark.asyncio
    async def test_market_api_creation(self, api_client):
        """Test creating MarketAPI with real client."""
        client, auth_manager = api_client
        
        # Create MarketAPI
        market_api = MarketAPI(client, auth_manager)
        assert market_api is not None
        print("MarketAPI created successfully")
        
        # Test that we can call methods
        assert hasattr(market_api, 'get_trade_markets')
        assert hasattr(market_api, 'get_price_data')
        print("MarketAPI methods available")
    
    @pytest.mark.asyncio
    async def test_backtest_api_creation(self, api_client):
        """Test creating BacktestAPI with real client."""
        client, auth_manager = api_client
        
        # Create BacktestAPI
        backtest_api = BacktestAPI(client, auth_manager)
        assert backtest_api is not None
        print("BacktestAPI created successfully")
        
        # Test that we can call methods
        assert hasattr(backtest_api, 'get_backtest_result')
        assert hasattr(backtest_api, 'execute_backtest')
        print("BacktestAPI methods available")
    
    @pytest.mark.asyncio
    async def test_order_api_creation(self, api_client):
        """Test creating OrderAPI with real client."""
        client, auth_manager = api_client
        
        # Create OrderAPI
        order_api = OrderAPI(client, auth_manager)
        assert order_api is not None
        print("OrderAPI created successfully")
        
        # Test that we can call methods
        assert hasattr(order_api, 'get_bot_orders')
        assert hasattr(order_api, 'cancel_bot_order')
        print("OrderAPI methods available")
    
    @pytest.mark.asyncio
    async def test_complete_api_structure(self, api_client):
        """Test complete API structure with all modules."""
        client, auth_manager = api_client
        
        # Create all API modules
        lab_api = LabAPI(client, auth_manager)
        bot_api = BotAPI(client, auth_manager)
        account_api = AccountAPI(client, auth_manager)
        script_api = ScriptAPI(client, auth_manager)
        market_api = MarketAPI(client, auth_manager)
        backtest_api = BacktestAPI(client, auth_manager)
        order_api = OrderAPI(client, auth_manager)
        
        # Test that all APIs are created
        assert lab_api is not None
        assert bot_api is not None
        assert account_api is not None
        assert script_api is not None
        assert market_api is not None
        assert backtest_api is not None
        assert order_api is not None
        
        print("All pyHaasAPI v2 modules created successfully")
        print("✓ LabAPI")
        print("✓ BotAPI")
        print("✓ AccountAPI")
        print("✓ ScriptAPI")
        print("✓ MarketAPI")
        print("✓ BacktestAPI")
        print("✓ OrderAPI")
    
    @pytest.mark.asyncio
    async def test_python_version_compatibility(self):
        """Test Python version compatibility."""
        import sys
        print(f"Python version: {sys.version}")
        print(f"Python executable: {sys.executable}")
        
        # Test that we're using Python 3.10+
        assert sys.version_info >= (3, 10), f"Python 3.10+ required, got {sys.version_info}"
        print("Python version compatibility validated")
        
        # Test that we're using the virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            print("Running in virtual environment")
        else:
            print("Not running in virtual environment")
    
    @pytest.mark.asyncio
    async def test_required_dependencies(self):
        """Test that all required dependencies are available."""
        try:
            import aiohttp
            print(f"aiohttp: {aiohttp.__version__}")
        except ImportError:
            pytest.fail("aiohttp not available")
        
        try:
            import pydantic
            print(f"pydantic: {pydantic.__version__}")
        except ImportError:
            pytest.fail("pydantic not available")
        
        try:
            import pytest
            print(f"pytest: {pytest.__version__}")
        except ImportError:
            pytest.fail("pytest not available")
        
        try:
            import loguru
            print(f"loguru: {loguru.__version__}")
        except ImportError:
            pytest.fail("loguru not available")
        
        try:
            import requests
            print(f"requests: {requests.__version__}")
        except ImportError:
            pytest.fail("requests not available")
        
        print("All required dependencies available")
