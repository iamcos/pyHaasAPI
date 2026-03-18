"""
AI Script Generation Demonstration (Mocked API)

Demonstrates the full AI-driven script generation and auto-fix loop 
even when the Haas server is unreachable.
"""

import asyncio
import os
import json
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from pyHaasAPI.services.haasscript_knowledge_service import HaasScriptKnowledgeService
from pyHaasAPI.services.ai_script_generator import AIScriptGenerator, AIConfig
from pyHaasAPI.services.script_automation_service import ScriptAutomationService
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService


async def main():
    print("=== AI Script Generation Demonstration ===")
    
    # 1. Setup Mock API
    # We mock the API layer since srv02:8090 is unreachable
    mock_client = MagicMock()
    mock_auth = MagicMock()
    mock_auth.user_id = "test_user"
    mock_auth.interface_key = "test_key"
    
    script_api = ScriptAPI(mock_client, mock_auth)
    
    # Pre-set mock responses
    script_api.get_scripts_by_name = AsyncMock(return_value=[])
    script_api.get_haasscript_commands = AsyncMock(return_value=[])
    script_api.add_script = AsyncMock(return_value=MagicMock(script_id="gen_123", name="AI Strategy"))
    script_api.edit_script_sourcecode = AsyncMock(return_value=True)
    
    # Mock Script Record for "Get current script"
    mock_record = MagicMock()
    mock_record.script_id = "gen_123"
    mock_record.name = "AI Strategy"
    mock_record.source_code = "function Initialize()\n    Log('Broken Code')\n    GetPrice(\nend"
    script_api.get_script_record = AsyncMock(return_value=mock_record)

    # Mock Debug Test to simulate a failure then a success
    debug_responses = [
        # First call: Compilation error
        {'success': False, 'error': "Compilation error: unexpected symbol near 'end' at line 4", 'logs': []},
        # Second call: Success
        {'success': True, 'logs': [{'level': 'info', 'message': 'Script compiled and running'}]}
    ]
    script_api.execute_debug_test = AsyncMock(side_effect=debug_responses)
    
    # 2. Setup AI Services
    knowledge_service = HaasScriptKnowledgeService(script_api)
    
    # Seed knowledge service with manual examples for the demo
    knowledge_service.add_example(
        "Simple SMA", 
        "function Initialize()\n    Log('SMA Init')\nend\n\nfunction OnTick()\n    local sma = SMA(settings.market, 20)\nend",
        "Basic SMA implementation"
    )
    
    ai_config = AIConfig.from_env()
    if not ai_config.api_key:
        print("ERROR: GEMINI_API_KEY not found in .env. Cannot run AI demo.")
        return

    generator = AIScriptGenerator(knowledge_service, ai_config)
    
    # 3. Setup Automation Service
    automation = ScriptAutomationService(
        script_api=script_api,
        backtest_api=MagicMock(),
        lab_api=MagicMock(),
        bot_api=MagicMock(),
        cached_analysis_service=CachedAnalysisService(cache_dir=Path("data")),
        ai_generator=generator,
        knowledge_service=knowledge_service
    )
    
    # 4. RUN DEMO: Generate from Idea
    print("\n[Step 1] Generating script from idea...")
    idea = "A simple scalping strategy that buys when price drops 1% and sells when it gains 1.5%. Use RSI for confirmation."
    
    # We call the service method
    try:
        script_id = await automation.generate_script_from_idea(
            idea=idea,
            name="AI Scalper Demo",
            auto_debug=False # We'll run debug manually to show the loop
        )
        print(f"✓ Created Script ID: {script_id}")
    except Exception as e:
        print(f"FAILED: {e}")
        return

    # 5. RUN DEMO: Auto-Debug and Fix
    print("\n[Step 2] running Auto-Debug and Fix loop...")
    # Note: We mocked execute_debug_test to fail on first attempt and succeed on second
    
    # We need to update the mock_record's source code before the loop to simulate the "broken" generator output
    mock_record.source_code = "function Initialize()\n    GetPrice(\nend" # Intentional error
    
    result = await automation.auto_debug_and_fix(script_id, max_iterations=3)
    
    print(f"✓ Debug Result: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"✓ Iterations taken: {result['iterations']}")
    
    if result['fix_history']:
        print("\nFix History:")
        for fix in result['fix_history']:
            print(f"- Iteration {fix['iteration']}:")
            print(f"  Errors found: {fix['errors']}")
            print(f"  AI Fix applied: {fix['fixed']}")

    # 6. RUN DEMO: Script Explanation
    print("\n[Step 3] Explaining the final script...")
    explanation = await generator.explain_script(mock_record.source_code)
    print("\nAI Explanation:")
    print(explanation)

    print("\n=== Demo Completed Successfully ===")

if __name__ == "__main__":
    asyncio.run(main())
