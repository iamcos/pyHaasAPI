#!/usr/bin/env python3
"""
Test advanced market data features
"""
import os
from config import settings
from dotenv import load_dotenv
load_dotenv()
import time
from tests.integration.test_utils import TestLogger

def test_advanced_market_data(logger: TestLogger):
    """Test advanced market data features"""
    print("\n📊 Testing advanced market data...")
    
    executor = logger.test_data.get('executor')
    markets = logger.test_data.get('markets', [])
    
    if not executor:
        logger.log_test("advanced_market_data", False, "No executor available")
        return
    
    if not markets:
        logger.log_test("advanced_market_data", False, "No markets available for testing")
        return
    
    market = markets[0]
    market_symbol = f"{market.price_source.upper()}_{market.primary.upper()}_{market.secondary.upper()}_"
    print(f"  Testing with market: {market_symbol}")
    
    from pyHaasAPI import api
    
    # Test market price with retries
    print("  Testing market price (with retries)...")
    for attempt in range(3):
        try:
            price = api.get_market_price(executor, market_symbol)
            logger.log_test("get_market_price", True, data=price)
            break
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                print(f"    Attempt {attempt + 1} failed: {e}")
                print(f"    Waiting 120 seconds before retry...")
                time.sleep(120)
            else:
                logger.log_test("get_market_price", False, str(e))
    
    # Test order book with retries
    print("  Testing order book (with retries)...")
    for attempt in range(3):
        try:
            order_book = api.get_order_book(executor, market_symbol, depth=10)
            logger.log_test("get_order_book", True, data=order_book)
            break
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                print(f"    Attempt {attempt + 1} failed: {e}")
                print(f"    Waiting 120 seconds before retry...")
                time.sleep(120)
            else:
                logger.log_test("get_order_book", False, str(e))
    
    # Test last trades with retries
    print("  Testing last trades (with retries)...")
    for attempt in range(3):
        try:
            trades = api.get_last_trades(executor, market_symbol, limit=50)
            logger.log_test("get_last_trades", True, data=trades)
            break
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                print(f"    Attempt {attempt + 1} failed: {e}")
                print(f"    Waiting 120 seconds before retry...")
                time.sleep(120)
            else:
                logger.log_test("get_last_trades", False, str(e))
    
    # Test market snapshot with retries
    print("  Testing market snapshot (with retries)...")
    for attempt in range(3):
        try:
            snapshot = api.get_market_snapshot(executor, market_symbol)
            logger.log_test("get_market_snapshot", True, data=snapshot)
            break
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                print(f"    Attempt {attempt + 1} failed: {e}")
                print(f"    Waiting 120 seconds before retry...")
                time.sleep(120)
            else:
                logger.log_test("get_market_snapshot", False, str(e)) 

if __name__ == "__main__":
    # Place the main execution logic here
    pass 