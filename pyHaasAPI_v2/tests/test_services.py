"""
Unit tests for pyHaasAPI v2 service modules

This module provides comprehensive unit tests for all service components
including Lab, Bot, Analysis, and Reporting services.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from ..services.lab import LabService
from ..services.bot import BotService
from ..services.analysis import AnalysisService
from ..services.reporting import ReportingService


class TestLabService:
    """Test cases for LabService"""
    
    @pytest.mark.async
    async def test_lab_service_initialization(self, mock_lab_api, mock_backtest_api, mock_script_api, mock_account_api):
        """Test lab service initialization"""
        service = LabService(mock_lab_api, mock_backtest_api, mock_script_api, mock_account_api)
        assert service.lab_api == mock_lab_api
        assert service.backtest_api == mock_backtest_api
        assert service.script_api == mock_script_api
        assert service.account_api == mock_account_api
    
    @pytest.mark.async
    async def test_get_all_labs(self, mock_lab_service):
        """Test getting all labs"""
        mock_lab_service.get_all_labs.return_value = [{"lab_id": "test_lab_123", "name": "Test Lab"}]
        
        labs = await mock_lab_service.get_all_labs()
        
        assert len(labs) == 1
        assert labs[0]["lab_id"] == "test_lab_123"
        assert labs[0]["name"] == "Test Lab"
    
    @pytest.mark.async
    async def test_create_lab(self, mock_lab_service):
        """Test creating a lab"""
        mock_lab_service.create_lab.return_value = {"success": True, "data": {"lab_id": "test_lab_123", "name": "Test Lab"}}
        
        result = await mock_lab_service.create_lab("Test Lab", "script_123", "Test description")
        
        assert result["success"] is True
        assert result["data"]["lab_id"] == "test_lab_123"
        assert result["data"]["name"] == "Test Lab"
    
    @pytest.mark.async
    async def test_delete_lab(self, mock_lab_service):
        """Test deleting a lab"""
        mock_lab_service.delete_lab.return_value = {"success": True}
        
        result = await mock_lab_service.delete_lab("test_lab_123")
        
        assert result["success"] is True
    
    @pytest.mark.async
    async def test_execute_lab(self, mock_lab_service):
        """Test executing a lab"""
        mock_lab_service.execute_lab.return_value = {"success": True, "data": {"lab_id": "test_lab_123", "status": "running"}}
        
        result = await mock_lab_service.execute_lab("test_lab_123")
        
        assert result["success"] is True
        assert result["data"]["lab_id"] == "test_lab_123"
        assert result["data"]["status"] == "running"
    
    @pytest.mark.async
    async def test_get_lab_status(self, mock_lab_service):
        """Test getting lab status"""
        mock_lab_service.get_lab_status.return_value = {"success": True, "data": {"lab_id": "test_lab_123", "status": "completed"}}
        
        result = await mock_lab_service.get_lab_status("test_lab_123")
        
        assert result["success"] is True
        assert result["data"]["lab_id"] == "test_lab_123"
        assert result["data"]["status"] == "completed"


class TestBotService:
    """Test cases for BotService"""
    
    @pytest.mark.async
    async def test_bot_service_initialization(self, mock_bot_api, mock_account_api, mock_backtest_api, mock_market_api, mock_async_client, mock_auth_manager):
        """Test bot service initialization"""
        service = BotService(mock_bot_api, mock_account_api, mock_backtest_api, mock_market_api, mock_async_client, mock_auth_manager)
        assert service.bot_api == mock_bot_api
        assert service.account_api == mock_account_api
        assert service.backtest_api == mock_backtest_api
        assert service.market_api == mock_market_api
        assert service.client == mock_async_client
        assert service.auth_manager == mock_auth_manager
    
    @pytest.mark.async
    async def test_get_all_bots(self, mock_bot_service):
        """Test getting all bots"""
        mock_bot_service.get_all_bots.return_value = [{"bot_id": "test_bot_789", "name": "Test Bot"}]
        
        bots = await mock_bot_service.get_all_bots()
        
        assert len(bots) == 1
        assert bots[0]["bot_id"] == "test_bot_789"
        assert bots[0]["name"] == "Test Bot"
    
    @pytest.mark.async
    async def test_create_bot(self, mock_bot_service):
        """Test creating a bot"""
        mock_bot_service.create_bot.return_value = {"success": True, "data": {"bot_id": "test_bot_789", "name": "Test Bot"}}
        
        result = await mock_bot_service.create_bot("Test Bot", "account_123", "BTC_USDT_PERPETUAL")
        
        assert result["success"] is True
        assert result["data"]["bot_id"] == "test_bot_789"
        assert result["data"]["name"] == "Test Bot"
    
    @pytest.mark.async
    async def test_delete_bot(self, mock_bot_service):
        """Test deleting a bot"""
        mock_bot_service.delete_bot.return_value = {"success": True}
        
        result = await mock_bot_service.delete_bot("test_bot_789")
        
        assert result["success"] is True
    
    @pytest.mark.async
    async def test_activate_bot(self, mock_bot_service):
        """Test activating a bot"""
        mock_bot_service.activate_bot.return_value = {"success": True}
        
        result = await mock_bot_service.activate_bot("test_bot_789")
        
        assert result["success"] is True
    
    @pytest.mark.async
    async def test_deactivate_bot(self, mock_bot_service):
        """Test deactivating a bot"""
        mock_bot_service.deactivate_bot.return_value = {"success": True}
        
        result = await mock_bot_service.deactivate_bot("test_bot_789")
        
        assert result["success"] is True
    
    @pytest.mark.async
    async def test_pause_bot(self, mock_bot_service):
        """Test pausing a bot"""
        mock_bot_service.pause_bot.return_value = {"success": True}
        
        result = await mock_bot_service.pause_bot("test_bot_789")
        
        assert result["success"] is True
    
    @pytest.mark.async
    async def test_resume_bot(self, mock_bot_service):
        """Test resuming a bot"""
        mock_bot_service.resume_bot.return_value = {"success": True}
        
        result = await mock_bot_service.resume_bot("test_bot_789")
        
        assert result["success"] is True


class TestAnalysisService:
    """Test cases for AnalysisService"""
    
    @pytest.mark.async
    async def test_analysis_service_initialization(self, mock_lab_api, mock_backtest_api, mock_bot_api, mock_async_client, mock_auth_manager):
        """Test analysis service initialization"""
        service = AnalysisService(mock_lab_api, mock_backtest_api, mock_bot_api, mock_async_client, mock_auth_manager)
        assert service.lab_api == mock_lab_api
        assert service.backtest_api == mock_backtest_api
        assert service.bot_api == mock_bot_api
        assert service.client == mock_async_client
        assert service.auth_manager == mock_auth_manager
    
    @pytest.mark.async
    async def test_analyze_lab_comprehensive(self, mock_analysis_service):
        """Test comprehensive lab analysis"""
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
        
        result = await mock_analysis_service.analyze_lab_comprehensive("test_lab_123", 5)
        
        assert result["success"] is True
        assert result["lab_id"] == "test_lab_123"
        assert result["lab_name"] == "Test Lab"
        assert result["total_backtests"] == 10
        assert result["average_roi"] == 100.0
        assert result["best_roi"] == 200.0
        assert result["average_win_rate"] == 0.6
        assert len(result["top_performers"]) == 1
    
    @pytest.mark.async
    async def test_analyze_bot(self, mock_analysis_service):
        """Test bot analysis"""
        mock_analysis_service.analyze_bot.return_value = {"success": True, "data": {"bot_id": "test_bot_789", "status": "active"}}
        
        result = await mock_analysis_service.analyze_bot("test_bot_789")
        
        assert result["success"] is True
        assert result["data"]["bot_id"] == "test_bot_789"
        assert result["data"]["status"] == "active"
    
    @pytest.mark.async
    async def test_analyze_wfo(self, mock_analysis_service):
        """Test Walk Forward Optimization analysis"""
        mock_analysis_service.analyze_wfo.return_value = {"success": True, "data": {"lab_id": "test_lab_123", "periods": 5}}
        
        result = await mock_analysis_service.analyze_wfo("test_lab_123", "2022-01-01", "2023-12-31")
        
        assert result["success"] is True
        assert result["data"]["lab_id"] == "test_lab_123"
        assert result["data"]["periods"] == 5
    
    @pytest.mark.async
    async def test_get_performance_metrics(self, mock_analysis_service):
        """Test getting performance metrics"""
        mock_analysis_service.get_performance_metrics.return_value = {"success": True, "data": {"total_requests": 100, "success_rate": 0.95}}
        
        result = await mock_analysis_service.get_performance_metrics()
        
        assert result["success"] is True
        assert result["data"]["total_requests"] == 100
        assert result["data"]["success_rate"] == 0.95


class TestReportingService:
    """Test cases for ReportingService"""
    
    def test_reporting_service_initialization(self):
        """Test reporting service initialization"""
        service = ReportingService()
        assert service is not None
    
    @pytest.mark.async
    async def test_generate_analysis_report(self, mock_reporting_service):
        """Test generating analysis report"""
        mock_reporting_service.generate_analysis_report.return_value = {"report_path": "/tmp/test_report.csv"}
        
        result = await mock_reporting_service.generate_analysis_report([{"lab_id": "test_lab_123"}], "lab_analysis", "csv")
        
        assert result["report_path"] == "/tmp/test_report.csv"
    
    @pytest.mark.async
    async def test_generate_bot_recommendations_report(self, mock_reporting_service):
        """Test generating bot recommendations report"""
        mock_reporting_service.generate_bot_recommendations_report.return_value = {"report_path": "/tmp/test_bot_report.csv"}
        
        result = await mock_reporting_service.generate_bot_recommendations_report([{"bot_id": "test_bot_789"}], "bot_recommendations", "csv")
        
        assert result["report_path"] == "/tmp/test_bot_report.csv"
    
    @pytest.mark.async
    async def test_generate_wfo_report(self, mock_reporting_service):
        """Test generating WFO report"""
        mock_reporting_service.generate_wfo_report.return_value = {"report_path": "/tmp/test_wfo_report.csv"}
        
        result = await mock_reporting_service.generate_wfo_report({"lab_id": "test_lab_123", "periods": 5}, "wfo_analysis", "csv")
        
        assert result["report_path"] == "/tmp/test_wfo_report.csv"
    
    @pytest.mark.async
    async def test_generate_performance_report(self, mock_reporting_service):
        """Test generating performance report"""
        mock_reporting_service.generate_performance_report.return_value = {"report_path": "/tmp/test_performance_report.csv"}
        
        result = await mock_reporting_service.generate_performance_report({"total_requests": 100, "success_rate": 0.95}, "performance_analysis", "csv")
        
        assert result["report_path"] == "/tmp/test_performance_report.csv"