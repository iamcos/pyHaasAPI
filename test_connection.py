import asyncio
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.server_manager import ServerManager

async def main():
    try:
        settings = Settings()
        sm = ServerManager(settings)
        print("Attempting to connect to srv02...")
        # Since I'm using the library, this will set up the SSH tunnel
        success = await sm.connect_server('srv02')
        print(f"Connection result: {success}")
        
        if success:
            print("Fetching srv02 resources...")
            resources = await sm.get_server_resources('srv02')
            print(f"Resources: {resources}")
            
        await sm.shutdown()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
