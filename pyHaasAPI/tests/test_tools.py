"""
Unit tests for pyHaasAPI v2 tools modules

This module provides comprehensive unit tests for all tools components
including DataDumper and TestingManager.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from ..tools.data_dumper import DataDumper
from ..tools.testing_manager import TestingManager


class TestDataDumper:
    """Test cases for DataDumper"""
    
    @pytest.mark.async
    async def test_data_dumper_initialization(self, mock_async_client_wrapper):
        """Test data dumper initialization"""
        dumper = DataDumper(mock_async_client_wrapper)
        assert dumper.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_dump_data(self, mock_data_dumper):
        """Test dumping data"""
        mock_data_dumper.dump_data.return_value = {"success": True, "files": ["/tmp/test_dump.json"]}
        
        result = await mock_data_dumper.dump_data("labs", "json", "/tmp")
        
        assert result["success"] is True
        assert len(result["files"]) == 1
        assert result["files"][0] == "/tmp/test_dump.json"
    
    @pytest.mark.async
    async def test_dump_labs(self, mock_data_dumper):
        """Test dumping labs data"""
        mock_data_dumper.dump_labs.return_value = {"success": True, "files": ["/tmp/labs.json"]}
        
        result = await mock_data_dumper.dump_labs("json", "/tmp")
        
        assert result["success"] is True
        assert len(result["files"]) == 1
        assert result["files"][0] == "/tmp/labs.json"
    
    @pytest.mark.async
    async def test_dump_bots(self, mock_data_dumper):
        """Test dumping bots data"""
        mock_data_dumper.dump_bots.return_value = {"success": True, "files": ["/tmp/bots.json"]}
        
        result = await mock_data_dumper.dump_bots("json", "/tmp")
        
        assert result["success"] is True
        assert len(result["files"]) == 1
        assert result["files"][0] == "/tmp/bots.json"
    
    @pytest.mark.async
    async def test_dump_accounts(self, mock_data_dumper):
        """Test dumping accounts data"""
        mock_data_dumper.dump_accounts.return_value = {"success": True, "files": ["/tmp/accounts.json"]}
        
        result = await mock_data_dumper.dump_accounts("json", "/tmp")
        
        assert result["success"] is True
        assert len(result["files"]) == 1
        assert result["files"][0] == "/tmp/accounts.json"


class TestTestingManager:
    """Test cases for TestingManager"""
    
    @pytest.mark.async
    async def test_testing_manager_initialization(self, mock_async_client_wrapper):
        """Test testing manager initialization"""
        manager = TestingManager(mock_async_client_wrapper)
        assert manager.client == mock_async_client_wrapper
    
    @pytest.mark.async
    async def test_create_test_data(self, mock_testing_manager):
        """Test creating test data"""
        mock_testing_manager.create_test_data.return_value = {"success": True, "data": {"labs": 1, "bots": 1, "accounts": 1}}
        
        result = await mock_testing_manager.create_test_data("all", 1)
        
        assert result["success"] is True
        assert result["data"]["labs"] == 1
        assert result["data"]["bots"] == 1
        assert result["data"]["accounts"] == 1
    
    @pytest.mark.async
    async def test_cleanup_test_data(self, mock_testing_manager):
        """Test cleaning up test data"""
        mock_testing_manager.cleanup_test_data.return_value = {"success": True, "cleaned": {"labs": 1, "bots": 1, "accounts": 1}}
        
        result = await mock_testing_manager.cleanup_test_data("all")
        
        assert result["success"] is True
        assert result["cleaned"]["labs"] == 1
        assert result["cleaned"]["bots"] == 1
        assert result["cleaned"]["accounts"] == 1
    
    @pytest.mark.async
    async def test_validate_test_data(self, mock_testing_manager):
        """Test validating test data"""
        mock_testing_manager.validate_test_data.return_value = {"success": True, "valid": True}
        
        result = await mock_testing_manager.validate_test_data("all")
        
        assert result["success"] is True
        assert result["valid"] is True
    
    @pytest.mark.async
    async def test_isolate_test_data(self, mock_testing_manager):
        """Test isolating test data"""
        mock_testing_manager.isolate_test_data.return_value = {"success": True, "isolated": True}
        
        result = await mock_testing_manager.isolate_test_data("all")
        
        assert result["success"] is True
        assert result["isolated"] is True
