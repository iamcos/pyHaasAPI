#!/usr/bin/env python3
"""
Test script to verify the balance extraction fix
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
    
    # Test the first few labs to see if balance data is now working
    for i, lab in enumerate(labs[:3]):
        print(f'\n=== TESTING LAB {i+1}: {lab.name} ===')
        
        try:
            # Analyze lab and get top backtests
            result = analyzer.analyze_lab(lab.lab_id, top_count=2)
            print(f'Found {len(result.top_backtests)} backtests')
            
            if result.top_backtests:
                # Check the first backtest's balance data
                backtest = result.top_backtests[0]
                print(f'Backtest ID: {backtest.backtest_id}')
                print(f'Starting Balance: {backtest.starting_balance:.2f} USDT')
                print(f'Final Balance: {backtest.final_balance:.2f} USDT')
                print(f'Peak Balance: {backtest.peak_balance:.2f} USDT')
                print(f'Lab ROI: {backtest.roi_percentage:.1f}%')
                print(f'Calculated ROI: {backtest.calculated_roi_percentage:.1f}%')
                
                # Run robustness analysis to see the balance in the report
                robustness_metrics = robustness_analyzer.analyze_backtest_robustness(backtest)
                print(f'Robustness Score: {robustness_metrics.robustness_score:.1f}/100')
                print(f'Risk Level: {robustness_metrics.risk_level}')
                
                # If we found non-zero balance data, break
                if backtest.starting_balance > 0:
                    print('✅ SUCCESS: Found lab with proper balance data!')
                    break
                else:
                    print('❌ Still showing 0 balance data')
                    
        except Exception as e:
            print(f'Error analyzing lab {lab.lab_id}: {e}')
            continue

if __name__ == '__main__':
    main()
