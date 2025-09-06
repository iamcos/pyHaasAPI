#!/usr/bin/env python3
"""
Test Margin Settings API Functions

This script tests the newly implemented margin settings functions
to ensure they work with the real HaasOnline API endpoints.
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def test_margin_settings():
    """Test margin settings API functions"""
    
    # Connect to API
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        logger.error("❌ API_EMAIL and API_PASSWORD must be set in .env file")
        return False

    logger.info("Connecting to HaasOnline API...")

    try:
        haas_api = api.RequestsExecutor(
            host=api_host,
            port=api_port,
            state=api.Guest()
        )
        executor = haas_api.authenticate(api_email, api_password)
        logger.info("✅ Connected to API")
    except Exception as e:
        logger.error(f"❌ Failed to connect to API: {e}")
        return False

    # Get all accounts
    try:
        accounts = api.get_all_accounts(executor)
        logger.info(f"Found {len(accounts)} accounts")
        
        # Find a Binance Futures account for testing
        test_account = None
        test_market = "BINANCEFUTURES_LTC_USDT_PERPETUAL"
        
        for account in accounts:
            if account.get('EC') == 'BINANCEFUTURES':
                test_account = account
                break
        
        if not test_account:
            logger.error("❌ No Binance Futures account found for testing")
            return False
            
        account_id = test_account['AID']
        logger.info(f"Using test account: {test_account['N']} ({account_id[:8]})")
        
    except Exception as e:
        logger.error(f"❌ Failed to get accounts: {e}")
        return False

    # Test 1: Get current margin settings
    logger.info("\n🔍 Test 1: Getting current margin settings...")
    try:
        current_settings = api.get_margin_settings(executor, account_id, test_market)
        logger.info(f"✅ Current settings: {current_settings}")
        
        # Parse the response
        position_mode = current_settings.get('PM', 'Unknown')
        margin_mode = current_settings.get('SMM', 'Unknown')
        leverage_limit = current_settings.get('LL', 'Unknown')
        spot_leverage = current_settings.get('SL', 'Unknown')
        
        logger.info(f"  Position Mode: {position_mode} ({'HEDGE' if position_mode == 1 else 'ONE_WAY'})")
        logger.info(f"  Margin Mode: {margin_mode} ({'ISOLATED' if margin_mode == 1 else 'CROSS'})")
        logger.info(f"  Leverage Limit: {leverage_limit}")
        logger.info(f"  Spot Leverage: {spot_leverage}")
        
    except Exception as e:
        logger.error(f"❌ Failed to get margin settings: {e}")
        return False

    # Test 2: Set position mode to HEDGE (1)
    logger.info("\n🔧 Test 2: Setting position mode to HEDGE...")
    try:
        success = api.set_position_mode(executor, account_id, test_market, 1)
        if success:
            logger.info("✅ Position mode set to HEDGE successfully")
        else:
            logger.warning("⚠️ Position mode change may have failed")
    except Exception as e:
        logger.error(f"❌ Failed to set position mode: {e}")

    # Test 3: Set margin mode to CROSS (0)
    logger.info("\n🔧 Test 3: Setting margin mode to CROSS...")
    try:
        success = api.set_margin_mode(executor, account_id, test_market, 0)
        if success:
            logger.info("✅ Margin mode set to CROSS successfully")
        else:
            logger.warning("⚠️ Margin mode change may have failed")
    except Exception as e:
        logger.error(f"❌ Failed to set margin mode: {e}")

    # Test 4: Set leverage to 20x
    logger.info("\n🔧 Test 4: Setting leverage to 20x...")
    try:
        success = api.set_leverage(executor, account_id, test_market, 20.0)
        if success:
            logger.info("✅ Leverage set to 20x successfully")
        else:
            logger.warning("⚠️ Leverage change may have failed")
    except Exception as e:
        logger.error(f"❌ Failed to set leverage: {e}")

    # Test 5: Use adjust_margin_settings to set all at once
    logger.info("\n🔧 Test 5: Setting all margin settings at once...")
    try:
        success = api.adjust_margin_settings(
            executor, 
            account_id, 
            test_market,
            position_mode=1,  # HEDGE
            margin_mode=0,    # CROSS
            leverage=20.0     # 20x
        )
        if success:
            logger.info("✅ All margin settings adjusted successfully")
        else:
            logger.warning("⚠️ Margin settings adjustment may have failed")
    except Exception as e:
        logger.error(f"❌ Failed to adjust margin settings: {e}")

    # Test 6: Verify the changes
    logger.info("\n🔍 Test 6: Verifying changes...")
    try:
        updated_settings = api.get_margin_settings(executor, account_id, test_market)
        logger.info(f"✅ Updated settings: {updated_settings}")
        
        # Parse the response
        position_mode = updated_settings.get('PM', 'Unknown')
        margin_mode = updated_settings.get('SMM', 'Unknown')
        leverage_limit = updated_settings.get('LL', 'Unknown')
        spot_leverage = updated_settings.get('SL', 'Unknown')
        
        logger.info(f"  Position Mode: {position_mode} ({'HEDGE' if position_mode == 1 else 'ONE_WAY'})")
        logger.info(f"  Margin Mode: {margin_mode} ({'ISOLATED' if margin_mode == 1 else 'CROSS'})")
        logger.info(f"  Leverage Limit: {leverage_limit}")
        logger.info(f"  Spot Leverage: {spot_leverage}")
        
    except Exception as e:
        logger.error(f"❌ Failed to verify margin settings: {e}")
        return False

    logger.info("\n🎉 All margin settings tests completed!")
    return True

if __name__ == "__main__":
    test_margin_settings()

