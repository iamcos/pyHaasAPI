import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.config.api_config import APIConfig

async def main():
    load_dotenv()
    settings = Settings()
    sm = ServerManager(settings)
    
    try:
        await sm.connect_server('srv02')
        api_config = APIConfig()
        api_config.host = "127.0.0.1"
        api_config.port = 8090
        
        client = AsyncHaasClient(api_config)
        auth = AuthenticationManager(client, api_config)
        await auth.authenticate()
        
        script_api = ScriptAPI(client, auth)
        
        # Create a bad script
        script_id = await script_api.add_script("Diagnostic Bad Script", "NonExistentCommand()", script_type=1)
        print(f"Created script: {script_id.script_id}")
        
        # Debug it
        debug_settings = {"market": "BINANCE_BTC_USDT_"}
        result = await script_api.execute_debug_test(script_id.script_id, 1, debug_settings)
        
        print("\n--- RAW DEBUG RESULT ---")
        print(json.dumps(result, indent=2))
        
    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

