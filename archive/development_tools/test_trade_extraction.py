#!/usr/bin/env python3
"""
Test script to verify trade extraction works
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
import json

def test_trade_extraction():
    # Create analyzer
    cache_manager = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache_manager)
    
    # Load test cache file
    with open('unified_cache/backtests/058c6c5a-549a-4828-9169-a79b0a317229_02f6a4af-2bb0-42f2-9a71-9f2b522c7d0b.json', 'r') as f:
        cached_data = json.load(f)
    
    runtime_data = cached_data.get('runtime_data', {})
    print(f"Runtime data keys: {list(runtime_data.keys())}")
    
    # Test trade extraction
    trades = analyzer._extract_trades_from_runtime_data(runtime_data)
    print(f"Extracted {len(trades)} trades")
    
    if trades:
        print("First 3 trades:")
        for i, trade in enumerate(trades[:3]):
            print(f"  Trade {i+1}: ID={trade['position_id'][:8]}, P&L={trade['profit_loss']:.2f}, Fees={trade['fees']:.2f}, Amount={trade['trade_amount']:.2f}")
        
        # Test ROI calculation
        calculated_roi = analyzer._calculate_roi_from_trades(runtime_data)
        print(f"Calculated ROI: {calculated_roi:.2f}%")
        
        # Compare with lab ROI
        lab_roi = cached_data.get('roi_percentage', 0.0)
        print(f"Lab ROI: {lab_roi:.2f}%")
        print(f"Difference: {abs(lab_roi - calculated_roi):.2f}%")
    else:
        print("No trades found!")

if __name__ == "__main__":
    test_trade_extraction()
