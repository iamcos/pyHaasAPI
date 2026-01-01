#!/usr/bin/env python3
"""
Minimal test script for the project manager CLI
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

async def test_basic_imports():
    """Test basic imports without initialization"""
    print("Testing basic imports...")
    
    try:
        from pyHaasAPI.core.logging import get_logger
        print("✓ Logging imported")
        
        from pyHaasAPI.config.api_config import APIConfig
        print("✓ APIConfig imported")
        
        from pyHaasAPI.core.client import AsyncHaasClient
        print("✓ AsyncHaasClient imported")
        
        from pyHaasAPI.core.auth import AuthenticationManager
        print("✓ AuthenticationManager imported")
        
        from pyHaasAPI.core.server_manager import ServerManager
        print("✓ ServerManager imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

async def test_settings():
    """Test Settings class"""
    print("\nTesting Settings...")
    
    try:
        from pyHaasAPI.config.settings import Settings
        print("✓ Settings imported")
        
        # Try to create Settings instance
        settings = Settings()
        print(f"✓ Settings created, default_server: {settings.default_server}")
        
        return True
        
    except Exception as e:
        print(f"✗ Settings failed: {e}")
        return False

async def test_cli_creation():
    """Test CLI creation"""
    print("\nTesting CLI creation...")
    
    try:
        from pyHaasAPI.cli.consolidated_cli import ConsolidatedCLI
        print("✓ ConsolidatedCLI imported")
        
        # Try to create CLI instance
        cli = ConsolidatedCLI()
        print("✓ ConsolidatedCLI created")
        
        return True
        
    except Exception as e:
        print(f"✗ CLI creation failed: {e}")
        return False

async def main():
    """Main test function"""
    print("=== Consolidated CLI Test ===")
    
    # Test 1: Basic imports
    if not await test_basic_imports():
        print("\n❌ Basic imports failed")
        return 1
    
    # Test 2: Settings
    if not await test_settings():
        print("\n❌ Settings failed")
        return 1
    
    # Test 3: CLI creation
    if not await test_cli_creation():
        print("\n❌ CLI creation failed")
        return 1
    
    print("\n✅ All tests passed!")
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))


