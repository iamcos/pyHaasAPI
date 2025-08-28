#!/usr/bin/env python3
"""
Debug script to trace data processing for a single backtest
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

def debug_single_backtest():
    # The specific backtest ID with trading data
    backtest_id = "0e3a5382-3de3-4be4-935e-9511bd3d7f66"
    lab_id = "6e04e13c-1a12-4759-b037-b6997f830edf"

    print(f"🔍 Debugging backtest: {backtest_id}")
    print("=" * 60)

    # Step 1: Get raw API response
    print("\n📡 Step 1: Getting raw API response...")
    try:
        # Create authenticated executor (you'll need to replace with actual credentials)
        executor = SyncExecutor[Authenticated]()

        raw_response = get_backtest_runtime(executor, lab_id, backtest_id)
        print("✅ Raw API response received")
        print(f"Response keys: {list(raw_response.keys())}")

        # Save raw response for inspection
        with open('debug_raw_response.json', 'w') as f:
            json.dump(raw_response, f, indent=2)
        print("💾 Raw response saved to debug_raw_response.json")

    except Exception as e:
        print(f"❌ Failed to get API response: {e}")
        return

    # Step 2: Parse with Pydantic model
    print("\n🔧 Step 2: Parsing with BacktestRuntimeData model...")
    try:
        if 'Data' in raw_response:
            data_content = raw_response['Data']
            print(f"Data content keys: {list(data_content.keys())}")

            # Check if Reports exist
            if 'Reports' in data_content:
                print(f"Reports keys: {list(data_content['Reports'].keys())}")
                for report_key, report_data in data_content['Reports'].items():
                    print(f"Report {report_key}: {type(report_data)}")
                    if isinstance(report_data, dict):
                        print(f"  Report data keys: {list(report_data.keys())}")
                        # Check for trading data
                        if 'T' in report_data:
                            print(f"  Trading data (T): {report_data['T']}")
                        if 'P' in report_data:
                            print(f"  Position data (P): {report_data['P']}")
                        if 'O' in report_data:
                            print(f"  Orders data (O): {report_data['O']}")
            else:
                print("❌ No Reports found in data_content")

            # Parse with Pydantic
            runtime_data = BacktestRuntimeData(**data_content)
            print("✅ Successfully parsed with BacktestRuntimeData")

            # Check parsed data
            print(f"Reports in parsed data: {len(runtime_data.Reports) if runtime_data.Reports else 0}")

            # Save parsed data
            with open('debug_parsed_data.json', 'w') as f:
                json.dump(runtime_data.model_dump(), f, indent=2)
            print("💾 Parsed data saved to debug_parsed_data.json")

        else:
            print("❌ No 'Data' key in response")
            return

    except Exception as e:
        print(f"❌ Failed to parse data: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Create BacktestObject
    print("\n🏗️ Step 3: Creating BacktestObject...")
    try:
        backtest_obj = BacktestObject(backtest_id, lab_id)
        backtest_obj._load_core_data(runtime_data)
        print("✅ BacktestObject created and core data loaded")

        # Check the backtest object's data
        print(f"Script name: {backtest_obj.script_name}")
        print(f"Account ID: {backtest_obj.account_id}")
        print(f"Market: {backtest_obj.market_tag}")
        print(f"Total trades: {backtest_obj.total_trades}")
        print(f"Winning trades: {backtest_obj.winning_trades}")
        print(f"Losing trades: {backtest_obj.losing_trades}")
        print(f"Total profit: {backtest_obj.total_profit}")
        print(f"ROI: {backtest_obj.roi_percentage}%")

        # Save backtest object data
        with open('debug_backtest_object.json', 'w') as f:
            json.dump({
                'script_name': backtest_obj.script_name,
                'account_id': backtest_obj.account_id,
                'market_tag': backtest_obj.market_tag,
                'total_trades': backtest_obj.total_trades,
                'winning_trades': backtest_obj.winning_trades,
                'losing_trades': backtest_obj.losing_trades,
                'total_profit': backtest_obj.total_profit,
                'roi_percentage': backtest_obj.roi_percentage,
                'start_time': backtest_obj.start_time.isoformat() if backtest_obj.start_time else None,
                'end_time': backtest_obj.end_time.isoformat() if backtest_obj.end_time else None,
            }, f, indent=2)
        print("💾 BacktestObject data saved to debug_backtest_object.json")

    except Exception as e:
        print(f"❌ Failed to create BacktestObject: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Analyze with financial analytics
    print("\n📊 Step 4: Running financial analysis...")
    try:
        # Import and run analysis
        from financial_analytics import analyze_single_backtest

        analysis_result = analyze_single_backtest(backtest_obj)

        print("✅ Financial analysis completed")
        print(f"Analysis result: {analysis_result}")

        # Save analysis result
        with open('debug_analysis_result.json', 'w') as f:
            json.dump(analysis_result, f, indent=2)
        print("💾 Analysis result saved to debug_analysis_result.json")

    except Exception as e:
        print(f"❌ Failed financial analysis: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n🎯 Debug complete! Check the debug_*.json files for detailed data.")

if __name__ == "__main__":
    debug_single_backtest()

