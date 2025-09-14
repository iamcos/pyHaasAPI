#!/usr/bin/env python3
"""
Debug script to fix bot configuration for backtest execution
This will help us understand how to properly configure bots for backtesting
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

from pyHaasAPI import api
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
            
            # Convert to dictionary format for testing
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


def build_backtest_settings_fixed(bot_data, script_record):
    """
    Build the settings JSON for EXECUTE_BACKTEST with proper field mapping
    """
    import json
    
    print(f"\n🔧 Building backtest settings...")
    print(f"   Bot Data Keys: {list(bot_data.keys())}")
    
    # Extract script parameters from script record
    script_parameters = {}
    if 'Data' in script_record and 'I' in script_record['Data']:
        for param in script_record['Data']['I']:
            if 'K' in param and 'V' in param:
                script_parameters[param['K']] = param['V']
        print(f"   Found {len(script_parameters)} script parameters")
    
    # Build settings JSON with proper field names
    settings = {
        "botId": bot_data.get('BotId', ''),
        "botName": bot_data.get('BotName', ''),
        "accountId": bot_data.get('AccountId', ''),
        "marketTag": bot_data.get('MarketTag', '') or bot_data.get('Market', ''),
        "leverage": bot_data.get('Leverage', 0),
        "positionMode": bot_data.get('PositionMode', 0),
        "marginMode": bot_data.get('MarginMode', 0),
        "interval": bot_data.get('Interval', 1),
        "chartStyle": bot_data.get('ChartStyle', 300),
        "tradeAmount": bot_data.get('TradeAmount', 0.005),
        "orderTemplate": bot_data.get('OrderTemplate', 500),
        "scriptParameters": script_parameters
    }
    
    print(f"   Built settings with:")
    for key, value in settings.items():
        if key != 'scriptParameters':
            print(f"     {key}: {value}")
        else:
            print(f"     {key}: {len(value)} parameters")
    
    return settings


def execute_direct_backtest_fixed(executor, bot_data, script_record, start_unix, end_unix):
    """Execute direct backtest with fixed settings"""
    print("🚀 Executing direct backtest with fixed configuration...")
    
    # Generate new backtest ID
    backtest_id = str(uuid.uuid4())
    print(f"📝 Generated backtest ID: {backtest_id}")
    
    # Build settings JSON with fixed function
    settings = build_backtest_settings_fixed(bot_data, script_record)
    
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


def main():
    """Main debug function"""
    print("🔧 Debug: Bot Configuration for Backtest Execution")
    print("🎯 Testing with specific bot: ad31b193572f4add898853b35d36dfca")
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
        
        # Get specific bot with detailed info
        bot_id = "ad31b193572f4add898853b35d36dfca"
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
        
        # Set up 1-day backtest period
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        start_unix = int(start_time.timestamp())
        end_unix = int(end_time.timestamp())
        
        print(f"\n📅 Backtest period: {start_time} to {end_time}")
        print(f"⏰ Unix timestamps: {start_unix} to {end_unix}")
        
        # Execute direct backtest with fixed configuration
        backtest_id = execute_direct_backtest_fixed(executor, bot_data, script_record, start_unix, end_unix)
        if not backtest_id:
            return
        
        print(f"\n🎯 Backtest ID: {backtest_id}")
        print("✅ Debug test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
