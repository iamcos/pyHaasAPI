import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from pyHaasAPI.backtest_object import BacktestManager, BacktestObject
from pyHaasAPI.api import RequestsExecutor # Changed from HaasAPI to RequestsExecutor
from pyHaasAPI.types import Guest, Authenticated # Import Guest and Authenticated states

logger = logging.getLogger(__name__)

class BacktestAnalyzer:
    def __init__(self, executor):
        self.executor = executor
        self.backtest_manager = BacktestManager(executor)

    def get_all_labs(self) -> List[Dict[str, str]]:
        """
        Retrieves all unique ScriptIds to represent labs.
        Returns a list of dictionaries suitable for Dash dropdown options.
        """
        logger.info("Fetching all backtest history to identify labs...")
        backtest_history = self.backtest_manager.get_backtest_history()
        
        logger.info(f"Raw backtest history from manager: {backtest_history}")

        if not backtest_history:
            logger.warning("No backtest history found.")
            return []

        labs = sorted(list(set([bt.get("ScriptId") for bt in backtest_history if bt.get("ScriptId")])))
        options = [{"label": lab, "value": lab} for lab in labs]
        
        logger.info(f"Found {len(labs)} unique labs: {labs}")
        return options

    def get_backtests_for_lab(self, selected_lab_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves backtests for a given lab (ScriptId) and formats them for a Dash table.
        """
        logger.info(f"Fetching backtests for lab: {selected_lab_id}")
        if not selected_lab_id:
            return []

        backtest_history = self.backtest_manager.get_backtest_history()
        logger.info(f"Raw backtest history for filtering: {backtest_history}")

        filtered_backtests = [bt for bt in backtest_history if bt.get("ScriptId") == selected_lab_id]
        logger.info(f"Filtered backtests for lab {selected_lab_id}: {filtered_backtests}")
        
        table_data = []
        for bt_summary in filtered_backtests:
            backtest_obj = self.backtest_manager.get_backtest(bt_summary["BacktestId"])
            logger.info(f"Processing backtest {bt_summary['BacktestId']}: metadata={backtest_obj.metadata}, runtime={backtest_obj.runtime}")

            if backtest_obj.runtime and backtest_obj.metadata:
                table_data.append({
                    "backtest_id": backtest_obj.metadata.backtest_id,
                    "script_name": backtest_obj.metadata.script_name,
                    "market_tag": backtest_obj.metadata.market_tag,
                    "start_time": backtest_obj.metadata.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": backtest_obj.metadata.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_profit": f"{backtest_obj.runtime.total_profit:.2f}",
                    "win_rate": f"{backtest_obj.runtime.win_rate:.2f}%",
                    "max_drawdown": f"{backtest_obj.runtime.max_drawdown:.2f}",
                    "status": backtest_obj.metadata.status,
                })
            else:
                logger.warning(f"Runtime or metadata not available for backtest {bt_summary['BacktestId']}")
                table_data.append({
                    "backtest_id": bt_summary.get("BacktestId"),
                    "script_name": bt_summary.get("ScriptName"),
                    "market_tag": bt_summary.get("MarketTag"),
                    "start_time": datetime.fromtimestamp(bt_summary.get("BS", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": datetime.fromtimestamp(bt_summary.get("BE", 0)).strftime("%Y-%m-%d %H:%M:%S"),
                    "total_profit": "N/A",
                    "win_rate": "N/A",
                    "max_drawdown": "N/A",
                    "status": bt_summary.get("Status"),
                })
        logger.info(f"Found {len(table_data)} backtests for lab {selected_lab_id}.")
        return table_data

    def get_backtest_analysis_data(self, backtest_id: str) -> Dict[str, Any]:
        """
        Retrieves detailed analysis data for a single backtest.
        """
        logger.info(f"Retrieving detailed analysis for backtest: {backtest_id}")
        backtest_obj = self.backtest_manager.get_backtest(backtest_id)
        logger.info(f"Backtest object for analysis {backtest_id}: metadata={backtest_obj.metadata}, runtime={backtest_obj.runtime}, profit_chart_loaded={backtest_obj._profit_chart is not None}, positions_loaded={backtest_obj._positions is not None}")

        analysis_data = {
            "summary": {},
            "profit_chart": {"timestamps": [], "profits": []},
            "trade_distribution": []
        }

        if backtest_obj.metadata and backtest_obj.runtime:
            analysis_data["summary"] = {
                "script_name": backtest_obj.metadata.script_name,
                "market_tag": backtest_obj.metadata.market_tag,
                "total_profit": backtest_obj.runtime.total_profit,
                "win_rate": backtest_obj.runtime.win_rate,
                "max_drawdown": backtest_obj.runtime.max_drawdown,
                "sharpe_ratio": backtest_obj.runtime.sharpe_ratio,
                "profit_factor": backtest_obj.runtime.profit_factor,
                "total_trades": backtest_obj.runtime.total_trades,
                "winning_trades": backtest_obj.runtime.winning_trades,
                "losing_trades": backtest_obj.runtime.losing_trades,
            }

            if backtest_obj.profit_chart and backtest_obj.profit_chart.get("timestamps") and backtest_obj.profit_chart.get("profits"):
                analysis_data["profit_chart"] = {
                    "timestamps": backtest_obj.profit_chart["timestamps"],
                    "profits": backtest_obj.profit_chart["profits"]
                }
            else:
                logger.warning(f"Profit chart data not available for {backtest_id}")

            if backtest_obj.positions:
                analysis_data["trade_distribution"] = [pos.profit_loss for pos in backtest_obj.positions]
            else:
                logger.warning(f"Positions data not available for {backtest_id}")
        else:
            logger.warning(f"Metadata or runtime not available for detailed analysis of {backtest_id}")

        return analysis_data

# Initialize HaasAPI executor
try:
    # Start with a Guest executor
    guest_executor = RequestsExecutor(host="localhost", port=8000, state=Guest())
    logger.info("Attempting to authenticate executor...")
    # Placeholder credentials - REPLACE WITH ACTUAL CREDENTIALS FOR FULL FUNCTIONALITY
    # These are just to allow the code to proceed for debugging purposes.
    # In a real application, you would get these securely from the user.
    try:
        executor = guest_executor.authenticate(email="your_email@example.com", password="your_password")
        logger.info("Executor authenticated successfully.")
    except Exception as auth_e:
        logger.warning(f"Authentication failed: {auth_e}. Proceeding with Guest executor. Backtest data may be limited or unavailable.")
        executor = guest_executor # Fallback to guest executor if authentication fails

except Exception as e:
    logger.warning(f"Could not initialize HaasAPI executor: {e}. Using a dummy executor.")
    class DummyExecutor:
        def __init__(self):
            pass
        def get_account_balance(self, account_id):
            return {"success": False, "error": "Dummy executor, no real connection"}
    executor = DummyExecutor()

# Instantiate the analyzer for direct use or for passing to the Dash app
backtest_analyzer = BacktestAnalyzer(executor)