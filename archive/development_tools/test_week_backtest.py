#!/usr/bin/env python3
"""
Test script for week-long backtest execution with settings verification
"""

import sys
import os
import uuid
import time
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
    """Get a specific bot by ID and show all its fields"""
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
            print(f"\n📋 Bot Details:")
            print(f"   Bot ID: {getattr(bot, 'bot_id', 'N/A')}")
            print(f"   Bot Name: {getattr(bot, 'bot_name', 'N/A')}")
            print(f"   Script ID: {getattr(bot, 'script_id', 'N/A')}")
            print(f"   Account ID: {getattr(bot, 'account_id', 'N/A')}")
            print(f"   Market: {getattr(bot, 'market', 'N/A')}")
            print(f"   Is Active: {getattr(bot, 'is_activated', False)}")
            print(f"   Chart Interval: {getattr(bot, 'chart_interval', 'N/A')}")
            print(f"   Chart Style: {getattr(bot, 'chart_style', 'N/A')}")
            
            # Show settings
            settings = getattr(bot, 'settings', None)
            if settings:
                print(f"\n⚙️ Bot Settings:")
                print(f"   Bot ID: {getattr(settings, 'bot_id', 'N/A')}")
                print(f"   Bot Name: {getattr(settings, 'bot_name', 'N/A')}")
                print(f"   Account ID: {getattr(settings, 'account_id', 'N/A')}")
                print(f"   Market Tag: {getattr(settings, 'market_tag', 'N/A')}")
                print(f"   Position Mode: {getattr(settings, 'position_mode', 'N/A')}")
                print(f"   Margin Mode: {getattr(settings, 'margin_mode', 'N/A')}")
                print(f"   Leverage: {getattr(settings, 'leverage', 'N/A')}")
                print(f"   Trade Amount: {getattr(settings, 'trade_amount', 'N/A')}")
                print(f"   Interval: {getattr(settings, 'interval', 'N/A')}")
                print(f"   Chart Style: {getattr(settings, 'chart_style', 'N/A')}")
                print(f"   Order Template: {getattr(settings, 'order_template', 'N/A')}")
                print(f"   Script Parameters: {getattr(settings, 'script_parameters', 'N/A')}")
            else:
                print(f"\n⚠️ No settings found")
            
            # Convert to dictionary format for BacktestManager
            bot_data = {
                'BotId': getattr(bot, 'bot_id', ''),
                'BotName': getattr(bot, 'bot_name', ''),
                'ScriptId': getattr(bot, 'script_id', ''),
                'AccountId': getattr(bot, 'account_id', ''),
                'Market': getattr(bot, 'market', ''),
                'MarketTag': getattr(settings, 'market_tag', '') if settings else '',
                'Leverage': getattr(settings, 'leverage', 0) if settings else 0,
                'PositionMode': getattr(settings, 'position_mode', 0) if settings else 0,
                'MarginMode': getattr(settings, 'margin_mode', 0) if settings else 0,
                'TradeAmount': getattr(settings, 'trade_amount', 0) if settings else 0,
                'Interval': getattr(settings, 'interval', 1) if settings else 1,
                'ChartStyle': getattr(settings, 'chart_style', 300) if settings else 300,
                'OrderTemplate': getattr(settings, 'order_template', 500) if settings else 500,
                'ScriptParameters': getattr(settings, 'script_parameters', {}) if settings else {},
                'IsActive': getattr(bot, 'is_activated', False),
                'Settings': settings
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


def build_backtest_settings_debug(bot_data, script_record):
    """Build and display backtest settings for verification"""
    import json
    
    print(f"\n🔧 Building backtest settings...")
    
    # Extract script parameters from script record
    script_parameters = {}
    if 'Data' in script_record and 'I' in script_record['Data']:
        for param in script_record['Data']['I']:
            if 'K' in param and 'V' in param:
                script_parameters[param['K']] = param['V']
        print(f"   Found {len(script_parameters)} script parameters")
    
    # Build settings JSON using the fixed API function
    settings = api.build_backtest_settings(bot_data, script_record)
    
    print(f"\n📊 Backtest Settings Verification:")
    print(f"   Bot ID: {settings.get('botId', 'N/A')}")
    print(f"   Bot Name: {settings.get('botName', 'N/A')}")
    print(f"   Account ID: {settings.get('accountId', 'N/A')}")
    print(f"   Market Tag: {settings.get('marketTag', 'N/A')}")
    print(f"   Leverage: {settings.get('leverage', 'N/A')}")
    print(f"   Position Mode: {settings.get('positionMode', 'N/A')}")
    print(f"   Margin Mode: {settings.get('marginMode', 'N/A')}")
    print(f"   Interval: {settings.get('interval', 'N/A')}")
    print(f"   Chart Style: {settings.get('chartStyle', 'N/A')}")
    print(f"   Trade Amount: {settings.get('tradeAmount', 'N/A')}")
    print(f"   Order Template: {settings.get('orderTemplate', 'N/A')}")
    print(f"   Script Parameters: {len(settings.get('scriptParameters', {}))} parameters")
    
    return settings


def execute_week_backtest(executor, bot_data, script_record, start_unix, end_unix):
    """Execute week-long backtest"""
    print("🚀 Executing week-long backtest...")
    
    # Generate new backtest ID
    backtest_id = str(uuid.uuid4())
    print(f"📝 Generated backtest ID: {backtest_id}")
    
    # Build settings JSON
    settings = build_backtest_settings_debug(bot_data, script_record)
    
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


def wait_for_backtest_completion(executor, backtest_id, script_id, max_wait_minutes=30):
    """Wait for backtest to complete and get results"""
    print(f"\n⏳ Waiting for backtest completion...")
    print(f"   Backtest ID: {backtest_id}")
    print(f"   Max wait time: {max_wait_minutes} minutes")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        try:
            # Get backtest history
            request = BacktestHistoryRequest(
                script_id=script_id,
                limit=10
            )
            
            result = api.get_backtest_history(executor, request)
            
            if result.get('Success', False) and 'I' in result:
                backtests = result['I']
                
                # Look for our backtest
                for bt in backtests:
                    if bt.get('BID') == backtest_id:
                        print(f"✅ Found backtest in history!")
                        return bt
                
                print(f"⏳ Backtest not yet in history, waiting...")
            else:
                print(f"⚠️ Could not get backtest history")
            
            # Wait 30 seconds before checking again
            time.sleep(30)
            
        except Exception as e:
            print(f"⚠️ Error checking backtest status: {e}")
            time.sleep(30)
    
    print(f"⏰ Timeout waiting for backtest completion")
    return None


def display_backtest_results(backtest_data):
    """Display backtest results"""
    if not backtest_data:
        print("❌ No backtest data to display")
        return
    
    print(f"\n📊 Backtest Results:")
    print(f"   Backtest ID: {backtest_data.get('BID', 'N/A')}")
    print(f"   Script Title: {backtest_data.get('ST', 'N/A')}")
    print(f"   Start Time: {backtest_data.get('BS', 'N/A')}")
    print(f"   End Time: {backtest_data.get('BE', 'N/A')}")
    print(f"   Execution Start: {backtest_data.get('ES', 'N/A')}")
    print(f"   Execution End: {backtest_data.get('EE', 'N/A')}")
    print(f"   Account Tag: {backtest_data.get('AT', 'N/A')}")
    print(f"   Market: {backtest_data.get('ME', 'N/A')}")
    print(f"   Profit: {backtest_data.get('PT', 'N/A')}")
    print(f"   ROI: {backtest_data.get('RT', 'N/A')}")
    print(f"   Is Active: {backtest_data.get('IA', 'N/A')}")
    
    # Parse profit and ROI
    profit_str = backtest_data.get('PT', '')
    roi_str = backtest_data.get('RT', '')
    
    if profit_str and '_' in profit_str:
        profit_value, currency = profit_str.split('_', 1)
        print(f"\n💰 Performance Summary:")
        print(f"   Profit: {profit_value} {currency}")
        print(f"   ROI: {roi_str}%")
        
        # Calculate additional metrics if possible
        try:
            profit_float = float(profit_value)
            roi_float = float(roi_str)
            print(f"   Profit (USD): ${profit_float:.2f}")
            print(f"   ROI: {roi_float:.2f}%")
        except ValueError:
            print(f"   Could not parse profit/ROI values")


def main():
    """Main test function"""
    print("🧪 Week-Long Backtest Execution Test")
    print("🎯 Testing with specific bot: d7a07409f52d44b6a2ee55cdccbd7546")
    print("=" * 70)
    
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
        
        # Get specific bot
        bot_id = "d7a07409f52d44b6a2ee55cdccbd7546"
        bot_data = get_specific_bot(executor, bot_id)
        if not bot_data:
            return
        
        script_id = bot_data.get('ScriptId')
        if not script_id:
            print("❌ Bot has no ScriptId")
            return
        
        # Get script record
        script_record = get_script_record(executor, script_id)
        if not script_record:
            return
        
        # Set up 7-day backtest period
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        start_unix = int(start_time.timestamp())
        end_unix = int(end_time.timestamp())
        
        print(f"\n📅 Backtest period: {start_time} to {end_time}")
        print(f"⏰ Unix timestamps: {start_unix} to {end_unix}")
        print(f"📊 Duration: 7 days")
        
        # Execute week-long backtest
        backtest_id = execute_week_backtest(executor, bot_data, script_record, start_unix, end_unix)
        if not backtest_id:
            return
        
        print(f"\n🎯 Backtest ID: {backtest_id}")
        
        # Wait for completion and get results
        backtest_results = wait_for_backtest_completion(executor, backtest_id, script_id, max_wait_minutes=10)
        
        if backtest_results:
            display_backtest_results(backtest_results)
        else:
            print(f"\n⚠️ Backtest may still be processing. Check back later with ID: {backtest_id}")
        
        print("\n✅ Week-long backtest test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
