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

async def connect_and_get_api(sm, server_name):
    print(f"Connecting to {server_name}...")
    if not await sm.connect_server(server_name):
        print(f"Failed to connect to {server_name}")
        return None
    
    api_config = APIConfig(host='127.0.0.1', port=8090, email=os.getenv('API_EMAIL'), password=os.getenv('API_PASSWORD'))
    client = AsyncHaasClient(api_config)
    await client.connect()
    
    auth = AuthenticationManager(client, api_config)
    await auth.ensure_authenticated()
    
    return ScriptAPI(client, auth), client

async def main():
    load_dotenv()
    sm = ServerManager(Settings())
    
    # Get source script from srv02
    api_source, client_source = await connect_and_get_api(sm, 'srv02')
    # SuperTrend Extended (UPDATED) (63c243f503214cd4b1e3dfe4140c2b8d)
    source_script_id = "63c243f503214cd4b1e3dfe4140c2b8d"
    print(f"Fetching script {source_script_id} from srv02...")
    st_ext = await api_source.get_script_item(source_script_id)
    await client_source.close()
    
    # Disconnect srv02 before connecting to srv03
    await sm.disconnect_server('srv02')
    
    # Upload to srv03
    api_target, client_target = await connect_and_get_api(sm, 'srv03')
    print(f"Uploading script to srv03 as {st_ext.name}...")
    try:
        await api_target.add_script(
            script_name=st_ext.name,
            script_content=st_ext.source_code,
            description=st_ext.description or "Dependency for SuperTrend bots"
        )
        print("Success!")
    except Exception as e:
        print(f"Failed to upload: {e}")
        
    await client_target.close()
    await sm.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
