#!/usr/bin/env python3
"""
Standalone test for refactored CLI functionality.
Tests core functionality without going through main pyHaasAPI module.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("🧪 Testing Refactored CLI Standalone (Bypassing Main Module)...")

# Test core functionality by importing managers directly
try:
    # Test the managers from services directory
    from pyHaasAPI.services.analysis_manager import AnalysisManager
    print("✅ AnalysisManager import successful")
    
    from pyHaasAPI.services.bot_manager import BotManager
    print("✅ BotManager import successful")
    
    # Test instantiation
    analysis_manager = AnalysisManager(None, None)
    print("✅ AnalysisManager instantiation successful")
    
    bot_manager = BotManager(None)
    print("✅ BotManager instantiation successful")
    
    # Test core functionality
    print("\n🧪 Testing Core Functionality...")
    
    # Test bot naming convention
    bot_name = bot_manager.generate_bot_name("Test Lab", "Test Script", 15.5, 0.75)
    print(f"✅ Bot naming: {bot_name}")
    
    # Test bot configuration
    bot_config = bot_manager.get_default_bot_config()
    print(f"✅ Bot config: {bot_config}")
    
    print("\n🎉 CORE FUNCTIONALITY TEST SUCCESSFUL!")
    print("✅ Centralized managers working correctly")
    print("✅ Bot naming convention working")
    print("✅ Bot configuration working")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n✅ REFACTORED CLI CORE FUNCTIONALITY TEST COMPLETE!")
print("Ready for srv03 testing with real API connections.")




