#!/usr/bin/env python3
"""
Analyze ALL backtests in cache to identify viable bots for live trading
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reanalyze_cached_backtests import load_cached_backtest_data, extract_lab_id_from_filename, reanalyze_backtest_with_enhanced_features
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any

def analyze_all_backtests():
    """Analyze all backtests and identify viable bots"""
    
    # Get all cached backtest files
    cache_dir = Path('unified_cache/backtests')
    backtest_files = list(cache_dir.glob('*.json'))
    
    print(f"🔍 Found {len(backtest_files)} cached backtests")
    print(f"🚀 Starting comprehensive analysis...")
    
    results = []
    viable_bots = []
    processed = 0
    
    for i, cache_file in enumerate(backtest_files):
        if i % 100 == 0:
            print(f"📊 Progress: {i}/{len(backtest_files)} ({i/len(backtest_files)*100:.1f}%)")
        
        try:
            # Load and analyze
            cached_data = load_cached_backtest_data(cache_file)
            lab_id = extract_lab_id_from_filename(cache_file.name)
            
            # Skip if no meaningful data
            if cached_data.get('total_trades', 0) == 0:
                continue
            
            # Reanalyze with enhanced features
            enhanced_analysis = reanalyze_backtest_with_enhanced_features(cached_data, lab_id)
            
            if not enhanced_analysis:
                continue
            
            # Store results
            result = {
                'backtest_id': enhanced_analysis.backtest_id,
                'lab_id': lab_id,
                'script_name': enhanced_analysis.script_name,
                'lab_roi': enhanced_analysis.roi_percentage,
                'calculated_roi': enhanced_analysis.calculated_roi_percentage,
                'roi_difference': enhanced_analysis.roi_difference,
                'win_rate': enhanced_analysis.win_rate,
                'max_drawdown': enhanced_analysis.max_drawdown,
                'total_trades': enhanced_analysis.total_trades,
                'drawdown_count': enhanced_analysis.drawdown_analysis.drawdown_count if enhanced_analysis.drawdown_analysis else 0,
                'lowest_balance': enhanced_analysis.drawdown_analysis.lowest_balance if enhanced_analysis.drawdown_analysis else 0,
                'drawdown_events': len(enhanced_analysis.drawdown_analysis.drawdown_events) if enhanced_analysis.drawdown_analysis else 0,
                'profit_factor': enhanced_analysis.profit_factor,
                'sharpe_ratio': enhanced_analysis.sharpe_ratio
            }
            results.append(result)
            
            # Check if bot is viable
            if is_bot_viable(result):
                viable_bots.append(result)
            
            processed += 1
            
        except Exception as e:
            print(f"❌ Error analyzing {cache_file.name}: {e}")
            continue
    
    # Generate comprehensive report
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE ANALYSIS REPORT - {processed} BACKTESTS ANALYZED")
    print(f"{'='*80}")
    
    if not results:
        print("No results to report")
        return
    
    # Summary statistics
    lab_rois = [r['lab_roi'] for r in results]
    calculated_rois = [r['calculated_roi'] for r in results]
    roi_differences = [r['roi_difference'] for r in results]
    win_rates = [r['win_rate'] for r in results]
    max_drawdowns = [r['max_drawdown'] for r in results]
    drawdown_counts = [r['drawdown_count'] for r in results]
    
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"  Total Backtests Analyzed: {len(results)}")
    print(f"  Viable Bots Found: {len(viable_bots)}")
    print(f"  Viability Rate: {len(viable_bots)/len(results)*100:.1f}%")
    print(f"  Lab ROI Range: {min(lab_rois):.2f}% to {max(lab_rois):.2f}%")
    print(f"  Calculated ROI Range: {min(calculated_rois):.2f}% to {max(calculated_rois):.2f}%")
    print(f"  Win Rate Range: {min(win_rates):.1%} to {max(win_rates):.1%}")
    print(f"  Max Drawdown Range: {min(max_drawdowns):.2f}% to {max(max_drawdowns):.2f}%")
    print(f"  Drawdown Count Range: {min(drawdown_counts)} to {max(drawdown_counts)}")
    
    # Average statistics
    print(f"\n📈 AVERAGE STATISTICS:")
    print(f"  Average Lab ROI: {sum(lab_rois)/len(lab_rois):.2f}%")
    print(f"  Average Calculated ROI: {sum(calculated_rois)/len(calculated_rois):.2f}%")
    print(f"  Average Win Rate: {sum(win_rates)/len(win_rates):.1%}")
    print(f"  Average Max Drawdown: {sum(max_drawdowns)/len(max_drawdowns):.2f}%")
    print(f"  Average Drawdown Count: {sum(drawdown_counts)/len(drawdown_counts):.1f}")
    
    # Viable bots analysis
    if viable_bots:
        print(f"\n🎯 VIABLE BOTS ANALYSIS ({len(viable_bots)} bots):")
        viable_rois = [b['calculated_roi'] for b in viable_bots]
        viable_win_rates = [b['win_rate'] for b in viable_bots]
        viable_drawdowns = [b['max_drawdown'] for b in viable_bots]
        
        print(f"  Average Viable ROI: {sum(viable_rois)/len(viable_rois):.2f}%")
        print(f"  Average Viable Win Rate: {sum(viable_win_rates)/len(viable_win_rates):.1%}")
        print(f"  Average Viable Max Drawdown: {sum(viable_drawdowns)/len(viable_drawdowns):.2f}%")
        
        # Top 10 viable bots
        print(f"\n🏆 TOP 10 VIABLE BOTS:")
        viable_bots_sorted = sorted(viable_bots, key=lambda x: x['calculated_roi'], reverse=True)[:10]
        
        print(f"{'Rank':<4} {'ID':<12} {'Script':<25} {'ROE':<10} {'Win%':<8} {'Max DD':<8} {'DD Count':<8} {'Trades':<8}")
        print(f"{'-'*4} {'-'*12} {'-'*25} {'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        
        for i, bot in enumerate(viable_bots_sorted, 1):
            print(f"{i:<4} {bot['backtest_id'][:8]:<12} {bot['script_name'][:25]:<25} "
                  f"{bot['calculated_roi']:>8.2f}% {bot['win_rate']:>6.1%} "
                  f"{bot['max_drawdown']:>6.2f}% {bot['drawdown_count']:>6} {bot['total_trades']:>6}")
    
    # Key insights
    print(f"\n🔍 KEY INSIGHTS:")
    
    # ROI discrepancies
    large_discrepancies = [r for r in results if r['roi_difference'] > 100]
    print(f"  • {len(large_discrepancies)} backtests have ROI differences > 100%")
    
    # Profitable vs unprofitable
    profitable_lab = [r for r in results if r['lab_roi'] > 0]
    profitable_calc = [r for r in results if r['calculated_roi'] > 0]
    print(f"  • Lab data shows {len(profitable_lab)} profitable backtests")
    print(f"  • Calculated ROI shows {len(profitable_calc)} profitable backtests")
    
    # High drawdown backtests
    high_drawdown = [r for r in results if r['max_drawdown'] > 50]
    print(f"  • {len(high_drawdown)} backtests have max drawdown > 50%")
    
    # High drawdown count
    high_dd_count = [r for r in results if r['drawdown_count'] > 10]
    print(f"  • {len(high_dd_count)} backtests have > 10 drawdown events")
    
    # Save detailed reports
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # All results
    all_report_file = f"all_backtests_analysis_{timestamp}.json"
    with open(all_report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Viable bots only
    viable_report_file = f"viable_bots_{timestamp}.json"
    with open(viable_report_file, 'w') as f:
        json.dump(viable_bots, f, indent=2, default=str)
    
    print(f"\n💾 Reports saved:")
    print(f"  • All backtests: {all_report_file}")
    print(f"  • Viable bots: {viable_report_file}")
    
    return results, viable_bots

def is_bot_viable(result: Dict[str, Any]) -> bool:
    """Determine if a bot is viable for live trading based on multiple criteria"""
    
    # Criteria for viable bots
    criteria = {
        'profitable': result['calculated_roi'] > 0,  # Must be profitable
        'decent_win_rate': result['win_rate'] > 0.4,  # At least 40% win rate
        'reasonable_drawdown': result['max_drawdown'] < 50,  # Max drawdown under 50%
        'low_drawdown_count': result['drawdown_count'] < 15,  # Less than 15 drawdown events
        'sufficient_trades': result['total_trades'] >= 50,  # At least 50 trades for statistical significance
        'positive_sharpe': result.get('sharpe_ratio', 0) > 0,  # Positive Sharpe ratio if available
    }
    
    # Count how many criteria are met
    criteria_met = sum(criteria.values())
    
    # Bot is viable if it meets at least 4 out of 6 criteria
    # and must be profitable
    return criteria_met >= 4 and criteria['profitable']

if __name__ == "__main__":
    results, viable_bots = analyze_all_backtests()
