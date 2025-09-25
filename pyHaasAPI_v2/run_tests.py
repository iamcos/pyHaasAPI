#!/usr/bin/env python3
"""
Test runner for pyHaasAPI v2

This script provides a convenient way to run tests with different configurations
and options for the pyHaasAPI v2 test suite.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=False, parallel=False, markers=None):
    """
    Run tests with the specified configuration.
    
    Args:
        test_type: Type of tests to run (all, unit, integration, performance)
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        parallel: Run tests in parallel
        markers: Additional pytest markers to filter tests
    """
    
    # Base command
    cmd = ["python", "-m", "pytest"]
    
    # Add test type specific options
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    
    # Add markers if specified
    if markers:
        cmd.extend(["-m", markers])
    
    # Add verbose output
    if verbose:
        cmd.append("-vv")
    
    # Add coverage reporting
    if coverage:
        cmd.extend(["--cov=pyHaasAPI_v2", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add test directory
    cmd.append("tests/")
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest: pip install pytest")
        return 1


def main():
    """Main entry point for the test runner"""
    parser = argparse.ArgumentParser(
        description="Test runner for pyHaasAPI v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_tests.py
  
  # Run only unit tests
  python run_tests.py --type unit
  
  # Run tests with coverage
  python run_tests.py --coverage
  
  # Run tests in parallel
  python run_tests.py --parallel
  
  # Run specific test file
  python run_tests.py --file test_core.py
  
  # Run tests with specific markers
  python run_tests.py --markers "not slow"
        """
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "integration", "performance", "fast"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Enable coverage reporting"
    )
    
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--file", "-f",
        help="Run specific test file"
    )
    
    parser.add_argument(
        "--markers", "-m",
        help="Additional pytest markers to filter tests"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        deps = [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "pytest-xdist>=2.5.0",
            "pytest-mock>=3.6.0"
        ]
        
        for dep in deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                print(f"✅ Installed {dep}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {dep}")
                return 1
        
        print("✅ All test dependencies installed!")
        return 0
    
    # Check if we're in the right directory
    if not Path("pyHaasAPI_v2").exists():
        print("❌ Please run this script from the project root directory")
        return 1
    
    # Run specific test file if specified
    if args.file:
        cmd = ["python", "-m", "pytest", f"pyHaasAPI_v2/tests/{args.file}"]
        if args.verbose:
            cmd.append("-vv")
        if args.coverage:
            cmd.extend(["--cov=pyHaasAPI_v2", "--cov-report=html", "--cov-report=term-missing"])
        
        print(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True)
            print("\n✅ All tests passed!")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Tests failed with exit code {e.returncode}")
            return e.returncode
    
    # Run tests with the specified configuration
    return run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
        markers=args.markers
    )


if __name__ == "__main__":
    sys.exit(main())
