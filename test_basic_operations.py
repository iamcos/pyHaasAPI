#!/usr/bin/env python3
"""
Test basic API operations
"""
from test_utils import TestLogger

def test_basic_operations(logger: TestLogger):
    """Test basic API operations"""
    print("\n📋 Testing basic operations...")
    
    executor = logger.test_data.get('executor')
    if not executor:
        logger.log_test("basic_operations", False, "No executor available")
        return
    
    from pyHaasAPI import api
    
    # Get scripts
    try:
        scripts = api.get_scripts_by_name(executor, "Scalper Bot")
        logger.log_test("get_scripts_by_name", True, data=scripts)
        logger.test_data['scripts'] = scripts
    except Exception as e:
        logger.log_test("get_scripts_by_name", False, str(e))
    
    # Get all scripts
    try:
        all_scripts = api.get_all_scripts(executor)
        logger.log_test("get_all_scripts", True, data=all_scripts)
    except Exception as e:
        logger.log_test("get_all_scripts", False, str(e))
    
    # Get markets
    try:
        markets = api.get_all_markets(executor)
        logger.log_test("get_all_markets", True, data=markets)
        logger.test_data['markets'] = markets
    except Exception as e:
        logger.log_test("get_all_markets", False, str(e))
    
    # Get accounts
    try:
        accounts = api.get_accounts(executor)
        logger.log_test("get_accounts", True, data=accounts)
        logger.test_data['accounts'] = accounts
    except Exception as e:
        logger.log_test("get_accounts", False, str(e))
    
    # Get bots
    try:
        bots = api.get_all_bots(executor)
        logger.log_test("get_all_bots", True, data=bots)
        logger.test_data['bots'] = bots
    except Exception as e:
        logger.log_test("get_all_bots", False, str(e))
    
    # Get labs
    try:
        labs = api.get_all_labs(executor)
        logger.log_test("get_all_labs", True, data=labs)
        logger.test_data['labs'] = labs
    except Exception as e:
        logger.log_test("get_all_labs", False, str(e)) 