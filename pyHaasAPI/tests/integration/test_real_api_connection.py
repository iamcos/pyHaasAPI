"""
Real API Integration Tests

These tests use REAL server connections via SSH tunnels to srv03.
No mocks, no fake data - only real API calls to actual HaasOnline servers.
"""

import pytest
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Import real API modules with error handling
try:
    from pyHaasAPI_v1.core.server_manager import ServerManager
    from pyHaasAPI import api
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}")


class TestRealAPIConnection:
    """Test real API connections to HaasOnline servers."""
    
    @pytest.fixture(scope="class")
    async def server_connection(self):
        """Establish real SSH tunnel connection to srv03."""
        server_manager = ServerManager()
        
        # Connect to srv03 as specified in .cursorrules
        connection_status = await server_manager.connect_to_server("srv03")
        
        if not connection_status.connected:
            pytest.skip(f"Could not connect to srv03: {connection_status.error}")
        
        yield connection_status
        
        # Cleanup: disconnect from server
        await server_manager.disconnect()
    
    @pytest.fixture(scope="class")
    async def authenticated_executor(self, server_connection):
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
    
    @pytest.mark.asyncio
    async def test_server_connection(self, server_connection):
        """Test that we can connect to srv03 via SSH tunnel."""
        assert server_connection.connected
        assert server_connection.local_port is not None
        assert server_connection.local_port > 8000  # Should be a valid port
    
    @pytest.mark.asyncio
    async def test_authentication(self, authenticated_executor):
        """Test real authentication with HaasOnline API."""
        # This should work with real credentials
        assert authenticated_executor is not None
    
    @pytest.mark.asyncio
    async def test_get_labs_real(self, authenticated_executor):
        """Test getting real labs from the API."""
        # Get real labs from the server
        labs = api.get_labs(authenticated_executor)
        
        # Should return real lab data
        assert isinstance(labs, list)
        print(f"Found {len(labs)} real labs")
    
    @pytest.mark.asyncio
    async def test_get_accounts_real(self, authenticated_executor):
        """Test getting real accounts from the API."""
        # Get real accounts from the server
        accounts = api.get_accounts(authenticated_executor)
        
        # Should return real account data
        assert isinstance(accounts, list)
        print(f"Found {len(accounts)} real accounts")
    
    @pytest.mark.asyncio
    async def test_get_scripts_real(self, authenticated_executor):
        """Test getting real scripts from the API."""
        # Get real scripts from the server
        scripts = api.get_all_scripts(authenticated_executor)
        
        # Should return real script data
        assert isinstance(scripts, list)
        print(f"Found {len(scripts)} real scripts")
    
    @pytest.mark.asyncio
    async def test_create_test_lab_real(self, authenticated_executor):
        """Test creating a real test lab (will be cleaned up)."""
        # Get a real script to use
        scripts = api.get_all_scripts(authenticated_executor)
        if not scripts:
            pytest.skip("No scripts available for testing")
        
        script = scripts[0]
        
        # Get a real account to use
        accounts = api.get_accounts(authenticated_executor)
        if not accounts:
            pytest.skip("No accounts available for testing")
        
        account = accounts[0]
        
        # Create a real test lab
        lab_request = api.CreateLabRequest(
            script_id=script.script_id,
            name="Test Lab - Real API Test",
            account_id=account.account_id,
            market="BTC_USDT"
        )
        
        lab = api.create_lab(authenticated_executor, lab_request)
        
        # Verify the lab was created
        assert lab is not None
        assert lab.lab_id is not None
        print(f"Created real test lab: {lab.lab_id}")
        
        # Clean up: delete the test lab
        try:
            api.delete_lab(authenticated_executor, lab.lab_id)
            print(f"Cleaned up test lab: {lab.lab_id}")
        except Exception as e:
            print(f"Warning: Could not clean up test lab {lab.lab_id}: {e}")
    
    @pytest.mark.asyncio
    async def test_get_markets_real(self, authenticated_executor):
        """Test getting real market data from the API."""
        # Get real market data
        markets = api.get_trade_markets(authenticated_executor)
        
        # Should return real market data
        assert isinstance(markets, list)
        print(f"Found {len(markets)} real markets")
        
        # Check for common markets
        market_symbols = [market.symbol for market in markets]
        assert "BTC_USDT" in market_symbols or "BTCUSDT" in market_symbols
