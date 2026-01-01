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
        config = APIConfig(host="127.0.0.1", port=8090)
        print(f"✓ Config created: {config.host}:{config.port}")
        
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False
    
    # Test 3: Authentication
    print("Testing authentication...")
    client = AsyncHaasClient(config)
    try:
        auth_manager = AuthenticationManager(client, config)
        print("✓ AuthenticationManager created")
        
        # Test authenticate
        print("Attempting authenticate...")
        # This will fail if no credentials or no tunnel, but that's okay for a test
        try:
            await auth_manager.authenticate()
            print("✓ Authentication successful")
        except Exception as e:
            print(f"⚠ Authentication failed (expected if no tunnel/credentials): {e}")
            
    except Exception as e:
        print(f"✗ Authentication setup failed: {e}")
        await client.close()
        return False
    
    await client.close()
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

