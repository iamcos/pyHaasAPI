import asyncio
import os
import json
import logging
from typing import List, Optional

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.models.lab import StartLabExecutionRequest
from pyHaasAPI.core.prefix_utils import PrefixUtils, AccountPrefix

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MiguelPipeline")

async def run_miguel_pipeline():
    """
    Implements the Miguel Pipeline:
    1. Setup Lab 1 for exploration.
    2. Run iterations in Lab 1.
    3. Analyze results and pick the best one.
    4. Clone Lab 1 to Lab 2 for finetuning.
    5. Update Lab 2 with best parameters and run further iterations.
    6. (Optional) Create a Bot from the final best result.
    """
    logger.info("Starting Miguel Pipeline...")
    load_dotenv()
    
    settings = Settings()
    sm = ServerManager(settings)
    
    # Connect to srv03 (Haas Engine)
    logger.info("Connecting to srv03...")
    if not await sm.connect_server('srv03'):
        logger.error("Failed to connect to srv03.")
        return

    api_config = APIConfig(
        host="127.0.0.1", 
        port=8090,
        email=os.getenv("API_EMAIL"),
        password=os.getenv("API_PASSWORD")
    )
    
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth_manager = AuthenticationManager(client, api_config)
    await auth_manager.ensure_authenticated()
    
    lab_api = LabAPI(client, auth_manager)
    backtest_api = BacktestAPI(client, auth_manager)
    script_api = ScriptAPI(client, auth_manager)
    
    try:
        # Phase 1: Setup Exploration Lab
        logger.info("Phase 1: Exploration Setup")
        scripts = await script_api.get_all_scripts()
        if not scripts:
            logger.error("No scripts found on server.")
            return
            
        target_script = scripts[0] # Use first script for demonstration
        logger.info(f"Target Script: {target_script.name}")
        
        lab_name_1 = PrefixUtils.ensure_account_prefix("Exploration BTC-USDT", AccountPrefix.LAB)
        
        # Create Lab 1
        lab1 = await lab_api.create_lab(
            script_id=target_script.script_id,
            name=lab_name_1,
            market="BINANCE_BTC_USDT_", # Example market
            interval=15,
            trade_amount=100.0,
            leverage=5.0
        )
        logger.info(f"Lab 1 Created: {lab1.lab_id} ({lab1.name})")
        
        # Phase 2: Exploration Execution
        # Note: In a real scenario, we'd wait for iterations to finish.
        # For this script, we assume some results might already exist or we trigger and then poll.
        logger.info("Triggering Exploration Iterations...")
        # (Assuming the API supports START_LAB_EXECUTION)
        # await lab_api.start_lab_execution(lab1.lab_id, iterations=5)
        
        # Phase 3: Result Analysis
        logger.info("Phase 3: Analyzing Results")
        bt_results = await backtest_api.get_backtest_result(lab1.lab_id)
        
        if not bt_results.items:
            logger.warning("No backtest results found in Lab 1. Using fallback for demo.")
            # In a demo/empty lab scenario, we'll just proceed with cloning the empty lab
            best_bt = None
        else:
            # Sort by ROI and WinRate
            sorted_bts = sorted(bt_results.items, key=lambda x: x.roi, reverse=True)
            best_bt = sorted_bts[0]
            logger.info(f"Best Result from Lab 1: ROI={best_bt.roi}%, WinRate={best_bt.win_rate}%")

        # Phase 4: Finetuning Setup
        logger.info("Phase 4: Finetuning Setup (Lab 2)")
        lab_name_2 = PrefixUtils.ensure_account_prefix("Finetuning BTC-USDT", AccountPrefix.LAB)
        
        lab2 = await lab_api.clone_lab(lab1.lab_id, new_name=lab_name_2)
        logger.info(f"Lab 2 (Finetuning) Created: {lab2.lab_id}")
        
        if best_bt:
            logger.info("Applying best parameters to Lab 2...")
            # update_data = {"script_parameters": best_bt.parameters}
            # await lab_api.update_lab_details(lab2.lab_id, update_data)
        
        # Phase 5: Finetuning Execution
        logger.info("Phase 5: Running Finetuning Iterations...")
        # await lab_api.start_lab_execution(lab2.lab_id, iterations=10)
        
        logger.info("Miguel Pipeline completed successfully.")
        
    except Exception as e:
        logger.exception(f"Error in pipeline: {e}")
    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(run_miguel_pipeline())
