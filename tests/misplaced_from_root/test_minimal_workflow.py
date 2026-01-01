#!/usr/bin/env python3
"""
Test minimal workflow without complex imports
"""

import asyncio
import sys
import os
import signal
import time

def timeout_handler(signum, frame):
    print(f"\n⏰ TIMEOUT after 15 seconds")
    sys.exit(1)

async def test_minimal_workflow():
    """Test minimal workflow components"""
    print("=== Testing Minimal Workflow ===")
    
    # Test 1: Basic imports
    print("Testing basic imports...")
    try:
        from pyHaasAPI.core.auth import AuthenticationManager
        print("✓ AuthenticationManager imported")
        
        from pyHaasAPI.core.client import AsyncHaasClient
        print("✓ AsyncHaasClient imported")
        
        from pyHaasAPI.config.api_config import APIConfig
        print("✓ APIConfig imported")
        
    except Exception as e:
        print(f"✗ Basic imports failed: {e}")
        return False
    
    # Test 2: Configuration
    print("Testing configuration...")
    try:
        config = APIConfig()
        print(f"✓ Config created: {config.host}:{config.port}")
        
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False
    
    # Test 3: Authentication
    print("Testing authentication...")
    try:
        auth_manager = AuthenticationManager(config)
        print("✓ AuthenticationManager created")
        
        # Test login (this might fail if no tunnel, but should not hang)
        print("Attempting login...")
        login_success = await auth_manager.login()
        if login_success:
            print("✓ Login successful")
        else:
            print("⚠ Login failed (expected if no tunnel)")
            
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False
    
    print("\n✅ Minimal workflow components working!")
    return True

def main():
    """Main test function"""
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        result = asyncio.run(test_minimal_workflow())
        signal.alarm(0)  # Cancel timeout
        return 0 if result else 1
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"✗ Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

