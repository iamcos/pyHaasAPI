#!/usr/bin/env python3
"""
Debug script to see what data is available in backtest history
"""

import os
import json
from dotenv import load_dotenv
from pyHaasAPI import api
from pyHaasAPI.model import BacktestHistoryRequest

def debug_backtest_data():
    """Debug what data is available in backtest history"""
    
    # Load environment variables
    load_dotenv()
    
    # Create API connection
    haas_api = api.RequestsExecutor(
        host='127.0.0.1',
        port=8090,
        state=api.Guest()
    )
    
    print("🔍 Debugging Backtest Data")
    print("=" * 50)
    
    try:
        # Authenticate
        print("🔐 Authenticating...")
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        print("✅ Authentication successful")
        
        # Get backtest history
        print("\n📋 Getting backtest history...")
        history_request = BacktestHistoryRequest(
            offset=0,
            limit=10
        )
        
        history = api.get_backtest_history(executor, history_request)
        
        if not history or 'I' not in history:
            print("❌ No backtest history found")
            return
        
        backtests = history['I']
        print(f"📊 Found {len(backtests)} backtests")
        
        # Find our specific backtest
        target_backtest_id = "7b0f14c2-47c8-412a-979a-a6bd2e25424d"
        our_backtest = None
        
        for bt in backtests:
            if bt.get('BID') == target_backtest_id:
                our_backtest = bt
                break
        
        if not our_backtest:
            print(f"❌ Backtest {target_backtest_id} not found")
            return
        
        print(f"✅ Found our backtest: {target_backtest_id}")
        print(f"\n📊 RAW BACKTEST DATA:")
        print(json.dumps(our_backtest, indent=2))
        
        print(f"\n📊 AVAILABLE FIELDS:")
        for key, value in our_backtest.items():
            print(f"  {key}: {value} ({type(value).__name__})")
        
        # Try to calculate max drawdown from available data
        print(f"\n🔍 ANALYZING AVAILABLE DATA:")
        
        # Check if we have any performance metrics
        roi_str = our_backtest.get('RT', '0')
        profit = our_backtest.get('PT', '0')
        
        # Convert ROI to float
        try:
            roi = float(roi_str)
        except (ValueError, TypeError):
            roi = 0.0
        
        print(f"ROI: {roi} (from string: {roi_str})")
        print(f"Profit: {profit}")
        
        # Try to estimate max drawdown based on ROI
        # High ROI with low volatility = low drawdown
        # High ROI with high volatility = high drawdown
        if roi > 0:
            # Rough estimation: if ROI is very high (>50%), assume some volatility
            if roi > 100:
                estimated_max_drawdown = min(30, roi / 10)  # Cap at 30%
            elif roi > 50:
                estimated_max_drawdown = min(20, roi / 15)  # Cap at 20%
            else:
                estimated_max_drawdown = min(15, roi / 20)  # Cap at 15%
        else:
            estimated_max_drawdown = 50  # High drawdown for negative ROI
        
        print(f"Estimated Max Drawdown: {estimated_max_drawdown:.2f}%")
        
        # Try to get more detailed data using different API calls
        print(f"\n🔄 Trying to get more detailed data...")
        
        # Try to get backtest runtime data (might work for some backtests)
        try:
            # This might fail for direct backtests, but let's try
            runtime_data = api.get_backtest_runtime(executor, "direct_backtest", target_backtest_id)
            if runtime_data:
                print("✅ Got runtime data!")
                print(json.dumps(runtime_data, indent=2))
            else:
                print("❌ No runtime data available")
        except Exception as e:
            print(f"❌ Runtime data not available: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_backtest_data()
