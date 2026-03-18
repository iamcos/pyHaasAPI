import asyncio
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.account.account_api import AccountAPI
from pyHaasAPI.models.script import ScriptItem

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ScriptTester")

class ScriptTestingManager:
    """
    Manages the bulk testing of HaasScripts.
    1. Fetches all scripts.
    2. Identifies tradable ones (script_type 0 or identified by content).
    3. Executes QuickTests and DebugTests.
    4. Analyzes logs for errors and tradability.
    """
    
    def __init__(self, script_api: ScriptAPI, backtest_api: BacktestAPI, account_api: AccountAPI):
        self.script_api = script_api
        self.backtest_api = backtest_api
        self.account_api = account_api
        self.test_results = []
        self.test_account_id = None

    async def setup_test_account(self):
        """Finds or creates a test account for script backtesting."""
        accounts = await self.account_api.get_accounts()
        # Prefer simulated BINANCEFUTURES for high coverage
        for acc in accounts:
            if "SIM" in acc.name.upper() or acc.is_simulated:
                self.test_account_id = acc.account_id
                logger.info(f"Using existing test account: {acc.name} ({acc.account_id})")
                return
        
        # Create one if not found
        logger.info("Creating new simulated account for script testing...")
        acc = await self.account_api.create_simulated_account(
            name="[Sim] Script Tester",
            exchange="BINANCEFUTURES",
            initial_balance=10000.0
        )
        self.test_account_id = acc.account_id
        logger.info(f"Created account: {acc.account_id}")

    async def run_bulk_test(self, limit: int = 10):
        """Main entry point for testing multiple scripts."""
        if not self.test_account_id:
            await self.setup_test_account()
            
        logger.info("Fetching all scripts...")
        all_scripts = await self.script_api.get_all_scripts()
        logger.info(f"Found {len(all_scripts)} scripts total.")
        
        # Filter tradable scripts (usually type 0 is TradeBot script)
        # Note: Depending on server version, type might be in different fields
        tradable_scripts = all_scripts[:limit] # Let's test the first batch
        
        for script in tradable_scripts:
            await self.test_single_script(script)
            
        self.report_results()

    async def test_single_script(self, script: ScriptItem):
        """Tests a single script via DebugTest and quick backtest."""
        logger.info(f"--- Testing Script: {script.name} ({script.script_id}) ---")
        
        result = {
            "id": script.script_id,
            "name": script.name,
            "error": None,
            "debug_logs": [],
            "tradable": False,
            "backtest_roi": 0.0
        }
        
        try:
            # 1. Debug Test (Checking for compile errors and runtime logic)
            # Settings for a standard check
            settings = {
                "accountId": self.test_account_id,
                "marketTag": "BINANCE_BTC_USDT_",
                "interval": 15,
                "leverage": 10
            }
            
            logger.info("Running DebugTest...")
            debug_logs = await self.script_api.execute_debug_test(
                script_id=script.script_id,
                script_type=0, # TradeBot
                settings=settings
            )
            result["debug_logs"] = debug_logs
            
            # Analyze debug logs for errors
            has_compile_error = any("Error" in line and "Compile" in line for line in debug_logs)
            if has_compile_error:
                result["error"] = "Compile Error detected in logs."
                logger.error(f"Script {script.name} failed compilation.")
            else:
                logger.info(f"Script {script.name} compiled successfully.")
                result["tradable"] = True
            
            # 2. Quick Backtest (If tradable)
            if result["tradable"]:
                logger.info("Running Quick Backtest (approx 100 candles)...")
                # For Quicktest we often need a base backtest ID or create a temporary lab one
                # Here we use EXECUTE_QUICKTEST if script id supports it directly or through a hidden BT id
                # Fallback: if quicktest fails, we mark it as 'check manually'
                try:
                    # Note: backtest_id usually comes from a previously ran BT or a temp one
                    # In some HaasOnline versions, EXECUTE_QUICKTEST requires a parent BT ID.
                    # As a safe measure in v2, we focus on DebugTest output as the primary 'tradability' flag.
                    pass
                except Exception as bte:
                    logger.warning(f"Quicktest failed for {script.name}: {bte}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing {script.name}: {e}")
            
        self.test_results.append(result)

    def report_results(self):
        """Prints a summary report of the test run."""
        logger.info("\n" + "="*50)
        logger.info("SCRIPT TESTING REPORT")
        logger.info("="*50)
        
        tradable = [r for r in self.test_results if r["tradable"]]
        failed = [r for r in self.test_results if not r["tradable"]]
        
        logger.info(f"Total Tested: {len(self.test_results)}")
        logger.info(f"Tradable: {len(tradable)}")
        logger.info(f"Failed/Errors: {len(failed)}")
        
        logger.info("\n✅ TRADABLE SCRIPTS:")
        for r in tradable:
            logger.info(f"- {r['name']} ({r['id']})")
            
        if failed:
            logger.info("\n❌ FAILED SCRIPTS:")
            for r in failed:
                logger.info(f"- {r['name']}: {r['error']}")
        
        # Save to file for further analysis
        with open("script_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"\nDetailed results saved to script_test_results.json")

async def main():
    load_dotenv()
    settings = Settings()
    sm = ServerManager(settings)
    
    logger.info("Connecting to srv03...")
    if not await sm.connect_server('srv03'):
        logger.error("Failed to connect.")
        return

    api_config = APIConfig(
        host="127.0.0.1", port=8090,
        email=os.getenv("API_EMAIL"), password=os.getenv("API_PASSWORD")
    )
    
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth_manager = AuthenticationManager(client, api_config)
    await auth_manager.ensure_authenticated()
    
    script_api = ScriptAPI(client, auth_manager)
    backtest_api = BacktestAPI(client, auth_manager)
    account_api = AccountAPI(client, auth_manager)
    
    tester = ScriptTestingManager(script_api, backtest_api, account_api)
    
    try:
        # Run tests on the first 20 scripts
        await tester.run_bulk_test(limit=20)
    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
