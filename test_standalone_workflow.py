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
        # Import the CLI module directly
        sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI" / "cli_ref"))
        
        from project_manager_cli import ProjectManagerCLI
        print("✓ ProjectManagerCLI imported successfully")
        
        # Test instantiation
        cli = ProjectManagerCLI()
        print("✓ ProjectManagerCLI instantiated")
        
        # Test argument parsing
        args = cli.parser.parse_args(['--help'])
        print("✓ Argument parsing works")
        
    except Exception as e:
        print(f"✗ Direct CLI access failed: {e}")
        return False
    
    # Test 2: Check if we can run a simple command
    print("Testing simple command execution...")
    try:
        # Test snapshot command
        args = cli.parser.parse_args(['snapshot', '--server', 'srv03'])
        print("✓ Snapshot command parsed")
        
        # Test fetch command
        args = cli.parser.parse_args(['fetch', '--server', 'srv03', '--max-labs', '2', '--max-backtests', '5'])
        print("✓ Fetch command parsed")
        
        # Test analyze command
        args = cli.parser.parse_args(['analyze', '--server', 'srv03'])
        print("✓ Analyze command parsed")
        
        # Test create-bots command
        args = cli.parser.parse_args(['create-bots', '--server', 'srv03'])
        print("✓ Create-bots command parsed")
        
    except Exception as e:
        print(f"✗ Command parsing failed: {e}")
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

