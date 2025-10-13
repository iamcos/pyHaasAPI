#!/usr/bin/env python3
"""
Standalone test script for refactored CLI functionality.
Tests all CLI modules and managers without going through main pyHaasAPI module.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("🧪 Testing Refactored CLI Standalone...")

# Test individual module imports
try:
    # Test core managers
    sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI" / "cli_ref"))
    
    from analysis_manager import AnalysisManager
    print("✅ AnalysisManager import successful")
    
    from bot_manager import BotManager
    print("✅ BotManager import successful")
    
    from report_manager import ReportManager
    print("✅ ReportManager import successful")
    
    # Test core CLI modules
    from account_cli import AccountCLI
    print("✅ AccountCLI import successful")
    
    from backtest_cli import BacktestCLI
    print("✅ BacktestCLI import successful")
    
    from market_cli import MarketCLI
    print("✅ MarketCLI import successful")
    
    from order_cli import OrderCLI
    print("✅ OrderCLI import successful")
    
    from script_cli import ScriptCLI
    print("✅ ScriptCLI import successful")
    
    # Test advanced workflow modules
    from orchestrator_cli import OrchestratorCLI
    print("✅ OrchestratorCLI import successful")
    
    from backtest_workflow_cli import BacktestWorkflowCLI
    print("✅ BacktestWorkflowCLI import successful")
    
    from cache_analysis_cli import CacheAnalysisCLI
    print("✅ CacheAnalysisCLI import successful")
    
    from data_manager_cli import DataManagerCLI
    print("✅ DataManagerCLI import successful")
    
    print("\n🎉 ALL REFACTORED CLI IMPORTS SUCCESSFUL!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test basic functionality
print("\n🧪 Testing Basic Functionality...")

try:
    # Test managers
    analysis_manager = AnalysisManager(None, None)
    print("✅ AnalysisManager instantiation successful")
    
    bot_manager = BotManager(None)
    print("✅ BotManager instantiation successful")
    
    report_manager = ReportManager()
    print("✅ ReportManager instantiation successful")
    
    # Test CLI modules
    account_cli = AccountCLI()
    print("✅ AccountCLI instantiation successful")
    
    backtest_cli = BacktestCLI()
    print("✅ BacktestCLI instantiation successful")
    
    market_cli = MarketCLI()
    print("✅ MarketCLI instantiation successful")
    
    order_cli = OrderCLI()
    print("✅ OrderCLI instantiation successful")
    
    script_cli = ScriptCLI()
    print("✅ ScriptCLI instantiation successful")
    
    # Test advanced workflow modules
    orchestrator_cli = OrchestratorCLI()
    print("✅ OrchestratorCLI instantiation successful")
    
    backtest_workflow_cli = BacktestWorkflowCLI()
    print("✅ BacktestWorkflowCLI instantiation successful")
    
    cache_analysis_cli = CacheAnalysisCLI()
    print("✅ CacheAnalysisCLI instantiation successful")
    
    data_manager_cli = DataManagerCLI()
    print("✅ DataManagerCLI instantiation successful")
    
    print("\n🎉 ALL REFACTORED CLI INSTANTIATION SUCCESSFUL!")
    
except Exception as e:
    print(f"❌ Instantiation error: {e}")
    sys.exit(1)

print("\n✅ REFACTORED CLI STANDALONE TESTING COMPLETE!")
print("All modules imported and instantiated successfully.")
print("Ready for srv03 testing with real API connections.")




