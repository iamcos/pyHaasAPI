#!/usr/bin/env python3
"""
Simple test to check basic functionality without complex imports
"""

import sys
import os

def test_basic_python():
    """Test basic Python functionality"""
    print("Testing basic Python...")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    return True

def test_simple_imports():
    """Test simple imports that shouldn't hang"""
    print("Testing simple imports...")
    
    try:
        import json
        print("✓ json imported")
        
        import asyncio
        print("✓ asyncio imported")
        
        import pathlib
        print("✓ pathlib imported")
        
        return True
    except Exception as e:
        print(f"✗ Simple imports failed: {e}")
        return False

def test_pyhaasapi_structure():
    """Test if pyHaasAPI directory structure exists"""
    print("Testing pyHaasAPI structure...")
    
    try:
        import pyHaasAPI
        print("✓ pyHaasAPI package found")
        
        # Check if key modules exist
        core_path = os.path.join(os.path.dirname(pyHaasAPI.__file__), 'core')
        if os.path.exists(core_path):
            print("✓ core directory exists")
        else:
            print("✗ core directory missing")
            return False
            
        return True
    except Exception as e:
        print(f"✗ pyHaasAPI structure test failed: {e}")
        return False

def main():
    """Main test function"""
    print("=== Simple System Test ===")
    
    # Test 1: Basic Python
    if not test_basic_python():
        print("❌ Basic Python test failed")
        return 1
    
    # Test 2: Simple imports
    if not test_simple_imports():
        print("❌ Simple imports test failed")
        return 1
    
    # Test 3: Package structure
    if not test_pyhaasapi_structure():
        print("❌ Package structure test failed")
        return 1
    
    print("\n✅ All basic tests passed!")
    return 0

if __name__ == "__main__":
    exit(main())