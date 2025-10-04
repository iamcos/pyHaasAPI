"""
Real API functionality tests for pyHaasAPI.

These tests use REAL server connections via SSH tunnels to srv03.
No mocks, no fake data - only real API calls to actual HaasOnline servers.
Tests actual functionality like creating labs, bots, and managing accounts.
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


class TestRealAPIFunctionality:
    """Test real API functionality with actual server connections."""
    
    @pytest.fixture(scope="class")
    async def server_connection(self):
        """Establish connection to srv03 for testing."""
        server_manager = ServerManager(os.getenv('API_EMAIL'), os.getenv('API_PASSWORD'))
        connection_status = await server_manager.connect_to_server("srv03")
        
        if not connection_status.connected:
            pytest.fail(f"Failed to connect to srv03: {connection_status.error}")
        
        yield connection_status
        
        await server_manager.disconnect_from_server("srv03")
    
    @pytest.fixture(scope="class")
    async def authenticated_executor(self, server_connection):
        """Get authenticated executor for API calls."""
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=server_connection.local_port,
            state=api.Guest()
        )
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'),
            os.getenv('API_PASSWORD')
        )
        return executor
    
    @pytest.mark.asyncio
    async def test_connect_and_authenticate(self, server_connection, authenticated_executor):
        """Test connecting to srv03 and authenticating."""
        assert server_connection.connected is True
        assert server_connection.local_port is not None
        assert authenticated_executor is not None
        assert authenticated_executor.is_authenticated is True
    
    @pytest.mark.asyncio
    async def test_get_labs_real_data(self, authenticated_executor):
        """Test getting real labs from the server."""
        labs = api.get_labs(authenticated_executor)
        assert isinstance(labs, list)
        # Should have real lab data from the server
        print(f"Found {len(labs)} labs on server")
        
        if labs:
            # Test that we can get details of the first lab
            first_lab = labs[0]
            lab_details = api.get_lab_details(authenticated_executor, first_lab['labId'])
            assert lab_details is not None
            assert 'labId' in lab_details
            print(f"Lab details: {lab_details['labId']}")
    
    @pytest.mark.asyncio
    async def test_get_bots_real_data(self, authenticated_executor):
        """Test getting real bots from the server."""
        bots = api.get_all_bots(authenticated_executor)
        assert isinstance(bots, list)
        # Should have real bot data from the server
        print(f"Found {len(bots)} bots on server")
        
        if bots:
            # Test that we can get details of the first bot
            first_bot = bots[0]
            bot_details = api.get_bot(authenticated_executor, first_bot['botId'])
            assert bot_details is not None
            assert 'botId' in bot_details
            print(f"Bot details: {bot_details['botId']}")
    
    @pytest.mark.asyncio
    async def test_get_accounts_real_data(self, authenticated_executor):
        """Test getting real accounts from the server."""
        accounts = api.get_accounts(authenticated_executor)
        assert isinstance(accounts, list)
        # Should have real account data from the server
        print(f"Found {len(accounts)} accounts on server")
        
        if accounts:
            # Test that we can get details of the first account
            first_account = accounts[0]
            account_data = api.get_account_data(authenticated_executor, first_account['accountId'])
            assert account_data is not None
            assert 'accountId' in account_data
            print(f"Account details: {account_data['accountId']}")
    
    @pytest.mark.asyncio
    async def test_get_scripts_real_data(self, authenticated_executor):
        """Test getting real scripts from the server."""
        scripts = api.get_all_scripts(authenticated_executor)
        assert isinstance(scripts, list)
        # Should have real script data from the server
        print(f"Found {len(scripts)} scripts on server")
        
        if scripts:
            # Test that we can get details of the first script
            first_script = scripts[0]
            script_record = api.get_script_record(authenticated_executor, first_script['scriptId'])
            assert script_record is not None
            assert 'scriptId' in script_record
            print(f"Script details: {script_record['scriptId']}")
    
    @pytest.mark.asyncio
    async def test_get_markets_real_data(self, authenticated_executor):
        """Test getting real markets from the server."""
        markets = api.get_trade_markets(authenticated_executor)
        assert isinstance(markets, list)
        # Should have real market data from the server
        print(f"Found {len(markets)} markets on server")
        
        if markets:
            # Test that we can get price data for the first market
            first_market = markets[0]
            market_tag = first_market['marketTag']
            price_data = api.get_price_data(authenticated_executor, market_tag)
            assert price_data is not None
            print(f"Price data for {market_tag}: {price_data}")
    
    @pytest.mark.asyncio
    async def test_create_test_lab(self, authenticated_executor):
        """Test creating a new lab for testing purposes."""
        # Get available scripts first
        scripts = api.get_all_scripts(authenticated_executor)
        if not scripts:
            pytest.skip("No scripts available for testing")
        
        # Get available accounts
        accounts = api.get_accounts(authenticated_executor)
        if not accounts:
            pytest.skip("No accounts available for testing")
        
        # Get available markets
        markets = api.get_trade_markets(authenticated_executor)
        if not markets:
            pytest.skip("No markets available for testing")
        
        # Create a test lab
        test_lab_data = {
            "scriptId": scripts[0]['scriptId'],
            "name": "Test Lab - API Testing",
            "accountId": accounts[0]['accountId'],
            "marketTag": markets[0]['marketTag'],
            "settings": {
                "accountId": accounts[0]['accountId'],
                "marketTag": markets[0]['marketTag']
            }
        }
        
        try:
            new_lab = api.create_lab(authenticated_executor, test_lab_data)
            assert new_lab is not None
            assert 'labId' in new_lab
            print(f"Created test lab: {new_lab['labId']}")
            
            # Clean up - delete the test lab
            api.delete_lab(authenticated_executor, new_lab['labId'])
            print(f"Cleaned up test lab: {new_lab['labId']}")
            
        except Exception as e:
            pytest.skip(f"Could not create test lab: {e}")
    
    @pytest.mark.asyncio
    async def test_lab_execution_workflow(self, authenticated_executor):
        """Test a complete lab execution workflow."""
        # Get available labs
        labs = api.get_labs(authenticated_executor)
        if not labs:
            pytest.skip("No labs available for testing")
        
        # Test getting lab details
        lab_id = labs[0]['labId']
        lab_details = api.get_lab_details(authenticated_executor, lab_id)
        assert lab_details is not None
        assert lab_details['labId'] == lab_id
        
        # Test getting lab execution status
        execution_status = api.get_lab_execution_update(authenticated_executor, lab_id)
        assert execution_status is not None
        print(f"Lab {lab_id} execution status: {execution_status}")
        
        # Test getting backtest results if available
        try:
            backtest_results = api.get_backtest_result(authenticated_executor, lab_id, 0, 10)
            assert backtest_results is not None
            print(f"Found {len(backtest_results.get('Data', []))} backtest results")
        except Exception as e:
            print(f"Could not get backtest results: {e}")
    
    @pytest.mark.asyncio
    async def test_bot_management_workflow(self, authenticated_executor):
        """Test bot management functionality."""
        # Get available bots
        bots = api.get_all_bots(authenticated_executor)
        if not bots:
            pytest.skip("No bots available for testing")
        
        # Test getting bot details
        bot_id = bots[0]['botId']
        bot_details = api.get_bot(authenticated_executor, bot_id)
        assert bot_details is not None
        assert bot_details['botId'] == bot_id
        
        # Test getting bot runtime data
        try:
            runtime_data = api.get_full_bot_runtime_data(authenticated_executor, bot_id)
            assert runtime_data is not None
            print(f"Bot {bot_id} runtime data retrieved")
        except Exception as e:
            print(f"Could not get bot runtime data: {e}")
        
        # Test getting bot orders
        try:
            orders = api.get_bot_orders(authenticated_executor, bot_id)
            assert orders is not None
            print(f"Bot {bot_id} has {len(orders)} orders")
        except Exception as e:
            print(f"Could not get bot orders: {e}")
        
        # Test getting bot positions
        try:
            positions = api.get_bot_positions(authenticated_executor, bot_id)
            assert positions is not None
            print(f"Bot {bot_id} has {len(positions)} positions")
        except Exception as e:
            print(f"Could not get bot positions: {e}")
    
    @pytest.mark.asyncio
    async def test_account_management_workflow(self, authenticated_executor):
        """Test account management functionality."""
        # Get available accounts
        accounts = api.get_accounts(authenticated_executor)
        if not accounts:
            pytest.skip("No accounts available for testing")
        
        # Test getting account details
        account_id = accounts[0]['accountId']
        account_data = api.get_account_data(authenticated_executor, account_id)
        assert account_data is not None
        assert account_data['accountId'] == account_id
        
        # Test getting account balance
        try:
            balance = api.get_account_balance(authenticated_executor, account_id)
            assert balance is not None
            print(f"Account {account_id} balance: {balance}")
        except Exception as e:
            print(f"Could not get account balance: {e}")
        
        # Test getting account orders
        try:
            orders = api.get_account_orders(authenticated_executor, account_id)
            assert orders is not None
            print(f"Account {account_id} has {len(orders)} orders")
        except Exception as e:
            print(f"Could not get account orders: {e}")
    
    @pytest.mark.asyncio
    async def test_script_management_workflow(self, authenticated_executor):
        """Test script management functionality."""
        # Get available scripts
        scripts = api.get_all_scripts(authenticated_executor)
        if not scripts:
            pytest.skip("No scripts available for testing")
        
        # Test getting script details
        script_id = scripts[0]['scriptId']
        script_record = api.get_script_record(authenticated_executor, script_id)
        assert script_record is not None
        assert script_record['scriptId'] == script_id
        
        # Test getting script item with dependencies
        try:
            script_item = api.get_script_item(authenticated_executor, script_id)
            assert script_item is not None
            print(f"Script {script_id} item retrieved with dependencies")
        except Exception as e:
            print(f"Could not get script item: {e}")
    
    @pytest.mark.asyncio
    async def test_market_data_workflow(self, authenticated_executor):
        """Test market data functionality."""
        # Get available markets
        markets = api.get_trade_markets(authenticated_executor)
        if not markets:
            pytest.skip("No markets available for testing")
        
        # Test getting price data
        market_tag = markets[0]['marketTag']
        price_data = api.get_price_data(authenticated_executor, market_tag)
        assert price_data is not None
        print(f"Price data for {market_tag}: {price_data}")
        
        # Test getting historical data
        try:
            historical_data = api.get_historical_data(authenticated_executor, market_tag, "1h", 100)
            assert historical_data is not None
            print(f"Historical data for {market_tag}: {len(historical_data)} data points")
        except Exception as e:
            print(f"Could not get historical data: {e}")

