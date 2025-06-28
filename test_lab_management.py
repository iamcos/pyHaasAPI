#!/usr/bin/env python3
"""
Test advanced lab management features
"""
from test_utils import TestLogger

def test_advanced_lab_management(logger: TestLogger):
    """Test advanced lab management features"""
    print("\n🧪 Testing advanced lab management...")
    
    executor = logger.test_data.get('executor')
    labs = logger.test_data.get('labs', [])
    
    if not executor:
        logger.log_test("advanced_lab_management", False, "No executor available")
        return
    
    if not labs:
        logger.log_test("advanced_lab_management", False, "No labs available for testing")
        return
    
    lab = labs[0]
    print(f"  Testing with lab: {lab.lab_name} ({lab.lab_id})")
    
    from pyHaasAPI import api
    
    # Test lab execution status
    try:
        status = api.get_lab_execution_status(executor, lab.lab_id)
        logger.log_test("get_lab_execution_status", True, data=status)
    except Exception as e:
        logger.log_test("get_lab_execution_status", False, str(e))
    
    # Test lab details
    try:
        details = api.get_lab_details(executor, lab.lab_id)
        logger.log_test("get_lab_details", True, data=details)
    except Exception as e:
        logger.log_test("get_lab_details", False, str(e))
    
    # Test start lab execution status (read-only test)
    try:
        start_status = api.start_lab_execution_status(executor, lab.lab_id)
        logger.log_test("start_lab_execution_status", True, data=start_status)
    except Exception as e:
        logger.log_test("start_lab_execution_status", False, str(e))
    
    # Test cancel lab execution status (read-only test)
    try:
        cancel_status = api.cancel_lab_execution_status(executor, lab.lab_id)
        logger.log_test("cancel_lab_execution_status", True, data=cancel_status)
    except Exception as e:
        logger.log_test("cancel_lab_execution_status", False, str(e)) 