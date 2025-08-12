"""
Basic functionality tests for the core system components.
"""

import unittest
from datetime import datetime, timedelta
import tempfile
import os

from ..config import ConfigManager, SystemConfig, HaasOnlineConfig, DatabaseConfig
from ..script_manager import ScriptManager
from ..backtest_manager import BacktestManager
from ..results_manager import ResultsManager
from ..models import BacktestConfig, PositionMode, ScriptType


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of core system components."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test configurations
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
        
        # Set up test environment variables
        os.environ['HAAS_SERVER_URL'] = 'https://test-server.com'
        os.environ['HAAS_API_KEY'] = 'test_api_key'
        os.environ['HAAS_API_SECRET'] = 'test_api_secret'
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up environment variables
        for key in ['HAAS_SERVER_URL', 'HAAS_API_KEY', 'HAAS_API_SECRET']:
            if key in os.environ:
                del os.environ[key]
    
    def test_config_manager_initialization(self):
        """Test configuration manager initialization."""
        # Test system config
        system_config = self.config_manager.system
        self.assertIsInstance(system_config, SystemConfig)
        self.assertEqual(system_config.environment, 'development')
        
        # Test HaasOnline config
        haasonline_config = self.config_manager.haasonline
        self.assertIsInstance(haasonline_config, HaasOnlineConfig)
        self.assertEqual(haasonline_config.server_url, 'https://test-server.com/')
        self.assertEqual(haasonline_config.api_key, 'test_api_key')
        
        # Test database config
        database_config = self.config_manager.database
        self.assertIsInstance(database_config, DatabaseConfig)
        self.assertTrue(database_config.enable_postgresql)
    
    def test_script_manager_basic_operations(self):
        """Test basic script manager operations."""
        script_manager = ScriptManager(self.config_manager)
        
        # Test loading script (will use placeholder implementation)
        script = script_manager.load_script('test_script_001')
        self.assertEqual(script.script_id, 'test_script_001')
        self.assertIsInstance(script.script_type, ScriptType)
        self.assertIsInstance(script.created_at, datetime)
        
        # Test script debugging
        debug_result = script_manager.debug_script(script)
        self.assertIsNotNone(debug_result)
        self.assertIsInstance(debug_result.success, bool)
        
        # Test script validation
        validation_result = script_manager.validate_script(script)
        self.assertIsNotNone(validation_result)
        self.assertIsInstance(validation_result.is_valid, bool)
        
        # Test parameter updates
        new_params = {'test_param': 123.45}
        updated_script = script_manager.update_parameters(script, new_params)
        self.assertEqual(updated_script.parameters['test_param'], 123.45)
        
        # Test script capabilities
        capabilities = script_manager.get_script_capabilities()
        self.assertIsNotNone(capabilities)
        self.assertGreater(len(capabilities.available_functions), 0)
    
    def test_backtest_manager_basic_operations(self):
        """Test basic backtest manager operations."""
        backtest_manager = BacktestManager(self.config_manager)
        
        # Create test backtest configuration
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        config = BacktestConfig(
            script_id='test_script_001',
            account_id='test_account',
            market_tag='BTC/USD',
            start_time=int(start_time.timestamp()),
            end_time=int(end_time.timestamp()),
            interval=60,
            execution_amount=1000.0,
            script_parameters={'param1': 100},
            position_mode=PositionMode.LONG_ONLY
        )
        
        # Test configuration validation
        self.assertTrue(config.validate())
        
        # Test backtest execution
        execution = backtest_manager.execute_backtest(config)
        self.assertIsNotNone(execution)
        self.assertEqual(execution.script_id, 'test_script_001')
        self.assertIsNotNone(execution.backtest_id)
        
        # Test execution monitoring
        status = backtest_manager.monitor_execution(execution.backtest_id)
        self.assertIsNotNone(status)
        
        # Test getting logs
        logs = backtest_manager.get_backtest_logs(execution.backtest_id)
        self.assertIsInstance(logs, list)
        
        # Test getting active executions
        active_executions = backtest_manager.get_active_executions()
        self.assertIsInstance(active_executions, list)
        
        # Test execution history
        history = backtest_manager.get_execution_history()
        self.assertIsInstance(history, list)
    
    def test_results_manager_basic_operations(self):
        """Test basic results manager operations."""
        results_manager = ResultsManager(self.config_manager)
        backtest_manager = BacktestManager(self.config_manager)
        
        # Create and execute a test backtest
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        config = BacktestConfig(
            script_id='test_script_001',
            account_id='test_account',
            market_tag='BTC/USD',
            start_time=int(start_time.timestamp()),
            end_time=int(end_time.timestamp()),
            interval=60,
            execution_amount=1000.0,
            script_parameters={'param1': 100},
            position_mode=PositionMode.LONG_ONLY
        )
        
        execution = backtest_manager.execute_backtest(config)
        
        # Test results processing
        results = results_manager.process_results(execution.backtest_id)
        self.assertIsNotNone(results)
        self.assertEqual(results.backtest_id, execution.backtest_id)
        self.assertIsNotNone(results.trading_metrics)
        self.assertIsNotNone(results.performance_data)
        
        # Test metrics calculation
        self.assertIsInstance(results.trading_metrics.total_return, float)
        self.assertIsInstance(results.trading_metrics.sharpe_ratio, float)
        self.assertIsInstance(results.trading_metrics.max_drawdown, float)
        
        # Test result export
        json_export = results_manager.export_results(results, 'json')
        self.assertIsInstance(json_export, bytes)
        self.assertGreater(len(json_export), 0)
        
        csv_export = results_manager.export_results(results, 'csv')
        self.assertIsInstance(csv_export, bytes)
        self.assertGreater(len(csv_export), 0)
        
        # Test lab compatibility formatting
        lab_format = results_manager.format_for_lab_compatibility(results)
        self.assertIsInstance(lab_format, dict)
        self.assertIn('backtest_id', lab_format)
        self.assertIn('performance_metrics', lab_format)
    
    def test_data_model_validation(self):
        """Test data model validation and functionality."""
        # Test BacktestConfig validation
        valid_config = BacktestConfig(
            script_id='test',
            account_id='test',
            market_tag='BTC/USD',
            start_time=1000000,
            end_time=2000000,
            interval=60,
            execution_amount=100.0,
            script_parameters={}
        )
        self.assertTrue(valid_config.validate())
        
        # Test invalid configuration
        invalid_config = BacktestConfig(
            script_id='test',
            account_id='test',
            market_tag='BTC/USD',
            start_time=2000000,  # Start after end
            end_time=1000000,
            interval=60,
            execution_amount=100.0,
            script_parameters={}
        )
        self.assertFalse(invalid_config.validate())
        
        # Test duration calculation
        self.assertEqual(valid_config.duration_days, 11)  # (2000000 - 1000000) / 86400
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        script_manager = ScriptManager(self.config_manager)
        backtest_manager = BacktestManager(self.config_manager)
        results_manager = ResultsManager(self.config_manager)
        
        # Test invalid script ID
        with self.assertRaises(ValueError):
            script_manager.load_script('')
        
        # Test invalid backtest configuration
        invalid_config = BacktestConfig(
            script_id='test',
            account_id='test',
            market_tag='BTC/USD',
            start_time=2000000,
            end_time=1000000,  # Invalid: end before start
            interval=60,
            execution_amount=100.0,
            script_parameters={}
        )
        
        with self.assertRaises(ValueError):
            backtest_manager.execute_backtest(invalid_config)
        
        # Test monitoring non-existent backtest
        with self.assertRaises(ValueError):
            backtest_manager.monitor_execution('non_existent_id')
        
        # Test processing non-existent results
        with self.assertRaises(ValueError):
            results_manager.process_results('non_existent_id')


if __name__ == '__main__':
    unittest.main()