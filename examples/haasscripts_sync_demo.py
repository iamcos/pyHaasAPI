"""
HaasScripts.com Community Sync Demo
Demonstrates importing scripts and their dependencies from the community website.
"""

import asyncio
import os
import json
import logging
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.external.haasscripts_com import HaasScriptsClient, ScriptSyncService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CommunitySync")

async def main():
    load_dotenv()
    
    # 1. Connect to Haas Trading Server (srv03 for Engine tasks)
    settings = Settings()
    sm = ServerManager(settings)
    
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
    
    script_api = ScriptAPI(client, auth_manager)
    
    try:
        # 2. Setup Community Client
        ext_client = HaasScriptsClient()
        sync_service = ScriptSyncService(ext_client, script_api)
        
        print("\n--- Community Script Sync ---")
        
        # Example Script ID (RSI-VWAP Trading Bot for Deribit port)
        target_script_id = "f4a48731bdab4e71a89445c33dfbc052"
        
        print(f"Target: {target_script_id}")
        
        # 3. Pull and Import
        success = await sync_service.import_from_community(target_script_id)
        
        if success:
            print("\nSync completed successfully (Main script & Dependencies imported).")
            
            # 4. Discovery & Debug Verification
            print("\nRunning compilation checks on imported scripts...")
            scripts = await script_api.get_all_scripts()
            
            for s in scripts:
                if s.description and "community" in s.description.lower():
                    print(f"Checking {s.name} ({s.script_id})...")
                    try:
                        settings = {
                            "AccountGuid": "", 
                            "PriceMarket": "BINANCE_BTC_USDT",
                            "TradeAmount": 1.0,
                        }
                        logs = await script_api.execute_debug_test(s.script_id, 0, settings)
                        
                        success_flag = any("Compile test OK" in line for line in logs.get('Data', []))
                        if success_flag:
                            print(f"  [PASS] {s.name} compiles correctly.")
                        else:
                            print(f"  [FAIL] {s.name} has compilation issues.")
                    except Exception as e:
                        print(f"  [ERROR] {s.name} check failed: {e}")
        else:
            print("\nSync failed. Check logs for authentication or network issues.")
                
    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
