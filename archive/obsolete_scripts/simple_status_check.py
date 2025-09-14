#!/usr/bin/env python3
"""
Simple Backtest Status Checker
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


def check_backtest_simple(backtest_id, script_id):
    """Simple backtest status check using only backtest history"""
    print(f"🔍 Checking backtest: {backtest_id}")
    print(f"📊 Script ID: {script_id}")
    print("=" * 50)
    
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
            limit=50  # Get more backtests
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
                display_results(our_backtest)
                return our_backtest
            else:
                print(f"\n⚠️ Backtest {backtest_id} not found in history yet")
                print(f"📋 Recent backtests:")
                for i, bt in enumerate(backtests[:10], 1):
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


def display_results(backtest_data):
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
        
        try:
            profit_float = float(profit_value)
            roi_float = float(roi_str)
            print(f"   Profit (USD): ${profit_float:.2f}")
            print(f"   ROI: {roi_float:.2f}%")
            
            # Calculate execution time
            start_time = backtest_data.get('ES', 0)
            end_time = backtest_data.get('EE', 0)
            if start_time and end_time:
                execution_seconds = end_time - start_time
                print(f"   ⏱️ Execution Time: {execution_seconds} seconds")
            
            print(f"\n📈 Analysis:")
            print(f"   ✅ Backtest completed successfully")
            print(f"   📊 Performance: {'Positive' if profit_float > 0 else 'Negative'}")
            print(f"   🎯 ROI: {'Good' if roi_float > 5 else 'Poor'} performance")
            
        except ValueError:
            print(f"   Could not parse profit/ROI values")


def main():
    """Main function"""
    print("🔍 Simple Backtest Status Checker")
    print("=" * 40)
    
    # Check the week-long backtest
    result = check_backtest_simple(
        "7b0f14c2-47c8-412a-979a-a6bd2e25424d",
        "f4a48731bdab4e71a89445c33dfbc052"
    )
    
    if result:
        print("\n✅ Backtest is ready!")
    else:
        print("\n⏳ Backtest may still be processing...")


if __name__ == "__main__":
    main()
