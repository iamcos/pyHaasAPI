#!/usr/bin/env python3
"""
Debug Tuple Structure

This script examines the actual tuple structure of backtest objects to understand
what data is available and how to access it properly.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


async def establish_ssh_tunnel(server_name="srv01"):
    """Establish SSH tunnel to server"""
    try:
        print(f"Connecting to {server_name}...")
        
        # SSH command for tunnel
        ssh_cmd = [
            "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
            f"prod@{server_name}"
        ]
        
        # Start SSH process
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        # Wait a moment for tunnel to establish
        await asyncio.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"SSH tunnel established (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"SSH tunnel failed: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"Failed to establish SSH tunnel: {e}")
        return None


async def cleanup_ssh_tunnel(process):
    """Clean up SSH tunnel"""
    try:
        if process and process.poll() is None:
            print("Cleaning up SSH tunnel...")
            process.terminate()
            process.wait(timeout=5)
            print("SSH tunnel cleaned up")
    except Exception as e:
        print(f"Error cleaning up SSH tunnel: {e}")


def debug_tuple_structure(backtest_tuple, index=0):
    """Debug a tuple backtest to understand its structure"""
    print(f"\nDebugging Backtest Tuple {index}:")
    print(f"  Type: {type(backtest_tuple)}")
    print(f"  Length: {len(backtest_tuple)}")
    
    # Print all elements
    for i, element in enumerate(backtest_tuple):
        print(f"  [{i}]: {element} (type: {type(element)})")
    
    # Try to access by index
    print(f"\n  Accessing by index:")
    try:
        print(f"    [0]: {backtest_tuple[0]}")
        print(f"    [1]: {backtest_tuple[1]}")
        print(f"    [2]: {backtest_tuple[2]}")
        if len(backtest_tuple) > 3:
            print(f"    [3]: {backtest_tuple[3]}")
        if len(backtest_tuple) > 4:
            print(f"    [4]: {backtest_tuple[4]}")
    except Exception as e:
        print(f"    Error accessing by index: {e}")
    
    # Try to convert to dict if it has model_dump
    try:
        if hasattr(backtest_tuple, 'model_dump'):
            data = backtest_tuple.model_dump()
            print(f"\n  Model Dump: {data}")
    except Exception as e:
        print(f"  Model dump error: {e}")


async def main():
    """Main debug function"""
    print("Debugging srv01 Backtest Tuple Structure")
    print("=" * 60)
    
    ssh_process = None
    
    try:
        # Step 1: Establish SSH tunnel
        ssh_process = await establish_ssh_tunnel("srv01")
        if not ssh_process:
            print("Failed to establish SSH tunnel. Exiting.")
            return 1
        
        # Step 2: Connect to API
        print("\nConnecting to HaasOnline API...")
        
        # Get credentials
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("API_EMAIL and API_PASSWORD environment variables are required")
            return 1
        
        # Initialize analyzer and connect
        cache = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache)
        success = analyzer.connect(
            host='127.0.0.1',
            port=8090,
            email=email,
            password=password
        )
        
        if not success:
            print("Failed to connect to HaasOnline API")
            return 1
        
        print("Connected successfully")
        executor = analyzer.executor
        
        # Step 3: Get first lab and its backtests
        print("\nGetting first lab...")
        labs = api.get_all_labs(executor)
        if not labs:
            print("No labs found")
            return 1
        
        first_lab = labs[0]
        lab_id = first_lab.lab_id
        lab_name = getattr(first_lab, 'lab_name', f'Lab {lab_id}')
        print(f"Using lab: {lab_name}")
        
        # Step 4: Get backtests for this lab
        print(f"\nGetting backtests for lab {lab_id}...")
        
        from pyHaasAPI.model import GetBacktestResultRequest
        request = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=5
        )
        backtest_results = api.get_backtest_result(executor, request)
        
        if not backtest_results:
            print("No backtest results found")
            return 1
        
        print(f"Got backtest results: {type(backtest_results)}")
        
        # Step 5: Debug the tuple structure
        if hasattr(backtest_results, '__iter__'):
            backtest_list = list(backtest_results)
            print(f"Converted to list: {len(backtest_list)} items")
            
            if backtest_list:
                # Debug first few backtests
                for i, backtest in enumerate(backtest_list[:2]):
                    debug_tuple_structure(backtest, i)
            else:
                print("Empty backtest list")
        else:
            print(f"Backtest results not iterable: {type(backtest_results)}")
            debug_tuple_structure(backtest_results, 0)
        
        print("\nDebug complete!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up SSH tunnel
        if ssh_process:
            await cleanup_ssh_tunnel(ssh_process)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
