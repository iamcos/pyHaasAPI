#!/usr/bin/env python3
"""
Test Backtest Execution System
This module provides comprehensive tests for the backtest execution system.
"""

import unittest
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_execution.backtest_executor import (
    BacktestExecutor, ExecutionStatus, ExecutionPriority, ExecutionRequest, ExecutionResult
)
from infrastructure.server_manager import ServerManager
from infrastructure.config_manager import ConfigManager
from account_management.account_manager import AccountManager
from lab_configuration.lab_configurator import LabConfigurator, LabAlgorithm

class TestBacktestExecutor(unittest.TestCase):
    """Test cases for BacktestExecutor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.server_manager = ServerManager()
        self.config_manager = ConfigManager()
        self.account_manager = AccountManager(self.server_manager, self.config_manager)
        self.executor = BacktestExecutor(self.server_manager, self.account_manager)
        
        # Create lab configurator for test configurations
        self.configurator = LabConfigurator()
        self.configurator.register_server_config("test-srv01", 50, 5)
        
        # Mock server availability for testing
        self.server_manager._available_servers = ["test-srv01", "test-srv02"]
    
    def test_execution_submission(self):
        """Test submitting execution requests"""
        # Create test configuration
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-submit-001",
            lab_name="Test Submit Lab",
            script_id="script-123",
            server_id="test-srv01",
            market_tag="BINANCEFUTURES_BTC_USDT_PERPETUAL",
            exchange_code="BINANCEFUTURES",
            account_id="test_account_1"
        )
        
        # Submit execution
        execution_id = self.executor.submit_execution(
            lab_configuration=config,
            priority=ExecutionPriority.HIGH,
            timeout_minutes=60
        )
        
        self.assertIsNotNone(execution_id)
        self.assertTrue(execution_id.startswith("exec_"))
        
        # Check that request is in queue
        self.assertEqual(len(self.executor.execution_queue), 1)
        self.assertEqual(self.executor.execution_queue[0].lab_id, config.lab_id)
    
    def test_execution_priority_ordering(self):
        """Test that executions are ordered by priority"""
        configs = []
        priorities = [ExecutionPriority.LOW, ExecutionPriority.URGENT, ExecutionPriority.NORMAL, ExecutionPriority.HIGH]
        
        # Submit executions with different priorities
        for i, priority in enumerate(priorities):
            config = self.configurator.create_lab_configuration(
                template_name="standard",
                lab_id=f"test-priority-{i:03d}",
                lab_name=f"Test Priority Lab {i}",
                script_id="script-priority",
                server_id="test-srv01",
                market_tag="BINANCE_ETH_USDT",
                exchange_code="BINANCE",
                account_id="test_account_1"
            )
            configs.append(config)
            
            self.executor.submit_execution(
                lab_configuration=config,
                priority=priority
            )
        
        # Check that queue is ordered by priority (highest first)
        queue_priorities = [req.priority.value for req in self.executor.execution_queue]
        expected_priorities = sorted([p.value for p in priorities], reverse=True)
        self.assertEqual(queue_priorities, expected_priorities)
    
    def test_execution_validation(self):
        """Test execution request validation"""
        # Create invalid configuration (missing required fields)
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-invalid-001",
            lab_name="Test Invalid Lab",
            script_id="",  # Missing script ID
            server_id="nonexistent-server",  # Invalid server
            market_tag="",  # Missing market tag
            exchange_code="BINANCE",
            account_id=""  # Missing account ID
        )
        
        request = ExecutionRequest(
            lab_id=config.lab_id,
            lab_configuration=config,
            priority=ExecutionPriority.NORMAL,
            timeout_minutes=60,
            retry_on_failure=True,
            max_retries=3
        )
        
        # Validate request
        is_valid, issues = self.executor._validate_execution_request(request)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(issues), 0)
        
        # Check specific validation issues
        issue_text = " ".join(issues).lower()
        self.assertIn("script", issue_text)
        self.assertIn("server", issue_text)
        self.assertIn("market", issue_text)
        self.assertIn("account", issue_text)
    
    def test_execution_status_tracking(self):
        """Test execution status tracking"""
        # Create test configuration
        config = self.configurator.create_lab_configuration(
            template_name="high_frequency",
            lab_id="test-status-001",
            lab_name="Test Status Lab",
            script_id="script-status",
            server_id="test-srv01",
            market_tag="BINANCE_BTC_USDT",
            exchange_code="BINANCE",
            account_id="test_account_1",
            max_generations=5  # Fast execution for testing
        )
        
        # Submit execution
        execution_id = self.executor.submit_execution(config)
        
        # Check initial status
        status = self.executor.get_execution_status(config.lab_id)
        self.assertEqual(status, ExecutionStatus.PENDING)
        
        # Process queue (this will start execution)
        self.executor._process_execution_queue()
        
        # Check running status
        status = self.executor.get_execution_status(config.lab_id)
        self.assertEqual(status, ExecutionStatus.RUNNING)
        
        # Check that execution is in active executions
        self.assertIn(config.lab_id, self.executor.active_executions)
    
    def test_execution_cancellation(self):
        """Test execution cancellation"""
        # Create test configuration
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-cancel-001",
            lab_name="Test Cancel Lab",
            script_id="script-cancel",
            server_id="test-srv01",
            market_tag="BINANCE_ADA_USDT",
            exchange_code="BINANCE",
            account_id="test_account_1"
        )
        
        # Submit execution
        execution_id = self.executor.submit_execution(config)
        
        # Cancel while in queue
        success = self.executor.cancel_execution(config.lab_id)
        self.assertTrue(success)
        
        # Check that execution is no longer in queue
        lab_ids_in_queue = [req.lab_id for req in self.executor.execution_queue]
        self.assertNotIn(config.lab_id, lab_ids_in_queue)
        
        # Check status
        status = self.executor.get_execution_status(config.lab_id)
        self.assertIsNone(status)  # Should be None since it was cancelled from queue
    
    def test_execution_summary(self):
        """Test execution summary generation"""
        # Submit multiple executions
        configs = []
        for i in range(3):
            config = self.configurator.create_lab_configuration(
                template_name="standard",
                lab_id=f"test-summary-{i:03d}",
                lab_name=f"Test Summary Lab {i}",
                script_id="script-summary",
                server_id="test-srv01",
                market_tag="BINANCE_DOT_USDT",
                exchange_code="BINANCE",
                account_id="test_account_1"
            )
            configs.append(config)
            self.executor.submit_execution(config)
        
        # Get summary
        summary = self.executor.get_execution_summary()
        
        self.assertIn('total_executions', summary)
        self.assertIn('status_distribution', summary)
        self.assertIn('active_executions', summary)
        self.assertIn('queued_executions', summary)
        self.assertIn('max_concurrent_executions', summary)
        
        # Check that we have the expected number of executions
        self.assertEqual(summary['queued_executions'], 3)
        self.assertEqual(summary['total_executions'], 3)
    
    def test_execution_result_storage(self):
        """Test that execution results are properly stored"""
        # Create a mock result
        result = ExecutionResult(
            lab_id="test-result-001",
            execution_id="exec_test_123",
            status=ExecutionStatus.COMPLETED,
            start_time=time.time() - 100,
            end_time=time.time(),
            total_duration=100.0,
            best_configuration={'param1': 0.5},
            best_fitness=85.6,
            total_generations=50,
            total_evaluations=2500,
            result_data={'trades': 156},
            error_message=None,
            server_id="test-srv01"
        )
        
        # Store result
        self.executor.execution_results[result.lab_id] = result
        
        # Retrieve result
        retrieved_result = self.executor.get_execution_result(result.lab_id)
        
        self.assertIsNotNone(retrieved_result)
        self.assertEqual(retrieved_result.lab_id, result.lab_id)
        self.assertEqual(retrieved_result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(retrieved_result.best_fitness, 85.6)
        self.assertEqual(retrieved_result.total_generations, 50)
    
    def test_execution_progress_tracking(self):
        """Test execution progress tracking"""
        from backtest_execution.backtest_executor import ExecutionProgress
        
        # Create mock progress
        progress = ExecutionProgress(
            lab_id="test-progress-001",
            current_generation=25,
            max_generations=100,
            current_population=50,
            max_population=50,
            best_fitness=75.2,
            elapsed_time=300.0,
            estimated_remaining=900.0,
            progress_percentage=25.0,
            last_update=time.time()
        )
        
        # Store progress
        self.executor.execution_progress[progress.lab_id] = progress
        
        # Retrieve progress
        retrieved_progress = self.executor.get_execution_progress(progress.lab_id)
        
        self.assertIsNotNone(retrieved_progress)
        self.assertEqual(retrieved_progress.lab_id, progress.lab_id)
        self.assertEqual(retrieved_progress.current_generation, 25)
        self.assertEqual(retrieved_progress.progress_percentage, 25.0)
        self.assertEqual(retrieved_progress.best_fitness, 75.2)
    
    def test_concurrent_execution_limits(self):
        """Test concurrent execution limits"""
        # Set low limit for testing
        original_limit = self.executor.max_concurrent_executions
        self.executor.max_concurrent_executions = 2
        
        try:
            # Submit more executions than the limit
            configs = []
            for i in range(5):
                config = self.configurator.create_lab_configuration(
                    template_name="high_frequency",
                    lab_id=f"test-concurrent-{i:03d}",
                    lab_name=f"Test Concurrent Lab {i}",
                    script_id="script-concurrent",
                    server_id="test-srv01",
                    market_tag="BINANCE_LINK_USDT",
                    exchange_code="BINANCE",
                    account_id="test_account_1",
                    max_generations=10  # Fast for testing
                )
                configs.append(config)
                self.executor.submit_execution(config)
            
            # Process queue
            self.executor._process_execution_queue()
            
            # Should only have 2 active executions (the limit)
            self.assertLessEqual(len(self.executor.active_executions), 2)
            
            # Should have remaining executions in queue
            self.assertGreater(len(self.executor.execution_queue), 0)
            
        finally:
            # Restore original limit
            self.executor.max_concurrent_executions = original_limit
    
    def test_execution_timeout_handling(self):
        """Test execution timeout handling"""
        # This test would require actual execution, so we'll test the timeout logic
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-timeout-001",
            lab_name="Test Timeout Lab",
            script_id="script-timeout",
            server_id="test-srv01",
            market_tag="BINANCE_XRP_USDT",
            exchange_code="BINANCE",
            account_id="test_account_1"
        )
        
        # Submit with very short timeout
        execution_id = self.executor.submit_execution(
            lab_configuration=config,
            timeout_minutes=0.01  # 0.6 seconds
        )
        
        # Check that timeout is properly set in request
        request = self.executor.execution_queue[0]
        self.assertEqual(request.timeout_minutes, 0.01)
    
    def test_execution_retry_configuration(self):
        """Test execution retry configuration"""
        config = self.configurator.create_lab_configuration(
            template_name="standard",
            lab_id="test-retry-001",
            lab_name="Test Retry Lab",
            script_id="script-retry",
            server_id="test-srv01",
            market_tag="BINANCE_ATOM_USDT",
            exchange_code="BINANCE",
            account_id="test_account_1"
        )
        
        # Submit with custom retry settings
        execution_id = self.executor.submit_execution(
            lab_configuration=config,
            retry_on_failure=True,
            max_retries=5
        )
        
        # Check that retry settings are properly set
        request = self.executor.execution_queue[0]
        self.assertTrue(request.retry_on_failure)
        self.assertEqual(request.max_retries, 5)

def main():
    """Run all tests"""
    unittest.main(verbosity=2)

if __name__ == "__main__":
    main()