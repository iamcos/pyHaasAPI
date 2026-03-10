"""
Automated Script Ingestor
Searches and imports missing scripts from HaasScripts.com.
"""

import asyncio
import os
import json
import logging
import re
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.external.haasscripts_com import HaasScriptsClient, ScriptSyncService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScriptIngestor")

missing_scripts = [
    "Stoch-rsi FW2", "⭕️RSI Ssa scalper", "ADX +KC+Stoch", "Yolodiv", 
    "Smokybot RS MK1", "Smmdh shenom", "Leved Long Scalper", "Blood Emperor", 
    "Kobalt SMDB", "ZRB SMOD", "Bitget Fut CTA", "Band-it RSI", "SMM 2.6c", 
    "SMMD 2.51 SMOD", "Nadaraya (non Repaint)", 
    "Triple MA SMA By Ratimbum V2.1 With RSI EXIT clause", "Simple DCA Bot", 
    "Firetron’s Hedged DCA Dipper", "HedgedDCADipper", "Simple Market Maker BFH", 
    "BOT LONG SHORT MACD DCA 1%profit (V1)", "Firetron’s Hedge Race", 
    "Kernel Trading Machine", "MadHatter Bot v2", "VE Unmanaged Trading", 
    "Nadaraya bot", "Nadaraya-Watson: Envelope (Non-Repainting)", "Spagetti Bot (VE)", 
    "[EXPERIMENTAL] [pshaiBot] Keltner Grid Bot v2 (KGB)", 
    "Bot Engine – Strooth Version [FEBE Mod]", "HB 3.0", "BitcoinFib30-Clean", 
    "Predictor remote", "FBI", "1 scalper", "BitcoinFib30- Fibonacci,Williams R%, Super Saf –"
]

missing_deps = ["CC_SuperTrendExt", "CC_CC_StorchRSI", "CC_Stochastic_Momentum_Index", "CC_All_BF_Markets"]

async def main():
    load_dotenv()
    sm = ServerManager(Settings())
    await sm.connect_server('srv02')
    api_config = APIConfig(host='127.0.0.1', port=8090, email=os.getenv('API_EMAIL'), password=os.getenv('API_PASSWORD'))
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth = AuthenticationManager(client, api_config)
    await auth.ensure_authenticated()
    script_api = ScriptAPI(client, auth)
    
    ext_client = HaasScriptsClient()
    sync_service = ScriptSyncService(ext_client, script_api)
    
    async with ext_client as ext:
        # Search and import missing scripts
        for query in missing_scripts:
            print(f"\nSearching for missing script: {query}...")
            search_results = await ext.search_scripts(query)
            if search_results:
                print(f"  Found {len(search_results)} results. Importing first match: {search_results[0]['name']}...")
                await sync_service.import_from_community(search_results[0]['id'])
            else:
                print(f"  No exact match for {query}. Trying related keywords...")
                # Try a broader search with the first word
                search_results = await ext.search_scripts(query.split()[0])
                for res in search_results[:2]:
                    print(f"  Found related: {res['name']}. Importing...")
                    await sync_service.import_from_community(res['id'])
                    
        # Search and import missing dependencies
        for dep in missing_deps:
            print(f"\nSearching for missing dependency: {dep}...")
            # GUID is usually the last part of the name if it's CC_GUID
            guid_match = re.search(r'([a-fA-F0-9-]{32,})', dep)
            if guid_match:
                print(f"  Detected GUID: {guid_match.group(1)}. Resolving...")
                await sync_service.import_from_community(guid_match.group(1))
            else:
                # Search by name (strip CC_)
                clean_name = dep.replace("CC_", "")
                search_results = await ext.search_scripts(clean_name)
                if search_results:
                    print(f"  Found {len(search_results)} results. Importing: {search_results[0]['name']}...")
                    await sync_service.import_from_community(search_results[0]['id'])
                    
    await client.close()
    await sm.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
