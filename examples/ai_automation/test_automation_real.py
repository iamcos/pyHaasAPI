import asyncio
import os
from dotenv import load_dotenv
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.services.script_automation_service import ScriptAutomationService
from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService
from pathlib import Path

# Load env for credentials
load_dotenv()

MANUAL_SCALPER_SCRIPT = """
-- Antigravity Real-Server Scalper
function Initialize()
    AddInput("RSI_Period", 14, "RSI calculation period")
    AddInput("RSI_Threshold", 30, "Buy only if RSI is below this")
    AddInput("Buy_Drop", 1.0, "Percentage drop for buy signal")
    AddInput("Sell_Gain", 1.5, "Percentage gain for sell signal")
    
    self.last_buy_price = 0
    self.in_position = false
    Log("AI Scalper Initialized")
end

function OnTick()
    local current_price = GetPrice(settings.market)
    -- This call might fail if RSI is not available for this market/TF
    local rsi = RSI(settings.market, settings.RSI_Period)
    
    Log("Tick: " .. current_price .. " RSI: " .. rsi)
end
"""

async def main():
    print("=== Real-Server Automation Test (srv02) ===")
    
    settings = Settings()
    sm = ServerManager(settings)
    
    if not await sm.connect_server('srv02'):
        print("FAILED to connect to srv02")
        return

    # Initialize Client & APIs
    # NOTE: APIConfig.from_env() will load srv02 settings from .env
    from pyHaasAPI.config.api_config import APIConfig
    client_config = APIConfig()
    # Ensure we use 127.0.0.1 for the tunnel
    client_config.host = "127.0.0.1"
    client_config.port = 8090
    
    client = AsyncHaasClient(client_config)
    auth = AuthenticationManager(client, client_config)
    
    try:
        await auth.authenticate()
        print(f"Authenticated as User ID: {auth.user_id}")
        
        script_api = ScriptAPI(client, auth)
        automation = ScriptAutomationService(
            script_api=script_api,
            backtest_api=BacktestAPI(client, auth),
            lab_api=LabAPI(client, auth),
            bot_api=BotAPI(client, auth),
            cached_analysis_service=CachedAnalysisService(cache_dir=Path("data"))
        )
        
        # 1. Create Script
        print("\n[Step 1] Creating/Updating Script...")
        # Use script_type=1 for SmartScript (v2)
        script_id = await automation.create_or_update_script(
            name="AI Scalper Demo Real",
            content=MANUAL_SCALPER_SCRIPT,
            description="Real server test of automation",
            script_type=1
        )
        print(f"✓ Script ID: {script_id}")
        
        # 2. Run Debug Test
        print("\n[Step 2] Running Debug Test...")
        # Note: We use a common market from Binance
        debug_settings = {
            "market": "BINANCE_BTC_USDT_",
            "TradeAmount": 100.0,
            "RSI_Period": 14,
            "RSI_Threshold": 30,
            "Buy_Drop": 1.0,
            "Sell_Gain": 1.5
        }
        
        # Run debug test (also using script_type=1)
        debug_result = await automation.debug_script(script_id, debug_settings, script_type=1)
        print(f"Debug Success (API): {debug_result.get('success')}")
        print(f"Extracted Errors: {debug_result.get('errors')}")
        
        if debug_result.get('errors'):
            print("\nErrors Found:")
            for err in debug_result['errors']:
                print(f"  - {err}")
        else:
            print("\n✓ No compilation errors found!")

    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
