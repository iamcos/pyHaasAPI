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
    await sm.connect_server('srv02')
    api_config = APIConfig(host='127.0.0.1', port=8090, email=os.getenv('API_EMAIL'), password=os.getenv('API_PASSWORD'))
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth = AuthenticationManager(client, api_config)
    await auth.ensure_authenticated()
    api = ScriptAPI(client, auth)
    scripts = await api.get_all_scripts()
    for s in scripts:
        print(f"{s.name} ({s.script_id}) | {s.description[:50]}")
    await client.close()
    await sm.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
