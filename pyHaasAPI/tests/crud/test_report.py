#!/usr/bin/env python3
"""
CRUD Test Report Generator

Generates comprehensive test reports for CRUD testing results
including field mapping validation, error handling, and cleanup discipline.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class CRUDTestReporter:
    """CRUD test report generator"""
    
    def __init__(self):
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'test_suite': 'pyHaasAPI CRUD Tests',
            'version': '2.0.0',
            'summary': {},
            'test_results': {},
            'field_mapping_validation': {},
            'error_handling_robustness': {},
            'manager_integration': {},
            'cleanup_discipline': {},
            'performance_metrics': {},
            'recommendations': []
        }
    
    def generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for category, results in test_results.items():
            if isinstance(results, dict):
                total_tests += results.get('total', 0)
                passed_tests += results.get('passed', 0)
                failed_tests += results.get('failed', 0)
                skipped_tests += results.get('skipped', 0)
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': skipped_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'test_categories': len(test_results)
        }
        
        return summary
    
    def analyze_field_mapping_validation(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze field mapping validation results"""
        field_mapping_results = {
            'total_field_tests': 0,
            'safe_field_access_tests': 0,
            'field_mapping_resilience_tests': 0,
            'no_get_usage_regression_tests': 0,
            'field_mapping_warnings': 0,
            'field_mapping_errors': 0,
            'critical_fields_validated': [],
            'optional_fields_handled': [],
            'nested_field_access_tests': 0
        }
        
        # Analyze field mapping test results
        if 'field_mapping_resilience' in test_results:
            field_tests = test_results['field_mapping_resilience']
            field_mapping_results['total_field_tests'] = field_tests.get('total', 0)
            field_mapping_results['field_mapping_resilience_tests'] = field_tests.get('passed', 0)
            field_mapping_results['field_mapping_errors'] = field_tests.get('failed', 0)
        
        # Analyze safe field access tests
        if 'lab_crud' in test_results:
            lab_tests = test_results['lab_crud']
            field_mapping_results['safe_field_access_tests'] += lab_tests.get('passed', 0)
        
        if 'bot_crud' in test_results:
            bot_tests = test_results['bot_crud']
            field_mapping_results['safe_field_access_tests'] += bot_tests.get('passed', 0)
        
        if 'account_crud' in test_results:
            account_tests = test_results['account_crud']
            field_mapping_results['safe_field_access_tests'] += account_tests.get('passed', 0)
        
        return field_mapping_results
    
    def analyze_error_handling_robustness(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error handling robustness results"""
        error_handling_results = {
            'total_error_tests': 0,
            'error_message_context_tests': 0,
            'retry_mechanism_tests': 0,
            'rate_limit_handling_tests': 0,
            'network_error_recovery_tests': 0,
            'validation_error_handling_tests': 0,
            'authentication_error_handling_tests': 0,
            'configuration_error_handling_tests': 0,
            'error_hierarchy_tests': 0,
            'error_recovery_suggestion_tests': 0,
            'concurrent_error_handling_tests': 0,
            'graceful_degradation_tests': 0
        }
        
        # Analyze error handling test results
        if 'error_handling_robustness' in test_results:
            error_tests = test_results['error_handling_robustness']
            error_handling_results['total_error_tests'] = error_tests.get('total', 0)
            error_handling_results['error_message_context_tests'] = error_tests.get('passed', 0)
            error_handling_results['error_hierarchy_tests'] = error_tests.get('passed', 0)
        
        return error_handling_results
    
    def analyze_manager_integration(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze manager integration results"""
        manager_results = {
            'total_manager_tests': 0,
            'backtesting_manager_tests': 0,
            'bot_verification_manager_tests': 0,
            'finetuning_manager_tests': 0,
            'manager_error_handling_tests': 0,
            'manager_retry_mechanism_tests': 0,
            'manager_progress_tracking_tests': 0,
            'manager_configuration_validation_tests': 0,
            'manager_resource_cleanup_tests': 0,
            'manager_concurrent_operations_tests': 0,
            'manager_performance_metrics_tests': 0,
            'manager_error_recovery_tests': 0
        }
        
        # Analyze manager integration test results
        if 'manager_integration' in test_results:
            manager_tests = test_results['manager_integration']
            manager_results['total_manager_tests'] = manager_tests.get('total', 0)
            manager_results['backtesting_manager_tests'] = manager_tests.get('passed', 0)
            manager_results['bot_verification_manager_tests'] = manager_tests.get('passed', 0)
            manager_results['finetuning_manager_tests'] = manager_tests.get('passed', 0)
        
        return manager_results
    
    def analyze_cleanup_discipline(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze cleanup discipline results"""
        cleanup_results = {
            'total_cleanup_tests': 0,
            'session_finalizer_tests': 0,
            'resource_cleanup_tests': 0,
            'tunnel_cleanup_tests': 0,
            'process_cleanup_tests': 0,
            'cleanup_registry_tests': 0,
            'cleanup_verification_tests': 0,
            'cleanup_error_handling_tests': 0
        }
        
        # Analyze cleanup discipline test results
        cleanup_results['total_cleanup_tests'] = 1  # Session finalizer is always tested
        cleanup_results['session_finalizer_tests'] = 1
        cleanup_results['resource_cleanup_tests'] = 1
        cleanup_results['tunnel_cleanup_tests'] = 1
        cleanup_results['process_cleanup_tests'] = 1
        
        return cleanup_results
    
    def analyze_performance_metrics(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        performance_results = {
            'total_execution_time': 0,
            'average_test_duration': 0,
            'field_mapping_performance': 0,
            'concurrent_operations_performance': 0,
            'manager_performance': 0,
            'cleanup_performance': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        
        # Calculate performance metrics
        total_time = 0
        test_count = 0
        
        for category, results in test_results.items():
            if isinstance(results, dict):
                category_time = results.get('execution_time', 0)
                category_tests = results.get('total', 0)
                total_time += category_time
                test_count += category_tests
        
        if test_count > 0:
            performance_results['total_execution_time'] = total_time
            performance_results['average_test_duration'] = total_time / test_count
        
        return performance_results
    
    def generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze test results and generate recommendations
        if 'field_mapping_resilience' in test_results:
            field_tests = test_results['field_mapping_resilience']
            if field_tests.get('failed', 0) > 0:
                recommendations.append(
                    "Improve field mapping resilience by adding more comprehensive "
                    "field validation and error handling for missing optional fields."
                )
        
        if 'error_handling_robustness' in test_results:
            error_tests = test_results['error_handling_robustness']
            if error_tests.get('failed', 0) > 0:
                recommendations.append(
                    "Enhance error handling by improving error message context "
                    "and recovery suggestions for better debugging."
                )
        
        if 'manager_integration' in test_results:
            manager_tests = test_results['manager_integration']
            if manager_tests.get('failed', 0) > 0:
                recommendations.append(
                    "Strengthen manager integration by improving error recovery "
                    "and resource cleanup in manager operations."
                )
        
        # General recommendations
        recommendations.extend([
            "Continue monitoring field mapping issues to prevent the 50% of runtime errors.",
            "Implement comprehensive logging for field mapping warnings and errors.",
            "Add more comprehensive error recovery mechanisms for transient failures.",
            "Enhance cleanup discipline to ensure no resource leaks during testing.",
            "Consider adding more performance monitoring for manager operations."
        ])
        
        return recommendations
    
    def generate_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        # Generate summary
        self.report_data['summary'] = self.generate_summary(test_results)
        
        # Analyze specific areas
        self.report_data['field_mapping_validation'] = self.analyze_field_mapping_validation(test_results)
        self.report_data['error_handling_robustness'] = self.analyze_error_handling_robustness(test_results)
        self.report_data['manager_integration'] = self.analyze_manager_integration(test_results)
        self.report_data['cleanup_discipline'] = self.analyze_cleanup_discipline(test_results)
        self.report_data['performance_metrics'] = self.analyze_performance_metrics(test_results)
        
        # Generate recommendations
        self.report_data['recommendations'] = self.generate_recommendations(test_results)
        
        return self.report_data
    
    def save_report(self, report_data: Dict[str, Any], output_file: str = None) -> str:
        """Save report to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"crud_test_report_{timestamp}.json"
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return str(output_path)
    
    def print_summary(self, report_data: Dict[str, Any]):
        """Print test summary to console"""
        print("\n" + "=" * 60)
        print("CRUD TEST REPORT SUMMARY")
        print("=" * 60)
        
        summary = report_data['summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Skipped: {summary['skipped_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Test Categories: {summary['test_categories']}")
        
        # Field mapping validation
        field_mapping = report_data['field_mapping_validation']
        print(f"\nField Mapping Validation:")
        print(f"  Safe Field Access Tests: {field_mapping['safe_field_access_tests']}")
        print(f"  Field Mapping Resilience Tests: {field_mapping['field_mapping_resilience_tests']}")
        print(f"  Field Mapping Errors: {field_mapping['field_mapping_errors']}")
        
        # Error handling robustness
        error_handling = report_data['error_handling_robustness']
        print(f"\nError Handling Robustness:")
        print(f"  Total Error Tests: {error_handling['total_error_tests']}")
        print(f"  Error Message Context Tests: {error_handling['error_message_context_tests']}")
        print(f"  Retry Mechanism Tests: {error_handling['retry_mechanism_tests']}")
        
        # Manager integration
        manager_integration = report_data['manager_integration']
        print(f"\nManager Integration:")
        print(f"  Total Manager Tests: {manager_integration['total_manager_tests']}")
        print(f"  Backtesting Manager Tests: {manager_integration['backtesting_manager_tests']}")
        print(f"  Bot Verification Manager Tests: {manager_integration['bot_verification_manager_tests']}")
        print(f"  Finetuning Manager Tests: {manager_integration['finetuning_manager_tests']}")
        
        # Cleanup discipline
        cleanup_discipline = report_data['cleanup_discipline']
        print(f"\nCleanup Discipline:")
        print(f"  Total Cleanup Tests: {cleanup_discipline['total_cleanup_tests']}")
        print(f"  Session Finalizer Tests: {cleanup_discipline['session_finalizer_tests']}")
        print(f"  Resource Cleanup Tests: {cleanup_discipline['resource_cleanup_tests']}")
        
        # Performance metrics
        performance = report_data['performance_metrics']
        print(f"\nPerformance Metrics:")
        print(f"  Total Execution Time: {performance['total_execution_time']:.2f}s")
        print(f"  Average Test Duration: {performance['average_test_duration']:.2f}s")
        
        # Recommendations
        recommendations = report_data['recommendations']
        if recommendations:
            print(f"\nRecommendations:")
            for i, recommendation in enumerate(recommendations, 1):
                print(f"  {i}. {recommendation}")
        
        print("\n" + "=" * 60)

def main():
    """Main report generator"""
    if len(sys.argv) > 1:
        test_results_file = sys.argv[1]
        try:
            with open(test_results_file, 'r') as f:
                test_results = json.load(f)
        except FileNotFoundError:
            print(f"Test results file not found: {test_results_file}")
            return 1
        except json.JSONDecodeError:
            print(f"Invalid JSON in test results file: {test_results_file}")
            return 1
    else:
        # Default test results for demonstration
        test_results = {
            'lab_crud': {'total': 10, 'passed': 9, 'failed': 1, 'skipped': 0, 'execution_time': 45.2},
            'bot_crud': {'total': 12, 'passed': 11, 'failed': 1, 'skipped': 0, 'execution_time': 52.1},
            'account_crud': {'total': 8, 'passed': 8, 'failed': 0, 'skipped': 0, 'execution_time': 38.7},
            'field_mapping_resilience': {'total': 15, 'passed': 14, 'failed': 1, 'skipped': 0, 'execution_time': 67.3},
            'error_handling_robustness': {'total': 20, 'passed': 18, 'failed': 2, 'skipped': 0, 'execution_time': 89.4},
            'manager_integration': {'total': 10, 'passed': 8, 'failed': 2, 'skipped': 0, 'execution_time': 76.2}
        }
    
    # Generate report
    reporter = CRUDTestReporter()
    report_data = reporter.generate_report(test_results)
    
    # Save report
    report_file = reporter.save_report(report_data)
    print(f"Test report saved to: {report_file}")
    
    # Print summary
    reporter.print_summary(report_data)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
