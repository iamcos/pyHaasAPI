"""
Error Learning Demonstration (Manual AI Mode)
Target: srv02 (Real Server)

This demo showcases the system learning from a script error.
"""

import asyncio
from pathlib import Path
from pyHaasAPI.core.server_manager import ServerManager
from pyHaasAPI.config.settings import Settings
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.services.script_automation_service import ScriptAutomationService
from pyHaasAPI.services.script_error_repository import ScriptErrorRepository
from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService
from pyHaasAPI.config.api_config import APIConfig

class LearningAIGenerator:
    def __init__(self):
        self.learned = False

    async def fix_errors(self, script_code: str, errors: list) -> str:
        print(f"\n[AI] Fixing known error: {errors}")
        # The error will be 'Unknown reference: NonExistentCommand'
        # Fix: Replace it with a valid 'Log' command
        fixed_code = script_code.replace("NonExistentCommand()", "Log('Fixed by AI')")
        self.learned = True
        return fixed_code

from dotenv import load_dotenv

async def main():
    load_dotenv()
    settings = Settings()
    sm = ServerManager(settings)
    
    try:
        await sm.connect_server('srv02')
        api_config = APIConfig()
        api_config.host = "127.0.0.1"
        api_config.port = 8090
        
        client = AsyncHaasClient(api_config)
        auth = AuthenticationManager(client, api_config)
        await auth.authenticate()
        
        repo_path = Path("data/error_learning.json")
        if repo_path.exists(): repo_path.unlink() # Start fresh
        
        error_repo = ScriptErrorRepository(repo_path)
        ai_gen = LearningAIGenerator()
        
        automation = ScriptAutomationService(
            script_api=ScriptAPI(client, auth),
            backtest_api=None, lab_api=None, bot_api=None,
            cached_analysis_service=CachedAnalysisService(Path("data/cache")),
            ai_generator=ai_gen,
            error_repository=error_repo
        )
        
        # 1. Create script with error
        script_name = "AI Error Learning Test"
        bad_code = "NonExistentCommand()" # This will trigger 'Unknown references' on srv02
        
        print(f"\n[Step 1] Creating script with deliberate error: {script_name}")
        script_id = await automation.create_or_update_script(script_name, bad_code, script_type=1)
        
        # 2. Run Auto-Debug (this should trigger learning)
        print("\n[Step 2] Running auto-debug-and-fix loop...")
        settings = {"market": "BINANCE_BTC_USDT_"}
        result = await automation.auto_debug_and_fix(script_id, settings=settings)
        
        print(f"Loop result: Success={result['success']}, Iterations={result['iterations']}")
        
        # 3. Verify Repository
        error_repo._load() # Reload to be sure
        if error_repo.solutions:
            print(f"\n✓ SUCCESS: System learned {len(error_repo.solutions)} solution(s)!")
            for sol in error_repo.solutions:
                print(f"  Error Message: {sol.error_message.strip()[:60]}...")
                print(f"  Applied Fix: {sol.fixed_code}")
        else:
            print("\n❌ FAILURE: System did not learn from the fix.")

    finally:
        await client.close()
        await sm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

