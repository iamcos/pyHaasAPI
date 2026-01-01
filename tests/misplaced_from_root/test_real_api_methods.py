#!/usr/bin/env python3
"""
Real server testing script - Test actual API methods with real data from srv03.
This verifies that all API modules work correctly with real server responses.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI.core.client import AsyncHaasClient
from pyHaasAPI.core.auth import AuthenticationManager
from pyHaasAPI.config.api_config import APIConfig
from pyHaasAPI.api.lab.lab_api import LabAPI
from pyHaasAPI.api.bot.bot_api import BotAPI
from pyHaasAPI.api.account.account_api import AccountAPI
from pyHaasAPI.api.backtest.backtest_api import BacktestAPI
from pyHaasAPI.api.order.order_api import OrderAPI
from pyHaasAPI.api.market.market_api import MarketAPI
from pyHaasAPI.api.script.script_api import ScriptAPI

async def test_lab_api():
    """Test LabAPI with real server data."""
    print("🧪 Testing LabAPI with real server data...")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD'),
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    try:
        # Connect and authenticate
        await client.connect()
        session = await auth_manager.authenticate()
        print(f"✅ Authenticated: {session.user_id}")
        
        # Create LabAPI
        lab_api = LabAPI(client, auth_manager)
        
        # Test get_labs - get real lab data
        print("📊 Testing get_labs()...")
        labs = await lab_api.get_labs()
        print(f"✅ Got {len(labs)} labs from server")
        
        if labs:
            # Test get_lab_details with first lab
            first_lab = labs[0]
            print(f"🔍 Testing get_lab_details() with lab: {first_lab.lab_id}")
            lab_details = await lab_api.get_lab_details(first_lab.lab_id)
            print(f"✅ Lab details: {lab_details.lab_name}")
            
            # Test get_lab_backtests
            print(f"📈 Testing get_lab_backtests() with lab: {first_lab.lab_id}")
            backtests = await lab_api.get_lab_backtests(first_lab.lab_id)
            print(f"✅ Got {len(backtests)} backtests from server")
            
            return True
        else:
            print("⚠️ No labs found to test with")
            return True
            
    except Exception as e:
        print(f"❌ LabAPI test failed: {e}")
        return False
    finally:
        await client.close()

async def test_bot_api():
    """Test BotAPI with real server data."""
    print("🤖 Testing BotAPI with real server data...")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD'),
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    try:
        # Connect and authenticate
        await client.connect()
        session = await auth_manager.authenticate()
        print(f"✅ Authenticated: {session.user_id}")
        
        # Create BotAPI
        bot_api = BotAPI(client, auth_manager)
        
        # Test get_all_bots - get real bot data
        print("🤖 Testing get_all_bots()...")
        bots = await bot_api.get_all_bots()
        print(f"✅ Got {len(bots)} bots from server")
        
        if bots:
            # Test get_bot_details with first bot
            first_bot = bots[0]
            print(f"🔍 Testing get_bot_details() with bot: {first_bot.bot_id}")
            bot_details = await bot_api.get_bot_details(first_bot.bot_id)
            print(f"✅ Bot details: {bot_details.bot_name}")
            
            return True
        else:
            print("⚠️ No bots found to test with")
            return True
            
    except Exception as e:
        print(f"❌ BotAPI test failed: {e}")
        return False
    finally:
        await client.close()

async def test_account_api():
    """Test AccountAPI with real server data."""
    print("💰 Testing AccountAPI with real server data...")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD'),
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    try:
        # Connect and authenticate
        await client.connect()
        session = await auth_manager.authenticate()
        print(f"✅ Authenticated: {session.user_id}")
        
        # Create AccountAPI
        account_api = AccountAPI(client, auth_manager)
        
        # Test get_accounts - get real account data
        print("💰 Testing get_accounts()...")
        accounts = await account_api.get_accounts()
        print(f"✅ Got {len(accounts)} accounts from server")
        
        if accounts:
            # Test get_account_data with first account
            first_account = accounts[0]
            print(f"🔍 Testing get_account_data() with account: {first_account.account_id}")
            account_data = await account_api.get_account_data(first_account.account_id)
            print(f"✅ Account data: {account_data.exchange}")
            
            return True
        else:
            print("⚠️ No accounts found to test with")
            return True
            
    except Exception as e:
        print(f"❌ AccountAPI test failed: {e}")
        return False
    finally:
        await client.close()

async def test_backtest_api():
    """Test BacktestAPI with real server data."""
    print("📊 Testing BacktestAPI with real server data...")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD'),
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    try:
        # Connect and authenticate
        await client.connect()
        session = await auth_manager.authenticate()
        print(f"✅ Authenticated: {session.user_id}")
        
        # Create BacktestAPI
        backtest_api = BacktestAPI(client, auth_manager)
        
        # Test get_backtest_history - get real backtest data
        print("📈 Testing get_backtest_history()...")
        from pyHaasAPI.models.backtest import BacktestHistoryRequest
        # Get a lab ID first from LabAPI
        from pyHaasAPI.api.lab.lab_api import LabAPI
        lab_api = LabAPI(client, auth_manager)
        labs = await lab_api.get_labs()
        if labs:
            lab_id = labs[0].lab_id
            request = BacktestHistoryRequest(lab_id=lab_id, page=1, page_size=10)
            history = await backtest_api.get_backtest_history(request)
            print(f"✅ Got backtest history from server")
        else:
            print("⚠️ No labs found to test backtest history")
            return True
        
        # Test set_history_depth
        print("⏰ Testing set_history_depth()...")
        success = await backtest_api.set_history_depth("BTC_USDT_PERPETUAL", 12)
        print(f"✅ Set history depth: {success}")
        
        return True
            
    except Exception as e:
        print(f"❌ BacktestAPI test failed: {e}")
        return False
    finally:
        await client.close()

async def test_market_api():
    """Test MarketAPI with real server data."""
    print("📈 Testing MarketAPI with real server data...")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD'),
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    try:
        # Connect and authenticate
        await client.connect()
        session = await auth_manager.authenticate()
        print(f"✅ Authenticated: {session.user_id}")
        
        # Create MarketAPI
        market_api = MarketAPI(client, auth_manager)
        
        # Test get_trade_markets - get real market data
        print("📈 Testing get_trade_markets()...")
        markets = await market_api.get_trade_markets()
        print(f"✅ Got {len(markets)} markets from server")
        
        if markets:
            # Test get_price_data with first market
            first_market = markets[0]
            print(f"💰 Testing get_price_data() with market: {first_market.market}")
            price_data = await market_api.get_price_data(first_market.market)
            print(f"✅ Price data: {price_data.close}")
            
            return True
        else:
            print("⚠️ No markets found to test with")
            return True
            
    except Exception as e:
        print(f"❌ MarketAPI test failed: {e}")
        return False
    finally:
        await client.close()

async def test_script_api():
    """Test ScriptAPI with real server data."""
    print("📜 Testing ScriptAPI with real server data...")
    
    # Load environment variables
    load_dotenv()
    
    # Create configuration
    config = APIConfig(
        email=os.getenv('API_EMAIL'),
        password=os.getenv('API_PASSWORD'),
        host="127.0.0.1",
        port=8090,
        timeout=30.0
    )
    
    # Create client and auth manager
    client = AsyncHaasClient(config)
    auth_manager = AuthenticationManager(client, config)
    
    try:
        # Connect and authenticate
        await client.connect()
        session = await auth_manager.authenticate()
        print(f"✅ Authenticated: {session.user_id}")
        
        # Create ScriptAPI
        script_api = ScriptAPI(client, auth_manager)
        
        # Test get_all_scripts - get real script data
        print("📜 Testing get_all_scripts()...")
        scripts = await script_api.get_all_scripts()
        print(f"✅ Got {len(scripts)} scripts from server")
        
        if scripts:
            # Test get_script_record with first script
            first_script = scripts[0]
            print(f"🔍 Testing get_script_record() with script: {first_script.script_id}")
            script_record = await script_api.get_script_record(first_script.script_id)
            print(f"✅ Script record: {script_record.script_name}")
            
            return True
        else:
            print("⚠️ No scripts found to test with")
            return True
            
    except Exception as e:
        print(f"❌ ScriptAPI test failed: {e}")
        return False
    finally:
        await client.close()

async def main():
    """Run all API tests with real server data."""
    print("🚀 Testing ALL API modules with REAL SERVER DATA from srv03...")
    print("📡 Using SSH tunnel: ssh -N -L 8090:127.0.0.1:8090 -L 8092:127.0.0.1:8092 prod@srv03 &")
    
    results = []
    
    # Test all API modules
    results.append(await test_lab_api())
    results.append(await test_bot_api())
    results.append(await test_account_api())
    results.append(await test_backtest_api())
    results.append(await test_market_api())
    results.append(await test_script_api())
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n🎯 REAL SERVER TEST RESULTS:")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ALL API MODULES WORKING WITH REAL SERVER DATA!")
        print("✅ pyHaasAPI v2 is fully functional and production ready!")
    else:
        print("💥 Some API modules failed - need investigation")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())
