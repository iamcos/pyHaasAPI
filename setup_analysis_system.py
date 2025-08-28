#!/usr/bin/env python3
"""
Setup script for the Comprehensive Backtest Analysis System
Run this first to ensure everything is properly configured
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'numpy',
        'pandas', 
        'scipy',
        'loguru',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("✅ All packages installed!")
    
    return True

def check_pyhaas_api():
    """Check if pyHaasAPI is available"""
    print("\n🔍 Checking pyHaasAPI...")
    
    try:
        from pyHaasAPI import api
        print("✅ pyHaasAPI available")
        return True
    except ImportError:
        print("❌ pyHaasAPI not found")
        print("💡 Make sure you're in the correct directory with pyHaasAPI installed")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("\n🔍 Checking file structure...")
    
    required_files = [
        'backtest_analysis/comprehensive_backtest_analyzer.py',
        'account_management/account_manager.py',
        'ai-trading-interface/src/components/analysis/BacktestAnalysisDashboard.tsx',
        'mcp_server/tools/comprehensive_analysis_tools.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print("\n⚠️  Some files are missing. Make sure you have all the analysis system files.")
        return False
    
    return True

def setup_environment():
    """Setup environment variables"""
    print("\n🔍 Checking environment setup...")
    
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found")
        print("💡 Create a .env file with your HaasOnline API credentials")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Comprehensive Backtest Analysis System Setup")
    print("=" * 60)
    
    checks = [
        check_dependencies(),
        check_pyhaas_api(),
        check_file_structure(),
        setup_environment()
    ]
    
    if all(checks):
        print("\n" + "=" * 60)
        print("✅ Setup completed successfully!")
        print("🎯 You're ready to run the analysis system")
        print("\nNext steps:")
        print("1. Run: python run_analysis.py")
        print("2. Or use the example: python examples/comprehensive_backtest_analysis_example.py")
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ Setup incomplete")
        print("Please fix the issues above before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)