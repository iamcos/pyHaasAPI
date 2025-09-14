#!/usr/bin/env python3
"""
Debug script to examine Reports section in runtime_data
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
                    print(f"Reports type: {type(reports)}")
                    if isinstance(reports, dict):
                        print(f"Reports keys: {list(reports.keys())}")
                        
                        # Look for balance-related fields in Reports
                        balance_fields = ['SB', 'RPH', 'StartingBalance', 'FinalBalance', 'Balance']
                        for field in balance_fields:
                            if field in reports:
                                value = reports[field]
                                print(f"Reports {field}: {value}")
                                if isinstance(value, list) and len(value) > 0:
                                    print(f"  First value: {value[0]}")
                                    print(f"  Last value: {value[-1]}")
                                    print(f"  Length: {len(value)}")
                        
                        # Show all fields in Reports that might contain balance info
                        print("\nAll fields in Reports:")
                        for key, value in reports.items():
                            if isinstance(value, (int, float)) and value > 1000:  # Potential balance values
                                print(f"  {key}: {value}")
                            elif isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], (int, float)) and value[0] > 1000:
                                    print(f"  {key}: list with {len(value)} values, first={value[0]}")
                    else:
                        print(f"Reports is not a dict: {reports}")
                else:
                    print("No Reports section found in runtime_data")
                    
                # Also check if SB and RPH are at the top level of runtime_data
                print("\nChecking top-level runtime_data for SB and RPH:")
                for key in ['SB', 'RPH']:
                    if key in runtime_data:
                        value = runtime_data[key]
                        print(f"Top-level {key}: {value}")
                        if isinstance(value, list) and len(value) > 0:
                            print(f"  First value: {value[0]}")
                            print(f"  Last value: {value[-1]}")
                            print(f"  Length: {len(value)}")
    else:
        print("Cache directory not found")

if __name__ == '__main__':
    main()
