#!/usr/bin/env python3
"""
Debug script to examine the structure of cached backtest data
"""

import json
from pathlib import Path

def debug_cache_structure():
    # Load the cache file and examine the structure
    cache_file = Path('unified_cache/backtests/058c6c5a-549a-4828-9169-a79b0a317229_02f6a4af-2bb0-42f2-9a71-9f2b522c7d0b.json')
    
    print(f"Loading cache file: {cache_file.name}")
    
    with open(cache_file, 'r') as f:
        data = json.load(f)

    runtime_data = data.get('runtime_data', {})
    print('Runtime data keys:', list(runtime_data.keys()))

    reports = runtime_data.get('Reports', {})
    print('Reports keys:', list(reports.keys()))

    if reports:
        report_key = list(reports.keys())[0]
        report_data = reports[report_key]
        print('Report data keys:', list(report_data.keys()))
        
        finished_positions = report_data.get('FinishedPositions', [])
        print(f'Found {len(finished_positions)} finished positions')
        
        if finished_positions:
            first_position = finished_positions[0]
            print('First position keys:', list(first_position.keys()))
            print('First position rp (realized profit):', first_position.get('rp', 'NOT FOUND'))
            print('First position fe (fees):', first_position.get('fe', 'NOT FOUND'))
            print('First position eno (entry orders):', len(first_position.get('eno', [])))
            
            # Show first few trades
            print(f'\nFirst 3 trades:')
            for i, position in enumerate(finished_positions[:3]):
                rp = position.get('rp', 0)
                fe = position.get('fe', 0)
                eno_count = len(position.get('eno', []))
                print(f'  Trade {i+1}: rp={rp}, fe={fe}, entry_orders={eno_count}')
        else:
            print('No finished positions found!')
    else:
        print('No reports found!')

if __name__ == "__main__":
    debug_cache_structure()

