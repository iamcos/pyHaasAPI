import asyncio
import os
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.log.log_api import LogAPI

async def test_log_api():
    # Load credentials from .env
    from dotenv import load_dotenv
    load_dotenv()
    
    from pyHaasAPI.config.settings import settings
    
    config = APIConfig()
    # Try both API_PASSWORD and API_PASSWORD_LOCAL
    passwords = [os.getenv("HTS_SUDO_PASSWORD"), os.getenv("API_PASSWORD"), os.getenv("API_PASSWORD_LOCAL")]
    passwords = [p for p in passwords if p]
    
    # We'll try the first one first. If it fails, we might need a more complex loop, 
    # but for now let's just use the priority list.
    sudo_pass = passwords[0] if passwords else None
    if sudo_pass:
        settings.sudo_password = sudo_pass
        os.environ["HTS_SUDO_PASSWORD"] = sudo_pass
    
    # Explicitly enable remote logging for test
    config.enable_remote_logging = True
    
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    log_api = LogAPI(client, auth_manager)
    
    servers = ["srv01", "srv02", "srv03"]
    
    for server in servers:
        print(f"\n--- Testing LogAPI.get_sessions on {server} ---")
        try:
            sessions = await log_api.get_sessions(server)
            if sessions:
                print(f"[{server}] Found {len(sessions)} sessions:")
                for s in sessions:
                    print(f"  - ID: {s['id']}, Name: {s['name']}, Status: {s['status']}")
                    
                    # Try to get a snapshot for the first session
                    print(f"  - Fetching snapshot for {s['id']}...")
                    snapshot = await log_api.get_session_snapshot(server, s['id'])
                    print(f"  - Snapshot (first 200 chars): {snapshot[:200]}...")
            else:
                print(f"[{server}] No active sessions found.")
        except Exception as e:
            print(f"[{server}] Operation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_log_api())
