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
        tunnel_ok = await server_manager.ensure_srv03_tunnel()
        if tunnel_ok:
            print("✓ SSH tunnel established")
        else:
            print("✗ SSH tunnel failed")
            return False
            
        # Test preflight
        preflight_ok = await server_manager.preflight_check()
        if preflight_ok:
            print("✓ Preflight check passed")
        else:
            print("✗ Preflight check failed")
            return False
            
    except Exception as e:
        print(f"✗ Server connection failed: {e}")
        return False
    
    # Test 2: Authentication
    print("Testing authentication...")
    try:
        from pyHaasAPI.core.auth import AuthenticationManager
        from pyHaasAPI.config.api_config import APIConfig
        
        config = APIConfig()
        auth_manager = AuthenticationManager(config)
        
        # Test login
        login_success = await auth_manager.login()
        if login_success:
            print("✓ Authentication successful")
        else:
            print("✗ Authentication failed")
            return False
            
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False
    
    # Test 3: Basic API calls
    print("Testing basic API calls...")
    try:
        from pyHaasAPI.core.client import AsyncHaasClient
        
        client = AsyncHaasClient(
            host="127.0.0.1",
            port=8090,
            auth_manager=auth_manager
        )
        
        # Test simple API call
        response = await client.get_json("/LabsAPI.php", {
            "channel": "GET_LABS",
            "interfacekey": auth_manager.interface_key,
            "userid": auth_manager.user_id
        })
        
        if response and "Success" in response:
            print("✓ Basic API call successful")
        else:
            print("✗ Basic API call failed")
            return False
            
    except Exception as e:
        print(f"✗ API call failed: {e}")
        return False
    
    print("\n✅ All basic workflow components working!")
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

