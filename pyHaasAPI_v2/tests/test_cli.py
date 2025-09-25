"""
Unit tests for pyHaasAPI v2 CLI modules

This module provides comprehensive unit tests for all CLI components
including BaseCLI, LabCLI, BotCLI, and AnalysisCLI.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from ..cli.base import BaseCLI, AsyncBaseCLI, CLIConfig
from ..cli.lab_cli import LabCLI
from ..cli.bot_cli import BotCLI
from ..cli.analysis_cli import AnalysisCLI


class TestBaseCLI:
    """Test cases for BaseCLI"""
    
    def test_base_cli_initialization(self):
        """Test base CLI initialization"""
        config = CLIConfig(host="127.0.0.1", port=8090, timeout=30.0)
        cli = BaseCLI(config)
        
        assert cli.config == config
        assert cli.client is None
        assert cli.auth_manager is None
        assert cli.async_client is None
        assert cli.lab_api is None
        assert cli.bot_api is None
        assert cli.account_api is None
        assert cli.script_api is None
        assert cli.market_api is None
        assert cli.backtest_api is None
        assert cli.order_api is None
        assert cli.lab_service is None
        assert cli.bot_service is None
        assert cli.analysis_service is None
        assert cli.reporting_service is None
        assert cli.data_dumper is None
        assert cli.testing_manager is None
    
    def test_cli_config_defaults(self):
        """Test CLI config defaults"""
        config = CLIConfig()
        
        assert config.host == "127.0.0.1"
        assert config.port == 8090
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.verify_ssl is True
        assert config.enable_caching is True
        assert config.cache_ttl == 300.0
        assert config.enable_rate_limiting is True
        assert config.max_concurrent_requests == 10
        assert config.log_level == "INFO"
        assert config.strict_mode is False
    
    @pytest.mark.async
    async def test_connect_success(self, mock_async_client, mock_auth_manager):
        """Test successful connection"""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda key: {
                'API_EMAIL': 'test@example.com',
                'API_PASSWORD': 'test_password'
            }.get(key)
            
            config = CLIConfig()
            cli = BaseCLI(config)
            
            # Mock the client and auth manager creation
            with patch('pyHaasAPI_v2.core.client.AsyncHaasClient') as mock_client_class:
                with patch('pyHaasAPI_v2.core.auth.AuthenticationManager') as mock_auth_class:
                    with patch('pyHaasAPI_v2.core.async_client.AsyncHaasClientWrapper') as mock_wrapper_class:
                        mock_client_class.return_value = mock_async_client
                        mock_auth_class.return_value = mock_auth_manager
                        mock_wrapper_class.return_value = AsyncMock()
                        
                        result = await cli.connect()
                        
                        assert result is True
                        assert cli.client == mock_async_client
                        assert cli.auth_manager == mock_auth_manager
    
    @pytest.mark.async
    async def test_connect_failure_no_credentials(self):
        """Test connection failure due to missing credentials"""
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            
            config = CLIConfig()
            cli = BaseCLI(config)
            
            result = await cli.connect()
            
            assert result is False
    
    @pytest.mark.async
    async def test_disconnect(self, mock_async_client, mock_auth_manager):
        """Test disconnection"""
        config = CLIConfig()
        cli = BaseCLI(config)
        cli.async_client = AsyncMock()
        cli.auth_manager = mock_auth_manager
        
        await cli.disconnect()
        
        cli.async_client.__aexit__.assert_called_once()
        mock_auth_manager.logout.assert_called_once()
    
    @pytest.mark.async
    async def test_health_check(self, mock_async_client_wrapper):
        """Test health check"""
        config = CLIConfig()
        cli = BaseCLI(config)
        cli.async_client = mock_async_client_wrapper
        cli.lab_api = AsyncMock()
        cli.lab_api.get_labs = AsyncMock(return_value=[])
        
        health = await cli.health_check()
        
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert "components" in health
    
    def test_create_parser(self):
        """Test parser creation"""
        config = CLIConfig()
        cli = BaseCLI(config)
        
        parser = cli.create_parser("Test CLI")
        
        assert parser.description == "Test CLI"
        assert parser.prog == "Test CLI"
    
    def test_update_config_from_args(self):
        """Test config update from arguments"""
        config = CLIConfig()
        cli = BaseCLI(config)
        
        # Mock args object
        args = MagicMock()
        args.host = "192.168.1.1"
        args.port = 9000
        args.timeout = 60.0
        args.log_level = "DEBUG"
        args.strict_mode = True
        
        cli.update_config_from_args(args)
        
        assert cli.config.host == "192.168.1.1"
        assert cli.config.port == 9000
        assert cli.config.timeout == 60.0
        assert cli.config.log_level == "DEBUG"
        assert cli.config.strict_mode is True


class TestAsyncBaseCLI:
    """Test cases for AsyncBaseCLI"""
    
    def test_async_base_cli_initialization(self):
        """Test async base CLI initialization"""
        config = CLIConfig()
        cli = AsyncBaseCLI(config)
        
        assert cli.config == config
        assert cli.event_loop is None
    
    @pytest.mark.async
    async def test_run_async(self):
        """Test running async function"""
        config = CLIConfig()
        cli = AsyncBaseCLI(config)
        
        async def test_func():
            return "test_result"
        
        result = await cli.run_async(test_func)
        
        assert result == "test_result"
    
    @pytest.mark.async
    async def test_run_concurrent(self):
        """Test running concurrent tasks"""
        config = CLIConfig()
        cli = AsyncBaseCLI(config)
        
        async def task1():
            return "result1"
        
        async def task2():
            return "result2"
        
        tasks = [task1, task2]
        results = await cli.run_concurrent(tasks, max_concurrent=2)
        
        assert len(results) == 2
        assert results[0] == "result1"
        assert results[1] == "result2"
    
    @pytest.mark.async
    async def test_run_with_progress(self):
        """Test running tasks with progress tracking"""
        config = CLIConfig()
        cli = AsyncBaseCLI(config)
        
        async def task1():
            return "result1"
        
        async def task2():
            return "result2"
        
        tasks = [task1, task2]
        results = await cli.run_with_progress(tasks, "Processing")
        
        assert len(results) == 2
        assert results[0] == "result1"
        assert results[1] == "result2"


class TestLabCLI:
    """Test cases for LabCLI"""
    
    def test_lab_cli_initialization(self):
        """Test lab CLI initialization"""
        config = CLIConfig()
        cli = LabCLI(config)
        
        assert cli.config == config
        assert cli.logger is not None
    
    @pytest.mark.async
    async def test_list_labs_success(self, mock_lab_api):
        """Test successful lab listing"""
        config = CLIConfig()
        cli = LabCLI(config)
        cli.lab_api = mock_lab_api
        
        mock_lab_api.get_labs.return_value = [{"lab_id": "test_lab_123", "name": "Test Lab"}]
        
        # Mock args
        args = MagicMock()
        args.output_format = "table"
        args.output_file = None
        
        result = await cli.list_labs(args)
        
        assert result == 0
        mock_lab_api.get_labs.assert_called_once()
    
    @pytest.mark.async
    async def test_list_labs_no_labs(self, mock_lab_api):
        """Test lab listing with no labs"""
        config = CLIConfig()
        cli = LabCLI(config)
        cli.lab_api = mock_lab_api
        
        mock_lab_api.get_labs.return_value = []
        
        # Mock args
        args = MagicMock()
        args.output_format = "table"
        args.output_file = None
        
        result = await cli.list_labs(args)
        
        assert result == 0
        mock_lab_api.get_labs.assert_called_once()
    
    @pytest.mark.async
    async def test_create_lab_success(self, mock_lab_api):
        """Test successful lab creation"""
        config = CLIConfig()
        cli = LabCLI(config)
        cli.lab_api = mock_lab_api
        
        mock_lab_api.create_lab.return_value = {"lab_id": "test_lab_123", "name": "Test Lab"}
        
        # Mock args
        args = MagicMock()
        args.name = "Test Lab"
        args.script_id = "script_123"
        args.description = "Test description"
        
        result = await cli.create_lab(args)
        
        assert result == 0
        mock_lab_api.create_lab.assert_called_once_with("Test Lab", "script_123", "Test description")
    
    @pytest.mark.async
    async def test_create_lab_missing_args(self, mock_lab_api):
        """Test lab creation with missing arguments"""
        config = CLIConfig()
        cli = LabCLI(config)
        cli.lab_api = mock_lab_api
        
        # Mock args
        args = MagicMock()
        args.name = None
        args.script_id = None
        args.description = None
        
        result = await cli.create_lab(args)
        
        assert result == 1
        mock_lab_api.create_lab.assert_not_called()
    
    @pytest.mark.async
    async def test_delete_lab_success(self, mock_lab_api):
        """Test successful lab deletion"""
        config = CLIConfig()
        cli = LabCLI(config)
        cli.lab_api = mock_lab_api
        
        mock_lab_api.delete_lab.return_value = True
        
        # Mock args
        args = MagicMock()
        args.lab_id = "test_lab_123"
        
        result = await cli.delete_lab(args)
        
        assert result == 0
        mock_lab_api.delete_lab.assert_called_once_with("test_lab_123")
    
    @pytest.mark.async
    async def test_delete_lab_missing_id(self, mock_lab_api):
        """Test lab deletion with missing ID"""
        config = CLIConfig()
        cli = LabCLI(config)
        cli.lab_api = mock_lab_api
        
        # Mock args
        args = MagicMock()
        args.lab_id = None
        
        result = await cli.delete_lab(args)
        
        assert result == 1
        mock_lab_api.delete_lab.assert_not_called()


class TestBotCLI:
    """Test cases for BotCLI"""
    
    def test_bot_cli_initialization(self):
        """Test bot CLI initialization"""
        config = CLIConfig()
        cli = BotCLI(config)
        
        assert cli.config == config
        assert cli.logger is not None
    
    @pytest.mark.async
    async def test_list_bots_success(self, mock_bot_api):
        """Test successful bot listing"""
        config = CLIConfig()
        cli = BotCLI(config)
        cli.bot_api = mock_bot_api
        
        mock_bot_api.get_all_bots.return_value = [{"bot_id": "test_bot_789", "name": "Test Bot"}]
        
        # Mock args
        args = MagicMock()
        args.output_format = "table"
        args.output_file = None
        args.status = None
        
        result = await cli.list_bots(args)
        
        assert result == 0
        mock_bot_api.get_all_bots.assert_called_once()
    
    @pytest.mark.async
    async def test_create_bots_success(self, mock_bot_api):
        """Test successful bot creation"""
        config = CLIConfig()
        cli = BotCLI(config)
        cli.bot_api = mock_bot_api
        
        mock_bot_api.create_bot.return_value = {"bot_id": "test_bot_789", "name": "Test Bot"}
        
        # Mock args
        args = MagicMock()
        args.from_lab = "test_lab_123"
        args.count = 1
        args.activate = False
        
        result = await cli.create_bots(args)
        
        assert result == 0
        mock_bot_api.create_bot.assert_called_once()
    
    @pytest.mark.async
    async def test_create_bots_missing_lab(self, mock_bot_api):
        """Test bot creation with missing lab ID"""
        config = CLIConfig()
        cli = BotCLI(config)
        cli.bot_api = mock_bot_api
        
        # Mock args
        args = MagicMock()
        args.from_lab = None
        args.count = 1
        args.activate = False
        
        result = await cli.create_bots(args)
        
        assert result == 1
        mock_bot_api.create_bot.assert_not_called()
    
    @pytest.mark.async
    async def test_activate_bots_success(self, mock_bot_api):
        """Test successful bot activation"""
        config = CLIConfig()
        cli = BotCLI(config)
        cli.bot_api = mock_bot_api
        
        mock_bot_api.activate_bot.return_value = True
        
        # Mock args
        args = MagicMock()
        args.bot_ids = "test_bot_789,test_bot_790"
        args.all = False
        
        result = await cli.activate_bots(args)
        
        assert result == 0
        mock_bot_api.activate_bot.assert_called()
    
    @pytest.mark.async
    async def test_activate_bots_missing_ids(self, mock_bot_api):
        """Test bot activation with missing IDs"""
        config = CLIConfig()
        cli = BotCLI(config)
        cli.bot_api = mock_bot_api
        
        # Mock args
        args = MagicMock()
        args.bot_ids = None
        args.all = False
        
        result = await cli.activate_bots(args)
        
        assert result == 1
        mock_bot_api.activate_bot.assert_not_called()


class TestAnalysisCLI:
    """Test cases for AnalysisCLI"""
    
    def test_analysis_cli_initialization(self):
        """Test analysis CLI initialization"""
        config = CLIConfig()
        cli = AnalysisCLI(config)
        
        assert cli.config == config
        assert cli.logger is not None
    
    @pytest.mark.async
    async def test_analyze_labs_success(self, mock_analysis_service):
        """Test successful lab analysis"""
        config = CLIConfig()
        cli = AnalysisCLI(config)
        cli.analysis_service = mock_analysis_service
        
        mock_analysis_service.analyze_lab_comprehensive.return_value = {
            "success": True,
            "lab_id": "test_lab_123",
            "lab_name": "Test Lab",
            "total_backtests": 10,
            "average_roi": 100.0,
            "best_roi": 200.0,
            "average_win_rate": 0.6,
            "top_performers": [{"backtest_id": "test_backtest_202", "roi_percentage": 150.5}]
        }
        
        # Mock args
        args = MagicMock()
        args.lab_id = "test_lab_123"
        args.top_count = 5
        args.generate_reports = False
        args.output_format = "table"
        args.output_file = None
        
        result = await cli.analyze_labs(args)
        
        assert result == 0
        mock_analysis_service.analyze_lab_comprehensive.assert_called_once()
    
    @pytest.mark.async
    async def test_analyze_labs_missing_id(self, mock_analysis_service):
        """Test lab analysis with missing ID"""
        config = CLIConfig()
        cli = AnalysisCLI(config)
        cli.analysis_service = mock_analysis_service
        
        # Mock args
        args = MagicMock()
        args.lab_id = None
        args.top_count = 5
        args.generate_reports = False
        args.output_format = "table"
        args.output_file = None
        
        result = await cli.analyze_labs(args)
        
        assert result == 1
        mock_analysis_service.analyze_lab_comprehensive.assert_not_called()
    
    @pytest.mark.async
    async def test_analyze_bots_success(self, mock_analysis_service):
        """Test successful bot analysis"""
        config = CLIConfig()
        cli = AnalysisCLI(config)
        cli.analysis_service = mock_analysis_service
        
        mock_analysis_service.analyze_bot.return_value = {"success": True, "data": {"bot_id": "test_bot_789", "status": "active"}}
        
        # Mock args
        args = MagicMock()
        args.bot_id = "test_bot_789"
        args.generate_reports = False
        args.output_format = "table"
        args.output_file = None
        
        result = await cli.analyze_bots(args)
        
        assert result == 0
        mock_analysis_service.analyze_bot.assert_called_once()
    
    @pytest.mark.async
    async def test_analyze_wfo_success(self, mock_analysis_service):
        """Test successful WFO analysis"""
        config = CLIConfig()
        cli = AnalysisCLI(config)
        cli.analysis_service = mock_analysis_service
        
        mock_analysis_service.analyze_wfo.return_value = {"success": True, "data": {"lab_id": "test_lab_123", "periods": 5}}
        
        # Mock args
        args = MagicMock()
        args.lab_id = "test_lab_123"
        args.start_date = "2022-01-01"
        args.end_date = "2023-12-31"
        args.generate_reports = False
        args.output_format = "table"
        args.output_file = None
        
        result = await cli.analyze_wfo(args)
        
        assert result == 0
        mock_analysis_service.analyze_wfo.assert_called_once()
    
    @pytest.mark.async
    async def test_analyze_wfo_missing_args(self, mock_analysis_service):
        """Test WFO analysis with missing arguments"""
        config = CLIConfig()
        cli = AnalysisCLI(config)
        cli.analysis_service = mock_analysis_service
        
        # Mock args
        args = MagicMock()
        args.lab_id = None
        args.start_date = None
        args.end_date = None
        args.generate_reports = False
        args.output_format = "table"
        args.output_file = None
        
        result = await cli.analyze_wfo(args)
        
        assert result == 1
        mock_analysis_service.analyze_wfo.assert_not_called()
