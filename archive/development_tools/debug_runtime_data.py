#!/usr/bin/env python3
"""
Debug script to examine runtime_data structure in cached files
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
        print(f"Found {len(files)} cached files")
        
        # Examine the first file
        filename = files[0]
        print(f"\n=== FILE: {filename} ===")
        
        # Extract lab_id and backtest_id from filename
        if '_' in filename:
            parts = filename.replace('.json', '').split('_', 1)
            lab_id = parts[0]
            backtest_id = parts[1]
            
            print(f"Lab ID: {lab_id}")
            print(f"Backtest ID: {backtest_id}")
            
            # Load cached data
            cached_data = cache.load_backtest_cache(lab_id, backtest_id)
            if cached_data and 'runtime_data' in cached_data:
                runtime_data = cached_data['runtime_data']
                print(f"Runtime data type: {type(runtime_data)}")
                print(f"Runtime data keys: {list(runtime_data.keys()) if isinstance(runtime_data, dict) else 'Not a dict'}")
                
                # Check for balance-related fields in runtime_data
                if isinstance(runtime_data, dict):
                    balance_fields = ['SB', 'RPH', 'StartingBalance', 'FinalBalance', 'Balance']
                    for field in balance_fields:
                        if field in runtime_data:
                            value = runtime_data[field]
                            print(f"Runtime {field}: {value}")
                            if isinstance(value, list) and len(value) > 0:
                                print(f"  First value: {value[0]}")
                                print(f"  Last value: {value[-1]}")
                                print(f"  Length: {len(value)}")
                    
                    # Show all fields in runtime_data
                    print("\nAll fields in runtime_data:")
                    for key, value in runtime_data.items():
                        if isinstance(value, (int, float)) and value > 1000:  # Potential balance values
                            print(f"  {key}: {value}")
                        elif isinstance(value, list) and len(value) > 0:
                            if isinstance(value[0], (int, float)) and value[0] > 1000:
                                print(f"  {key}: list with {len(value)} values, first={value[0]}")
            else:
                print("No runtime_data found in cached data")
    else:
        print("Cache directory not found")

if __name__ == '__main__':
    main()
