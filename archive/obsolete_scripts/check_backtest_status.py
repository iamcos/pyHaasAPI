#!/usr/bin/env python3
"""
Check backtest status script
Use this to check on previously executed backtests
"""

import sys
import os
from dotenv import load_dotenv

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from pyHaasAPI import api
from pyHaasAPI.model import BacktestHistoryRequest


def check_backtest_status(backtest_id, script_id):
    """Check the status of a specific backtest"""
    print(f"🔍 Checking status for backtest: {backtest_id}")
    print(f"📊 Script ID: {script_id}")
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
        
        # Get backtest history
        print(f"\n📋 Getting backtest history...")
        request = BacktestHistoryRequest(
            script_id=script_id,
            limit=20  # Get more backtests to find ours
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
            else:
                print(f"\n⚠️ Backtest {backtest_id} not found in history yet")
                print(f"📋 Recent backtests:")
                for i, bt in enumerate(backtests[:5], 1):
                    bt_id = bt.get('BID', 'Unknown')
                    market = bt.get('ME', 'N/A')
                    profit = bt.get('PT', 'N/A')
                    roi = bt.get('RT', 'N/A')
                    print(f"   {i}. {bt_id[:8]}... - Market: {market} - Profit: {profit} - ROI: {roi}%")
        else:
            print(f"❌ Failed to get backtest history: {result.get('Error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def display_backtest_results(backtest_data):
    """Display backtest results"""
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
            
        except ValueError:
            print(f"   Could not parse profit/ROI values")


def main():
    """Main function"""
    print("🔍 Backtest Status Checker")
    print("=" * 40)
    
    # Tracked backtests
    tracked_backtests = [
        {
            "name": "Week-long backtest (7 days)",
            "backtest_id": "7b0f14c2-47c8-412a-979a-a6bd2e25424d",
            "script_id": "f4a48731bdab4e71a89445c33dfbc052",
            "bot_id": "d7a07409f52d44b6a2ee55cdccbd7546"
        },
        {
            "name": "Previous 1-day backtest",
            "backtest_id": "f75a6168-efbc-46cb-a4f5-4586497cd610", 
            "script_id": "f4a48731bdab4e71a89445c33dfbc052",
            "bot_id": "ad31b193572f4add898853b35d36dfca"
        }
    ]
    
    print("📋 Tracked Backtests:")
    for i, bt in enumerate(tracked_backtests, 1):
        print(f"   {i}. {bt['name']}")
        print(f"      Backtest ID: {bt['backtest_id']}")
        print(f"      Bot ID: {bt['bot_id']}")
        print()
    
    # Check the week-long backtest
    print("🔍 Checking week-long backtest status...")
    check_backtest_status(
        "7b0f14c2-47c8-412a-979a-a6bd2e25424d",
        "f4a48731bdab4e71a89445c33dfbc052"
    )


if __name__ == "__main__":
    main()
