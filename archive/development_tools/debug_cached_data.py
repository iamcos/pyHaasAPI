#!/usr/bin/env python3
"""
Debug script to examine cached data structure
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
        
        # Examine the first few files
        for i, filename in enumerate(files[:3]):
            print(f"\n=== FILE {i+1}: {filename} ===")
            
            # Extract lab_id and backtest_id from filename
            if '_' in filename:
                parts = filename.replace('.json', '').split('_', 1)
                lab_id = parts[0]
                backtest_id = parts[1]
                
                print(f"Lab ID: {lab_id}")
                print(f"Backtest ID: {backtest_id}")
                
                # Load cached data
                cached_data = cache.load_backtest_cache(lab_id, backtest_id)
                if cached_data:
                    print("Cached data keys:", list(cached_data.keys()))
                    
                    # Check for balance-related fields
                    balance_fields = ['SB', 'RPH', 'StartingBalance', 'FinalBalance', 'Balance']
                    for field in balance_fields:
                        if field in cached_data:
                            value = cached_data[field]
                            print(f"{field}: {value}")
                            if isinstance(value, list) and len(value) > 0:
                                print(f"  First value: {value[0]}")
                                print(f"  Last value: {value[-1]}")
                                print(f"  Length: {len(value)}")
                    
                    # Check for any field that might contain balance info
                    print("\nAll fields in cached data:")
                    for key, value in cached_data.items():
                        if isinstance(value, (int, float)) and value > 1000:  # Potential balance values
                            print(f"  {key}: {value}")
                        elif isinstance(value, list) and len(value) > 0:
                            if isinstance(value[0], (int, float)) and value[0] > 1000:
                                print(f"  {key}: list with {len(value)} values, first={value[0]}")
                else:
                    print("No cached data found")
            else:
                print(f"Unexpected filename format: {filename}")
    else:
        print("Cache directory not found")

if __name__ == '__main__':
    main()
