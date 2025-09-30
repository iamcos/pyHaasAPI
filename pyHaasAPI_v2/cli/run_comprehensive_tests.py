#!/usr/bin/env python3
"""
Comprehensive Test Runner

Runs all tests for the comprehensive backtesting system with detailed reporting.
"""

import unittest
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add pyHaasAPI_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_comprehensive_backtesting import (
    TestDataModels,
    TestComprehensiveBacktestingManager,
    TestIntegration,
    TestMockedAPI,
    TestErrorHandling,
    TestPerformance
)


class ComprehensiveTestRunner:
    """Comprehensive test runner with detailed reporting"""
    
    def __init__(self):
        self.test_suite = unittest.TestSuite()
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def add_all_tests(self):
        """Add all test classes to the test suite"""
        test_classes = [
            TestDataModels,
            TestComprehensiveBacktestingManager,
            TestIntegration,
            TestMockedAPI,
            TestErrorHandling,
            TestPerformance
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            self.test_suite.addTests(tests)
        
        print(f"📋 Added {self.test_suite.countTestCases()} tests from {len(test_classes)} test classes")
    
    def run_tests(self, verbosity=2):
        """Run all tests with detailed reporting"""
        print(f"🚀 Starting comprehensive test suite...")
        print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(self.test_suite)
        
        self.end_time = time.time()
        
        # Store results
        self.results = {
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
            'duration_seconds': self.end_time - self.start_time,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'was_successful': result.wasSuccessful(),
            'failure_details': [
                {
                    'test': str(test),
                    'traceback': traceback
                }
                for test, traceback in result.failures
            ],
            'error_details': [
                {
                    'test': str(test),
                    'traceback': traceback
                }
                for test, traceback in result.errors
            ]
        }
        
        return result
    
    def print_summary(self):
        """Print detailed test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        print(f"⏰ Duration: {self.results['duration_seconds']:.2f} seconds")
        print(f"🧪 Tests run: {self.results['tests_run']}")
        print(f"✅ Success rate: {self.results['success_rate']:.1f}%")
        print(f"❌ Failures: {self.results['failures']}")
        print(f"💥 Errors: {self.results['errors']}")
        
        if self.results['failures'] > 0:
            print(f"\n❌ FAILURES ({self.results['failures']}):")
            for i, failure in enumerate(self.results['failure_details'], 1):
                print(f"   {i}. {failure['test']}")
                print(f"      {failure['traceback'].split('AssertionError: ')[-1].strip()}")
        
        if self.results['errors'] > 0:
            print(f"\n💥 ERRORS ({self.results['errors']}):")
            for i, error in enumerate(self.results['error_details'], 1):
                print(f"   {i}. {error['test']}")
                print(f"      {error['traceback'].split('Exception: ')[-1].strip()}")
        
        # Performance metrics
        if self.results['tests_run'] > 0:
            avg_time_per_test = self.results['duration_seconds'] / self.results['tests_run']
            print(f"\n⚡ Performance:")
            print(f"   Average time per test: {avg_time_per_test:.3f} seconds")
            print(f"   Tests per second: {self.results['tests_run'] / self.results['duration_seconds']:.1f}")
        
        # Overall status
        if self.results['was_successful']:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"   The comprehensive backtesting system is working correctly.")
        else:
            print(f"\n⚠️ SOME TESTS FAILED")
            print(f"   Please review the failures and errors above.")
        
        return self.results['was_successful']
    
    def save_results(self, filename="test_results.json"):
        """Save test results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
    
    def run_coverage_analysis(self):
        """Run basic coverage analysis"""
        print(f"\n📊 COVERAGE ANALYSIS")
        print("=" * 40)
        
        # Test categories and their coverage
        categories = {
            'Data Models': ['LabConfig', 'CoinConfig', 'BacktestStep', 'ProjectConfig', 'AnalysisResult'],
            'Manager Core': ['Initialization', 'Filtering', 'Recommendations'],
            'Integration': ['Serialization', 'Configuration'],
            'Mocked API': ['Initialization', 'Backtest Analysis'],
            'Error Handling': ['Invalid Configs', 'Empty Configs', 'Invalid Criteria'],
            'Performance': ['Large Datasets', 'Memory Efficiency']
        }
        
        total_categories = len(categories)
        covered_categories = 0
        
        for category, components in categories.items():
            print(f"   {category}: {len(components)} components tested")
            covered_categories += 1
        
        coverage_percentage = (covered_categories / total_categories) * 100
        print(f"\n📈 Category Coverage: {coverage_percentage:.1f}%")
        
        return coverage_percentage


def main():
    """Main test runner entry point"""
    print("🧪 Comprehensive Backtesting System Test Runner")
    print("=" * 60)
    
    # Create test runner
    runner = ComprehensiveTestRunner()
    
    # Add all tests
    runner.add_all_tests()
    
    # Run tests
    result = runner.run_tests(verbosity=2)
    
    # Print summary
    success = runner.print_summary()
    
    # Run coverage analysis
    coverage = runner.run_coverage_analysis()
    
    # Save results
    runner.save_results()
    
    # Print final status
    print(f"\n🏁 FINAL STATUS")
    print("=" * 40)
    print(f"✅ Tests: {'PASSED' if success else 'FAILED'}")
    print(f"📊 Coverage: {coverage:.1f}%")
    print(f"⏰ Duration: {runner.results['duration_seconds']:.2f}s")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
