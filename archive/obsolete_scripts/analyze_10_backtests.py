#!/usr/bin/env python3
"""
Analyze 10 backtests from cache with enhanced features and generate a comprehensive report
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reanalyze_cached_backtests import load_cached_backtest_data, extract_lab_id_from_filename, reanalyze_backtest_with_enhanced_features
from pathlib import Path
import json
from datetime import datetime

def analyze_10_backtests():
    """Analyze 10 backtests and generate a comprehensive report"""
    
    # Get all cached backtest files
    cache_dir = Path('unified_cache/backtests')
    backtest_files = list(cache_dir.glob('*.json'))
    
    print(f"Found {len(backtest_files)} cached backtests")
    
    # Analyze first 10 files
    results = []
    for i, cache_file in enumerate(backtest_files[:10]):
        print(f"\n{'='*60}")
        print(f"ANALYZING BACKTEST {i+1}/10: {cache_file.name}")
        print(f"{'='*60}")
        
        try:
            # Load and analyze
            cached_data = load_cached_backtest_data(cache_file)
            lab_id = extract_lab_id_from_filename(cache_file.name)
            
            print(f"Lab ID: {lab_id}")
            print(f"Original ROI: {cached_data.get('roi_percentage', 0):.2f}%")
            print(f"Total Trades: {cached_data.get('total_trades', 0)}")
            print(f"Max Drawdown: {cached_data.get('max_drawdown', 0):.2f}%")
            
            # Reanalyze with enhanced features
            enhanced_analysis = reanalyze_backtest_with_enhanced_features(cached_data, lab_id)
            
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
                'drawdown_events': len(enhanced_analysis.drawdown_analysis.drawdown_events) if enhanced_analysis.drawdown_analysis else 0
            }
            results.append(result)
            
            # Display results
            print(f"\n=== ENHANCED ANALYSIS RESULTS ===")
            print(f"Lab ROI: {enhanced_analysis.roi_percentage:.2f}%")
            print(f"ROE (Calculated ROI): {enhanced_analysis.calculated_roi_percentage:.2f}%")
            print(f"ROI Difference: {enhanced_analysis.roi_difference:.2f}%")
            print(f"Win Rate: {enhanced_analysis.win_rate:.1%}")
            print(f"Max Drawdown: {enhanced_analysis.max_drawdown:.2f}%")
            print(f"Total Trades: {enhanced_analysis.total_trades}")
            
            if enhanced_analysis.drawdown_analysis:
                dd = enhanced_analysis.drawdown_analysis
                print(f"\n=== DRAWDOWN ANALYSIS ===")
                print(f"Drawdown Count: {dd.drawdown_count}")
                print(f"Lowest Balance: {dd.lowest_balance:.2f}")
                print(f"Max Drawdown %: {dd.max_drawdown_percentage:.2f}%")
                
                if dd.drawdown_events:
                    print(f"\nFirst 3 Drawdown Events:")
                    for j, event in enumerate(dd.drawdown_events[:3]):
                        print(f"  {j+1}. {event.timestamp} - Balance: {event.balance:.2f}, DD: {event.drawdown_amount:.2f}")
                    
                    if len(dd.drawdown_events) > 3:
                        print(f"  ... and {len(dd.drawdown_events) - 3} more drawdown events")
            else:
                print('\nNo drawdown analysis available')
                
        except Exception as e:
            print(f"❌ Error analyzing {cache_file.name}: {e}")
            continue
    
    # Generate comprehensive report
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE ANALYSIS REPORT - {len(results)} BACKTESTS")
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
    print(f"  Lab ROI Range: {min(lab_rois):.2f}% to {max(lab_rois):.2f}%")
    print(f"  Calculated ROI Range: {min(calculated_rois):.2f}% to {max(calculated_rois):.2f}%")
    print(f"  ROI Difference Range: {min(roi_differences):.2f}% to {max(roi_differences):.2f}%")
    print(f"  Win Rate Range: {min(win_rates):.1%} to {max(win_rates):.1%}")
    print(f"  Max Drawdown Range: {min(max_drawdowns):.2f}% to {max(max_drawdowns):.2f}%")
    print(f"  Drawdown Count Range: {min(drawdown_counts)} to {max(drawdown_counts)}")
    
    # Average statistics
    print(f"\n📈 AVERAGE STATISTICS:")
    print(f"  Average Lab ROI: {sum(lab_rois)/len(lab_rois):.2f}%")
    print(f"  Average Calculated ROI: {sum(calculated_rois)/len(calculated_rois):.2f}%")
    print(f"  Average ROI Difference: {sum(roi_differences)/len(roi_differences):.2f}%")
    print(f"  Average Win Rate: {sum(win_rates)/len(win_rates):.1%}")
    print(f"  Average Max Drawdown: {sum(max_drawdowns)/len(max_drawdowns):.2f}%")
    print(f"  Average Drawdown Count: {sum(drawdown_counts)/len(drawdown_counts):.1f}")
    
    # Detailed results table
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'ID':<12} {'Script':<25} {'Lab ROI':<10} {'ROE':<10} {'Diff':<10} {'Win%':<8} {'Max DD':<8} {'DD Count':<8}")
    print(f"{'-'*12} {'-'*25} {'-'*10} {'-'*10} {'-'*10} {'-'*8} {'-'*8} {'-'*8}")
    
    for result in results:
        print(f"{result['backtest_id'][:8]:<12} {result['script_name'][:25]:<25} "
              f"{result['lab_roi']:>8.2f}% {result['calculated_roi']:>8.2f}% "
              f"{result['roi_difference']:>8.2f}% {result['win_rate']:>6.1%} "
              f"{result['max_drawdown']:>6.2f}% {result['drawdown_count']:>6}")
    
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
    
    # Save detailed report to file
    report_file = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed report saved to: {report_file}")

if __name__ == "__main__":
    analyze_10_backtests()
