#!/usr/bin/env python3
"""
Examine Backtest Runtime Data

This script retrieves and examines the structure of backtest runtime data
to see what information is available (positions, orders, metrics, etc.)
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import json
from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest


def main():
    """Examine backtest runtime data structure"""
    print("🔍 Examining Backtest Runtime Data Structure...")
    
    # Initialize and authenticate
    executor = api.RequestsExecutor(
        host="127.0.0.1",
        port=8090,
        state=api.Guest()
    ).authenticate(
        email="garrypotterr@gmail.com",
        password="IQYTCQJIQYTCQJ"
    )
    
    # Use the same lab and backtest from our previous tests
    lab_id = "5a21c24f-5150-4dcd-b61c-595aef146d02"
    backtest_id = "aa03ddd4-3cac-4a8d-8305-a8c192ddf255"
    
    print(f"📋 Lab ID: {lab_id}")
    print(f"📋 Backtest ID: {backtest_id}")
    
    try:
        # Get runtime data
        print("\n⚡ Retrieving runtime data...")
        runtime = api.get_backtest_runtime(executor, lab_id, backtest_id)
        
        print(f"✅ Runtime data retrieved: {len(str(runtime))} characters")
        
        # Try to parse as JSON to see structure
        if isinstance(runtime, dict):
            print("\n📊 Runtime Data Structure:")
            print(f"   Top-level keys: {list(runtime.keys())}")
            
            # Look for specific sections
            for key, value in runtime.items():
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        print(f"   📋 {key}: {len(value)} items")
                        if value and len(value) > 0:
                            print(f"      First item: {type(value[0])} - {str(value[0])[:100]}...")
                    else:
                        print(f"   📋 {key}: {len(value)} keys")
                        print(f"      Keys: {list(value.keys())[:5]}...")
                else:
                    print(f"   📋 {key}: {type(value)} - {str(value)[:100]}...")
        
        # Look for specific data types
        print("\n🔍 Looking for specific data types...")
        runtime_str = str(runtime)
        
        # Check for positions
        if "position" in runtime_str.lower():
            print("   ✅ Contains position data")
        else:
            print("   ❌ No position data found")
            
        # Check for orders
        if "order" in runtime_str.lower():
            print("   ✅ Contains order data")
        else:
            print("   ❌ No order data found")
            
        # Check for trades
        if "trade" in runtime_str.lower():
            print("   ✅ Contains trade data")
        else:
            print("   ❌ No trade data found")
            
        # Check for performance metrics
        if "roi" in runtime_str.lower() or "profit" in runtime_str.lower():
            print("   ✅ Contains performance metrics")
        else:
            print("   ❌ No performance metrics found")
        
        # Save a sample to file for detailed examination
        print("\n💾 Saving sample data to 'runtime_sample.json'...")
        with open('runtime_sample.json', 'w') as f:
            json.dump(runtime, f, indent=2, default=str)
        print("   ✅ Sample saved for detailed examination")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Place the main execution logic here
    pass 