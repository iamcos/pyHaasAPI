#!/usr/bin/env python3
"""
Analyze backtest data from the JSON dumps and create a CSV report
"""

import json
import csv
import os
from typing import List, Dict, Any
from datetime import datetime

def parse_backtest_string(backtest_str: str) -> Dict[str, Any]:
    """Parse a backtest string representation into a dictionary"""
    try:
        # Extract key information using string parsing
        data = {}
        
        # Extract backtest_id
        if "backtest_id='" in backtest_str:
            start = backtest_str.find("backtest_id='") + 13
            end = backtest_str.find("'", start)
            data['backtest_id'] = backtest_str[start:end]
        
        # Extract generation_idx
        if "generation_idx=" in backtest_str:
            start = backtest_str.find("generation_idx=") + 15
            end = backtest_str.find(" ", start)
            data['generation_idx'] = int(backtest_str[start:end])
        
        # Extract population_idx
        if "population_idx=" in backtest_str:
            start = backtest_str.find("population_idx=") + 15
            end = backtest_str.find(" ", start)
            data['population_idx'] = int(backtest_str[start:end])
        
        # Extract parameters
        if "parameters={" in backtest_str:
            start = backtest_str.find("parameters={") + 12
            end = backtest_str.find("} runtime=", start)
            if end == -1:
                end = backtest_str.find("} summary=", start)
            if end != -1:
                params_str = backtest_str[start:end]
                params = {}
                # Parse parameters like "'3-3-21-26.Rising Length': '17'"
                parts = params_str.split("'")
                for i in range(1, len(parts), 4):
                    if i + 2 < len(parts):
                        key = parts[i]
                        value = parts[i + 2]
                        params[key] = value
                data['parameters'] = params
        
        # Extract settings information
        if "settings=HaasScriptSettings(" in backtest_str:
            start = backtest_str.find("settings=HaasScriptSettings(") + 29
            end = backtest_str.find(") parameters=", start)
            if end != -1:
                settings_str = backtest_str[start:end]
                # Extract interval
                if "interval=" in settings_str:
                    interval_start = settings_str.find("interval=") + 9
                    interval_end = settings_str.find(" ", interval_start)
                    if interval_end == -1:
                        interval_end = settings_str.find(",", interval_start)
                    if interval_end != -1:
                        interval_str = settings_str[interval_start:interval_end]
                        # Remove trailing comma if present
                        if interval_str.endswith(','):
                            interval_str = interval_str[:-1]
                        try:
                            data['interval'] = int(interval_str)
                        except ValueError:
                            pass
                
                # Extract trade_amount
                if "trade_amount=" in settings_str:
                    amount_start = settings_str.find("trade_amount=") + 13
                    amount_end = settings_str.find(" ", amount_start)
                    if amount_end == -1:
                        amount_end = settings_str.find(",", amount_start)
                    if amount_end != -1:
                        amount_str = settings_str[amount_start:amount_end]
                        # Remove trailing comma if present
                        if amount_str.endswith(','):
                            amount_str = amount_str[:-1]
                        try:
                            data['trade_amount'] = float(amount_str)
                        except ValueError:
                            pass
        
        return data
    except Exception as e:
        print(f"Error parsing backtest string: {e}")
        return {}

