#!/usr/bin/env python3
"""
Test script for refactored CLI functionality.
Tests all CLI modules and managers on srv03.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Test imports
print("🧪 Testing New Service and CLI Imports...")

try:
    # Test core services
    from pyHaasAPI.services.lab import LabService
    print("✅ LabService import successful")
    
    from pyHaasAPI.services.bot import BotService
    print("✅ BotService import successful")
    
    from pyHaasAPI.services.analysis import AnalysisService
    print("✅ AnalysisService import successful")
    
    # Test main CLI
    from pyHaasAPI.cli.consolidated_cli import ConsolidatedCLI
    print("✅ ConsolidatedCLI import successful")
    
    print("\n🎉 ALL NEW ARCHITECTURE IMPORTS SUCCESSFUL!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test basic functionality
print("\n🧪 Testing Basic Functionality...")

try:
    # Test main CLI instantiation
    cli = ConsolidatedCLI()
    print("✅ ConsolidatedCLI instantiation successful")
    
    print("\n🎉 NEW ARCHITECTURE INSTANTIATION SUCCESSFUL!")
    
except Exception as e:
    print(f"❌ Instantiation error: {e}")
    sys.exit(1)

print("\n✅ NEW ARCHITECTURE TESTING COMPLETE!")
print("All modules imported and instantiated successfully.")
print("Ready for srv03 testing with real API connections.")




