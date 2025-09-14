#!/usr/bin/env python3
"""
Test script for robustness analysis with enhanced balance reporting
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
    print('Available labs:')
    for i, lab in enumerate(labs[:5]):  # Show first 5 labs
        print(f'  {i+1}. {lab.name} (ID: {lab.lab_id})')

    # Analyze the first lab
    if labs:
        lab = labs[0]
        print(f'\nAnalyzing lab: {lab.name}')
        
        # Analyze lab and get top backtests
        result = analyzer.analyze_lab(lab.lab_id, top_count=3)
        print(f'Found {len(result.top_backtests)} backtests to analyze')
        
        # Run robustness analysis on the backtests
        robustness_results = robustness_analyzer.analyze_lab_robustness(result)
        
        # Generate and display report
        report = robustness_analyzer.generate_robustness_report(robustness_results)
        print('\n' + '='*80)
        print('ROBUSTNESS ANALYSIS REPORT')
        print('='*80)
        print(report)

if __name__ == '__main__':
    main()
