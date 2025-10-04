#!/usr/bin/env python3
import signal
import sys
import os
import subprocess

def timeout_handler(signum, frame):
    print("Test analysis timed out after 15 seconds")
    sys.exit(1)

# Set up timeout
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(15)

try:
    print("=== Analyzing Test Errors ===")
    
    # Change to project directory
    os.chdir('/Users/georgiigavrilenko/Documents/GitHub/pyHaasAPI')
    
    # Run pytest with limited output to see specific errors
    print("Running pytest with limited scope...")
    result = subprocess.run([
        'source', '.venv/bin/activate', '&&', 
        'python3', '-m', 'pytest', 'pyHaasAPI/tests/unit/test_minimal.py', '-v', '--tb=short'
    ], shell=True, capture_output=True, text=True, timeout=10)
    
    print("Minimal test output:")
    print(result.stdout)
    
    if result.stderr:
        print("Minimal test errors:")
        print(result.stderr)
    
    print(f"Minimal test exit code: {result.returncode}")
    
    # Try running just one integration test
    print("\nRunning single integration test...")
    result2 = subprocess.run([
        'source', '.venv/bin/activate', '&&', 
        'python3', '-m', 'pytest', 'pyHaasAPI/tests/integration/test_api_integration.py::TestAPIIntegration::test_error_handling_integration', '-v', '--tb=short'
    ], shell=True, capture_output=True, text=True, timeout=10)
    
    print("Single integration test output:")
    print(result2.stdout)
    
    if result2.stderr:
        print("Single integration test errors:")
        print(result2.stderr)
    
    print(f"Single integration test exit code: {result2.returncode}")
    
    print("=== Test Analysis Complete ===")
    
except Exception as e:
    print(f"Test analysis failed: {e}")
    import traceback
    traceback.print_exc()
finally:
    signal.alarm(0)  # Cancel timeout

