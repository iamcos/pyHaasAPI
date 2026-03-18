import asyncio
import os
from pyHaasAPI.api.external.haasscripts_com import HaasScriptsClient
from dotenv import load_dotenv

async def main():
    load_dotenv()
    async with HaasScriptsClient() as client:
        # Search for Stochastic Momentum Index
        print("Searching for Stochastic Momentum Index...")
        results = await client.search_scripts('Stochastic Momentum Index')
        for r in results:
            print(f"Found: {r['name']} ({r['id']})")
            
        # Search for All BF Markets
        print("\nSearching for All BF Markets...")
        results = await client.search_scripts('All BF Markets')
        for r in results:
            print(f"Found: {r['name']} ({r['id']})")

if __name__ == '__main__':
    asyncio.run(main())
