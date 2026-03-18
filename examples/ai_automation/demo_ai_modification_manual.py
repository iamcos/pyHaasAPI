"""
Script Modification & Error Learning Demonstration (Manual AI Mode)
Target: srv02 (Real Server)

This demo showcases:
1. Modifying an existing HaasScript via natural language.
2. The auto-debug-and-fix loop.
3. The Error Learning repository persisting successful fixes.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.services.script_automation_service import ScriptAutomationService
from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService
from pyHaasAPI.services.script_error_repository import ScriptErrorRepository

# Mocking the AI generator for "Manual AI" mode
class ManualAIGenerator:
    async def modify_script(self, current_code: str, modification: str) -> str:
        print(f"\n[AI] Received modification request: {modification}")
        # Logic: Adding a Trailing Stop Loss to the base scalper
        # This is the "Manual" generation by Antigravity
        modified_code = current_code.replace(
            "-- Strategy logic (to be filled by AI generation)",
            """-- Modified with Trailing Stop Loss
    local tsl_percent = 2.0
    local highest_price = 0.0
    
    -- (Symbolic logic for demo)
    if position > 0 then
        if current_price > highest_price then highest_price = current_price end
        if current_price < highest_price * (1 - tsl_percent/100) then
            -- Sell via TSL
            ExecuteSell()
        end
    end
            """
        )
        return modified_code

    async def fix_errors(self, script_code: str, errors: list) -> str:
        print(f"\n[AI] Fixing errors: {errors}")
        # In this demo, we'll simulate a fix if needed
        return script_code

async def main():
    load_dotenv()
    settings = Settings()
    sm = ServerManager(settings)
    
    print("=== Real-Server Modification & Learning Test (srv02) ===")
    
    try:
        # 1. Connect and Authenticate
        await sm.connect_server('srv02')
        from pyHaasAPI.config.api_config import APIConfig
        api_config = APIConfig()
        api_config.host = "127.0.0.1"
        # Force port to 8090 for local tunnel
        api_config.port = 8090
        
        client = AsyncHaasClient(api_config)
        auth = AuthenticationManager(client, api_config)
        await auth.authenticate()
        
        # 2. Setup Services
        script_api = ScriptAPI(client, auth)
        backtest_api = BacktestAPI(client, auth)
        lab_api = LabAPI(client, auth)
        bot_api = BotAPI(client, auth)
        
        cached_analysis = CachedAnalysisService(Path("data/cache"))
        error_repo = ScriptErrorRepository(Path("data/error_learning.json"))
        ai_gen = ManualAIGenerator()
        
        automation = ScriptAutomationService(
            script_api=script_api,
            backtest_api=backtest_api,
            lab_api=lab_api,
            bot_api=bot_api,
            cached_analysis_service=cached_analysis,
            ai_generator=ai_gen,
            error_repository=error_repo
        )
        
        # 3. Find the base script
        base_name = "AI Scalper Demo Real"
        scripts = await script_api.get_scripts_by_name(base_name)
        if not scripts:
            print(f"Error: Base script '{base_name}' not found. Run test_automation_real.py first.")
            return
            
        base_script_id = scripts[0].script_id
        print(f"✓ Found base script: {base_name} ({base_script_id})")
        
        # 4. Request Modification
        modification_query = "Add a 2% Trailing Stop Loss to protect profits."
        print(f"\n[Step 1] Requesting modification: '{modification_query}'")
        
        # This will call our ManualAIGenerator.modify_script
        new_script_id = await automation.modify_existing_script(
            script_id=base_script_id,
            modification=modification_query,
            auto_debug=True # This tests the learn-from-fix cycle
        )
        
        print(f"\n✓ Modified script created/updated: {new_script_id}")
        
        # 5. Check if learning happened
        if error_repo.solutions:
            print(f"\n[Learning] Repository count: {len(error_repo.solutions)}")
            for sol in error_repo.solutions:
                print(f"  - Learned solution for error: {sol.error_message[:50]}...")
        else:
            print("\n[Learning] No new errors encountered/fixed (Script was clean).")
            
    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

