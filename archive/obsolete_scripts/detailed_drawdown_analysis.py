#!/usr/bin/env python3
"""
Detailed drawdown analysis for the filtered viable bots
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def load_filtered_bots():
    """Load the filtered viable bots"""
    # Find the most recent filtered bots file
    filtered_files = list(Path('.').glob('filtered_viable_bots_*.json'))
    if not filtered_files:
        print("❌ No filtered bots file found. Run filter_viable_bots.py first.")
        return []
    
    # Get the most recent file
    latest_file = max(filtered_files, key=lambda x: x.stat().st_mtime)
    print(f"📁 Loading filtered bots from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        return json.load(f)

def analyze_drawdown_patterns(filtered_bots: List[Dict[str, Any]]):
    """Analyze drawdown patterns for statistical insights"""
    
    print(f"\n📊 DETAILED DRAWDOWN ANALYSIS")
    print("="*80)
    
    # Separate bots by drawdown characteristics
    zero_dd_bots = [b for b in filtered_bots if b['drawdown_count'] == 0]
    low_dd_bots = [b for b in filtered_bots if 0 < b['max_drawdown'] < 20]
    medium_dd_bots = [b for b in filtered_bots if 20 <= b['max_drawdown'] < 50]
    high_dd_bots = [b for b in filtered_bots if b['max_drawdown'] >= 50]
    
    print(f"🎯 DRAWDOWN CATEGORIES:")
    print(f"  Zero Drawdowns: {len(zero_dd_bots)} bots")
    print(f"  Low Drawdowns (0-20%): {len(low_dd_bots)} bots")
    print(f"  Medium Drawdowns (20-50%): {len(medium_dd_bots)} bots")
    print(f"  High Drawdowns (50%+): {len(high_dd_bots)} bots")
    
    # Analyze each category
    categories = [
        ("Zero Drawdowns", zero_dd_bots),
        ("Low Drawdowns", low_dd_bots),
        ("Medium Drawdowns", medium_dd_bots),
        ("High Drawdowns", high_dd_bots)
    ]
    
    for category_name, bots in categories:
        if not bots:
            continue
            
        print(f"\n📈 {category_name.upper()} ANALYSIS:")
        rois = [b['calculated_roi'] for b in bots]
        win_rates = [b['win_rate'] for b in bots]
        trades = [b['total_trades'] for b in bots]
        
        print(f"  Count: {len(bots)} bots")
        print(f"  ROI Range: {min(rois):.2f}% to {max(rois):.2f}%")
        print(f"  ROI Average: {sum(rois)/len(rois):.2f}%")
        print(f"  Win Rate Range: {min(win_rates):.1%} to {max(win_rates):.1%}")
        print(f"  Win Rate Average: {sum(win_rates)/len(win_rates):.1%}")
        print(f"  Trades Range: {min(trades)} to {max(trades)}")
        print(f"  Trades Average: {sum(trades)/len(trades):.1f}")
        
        # Show top 5 in each category
        top_bots = sorted(bots, key=lambda x: x['calculated_roi'], reverse=True)[:5]
        print(f"  Top 5 by ROI:")
        for i, bot in enumerate(top_bots, 1):
            print(f"    {i}. {bot['backtest_id'][:8]} - ROI: {bot['calculated_roi']:.2f}%, "
                  f"Win: {bot['win_rate']:.1%}, DD: {bot['max_drawdown']:.2f}%, "
                  f"Trades: {bot['total_trades']}")

def show_recommended_bots(filtered_bots: List[Dict[str, Any]]):
    """Show recommended bots based on conservative criteria"""
    
    print(f"\n🎯 RECOMMENDED BOTS FOR LIVE TRADING")
    print("="*80)
    
    # Conservative criteria: Zero drawdowns, good win rate, reasonable ROI
    recommended = [
        b for b in filtered_bots 
        if b['drawdown_count'] == 0 
        and b['win_rate'] >= 0.45 
        and b['calculated_roi'] >= 20.0
        and b['total_trades'] >= 100
    ]
    
    # Sort by ROI
    recommended.sort(key=lambda x: x['calculated_roi'], reverse=True)
    
    print(f"Conservative Criteria: Zero DD + Win Rate ≥45% + ROI ≥20% + Trades ≥100")
    print(f"Recommended Bots: {len(recommended)}")
    
    if recommended:
        print(f"\n🏆 TOP 15 RECOMMENDED BOTS:")
        print(f"{'Rank':<4} {'ID':<12} {'Script':<25} {'ROI':<8} {'ROE':<8} {'Win%':<8} {'Trades':<8}")
        print(f"{'-'*4} {'-'*12} {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        
        for i, bot in enumerate(recommended[:15], 1):
            print(f"{i:<4} {bot['backtest_id'][:8]:<12} {bot['script_name'][:25]:<25} "
                  f"{bot['lab_roi']:>6.1f}% {bot['calculated_roi']:>6.1f}% "
                  f"{bot['win_rate']:>6.1%} {bot['total_trades']:>6}")
    
    # Ultra-conservative criteria
    ultra_conservative = [
        b for b in filtered_bots 
        if b['drawdown_count'] == 0 
        and b['win_rate'] >= 0.50 
        and b['calculated_roi'] >= 30.0
        and b['total_trades'] >= 150
    ]
    
    ultra_conservative.sort(key=lambda x: x['calculated_roi'], reverse=True)
    
    print(f"\n🛡️ ULTRA-CONSERVATIVE BOTS:")
    print(f"Ultra-Conservative Criteria: Zero DD + Win Rate ≥50% + ROI ≥30% + Trades ≥150")
    print(f"Ultra-Conservative Bots: {len(ultra_conservative)}")
    
    if ultra_conservative:
        print(f"\n🏆 ULTRA-CONSERVATIVE BOTS:")
        print(f"{'Rank':<4} {'ID':<12} {'Script':<25} {'ROI':<8} {'ROE':<8} {'Win%':<8} {'Trades':<8}")
        print(f"{'-'*4} {'-'*12} {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        
        for i, bot in enumerate(ultra_conservative, 1):
            print(f"{i:<4} {bot['backtest_id'][:8]:<12} {bot['script_name'][:25]:<25} "
                  f"{bot['lab_roi']:>6.1f}% {bot['calculated_roi']:>6.1f}% "
                  f"{bot['win_rate']:>6.1%} {bot['total_trades']:>6}")

def main():
    """Main function"""
    print("🚀 DETAILED DRAWDOWN ANALYSIS FOR VIABLE BOTS")
    print("="*80)
    
    # Load filtered bots
    filtered_bots = load_filtered_bots()
    if not filtered_bots:
        return
    
    print(f"📊 Loaded {len(filtered_bots)} filtered bots for detailed analysis")
    
    # Analyze drawdown patterns
    analyze_drawdown_patterns(filtered_bots)
    
    # Show recommended bots
    show_recommended_bots(filtered_bots)
    
    # Save detailed analysis
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    analysis_file = f"detailed_drawdown_analysis_{timestamp}.json"
    
    analysis_data = {
        'timestamp': timestamp,
        'total_bots': len(filtered_bots),
        'zero_dd_bots': len([b for b in filtered_bots if b['drawdown_count'] == 0]),
        'low_dd_bots': len([b for b in filtered_bots if 0 < b['max_drawdown'] < 20]),
        'medium_dd_bots': len([b for b in filtered_bots if 20 <= b['max_drawdown'] < 50]),
        'high_dd_bots': len([b for b in filtered_bots if b['max_drawdown'] >= 50]),
        'recommended_bots': [b for b in filtered_bots if b['drawdown_count'] == 0 and b['win_rate'] >= 0.45 and b['calculated_roi'] >= 20.0 and b['total_trades'] >= 100],
        'ultra_conservative_bots': [b for b in filtered_bots if b['drawdown_count'] == 0 and b['win_rate'] >= 0.50 and b['calculated_roi'] >= 30.0 and b['total_trades'] >= 150]
    }
    
    with open(analysis_file, 'w') as f:
        json.dump(analysis_data, f, indent=2, default=str)
    
    print(f"\n💾 Detailed analysis saved to: {analysis_file}")

if __name__ == "__main__":
    main()