def analyze_backtest_data(output_dir: str):
    """Analyze the backtest data and create a CSV report"""
    
    # Read the backtests list
    backtests_list_file = os.path.join(output_dir, "backtests_list.json")
    if not os.path.exists(backtests_list_file):
        print(f"Backtests list file not found: {backtests_list_file}")
        return
    
    with open(backtests_list_file, 'r') as f:
        backtests_list = json.load(f)
    
    print(f"Found {len(backtests_list)} backtests")
    
    # Parse each backtest (limit to first 100 for analysis)
    parsed_backtests = []
    test_limit = 100
    for i, backtest_str in enumerate(backtests_list[:test_limit]):
        print(f"Processing backtest {i+1}/{test_limit}")
        
        data = parse_backtest_string(backtest_str)
        if data:
            parsed_backtests.append(data)
    
    print(f"Successfully parsed {len(parsed_backtests)} backtests")
    
    # Create CSV report
    csv_file = os.path.join(output_dir, "backtests_analysis.csv")
    
    # Define CSV headers
    headers = [
        'backtest_id', 'generation_idx', 'population_idx', 'interval', 'trade_amount',
        'rising_length', 'vwap_window', 'stop_loss_percentage', 'stop_loss_shrinkage'
    ]
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for backtest in parsed_backtests:
            row = {
                'backtest_id': backtest.get('backtest_id', ''),
                'generation_idx': backtest.get('generation_idx', ''),
                'population_idx': backtest.get('population_idx', ''),
                'interval': backtest.get('interval', ''),
                'trade_amount': backtest.get('trade_amount', ''),
                'rising_length': backtest.get('parameters', {}).get('3-3-21-26.Rising Length', ''),
                'vwap_window': backtest.get('parameters', {}).get('4-4-19-24.VWAP Window', ''),
                'stop_loss_percentage': backtest.get('parameters', {}).get('6-6-27-32.Stop Loss Percentage', ''),
                'stop_loss_shrinkage': backtest.get('parameters', {}).get('7-7-26-31.Stop Loss Shrinkage', '')
            }
            writer.writerow(row)
    
    print(f"CSV report created: {csv_file}")
    
    # Print summary statistics
    print("\n=== SUMMARY STATISTICS ===")
    
    # Generation distribution
    generations = [bt.get('generation_idx', 0) for bt in parsed_backtests]
    if generations:
        print(f"Generations: {min(generations)} to {max(generations)}")
        print(f"Total generations: {len(set(generations))}")
    
    # Interval distribution
    intervals = [bt.get('interval', 0) for bt in parsed_backtests if bt.get('interval')]
    if intervals:
        interval_counts = {}
        for interval in intervals:
            interval_counts[interval] = interval_counts.get(interval, 0) + 1
        print(f"\nInterval distribution:")
        for interval, count in sorted(interval_counts.items()):
            print(f"  {interval}: {count} backtests")
    
    # Parameter ranges
    rising_lengths = [bt.get('parameters', {}).get('3-3-21-26.Rising Length', '') for bt in parsed_backtests]
    rising_lengths = [int(x) for x in rising_lengths if x.isdigit()]
    if rising_lengths:
        print(f"\nRising Length range: {min(rising_lengths)} to {max(rising_lengths)}")
    
    vwap_windows = [bt.get('parameters', {}).get('4-4-19-24.VWAP Window', '') for bt in parsed_backtests]
    vwap_windows = [int(x) for x in vwap_windows if x.isdigit()]
    if vwap_windows:
        print(f"VWAP Window range: {min(vwap_windows)} to {max(vwap_windows)}")
    
    stop_losses = [bt.get('parameters', {}).get('6-6-27-32.Stop Loss Percentage', '') for bt in parsed_backtests]
    stop_losses = [float(x) for x in stop_losses if x.replace('.', '').isdigit()]
    if stop_losses:
        print(f"Stop Loss Percentage range: {min(stop_losses):.1f}% to {max(stop_losses):.1f}%")
    
    shrinkages = [bt.get('parameters', {}).get('7-7-26-31.Stop Loss Shrinkage', '') for bt in parsed_backtests]
    shrinkages = [float(x) for x in shrinkages if x.replace('.', '').isdigit()]
    if shrinkages:
        print(f"Stop Loss Shrinkage range: {min(shrinkages):.1f} to {max(shrinkages):.1f}")

if __name__ == "__main__":
    # Find the output directory
    current_dir = os.getcwd()
    output_dirs = [d for d in os.listdir(current_dir) if d.startswith("lab_backtests_") and os.path.isdir(d)]
    
    if not output_dirs:
        print("No backtest output directory found")
        exit(1)
    
    # Use the most recent directory
    output_dir = sorted(output_dirs)[-1]
    print(f"Using output directory: {output_dir}")
    
    analyze_backtest_data(output_dir)
