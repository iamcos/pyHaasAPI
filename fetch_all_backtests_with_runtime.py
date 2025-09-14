#!/usr/bin/env python3
"""
Script to fetch all backtests with their runtime data for a specific lab.
This will get the complete performance metrics for all backtests.
"""

import os
import time
from dotenv import load_dotenv
from pyHaasAPI import api
from pyHaasAPI.tools.utils import fetch_all_lab_backtests
from pyHaasAPI.analysis.cache import UnifiedCacheManager

load_dotenv()

def main():
    # Create API connection
    haas_api = api.RequestsExecutor(
        host='127.0.0.1',
        port=8090,
        state=api.Guest()
    )

    # Authenticate
    executor = haas_api.authenticate(
        os.getenv('API_EMAIL'), 
        os.getenv('API_PASSWORD')
    )
    
    lab_id = "d26e6ff3-a706-4ae1-89c9-d82d49274a5f"
    
    print(f"🔍 Fetching all backtests with runtime data for lab: {lab_id}")
    
    # Fetch all 1000 backtests using page size 1000
    print("🔍 Fetching all 1000 backtests with page_size=1000...")
    backtests = fetch_all_lab_backtests(executor, lab_id, page_size=1000)
    print(f"📊 Total backtests fetched: {len(backtests)}")
    
    if not backtests:
        print("❌ No backtests found")
        return
    
    # Initialize cache manager
    cache_manager = UnifiedCacheManager()
    
    # Fetch runtime data for each backtest
    print(f"\n🚀 Starting runtime data fetch for {len(backtests)} backtests...")
    
    successful_fetches = 0
    failed_fetches = 0
    
    for i, backtest in enumerate(backtests):
        backtest_id = getattr(backtest, 'backtest_id', None)
        if not backtest_id:
            print(f"❌ Backtest {i+1}: No backtest_id found")
            failed_fetches += 1
            continue
            
        try:
            print(f"📊 Fetching runtime data for backtest {i+1}/{len(backtests)}: {backtest_id}")
            
            # Fetch runtime data
            runtime_data = api.get_backtest_runtime(executor, lab_id, backtest_id)
            
            # Cache the runtime data
            cache_manager.cache_backtest_data(lab_id, backtest_id, runtime_data)
            
            successful_fetches += 1
            
            # Show progress every 50 backtests
            if (i + 1) % 50 == 0:
                print(f"✅ Progress: {i+1}/{len(backtests)} backtests processed")
                
            # Small delay to avoid overwhelming the API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error fetching runtime data for backtest {i+1}: {e}")
            failed_fetches += 1
            continue
    
    print(f"\n📊 FETCH SUMMARY:")
    print(f"✅ Successful fetches: {successful_fetches}")
    print(f"❌ Failed fetches: {failed_fetches}")
    print(f"📊 Total backtests: {len(backtests)}")
    
    # Check how many are now cached
    cached_count = len([f for f in os.listdir(cache_manager.base_dir / "backtests") 
                       if f.startswith(f"{lab_id}_")])
    print(f"📊 Cached backtests: {cached_count}")
    
    print(f"\n🎉 All backtests with runtime data have been fetched and cached!")

if __name__ == "__main__":
    main()
