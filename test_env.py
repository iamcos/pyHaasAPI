#!/usr/bin/env python3
"""
Test to examine nested backtest data structure
"""

import os
import sys
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the API
from pyHaasAPI import api
from dotenv import load_dotenv

def examine_nested_backtest_data():
    """Examine the nested data in backtest results"""
    print("🔍 Examining Nested Backtest Data")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        print("❌ Missing credentials")
        return

    # Authenticate
    print("🔐 Authenticating...")
    executor = api.RequestsExecutor(
        host=api_host,
        port=api_port,
        state=api.Guest()
    ).authenticate(
        email=api_email,
        password=api_password
    )
    print("✅ Authentication successful!")

    # Use the lab with backtests
    lab_id = "272bbb66-f2b3-4eae-8c32-714747dcb827"

    print(f"\n🏢 Testing with lab: {lab_id}")

    # Get backtest results
    print("\n📊 Getting backtest results...")
    try:
        backtest_results = api.get_backtest_result(
            executor,
            api.GetBacktestResultRequest(lab_id=lab_id, next_page_id=0, page_lenght=1)
        )

        if hasattr(backtest_results, 'items') and backtest_results.items:
            backtests = backtest_results.items
            print(f"✅ Found {len(backtests)} backtests")

            # Examine first backtest nested data
            if backtests:
                bt = backtests[0]
                print(f"\n🔍 First backtest ID: {bt.backtest_id}")

                # Check runtime data
                if hasattr(bt, 'runtime') and bt.runtime:
                    print(f"\n📈 Runtime data (first 1000 chars):")
                    runtime_str = str(bt.runtime)[:1000]
                    print(f"   {runtime_str}")
                    if len(str(bt.runtime)) > 1000:
                        print(f"   ... ({len(str(bt.runtime)) - 1000} more chars)")

                    # Try to parse as dict if it's JSON
                    try:
                        if isinstance(bt.runtime, str):
                            runtime_dict = json.loads(bt.runtime)
                            print(f"\n📈 Runtime as dict keys: {list(runtime_dict.keys())}")
                    except:
                        pass
                else:
                    print(f"\n📈 Runtime: None or empty")

                # Check summary data
                if hasattr(bt, 'summary') and bt.summary:
                    print(f"\n📊 Summary data (first 1000 chars):")
                    summary_str = str(bt.summary)[:1000]
                    print(f"   {summary_str}")
                    if len(str(bt.summary)) > 1000:
                        print(f"   ... ({len(str(bt.summary)) - 1000} more chars)")

                    # Try to parse as dict if it's JSON
                    try:
                        if isinstance(bt.summary, str):
                            summary_dict = json.loads(bt.summary)
                            print(f"\n📊 Summary as dict keys: {list(summary_dict.keys())}")
                    except:
                        pass
                else:
                    print(f"\n📊 Summary: None or empty")

                # Check settings data
                if hasattr(bt, 'settings') and bt.settings:
                    print(f"\n⚙️ Settings data (first 500 chars):")
                    settings_str = str(bt.settings)[:500]
                    print(f"   {settings_str}")
                    if len(str(bt.settings)) > 500:
                        print(f"   ... ({len(str(bt.settings)) - 500} more chars)")
                else:
                    print(f"\n⚙️ Settings: None or empty")

        else:
            print("⚠️ No backtest results found")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("🎉 Nested data examination complete!")

if __name__ == '__main__':
    examine_nested_backtest_data()
