#!/usr/bin/env python3
"""
Debug script that EXACTLY mimics the main financial_analytics.py flow
"""
import json
import sys
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Add the pyHaasAPI module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pyHaasAPI'))

from pyHaasAPI import api
from pyHaasAPI.backtest_object import BacktestObject
from pyHaasAPI.model import GetBacktestResultRequest

def debug_exact_main_flow():
    # The specific backtest ID with trading data
    backtest_id = "0e3a5382-3de3-4be4-935e-9511bd3d7f66"
    lab_id = "6e04e13c-1a12-4759-b037-b6997f830edf"

    print(f"🔍 Debugging EXACT main flow for backtest: {backtest_id}")
    print("=" * 60)

    # Load environment variables (exactly like main script)
    load_dotenv()

    # Step 1: Create executor (exactly like main script)
    print("\n📡 Step 1: Creating executor...")
    try:
        # This is EXACTLY how the main script creates the executor (lines 379-386)
        executor = api.RequestsExecutor(
            host="127.0.0.1",
            port=8090,
            state=api.Guest()
        ).authenticate(
            email=os.getenv("API_EMAIL"),
            password=os.getenv("API_PASSWORD")
        )
        print("✅ Executor created successfully")

        # Step 2: Create BacktestObject (EXACTLY like main script line 82)
        print("\n🏗️ Step 2: Creating BacktestObject...")
        bt_object = BacktestObject(executor, lab_id, backtest_id)
        print("✅ BacktestObject created")

        # Step 3: Check runtime data (exactly like main script lines 84-86)
        print("\n🎯 Step 3: Checking runtime data...")
        if not bt_object.runtime or not bt_object.metadata:
            print(f"❌ No runtime data for backtest {backtest_id}")
            print(f"   bt_object.runtime: {bt_object.runtime}")
            print(f"   bt_object.metadata: {bt_object.metadata}")

            # Debug: Let's see what attributes the object has
            print(f"   Available attributes: {dir(bt_object)}")

            # Try to access runtime directly to see what's happening
            if hasattr(bt_object, '_load_core_data'):
                print("   Attempting to load core data manually...")
                try:
                    bt_object._load_core_data()
                    print(f"   After manual load - runtime: {bt_object.runtime}")
                    print(f"   After manual load - metadata: {bt_object.metadata}")
                except Exception as e:
                    print(f"   Error during manual load: {e}")
                    import traceback
                    traceback.print_exc()

            return
        else:
            print("✅ Runtime and metadata exist")
            runtime = bt_object.runtime
            metadata = bt_object.metadata

            # Step 4: Extract data (exactly like main script)
            print("\n📊 Step 4: Extracting data...")
            print(f"   Total trades: {runtime.total_trades}")
            print(f"   Winning trades: {runtime.winning_trades}")
            print(f"   Total profit: {runtime.total_profit}")
            print(f"   Win rate: {runtime.win_rate}")

            losing_trades = runtime.total_trades - runtime.winning_trades
            avg_trade_profit = runtime.total_profit / runtime.total_trades if runtime.total_trades > 0 else 0

            print(f"   Losing trades: {losing_trades}")
            print(f"   Avg trade profit: {avg_trade_profit}")

            # Save detailed debug info
            debug_info = {
                'backtest_id': backtest_id,
                'lab_id': lab_id,
                'has_runtime': bt_object.runtime is not None,
                'has_metadata': bt_object.metadata is not None,
                'runtime_data': {
                    'total_trades': runtime.total_trades,
                    'winning_trades': runtime.winning_trades,
                    'losing_trades': losing_trades,
                    'total_profit': runtime.total_profit,
                    'win_rate': runtime.win_rate,
                    'max_drawdown': runtime.max_drawdown,
                    'sharpe_ratio': runtime.sharpe_ratio,
                    'profit_factor': runtime.profit_factor,
                    'raw_data_keys': list(runtime.raw_data.keys()) if runtime.raw_data else []
                } if bt_object.runtime else None,
                'metadata_data': {
                    'script_name': metadata.script_name if hasattr(metadata, 'script_name') else 'unknown',
                    'account_id': metadata.account_id if hasattr(metadata, 'account_id') else 'unknown',
                    'market': metadata.market if hasattr(metadata, 'market') else 'unknown',
                    'start_time': str(metadata.start_time) if hasattr(metadata, 'start_time') else 'unknown',
                    'end_time': str(metadata.end_time) if hasattr(metadata, 'end_time') else 'unknown'
                } if bt_object.metadata else None
            }

            with open('debug_exact_flow.json', 'w') as f:
                json.dump(debug_info, f, indent=2, default=str)

            print("💾 Debug info saved to debug_exact_flow.json")

    except Exception as e:
        print(f"❌ Error in main flow: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_exact_main_flow()
