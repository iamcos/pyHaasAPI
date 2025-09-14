#!/usr/bin/env python3
"""
Comprehensive search for balance fields (SB, RPH) in cached runtime data
"""

from pyHaasAPI.analysis.cache import UnifiedCacheManager
import json

def search_for_fields(data, path="", target_fields=['SB', 'RPH']):
    """Recursively search for target fields in nested data structure"""
    found_fields = {}
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check if this key matches our target fields
            if key in target_fields:
                found_fields[current_path] = value
                print(f"FOUND {key} at: {current_path}")
                if isinstance(value, list) and len(value) > 0:
                    print(f"  First value: {value[0]}")
                    print(f"  Last value: {value[-1]}")
                    print(f"  Length: {len(value)}")
                else:
                    print(f"  Value: {value}")
            
            # Recursively search nested structures
            if isinstance(value, (dict, list)):
                nested_found = search_for_fields(value, current_path, target_fields)
                found_fields.update(nested_found)
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            if isinstance(item, (dict, list)):
                nested_found = search_for_fields(item, current_path, target_fields)
                found_fields.update(nested_found)
    
    return found_fields

def main():
    cache = UnifiedCacheManager()
    
    # Get all cached files
    import os
    cache_dir = "unified_cache/backtests"
    if not os.path.exists(cache_dir):
        print("Cache directory not found")
        return
    
    files = os.listdir(cache_dir)
    print(f"Searching through {len(files)} cached files for SB and RPH fields...")
    
    # Search through first 10 files to find the pattern
    found_any = False
    for i, filename in enumerate(files[:10]):
        print(f"\n=== SEARCHING FILE {i+1}: {filename} ===")
        
        # Extract lab_id and backtest_id from filename
        if '_' in filename:
            parts = filename.replace('.json', '').split('_', 1)
            lab_id = parts[0]
            backtest_id = parts[1]
            
            # Load cached data
            cached_data = cache.load_backtest_cache(lab_id, backtest_id)
            if cached_data and 'runtime_data' in cached_data:
                runtime_data = cached_data['runtime_data']
                
                # Search for SB and RPH fields
                found_fields = search_for_fields(runtime_data, "runtime_data", ['SB', 'RPH'])
                
                if found_fields:
                    found_any = True
                    print(f"Found {len(found_fields)} balance fields in this file")
                else:
                    print("No SB or RPH fields found in this file")
            else:
                print("No runtime_data found")
    
    if not found_any:
        print("\n❌ NO SB OR RPH FIELDS FOUND IN ANY OF THE FIRST 10 FILES")
        print("This suggests the balance fields might be:")
        print("1. Named differently (not SB/RPH)")
        print("2. In a different data structure")
        print("3. Not cached at all")
        print("4. In a different location in the data hierarchy")
        
        # Let's also search for any fields that might contain balance-like data
        print("\n🔍 Searching for any fields that might contain balance data...")
        for i, filename in enumerate(files[:3]):
            print(f"\n=== ANALYZING FILE {i+1}: {filename} ===")
            
            parts = filename.replace('.json', '').split('_', 1)
            lab_id = parts[0]
            backtest_id = parts[1]
            
            cached_data = cache.load_backtest_cache(lab_id, backtest_id)
            if cached_data and 'runtime_data' in cached_data:
                runtime_data = cached_data['runtime_data']
                
                # Search for any fields that might contain balance data
                def find_balance_like_fields(data, path=""):
                    balance_like = {}
                    
                    if isinstance(data, dict):
                        for key, value in data.items():
                            current_path = f"{path}.{key}" if path else key
                            
                            # Look for fields that might contain balance data
                            if isinstance(value, (int, float)) and value > 1000:
                                balance_like[current_path] = value
                            elif isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], (int, float)) and value[0] > 1000:
                                    balance_like[current_path] = f"list with {len(value)} values, first={value[0]}"
                            
                            # Recursively search
                            if isinstance(value, (dict, list)):
                                nested = find_balance_like_fields(value, current_path)
                                balance_like.update(nested)
                    
                    elif isinstance(data, list):
                        for i, item in enumerate(data):
                            current_path = f"{path}[{i}]"
                            if isinstance(item, (dict, list)):
                                nested = find_balance_like_fields(item, current_path)
                                balance_like.update(nested)
                    
                    return balance_like
                
                balance_like_fields = find_balance_like_fields(runtime_data, "runtime_data")
                if balance_like_fields:
                    print("Found fields that might contain balance data:")
                    for path, value in balance_like_fields.items():
                        print(f"  {path}: {value}")
                else:
                    print("No balance-like fields found")

if __name__ == '__main__':
    main()
