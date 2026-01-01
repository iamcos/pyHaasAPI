#!/usr/bin/env python3
"""
Debug pyHaasAPI imports to find what's causing hanging
"""

import sys
import os
import signal
import time

def timeout_handler(signum, frame):
    print(f"\n⏰ TIMEOUT after 10 seconds at: {frame.f_code.co_filename}:{frame.f_lineno}")
    sys.exit(1)

def test_import_with_timeout(module_name, timeout=10):
    """Test importing a module with timeout"""
    print(f"Testing import: {module_name}")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        start_time = time.time()
        exec(f"import {module_name}")
        end_time = time.time()
        signal.alarm(0)  # Cancel timeout
        print(f"✓ {module_name} imported successfully in {end_time - start_time:.2f}s")
        return True
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"✗ {module_name} failed: {e}")
        return False

def main():
    """Test imports systematically"""
    print("=== Debugging pyHaasAPI Imports ===")
    
    # Test basic pyHaasAPI import
    if not test_import_with_timeout("pyHaasAPI"):
        return 1
    
    # Test core modules
    core_modules = [
        "pyHaasAPI.core.server_manager",
        "pyHaasAPI.core.auth", 
        "pyHaasAPI.core.client",
        "pyHaasAPI.core.field_utils"
    ]
    
    for module in core_modules:
        if not test_import_with_timeout(module):
            print(f"❌ Failed at core module: {module}")
            return 1
    
    # Test API modules
    api_modules = [
        "pyHaasAPI.api.account.account_api",
        "pyHaasAPI.api.bot.bot_api",
        "pyHaasAPI.api.lab.lab_api"
    ]
    
    for module in api_modules:
        if not test_import_with_timeout(module):
            print(f"❌ Failed at API module: {module}")
            return 1
    
    # Test services
    service_modules = [
        "pyHaasAPI.services.analysis_manager",
        "pyHaasAPI.services.bot_naming_service",
        "pyHaasAPI.services.account_manager"
    ]
    
    for module in service_modules:
        if not test_import_with_timeout(module):
            print(f"❌ Failed at service module: {module}")
            return 1
    
    print("\n✅ All imports successful!")
    return 0

if __name__ == "__main__":
    exit(main())

