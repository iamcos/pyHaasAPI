#!/usr/bin/env python3
"""
Debug script to check balance data in cached backtests
"""

from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.robustness import StrategyRobustnessAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI import api
import os
from dotenv import load_dotenv

def main():
    load_dotenv()

    # Initialize components
    cache = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache)
    robustness_analyzer = StrategyRobustnessAnalyzer(cache)

    # Connect to API
    print('Connecting to HaasOnline API...')
    executor = analyzer.connect()
    if not executor:
        print('Failed to connect to API')
        return

    print('Connected successfully!')

    # Get available labs
    labs = api.get_all_labs(analyzer.executor)
    if not labs:
        print('No labs found')
        return

    print(f'Found {len(labs)} labs')
    
    # Check multiple labs to find one with proper balance data
    for i, lab in enumerate(labs[:5]):
        print(f'\n=== LAB {i+1}: {lab.name} ===')
        print(f'Lab ID: {lab.lab_id}')
        
        try:
            # Analyze lab and get top backtests
            result = analyzer.analyze_lab(lab.lab_id, top_count=2)
            print(f'Found {len(result.top_backtests)} backtests')
            
            if result.top_backtests:
                # Check the first backtest's balance data
                backtest = result.top_backtests[0]
                print(f'Backtest ID: {backtest.backtest_id}')
                print(f'Starting Balance: {backtest.starting_balance}')
                print(f'Final Balance: {backtest.final_balance}')
                print(f'Peak Balance: {backtest.peak_balance}')
                print(f'Lab ROI: {backtest.roi_percentage}%')
                print(f'Calculated ROI: {backtest.calculated_roi_percentage}%')
                
                # Check if we have cached data
                cached_data = cache.load_backtest_cache(lab.lab_id, backtest.backtest_id)
                if cached_data:
                    print('Cached data available')
                    # Check for balance-related fields in cached data
                    if 'SB' in cached_data:
                        print(f'Cached SB (Starting Balance): {cached_data["SB"]}')
                    if 'RPH' in cached_data:
                        rph = cached_data['RPH']
                        if isinstance(rph, list) and len(rph) > 0:
                            print(f'Cached RPH (first value): {rph[0]}')
                            print(f'Cached RPH (last value): {rph[-1]}')
                            print(f'Cached RPH length: {len(rph)}')
                        else:
                            print(f'Cached RPH: {rph}')
                else:
                    print('No cached data available')
                    
                # If we found non-zero balance data, break
                if backtest.starting_balance > 0:
                    print('Found lab with proper balance data!')
                    break
                    
        except Exception as e:
            print(f'Error analyzing lab {lab.lab_id}: {e}')
            continue

if __name__ == '__main__':
    main()
