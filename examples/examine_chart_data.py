#!/usr/bin/env python3
"""
Examine Backtest Chart Data

This script retrieves and examines the structure of backtest chart data
to see what information is available (price data, indicators, etc.)
"""

import os
from config import settings
from dotenv import load_dotenv
load_dotenv()

import json
from pyHaasAPI import api


def main():
    """Examine backtest chart data structure"""
    print("📊 Examining Backtest Chart Data Structure...")
    
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
    lab_id = "9539af71-48db-4b13-a583-3169e57d107c"
    backtest_id = "62c413e5-00bf-4dba-8fbb-7ac3faa9aff6"
    
    print(f"📋 Lab ID: {lab_id}")
    print(f"📋 Backtest ID: {backtest_id}")
    
    try:
        # Get chart data
        print("\n📈 Retrieving chart data...")
        chart = api.get_backtest_chart(executor, lab_id, backtest_id)
        
        print(f"✅ Chart data retrieved: {len(str(chart))} characters")
        
        # Try to parse as JSON to see structure
        if isinstance(chart, dict):
            print("\n📊 Chart Data Structure:")
            print(f"   Top-level keys: {list(chart.keys())}")
            
            # Look for specific sections
            for key, value in chart.items():
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
        chart_str = str(chart)
        
        # Check for price data
        if "price" in chart_str.lower() or "close" in chart_str.lower() or "open" in chart_str.lower():
            print("   ✅ Contains price data")
        else:
            print("   ❌ No price data found")
            
        # Check for volume data
        if "volume" in chart_str.lower():
            print("   ✅ Contains volume data")
        else:
            print("   ❌ No volume data found")
            
        # Check for indicators
        if "indicator" in chart_str.lower() or "ma" in chart_str.lower() or "rsi" in chart_str.lower():
            print("   ✅ Contains indicator data")
        else:
            print("   ❌ No indicator data found")
            
        # Check for timestamps
        if "timestamp" in chart_str.lower() or "time" in chart_str.lower():
            print("   ✅ Contains timestamp data")
        else:
            print("   ❌ No timestamp data found")
        
        # Save a sample to file for detailed examination
        print("\n💾 Saving sample data to 'chart_sample.json'...")
        with open('chart_sample.json', 'w') as f:
            json.dump(chart, f, indent=2, default=str)
        print("   ✅ Sample saved for detailed examination")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Place the main execution logic here
    pass 