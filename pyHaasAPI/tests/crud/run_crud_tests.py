#!/usr/bin/env python3
"""
CRUD Test Runner

Executes comprehensive CRUD tests with proper environment setup,
tunnel management, and cleanup discipline.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def kill_python_processes():
    """Kill all Python processes before starting tests"""
    print("Killing all Python processes...")
    try:
        subprocess.run(["timeout", "30", "pkill", "-f", "python"], 
                      capture_output=True, text=True, check=False)
        time.sleep(2)
        print("Python processes killed")
    except Exception as e:
        print(f"Warning: Could not kill Python processes: {e}")

def setup_ssh_tunnel():
    """Setup SSH tunnel to srv03"""
    print("Setting up SSH tunnel to srv03...")
    try:
        # Kill any existing SSH tunnels
        subprocess.run(["pkill", "-f", "ssh.*srv03"], 
                      capture_output=True, text=True, check=False)
        time.sleep(1)
        
        # Start new tunnel
        tunnel_cmd = [
            "ssh", "-N", 
            "-L", "8090:127.0.0.1:8090", 
            "-L", "8092:127.0.0.1:8092", 
            "prod@srv03"
        ]
        
        # Start tunnel in background
        tunnel_process = subprocess.Popen(tunnel_cmd, 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
        
        # Wait for tunnel to establish
        time.sleep(3)
        
        # Check if tunnel is working
        try:
            result = subprocess.run(["nc", "-zv", "127.0.0.1", "8090"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("SSH tunnel established successfully")
                return tunnel_process
            else:
                print("SSH tunnel failed to establish")
                tunnel_process.terminate()
                return None
        except subprocess.TimeoutExpired:
            print("SSH tunnel check timed out")
            tunnel_process.terminate()
            return None
            
    except Exception as e:
        print(f"Error setting up SSH tunnel: {e}")
        return None

def run_tests():
    """Run CRUD tests with proper environment"""
    print("Running CRUD tests...")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # Run tests with timeout
    test_cmd = [
        "timeout", "300",  # 5 minute timeout
        "bash", "-lc", 
        "source .venv/bin/activate && python -m pytest -v pyHaasAPI/tests/crud/"
    ]
    
    try:
        result = subprocess.run(test_cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=300,
                              env=env)
        
        print("Test output:")
        print(result.stdout)
        
        if result.stderr:
            print("Test errors:")
            print(result.stderr)
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("Tests timed out after 5 minutes")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def cleanup_tunnel(tunnel_process):
    """Clean up SSH tunnel"""
    if tunnel_process:
        print("Cleaning up SSH tunnel...")
        try:
            tunnel_process.terminate()
            tunnel_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            tunnel_process.kill()
        except Exception as e:
            print(f"Error cleaning up tunnel: {e}")

def main():
    """Main test runner"""
    print("Starting CRUD Test Runner")
    print("=" * 50)
    
    tunnel_process = None
    
    try:
        # Step 1: Kill existing Python processes
        kill_python_processes()
        
        # Step 2: Setup SSH tunnel
        tunnel_process = setup_ssh_tunnel()
        if not tunnel_process:
            print("Failed to setup SSH tunnel. Exiting.")
            return 1
        
        # Step 3: Run tests
        exit_code = run_tests()
        
        # Step 4: Report results
        if exit_code == 0:
            print("\n" + "=" * 50)
            print("✅ All CRUD tests passed!")
        else:
            print("\n" + "=" * 50)
            print("❌ Some CRUD tests failed!")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        # Cleanup
        cleanup_tunnel(tunnel_process)
        kill_python_processes()

if __name__ == "__main__":
    sys.exit(main())
