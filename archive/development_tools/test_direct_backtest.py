#!/usr/bin/env python3
"""
Test script for direct backtest execution

This script tests the new direct backtest execution API functions
by executing a 1-day backtest for one of the live bots.
"""

import os
import time
from datetime import datetime, timedelta

from pyHaasAPI import api
from pyHaasAPI.api import RequestsExecutor, Guest
from pyHaasAPI.model import (
    ExecuteBacktestRequest, 
    BacktestHistoryRequest,
    EditBacktestTagRequest,
    ArchiveBacktestRequest
)

def setup_authentication():
    """Setup authentication with HaasOnline API"""
    host = os.getenv('API_HOST', '127.0.0.1')
    port = int(os.getenv('API_PORT', '8090'))
    email = os.getenv('API_EMAIL')
    password = os.getenv('API_PASSWORD')
    
    if not email or not password:
        print("❌ Missing API_EMAIL or API_PASSWORD in environment variables")
        return None
    
    # Create executor and authenticate
    haas_api = RequestsExecutor(host=host, port=port, state=Guest())
    executor = haas_api.authenticate(email, password)
    
    if not executor:
        print("❌ Authentication failed")
        return None
    
    print("✅ Successfully authenticated with HaasOnline API")
    return executor

def get_test_bot():
    """Get a test bot for backtesting"""
    executor = setup_authentication()
    if not executor:
        return None, None
    
    # Get all bots
    bots = api.get_all_bots(executor)
    if not bots:
        print("❌ No bots found")
        return None, None
    
    # Filter for active bots
    live_bots = [bot for bot in bots if hasattr(bot, 'is_activated') and bot.is_activated]
    
    if not live_bots:
        print("❌ No live bots found")
        return None, None
    
    # Use the first live bot
    test_bot = live_bots[0]
    print(f"🎯 Selected test bot: {test_bot.bot_name}")
    print(f"   Bot ID: {test_bot.bot_id}")
    print(f"   Script ID: {test_bot.script_id}")
    print(f"   Market: {test_bot.market}")
    print(f"   Account ID: {test_bot.account_id}")
    print(f"   Live ROI: {test_bot.return_on_investment:.2f}%")
    
    return executor, test_bot

