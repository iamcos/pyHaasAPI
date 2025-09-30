"""
Unit tests for pyHaasAPI v2 API modules

This module provides comprehensive unit tests for all API components
including Lab, Bot, Account, Script, Market, Backtest, and Order APIs.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from ..api.lab import LabAPI
from ..api.bot import BotAPI
from ..api.account import AccountAPI
from ..api.script import ScriptAPI
from ..api.market import MarketAPI
from ..api.backtest import BacktestAPI
from ..api.order import OrderAPI


class TestLabAPI:
    """Test cases for LabAPI"""
    
    @pytest.mark.async
    async def test_lab_api_initialization(self, mock_async_client_wrapper):
        """Test lab API initialization"""
        lab_api = LabAPI(mock_async_client_wrapper)
        assert lab_api.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_get_labs(self, mock_lab_api):
        """Test getting labs"""
        mock_lab_api.get_labs.return_value = [{"lab_id": "test_lab_123", "name": "Test Lab"}]
        
        labs = await mock_lab_api.get_labs()
        
        assert len(labs) == 1
        assert labs[0]["lab_id"] == "test_lab_123"
        assert labs[0]["name"] == "Test Lab"
    
    @pytest.mark.async
    async def test_create_lab(self, mock_lab_api):
        """Test creating a lab"""
        mock_lab_api.create_lab.return_value = {"lab_id": "test_lab_123", "name": "Test Lab"}
        
        lab = await mock_lab_api.create_lab("Test Lab", "script_123", "Test description")
        
        assert lab["lab_id"] == "test_lab_123"
        assert lab["name"] == "Test Lab"
        mock_lab_api.create_lab.assert_called_once_with("Test Lab", "script_123", "Test description")
    
    @pytest.mark.async
    async def test_delete_lab(self, mock_lab_api):
        """Test deleting a lab"""
        mock_lab_api.delete_lab.return_value = True
        
        result = await mock_lab_api.delete_lab("test_lab_123")
        
        assert result is True
        mock_lab_api.delete_lab.assert_called_once_with("test_lab_123")


class TestBotAPI:
    """Test cases for BotAPI"""
    
    @pytest.mark.async
    async def test_bot_api_initialization(self, mock_async_client_wrapper):
        """Test bot API initialization"""
        bot_api = BotAPI(mock_async_client_wrapper)
        assert bot_api.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_get_all_bots(self, mock_bot_api):
        """Test getting all bots"""
        mock_bot_api.get_all_bots.return_value = [{"bot_id": "test_bot_789", "name": "Test Bot"}]
        
        bots = await mock_bot_api.get_all_bots()
        
        assert len(bots) == 1
        assert bots[0]["bot_id"] == "test_bot_789"
        assert bots[0]["name"] == "Test Bot"
    
    @pytest.mark.async
    async def test_create_bot(self, mock_bot_api):
        """Test creating a bot"""
        mock_bot_api.create_bot.return_value = {"bot_id": "test_bot_789", "name": "Test Bot"}
        
        bot = await mock_bot_api.create_bot("Test Bot", "account_123", "BTC_USDT_PERPETUAL")
        
        assert bot["bot_id"] == "test_bot_789"
        assert bot["name"] == "Test Bot"
        mock_bot_api.create_bot.assert_called_once()
    
    @pytest.mark.async
    async def test_activate_bot(self, mock_bot_api):
        """Test activating a bot"""
        mock_bot_api.activate_bot.return_value = True
        
        result = await mock_bot_api.activate_bot("test_bot_789")
        
        assert result is True
        mock_bot_api.activate_bot.assert_called_once_with("test_bot_789")


class TestAccountAPI:
    """Test cases for AccountAPI"""
    
    @pytest.mark.async
    async def test_account_api_initialization(self, mock_async_client_wrapper):
        """Test account API initialization"""
        account_api = AccountAPI(mock_async_client_wrapper)
        assert account_api.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_get_accounts(self, mock_account_api):
        """Test getting accounts"""
        mock_account_api.get_accounts.return_value = [{"account_id": "test_account_101", "name": "Test Account"}]
        
        accounts = await mock_account_api.get_accounts()
        
        assert len(accounts) == 1
        assert accounts[0]["account_id"] == "test_account_101"
        assert accounts[0]["name"] == "Test Account"
    
    @pytest.mark.async
    async def test_get_account_balance(self, mock_account_api):
        """Test getting account balance"""
        mock_account_api.get_account_balance.return_value = 10000.0
        
        balance = await mock_account_api.get_account_balance("test_account_101")
        
        assert balance == 10000.0
        mock_account_api.get_account_balance.assert_called_once_with("test_account_101")
    
    @pytest.mark.async
    async def test_set_leverage(self, mock_account_api):
        """Test setting leverage"""
        mock_account_api.set_leverage.return_value = True
        
        result = await mock_account_api.set_leverage("test_account_101", 20)
        
        assert result is True
        mock_account_api.set_leverage.assert_called_once_with("test_account_101", 20)


class TestScriptAPI:
    """Test cases for ScriptAPI"""
    
    @pytest.mark.async
    async def test_script_api_initialization(self, mock_async_client_wrapper):
        """Test script API initialization"""
        script_api = ScriptAPI(mock_async_client_wrapper)
        assert script_api.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_get_all_scripts(self, mock_script_api):
        """Test getting all scripts"""
        mock_script_api.get_all_scripts.return_value = [{"script_id": "test_script_456", "name": "Test Script"}]
        
        scripts = await mock_script_api.get_all_scripts()
        
        assert len(scripts) == 1
        assert scripts[0]["script_id"] == "test_script_456"
        assert scripts[0]["name"] == "Test Script"
    
    @pytest.mark.async
    async def test_add_script(self, mock_script_api):
        """Test adding a script"""
        mock_script_api.add_script.return_value = {"script_id": "test_script_456", "name": "Test Script"}
        
        script = await mock_script_api.add_script("Test Script", "print('hello')", "Test description")
        
        assert script["script_id"] == "test_script_456"
        assert script["name"] == "Test Script"
        mock_script_api.add_script.assert_called_once()
    
    @pytest.mark.async
    async def test_delete_script(self, mock_script_api):
        """Test deleting a script"""
        mock_script_api.delete_script.return_value = True
        
        result = await mock_script_api.delete_script("test_script_456")
        
        assert result is True
        mock_script_api.delete_script.assert_called_once_with("test_script_456")


class TestMarketAPI:
    """Test cases for MarketAPI"""
    
    @pytest.mark.async
    async def test_market_api_initialization(self, mock_async_client_wrapper):
        """Test market API initialization"""
        market_api = MarketAPI(mock_async_client_wrapper)
        assert market_api.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_get_trade_markets(self, mock_market_api):
        """Test getting trade markets"""
        mock_market_api.get_trade_markets.return_value = [{"market_tag": "BTC_USDT_PERPETUAL", "price": 50000.0}]
        
        markets = await mock_market_api.get_trade_markets()
        
        assert len(markets) == 1
        assert markets[0]["market_tag"] == "BTC_USDT_PERPETUAL"
        assert markets[0]["price"] == 50000.0
    
    @pytest.mark.async
    async def test_get_price_data(self, mock_market_api):
        """Test getting price data"""
        mock_market_api.get_price_data.return_value = {"market_tag": "BTC_USDT_PERPETUAL", "price": 50000.0}
        
        price_data = await mock_market_api.get_price_data("BTC_USDT_PERPETUAL")
        
        assert price_data["market_tag"] == "BTC_USDT_PERPETUAL"
        assert price_data["price"] == 50000.0
        mock_market_api.get_price_data.assert_called_once_with("BTC_USDT_PERPETUAL")
    
    @pytest.mark.async
    async def test_validate_market(self, mock_market_api):
        """Test validating a market"""
        mock_market_api.validate_market.return_value = True
        
        result = await mock_market_api.validate_market("BTC_USDT_PERPETUAL")
        
        assert result is True
        mock_market_api.validate_market.assert_called_once_with("BTC_USDT_PERPETUAL")


class TestBacktestAPI:
    """Test cases for BacktestAPI"""
    
    @pytest.mark.async
    async def test_backtest_api_initialization(self, mock_async_client_wrapper):
        """Test backtest API initialization"""
        backtest_api = BacktestAPI(mock_async_client_wrapper)
        assert backtest_api.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_get_backtest_result(self, mock_backtest_api):
        """Test getting backtest result"""
        mock_backtest_api.get_backtest_result.return_value = [{"backtest_id": "test_backtest_202", "roi": 150.5}]
        
        backtests = await mock_backtest_api.get_backtest_result("test_lab_123")
        
        assert len(backtests) == 1
        assert backtests[0]["backtest_id"] == "test_backtest_202"
        assert backtests[0]["roi"] == 150.5
        mock_backtest_api.get_backtest_result.assert_called_once_with("test_lab_123")
    
    @pytest.mark.async
    async def test_get_backtest_runtime(self, mock_backtest_api):
        """Test getting backtest runtime data"""
        mock_backtest_api.get_backtest_runtime.return_value = {"backtest_id": "test_backtest_202", "status": "completed"}
        
        runtime_data = await mock_backtest_api.get_backtest_runtime("test_backtest_202")
        
        assert runtime_data["backtest_id"] == "test_backtest_202"
        assert runtime_data["status"] == "completed"
        mock_backtest_api.get_backtest_runtime.assert_called_once_with("test_backtest_202")
    
    @pytest.mark.async
    async def test_execute_backtest(self, mock_backtest_api):
        """Test executing a backtest"""
        mock_backtest_api.execute_backtest.return_value = True
        
        result = await mock_backtest_api.execute_backtest("test_lab_123", "test_script_456")
        
        assert result is True
        mock_backtest_api.execute_backtest.assert_called_once_with("test_lab_123", "test_script_456")


class TestOrderAPI:
    """Test cases for OrderAPI"""
    
    @pytest.mark.async
    async def test_order_api_initialization(self, mock_async_client_wrapper):
        """Test order API initialization"""
        order_api = OrderAPI(mock_async_client_wrapper)
        assert order_api.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_place_order(self, mock_order_api):
        """Test placing an order"""
        mock_order_api.place_order.return_value = {"order_id": "test_order_303", "status": "filled"}
        
        order = await mock_order_api.place_order("test_bot_789", "buy", 1000.0, 50000.0)
        
        assert order["order_id"] == "test_order_303"
        assert order["status"] == "filled"
        mock_order_api.place_order.assert_called_once()
    
    @pytest.mark.async
    async def test_cancel_order(self, mock_order_api):
        """Test canceling an order"""
        mock_order_api.cancel_order.return_value = True
        
        result = await mock_order_api.cancel_order("test_order_303")
        
        assert result is True
        mock_order_api.cancel_order.assert_called_once_with("test_order_303")
    
    @pytest.mark.async
    async def test_get_order_status(self, mock_order_api):
        """Test getting order status"""
        mock_order_api.get_order_status.return_value = {"order_id": "test_order_303", "status": "filled"}
        
        status = await mock_order_api.get_order_status("test_order_303")
        
        assert status["order_id"] == "test_order_303"
        assert status["status"] == "filled"
        mock_order_api.get_order_status.assert_called_once_with("test_order_303")
    
    @pytest.mark.async
    async def test_get_bot_orders(self, mock_order_api):
        """Test getting bot orders"""
        mock_order_api.get_bot_orders.return_value = [{"order_id": "test_order_303", "bot_id": "test_bot_789"}]
        
        orders = await mock_order_api.get_bot_orders("test_bot_789")
        
        assert len(orders) == 1
        assert orders[0]["order_id"] == "test_order_303"
        assert orders[0]["bot_id"] == "test_bot_789"
        mock_order_api.get_bot_orders.assert_called_once_with("test_bot_789")
