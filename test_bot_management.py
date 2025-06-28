#!/usr/bin/env python3
"""
Test advanced bot management features
"""
from test_utils import TestLogger

def test_advanced_bot_management(logger: TestLogger):
    """Test advanced bot management features"""
    print("\n🤖 Testing advanced bot management...")
    
    executor = logger.test_data.get('executor')
    bots = logger.test_data.get('bots', [])
    
    if not executor:
        logger.log_test("advanced_bot_management", False, "No executor available")
        return
    
    if not bots:
        logger.log_test("advanced_bot_management", False, "No bots available for testing")
        return
    
    bot = bots[0]
    print(f"  Testing with bot: {bot.bot_name} ({bot.bot_id})")
    
    from pyHaasAPI import api
    
    # Test bot runtime
    try:
        runtime = api.get_bot_runtime(executor, bot.bot_id)
        logger.log_test("get_bot_runtime", True, data=runtime)
    except Exception as e:
        logger.log_test("get_bot_runtime", False, str(e))
    
    # Test bot orders
    try:
        orders = api.get_bot_orders(executor, bot.bot_id)
        logger.log_test("get_bot_orders", True, data=orders)
    except Exception as e:
        logger.log_test("get_bot_orders", False, str(e))
    
    # Test bot positions
    try:
        positions = api.get_bot_positions(executor, bot.bot_id)
        logger.log_test("get_bot_positions", True, data=positions)
    except Exception as e:
        logger.log_test("get_bot_positions", False, str(e))
    
    # Test bot open orders
    try:
        open_orders = api.get_bot_open_orders(executor, bot.bot_id)
        logger.log_test("get_bot_open_orders", True, data=open_orders)
    except Exception as e:
        logger.log_test("get_bot_open_orders", False, str(e))
    
    # Test bot open positions
    try:
        open_positions = api.get_bot_open_positions(executor, bot.bot_id)
        logger.log_test("get_bot_open_positions", True, data=open_positions)
    except Exception as e:
        logger.log_test("get_bot_open_positions", False, str(e))
    
    # Test bot closed positions
    try:
        closed_positions = api.get_bot_closed_positions(executor, bot.bot_id)
        logger.log_test("get_bot_closed_positions", True, data=closed_positions)
    except Exception as e:
        logger.log_test("get_bot_closed_positions", False, str(e))
    
    # Test bot settings (read-only test)
    try:
        settings = {"test_setting": "test_value"}
        updated_bot = api.edit_bot_settings(executor, bot.bot_id, settings)
        logger.log_test("edit_bot_settings", True, data=updated_bot)
    except Exception as e:
        logger.log_test("edit_bot_settings", False, str(e))
    
    # Test bot rename (read-only test)
    try:
        new_name = f"{bot.bot_name}_TEST"
        renamed_bot = api.rename_bot(executor, bot.bot_id, new_name)
        logger.log_test("rename_bot", True, data=renamed_bot)
    except Exception as e:
        logger.log_test("rename_bot", False, str(e))
    
    # Test bot clone (read-only test)
    try:
        cloned_bot = api.clone_bot(executor, bot.bot_id, "TEST_CLONE")
        logger.log_test("clone_bot", True, data=cloned_bot)
    except Exception as e:
        logger.log_test("clone_bot", False, str(e))
    
    # Test bot reset (read-only test)
    try:
        reset_bot = api.reset_bot(executor, bot.bot_id)
        logger.log_test("reset_bot", True, data=reset_bot)
    except Exception as e:
        logger.log_test("reset_bot", False, str(e))
    
    # Test bot favorite (read-only test)
    try:
        favorited_bot = api.favorite_bot(executor, bot.bot_id, True)
        logger.log_test("favorite_bot", True, data=favorited_bot)
    except Exception as e:
        logger.log_test("favorite_bot", False, str(e)) 