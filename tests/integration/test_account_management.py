#!/usr/bin/env python3
"""
Test advanced account management features
"""
import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
from .test_utils import TestLogger, authenticate_for_tests

def test_advanced_account_management(logger: TestLogger):
    """Test advanced account management features"""
    print("\n💰 Testing advanced account management...")
    
    executor = logger.test_data.get('executor')
    accounts = logger.test_data.get('accounts', [])
    
    if not executor:
        logger.log_test("advanced_account_management", False, "No executor available")
        return
    
    if not accounts:
        logger.log_test("advanced_account_management", False, "No accounts available for testing")
        return
    
    account = accounts[0]
    print(f"  Testing with account: {account.name} ({account.account_id})")
    
    from pyHaasAPI import api
    
    # Test account deposits
    try:
        deposits = api.get_account_deposits(executor, account.account_id)
        logger.log_test("get_account_deposits", True, data=deposits)
    except Exception as e:
        logger.log_test("get_account_deposits", False, str(e))
    
    # Test account withdrawals
    try:
        withdrawals = api.get_account_withdrawals(executor, account.account_id)
        logger.log_test("get_account_withdrawals", True, data=withdrawals)
    except Exception as e:
        logger.log_test("get_account_withdrawals", False, str(e))
    
    # Test position mode setting (read-only test)
    try:
        result = api.set_position_mode(executor, account.account_id, "hedged")
        logger.log_test("set_position_mode", True, data=result)
    except Exception as e:
        logger.log_test("set_position_mode", False, str(e))
    
    # Test margin mode setting (read-only test)
    try:
        result = api.set_margin_mode(executor, account.account_id, "isolated")
        logger.log_test("set_margin_mode", True, data=result)
    except Exception as e:
        logger.log_test("set_margin_mode", False, str(e))
    
    # Test account data
    try:
        account_data = api.get_account_data(executor, account.account_id)
        logger.log_test("get_account_data", True, data=account_data)
    except Exception as e:
        logger.log_test("get_account_data", False, str(e))
    
    # Test account balance
    try:
        balance = api.get_account_balance(executor, account.account_id)
        logger.log_test("get_account_balance", True, data=balance)
    except Exception as e:
        logger.log_test("get_account_balance", False, str(e))
    
    # Test all account balances
    try:
        all_balances = api.get_all_account_balances(executor)
        logger.log_test("get_all_account_balances", True, data=all_balances)
    except Exception as e:
        logger.log_test("get_all_account_balances", False, str(e))
    
    # Test account orders
    try:
        account_orders = api.get_account_orders(executor, account.account_id)
        logger.log_test("get_account_orders", True, data=account_orders)
    except Exception as e:
        logger.log_test("get_account_orders", False, str(e))
    
    # Test account positions
    try:
        account_positions = api.get_account_positions(executor, account.account_id)
        logger.log_test("get_account_positions", True, data=account_positions)
    except Exception as e:
        logger.log_test("get_account_positions", False, str(e))
    
    # Test account trades
    try:
        account_trades = api.get_account_trades(executor, account.account_id)
        logger.log_test("get_account_trades", True, data=account_trades)
    except Exception as e:
        logger.log_test("get_account_trades", False, str(e))

if __name__ == "__main__":
    # Place the main execution logic here
    pass 