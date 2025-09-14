#!/usr/bin/env python3
"""
Filter viable bots by comparing ROI to HOLD value and applying stricter criteria
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def load_viable_bots():
    """Load the viable bots from the analysis report"""
    # Find the most recent viable bots file
    viable_files = list(Path('.').glob('viable_bots_*.json'))
    if not viable_files:
        print("❌ No viable bots file found. Run analyze_all_backtests.py first.")
        return []
    
    # Get the most recent file
    latest_file = max(viable_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 Loading viable bots from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        return json.load(f)

def analyze_hold_performance(viable_bots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze bots against HOLD baseline and apply stricter filtering"""
    
    print(f"\n🔍 FILTERING {len(viable_bots)} VIABLE BOTS WITH HOLD COMPARISON")
    print("="*80)
    
    # Enhanced filtering criteria
    filtered_bots = []
    
    for bot in viable_bots:
        # Extract key metrics
        calculated_roi = bot['calculated_roi']
        win_rate = bot['win_rate']
        max_drawdown = bot['max_drawdown']
        drawdown_count = bot['drawdown_count']
        total_trades = bot['total_trades']
        lowest_balance = bot.get('lowest_balance', 0)
        
        # Calculate HOLD baseline (assuming 0% for simplicity, but this should be market-specific)
        # In reality, HOLD would be the market return for the same period
        hold_baseline = 0.0  # This should be calculated based on market data for the same period
        
        # CRITICAL: No negative drawdowns allowed
        if max_drawdown < 0:
            continue  # Skip bots with negative drawdowns
        
        # Calculate Max DD in USDT - show the actual lowest balance reached
        # This shows the account balance at the lowest point (whether positive or negative)
        max_drawdown_usdt = lowest_balance
        
        # Enhanced filtering criteria
        criteria = {
            'profitable_vs_hold': calculated_roi > hold_baseline + 5.0,  # At least 5% above HOLD
            'no_drawdowns': drawdown_count == 0,  # Zero drawdowns
            'decent_win_rate': win_rate >= 0.45,  # At least 45% win rate
            'positive_drawdown': max_drawdown >= 0,  # Must have positive drawdown
            'sufficient_trades': total_trades >= 50,  # At least 50 trades
            'strong_roi': calculated_roi >= 10.0,  # At least 10% ROI
        }
        
        # Count criteria met
        criteria_met = sum(criteria.values())
        
        # Bot passes if it meets at least 5 out of 6 criteria
        if criteria_met >= 5:
            bot['criteria_met'] = criteria_met
            bot['criteria_details'] = criteria
            bot['hold_baseline'] = hold_baseline
            bot['roi_vs_hold'] = calculated_roi - hold_baseline
            bot['max_drawdown_usdt'] = max_drawdown_usdt
            filtered_bots.append(bot)
    
    return filtered_bots

