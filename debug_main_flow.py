#!/usr/bin/env python3
"""
Debug script that exactly mimics the main financial_analytics.py flow
"""
import json
import sys
import os
from datetime import datetime
from typing import Optional

# Add the pyHaasAPI module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pyHaasAPI'))

from pyHaasAPI.api import get_backtest_runtime
from pyHaasAPI.backtest_object import BacktestObject
from pyHaasAPI.model import BacktestRuntimeData
from pyHaasAPI.executor import SyncExecutor, Authenticated

def debug_main_flow():
    # The specific backtest ID with trading data
    backtest_id = "0e3a5382-3de3-4be4-935e-9511bd3d7f66"
    lab_id = "6e04e13c-1a12-4759-b037-b6997f830edf"

    print(f"🔍 Debugging main flow for backtest: {backtest_id}")
    print("=" * 60)

    # Step 1: Get raw API response (exactly like main script)
    print("\n📡 Step 1: Getting raw API response...")
    try:
        # Create authenticated executor (exactly like main script)
        executor = SyncExecutor()
        auth_executor = Authenticated(executor)

        # Get the backtest runtime data (exactly like main script)
        raw_response = get_backtest_runtime(auth_executor, lab_id, backtest_id)
        print(f"✅ Got raw response, Success: {raw_response.Success}")

        if not raw_response.Success:
            print(f"❌ API call failed: {raw_response.Error}")
            return

        # Step 2: Parse with BacktestRuntimeData (exactly like main script)
        print("\n🏗️ Step 2: Parsing with BacktestRuntimeData...")
        try:
            full_runtime_data = BacktestRuntimeData(**raw_response.Data)
            print("✅ Successfully parsed with BacktestRuntimeData")

            # Print key data to verify
            print(f"Reports keys: {list(full_runtime_data.Reports.keys())}")

            # Step 3: Create BacktestObject (exactly like main script)
            print("\n🎯 Step 3: Creating BacktestObject...")
            backtest_obj = BacktestObject(
                backtest_id=backtest_id,
                lab_id=lab_id,
                full_runtime_data=full_runtime_data
            )

            print("✅ BacktestObject created successfully")

            # Check if runtime data was loaded
            if hasattr(backtest_obj, 'runtime') and backtest_obj.runtime:
                runtime = backtest_obj.runtime
                print("✅ Runtime data loaded:")
                print(f"   Total trades: {runtime.total_trades}")
                print(f"   Winning trades: {runtime.winning_trades}")
                print(f"   Total profit: {runtime.total_profit}")
                print(f"   Win rate: {runtime.win_rate}")
            else:
                print("❌ No runtime data loaded!")

            # Step 4: Simulate the analysis processing
            print("\n📊 Step 4: Simulating analysis processing...")

            # This is exactly what happens in analyze_single_backtest
            losing_trades = runtime.total_trades - runtime.winning_trades
            avg_trade_profit = runtime.total_profit / runtime.total_trades if runtime.total_trades > 0 else 0

            print("✅ Analysis calculations:")
            print(f"   Losing trades: {losing_trades}")
            print(f"   Avg trade profit: {avg_trade_profit}")

            # Save the backtest object for inspection
            with open('debug_backtest_object.json', 'w') as f:
                json.dump({
                    'backtest_id': backtest_obj.backtest_id,
                    'lab_id': backtest_obj.lab_id,
                    'has_runtime': hasattr(backtest_obj, 'runtime') and backtest_obj.runtime is not None,
                    'runtime_data': backtest_obj.runtime.__dict__ if hasattr(backtest_obj, 'runtime') and backtest_obj.runtime else None
                }, f, indent=2, default=str)

            print("💾 BacktestObject saved to debug_backtest_object.json")

        except Exception as e:
            print(f"❌ Error parsing data: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Error in main flow: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_main_flow()

