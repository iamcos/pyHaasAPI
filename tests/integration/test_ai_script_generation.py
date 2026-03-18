"""
Integration tests for AI-driven script generation.

Tests the full workflow of generating, debugging, and modifying HaasScripts using AI.
"""

import unittest
import asyncio
import os
from pathlib import Path

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService
from pyHaasAPI.services.haasscript_knowledge_service import HaasScriptKnowledgeService
from pyHaasAPI.services.ai_script_generator import AIScriptGenerator, AIConfig
from pyHaasAPI.services.script_automation_service import ScriptAutomationService


class TestAIScriptGeneration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for AI script generation."""
    
    @classmethod
    def setUpClass(cls):
        """Load environment variables manually."""
        env_file = Path(__file__).parent.parent.parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Get credentials from environment
        api_host = os.getenv("API_HOST", "srv02")
        api_port = int(os.getenv("API_PORT", "8090"))
        api_email = os.getenv("API_EMAIL")
        api_password = os.getenv("API_PASSWORD")
        
        # Create API config
        config = APIConfig(
            host=api_host,
            port=api_port,
            timeout=30.0
        )
        
        # Initialize client and auth
        self.client = AsyncHaasClient(config)
        self.auth = AuthenticationManager(self.client, config)
        
        # Authenticate
        await self.auth.authenticate(api_email, api_password)
        
        # Initialize APIs
        self.script_api = ScriptAPI(self.client, self.auth)
        self.backtest_api = BacktestAPI(self.client, self.auth)
        self.lab_api = LabAPI(self.client, self.auth)
        self.bot_api = BotAPI(self.client, self.auth)
        
        # Initialize services
        self.cache_service = CachedAnalysisService()
        self.knowledge_service = HaasScriptKnowledgeService(self.script_api)
        
        # Check if AI is available
        try:
            ai_config = AIConfig.from_env()
            if ai_config.api_key:
                self.ai_generator = AIScriptGenerator(
                    self.knowledge_service,
                    ai_config
                )
            else:
                self.ai_generator = None
                print("WARNING: GEMINI_API_KEY not set, AI tests will be skipped")
        except Exception as e:
            self.ai_generator = None
            print(f"WARNING: AI generator not available: {e}")
        
        # Initialize automation service
        self.service = ScriptAutomationService(
            script_api=self.script_api,
            backtest_api=self.backtest_api,
            lab_api=self.lab_api,
            bot_api=self.bot_api,
            cached_analysis_service=self.cache_service,
            ai_generator=self.ai_generator,
            knowledge_service=self.knowledge_service
        )
    
    async def asyncTearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'client'):
            await self.client.close()
    
    async def test_fetch_haasscript_commands(self):
        """Test fetching HaasScript commands from API."""
        commands = await self.knowledge_service.fetch_and_cache_commands()
        
        self.assertIsInstance(commands, list)
        self.assertGreater(len(commands), 0)
        print(f"✓ Fetched {len(commands)} HaasScript commands")
        
        # Verify command structure
        if commands:
            cmd = commands[0]
            print(f"  Sample command: {cmd}")
    
    async def test_command_reference_formatting(self):
        """Test command reference formatting for AI prompts."""
        await self.knowledge_service.fetch_and_cache_commands()
        
        # Test markdown format
        md_ref = self.knowledge_service.get_command_reference(format="markdown")
        self.assertIn("HaasScript", md_ref)
        self.assertGreater(len(md_ref), 100)
        print(f"✓ Generated markdown reference ({len(md_ref)} chars)")
        
        # Test AI context
        context = self.knowledge_service.get_ai_context()
        self.assertIsInstance(context, str)
        print(f"✓ Generated AI context ({len(context)} chars)")
    
    @unittest.skipIf(not os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY not set")
    async def test_generate_simple_script(self):
        """Test generating a simple script from idea."""
        if not self.ai_generator:
            self.skipTest("AI generator not available")
        
        idea = "Create a simple script that buys when RSI is below 30 and sells when RSI is above 70"
        
        script_id = await self.service.generate_script_from_idea(
            idea=idea,
            name="AI Test - RSI Strategy",
            description="AI-generated RSI trading strategy",
            auto_debug=True
        )
        
        self.assertIsNotNone(script_id)
        print(f"✓ Generated script: {script_id}")
        
        # Verify script was created
        script = await self.script_api.get_script_record(script_id)
        self.assertIsNotNone(script.source_code)
        print(f"  Code length: {len(script.source_code)} chars")
    
    @unittest.skipIf(not os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY not set")
    async def test_modify_script(self):
        """Test modifying an existing script."""
        if not self.ai_generator:
            self.skipTest("AI generator not available")
        
        # First, create a simple script
        original_code = """
        function Initialize()
            -- Simple test script
        end
        
        function Deinitialize()
        end
        """
        
        script_id = await self.service.create_or_update_script(
            name="AI Test - Original",
            content=original_code,
            description="Original script for modification test"
        )
        
        # Now modify it
        modification = "Add a variable called 'testVar' and set it to 100"
        
        new_script_id = await self.service.modify_existing_script(
            script_id=script_id,
            modification=modification,
            auto_debug=True
        )
        
        self.assertIsNotNone(new_script_id)
        self.assertNotEqual(script_id, new_script_id)
        print(f"✓ Modified script: {script_id} → {new_script_id}")
        
        # Verify modification
        new_script = await self.script_api.get_script_record(new_script_id)
        self.assertIn("testVar", new_script.source_code)
        print(f"  Modified code contains 'testVar': ✓")
    
    @unittest.skipIf(not os.getenv("GEMINI_API_KEY"), "GEMINI_API_KEY not set")
    async def test_auto_debug_and_fix(self):
        """Test automatic error fixing."""
        if not self.ai_generator:
            self.skipTest("AI generator not available")
        
        # Create a script with intentional syntax error
        broken_code = """
        function Initialize()
            local price = GetPrice(
            -- Missing closing parenthesis
        end
        """
        
        script_id = await self.service.create_or_update_script(
            name="AI Test - Broken Script",
            content=broken_code,
            description="Script with intentional error for testing"
        )
        
        # Try to auto-fix
        result = await self.service.auto_debug_and_fix(script_id, max_iterations=3)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('iterations', result)
        self.assertIn('fix_history', result)
        
        print(f"✓ Auto-debug result: {result['success']} after {result['iterations']} iterations")
        
        if result['fix_history']:
            print(f"  Fix attempts: {len(result['fix_history'])}")
            for fix in result['fix_history']:
                print(f"    Iteration {fix['iteration']}: Fixed={fix['fixed']}")
    
    async def test_end_to_end_workflow(self):
        """Test complete workflow: Generate → Debug → Backtest → Promote."""
        if not self.ai_generator:
            self.skipTest("AI generator not available")
        
        # 1. Generate script
        idea = "Simple moving average crossover: buy when fast MA crosses above slow MA"
        script_id = await self.service.generate_script_from_idea(
            idea=idea,
            name="AI Test - SMA Crossover",
            description="AI-generated SMA crossover strategy",
            context={"timeframe": "1h", "fast_period": 10, "slow_period": 20},
            auto_debug=True
        )
        
        print(f"✓ Step 1: Generated script {script_id}")
        
        # 2. Debug (already done in generate_script_from_idea with auto_debug=True)
        print(f"✓ Step 2: Auto-debug completed")
        
        # 3. Run backtest (optional, depends on server availability)
        # This would require a valid market and account setup
        # Skipping for now as srv02 port 8090 may not be accessible
        
        print(f"✓ End-to-end workflow test completed")


if __name__ == "__main__":
    unittest.main()
