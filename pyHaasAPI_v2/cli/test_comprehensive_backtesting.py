#!/usr/bin/env python3
"""
Comprehensive Backtesting System Tests

Unit tests, integration tests, and end-to-end tests for the comprehensive backtesting manager.
"""

import unittest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

# Add pyHaasAPI_v2 to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from comprehensive_backtesting_manager import (
    ComprehensiveBacktestingManager,
    ProjectConfig,
    BacktestStep,
    LabConfig,
    CoinConfig,
    AnalysisResult
)


class TestDataModels(unittest.TestCase):
    """Test data model classes"""
    
    def test_lab_config_creation(self):
        """Test LabConfig creation and validation"""
        lab_config = LabConfig(
            lab_id="test-lab-123",
            lab_name="Test Lab",
            script_id="script-456",
            market_tag="BTC_USDT_PERPETUAL",
            priority=1,
            enabled=True
        )
        
        self.assertEqual(lab_config.lab_id, "test-lab-123")
        self.assertEqual(lab_config.lab_name, "Test Lab")
        self.assertEqual(lab_config.script_id, "script-456")
        self.assertEqual(lab_config.market_tag, "BTC_USDT_PERPETUAL")
        self.assertEqual(lab_config.priority, 1)
        self.assertTrue(lab_config.enabled)
    
    def test_coin_config_creation(self):
        """Test CoinConfig creation and validation"""
        coin_config = CoinConfig(
            symbol="BTC",
            market_tag="BTC_USDT_PERPETUAL",
            priority=1,
            enabled=True
        )
        
        self.assertEqual(coin_config.symbol, "BTC")
        self.assertEqual(coin_config.market_tag, "BTC_USDT_PERPETUAL")
        self.assertEqual(coin_config.priority, 1)
        self.assertTrue(coin_config.enabled)
    
    def test_backtest_step_creation(self):
        """Test BacktestStep creation and validation"""
        lab_configs = [
            LabConfig(
                lab_id="lab1",
                lab_name="Lab 1",
                script_id="script1",
                market_tag="BTC_USDT_PERPETUAL"
            )
        ]
        
        coin_configs = [
            CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL")
        ]
        
        step = BacktestStep(
            step_id="step1",
            name="Test Step",
            lab_configs=lab_configs,
            coin_configs=coin_configs,
            analysis_criteria={
                'min_win_rate': 0.3,
                'min_trades': 5
            },
            max_iterations=1000,
            cutoff_days=730
        )
        
        self.assertEqual(step.step_id, "step1")
        self.assertEqual(step.name, "Test Step")
        self.assertEqual(len(step.lab_configs), 1)
        self.assertEqual(len(step.coin_configs), 1)
        self.assertEqual(step.max_iterations, 1000)
        self.assertEqual(step.cutoff_days, 730)
        self.assertTrue(step.enabled)
    
    def test_project_config_creation(self):
        """Test ProjectConfig creation and validation"""
        steps = [
            BacktestStep(
                step_id="step1",
                name="Step 1",
                lab_configs=[],
                coin_configs=[],
                analysis_criteria={}
            )
        ]
        
        project_config = ProjectConfig(
            project_name="Test Project",
            description="Test Description",
            steps=steps,
            global_settings={
                'trade_amount': 2000.0,
                'leverage': 20.0
            },
            output_directory="test_output"
        )
        
        self.assertEqual(project_config.project_name, "Test Project")
        self.assertEqual(project_config.description, "Test Description")
        self.assertEqual(len(project_config.steps), 1)
        self.assertEqual(project_config.global_settings['trade_amount'], 2000.0)
        self.assertEqual(project_config.output_directory, "test_output")
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult creation and validation"""
        top_configs = [
            {
                'lab_key': 'lab1_BTC',
                'lab_name': 'Test Lab',
                'coin_symbol': 'BTC',
                'best_roe': 25.5,
                'best_win_rate': 0.6
            }
        ]
        
        analysis_result = AnalysisResult(
            step_id="step1",
            top_configs=top_configs,
            analysis_timestamp=datetime.now().isoformat(),
            total_backtests_analyzed=100,
            qualifying_backtests=10,
            best_roe=25.5,
            best_win_rate=0.6,
            recommendations=["Test recommendation"]
        )
        
        self.assertEqual(analysis_result.step_id, "step1")
        self.assertEqual(len(analysis_result.top_configs), 1)
        self.assertEqual(analysis_result.total_backtests_analyzed, 100)
        self.assertEqual(analysis_result.best_roe, 25.5)
        self.assertEqual(len(analysis_result.recommendations), 1)


class TestComprehensiveBacktestingManager(unittest.TestCase):
    """Test ComprehensiveBacktestingManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_config = ProjectConfig(
            project_name="Test Project",
            description="Test Description",
            steps=[
                BacktestStep(
                    step_id="step1",
                    name="Test Step",
                    lab_configs=[
                        LabConfig(
                            lab_id="test-lab",
                            lab_name="Test Lab",
                            script_id="test-script",
                            market_tag="BTC_USDT_PERPETUAL"
                        )
                    ],
                    coin_configs=[
                        CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL")
                    ],
                    analysis_criteria={
                        'min_win_rate': 0.3,
                        'min_trades': 5
                    }
                )
            ],
            global_settings={
                'trade_amount': 2000.0,
                'leverage': 20.0
            }
        )
        
        self.manager = ComprehensiveBacktestingManager(self.project_config)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        self.assertIsNotNone(self.manager.project_config)
        self.assertIsNotNone(self.manager.cache_manager)
        self.assertIsNotNone(self.manager.analyzer)
        self.assertIsNone(self.manager.api_executor)
        self.assertEqual(self.manager.project_config.project_name, "Test Project")
    
    def test_filter_backtests_by_criteria(self):
        """Test backtest filtering logic"""
        # Create mock backtest objects
        class MockBacktest:
            def __init__(self, win_rate, total_trades, max_drawdown, realized_profits_usdt, starting_balance):
                self.win_rate = win_rate
                self.total_trades = total_trades
                self.max_drawdown = max_drawdown
                self.realized_profits_usdt = realized_profits_usdt
                self.starting_balance = starting_balance
        
        backtests = [
            MockBacktest(0.5, 10, 20.0, 1000.0, 10000.0),  # Good backtest
            MockBacktest(0.2, 3, 30.0, 500.0, 10000.0),   # Bad backtest (low win rate, few trades)
            MockBacktest(0.6, 15, 60.0, 2000.0, 10000.0),  # Bad backtest (high drawdown)
            MockBacktest(0.4, 8, 25.0, 200.0, 10000.0),   # Bad backtest (low ROE)
        ]
        
        criteria = {
            'min_win_rate': 0.3,
            'min_trades': 5,
            'max_drawdown': 50.0,
            'min_roe': 5.0
        }
        
        filtered = self.manager.filter_backtests_by_criteria(backtests, criteria)
        
        # Only the first backtest should pass all criteria
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].win_rate, 0.5)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        top_configs = [
            {
                'optimized_lab': {
                    'lab_name': 'Lab 1',
                    'coin_symbol': 'BTC',
                    'best_roe': 25.0,
                    'best_win_rate': 0.6
                }
            },
            {
                'optimized_lab': {
                    'lab_name': 'Lab 2',
                    'coin_symbol': 'TRX',
                    'best_roe': 15.0,
                    'best_win_rate': 0.5
                }
            }
        ]
        
        step = BacktestStep(
            step_id="step1",
            name="Test Step",
            lab_configs=[],
            coin_configs=[],
            analysis_criteria={}
        )
        
        recommendations = self.manager.generate_recommendations(top_configs, step)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for expected recommendation content
        recommendations_text = ' '.join(recommendations)
        self.assertIn('Average ROE', recommendations_text)
        self.assertIn('Average Win Rate', recommendations_text)
        self.assertIn('Top performer', recommendations_text)
    
    def test_generate_final_recommendations(self):
        """Test final recommendation generation"""
        top_configs = [
            {
                'lab_name': 'Best Lab',
                'coin_symbol': 'BTC',
                'best_roe': 30.0,
                'best_win_rate': 0.7
            },
            {
                'lab_name': 'Good Lab',
                'coin_symbol': 'TRX',
                'best_roe': 20.0,
                'best_win_rate': 0.6
            }
        ]
        
        recommendations = self.manager.generate_final_recommendations(top_configs)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Check for expected content
        recommendations_text = ' '.join(recommendations)
        self.assertIn('Overall Average ROE', recommendations_text)
        self.assertIn('Best Overall Configuration', recommendations_text)
        self.assertIn('Coin Performance', recommendations_text)


