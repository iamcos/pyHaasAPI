import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys
import os

# Add the project root to sys.path to enable module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backtest_data_analyzer import BacktestAnalyzer
from pyHaasAPI.backtest_object import BacktestMetadata, BacktestRuntime, BacktestPosition, BacktestLogs

class TestBacktestAnalyzer(unittest.TestCase):

    def setUp(self):
        # Mock the HaasAPI executor
        self.mock_executor = MagicMock()

        # Mock BacktestManager and its methods
        self.mock_backtest_manager = MagicMock()
        
        # Patch BacktestManager within BacktestAnalyzer to use our mock
        # This is important because BacktestAnalyzer instantiates BacktestManager internally
        with patch('backtest_data_analyzer.BacktestManager', return_value=self.mock_backtest_manager):
            self.analyzer = BacktestAnalyzer(self.mock_executor)

    def test_get_all_labs(self):
        # Mock get_backtest_history to return sample data
        self.mock_backtest_manager.get_backtest_history.return_value = [
            {"BacktestId": "bt1", "ScriptId": "script_A", "ScriptName": "Script A"},
            {"BacktestId": "bt2", "ScriptId": "script_B", "ScriptName": "Script B"},
            {"BacktestId": "bt3", "ScriptId": "script_A", "ScriptName": "Script A"},
        ]

        labs = self.analyzer.get_all_labs()
        self.assertEqual(len(labs), 2)
        self.assertIn({"label": "script_A", "value": "script_A"}, labs)
        self.assertIn({"label": "script_B", "value": "script_B"}, labs)
        self.mock_backtest_manager.get_backtest_history.assert_called_once()

    def test_get_all_labs_no_history(self):
        self.mock_backtest_manager.get_backtest_history.return_value = []
        labs = self.analyzer.get_all_labs()
        self.assertEqual(len(labs), 0)

    def test_get_backtests_for_lab(self):
        # Mock get_backtest_history and get_backtest
        self.mock_backtest_manager.get_backtest_history.return_value = [
            {"BacktestId": "bt1", "ScriptId": "script_A", "ScriptName": "Script A", "BS": 1678886400, "BE": 1678972800, "Status": 1},
            {"BacktestId": "bt2", "ScriptId": "script_B", "ScriptName": "Script B", "BS": 1678886400, "BE": 1678972800, "Status": 1},
            {"BacktestId": "bt3", "ScriptId": "script_A", "ScriptName": "Script A", "BS": 1678886400, "BE": 1678972800, "Status": 1},
        ]

        # Mock BacktestObject instances
        mock_bt_obj_1 = MagicMock()
        mock_bt_obj_1.metadata = BacktestMetadata(
            backtest_id="bt1", script_id="script_A", script_name="Script A",
            account_id="acc1", market_tag="BTC/USD",
            start_time=datetime.fromtimestamp(1678886400), end_time=datetime.fromtimestamp(1678972800),
            execution_start=datetime.fromtimestamp(1678886400), execution_end=datetime.fromtimestamp(1678972800),
            status=1
        )
        mock_bt_obj_1.runtime = BacktestRuntime(
            total_profit=100.50, win_rate=75.0, max_drawdown=10.20,
            sharpe_ratio=1.5, profit_factor=2.0, total_trades=10, winning_trades=7, losing_trades=3
        )

        mock_bt_obj_3 = MagicMock()
        mock_bt_obj_3.metadata = BacktestMetadata(
            backtest_id="bt3", script_id="script_A", script_name="Script A",
            account_id="acc1", market_tag="ETH/USD",
            start_time=datetime.fromtimestamp(1678886400), end_time=datetime.fromtimestamp(1678972800),
            execution_start=datetime.fromtimestamp(1678886400), execution_end=datetime.fromtimestamp(1678972800),
            status=1
        )
        mock_bt_obj_3.runtime = BacktestRuntime(
            total_profit=50.25, win_rate=60.0, max_drawdown=5.10,
            sharpe_ratio=1.0, profit_factor=1.5, total_trades=5, winning_trades=3, losing_trades=2
        )

        self.mock_backtest_manager.get_backtest.side_effect = {"bt1": mock_bt_obj_1, "bt3": mock_bt_obj_3}.get

        table_data = self.analyzer.get_backtests_for_lab("script_A")
        self.assertEqual(len(table_data), 2)
        self.assertEqual(table_data[0]["backtest_id"], "bt1")
        self.assertEqual(table_data[0]["total_profit"], "100.50")
        self.assertEqual(table_data[1]["backtest_id"], "bt3")
        self.assertEqual(table_data[1]["total_profit"], "50.25")
        self.mock_backtest_manager.get_backtest.assert_any_call("bt1")
        self.mock_backtest_manager.get_backtest.assert_any_call("bt3")

    def test_get_backtest_analysis_data(self):
        # Mock a BacktestObject with full data
        mock_bt_obj = MagicMock()
        mock_bt_obj.metadata = BacktestMetadata(
            backtest_id="bt_analysis", script_id="script_C", script_name="Script C",
            account_id="acc2", market_tag="LTC/USD",
            start_time=datetime.fromtimestamp(1678886400), end_time=datetime.fromtimestamp(1678972800),
            execution_start=datetime.fromtimestamp(1678886400), execution_end=datetime.fromtimestamp(1678972800),
            status=1
        )
        mock_bt_obj.runtime = BacktestRuntime(
            total_profit=200.00, win_rate=80.0, max_drawdown=15.00,
            sharpe_ratio=2.0, profit_factor=3.0, total_trades=20, winning_trades=16, losing_trades=4
        )
        mock_bt_obj.profit_chart = {
            "timestamps": [1678886400, 1678886400 + 3600, 1678886400 + 7200],
            "profits": [0.0, 50.0, 200.0]
        }
        mock_bt_obj.positions = [
            BacktestPosition(position_id="pos1", entry_time=datetime.now(), exit_time=datetime.now(), entry_price=100, exit_price=105, quantity=1, side="long", profit_loss=5.0),
            BacktestPosition(position_id="pos2", entry_time=datetime.now(), exit_time=datetime.now(), entry_price=200, exit_price=190, quantity=1, side="short", profit_loss=10.0),
        ]

        self.mock_backtest_manager.get_backtest.return_value = mock_bt_obj

        analysis_data = self.analyzer.get_backtest_analysis_data("bt_analysis")

        self.assertIn("summary", analysis_data)
        self.assertEqual(analysis_data["summary"]["total_profit"], 200.00)
        self.assertEqual(analysis_data["profit_chart"]["profits"], [0.0, 50.0, 200.0])
        self.assertEqual(analysis_data["trade_distribution"], [5.0, 10.0])
        self.mock_backtest_manager.get_backtest.assert_called_once_with("bt_analysis")

    def test_get_backtest_analysis_data_no_profit_chart(self):
        mock_bt_obj = MagicMock()
        mock_bt_obj.metadata = BacktestMetadata(
            backtest_id="bt_no_chart", script_id="script_D", script_name="Script D",
            account_id="acc3", market_tag="XRP/USD",
            start_time=datetime.fromtimestamp(1678886400), end_time=datetime.fromtimestamp(1678972800),
            execution_start=datetime.fromtimestamp(1678886400), execution_end=datetime.fromtimestamp(1678972800),
            status=1
        )
        mock_bt_obj.runtime = BacktestRuntime(
            total_profit=10.00, win_rate=50.0, max_drawdown=2.00,
            sharpe_ratio=0.5, profit_factor=1.1, total_trades=2, winning_trades=1, losing_trades=1
        )
        mock_bt_obj.profit_chart = None # Simulate no profit chart data
        mock_bt_obj.positions = []

        self.mock_backtest_manager.get_backtest.return_value = mock_bt_obj

        analysis_data = self.analyzer.get_backtest_analysis_data("bt_no_chart")
        self.assertEqual(analysis_data["profit_chart"]["profits"], [])
        self.assertEqual(analysis_data["trade_distribution"], [])

if __name__ == '__main__':
    unittest.main()