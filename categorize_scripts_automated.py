import asyncio
import os
import json
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.server_manager import ServerManager
from dotenv import load_dotenv

load_dotenv()

USER_SCRIPT_LIST = [
    "Smi", "Emdi", "Stoch-rsi FW2", "Supertrend Stoch-RSI", "Alpha", 
    "Simple RSING VWAP Strategy", "Blueprint", "⭕️RSI Ssa scalper", 
    "ADX +KC+Stoch", "ADX BB STOCH Scalper", "YATS", "Yolodiv", 
    "Smokybot MK4", "Smokybot MK3", "Smokybot RS MK1", "Smmdh shenom", 
    "Leved Long Scalper", "Simple Leverage Scalper v3", "Blood Emperor", 
    "Kobalt SMDB", "ZRB SMOD", "Bitget Fut CTA", "Band-it RSI", "SMM 2.6c", 
    "SMMDH v3.3", "SMMD 2.51 SMOD", "Nadaraya (non Repaint)", "Triple MA SMA", 
    "AIB - Advanced Index Bot", "Simple DCA Bot", "Firetron’s Hedged DCA Dipper", 
    "HedgedDCADipper", "Simple Market Maker BFH", "BOT LONG SHORT MACD DCA", 
    "Firetron’s Hedge Race", "Kernel Trading Machine", "RSI-VWAP Trading Bot", 
    "Intelli Alice Bot", "5 minute Standard Deviation Scalping Bot Redux", 
    "Simple HullMA Heiki tradebot", "Flash Crash Bot", "MadHatter Bot", 
    "VE Unmanaged Trading", "Nadaraya bot", "Nadaraya-Watson: Envelope", 
    "Spagetti Bot", "Keltner Grid Bot v2 (KGB)", "Swing Trading Safely with Super Trend Signal v1", 
    "Bot Engine", "Simple Grid Bot (FUTURES)", "HB 3.0", 
    "Triangle-Arbitrage", "BitcoinFib30-Clean", "Market Making Bot", 
    "Predictor remote", "FBI", "1 scalper"
]

async def categorize_scripts():
    sm = ServerManager(Settings())
    print("Setting up SSH tunnel to srv03...")
    connected = await sm.connect_server('srv03')
    if not connected:
        print("Failed to establish SSH tunnel.")
        return
        
    config = APIConfig(
        host="127.0.0.1",
        port=8092,
        email=os.getenv("API_EMAIL"),
        password=os.getenv("API_PASSWORD")
    )
    
    try:
        async with AsyncHaasClient(config) as client:
            auth = AuthenticationManager(client, config)
            script_api = ScriptAPI(client, auth)
            
            print("Fetching remote scripts...")
            try:
                remote_scripts = await script_api.get_all_scripts()
            except Exception as e:
                print(f"Failed to fetch scripts: {e}")
                return
                
            remote_map = {s.name: s.script_id for s in remote_scripts}
            
            results = {
                "TESTABLE": [],
                "MISSING_REMOTE": [],
                "BROKEN": [],
                "NOT_TESTABLE": [] 
            }
            
            for script_name in USER_SCRIPT_LIST:
                found_id = None
                matched_name = script_name
                
                # Simple fuzzy matching
                for r_name, r_id in remote_map.items():
                    if script_name.lower() in r_name.lower():
                        found_id = r_id
                        matched_name = r_name
                        break
                
                if not found_id:
                    results["MISSING_REMOTE"].append(script_name)
                    continue
                    
                print(f"Checking {matched_name} ({found_id})...")
                try:
                    # Call execute_debug_test to verify compilation
                    # We need to know the script type. Assuming 0 for Trading Script.
                    debug_result = await script_api.execute_debug_test(found_id, 0, {})
                    
                    # Fetch record to check for errors explicitly
                    record = await script_api.get_script_record(found_id)
                    
                    if record.compile_errors and len(record.compile_errors) > 0:
                        results["BROKEN"].append({
                            "id": found_id,
                            "name": matched_name, 
                            "errors": record.compile_errors
                        })
                    else:
                        results["TESTABLE"].append({
                            "id": found_id,
                            "name": matched_name
                        })
                except Exception as e:
                    print(f"Error checking {matched_name}: {e}")
                    results["BROKEN"].append({
                        "id": found_id,
                        "name": matched_name, 
                        "error": str(e)
                    })

        with open("script_categorization.json", "w") as f:
            json.dump(results, f, indent=4)
        
        print("Categorization complete. Results saved to script_categorization.json")
    finally:
        print("Shutting down SSH tunnel...")
        await sm.shutdown()


if __name__ == "__main__":
    asyncio.run(categorize_scripts())
