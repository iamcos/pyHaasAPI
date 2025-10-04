#!/usr/bin/env python3
"""
Test runner script for pyHaasAPI tests.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False):
    """Run tests with specified options."""
    
    # Base pytest command
    cmd = ["python3", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=pyHaasAPI", "--cov-report=html", "--cov-report=term"])
    
    # Add test type filters
    if test_type == "unit":
        cmd.extend(["-m", "unit", "pyHaasAPI/tests/unit/"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration", "pyHaasAPI/tests/integration/"])
    elif test_type == "performance":
        cmd.extend(["-m", "performance", "pyHaasAPI/tests/performance/"])
    else:
        # Run all tests
        cmd.append("pyHaasAPI/tests/")
    
    # Add ignore patterns for problematic directories
    cmd.extend([
        "--ignore=archive",
        "--ignore=pyHaasAPI_v1", 
        "--ignore=tests",
        "--ignore=pyHaasAPI_no_pydantic"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ All tests passed!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run pyHaasAPI tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "performance"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    
    args = parser.parse_args()
    
    print(f"🧪 Running {args.type} tests...")
    if args.verbose:
        print("📝 Verbose mode enabled")
    if args.coverage:
        print("📊 Coverage reporting enabled")
    
    return run_tests(args.type, args.verbose, args.coverage)


if __name__ == "__main__":
    sys.exit(main())


