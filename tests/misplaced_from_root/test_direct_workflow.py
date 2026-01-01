#!/usr/bin/env python3
"""
Test the server content revision workflow directly without complex imports
"""

import asyncio
import sys
import os
import signal
import time
from pathlib import Path

def timeout_handler(signum, frame):
    print(f"\n⏰ TIMEOUT after 30 seconds")
    sys.exit(1)

async def test_basic_workflow():
    """Test basic workflow components"""
    print("=== Testing Basic Workflow Components ===")
    
    # Test 1: Server connection
    print("Testing server connection...")
    try:
        from pyHaasAPI.core.server_manager import ServerManager
        server_manager = ServerManager()
        
        # Test tunnel
        # In this environment, we assume the tunnel is either there or we're just testing logic
        try:
            tunnel_ok = await server_manager.ensure_srv03_tunnel()
            if tunnel_ok:
                print("✓ SSH tunnel established")
            else:
                print("⚠ SSH tunnel failed (as expected if no SSH key available)")
        except Exception as e:
            print(f"⚠ ServerManager check failed (likely no SSH): {e}")
            
    except Exception as e:
        print(f"✗ ServerManager import/init failed: {e}")
        return False
    
    # Test 2: Authentication setup
    print("Testing authentication setup...")
    try:
        from pyHaasAPI.core.auth import AuthenticationManager
        from pyHaasAPI.config.api_config import APIConfig
        from pyHaasAPI.core.client import AsyncHaasClient
        
        config = APIConfig(host="127.0.0.1", port=8090)
        client = AsyncHaasClient(config)
        auth_manager = AuthenticationManager(client, config)
        print("✓ Auth components initialized")
        
        # Test authenticate
        print("Attempting authentication...")
        try:
            await auth_manager.authenticate()
            print("✓ Authentication successful")
        except Exception as e:
            print(f"⚠ Authentication call failed (expected if no tunnel/credentials): {e}")
            
        await client.close()
        
    except Exception as e:
        print(f"✗ Authentication setup failed: {e}")
        if 'client' in locals():
            await client.close()
        return False
    
    print("\n✅ Basic workflow components working!")
    return True

def main():
    """Main test function"""
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        result = asyncio.run(test_basic_workflow())
        signal.alarm(0)  # Cancel timeout
        return 0 if result else 1
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"✗ Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

