#!/usr/bin/env python3
"""
Main verification script for pyHaasAPI
Runs all individual test modules and provides comprehensive summary
"""
from test_utils import TestLogger, test_server_connectivity, test_authentication
from test_basic_operations import test_basic_operations
from test_bot_management import test_advanced_bot_management
from test_account_management import test_advanced_account_management
from test_market_data import test_advanced_market_data
from test_lab_management import test_advanced_lab_management
from test_script_management import test_script_management
from test_order_management import test_order_management

def run_verification():
    """Run complete verification test suite"""
    print("🧪 pyHaasAPI Verification Test Suite\n")
    print("=" * 60)
    
    # Initialize test logger
    logger = TestLogger()
    
    # Test 1: Server connectivity
    if not test_server_connectivity():
        print("\n❌ Server connectivity failed. Cannot proceed with API tests.")
        print_final_summary(logger)
        return
    
    # Test 2: Authentication
    if not test_authentication(logger):
        print("\n❌ Authentication failed. Cannot proceed with API tests.")
        print_final_summary(logger)
        return
    
    # Test 3: Basic operations
    test_basic_operations(logger)
    logger.print_category_summary("Basic Operations")
    
    # Test 4: Advanced bot management
    test_advanced_bot_management(logger)
    logger.print_category_summary("Advanced Bot Management")
    
    # Test 5: Advanced account management
    test_advanced_account_management(logger)
    logger.print_category_summary("Advanced Account Management")
    
    # Test 6: Advanced market data
    test_advanced_market_data(logger)
    logger.print_category_summary("Advanced Market Data")
    
    # Test 7: Advanced lab management
    test_advanced_lab_management(logger)
    logger.print_category_summary("Advanced Lab Management")
    
    # Test 8: Script management
    test_script_management(logger)
    logger.print_category_summary("Script Management")
    
    # Test 9: Order management
    test_order_management(logger)
    logger.print_category_summary("Order Management")
    
    # Print final summary
    print_final_summary(logger)

def print_final_summary(logger: TestLogger):
    """Print comprehensive final summary"""
    print("\n" + "=" * 60)
    print("📊 FINAL VERIFICATION SUMMARY")
    print("=" * 60)
    
    summary = logger.get_summary()
    
    print(f"Total Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    
    print("\n" + "=" * 60)
    print("🎯 VERIFICATION CONCLUSIONS")
    print("=" * 60)
    
    if summary['success_rate'] == 100:
        print("🎉 ALL CLAIMS VERIFIED! All endpoints are working correctly.")
    elif summary['success_rate'] > 80:
        print("✅ MOST CLAIMS VERIFIED! Most endpoints are working correctly.")
    elif summary['success_rate'] > 50:
        print("⚠️  PARTIAL VERIFICATION! Some endpoints are working, others need attention.")
    else:
        print("❌ VERIFICATION FAILED! Many endpoints are not working as expected.")
    
    print(f"\n📊 Final Statistics:")
    print(f"   - Total Endpoints Tested: {summary['total']}")
    print(f"   - Working Endpoints: {summary['passed']}")
    print(f"   - Non-Working Endpoints: {summary['failed']}")
    print(f"   - Overall Success Rate: {summary['success_rate']:.1f}%")
    
    # Detailed breakdown
    print("\n" + "=" * 60)
    print("📋 DETAILED BREAKDOWN")
    print("=" * 60)
    
    # Group by test type
    test_groups = {
        'authentication': 'Authentication',
        'get_scripts_by_name': 'Basic Operations',
        'get_all_scripts': 'Basic Operations',
        'get_all_markets': 'Basic Operations',
        'get_accounts': 'Basic Operations',
        'get_all_bots': 'Basic Operations',
        'get_all_labs': 'Basic Operations',
        'get_bot_runtime': 'Advanced Bot Management',
        'get_bot_orders': 'Advanced Bot Management',
        'get_bot_positions': 'Advanced Bot Management',
        'get_bot_open_orders': 'Advanced Bot Management',
        'get_bot_open_positions': 'Advanced Bot Management',
        'get_bot_closed_positions': 'Advanced Bot Management',
        'edit_bot_settings': 'Advanced Bot Management',
        'rename_bot': 'Advanced Bot Management',
        'clone_bot': 'Advanced Bot Management',
        'reset_bot': 'Advanced Bot Management',
        'favorite_bot': 'Advanced Bot Management',
        'get_account_deposits': 'Advanced Account Management',
        'get_account_withdrawals': 'Advanced Account Management',
        'set_position_mode': 'Advanced Account Management',
        'set_margin_mode': 'Advanced Account Management',
        'get_account_data': 'Advanced Account Management',
        'get_account_balance': 'Advanced Account Management',
        'get_all_account_balances': 'Advanced Account Management',
        'get_account_orders': 'Advanced Account Management',
        'get_account_positions': 'Advanced Account Management',
        'get_account_trades': 'Advanced Account Management',
        'get_tick_data': 'Advanced Market Data',
        'get_time_sync': 'Advanced Market Data',
        'get_price_sources': 'Advanced Market Data',
        'get_market_price': 'Advanced Market Data',
        'get_order_book': 'Advanced Market Data',
        'get_last_trades': 'Advanced Market Data',
        'get_market_snapshot': 'Advanced Market Data',
        'get_lab_execution_status': 'Advanced Lab Management',
        'get_lab_details': 'Advanced Lab Management',
        'start_lab_execution_status': 'Advanced Lab Management',
        'cancel_lab_execution_status': 'Advanced Lab Management',
        'get_script_record': 'Script Management',
        'get_all_script_folders': 'Script Management',
        'create_script_folder': 'Script Management',
        'move_script_to_folder': 'Script Management',
        'get_all_orders': 'Order Management',
        'place_order': 'Order Management',
        'cancel_order': 'Order Management',
    }
    
    category_results = {}
    for test_name, result in logger.test_results.items():
        category = test_groups.get(test_name, 'Other')
        if category not in category_results:
            category_results[category] = {'passed': 0, 'failed': 0, 'tests': []}
        
        if result['success']:
            category_results[category]['passed'] += 1
        else:
            category_results[category]['failed'] += 1
        
        category_results[category]['tests'].append({
            'name': test_name,
            'success': result['success'],
            'error': result['error']
        })
    
    for category, results in category_results.items():
        total = results['passed'] + results['failed']
        success_rate = (results['passed'] / total * 100) if total > 0 else 0
        print(f"\n📁 {category} ({success_rate:.1f}% success)")
        print(f"   Passed: {results['passed']}/{total}")
        
        for test in results['tests']:
            status = "✅" if test['success'] else "❌"
            print(f"   {status} {test['name']}")
            if not test['success'] and test['error']:
                print(f"      Error: {test['error']}")

if __name__ == "__main__":
    run_verification() 