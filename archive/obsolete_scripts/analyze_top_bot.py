#!/usr/bin/env python3
"""
Analyze the top-ranked bot's profit curve and drawdown pattern
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np

def load_top_bot_data():
    """Load the top bot's data from the analysis"""
    # Find the most recent filtered bots file
    filtered_files = list(Path('.').glob('filtered_viable_bots_*.json'))
    if not filtered_files:
        print("❌ No filtered bots file found.")
        return None
    
    # Get the most recent file
    latest_file = max(filtered_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 Loading filtered bots from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        bots = json.load(f)
    
    # Get the top bot
    top_bot = bots[0] if bots else None
    return top_bot

def analyze_bot_balance_history(bot_id: str):
    """Analyze the balance history for a specific bot"""
    # Find the cache file with the bot_id
    cache_dir = Path('unified_cache/backtests')
    cache_files = list(cache_dir.glob(f'*_{bot_id}.json'))
    
    if not cache_files:
        print(f"❌ Cache file not found for bot: {bot_id}")
        return None
    
    cache_file = cache_files[0]
    print(f"📁 Found cache file: {cache_file.name}")
    
    with open(cache_file, 'r') as f:
        cached_data = json.load(f)
    
    # Extract balance history from RPH (Realized Profit History)
    runtime_data = cached_data.get('runtime_data', {})
    if isinstance(runtime_data, str):
        runtime_data = json.loads(runtime_data)
    
    balance_history = []
    
    # Look for balance history in Reports section
    reports = runtime_data.get('Reports', {})
    for report_key, report_data in reports.items():
        pr_data = report_data.get('PR', {})
        rph_data = pr_data.get('RPH', [])  # Realized Profit History
        
        if rph_data:
            balance_history = rph_data
            break
    
    return balance_history

def create_profit_curve_graph(bot_data: Dict[str, Any], balance_history: List[float]):
    """Create a graph showing the profit curve and drawdown"""
    
    if not balance_history:
        print("❌ No balance history data available")
        return
    
    # Convert to numpy array for easier manipulation
    balances = np.array(balance_history)
    
    # Calculate key metrics
    starting_balance = balances[0] if len(balances) > 0 else 0
    peak_balance = np.max(balances)
    lowest_balance = np.min(balances)
    final_balance = balances[-1] if len(balances) > 0 else 0
    
    # Calculate drawdowns
    running_max = np.maximum.accumulate(balances)
    drawdowns = (balances - running_max) / running_max * 100
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    
    # Plot 1: Balance over time
    time_points = range(len(balances))
    ax1.plot(time_points, balances, 'b-', linewidth=2, label='Account Balance')
    ax1.axhline(y=starting_balance, color='g', linestyle='--', alpha=0.7, label=f'Starting Balance: {starting_balance:,.0f} USDT')
    ax1.axhline(y=peak_balance, color='r', linestyle='--', alpha=0.7, label=f'Peak Balance: {peak_balance:,.0f} USDT')
    ax1.axhline(y=lowest_balance, color='orange', linestyle='--', alpha=0.7, label=f'Lowest Balance: {lowest_balance:,.0f} USDT')
    
    ax1.set_title(f'Bot {bot_data["backtest_id"][:8]} - Account Balance Over Time', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time Points')
    ax1.set_ylabel('Balance (USDT)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.ticklabel_format(style='plain', axis='y')
    
    # Plot 2: Drawdown percentage
    ax2.fill_between(time_points, drawdowns, 0, alpha=0.3, color='red', label='Drawdown %')
    ax2.plot(time_points, drawdowns, 'r-', linewidth=1)
    ax2.set_title('Drawdown Percentage Over Time', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time Points')
    ax2.set_ylabel('Drawdown (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add text box with key metrics
    metrics_text = f"""
    Bot ID: {bot_data['backtest_id'][:8]}
    Lab ROI: {bot_data['lab_roi']:.1f}%
    Calculated ROI: {bot_data['calculated_roi']:.1f}%
    Win Rate: {bot_data['win_rate']:.1%}
    Total Trades: {bot_data['total_trades']}
    
    Starting Balance: {starting_balance:,.0f} USDT
    Peak Balance: {peak_balance:,.0f} USDT
    Lowest Balance: {lowest_balance:,.0f} USDT
    Final Balance: {final_balance:,.0f} USDT
    
    Total Profit: {final_balance - starting_balance:,.0f} USDT
    Max Drawdown: {np.min(drawdowns):.2f}%
    """
    
    ax1.text(0.02, 0.98, metrics_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    # Save the plot
    output_file = f"bot_{bot_data['backtest_id'][:8]}_profit_curve.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Profit curve saved to: {output_file}")
    
    # Show the plot
    plt.show()
    
    return {
        'starting_balance': starting_balance,
        'peak_balance': peak_balance,
        'lowest_balance': lowest_balance,
        'final_balance': final_balance,
        'total_profit': final_balance - starting_balance,
        'max_drawdown_pct': np.min(drawdowns)
    }

def main():
    """Main function"""
    print("🚀 ANALYZING TOP BOT'S PROFIT CURVE")
    print("="*60)
    
    # Load top bot data
    top_bot = load_top_bot_data()
    if not top_bot:
        print("❌ No top bot data found")
        return
    
    print(f"📊 Analyzing bot: {top_bot['backtest_id'][:8]}")
    print(f"   Lab ROI: {top_bot['lab_roi']:.1f}%")
    print(f"   Calculated ROI: {top_bot['calculated_roi']:.1f}%")
    print(f"   Win Rate: {top_bot['win_rate']:.1%}")
    print(f"   Max DD USDT: {top_bot['max_drawdown_usdt']:,.0f}")
    
    # Get balance history
    balance_history = analyze_bot_balance_history(top_bot['backtest_id'])
    if not balance_history:
        print("❌ No balance history found")
        return
    
    print(f"📈 Found {len(balance_history)} balance data points")
    
    # Create profit curve graph
    metrics = create_profit_curve_graph(top_bot, balance_history)
    
    if metrics:
        print(f"\n📊 KEY METRICS:")
        print(f"   Starting Balance: {metrics['starting_balance']:,.0f} USDT")
        print(f"   Peak Balance: {metrics['peak_balance']:,.0f} USDT")
        print(f"   Lowest Balance: {metrics['lowest_balance']:,.0f} USDT")
        print(f"   Final Balance: {metrics['final_balance']:,.0f} USDT")
        print(f"   Total Profit: {metrics['total_profit']:,.0f} USDT")
        print(f"   Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")

if __name__ == "__main__":
    main()
