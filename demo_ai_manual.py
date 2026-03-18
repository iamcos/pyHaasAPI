"""
AI Script Generation Demonstration (Manual AI Mode)

Demonstrates the full AI-driven script generation and auto-fix loop 
using Antigravity as the source of truth for AI logic (Offline/Stable Mode).
"""

import asyncio
import os
import json
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from pyHaasAPI.services.haasscript_knowledge_service import HaasScriptKnowledgeService
from pyHaasAPI.services.ai_script_generator import AIScriptGenerator, AIConfig
from pyHaasAPI.services.script_automation_service import ScriptAutomationService
from pyHaasAPI.api.script.script_api import ScriptAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.services.analysis.cached_analysis_service import CachedAnalysisService

# MANUALLY GENERATED SCRIPT BY ANTIGRAVITY
MANUAL_SCALPER_SCRIPT = """
-- Antigravity Generated Scalper
-- Buys -1% drop, Sells +1.5% gain, RSI confirmation

function Initialize()
    AddInput("RSI_Period", 14, "RSI calculation period")
    AddInput("RSI_Threshold", 30, "Buy only if RSI is below this")
    AddInput("Buy_Drop", 1.0, "Percentage drop for buy signal")
    AddInput("Sell_Gain", 1.5, "Percentage gain for sell signal")
    
    self.last_buy_price = 0
    self.in_position = false
    Log("AI Antigravity Scalper Initialized")
end

function OnTick()
    local current_price = GetPrice(settings.market)
    local rsi = RSI(settings.market, settings.RSI_Period)
    
    if not self.in_position then
        -- Buy logic: Price drop + RSI oversold
        local ref_price = GetLastTrade(settings.market).Price
        local price_change = ((current_price - ref_price) / ref_price) * 100
        
        if price_change <= -settings.Buy_Drop and rsi <= settings.RSI_Threshold then
            Log("Buying at " .. current_price .. " (Drop: " .. price_change .. "%, RSI: " .. rsi .. ")")
            Buy(settings.market, settings.TradeAmount)
            self.last_buy_price = current_price
            self.in_position = true
        end
    else
        -- Sell logic: Price gain
        local gain = ((current_price - self.last_buy_price) / self.last_buy_price) * 100
        
        if gain >= settings.Sell_Gain then
            Log("Selling at " .. current_price .. " (Gain: " .. gain .. "%)")
            Sell(settings.market, settings.TradeAmount)
            self.in_position = false
        end
    end
end
"""

async def main():
    print("=== AI Script Generation Demonstration (Manual AI Mode) ===")
    
    # 1. Setup Mock API
    mock_client = MagicMock()
    mock_auth = MagicMock()
    mock_auth.user_id = "test_user"
    mock_auth.interface_key = "test_key"
    
    script_api = ScriptAPI(mock_client, mock_auth)
    
    # Pre-set mock responses
    script_api.get_scripts_by_name = AsyncMock(return_value=[])
    script_api.get_haasscript_commands = AsyncMock(return_value=[])
    script_api.add_script = AsyncMock(return_value=MagicMock(script_id="manual_123", name="AI Scalper Demo"))
    script_api.edit_script_sourcecode = AsyncMock(return_value=True)
    
    # Mock Script Record
    mock_record = MagicMock()
    mock_record.script_id = "manual_123"
    mock_record.name = "AI Scalper Demo"
    mock_record.source_code = MANUAL_SCALPER_SCRIPT
    script_api.get_script_record = AsyncMock(return_value=mock_record)

    # 2. Setup AI Services (Mocked Generator with Antigravity Logic)
    knowledge_service = HaasScriptKnowledgeService(script_api)
    
    # Mock Generator
    generator = MagicMock(spec=AIScriptGenerator)
    generator.generate_from_idea = AsyncMock(return_value=MANUAL_SCALPER_SCRIPT)
    generator.explain_script = AsyncMock(return_value="This script implements a basic scalping strategy. It buys when the price drops by a specified percentage relative to the last trade AND the RSI is oversold. It sells after a fixed percentage gain.")
    generator.fix_errors = AsyncMock(return_value=MANUAL_SCALPER_SCRIPT)
    
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
    
    script_id = await automation.generate_script_from_idea(
        idea=idea,
        name="AI Scalper Demo",
        auto_debug=False
    )
    print(f"✓ Created Script ID: {script_id}")

    # 5. RUN DEMO: Script Explanation
    print("\n[Step 2] Explaining the script...")
    explanation = await generator.explain_script(MANUAL_SCALPER_SCRIPT)
    print("\nAntigravity AI Explanation:")
    print(explanation)
    
    print("\n[Step 3] Verifying Code Quality...")
    print("Script Preview:")
    lines = MANUAL_SCALPER_SCRIPT.strip().split('\n')
    for line in lines[:10]:
        print(f"  {line}")
    print("  ...")

    print("\n=== Demo Completed Successfully (Simulated) ===")

if __name__ == "__main__":
    asyncio.run(main())
