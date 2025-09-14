#!/usr/bin/env python3
"""
Investigate the balance anomaly - why is account balance so high?
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np

def investigate_top_bot():
    """Investigate the top bot's data structure and balance"""
    
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
    
    print(f"\n🔍 INVESTIGATING DATA STRUCTURE:")
    print(f"Keys in cached_data: {list(cached_data.keys())}")
    
    # Check runtime_data structure
    runtime_data = cached_data.get('runtime_data', {})
    if isinstance(runtime_data, str):
        runtime_data = json.loads(runtime_data)
    
    print(f"\n📊 RUNTIME DATA STRUCTURE:")
    print(f"Runtime data type: {type(runtime_data)}")
    if isinstance(runtime_data, dict):
        print(f"Runtime data keys: {list(runtime_data.keys())}")
        
        # Look at Reports section
        reports = runtime_data.get('Reports', {})
        print(f"Reports keys: {list(reports.keys())}")
        
        for report_key, report_data in reports.items():
            print(f"\n📈 REPORT: {report_key}")
            print(f"Report data keys: {list(report_data.keys())}")
            
            if 'PR' in report_data:
                pr_data = report_data['PR']
                print(f"PR data keys: {list(pr_data.keys())}")
                
                # Check RPH (Realized Profit History)
                if 'RPH' in pr_data:
                    rph_data = pr_data['RPH']
                    print(f"RPH data type: {type(rph_data)}")
                    print(f"RPH length: {len(rph_data) if isinstance(rph_data, list) else 'N/A'}")
                    
                    if isinstance(rph_data, list) and len(rph_data) > 0:
                        print(f"First 10 RPH values: {rph_data[:10]}")
                        print(f"Last 10 RPH values: {rph_data[-10:]}")
                        print(f"Min RPH: {min(rph_data)}")
                        print(f"Max RPH: {max(rph_data)}")
                        
                        # Check if this looks like cumulative profit or account balance
                        print(f"\n🤔 ANALYSIS:")
                        print(f"Starting value: {rph_data[0]}")
                        print(f"Ending value: {rph_data[-1]}")
                        print(f"Total change: {rph_data[-1] - rph_data[0]}")
                        
                        # Check for negative values (shouldn't happen with account balance if starting with 10k)
                        negative_count = sum(1 for x in rph_data if x < 0)
                        print(f"Negative values count: {negative_count}")
                        
                        # Check if values are reasonable for 10k starting balance
                        reasonable_count = sum(1 for x in rph_data if 0 <= x <= 50000)  # Reasonable range for 10k start
                        print(f"Values in reasonable range (0-50k): {reasonable_count}/{len(rph_data)}")
                        
                        return rph_data, pr_data
                
                # Check other relevant fields
                for key, value in pr_data.items():
                    if key not in ['RPH']:
                        print(f"{key}: {value}")
    
    return None, None

def create_balance_analysis_graph(balance_data: List[float], pr_data: Dict):
    """Create a detailed balance analysis graph"""
    
    if not balance_data:
        print("❌ No balance data to plot")
        return
    
    balances = np.array(balance_data)
    
    # Create comprehensive analysis
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Plot 1: Full balance curve
    time_points = range(len(balances))
    ax1.plot(time_points, balances, 'b-', linewidth=1, label='Balance Data')
    ax1.set_title('Full Balance Curve', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time Points')
    ax1.set_ylabel('Balance (USDT)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.ticklabel_format(style='plain', axis='y')
    
    # Plot 2: First 100 points (beginning)
    first_100 = min(100, len(balances))
    ax2.plot(time_points[:first_100], balances[:first_100], 'g-', linewidth=2, label='First 100 Points')
    ax2.axhline(y=10000, color='r', linestyle='--', alpha=0.7, label='Expected Start: 10,000 USDT')
    ax2.set_title('Beginning of Trading (First 100 Points)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time Points')
    ax2.set_ylabel('Balance (USDT)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Balance distribution
    ax3.hist(balances, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax3.axvline(x=10000, color='r', linestyle='--', alpha=0.7, label='Expected Start: 10,000 USDT')
    ax3.set_title('Balance Distribution', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Balance (USDT)')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Daily changes
    daily_changes = np.diff(balances)
    ax4.plot(time_points[1:], daily_changes, 'purple', linewidth=1, alpha=0.7)
    ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax4.set_title('Daily Balance Changes', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Time Points')
    ax4.set_ylabel('Daily Change (USDT)')
    ax4.grid(True, alpha=0.3)
    
    # Add comprehensive metrics
    metrics_text = f"""
    DATA ANALYSIS:
    
    Total Data Points: {len(balances)}
    Starting Value: {balances[0]:,.0f} USDT
    Ending Value: {balances[-1]:,.0f} USDT
    Min Value: {np.min(balances):,.0f} USDT
    Max Value: {np.max(balances):,.0f} USDT
    
    Total Change: {balances[-1] - balances[0]:,.0f} USDT
    Percentage Change: {((balances[-1] - balances[0]) / balances[0] * 100):.1f}%
    
    Negative Values: {sum(1 for x in balances if x < 0)}
    Values < 10k: {sum(1 for x in balances if x < 10000)}
    Values > 50k: {sum(1 for x in balances if x > 50000)}
    
    HYPOTHESIS:
    This looks like CUMULATIVE PROFIT data,
    not account balance!
    """
    
    ax1.text(0.02, 0.98, metrics_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    
    # Save the plot
    output_file = "balance_anomaly_investigation.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Investigation graph saved to: {output_file}")
    
    plt.show()

def main():
    """Main function"""
    print("🚨 INVESTIGATING BALANCE ANOMALY")
    print("="*60)
    print("Expected: Starting with 10,000 USDT, 20x leverage")
    print("Found: Balance reaching 160,889 USDT")
    print("This is IMPOSSIBLE unless data is misinterpreted!")
    print("="*60)
    
    balance_data, pr_data = investigate_top_bot()
    
    if balance_data:
        print(f"\n🎯 CONCLUSION:")
        print(f"The 'balance' data is likely CUMULATIVE PROFIT, not account balance!")
        print(f"Starting value: {balance_data[0]:,.0f} USDT")
        print(f"This suggests the bot started with {balance_data[0]:,.0f} USDT, not 10,000 USDT")
        
        create_balance_analysis_graph(balance_data, pr_data)
    else:
        print("❌ Could not analyze balance data")

if __name__ == "__main__":
    main()
