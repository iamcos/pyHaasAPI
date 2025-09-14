#!/usr/bin/env python3
"""
Debug script to examine nested Reports structure
"""

from pyHaasAPI.analysis.cache import UnifiedCacheManager
import json

def main():
    cache = UnifiedCacheManager()
    
    # List all cached files
    import os
    cache_dir = "unified_cache/backtests"
    if os.path.exists(cache_dir):
        files = os.listdir(cache_dir)
        
        # Examine the first file
        filename = files[0]
        print(f"\n=== FILE: {filename} ===")
        
        # Extract lab_id and backtest_id from filename
        if '_' in filename:
            parts = filename.replace('.json', '').split('_', 1)
            lab_id = parts[0]
            backtest_id = parts[1]
            
            # Load cached data
            cached_data = cache.load_backtest_cache(lab_id, backtest_id)
            if cached_data and 'runtime_data' in cached_data:
                runtime_data = cached_data['runtime_data']
                
                # Check Reports section
                if 'Reports' in runtime_data:
                    reports = runtime_data['Reports']
                    print(f"Reports keys: {list(reports.keys())}")
                    
                    # Check the first market report
                    market_key = list(reports.keys())[0]
                    market_report = reports[market_key]
                    print(f"\nMarket report for: {market_key}")
                    print(f"Market report type: {type(market_report)}")
                    
                    if isinstance(market_report, dict):
                        print(f"Market report keys: {list(market_report.keys())}")
                        
                        # Look for balance-related fields
                        balance_fields = ['SB', 'RPH', 'StartingBalance', 'FinalBalance', 'Balance']
                        for field in balance_fields:
                            if field in market_report:
                                value = market_report[field]
                                print(f"Market {field}: {value}")
                                if isinstance(value, list) and len(value) > 0:
                                    print(f"  First value: {value[0]}")
                                    print(f"  Last value: {value[-1]}")
                                    print(f"  Length: {len(value)}")
                        
                        # Show all fields that might contain balance info
                        print("\nAll fields in market report:")
                        for key, value in market_report.items():
                            if isinstance(value, (int, float)) and value > 1000:  # Potential balance values
                                print(f"  {key}: {value}")
                            elif isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], (int, float)) and value[0] > 1000:
                                    print(f"  {key}: list with {len(value)} values, first={value[0]}")
                    else:
                        print(f"Market report is not a dict: {market_report}")
    else:
        print("Cache directory not found")

if __name__ == '__main__':
    main()
