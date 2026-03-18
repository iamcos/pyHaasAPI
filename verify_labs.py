import asyncio
import os
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings

async def verify_labs():
    print("Verifying Lab & Backtest APIs...")
    load_dotenv()
    
    settings = Settings()
    sm = ServerManager(settings)
    print("Setting up SSH tunnel to srv03...")
    connected = await sm.connect_server('srv03')
    if not connected:
        print("Failed to establish SSH tunnel.")
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
    
    # 1. Get Labs
    print("1. Fetching existing labs...")
    labs = await lab_api.get_labs()
    print(f"Found {len(labs)} labs.")
    if labs:
        print(f"First lab: {labs[0].name} (ID: {labs[0].lab_id})")
        
        # 2. Get Lab Details
        print(f"\n2. Fetching details for lab {labs[0].lab_id}...")
        details = await lab_api.get_lab_details(labs[0].lab_id)
        print(f"Lab details fetched. Config max epochs: {details.config.max_epochs}")
        
        # 3. Get Backtest Results for Lab
        print(f"\n3. Fetching backtest results for lab {labs[0].lab_id}...")
        try:
            results = await backtest_api.get_backtest_result(labs[0].lab_id)
            print(f"Found {len(results.items)} backtests.")
            if results.items:
                print(f"First backtest ROI: {results.items[0].roi}%")
        except Exception as e:
            print(f"No backtest results found or error occurred: {e}")
            
    await client.close()
    
if __name__ == "__main__":
    asyncio.run(verify_labs())
