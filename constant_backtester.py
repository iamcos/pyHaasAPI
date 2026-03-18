import asyncio
import os
import json
import uuid
from datetime import datetime, timedelta

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.models.backtest import ExecuteBacktestRequest
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.server_manager import ServerManager
from dotenv import load_dotenv

load_dotenv()

async def run_constant_backtesting():
    sm = ServerManager(Settings())
    print("Setting up SSH tunnel to srv03...")
    connected = await sm.connect_server('srv03')
    if not connected:
        print("Failed to establish SSH tunnel.")
        return
        
    config = APIConfig(
        host="127.0.0.1",
        port=8090,
        email=os.getenv("API_EMAIL"),
        password=os.getenv("API_PASSWORD")
    )
    
    try:
        async with AsyncHaasClient(config) as client:
            auth = AuthenticationManager(client, config)
            # Ensure authenticated
            await auth.ensure_authenticated()
            
            lab_api = LabAPI(client, auth)
            backtest_api = BacktestAPI(client, auth)
            script_api = ScriptAPI(client, auth)

            print("Fetching existing labs to gather trading pairs...")
            try:
                labs = await lab_api.get_labs()
                unique_markets = list(set([lab.market_tag for lab in labs if lab.market_tag]))
                
                # Fallback if no specific markets could be retrieved
                if not unique_markets:
                    unique_markets = ["BINANCE_BTC_USDT_", "BINANCE_ETH_USDT_", "BINANCE_XRP_USDT_"]
            except Exception as e:
                print(f"Error fetching labs: {e}. Using default Binance pairs.")
                unique_markets = ["BINANCE_BTC_USDT_", "BINANCE_ETH_USDT_", "BINANCE_XRP_USDT_"]
                
            print(f"Discovered market pairs to test against: {unique_markets}")

            # Load testable scripts from our categorization output
            try:
                with open("script_categorization.json", "r") as f:
                    cat_data = json.load(f)
                testable_scripts = cat_data.get("TESTABLE", [])
            except (FileNotFoundError, json.JSONDecodeError):
                print("Could not load script_categorization.json. Please run categorize_scripts_automated.py first.")
                return

            if not testable_scripts:
                print("No TESTABLE scripts found.")
                return

            print(f"Initializing constant backtesting across {len(testable_scripts)} scripts and {len(unique_markets)} pairs.")
            
            # Loop continuously for constant backtesting
            while True:
                print(f"--- Starting Next Backtest Cycle at {datetime.now()} for Testable Scripts ---")
                for script_info in testable_scripts:
                    script_id = script_info["id"]
                    script_name = script_info["name"]

                    # Fetch real default parameters from script
                    script_record = {}
                    try:
                        record_full = await script_api.get_script_record(script_id)
                        script_parameters = {}
                        if record_full and hasattr(record_full, 'inputs'):
                            # Translate Record properties if applicable or mock
                            pass
                        
                        raw_record = await client.post_json(
                            endpoint="/HaasScriptAPI.php",
                            data={"channel": "GET_SCRIPT_RECORD", "scriptid": script_id, "scripttype": 0}
                        )
                        if "Data" in raw_record and "I" in raw_record["Data"]:
                            for param in raw_record["Data"]["I"]:
                                if "K" in param and "V" in param:
                                    script_parameters[param["K"]] = param["V"]
                    except Exception as e:
                        print(f"Could not load script inputs for {script_name}, using defaults. Error: {e}")
                        script_parameters = {}

                    for market in unique_markets:
                        print(f"Running backtest for {script_name} on {market}...")
                        
                        settings = {
                            "botId": str(uuid.uuid4()),
                            "botName": f"TestBot_{script_name}_{market}",
                            "accountId": "TEST_ACCOUNT_01",
                            "marketTag": market,
                            "leverage": 20.0,
                            "marginMode": 0, # CROSS
                            "positionMode": 1, # HEDGE
                            "interval": 15,
                            "chartStyle": 300,
                            "tradeAmount": 1000.0,
                            "orderTemplate": 500,
                            "scriptParameters": script_parameters
                        }
                        
                        start_time = datetime.now() - timedelta(days=7) # 1 week window
                        end_time = datetime.now()
                        
                        request = ExecuteBacktestRequest(
                            backtest_id=str(uuid.uuid4()),
                            script_id=script_id,
                            settings=settings,
                            start_unix=int(start_time.timestamp()),
                            end_unix=int(end_time.timestamp())
                        )
                        
                        try:
                            result = await backtest_api.execute_backtest(request)
                            print(f"Success! Backtest ID: {result.backtest_id}")
                        except Exception as e:
                            print(f"Backtest failed for {script_name} on {market}: {e}")
                        
                        # Throttle to avoid overloading backend
                        await asyncio.sleep(5)
                
                print("Finished one full sweep of all testable scripts.")
                # Optional: pause before the next giant loop
                await asyncio.sleep(60)
                
    finally:
        print("Shutting down SSH tunnel...")
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(run_constant_backtesting())
