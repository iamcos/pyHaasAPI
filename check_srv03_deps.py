import asyncio
import os
import json
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI

async def main():
    load_dotenv()
    sm = ServerManager(Settings())
    print("Connecting to srv02...")
    if not await sm.connect_server('srv02'):
        print("Failed to connect to srv03")
        return
    
    api_config = APIConfig(host='127.0.0.1', port=8090, email=os.getenv('API_EMAIL'), password=os.getenv('API_PASSWORD'))
    client = AsyncHaasClient(api_config)
    await client.connect()
    
    auth = AuthenticationManager(client, api_config)
    await auth.ensure_authenticated()
    
    script_api = ScriptAPI(client, auth)
    scripts = await script_api.get_all_scripts()
    
    search_terms = ["SuperTrendExt", "StorchRSI", "Stochastic_Momentum_Index", "All_BF_Markets", "Momentum", "All_BF"]
    
    for s in scripts:
        if s.name.startswith("CC_"):
            print(f"CC Script: {s.name} ({s.script_id})")
        for term in search_terms:
            if term.lower() in s.name.lower():
                print(f"Match found: {s.name} ({s.script_id})")
                
    await client.close()
    await sm.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
