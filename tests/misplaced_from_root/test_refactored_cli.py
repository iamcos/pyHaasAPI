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
print("🧪 Testing Refactored CLI Imports...")

try:
    # Test core managers
    from pyHaasAPI.cli_ref.analysis_manager import AnalysisManager
    print("✅ AnalysisManager import successful")
    
    from pyHaasAPI.cli_ref.bot_manager import BotManager
    print("✅ BotManager import successful")
    
    from pyHaasAPI.cli_ref.report_manager import ReportManager
    print("✅ ReportManager import successful")
    
    # Test core CLI modules
    from pyHaasAPI.cli_ref.account_cli import AccountCLI
    print("✅ AccountCLI import successful")
    
    from pyHaasAPI.cli_ref.backtest_cli import BacktestCLI
    print("✅ BacktestCLI import successful")
    
    from pyHaasAPI.cli_ref.market_cli import MarketCLI
    print("✅ MarketCLI import successful")
    
    from pyHaasAPI.cli_ref.order_cli import OrderCLI
    print("✅ OrderCLI import successful")
    
    from pyHaasAPI.cli_ref.script_cli import ScriptCLI
    print("✅ ScriptCLI import successful")
    
    # Test advanced workflow modules
    from pyHaasAPI.cli_ref.orchestrator_cli import OrchestratorCLI
    print("✅ OrchestratorCLI import successful")
    
    from pyHaasAPI.cli_ref.backtest_workflow_cli import BacktestWorkflowCLI
    print("✅ BacktestWorkflowCLI import successful")
    
    from pyHaasAPI.cli_ref.cache_analysis_cli import CacheAnalysisCLI
    print("✅ CacheAnalysisCLI import successful")
    
    from pyHaasAPI.cli_ref.data_manager_cli import DataManagerCLI
    print("✅ DataManagerCLI import successful")
    
    # Test main CLI
    from pyHaasAPI.cli_ref.main import RefactoredCLI
    print("✅ RefactoredCLI import successful")
    
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
    
    # Test main CLI
    refactored_cli = RefactoredCLI()
    print("✅ RefactoredCLI instantiation successful")
    
    print("\n🎉 ALL REFACTORED CLI INSTANTIATION SUCCESSFUL!")
    
except Exception as e:
    print(f"❌ Instantiation error: {e}")
    sys.exit(1)

print("\n✅ REFACTORED CLI TESTING COMPLETE!")
print("All modules imported and instantiated successfully.")
print("Ready for srv03 testing with real API connections.")




