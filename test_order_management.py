#!/usr/bin/env python3
"""
Test order management features
"""
from test_utils import TestLogger

def test_order_management(logger: TestLogger):
    """Test order management features"""
    print("\n📋 Testing order management...")
    
    executor = logger.test_data.get('executor')
    accounts = logger.test_data.get('accounts', [])
    markets = logger.test_data.get('markets', [])
    
    if not executor:
        logger.log_test("order_management", False, "No executor available")
        return
    
    from pyHaasAPI import api
    
    # Test get all orders
    try:
        all_orders = api.get_all_orders(executor)
        logger.log_test("get_all_orders", True, data=all_orders)
    except Exception as e:
        logger.log_test("get_all_orders", False, str(e))
    
    # Test place order (read-only test with dummy data)
    if accounts and markets:
        account = accounts[0]
        market = markets[0]
        market_symbol = f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
        
        try:
            order_id = api.place_order(
                executor, 
                account.account_id, 
                market_symbol, 
                "buy", 
                100.0, 
                0.001, 
                0, 
                0, 
                "Test"
            )
            logger.log_test("place_order", True, data=order_id)
        except Exception as e:
            logger.log_test("place_order", False, str(e))
        
        # Test cancel order (read-only test)
        try:
            result = api.cancel_order(executor, account.account_id, "test_order_id")
            logger.log_test("cancel_order", True, data=result)
        except Exception as e:
            logger.log_test("cancel_order", False, str(e))
    else:
        logger.log_test("place_order", False, "No accounts or markets available")
        logger.log_test("cancel_order", False, "No accounts or markets available") 