#!/usr/bin/env python3
"""
Test utilities for pyHaasAPI verification
"""
import time
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import os
load_dotenv()
from config import settings

class TestLogger:
    def __init__(self):
        self.test_results = {}
        self.test_data = {}
    
    def log_test(self, test_name: str, success: bool, error: str = None, data: Any = None):
        """Log test result with details"""
        self.test_results[test_name] = {
            'success': success,
            'error': error,
            'data': data,
            'timestamp': time.time()
        }
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if error:
            print(f"    Error: {error}")
        if data and success:
            print(f"    Data: {type(data).__name__} ({len(data) if hasattr(data, '__len__') else 'N/A'})")
    
    def get_summary(self):
        """Get test summary statistics"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': success_rate
        }
    
    def print_category_summary(self, category_name: str):
        """Print summary for a specific category"""
        summary = self.get_summary()
        print(f"\n📁 {category_name} ({summary['success_rate']:.1f}% success)")
        print(f"   Passed: {summary['passed']}/{summary['total']}")
        
        for test_name, result in self.test_results.items():
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {test_name}")
            if not result['success'] and result['error']:
                print(f"      Error: {result['error']}")

def test_server_connectivity() -> bool:
    """Test basic server connectivity"""
    print("🔍 Testing server connectivity...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:8090/api/v1/guest", timeout=10)
        print(f"  ✅ PASS server_connectivity")
        print(f"    Data: Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"  ❌ FAIL server_connectivity")
        print(f"    Error: {e}")
        return False

def test_authentication(logger: TestLogger) -> bool:
    """Test authentication"""
    print("\n🔐 Testing authentication...")
    try:
        from pyHaasAPI import api
        
        executor = api.RequestsExecutor(
            host=settings.API_HOST,
            port=settings.API_PORT,
            state=api.Guest()
        )
        
        auth_result = executor.authenticate(
            email=settings.API_EMAIL,
            password=settings.API_PASSWORD
        )
        
        logger.log_test("authentication", True, data="Authenticated successfully")
        logger.test_data['executor'] = auth_result  # Store the authenticated executor
        return True
        
    except Exception as e:
        logger.log_test("authentication", False, str(e))
        return False 

if __name__ == "__main__":
    # Place the main execution logic here
    pass 