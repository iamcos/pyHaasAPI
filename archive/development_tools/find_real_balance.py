#!/usr/bin/env python3
"""
Find the real account balance by investigating all available fields
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path

def investigate_real_balance():
    """Investigate to find the real account balance"""
    
    # Find the cache file for the top bot
    cache_dir = Path('unified_cache/backtests')
    cache_files = list(cache_dir.glob('*_c44453ee-8be0-4c5f-8504-c4d2bfe26ebd.json'))
    
    if not cache_files:
        print("❌ Cache file not found")
        return
    
    cache_file = cache_files[0]
    print(f"📁 Analyzing: {cache_file.name}")
    
    with open(cache_file, 'r') as f:
        cached_data = json.load(f)
    
    runtime_data = cached_data.get('runtime_data', {})
    if isinstance(runtime_data, str):
        runtime_data = json.loads(runtime_data)
    
    print(f"\n🔍 INVESTIGATING ALL BALANCE-RELATED FIELDS:")
    
    # Check top-level fields that might contain balance info
    balance_fields = ['TradeAmount', 'AccountId', 'Leverage', 'MarginMode', 'PositionMode']
    for field in balance_fields:
        if field in runtime_data:
            print(f"{field}: {runtime_data[field]}")
    
    # Check Reports section for balance info
    reports = runtime_data.get('Reports', {})
    for report_key, report_data in reports.items():
        print(f"\n📊 REPORT: {report_key}")
        
        # Check PR (Performance Report) section
        if 'PR' in report_data:
            pr_data = report_data['PR']
            print(f"PR fields: {list(pr_data.keys())}")
            
            # Check each field in PR
            for key, value in pr_data.items():
                if key == 'RPH':
                    print(f"{key}: [list with {len(value)} values, first: {value[0]:.2f}, last: {value[-1]:.2f}]")
                else:
                    print(f"{key}: {value}")
            
            # Look for starting balance indicators
            print(f"\n🎯 BALANCE ANALYSIS:")
            print(f"SP (Starting Price?): {pr_data.get('SP', 'N/A')}")
            print(f"SB (Starting Balance?): {pr_data.get('SB', 'N/A')}")
            print(f"PC (Portfolio Current?): {pr_data.get('PC', 'N/A')}")
            print(f"BC (Balance Current?): {pr_data.get('BC', 'N/A')}")
            print(f"GP (Gross Profit?): {pr_data.get('GP', 'N/A')}")
            print(f"RP (Realized Profit?): {pr_data.get('RP', 'N/A')}")
            print(f"UP (Unrealized Profit?): {pr_data.get('UP', 'N/A')}")
            print(f"ROI: {pr_data.get('ROI', 'N/A')}")
            print(f"RM (Risk Management?): {pr_data.get('RM', 'N/A')}")
            print(f"CRM (Current Risk Management?): {pr_data.get('CRM', 'N/A')}")
            
            # Calculate what the starting balance might be
            rph_data = pr_data.get('RPH', [])
            if rph_data:
                first_rph = rph_data[0]
                last_rph = rph_data[-1]
                total_profit = last_rph - first_rph
                
                print(f"\n🧮 CALCULATIONS:")
                print(f"First RPH: {first_rph:,.2f}")
                print(f"Last RPH: {last_rph:,.2f}")
                print(f"RPH Change: {total_profit:,.2f}")
                
                # If RPH is cumulative profit, what's the starting balance?
                # Let's assume the bot started with some initial balance
                possible_starting_balances = [10000, 50000, 100000, 200000]
                
                print(f"\n💡 POSSIBLE SCENARIOS:")
                for start_balance in possible_starting_balances:
                    current_balance = start_balance + last_rph
                    print(f"  If started with {start_balance:,} USDT:")
                    print(f"    Current balance would be: {current_balance:,.2f} USDT")
                    print(f"    Total profit: {last_rph:,.2f} USDT")
                    print(f"    ROI: {(last_rph / start_balance * 100):.2f}%")
    
    # Check if there are any other balance-related fields
    print(f"\n🔍 CHECKING FOR OTHER BALANCE FIELDS:")
    all_keys = []
    def get_all_keys(obj, prefix=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_key = f"{prefix}.{key}" if prefix else key
                all_keys.append(current_key)
                if isinstance(value, (dict, list)) and len(str(value)) < 100:
                    get_all_keys(value, current_key)
        elif isinstance(obj, list) and len(obj) > 0:
            get_all_keys(obj[0], f"{prefix}[0]")
    
    get_all_keys(runtime_data)
    
    balance_related_keys = [key for key in all_keys if any(word in key.lower() for word in ['balance', 'amount', 'capital', 'equity', 'margin', 'fund'])]
    print(f"Balance-related keys found: {balance_related_keys}")

if __name__ == "__main__":
    investigate_real_balance()
