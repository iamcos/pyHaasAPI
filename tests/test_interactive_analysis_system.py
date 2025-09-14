#!/usr/bin/env python3
"""
Test suite for the Interactive Analysis System

This test suite covers:
- Enhanced cache management
- Interactive analyzer functionality
- Visualization tool
- Bot creation workflow
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.analysis.models import BacktestAnalysis, LabAnalysisResult
from pyHaasAPI.cli.interactive_analyzer import InteractiveAnalyzer
from pyHaasAPI.cli.visualization_tool import VisualizationTool


class TestEnhancedCacheManagement:
    """Test enhanced cache management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = UnifiedCacheManager()
        self.cache.base_dir = Path(self.temp_dir)
        
        # Create cache directory structure
        (self.cache.base_dir / "backtests").mkdir(parents=True, exist_ok=True)
        (self.cache.base_dir / "reports").mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_save_analysis_result(self):
        """Test saving analysis results to JSON"""
        # Create mock analysis result
        backtest = BacktestAnalysis(
            backtest_id="test_bt_123",
            lab_id="test_lab_456",
            generation_idx=1,
            population_idx=2,
            market_tag="BINANCE_BTC_USDT_",
            script_id="script_789",
            script_name="Test Script",
            roi_percentage=150.5,
            calculated_roi_percentage=145.2,
            roi_difference=5.3,
            win_rate=0.65,
            total_trades=100,
            max_drawdown=15.2,
            realized_profits_usdt=1500.0,
            pc_value=1.5,
            avg_profit_per_trade=15.0,
            profit_factor=1.8,
            sharpe_ratio=1.2,
            starting_balance=1000.0,
            final_balance=2500.0,
            peak_balance=2600.0,
            analysis_timestamp="2024-01-01T12:00:00"
        )
        
        result = LabAnalysisResult(
            lab_id="test_lab_456",
            lab_name="Test Lab",
            total_backtests=50,
            analyzed_backtests=10,
            processing_time=30.5,
            top_backtests=[backtest],
            bots_created=0,
            analysis_timestamp="2024-01-01T12:00:00"
        )
        
        # Save analysis result
        result_path = self.cache.save_analysis_result(result)
        
        # Verify file was created
        assert result_path.exists()
        assert "analysis_result_test_lab_456" in str(result_path)
        
        # Verify content
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert data["lab_id"] == "test_lab_456"
        assert data["lab_name"] == "Test Lab"
        assert len(data["top_backtests"]) == 1
        assert data["top_backtests"][0]["backtest_id"] == "test_bt_123"
    
    def test_load_analysis_result(self):
        """Test loading analysis results from JSON"""
        # Create test data
        test_data = {
            "lab_id": "test_lab_789",
            "lab_name": "Test Lab 2",
            "total_backtests": 25,
            "analyzed_backtests": 5,
            "processing_time": 20.0,
            "top_backtests": [
                {
                    "backtest_id": "test_bt_456",
                    "lab_id": "test_lab_789",
                    "script_name": "Test Script 2",
                    "roi_percentage": 200.0,
                    "win_rate": 0.7,
                    "total_trades": 80,
                    "realized_profits_usdt": 2000.0,
                    "starting_balance": 1000.0,
                    "final_balance": 3000.0,
                    "peak_balance": 3100.0,
                    "analysis_timestamp": "2024-01-02T12:00:00"
                }
            ],
            "saved_at": "2024-01-02T12:00:00"
        }
        
        # Save test data
        result_path = self.cache.base_dir / "reports" / "analysis_result_test_lab_789_20240102_120000.json"
        with open(result_path, 'w') as f:
            json.dump(test_data, f)
        
        # Load analysis result
        loaded_data = self.cache.load_analysis_result("test_lab_789")
        
        # Verify loaded data
        assert loaded_data is not None
        assert loaded_data["lab_id"] == "test_lab_789"
        assert loaded_data["lab_name"] == "Test Lab 2"
        assert len(loaded_data["top_backtests"]) == 1
        assert loaded_data["top_backtests"][0]["backtest_id"] == "test_bt_456"
    
    def test_list_analysis_results(self):
        """Test listing all analysis results"""
        # Create multiple test files
        test_files = [
            "analysis_result_lab1_20240101_120000.json",
            "analysis_result_lab2_20240102_130000.json",
            "analysis_result_lab1_20240103_140000.json"
        ]
        
        for filename in test_files:
            file_path = self.cache.base_dir / "reports" / filename
            with open(file_path, 'w') as f:
                json.dump({
                    "lab_id": filename.split('_')[2],
                    "lab_name": f"Lab {filename.split('_')[2]}",
                    "saved_at": "2024-01-01T12:00:00",
                    "top_backtests": [],
                    "total_backtests": 10
                }, f)
        
        # List analysis results
        results = self.cache.list_analysis_results()
        
        # Verify results
        assert len(results) == 3
        assert all("lab_id" in result for result in results)
        assert all("saved_at" in result for result in results)
    
    def test_refresh_backtest_cache(self):
        """Test cache refresh functionality"""
        # Create test cache file
        cache_file = self.cache.base_dir / "backtests" / "test_lab_123_test_bt_456.json"
        with open(cache_file, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Verify file exists
        assert cache_file.exists()
        
        # Refresh cache
        result = self.cache.refresh_backtest_cache("test_lab_123", "test_bt_456")
        
        # Verify file was deleted
        assert result is True
        assert not cache_file.exists()


class TestInteractiveAnalyzer:
    """Test interactive analyzer functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = InteractiveAnalyzer()
        self.analyzer.cache = UnifiedCacheManager()
        self.analyzer.cache.base_dir = Path(self.temp_dir)
        
        # Create cache directory structure
        (self.analyzer.cache.base_dir / "backtests").mkdir(parents=True, exist_ok=True)
        (self.analyzer.cache.base_dir / "reports").mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch('pyHaasAPI.cli.interactive_analyzer.HaasAnalyzer')
    def test_connect(self, mock_analyzer_class):
        """Test API connection"""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer.connect.return_value = True
        mock_analyzer_class.return_value = mock_analyzer
        
        # Test connection
        result = self.analyzer.connect()
        
        # Verify connection
        assert result is True
        assert self.analyzer.analyzer is not None
    
    def test_get_cached_labs(self):
        """Test getting cached labs list"""
        # Create test cache files
        test_files = [
            "lab1_backtest1.json",
            "lab1_backtest2.json",
            "lab2_backtest1.json",
            "lab3_backtest1.json"
        ]
        
        for filename in test_files:
            file_path = self.analyzer.cache.base_dir / "backtests" / filename
            with open(file_path, 'w') as f:
                json.dump({"test": "data"}, f)
        
        # Get cached labs
        lab_ids = self.analyzer.get_cached_labs()
        
        # Verify results
        assert len(lab_ids) == 3
        assert "lab1" in lab_ids
        assert "lab2" in lab_ids
        assert "lab3" in lab_ids
    
    def test_calculate_advanced_metrics(self):
        """Test advanced metrics calculation"""
        # Create mock backtest
        backtest = BacktestAnalysis(
            backtest_id="test_bt_123",
            lab_id="test_lab_456",
            generation_idx=1,
            population_idx=2,
            market_tag="BINANCE_BTC_USDT_",
            script_id="script_789",
            script_name="Test Script",
            roi_percentage=150.5,
            calculated_roi_percentage=145.2,
            roi_difference=5.3,
            win_rate=0.65,
            total_trades=100,
            max_drawdown=15.2,
            realized_profits_usdt=1500.0,
            pc_value=1.5,
            avg_profit_per_trade=15.0,
            profit_factor=1.8,
            sharpe_ratio=1.2,
            starting_balance=1000.0,
            final_balance=2500.0,
            peak_balance=2600.0,
            analysis_timestamp="2024-01-01T12:00:00"
        )
        
        # Mock cache data
        mock_cache_data = {
            "trades": [
                {"profit_loss": 100, "fees": 5, "exit_time": "2024-01-01T12:00:00"},
                {"profit_loss": -50, "fees": 3, "exit_time": "2024-01-01T13:00:00"},
                {"profit_loss": 200, "fees": 10, "exit_time": "2024-01-01T14:00:00"}
            ]
        }
        
        with patch.object(self.analyzer.cache, 'load_backtest_cache', return_value=mock_cache_data):
            with patch('pyHaasAPI.cli.interactive_analyzer.BacktestDataExtractor') as mock_extractor:
                # Mock extractor
                mock_summary = Mock()
                mock_trade1 = Mock()
                mock_trade1.profit_loss = 100
                mock_trade1.fees = 5
                mock_trade1.exit_time = "2024-01-01T12:00:00"
                mock_trade1.net_pnl = 95
                
                mock_trade2 = Mock()
                mock_trade2.profit_loss = -50
                mock_trade2.fees = 3
                mock_trade2.exit_time = "2024-01-01T13:00:00"
                mock_trade2.net_pnl = -53
                
                mock_trade3 = Mock()
                mock_trade3.profit_loss = 200
                mock_trade3.fees = 10
                mock_trade3.exit_time = "2024-01-01T14:00:00"
                mock_trade3.net_pnl = 190
                
                mock_summary.trades = [mock_trade1, mock_trade2, mock_trade3]
                mock_extractor.return_value.extract_backtest_summary.return_value = mock_summary
                
                # Calculate metrics
                metrics = self.analyzer.calculate_advanced_metrics(backtest)
                
                # Verify metrics
                assert "roe_percentage" in metrics
                assert "dd_usdt" in metrics
                assert "dd_percentage" in metrics
                assert "risk_score" in metrics
                assert "stability_score" in metrics
                assert "advanced_metrics" in metrics
    
    def test_sort_backtests(self):
        """Test backtest sorting functionality"""
        # Create test backtests
        backtests = [
            BacktestAnalysis(
                backtest_id="bt1", lab_id="lab1", generation_idx=1, population_idx=1,
                market_tag="BTC", script_id="s1", script_name="Script 1",
                roi_percentage=100.0, calculated_roi_percentage=95.0, roi_difference=5.0,
                win_rate=0.6, total_trades=50, max_drawdown=10.0,
                realized_profits_usdt=1000.0, pc_value=1.0, avg_profit_per_trade=20.0,
                profit_factor=1.5, sharpe_ratio=1.0, starting_balance=1000.0,
                final_balance=2000.0, peak_balance=2100.0, analysis_timestamp="2024-01-01"
            ),
            BacktestAnalysis(
                backtest_id="bt2", lab_id="lab1", generation_idx=1, population_idx=2,
                market_tag="BTC", script_id="s1", script_name="Script 1",
                roi_percentage=200.0, calculated_roi_percentage=190.0, roi_difference=10.0,
                win_rate=0.7, total_trades=80, max_drawdown=15.0,
                realized_profits_usdt=2000.0, pc_value=2.0, avg_profit_per_trade=25.0,
                profit_factor=2.0, sharpe_ratio=1.5, starting_balance=1000.0,
                final_balance=3000.0, peak_balance=3100.0, analysis_timestamp="2024-01-01"
            )
        ]
        
        # Test sorting by ROI
        sorted_by_roi = self.analyzer._sort_backtests(backtests, 'roi')
        assert sorted_by_roi[0].roi_percentage == 200.0
        assert sorted_by_roi[1].roi_percentage == 100.0
        
        # Test sorting by win rate
        sorted_by_winrate = self.analyzer._sort_backtests(backtests, 'winrate')
        assert sorted_by_winrate[0].win_rate == 0.7
        assert sorted_by_winrate[1].win_rate == 0.6


class TestVisualizationTool:
    """Test visualization tool functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.tool = VisualizationTool()
        self.tool.cache = UnifiedCacheManager()
        self.tool.cache.base_dir = Path(self.temp_dir)
        
        # Create cache directory structure
        (self.tool.cache.base_dir / "backtests").mkdir(parents=True, exist_ok=True)
        (self.tool.cache.base_dir / "reports").mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    @patch('pyHaasAPI.cli.visualization_tool.VISUALIZATION_AVAILABLE', True)
    def test_generate_equity_curve(self):
        """Test equity curve generation"""
        # Create mock backtest
        backtest = BacktestAnalysis(
            backtest_id="test_bt_123",
            lab_id="test_lab_456",
            generation_idx=1,
            population_idx=2,
            market_tag="BINANCE_BTC_USDT_",
            script_id="script_789",
            script_name="Test Script",
            roi_percentage=150.5,
            calculated_roi_percentage=145.2,
            roi_difference=5.3,
            win_rate=0.65,
            total_trades=100,
            max_drawdown=15.2,
            realized_profits_usdt=1500.0,
            pc_value=1.5,
            avg_profit_per_trade=15.0,
            profit_factor=1.8,
            sharpe_ratio=1.2,
            starting_balance=1000.0,
            final_balance=2500.0,
            peak_balance=2600.0,
            analysis_timestamp="2024-01-01T12:00:00"
        )
        
        # Mock cache data
        mock_cache_data = {
            "trades": [
                {"profit_loss": 100, "fees": 5, "exit_time": "2024-01-01T12:00:00"},
                {"profit_loss": -50, "fees": 3, "exit_time": "2024-01-01T13:00:00"},
                {"profit_loss": 200, "fees": 10, "exit_time": "2024-01-01T14:00:00"}
            ]
        }
        
        with patch.object(self.tool.cache, 'load_backtest_cache', return_value=mock_cache_data):
            with patch('pyHaasAPI.cli.visualization_tool.BacktestDataExtractor') as mock_extractor:
                # Mock extractor
                mock_summary = Mock()
                mock_trade = Mock()
                mock_trade.net_pnl = 95
                mock_trade.exit_time = "2024-01-01T12:00:00"
                mock_summary.trades = [mock_trade, mock_trade, mock_trade]
                mock_extractor.return_value.extract_backtest_summary.return_value = mock_summary
                
                # Mock numpy functions
                with patch('pyHaasAPI.cli.visualization_tool.np') as mock_np:
                    mock_np.maximum.accumulate.return_value = [95, 190, 285]
                    mock_np.cumsum.return_value = [95, 190, 285]
                
                # Generate equity curve
                result = self.tool.generate_equity_curve(backtest)
                
                # Verify result
                assert result != ""  # Should return a file path
    
    @patch('pyHaasAPI.cli.visualization_tool.VISUALIZATION_AVAILABLE', False)
    def test_visualization_not_available(self):
        """Test handling when visualization libraries are not available"""
        backtest = BacktestAnalysis(
            backtest_id="test_bt_123",
            lab_id="test_lab_456",
            generation_idx=1,
            population_idx=2,
            market_tag="BTC", script_id="s1", script_name="Script 1",
            roi_percentage=100.0, calculated_roi_percentage=95.0, roi_difference=5.0,
            win_rate=0.6, total_trades=50, max_drawdown=10.0,
            realized_profits_usdt=1000.0, pc_value=1.0, avg_profit_per_trade=20.0,
            profit_factor=1.5, sharpe_ratio=1.0, starting_balance=1000.0,
            final_balance=2000.0, peak_balance=2100.0, analysis_timestamp="2024-01-01"
        )
        
        # Try to generate equity curve
        result = self.tool.generate_equity_curve(backtest)
        
        # Should return empty string when visualization not available
        assert result == ""


class TestIntegrationWorkflow:
    """Test complete integration workflow"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = UnifiedCacheManager()
        self.cache.base_dir = Path(self.temp_dir)
        
        # Create cache directory structure
        (self.cache.base_dir / "backtests").mkdir(parents=True, exist_ok=True)
        (self.cache.base_dir / "reports").mkdir(parents=True, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_workflow_simulation(self):
        """Test complete workflow simulation"""
        # Step 1: Create mock analysis result
        backtest = BacktestAnalysis(
            backtest_id="workflow_bt_123",
            lab_id="workflow_lab_456",
            generation_idx=1,
            population_idx=2,
            market_tag="BINANCE_BTC_USDT_",
            script_id="script_789",
            script_name="Workflow Script",
            roi_percentage=175.0,
            calculated_roi_percentage=170.0,
            roi_difference=5.0,
            win_rate=0.68,
            total_trades=120,
            max_drawdown=12.5,
            realized_profits_usdt=1750.0,
            pc_value=1.75,
            avg_profit_per_trade=14.58,
            profit_factor=2.1,
            sharpe_ratio=1.4,
            starting_balance=1000.0,
            final_balance=2750.0,
            peak_balance=2800.0,
            analysis_timestamp="2024-01-01T12:00:00"
        )
        
        result = LabAnalysisResult(
            lab_id="workflow_lab_456",
            lab_name="Workflow Lab",
            total_backtests=30,
            analyzed_backtests=15,
            processing_time=45.0,
            top_backtests=[backtest],
            bots_created=0,
            analysis_timestamp="2024-01-01T12:00:00"
        )
        
        # Step 2: Save analysis result
        result_path = self.cache.save_analysis_result(result)
        assert result_path.exists()
        
        # Step 3: Load analysis result
        loaded_data = self.cache.load_analysis_result("workflow_lab_456")
        assert loaded_data is not None
        assert loaded_data["lab_id"] == "workflow_lab_456"
        
        # Step 4: List analysis results
        results = self.cache.list_analysis_results()
        assert len(results) == 1
        assert results[0]["lab_id"] == "workflow_lab_456"
        
        # Step 5: Verify data consistency
        assert loaded_data["top_backtests"][0]["backtest_id"] == "workflow_bt_123"
        assert loaded_data["top_backtests"][0]["roi_percentage"] == 175.0
        assert loaded_data["top_backtests"][0]["win_rate"] == 0.68


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
