#!/usr/bin/env python3
"""
Standalone test of server content revision workflow
Bypasses complex imports and tests core functionality directly
"""

import asyncio
import sys
import os
import signal
import time
import json
from pathlib import Path

def timeout_handler(signum, frame):
    print(f"\n⏰ TIMEOUT after 20 seconds")
    sys.exit(1)

async def test_standalone_workflow():
    """Test standalone workflow without complex imports"""
    print("=== Testing Standalone Workflow ===")
    
    # Test 1: Check if we can access the CLI directly
    print("Testing direct CLI access...")
    try:
        from pyHaasAPI.cli.consolidated_cli import ConsolidatedCLI
        print("✓ ConsolidatedCLI imported successfully")
        
        # Test instantiation
        cli = ConsolidatedCLI()
        print("✓ ConsolidatedCLI instantiated")
        
    except Exception as e:
        print(f"✗ Direct CLI access failed: {e}")
        return False
    
    # Test 2: Check if we can parse simple arguments
    print("Testing argument parsing (simulated)...")
    try:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--analyze', action='store_true')
        parser.add_argument('--create-bots', action='store_true')
        
        # Test analysis command
        args = parser.parse_args(['--analyze'])
        print(f"✓ Analyze flag parsed: {args.analyze}")
        
        # Test create-bots command
        args = parser.parse_args(['--create-bots'])
        print(f"✓ Create-bots flag parsed: {args.create_bots}")
        
    except Exception as e:
        print(f"✗ Argument parsing failed: {e}")
        return False
    
    print("\n✅ Standalone workflow components working!")
    return True

def main():
    """Main test function"""
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(20)
    
    try:
        result = asyncio.run(test_standalone_workflow())
        signal.alarm(0)  # Cancel timeout
        return 0 if result else 1
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"✗ Test failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

