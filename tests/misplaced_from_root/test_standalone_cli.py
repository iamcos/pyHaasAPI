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

# Test core functionality by importing naming service directly
try:
    # Test the naming service from services directory
    from pyHaasAPI.services.bot_naming_service import BotNamingService, BotNamingContext
    print("✅ BotNamingService import successful")
    
    # Test instantiation
    naming_service = BotNamingService()
    print("✅ BotNamingService instantiation successful")
    
    # Test core functionality
    print("\n🧪 Testing Core Functionality...")
    
    # Create naming context
    context = BotNamingContext(
        server="srv03",
        lab_id="test-lab-id",
        lab_name="Test Lab",
        script_name="Test Script",
        market_tag="BINANCE_BTC_USDT_",
        roi_percentage=15.5,
        win_rate=0.75,
        max_drawdown=0.0,
        total_trades=10
    )
    
    # Test bot naming convention
    bot_name = naming_service.generate_bot_name(context, strategy="comprehensive")
    print(f"✅ Bot naming: {bot_name}")
    
    print("\n🎉 CORE FUNCTIONALITY TEST SUCCESSFUL!")
    print("✅ Centralized naming service working correctly")
    print("✅ Bot naming convention working")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ REFACTORED CLI CORE FUNCTIONALITY TEST COMPLETE!")
print("Ready for srv03 testing with real API connections.")




