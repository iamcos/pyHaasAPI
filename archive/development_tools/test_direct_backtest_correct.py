#!/usr/bin/env python3
"""
Test script for direct backtest execution using the correct workflow:
1. GET_SCRIPT_RECORD - Get script details and parameters
2. EXECUTE_BACKTEST - Execute with bot parameters
3. GET_BACKTEST_* - Retrieve results
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from pyHaasAPI import api, BacktestManager
from pyHaasAPI.model import (
    GetScriptRecordRequest,
    ExecuteBacktestRequest,
    BacktestHistoryRequest
)
def get_specific_bot(executor, bot_id):
    """Get a specific bot by ID for backtesting"""
    print(f"🔍 Getting specific bot: {bot_id}")
    
    # Get all bots
    bots = api.get_all_bots(executor)
    if not bots:
        print("❌ No bots found")
        return None
    
    # Find the specific bot
    for bot in bots:
        if hasattr(bot, 'bot_id') and bot.bot_id == bot_id:
            print(f"✅ Found bot: {getattr(bot, 'bot_name', 'Unknown')}")
            print(f"   Bot ID: {getattr(bot, 'bot_id', 'N/A')}")
            print(f"   Script ID: {getattr(bot, 'script_id', 'N/A')}")
            print(f"   Market: {getattr(bot, 'market_tag', 'N/A')}")
            print(f"   Active: {getattr(bot, 'is_active', False)}")
            
            # Convert to dictionary format for BacktestManager
            bot_data = {
                'BotId': getattr(bot, 'bot_id', ''),
                'BotName': getattr(bot, 'bot_name', ''),
                'ScriptId': getattr(bot, 'script_id', ''),
                'MarketTag': getattr(bot, 'market_tag', ''),
                'IsActive': getattr(bot, 'is_active', False),
                'Settings': getattr(bot, 'settings', {})
            }
            return bot_data
    
    print(f"❌ Bot {bot_id} not found")
    return None


def get_script_record(executor, script_id):
    """Get script record with parameters"""
    print(f"📋 Getting script record for: {script_id}")
    
    request = GetScriptRecordRequest(script_id=script_id)
    result = api.get_script_record(executor, request)
    
    if result.get('Success', False):
        print("✅ Script record retrieved successfully")
        return result
    else:
        print(f"❌ Failed to get script record: {result.get('Error', 'Unknown error')}")
        return None


def execute_direct_backtest(executor, bot_data, script_record, start_unix, end_unix):
    """Execute direct backtest using EXECUTE_BACKTEST"""
    print("🚀 Executing direct backtest...")
    
    # Generate new backtest ID
    backtest_id = str(uuid.uuid4())
    print(f"📝 Generated backtest ID: {backtest_id}")
    
    # Build settings JSON
    settings = api.build_backtest_settings(bot_data, script_record)
    print(f"⚙️ Built settings with {len(settings.get('scriptParameters', {}))} parameters")
    
    # Create execute request
    request = ExecuteBacktestRequest(
        backtest_id=backtest_id,
        script_id=bot_data['ScriptId'],
        settings=settings,
        start_unix=start_unix,
        end_unix=end_unix
    )
    
    # Execute backtest
    result = api.execute_backtest(executor, request)
    
    if result.get('Success', False):
        print(f"✅ Backtest executed successfully: {result.get('Data', 'No data')}")
        return backtest_id
    else:
        print(f"❌ Failed to execute backtest: {result.get('Error', 'Unknown error')}")
        return None


def get_backtest_history(executor, script_id=None, limit=10):
    """Get backtest history"""
    print("📊 Getting backtest history...")
    
    request = BacktestHistoryRequest(
        script_id=script_id,
        limit=limit
    )
    
    result = api.get_backtest_history(executor, request)
    
    if result.get('Success', False):
        backtests = result.get('Data', [])
        print(f"✅ Found {len(backtests)} backtests")
        return backtests
    else:
        print(f"❌ Failed to get backtest history: {result.get('Error', 'Unknown error')}")
        return []


def main():
    """Main test function"""
    print("🧪 Testing Direct Backtest Execution Workflow")
    print("🎯 Testing with specific bot: ad31b193572f4add898853b35d36dfca")
    print("=" * 60)
    
    try:
        # Authenticate using the standard API workflow
        print("🔐 Authenticating...")
        
        # Create API connection
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        
        # Authenticate (this handles both email/password and OTC internally)
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        
        print("✅ Authentication successful")
        
        # Initialize BacktestManager
        backtest_manager = BacktestManager(executor)
        
        # Get specific bot
        bot_id = "ad31b193572f4add898853b35d36dfca"
        bot_data = get_specific_bot(executor, bot_id)
        if not bot_data:
            return
        
        print(f"🤖 Testing with bot: {bot_data.get('BotName', 'Unknown')}")
        
        # Execute backtest using BacktestManager
        print("🚀 Executing backtest via BacktestManager...")
        execution_result = backtest_manager.execute_bot_backtest(bot_data, duration_days=1)
        
        if execution_result.success:
            print(f"✅ Backtest executed successfully!")
            print(f"🎯 Backtest ID: {execution_result.backtest_id}")
            print(f"📊 Script ID: {execution_result.script_id}")
            print(f"🏷️ Market: {execution_result.market_tag}")
            
            # Get backtest results
            print(f"\n📊 Getting backtest results...")
            try:
                # Wait a moment for backtest to complete
                import time
                time.sleep(2)
                
                # Get backtest result
                from pyHaasAPI.model import GetBacktestResultRequest
                result_request = GetBacktestResultRequest(
                    backtest_id=execution_result.backtest_id,
                    next_page_id=0,
                    page_lenght=1
                )
                
                backtest_result = api.get_backtest_result(executor, result_request)
                if backtest_result and hasattr(backtest_result, 'items') and backtest_result.items:
                    bt = backtest_result.items[0]
                    print(f"📈 Backtest Results:")
                    print(f"   ROI: {getattr(bt, 'roi_percentage', 'N/A')}%")
                    print(f"   Win Rate: {getattr(bt, 'win_rate', 'N/A')}")
                    print(f"   Total Trades: {getattr(bt, 'total_trades', 'N/A')}")
                    print(f"   Max Drawdown: {getattr(bt, 'max_drawdown', 'N/A')}%")
                    print(f"   Realized Profits: ${getattr(bt, 'realized_profits_usdt', 'N/A')}")
                    print(f"   PC Value: {getattr(bt, 'pc_value', 'N/A')}")
                    print(f"   Status: {getattr(bt, 'status', 'N/A')}")
                else:
                    print("⚠️ Backtest results not yet available (may still be processing)")
                    
            except Exception as e:
                print(f"⚠️ Could not get backtest results: {e}")
        else:
            print(f"❌ Backtest execution failed: {execution_result.error_message}")
            return
        
        # Test backtest history
        print("\n📋 Getting backtest history...")
        history = backtest_manager.get_backtest_history(execution_result.script_id, limit=5)
        print(f"🔍 History data type: {type(history)}")
        print(f"🔍 History content: {history}")
        
        if history:
            # Check if it's a dict with 'I' key (backtest items)
            if isinstance(history, dict) and 'I' in history:
                backtests = history['I']
                print(f"✅ Found {len(backtests)} recent backtests:")
                for bt in backtests[:3]:
                    bt_id = bt.get('BID', 'Unknown')  # Backtest ID
                    script_title = bt.get('ST', 'Unknown')  # Script Title
                    print(f"  - {bt_id}: {script_title}")
                    
                # Look for our specific backtest in the history
                our_backtest = None
                for bt in backtests:
                    if bt.get('BID') == execution_result.backtest_id:
                        our_backtest = bt
                        break
                
                if our_backtest:
                    print(f"\n🎯 Found our backtest in history:")
                    print(f"   Backtest ID: {our_backtest.get('BID', 'N/A')}")
                    print(f"   Script Title: {our_backtest.get('ST', 'N/A')}")
                    print(f"   Start Time: {our_backtest.get('BS', 'N/A')}")
                    print(f"   End Time: {our_backtest.get('BE', 'N/A')}")
                    print(f"   Execution Start: {our_backtest.get('ES', 'N/A')}")
                    print(f"   Execution End: {our_backtest.get('EE', 'N/A')}")
                    print(f"   Account Tag: {our_backtest.get('AT', 'N/A')}")
                    print(f"   Market: {our_backtest.get('ME', 'N/A')}")
                    print(f"   Profit: {our_backtest.get('PT', 'N/A')}")
                    print(f"   ROI: {our_backtest.get('RT', 'N/A')}")
                    print(f"   Is Active: {our_backtest.get('IA', 'N/A')}")
                else:
                    print(f"⚠️ Our backtest {execution_result.backtest_id} not found in history yet")
            else:
                print(f"⚠️ Unexpected history format: {type(history)}")
        else:
            print("❌ No backtest history found")
        
        # Test validation workflow
        print("\n🔍 Testing bot validation...")
        validation_result = backtest_manager.validate_live_bot(bot_data)
        if validation_result.validation_successful:
            print(f"✅ Bot validation successful!")
            print(f"🎯 Validation backtest ID: {validation_result.backtest_id}")
        else:
            print(f"❌ Bot validation failed: {validation_result.error_message}")
        
        print("\n✅ Complete BacktestManager workflow tested successfully!")
        print(f"🔍 You can now use GET_BACKTEST_* commands with backtest ID: {execution_result.backtest_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