def execute_test_backtest():
    """Execute a 1-day backtest for the test bot using temporary lab"""
    executor, test_bot = get_test_bot()
    if not executor or not test_bot:
        return None
    
    # Calculate 1-day backtest period (yesterday)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    start_unix = int(start_date.timestamp())
    end_unix = int(end_date.timestamp())
    
    print(f"\n🚀 Executing 1-day backtest:")
    print(f"   Start: {start_date} ({start_unix})")
    print(f"   End: {end_date} ({end_unix})")
    
    try:
        # Create a temporary lab for backtesting
        print("\n🏗️ Creating temporary lab for backtesting...")
        
        from pyHaasAPI.model import CloudMarket, CreateLabRequest
        
        # Parse market tag
        market_parts = test_bot.market.split('_')
        if len(market_parts) >= 3:
            exchange_code = market_parts[0]
            primary = market_parts[1]
            secondary = market_parts[2]
        else:
            print(f"❌ Invalid market tag format: {test_bot.market}")
            return None, None
        
        cloud_market = CloudMarket(
            C="",  # category
            PS=exchange_code,  # price_source
            P=primary,  # primary
            S=secondary  # secondary
        )
        
        # Create lab request
        lab_name = f"TEMP_BOT_VALIDATION_{test_bot.bot_id[:8]}"
        req = CreateLabRequest.with_generated_name(
            script_id=test_bot.script_id,
            account_id=test_bot.account_id,
            market=cloud_market,
            exchange_code=exchange_code,
            interval=1,
            default_price_data_style="CandleStick"
        )
        
        lab = api.create_lab(executor, req)
        print(f"✅ Created temporary lab: {lab.lab_id}")
        
        # Execute backtest using the lab
        print("\n⏳ Executing backtest using lab...")
        from pyHaasAPI.model import StartLabExecutionRequest
        
        execution_request = StartLabExecutionRequest(
            lab_id=lab.lab_id,
            start_unix=start_unix,
            end_unix=end_unix,
            send_email=False
        )
        
        result = api.start_lab_execution(executor, execution_request)
        
        print(f"✅ Backtest execution response:")
        print(f"   Success: {result.get('Success', False)}")
        print(f"   Error: {result.get('Error', 'None')}")
        print(f"   Data: {result.get('Data', 'None')}")
        
        if result.get('Success', False):
            print(f"🎯 Lab ID: {lab.lab_id}")
            return executor, lab.lab_id
        else:
            print(f"❌ Backtest execution failed: {result.get('Error', 'Unknown error')}")
            return None, None
            
    except Exception as e:
        print(f"❌ Exception during backtest execution: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None, None

def monitor_backtest(executor, lab_id):
    """Monitor backtest progress using lab execution status"""
    print(f"\n🔍 Monitoring backtest for lab {lab_id}...")
    
    max_wait_time = 300  # 5 minutes
    wait_time = 0
    check_interval = 10  # Check every 10 seconds
    
    while wait_time < max_wait_time:
        try:
            # Get lab execution status
            execution_update = api.get_lab_execution_update(executor, lab_id)
            
            if execution_update:
                status = execution_update.status
                progress = execution_update.progress
                print(f"   Status: {status}, Progress: {progress}% (waiting {wait_time}s)")
                
                if status == 'COMPLETED':
                    print("✅ Backtest completed!")
                    return execution_update
                elif status == 'FAILED':
                    print("❌ Backtest failed!")
                    return execution_update
                elif status in ['RUNNING', 'QUEUED']:
                    print(f"   Still {status.lower()}...")
                else:
                    print(f"   Unknown status: {status}")
            else:
                print(f"   Failed to get execution status...")
            
            time.sleep(check_interval)
            wait_time += check_interval
            
        except Exception as e:
            print(f"   Error monitoring backtest: {e}")
            time.sleep(check_interval)
            wait_time += check_interval
    
    print("⏰ Timeout reached. Backtest may still be running.")
    return None

def get_backtest_results(executor, lab_id):
    """Get backtest results from the lab"""
    print(f"\n📊 Getting backtest results for lab {lab_id}...")
    
    try:
        # Get backtest results from the lab
        from pyHaasAPI.model import GetBacktestResultRequest
        
        request = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=100
        )
        
        result = api.get_backtest_result(executor, request)
        
        if result and hasattr(result, 'data') and result.data:
            backtests = result.data.data if hasattr(result.data, 'data') else []
            if backtests:
                backtest = backtests[0]  # Get the first (and likely only) backtest
                print(f"✅ Found backtest results:")
                print(f"   Backtest ID: {backtest.backtest_id}")
                print(f"   ROI: {backtest.roi:.2f}%")
                print(f"   Win Rate: {backtest.win_rate:.2f}%")
                print(f"   Total Trades: {backtest.total_trades}")
                print(f"   Max Drawdown: {backtest.max_drawdown:.2f}%")
                return backtest
            else:
                print("❌ No backtest results found")
                return None
        else:
            print("❌ Failed to get backtest results")
            return None
            
    except Exception as e:
        print(f"❌ Error getting backtest results: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

def cleanup_temp_lab(executor, lab_id):
    """Clean up the temporary lab"""
    print(f"\n🧹 Cleaning up temporary lab {lab_id}...")
    
    try:
        result = api.delete_lab(executor, lab_id)
        if result.get('Success', False):
            print("✅ Temporary lab deleted successfully")
        else:
            print(f"❌ Failed to delete lab: {result.get('Error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error deleting lab: {e}")

def main():
    """Main test function"""
    print("🧪 Testing Backtest Execution with Temporary Lab")
    print("=" * 50)
    
    # Execute backtest
    executor, lab_id = execute_test_backtest()
    if not executor or not lab_id:
        print("❌ Failed to execute backtest")
        return
    
    # Monitor backtest
    execution_result = monitor_backtest(executor, lab_id)
    if not execution_result:
        print("❌ Failed to monitor backtest")
        cleanup_temp_lab(executor, lab_id)
        return
    
    # Get backtest results
    backtest_results = get_backtest_results(executor, lab_id)
    if not backtest_results:
        print("❌ Failed to get backtest results")
        cleanup_temp_lab(executor, lab_id)
        return
    
    # Display results
    print(f"\n📊 Final Backtest Results:")
    print(f"   Backtest ID: {backtest_results.backtest_id}")
    print(f"   ROI: {backtest_results.roi:.2f}%")
    print(f"   Win Rate: {backtest_results.win_rate:.2f}%")
    print(f"   Total Trades: {backtest_results.total_trades}")
    print(f"   Max Drawdown: {backtest_results.max_drawdown:.2f}%")
    
    # Clean up temporary lab
    cleanup_temp_lab(executor, lab_id)
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    main()
