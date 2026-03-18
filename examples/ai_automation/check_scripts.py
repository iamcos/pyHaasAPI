import asyncio
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.config.api_config import APIConfig

async def main():
    try:
        settings = Settings()
        sm = ServerManager(settings)
        await sm.connect_server('srv02')
        
        client_config = APIConfig()
        client_config.host = "127.0.0.1"
        client_config.port = 8090
        
        client = AsyncHaasClient(client_config)
        auth = AuthenticationManager(client, client_config)
        await auth.authenticate()
        
        api = ScriptAPI(client, auth)
        print("Fetching scripts...")
        scripts = await api.get_all_scripts()
        
        print("\nExisting Scripts Sample:")
        for s in scripts[:10]:
            # We need to find the attribute name for script type. ScriptItem might not have it.
            # Let's check attributes
            attrs = [a for a in dir(s) if not a.startswith('_')]
            print(f"Name: {s.name}, ID: {s.script_id}, Attrs: {attrs}")
            # Usually it's ScriptType or Type
            if hasattr(s, 'script_type'): print(f"  Type: {s.script_type}")
            if hasattr(s, 'type'): print(f"  Type: {s.type}")
        
        await client.close()
        await sm.shutdown()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
