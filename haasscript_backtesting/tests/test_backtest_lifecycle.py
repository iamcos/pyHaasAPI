"""
Tests for backtest lifecycle management functionality.
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time

from ..backtest_manager.backtest_manager import BacktestManager, BacktestConfigValidator
from ..models import BacktestConfig, BacktestExecution, ExecutionStatus, ExecutionStatusType, PositionMode
from ..config import ConfigManager
from ..api_client import HaasOnlineClient


class TestBacktestLifecycleManagement(unittest.TestCase):
    """Test backtest lifecycle management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock configuration
        self.mock_config = Mock(spec=ConfigManager)
        self.mock_config.system.execution.max_concurrent_backtests = 3
        
        # Mock API client
        self.mock_api_client = Mock(spec=HaasOnlineClient)
        
        # Create backtest manager
        self.manager = BacktestManager(self.mock_config, self.mock_api_client)
        
        # Sample backtest configuration
        self.sample_config = BacktestConfig(
            script_id="test_script_123",
            account_id="test_account_456",
            market_tag="BTCUSDT",
            start_time=int((datetime.now() - timedelta(days=30)).timestamp()),
            end_time=int((datetime.now() - timedelta(days=1)).timestamp()),
            interval=60,
            execution_amount=1000.0,
            script_parameters={"param1": 10, "param2": 0.5},
            leverage=1,
            position_mode=PositionMode.LONG_ONLY
        )
    
    def tearDown(self):
        """Clean up after tests."""
        self.manager.stop_monitoring()
    
    def test_archive_backtest_success(self):
        """Test successful backtest archiving."""
        # Create a completed execution
        execution = self._create_completed_execution()
        self.manager._active_executions[execution.backtest_id] = execution
        
        # Mock API response
        self.mock_api_client.__enter__ = Mock(return_value=self.mock_api_client)
        self.mock_api_client.__exit__ = Mock(return_value=None)
        
        # Mock the archive API call
        with patch.object(self.manager, '_archive_backtest_via_api', return_value=True):
            result = self.manager.archive_backtest(execution.backtest_id)
        
        self.assertTrue(result)
        self.assertEqual(execution.status.status, ExecutionStatusType.ARCHIVED)
        self.assertEqual(len(self.manager._execution_history), 1)
    
    def test_archive_backtest_with_preserve_results(self):
        """Test archiving with result preservation."""
        execution = self._create_completed_execution()
        self.manager._active_executions[execution.backtest_id] = execution
        
        # Mock API responses
        mock_runtime_response = Mock()
        mock_runtime_response.backtest_id = execution.backtest_id
        mock_runtime_response.status = Mock()
        mock_runtime_response.status.value = "completed"
        
        self.mock_api_client.__enter__ = Mock(return_value=self.mock_api_client)
        self.mock_api_client.__exit__ = Mock(return_value=None)
        self.mock_api_client.get_backtest_runtime.return_value = mock_runtime_response
        
        with patch.object(self.manager, '_archive_backtest_via_api', return_value=True):
            result = self.manager.archive_backtest(execution.backtest_id, preserve_results=True)
        
        self.assertTrue(result)
    
    def test_delete_backtest_success(self):
        """Test successful backtest deletion."""
        execution = self._create_completed_execution()
        self.manager._active_executions[execution.backtest_id] = execution
        
        with patch.object(self.manager, '_delete_backtest_via_api', return_value=True):
            result = self.manager.delete_backtest(execution.backtest_id)
        
        self.assertTrue(result)
        self.assertNotIn(execution.backtest_id, self.manager._active_executions)
    
    def test_delete_running_backtest_without_force(self):
        """Test deletion of running backtest without force flag."""
        execution = self._create_running_execution()
        self.manager._active_executions[execution.backtest_id] = execution
        
        result = self.manager.delete_backtest(execution.backtest_id, force=False)
        
        self.assertFalse(result)
        self.assertIn(execution.backtest_id, self.manager._active_executions)
    
    def test_delete_running_backtest_with_force(self):
        """Test forced deletion of running backtest."""
        execution = self._create_running_execution()
        self.manager._active_executions[execution.backtest_id] = execution
        
        with patch.object(self.manager, 'cancel_execution', return_value=True):
            with patch.object(self.manager, '_delete_backtest_via_api', return_value=True):
                result = self.manager.delete_backtest(execution.backtest_id, force=True)
        
        self.assertTrue(result)
        self.assertNotIn(execution.backtest_id, self.manager._active_executions)
    
    def test_get_execution_history(self):
        """Test retrieval of execution history."""
        # Add some local history
        from ..models import BacktestSummary
        
        summary1 = BacktestSummary(
            backtest_id="test1",
            script_name="Script1",
            market_tag="BTCUSDT",
            start_date=datetime.now() - timedelta(days=2),
            end_date=datetime.now() - timedelta(days=1),
            status="completed"
        )
        
        summary2 = BacktestSummary(
            backtest_id="test2",
            script_name="Script2",
            market_tag="ETHUSDT",
            start_date=datetime.now() - timedelta(days=3),
            end_date=datetime.now() - timedelta(days=2),
            status="failed"
        )
        
        self.manager._execution_history = [summary1, summary2]
        
        # Mock API response
        with patch.object(self.manager, '_fetch_execution_history_from_api', return_value=[]):
            history = self.manager.get_execution_history(limit=10)
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].backtest_id, "test1")  # Most recent first
    
    def test_cleanup_completed_executions(self):
        """Test cleanup of old completed executions."""
        # Create old completed executions
        old_execution = self._create_completed_execution()
        old_execution.completed_at = datetime.now() - timedelta(hours=25)  # Older than 24 hours
        
        recent_execution = self._create_completed_execution()
        recent_execution.backtest_id = "recent_test"
        recent_execution.completed_at = datetime.now() - timedelta(hours=1)  # Recent
        
        self.manager._active_executions[old_execution.backtest_id] = old_execution
        self.manager._active_executions[recent_execution.backtest_id] = recent_execution
        
        # Mock API calls
        with patch.object(self.manager, 'archive_backtest', return_value=True):
            result = self.manager.cleanup_completed_executions(max_age_hours=24)
        
        self.assertEqual(result["archived"], 1)
        self.assertEqual(result["total_processed"], 1)
        self.assertIn(recent_execution.backtest_id, self.manager._active_executions)
    
    def test_bulk_archive_completed(self):
        """Test bulk archiving of completed backtests."""
        # Create multiple completed executions
        executions = []
        for i in range(3):
            execution = self._create_completed_execution()
            execution.backtest_id = f"test_{i}"
            execution.completed_at = datetime.now() - timedelta(hours=25)
            executions.append(execution)
            self.manager._active_executions[execution.backtest_id] = execution
        
        with patch.object(self.manager, 'archive_backtest', return_value=True):
            result = self.manager.bulk_archive_completed(older_than_hours=24)
        
        self.assertEqual(result["archived"], 3)
        self.assertEqual(result["total_candidates"], 3)
    
    def test_get_backtest_retention_status(self):
        """Test backtest retention status reporting."""
        # Add various executions
        completed_execution = self._create_completed_execution()
        completed_execution.completed_at = datetime.now() - timedelta(hours=50)  # Old
        
        running_execution = self._create_running_execution()
        running_execution.backtest_id = "running_test"
        
        self.manager._active_executions[completed_execution.backtest_id] = completed_execution
        self.manager._active_executions[running_execution.backtest_id] = running_execution
        
        status = self.manager.get_backtest_retention_status()
        
        self.assertEqual(status["total_executions"], 2)
        self.assertEqual(status["completed_executions"], 1)
        self.assertEqual(status["running_executions"], 1)
        self.assertEqual(status["old_executions_needing_cleanup"], 1)
        self.assertTrue(status["cleanup_recommended"])
    
    def test_config_validator(self):
        """Test backtest configuration validation."""
        validator = BacktestConfigValidator()
        
        # Test valid configuration
        errors = validator.validate_config(self.sample_config)
        self.assertEqual(len(errors), 0)
        
        # Test invalid configuration
        invalid_config = BacktestConfig(
            script_id="",  # Empty script ID
            account_id="test_account",
            market_tag="BTCUSDT",
            start_time=int(datetime.now().timestamp()),
            end_time=int((datetime.now() - timedelta(days=1)).timestamp()),  # End before start
            interval=-1,  # Negative interval
            execution_amount=-100,  # Negative amount
            script_parameters={},
            leverage=-1  # Negative leverage
        )
        
        errors = validator.validate_config(invalid_config)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Script ID is required" in error for error in errors))
        self.assertTrue(any("Start time must be before end time" in error for error in errors))
        self.assertTrue(any("Interval must be positive" in error for error in errors))
        self.assertTrue(any("Execution amount must be positive" in error for error in errors))
        self.assertTrue(any("Leverage cannot be negative" in error for error in errors))
    
    def test_parameter_validator(self):
        """Test script parameter validation."""
        validator = BacktestConfigValidator()
        
        # Test valid parameters
        valid_params = {"param1": 10, "param2": 0.5, "param3": "test"}
        errors = validator.validate_parameters(valid_params)
        self.assertEqual(len(errors), 0)
        
        # Test invalid parameters
        invalid_params = {123: "invalid_key", "param2": 999999999}  # Non-string key, extreme value
        errors = validator.validate_parameters(invalid_params)
        self.assertGreater(len(errors), 0)
    
    def _create_completed_execution(self):
        """Create a completed execution for testing."""
        from ..models import ResourceUsage
        
        execution = BacktestExecution(
            backtest_id="test_completed",
            script_id=self.sample_config.script_id,
            config=self.sample_config,
            status=ExecutionStatus(
                status=ExecutionStatusType.COMPLETED,
                progress_percentage=100.0,
                current_phase="Completed",
                estimated_completion=None,
                resource_usage=ResourceUsage(
                    cpu_percent=0.0,
                    memory_mb=0.0,
                    disk_io_mb=0.0,
                    network_io_mb=0.0,
                    active_connections=0
                )
            ),
            started_at=datetime.now() - timedelta(hours=2),
            completed_at=datetime.now() - timedelta(hours=1)
        )
        return execution
    
    def _create_running_execution(self):
        """Create a running execution for testing."""
        from ..models import ResourceUsage
        
        execution = BacktestExecution(
            backtest_id="test_running",
            script_id=self.sample_config.script_id,
            config=self.sample_config,
            status=ExecutionStatus(
                status=ExecutionStatusType.RUNNING,
                progress_percentage=50.0,
                current_phase="Executing",
                estimated_completion=datetime.now() + timedelta(minutes=30),
                resource_usage=ResourceUsage(
                    cpu_percent=25.0,
                    memory_mb=512.0,
                    disk_io_mb=10.0,
                    network_io_mb=5.0,
                    active_connections=2
                )
            ),
            started_at=datetime.now() - timedelta(minutes=30)
        )
        return execution


if __name__ == '__main__':
    unittest.main()