"""
Script Availability Checker
Lists scripts on the server and cross-references with the user's list.
"""

import asyncio
import os
import json
import logging
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScriptChecker")

user_list = [
    "Emdi", "Smi", "Stoch-rsi FW2", "Supertrend Stoch-RSI", "Alpha", 
    "Simple RSING VWAP Strategy", "Blueprint", "⭕️RSI Ssa scalper", 
    "ADX +KC+Stoch", "ADX BB STOCH Scalper", "YATS", "Yolodiv", 
    "Smokybot MK4", "Smokybot MK3", "Smokybot RS MK1", "Smmdh shenom", 
    "Leved Long Scalper", "Simple Leverage Scalper v3", "Blood Emperor", 
    "Kobalt SMDB", "ZRB SMOD", "Bitget Fut CTA", "Band-it RSI", "SMM 2.6c", 
    "SMMDH v3.3", "SMMD 2.51 SMOD", "Nadaraya (non Repaint)", 
    "Triple MA SMA By Ratimbum V2.1 With RSI EXIT clause", 
    "AIB - Advanced Index Bot", "Simple DCA Bot", "Firetron’s Hedged DCA Dipper", 
    "HedgedDCADipper", "Simple Market Maker BFH", "BOT LONG SHORT MACD DCA 1%profit (V1)", 
    "Firetron’s Hedge Race", "Kernel Trading Machine", "RSI-VWAP Trading Bot for Deribit (port)", 
    "Haasonline Original – Intelli Alice Bot", "5 minute Standard Deviation Scalping Bot Redux", 
    "Simple HullMA Heiki tradebot", "[HaasOnline] Flash Crash Bot (v4 only)", 
    "MadHatter Bot + mods", "MadHatter Bot v2", "VE Unmanaged Trading", 
    "Nadaraya bot", "Nadaraya-Watson: Envelope (Non-Repainting)", "Spagetti Bot (VE)", 
    "[EXPERIMENTAL] [pshaiBot] Keltner Grid Bot v2 (KGB)", 
    "Swing Trading Safely with Super Trend Signal v1 [Spot Version]", 
    "Bot Engine – Strooth Version [FEBE Mod]", "Script: [pshaiBot] YATS Bot", 
    "Simple Grid Bot (FUTURES)", "HB 3.0", "Triangle-Arbitrage, PROOF-OF-CONCEPT", 
    "BitcoinFib30-Clean", "Market Making Bot", "Predictor remote", "FBI", 
    "1 scalper", "BitcoinFib30- Fibonacci,Williams R%, Super Saf –"
]

async def main():
    load_dotenv()
    
    settings = Settings()
    sm = ServerManager(settings)
    
    logger.info("Connecting to srv03 (Main Engine)...")
    if not await sm.connect_server('srv03'):
        logger.error("Failed to connect to srv03.")
        return

    api_config = APIConfig(
        host="127.0.0.1", 
        port=8090,
        email=os.getenv("API_EMAIL"),
        password=os.getenv("API_PASSWORD")
    )
    
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth_manager = AuthenticationManager(client, api_config)
    await auth_manager.ensure_authenticated()
    
    script_api = ScriptAPI(client, auth_manager)
    
    try:
        server_scripts = await script_api.get_all_scripts()
        server_script_names = [s.name for s in server_scripts]
        
        found = []
        missing = []
        
        for name in user_list:
            match = next((s for s in server_scripts if name.lower() in s.name.lower() or s.name.lower() in name.lower()), None)
            if match:
                found.append({"requested": name, "found": match.name, "id": match.script_id})
            else:
                missing.append(name)
                
        print("\n--- FOUND SCRIPTS ---")
        for f in found:
            print(f"- {f['requested']} -> {f['found']} ({f['id']})")
            
        print("\n--- MISSING SCRIPTS ---")
        for m in missing:
            print(f"- {m}")
            
        # Also check other servers if needed, but for now we list srv02.
        
    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
