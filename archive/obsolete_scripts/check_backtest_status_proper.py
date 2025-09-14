#!/usr/bin/env python3
"""
Proper Backtest Status Checker using History Intelligence
"""

import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from pyHaasAPI import api, BacktestManager
from pyHaasAPI.model import BacktestHistoryRequest


def check_backtest_status_proper(backtest_id, script_id, market_tag=None):
    """Check backtest status using proper history tracking"""
    print(f"🔍 Checking backtest status using history intelligence")
    print(f"   Backtest ID: {backtest_id}")
    print(f"   Script ID: {script_id}")
    if market_tag:
        print(f"   Market: {market_tag}")
    print("=" * 60)
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        print("✅ Authentication successful")
        
        # Check history status if market is provided
        if market_tag:
            print(f"\n📊 Checking history status for market: {market_tag}")
            try:
                history_status = api.get_history_status(executor)
                market_info = history_status.get(market_tag)
                if market_info:
                    status = market_info.get("Status", "Unknown")
                    print(f"   Market Status: {status}")
                    if status == 3:
                        print("   ✅ Market is fully synced")
                    else:
                        print(f"   ⏳ Market sync status: {status} (3 = fully synced)")
                else:
                    print(f"   ⚠️ No history status found for market {market_tag}")
            except Exception as e:
                print(f"   ⚠️ Could not get history status: {e}")
        
        # Get backtest history
        print(f"\n📋 Getting backtest history...")
        request = BacktestHistoryRequest(
            script_id=script_id,
            limit=20
        )
        
        result = api.get_backtest_history(executor, request)
        
        if result.get('Success', False) and 'I' in result:
            backtests = result['I']
            print(f"✅ Found {len(backtests)} backtests in history")
            
            # Look for our specific backtest
            our_backtest = None
            for bt in backtests:
                if bt.get('BID') == backtest_id:
                    our_backtest = bt
                    break
            
            if our_backtest:
                print(f"\n🎯 Found our backtest!")
                display_backtest_results(our_backtest)
                return our_backtest
            else:
                print(f"\n⚠️ Backtest {backtest_id} not found in history yet")
                print(f"📋 Recent backtests:")
                for i, bt in enumerate(backtests[:5], 1):
                    bt_id = bt.get('BID', 'Unknown')
                    market = bt.get('ME', 'N/A')
                    profit = bt.get('PT', 'N/A')
                    roi = bt.get('RT', 'N/A')
                    print(f"   {i}. {bt_id[:8]}... - Market: {market} - Profit: {profit} - ROI: {roi}%")
                return None
        else:
            print(f"❌ Failed to get backtest history: {result.get('Error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_backtest_results(backtest_data):
    """Display comprehensive backtest results"""
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
            
            # Calculate win rate if we have trade data
            # Note: We'd need additional API calls to get detailed trade data
            print(f"\n📈 Additional Analysis:")
            print(f"   ✅ Backtest completed successfully")
            print(f"   📊 Performance: {'Positive' if profit_float > 0 else 'Negative'}")
            print(f"   🎯 ROI: {'Good' if roi_float > 5 else 'Poor'} performance")
            
            # Calculate execution time
            start_time = backtest_data.get('ES', 0)
            end_time = backtest_data.get('EE', 0)
            if start_time and end_time:
                execution_seconds = end_time - start_time
                print(f"   ⏱️ Execution Time: {execution_seconds} seconds")
            
        except ValueError:
            print(f"   Could not parse profit/ROI values")


def wait_for_backtest_completion(backtest_id, script_id, market_tag=None, max_wait_minutes=30):
    """Wait for backtest to complete with proper status checking"""
    print(f"⏳ Waiting for backtest completion...")
    print(f"   Backtest ID: {backtest_id}")
    print(f"   Max wait time: {max_wait_minutes} minutes")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        result = check_backtest_status_proper(backtest_id, script_id, market_tag)
        if result:
            return result
        
        print(f"⏳ Backtest not ready yet, waiting 30 seconds...")
        time.sleep(30)
    
    print(f"⏰ Timeout waiting for backtest completion")
    return None


def main():
    """Main function"""
    print("🔍 Proper Backtest Status Checker")
    print("=" * 50)
    
    # Tracked backtests with market information
    tracked_backtests = [
        {
            "name": "Week-long backtest (7 days)",
            "backtest_id": "7b0f14c2-47c8-412a-979a-a6bd2e25424d",
            "script_id": "f4a48731bdab4e71a89445c33dfbc052",
            "bot_id": "d7a07409f52d44b6a2ee55cdccbd7546",
            "market_tag": "BINANCEFUTURES_BNB_USDT_PERPETUAL"
        },
        {
            "name": "Previous 1-day backtest",
            "backtest_id": "f75a6168-efbc-46cb-a4f5-4586497cd610", 
            "script_id": "f4a48731bdab4e71a89445c33dfbc052",
            "bot_id": "ad31b193572f4add898853b35d36dfca",
            "market_tag": "BINANCEFUTURES_BNB_USDT_PERPETUAL"
        }
    ]
    
    print("📋 Tracked Backtests:")
    for i, bt in enumerate(tracked_backtests, 1):
        print(f"   {i}. {bt['name']}")
        print(f"      Backtest ID: {bt['backtest_id']}")
        print(f"      Bot ID: {bt['bot_id']}")
        print(f"      Market: {bt['market_tag']}")
        print()
    
    # Check the week-long backtest
    print("🔍 Checking week-long backtest status...")
    result = check_backtest_status_proper(
        "7b0f14c2-47c8-412a-979a-a6bd2e25424d",
        "f4a48731bdab4e71a89445c33dfbc052",
        "BINANCEFUTURES_BNB_USDT_PERPETUAL"
    )
    
    if result:
        print("\n✅ Backtest is ready!")
    else:
        print("\n⏳ Backtest may still be processing...")


if __name__ == "__main__":
    main()