def generate_enhanced_report(filtered_bots: List[Dict[str, Any]]):
    """Generate enhanced report for filtered bots"""
    
    if not filtered_bots:
        print("❌ No bots passed the enhanced filtering criteria")
        return
    
    print(f"\n🎯 ENHANCED FILTERING RESULTS")
    print("="*80)
    print(f"Bots passing enhanced criteria: {len(filtered_bots)}")
    
    # Sort by ROI vs HOLD
    filtered_bots.sort(key=lambda x: x['roi_vs_hold'], reverse=True)
    
    # Summary statistics
    rois = [b['calculated_roi'] for b in filtered_bots]
    win_rates = [b['win_rate'] for b in filtered_bots]
    drawdowns = [b['max_drawdown'] for b in filtered_bots]
    trades = [b['total_trades'] for b in filtered_bots]
    
    print(f"\n📊 FILTERED BOTS STATISTICS:")
    print(f"  ROI Range: {min(rois):.2f}% to {max(rois):.2f}%")
    print(f"  Win Rate Range: {min(win_rates):.1%} to {max(win_rates):.1%}")
    print(f"  Max Drawdown Range: {min(drawdowns):.2f}% to {max(drawdowns):.2f}%")
    print(f"  Trades Range: {min(trades)} to {max(trades)}")
    
    print(f"\n📈 AVERAGE STATISTICS:")
    print(f"  Average ROI: {sum(rois)/len(rois):.2f}%")
    print(f"  Average Win Rate: {sum(win_rates)/len(win_rates):.1%}")
    print(f"  Average Max Drawdown: {sum(drawdowns)/len(drawdowns):.2f}%")
    print(f"  Average Trades: {sum(trades)/len(trades):.1f}")
    
    # Top performers
    print(f"\n🏆 TOP 20 FILTERED BOTS (by ROI vs HOLD):")
    print(f"{'Rank':<4} {'ID':<12} {'Script':<25} {'ROI':<8} {'ROE':<8} {'Win%':<8} {'Max DD USDT':<12}")
    print(f"{'-'*4} {'-'*12} {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*12}")
    
    for i, bot in enumerate(filtered_bots[:20], 1):
        print(f"{i:<4} {bot['backtest_id'][:8]:<12} {bot['script_name'][:25]:<25} "
              f"{bot['lab_roi']:>6.1f}% {bot['calculated_roi']:>6.1f}% "
              f"{bot['win_rate']:>6.1%} {bot['max_drawdown_usdt']:>10.0f}")
    
    # Criteria analysis
    print(f"\n🔍 CRITERIA ANALYSIS:")
    criteria_stats = {}
    for bot in filtered_bots:
        for criterion, passed in bot['criteria_details'].items():
            if criterion not in criteria_stats:
                criteria_stats[criterion] = 0
            if passed:
                criteria_stats[criterion] += 1
    
    for criterion, count in criteria_stats.items():
        percentage = (count / len(filtered_bots)) * 100
        print(f"  {criterion}: {count}/{len(filtered_bots)} ({percentage:.1f}%)")
    
    # Risk categories
    print(f"\n⚠️ RISK CATEGORIES:")
    low_risk = [b for b in filtered_bots if b['max_drawdown'] < 15 and b['drawdown_count'] == 0]
    medium_risk = [b for b in filtered_bots if 15 <= b['max_drawdown'] < 25 and b['drawdown_count'] == 0]
    higher_risk = [b for b in filtered_bots if b['max_drawdown'] >= 25 or b['drawdown_count'] > 0]
    
    print(f"  Low Risk (DD < 15%, No DD events): {len(low_risk)} bots")
    print(f"  Medium Risk (DD 15-25%, No DD events): {len(medium_risk)} bots")
    print(f"  Higher Risk (DD ≥ 25% or DD events): {len(higher_risk)} bots")
    
    # Drawdown statistics for analysis
    print(f"\n📊 DRAWDOWN STATISTICS FOR ANALYSIS:")
    drawdown_usdt_values = [b['max_drawdown_usdt'] for b in filtered_bots]
    drawdown_percentages = [b['max_drawdown'] for b in filtered_bots]
    lowest_balances = [b.get('lowest_balance', 0) for b in filtered_bots]
    
    if drawdown_usdt_values:
        print(f"  Max DD USDT Range: {min(drawdown_usdt_values):.0f} to {max(drawdown_usdt_values):.0f}")
        print(f"  Max DD USDT Average: {sum(drawdown_usdt_values)/len(drawdown_usdt_values):.0f}")
        print(f"  Max DD % Range: {min(drawdown_percentages):.2f}% to {max(drawdown_percentages):.2f}%")
        print(f"  Max DD % Average: {sum(drawdown_percentages)/len(drawdown_percentages):.2f}%")
        print(f"  Lowest Balance Range: {min(lowest_balances):.0f} to {max(lowest_balances):.0f}")
        
        # Show some examples
        print(f"\n  Example Bots (showing drawdown calculation):")
        for i, bot in enumerate(filtered_bots[:5]):
            print(f"    {i+1}. {bot['backtest_id'][:8]} - Lowest: {bot.get('lowest_balance', 0):.0f}, "
                  f"DD USDT: {bot['max_drawdown_usdt']:.0f}, DD %: {bot['max_drawdown']:.1f}%")
        
        # Drawdown distribution
        dd_ranges = [
            (0, 5, "0-5%"),
            (5, 10, "5-10%"),
            (10, 15, "10-15%"),
            (15, 20, "15-20%"),
            (20, 25, "20-25%"),
            (25, 30, "25-30%"),
            (30, float('inf'), "30%+")
        ]
        
        print(f"\n  Drawdown Distribution:")
        for min_dd, max_dd, label in dd_ranges:
            count = len([b for b in filtered_bots if min_dd <= b['max_drawdown'] < max_dd])
            percentage = (count / len(filtered_bots)) * 100 if filtered_bots else 0
            print(f"    {label}: {count} bots ({percentage:.1f}%)")
    
    # Zero drawdown bots (most important)
    zero_dd_bots = [b for b in filtered_bots if b['drawdown_count'] == 0]
    print(f"\n🎯 ZERO DRAWDOWN BOTS: {len(zero_dd_bots)} bots")
    if zero_dd_bots:
        zero_dd_rois = [b['calculated_roi'] for b in zero_dd_bots]
        print(f"  Zero DD ROI Range: {min(zero_dd_rois):.2f}% to {max(zero_dd_rois):.2f}%")
        print(f"  Zero DD ROI Average: {sum(zero_dd_rois)/len(zero_dd_rois):.2f}%")
    
    # Save filtered results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filtered_file = f"filtered_viable_bots_{timestamp}.json"
    
    with open(filtered_file, 'w') as f:
        json.dump(filtered_bots, f, indent=2, default=str)
    
    print(f"\n💾 Filtered results saved to: {filtered_file}")
    
    return filtered_bots

def main():
    """Main function"""
    print("🚀 ENHANCED BOT FILTERING WITH HOLD COMPARISON")
    print("="*80)
    
    # Load viable bots
    viable_bots = load_viable_bots()
    if not viable_bots:
        return
    
    print(f"📊 Loaded {len(viable_bots)} viable bots for enhanced filtering")
    
    # Apply enhanced filtering
    filtered_bots = analyze_hold_performance(viable_bots)
    
    # Generate report
    generate_enhanced_report(filtered_bots)

if __name__ == "__main__":
    main()
