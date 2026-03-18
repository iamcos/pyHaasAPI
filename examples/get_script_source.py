import json
import asyncio
import os
import sys
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI

async def main():
    if len(sys.argv) < 2:
        print("Usage: python get_script_source.py <script_id>")
        return
    script_id = sys.argv[1]
    load_dotenv()
    sm = ServerManager(Settings())
    await sm.connect_server('srv02')
    api_config = APIConfig(host='127.0.0.1', port=8090, email=os.getenv('API_EMAIL'), password=os.getenv('API_PASSWORD'))
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth = AuthenticationManager(client, api_config)
    await auth.ensure_authenticated()
    api = ScriptAPI(client, auth)
    # response = await client.get_json(...)
    response = await client.get_json(
        endpoint="/HaasScriptAPI.php",
        params={
            "channel": "GET_SCRIPT_RECORD",
            "scriptid": script_id,
            "interfacekey": auth.interface_key,
            "userid": auth.user_id,
        }
    )
    print(json.dumps(response, indent=2))
    await client.close()
    await sm.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
