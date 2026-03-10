"""
Bulk Tester for Available User Scripts
Tests all identifying scripts from the user's list.
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.api.script.script_api import ScriptAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UserScriptTester")

found_scripts = [
    {"requested": "Emdi", "match": "EMDIbot 0.1.3 cross", "id": "f7481e261ca64ecb9c5bd8934791bdb5"},
    {"requested": "Smi", "match": "SMIbot_0.6.2-orig", "id": "22dd22b7bb93438b860422ba38775e8d"},
    {"requested": "Supertrend Stoch-RSI", "match": "[pshaiBot] SuperTrend Stoch-RSI bot", "id": "3d115cc5fdc64092a4e244c013bf69c1"},
    {"requested": "Alpha", "match": "[pshaiBot] Bot Blueprint (ALPHA TEST)", "id": "c8f6e6745b3d48e8af12a38fe60410ec"},
    {"requested": "Simple RSING VWAP Strategy", "match": "Simple RSING VWAP Strategy", "id": "e3568d723be04e13836b9b4b7e02e57d"},
    {"requested": "Blueprint", "match": "[pshaiBot] Bot Blueprint (ALPHA TEST)", "id": "c8f6e6745b3d48e8af12a38fe60410ec"},
    {"requested": "ADX +KC+Stoch", "match": "[pshaiBot] ADX KC STOCH Scalper", "id": "4adbb93f81434052bb3175583b616301"},
    {"requested": "ADX BB STOCH Scalper", "match": "ADX BB STOCH Scalper", "id": "7dda6a1e59594d4588b62619a848a6ae"},
    {"requested": "YATS", "match": "YATS bot", "id": "3fd8bff29c3347ffa72576ede717a13e"},
    {"requested": "Yolodiv", "match": "YOLO div", "id": "c552f5f597af416d96e61c556b943016"},
    {"requested": "Smokybot MK4", "match": "Smokybot MK4", "id": "a9384f0c86b149e89bb351d7c47aa539"},
    {"requested": "Smokybot MK3", "match": "Smokybot MK3", "id": "c8dcbe2231d14604837d336cb8ba8b5d"},
    {"requested": "Simple Leverage Scalper v3", "match": "[pshaiBot] Simple Leverage Scalper v3", "id": "90385fe7741b499e9afb497fd6c67533"},
    {"requested": "SMMDH v3.3", "match": "SMMDH v3.3", "id": "749ee7ccf4a6428d84c15477488ff6dc"},
    {"requested": "SMMD 2.51 SMOD", "match": "SMMD v2.51", "id": "3b20c600bb87499ca0f5c96316481ad5"},
    {"requested": "ZRB SMOD", "match": "Zone Recovery Bot Hedge SMOD", "id": "705c8d0d6692429c92ebe7ded0be8f0a"},
    {"requested": "AIB - Advanced Index Bot", "match": "Haasonline Original - Advanced Index Bot", "id": "f9d08fda66924ff6bc7b3e679d699a2a"},
    {"requested": "Simple DCA Bot", "match": "Haasonline Original - Dollar Cost Average Bot", "id": "7a4b2f91d6e53c8942a0bd7e1f5896c4"},
    {"requested": "RSI-VWAP Trading Bot for Deribit (port)", "match": "[pshaiBot] RSI-VWAP Trading Bot for Deribit (port)", "id": "f4a48731bdab4e71a89445c33dfbc052"},
    {"requested": "Haasonline Original – Intelli Alice Bot", "match": "Haasonline Original - Intelli Alice Bot", "id": "5ce06f1eb6f3d21c8c1331d45451937e"},
    {"requested": "[HaasOnline] Flash Crash Bot (v4 only)", "match": "Haasonline Original - Flash Crash Bot", "id": "ef8f16dcb428836c691985c41f88927b"},
    {"requested": "Swing Trading Safely with Super Trend Signal v1", "match": "Swing Trading Safely with Super Trend Signal v1", "id": "a4c9fc8e20664df4aa9b316f34fb67f7"},
    {"requested": "Simple Grid Bot (FUTURES)", "match": "Simple Grid Bot (FUTURES)", "id": "91413037a2a34a86957508a34c96ce48"},
    {"requested": "Triangle-Arbitrage", "match": "Triangle Arbitrage Bot", "id": "bac0964a4947401a9aaf865849ef7326"},
    {"requested": "Market Making Bot", "match": "Haasonline Original - Market Making Bot", "id": "8b14a78bfa90b14b40aeccbddebeda13"},
]

async def test_script(script_api, script_id, name):
    try:
        settings = {
            "AccountGuid": "",
            "PriceMarket": "BINANCE_BTC_USDT",
            "Interval": 15,
            "TradeAmount": 1.0,
            "Leverage": 1.0,
        }
        logs = await script_api.execute_debug_test(script_id, 0, settings)
        
        # Check for success
        success = any("Compile test OK" in line for line in logs.get('Data', []))
        if success:
            return {"status": "SUCCESS", "logs": logs.get('Data', [])[:5]}
        else:
            return {"status": "FAILED", "logs": logs.get('Data', [])} # Show full logs for debugging
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

async def main():
    load_dotenv()
    sm = ServerManager(Settings())
    await sm.connect_server('srv03')
    api_config = APIConfig(host='127.0.0.1', port=8090, email=os.getenv('API_EMAIL'), password=os.getenv('API_PASSWORD'))
    client = AsyncHaasClient(api_config)
    await client.connect()
    auth = AuthenticationManager(client, api_config)
    await auth.ensure_authenticated()
    script_api = ScriptAPI(client, auth)
    
    results = {}
    
    for script in found_scripts:
        print(f"Testing {script['match']}...")
        res = await test_script(script_api, script['id'], script['match'])
        results[script['requested']] = res
        print(f"  Result: {res['status']}")
        
    with open("user_script_test_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    await client.close()
    await sm.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
