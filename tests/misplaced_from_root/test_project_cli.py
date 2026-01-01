#!/usr/bin/env python3
"""
Test the project manager CLI directly
"""

import sys
import os
import signal
import time

def timeout_handler(signum, frame):
    print(f"\n⏰ TIMEOUT after 15 seconds")
    sys.exit(1)

def main():
    """Test consolidated CLI import"""
    print("=== Testing Consolidated CLI ===")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(15)
    
    try:
        start_time = time.time()
        
        # Test direct import of the CLI module
        from pyHaasAPI.cli.consolidated_cli import ConsolidatedCLI
        
        end_time = time.time()
        signal.alarm(0)  # Cancel timeout
        
        print(f"✓ ConsolidatedCLI imported successfully in {end_time - start_time:.2f}s")
        
        # Test instantiation
        cli = ConsolidatedCLI()
        print("✓ ConsolidatedCLI instantiated successfully")
        
        return 0
        
    except Exception as e:
        signal.alarm(0)  # Cancel timeout
        print(f"✗ ConsolidatedCLI import failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

