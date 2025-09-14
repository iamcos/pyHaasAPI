#!/usr/bin/env python3
"""
Test script to verify enhanced analysis with drawdowns works
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reanalyze_cached_backtests import load_cached_backtest_data, extract_lab_id_from_filename, reanalyze_backtest_with_enhanced_features
from pathlib import Path

def test_enhanced_analysis():
    # Test with one backtest file
    cache_file = Path('unified_cache/backtests/058c6c5a-549a-4828-9169-a79b0a317229_02f6a4af-2bb0-42f2-9a71-9f2b522c7d0b.json')
    print(f'Testing enhanced analysis with: {cache_file.name}')

    # Load and analyze
    cached_data = load_cached_backtest_data(cache_file)
    lab_id = extract_lab_id_from_filename(cache_file.name)
    
    print(f'Lab ID: {lab_id}')
    print(f'Original ROI: {cached_data.get("roi_percentage", 0):.2f}%')
    print(f'Total Trades: {cached_data.get("total_trades", 0)}')
    print(f'Max Drawdown: {cached_data.get("max_drawdown", 0):.2f}%')

    # Reanalyze with enhanced features
    enhanced_analysis = reanalyze_backtest_with_enhanced_features(cached_data, lab_id)
    
    print(f'\n=== ENHANCED ANALYSIS RESULTS ===')
    print(f'Lab ROI: {enhanced_analysis.roi_percentage:.2f}%')
    print(f'ROE (Calculated ROI): {enhanced_analysis.calculated_roi_percentage:.2f}%')
    print(f'ROI Difference: {enhanced_analysis.roi_difference:.2f}%')
    print(f'Win Rate: {enhanced_analysis.win_rate:.1%}')
    print(f'Max Drawdown: {enhanced_analysis.max_drawdown:.2f}%')
    print(f'Total Trades: {enhanced_analysis.total_trades}')
    
    if enhanced_analysis.drawdown_analysis:
        dd = enhanced_analysis.drawdown_analysis
        print(f'\n=== DRAWDOWN ANALYSIS ===')
        print(f'Drawdown Count: {dd.drawdown_count}')
        print(f'Lowest Balance: {dd.lowest_balance:.2f}')
        print(f'Max Drawdown %: {dd.max_drawdown_percentage:.2f}%')
        
        if dd.drawdown_events:
            print(f'\nFirst 5 Drawdown Events:')
            for i, event in enumerate(dd.drawdown_events[:5]):
                print(f'  {i+1}. {event.timestamp} - Balance: {event.balance:.2f}, DD: {event.drawdown_amount:.2f}')
            
            if len(dd.drawdown_events) > 5:
                print(f'  ... and {len(dd.drawdown_events) - 5} more drawdown events')
    else:
        print('\nNo drawdown analysis available')

if __name__ == "__main__":
    test_enhanced_analysis()
