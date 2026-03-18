import asyncio
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.server_manager import ServerManager

async def main():
    try:
        settings = Settings()
        sm = ServerManager(settings)
        print("Attempting to connect to srv03...")
        success = await sm.connect_server('srv03')
        print(f"srv03 Connection result: {success}")
        if success:
            resources = await sm.get_server_resources('srv03')
            print(f"Resources: {resources}")
        await sm.shutdown()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

