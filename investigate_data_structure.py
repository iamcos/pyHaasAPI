#!/usr/bin/env python3
import json
from pathlib import Path

# Check a few different cached files to see the data structure
cache_dir = Path('unified_cache/backtests')

# Check files from different labs
files_to_check = [
    'd26e6ff3-a706-4ae1-89c9-d82d49274a5f_*.json',  # Lab that shows generation/population
    '44f08a06-2a27-4015-910e-a7fd8cdb25b8_*.json'   # Lab that doesn't show generation/population
]

for pattern in files_to_check:
    files = list(cache_dir.glob(pattern))
    if files:
        print(f'\n🔍 CHECKING: {pattern}')
        print('-' * 60)
        
        with open(files[0], 'r') as f:
            data = json.load(f)
        
        print('Top-level keys:', list(data.keys()))
        
        # Check if there are any fields that might contain generation/population
        for key, value in data.items():
            if 'gen' in key.lower() or 'pop' in key.lower() or 'generation' in key.lower() or 'population' in key.lower():
                print(f'Found: {key} = {value}')
        
        # Check if there's a runtime_data section
        if 'runtime_data' in data:
            print('runtime_data keys:', list(data['runtime_data'].keys()))
            for key, value in data['runtime_data'].items():
                if 'gen' in key.lower() or 'pop' in key.lower() or 'generation' in key.lower() or 'population' in key.lower():
                    print(f'Found in runtime_data: {key} = {value}')
        
        # Check if there are any numeric fields that might be generation/population
        print('\nNumeric fields that might be generation/population:')
        for key, value in data.items():
            if isinstance(value, (int, float)) and value > 0 and value < 1000:
                print(f'{key}: {value}')
        
        # Check the backtest ID structure
        backtest_id = files[0].stem.split('_', 1)[1]
        print(f'\nBacktest ID: {backtest_id}')
        
        # Try to extract generation/population from the backtest ID
        parts = backtest_id.split('-')
        print(f'Backtest ID parts: {parts}')
        
        # Look for any patterns that might indicate generation/population
        for i, part in enumerate(parts):
            if part.isdigit():
                print(f'Numeric part {i}: {part}')
            elif len(part) == 4 and part.isalnum():
                # Try to convert hex to decimal
                try:
                    decimal = int(part, 16)
                    if 0 < decimal < 1000:
                        print(f'Hex part {i} ({part}) = {decimal}')
                except:
                    pass