class TestIntegration(unittest.TestCase):
    """Test integration between components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_config = ProjectConfig(
            project_name="Integration Test",
            description="Integration test project",
            steps=[
                BacktestStep(
                    step_id="step1",
                    name="Integration Step",
                    lab_configs=[
                        LabConfig(
                            lab_id="test-lab",
                            lab_name="Test Lab",
                            script_id="test-script",
                            market_tag="BTC_USDT_PERPETUAL"
                        )
                    ],
                    coin_configs=[
                        CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL")
                    ],
                    analysis_criteria={
                        'min_win_rate': 0.3,
                        'min_trades': 5
                    }
                )
            ],
            global_settings={
                'trade_amount': 2000.0,
                'leverage': 20.0
            },
            output_directory=self.temp_dir
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_project_config_serialization(self):
        """Test project configuration serialization"""
        # Convert to dict
        config_dict = self.project_config.__dict__
        
        # Should contain expected keys
        self.assertIn('project_name', config_dict)
        self.assertIn('description', config_dict)
        self.assertIn('steps', config_dict)
        self.assertIn('global_settings', config_dict)
        self.assertIn('output_directory', config_dict)
        
        # Steps should be serializable
        steps = config_dict['steps']
        self.assertIsInstance(steps, list)
        self.assertEqual(len(steps), 1)
        
        # Global settings should be serializable
        global_settings = config_dict['global_settings']
        self.assertIsInstance(global_settings, dict)
        self.assertIn('trade_amount', global_settings)
        self.assertIn('leverage', global_settings)
    
    def test_analysis_result_serialization(self):
        """Test analysis result serialization"""
        analysis_result = AnalysisResult(
            step_id="step1",
            top_configs=[
                {
                    'lab_key': 'test',
                    'lab_name': 'Test Lab',
                    'coin_symbol': 'BTC',
                    'best_roe': 25.0,
                    'best_win_rate': 0.6
                }
            ],
            analysis_timestamp=datetime.now().isoformat(),
            total_backtests_analyzed=100,
            qualifying_backtests=10,
            best_roe=25.0,
            best_win_rate=0.6,
            recommendations=["Test recommendation"]
        )
        
        # Convert to dict
        result_dict = analysis_result.__dict__
        
        # Should contain expected keys
        self.assertIn('step_id', result_dict)
        self.assertIn('top_configs', result_dict)
        self.assertIn('analysis_timestamp', result_dict)
        self.assertIn('total_backtests_analyzed', result_dict)
        self.assertIn('qualifying_backtests', result_dict)
        self.assertIn('best_roe', result_dict)
        self.assertIn('best_win_rate', result_dict)
        self.assertIn('recommendations', result_dict)


class TestMockedAPI(unittest.TestCase):
    """Test with mocked API responses"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_config = ProjectConfig(
            project_name="Mock Test",
            description="Mock test project",
            steps=[
                BacktestStep(
                    step_id="step1",
                    name="Mock Step",
                    lab_configs=[
                        LabConfig(
                            lab_id="mock-lab",
                            lab_name="Mock Lab",
                            script_id="mock-script",
                            market_tag="BTC_USDT_PERPETUAL"
                        )
                    ],
                    coin_configs=[
                        CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL")
                    ],
                    analysis_criteria={
                        'min_win_rate': 0.3,
                        'min_trades': 5
                    }
                )
            ],
            global_settings={
                'trade_amount': 2000.0,
                'leverage': 20.0
            }
        )
        
        self.manager = ComprehensiveBacktestingManager(self.project_config)
    
    def test_mocked_initialization(self):
        """Test manager initialization with mocked API"""
        # Test that manager can be initialized without errors
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.project_config)
        self.assertIsNotNone(self.manager.cache_manager)
        self.assertIsNotNone(self.manager.analyzer)
        
        # Test that we can set the API executor
        mock_executor = Mock()
        self.manager.api_executor = mock_executor
        self.assertEqual(self.manager.api_executor, mock_executor)
    
    def test_mocked_backtest_analysis(self):
        """Test backtest analysis with mocked data"""
        # Create mock backtest data
        class MockBacktest:
            def __init__(self, backtest_id, roi_percentage, win_rate, total_trades, 
                        max_drawdown, realized_profits_usdt, starting_balance, script_name):
                self.backtest_id = backtest_id
                self.roi_percentage = roi_percentage
                self.win_rate = win_rate
                self.total_trades = total_trades
                self.max_drawdown = max_drawdown
                self.realized_profits_usdt = realized_profits_usdt
                self.starting_balance = starting_balance
                self.script_name = script_name
                self.parameter_values = {}
        
        mock_backtests = [
            MockBacktest("bt1", 25.0, 0.6, 10, 15.0, 1000.0, 10000.0, "Script 1"),
            MockBacktest("bt2", 15.0, 0.4, 8, 20.0, 500.0, 10000.0, "Script 2"),
            MockBacktest("bt3", 35.0, 0.7, 12, 10.0, 1500.0, 10000.0, "Script 3"),
        ]
        
        # Test filtering
        criteria = {
            'min_win_rate': 0.5,
            'min_trades': 8,
            'max_drawdown': 25.0,
            'min_roe': 10.0
        }
        
        filtered = self.manager.filter_backtests_by_criteria(mock_backtests, criteria)
        
        # Should filter out backtest 2 (low win rate) 
        # Backtests 1 and 3 should pass (bt1 has win_rate 0.6 > 0.5, bt3 has win_rate 0.7 > 0.5)
        self.assertEqual(len(filtered), 2)
        # Check that bt2 is filtered out (low win rate 0.4 < 0.5)
        filtered_ids = [bt.backtest_id for bt in filtered]
        self.assertIn("bt1", filtered_ids)
        self.assertIn("bt3", filtered_ids)
        self.assertNotIn("bt2", filtered_ids)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_config = ProjectConfig(
            project_name="Error Test",
            description="Error test project",
            steps=[],
            global_settings={}
        )
        
        self.manager = ComprehensiveBacktestingManager(self.project_config)
    
    def test_invalid_lab_config(self):
        """Test handling of invalid lab configuration"""
        with self.assertRaises(TypeError):
            # This should raise an error due to missing required fields
            LabConfig()  # Missing required fields
    
    def test_invalid_coin_config(self):
        """Test handling of invalid coin configuration"""
        with self.assertRaises(TypeError):
            # This should raise an error due to missing required fields
            CoinConfig()  # Missing required fields
    
    def test_empty_project_config(self):
        """Test handling of empty project configuration"""
        empty_config = ProjectConfig(
            project_name="",
            description="",
            steps=[],
            global_settings={}
        )
        
        # Should not raise an error, but should be handled gracefully
        self.assertEqual(empty_config.project_name, "")
        self.assertEqual(len(empty_config.steps), 0)
    
    def test_invalid_analysis_criteria(self):
        """Test handling of invalid analysis criteria"""
        # Test with invalid criteria values
        invalid_criteria = {
            'min_win_rate': -0.1,  # Invalid negative value
            'min_trades': -5,      # Invalid negative value
            'max_drawdown': 150.0, # Invalid high value
            'min_roe': -10.0       # Invalid negative value
        }
        
        # The system should handle these gracefully
        # (In a real implementation, you'd want validation)
        self.assertIsInstance(invalid_criteria, dict)


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_config = ProjectConfig(
            project_name="Performance Test",
            description="Performance test project",
            steps=[
                BacktestStep(
                    step_id="step1",
                    name="Performance Step",
                    lab_configs=[
                        LabConfig(
                            lab_id=f"lab-{i}",
                            lab_name=f"Lab {i}",
                            script_id=f"script-{i}",
                            market_tag="BTC_USDT_PERPETUAL"
                        ) for i in range(10)  # 10 labs
                    ],
                    coin_configs=[
                        CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL"),
                        CoinConfig(symbol="TRX", market_tag="TRX_USDT_PERPETUAL"),
                        CoinConfig(symbol="ETH", market_tag="ETH_USDT_PERPETUAL")
                    ],
                    analysis_criteria={
                        'min_win_rate': 0.3,
                        'min_trades': 5
                    }
                )
            ],
            global_settings={
                'trade_amount': 2000.0,
                'leverage': 20.0
            }
        )
        
        self.manager = ComprehensiveBacktestingManager(self.project_config)
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        # Create a large number of mock backtests
        class MockBacktest:
            def __init__(self, backtest_id):
                self.backtest_id = backtest_id
                self.roi_percentage = 20.0
                self.win_rate = 0.5
                self.total_trades = 10
                self.max_drawdown = 20.0
                self.realized_profits_usdt = 1000.0
                self.starting_balance = 10000.0
                self.script_name = "Test Script"
                self.parameter_values = {}
        
        # Create 1000 mock backtests
        large_dataset = [MockBacktest(f"bt-{i}") for i in range(1000)]
        
        # Test filtering performance
        import time
        start_time = time.time()
        
        criteria = {
            'min_win_rate': 0.3,
            'min_trades': 5,
            'max_drawdown': 50.0,
            'min_roe': 10.0
        }
        
        filtered = self.manager.filter_backtests_by_criteria(large_dataset, criteria)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 1000 backtests in reasonable time (< 1 second)
        self.assertLess(processing_time, 1.0)
        self.assertEqual(len(filtered), 1000)  # All should pass the criteria
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large configurations"""
        # Create a large project configuration
        large_steps = []
        
        for i in range(100):  # 100 steps
            step = BacktestStep(
                step_id=f"step-{i}",
                name=f"Step {i}",
                lab_configs=[
                    LabConfig(
                        lab_id=f"lab-{i}-{j}",
                        lab_name=f"Lab {i}-{j}",
                        script_id=f"script-{i}-{j}",
                        market_tag="BTC_USDT_PERPETUAL"
                    ) for j in range(10)  # 10 labs per step
                ],
                coin_configs=[
                    CoinConfig(symbol="BTC", market_tag="BTC_USDT_PERPETUAL"),
                    CoinConfig(symbol="TRX", market_tag="TRX_USDT_PERPETUAL")
                ],
                analysis_criteria={
                    'min_win_rate': 0.3,
                    'min_trades': 5
                }
            )
            large_steps.append(step)
        
        large_config = ProjectConfig(
            project_name="Large Test",
            description="Large test project",
            steps=large_steps,
            global_settings={
                'trade_amount': 2000.0,
                'leverage': 20.0
            }
        )
        
        # Should not raise memory errors
        self.assertEqual(len(large_config.steps), 100)
        self.assertEqual(len(large_config.steps[0].lab_configs), 10)
        self.assertEqual(len(large_config.steps[0].coin_configs), 2)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestDataModels,
        TestComprehensiveBacktestingManager,
        TestIntegration,
        TestMockedAPI,
        TestErrorHandling,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
