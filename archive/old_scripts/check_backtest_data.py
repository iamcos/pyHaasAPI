#!/usr/bin/env python3
"""
Quick script to check what backtest data is actually available
"""
import pyHaasAPI.api as api
from dotenv import load_dotenv
import os
import json

def main():
    load_dotenv()
    # Create API connection
    haas_api = api.RequestsExecutor(
        host=os.getenv('API_HOST', '127.0.0.1'),
        port=int(os.getenv('API_PORT', 8090)),
        state=api.Guest()
    )

    # Authenticate
    api_instance = haas_api.authenticate(
        os.getenv('API_EMAIL'),
        os.getenv('API_PASSWORD')
    )

    # Get a specific backtest with full data
    print("🔍 Fetching backtest data...")
    from pyHaasAPI.model import GetBacktestResultRequest
    
    request = GetBacktestResultRequest(
        lab_id='e4616b35-8065-4095-966b-546de68fd493',
        next_page_id=0,
        page_lenght=1
    )
    
    response = api.get_backtest_result(api_instance, request)
    if not response or not hasattr(response, 'items'):
        print("❌ No response or items from lab")
        return
    
    backtests = response.items
    
    if not backtests:
        print("❌ No backtests found")
        return
    
    backtest = backtests[0]
    print(f"✅ Found backtest: {backtest.backtest_id}")
    print()
    
    # Check summary data
    print("=== SUMMARY DATA ===")
    if hasattr(backtest, 'summary') and backtest.summary:
        summary = backtest.summary
        print(f"Summary type: {type(summary)}")
        print(f"Summary dict: {summary.model_dump()}")
        print()
        
        # Check nested objects
        for attr in ['Trades', 'Orders', 'Positions', 'CustomReport']:
            if hasattr(summary, attr):
                value = getattr(summary, attr)
                print(f"{attr}: {type(value)} = {value}")
        print()
    
    # Check runtime data
    print("=== RUNTIME DATA ===")
    if hasattr(backtest, 'runtime') and backtest.runtime:
        runtime = backtest.runtime
        print(f"Runtime type: {type(runtime)}")
        print(f"Runtime dict: {runtime.model_dump()}")
        print()
    
    # Try to get full backtest data
    print("=== FULL BACKTEST DATA ===")
    try:
        full_data = api_instance.get_backtest_result(backtest.backtest_id)
        print(f"Full data type: {type(full_data)}")
        if hasattr(full_data, 'model_dump'):
            full_dict = full_data.model_dump()
            print(f"Full data keys: {list(full_dict.keys())}")
            
            # Look for performance metrics
            for key in ['summary', 'trades', 'orders', 'positions', 'performance']:
                if key in full_dict and full_dict[key]:
                    print(f"{key}: {full_dict[key]}")
        else:
            print(f"Full data: {full_data}")
    except Exception as e:
        print(f"Error getting full backtest data: {e}")
    
    # Check if we can get runtime data
    print("\n=== RUNTIME DATA CHECK ===")
    try:
        runtime_data = api_instance.get_full_backtest_runtime_data(backtest.backtest_id)
        print(f"Runtime data type: {type(runtime_data)}")
        if hasattr(runtime_data, 'model_dump'):
            runtime_dict = runtime_data.model_dump()
            print(f"Runtime data keys: {list(runtime_dict.keys())}")
        else:
            print(f"Runtime data: {runtime_data}")
    except Exception as e:
        print(f"Error getting runtime data: {e}")

if __name__ == "__main__":
    main()
