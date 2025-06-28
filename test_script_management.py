#!/usr/bin/env python3
"""
Test script management features
"""
from test_utils import TestLogger

def test_script_management(logger: TestLogger):
    """Test script management features"""
    print("\n📜 Testing script management...")
    
    executor = logger.test_data.get('executor')
    scripts = logger.test_data.get('scripts', [])
    
    if not executor:
        logger.log_test("script_management", False, "No executor available")
        return
    
    if not scripts:
        logger.log_test("script_management", False, "No scripts available for testing")
        return
    
    script = scripts[0]
    print(f"  Testing with script: {script.script_name} ({script.script_id})")
    
    from pyHaasAPI import api
    
    # Test script record
    try:
        record = api.get_script_record(executor, script.script_id)
        logger.log_test("get_script_record", True, data=record)
    except Exception as e:
        logger.log_test("get_script_record", False, str(e))
    
    # Test script folders
    try:
        folders = api.get_all_script_folders(executor)
        logger.log_test("get_all_script_folders", True, data=folders)
    except Exception as e:
        logger.log_test("get_all_script_folders", False, str(e))
    
    # Test create script folder (read-only test)
    try:
        folder = api.create_script_folder(executor, "TEST_FOLDER")
        logger.log_test("create_script_folder", True, data=folder)
    except Exception as e:
        logger.log_test("create_script_folder", False, str(e))
    
    # Test move script to folder (read-only test)
    try:
        result = api.move_script_to_folder(executor, script.script_id, -1)
        logger.log_test("move_script_to_folder", True, data=result)
    except Exception as e:
        logger.log_test("move_script_to_folder", False, str(e)) 