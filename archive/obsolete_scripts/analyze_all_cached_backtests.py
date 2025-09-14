#!/usr/bin/env python3
"""
Analyze all cached backtests and generate comprehensive report
"""

from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.robustness import StrategyRobustnessAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
import os
import json
from collections import defaultdict

def main():
    # Initialize components
    cache = UnifiedCacheManager()
    analyzer = HaasAnalyzer(cache)
    robustness_analyzer = StrategyRobustnessAnalyzer(cache)

    print('Analyzing all cached backtests...')
    
    # Get all cached files
    cache_dir = "unified_cache/backtests"
    if not os.path.exists(cache_dir):
        print("Cache directory not found")
        return
    
    files = os.listdir(cache_dir)
    print(f'Found {len(files)} cached backtests')
    
    # Analyze each cached backtest
    all_robustness_results = {}
    lab_stats = defaultdict(list)
    
    for i, filename in enumerate(files):
        if i % 100 == 0:
            print(f'Processing {i}/{len(files)} backtests...')
            
        try:
            # Extract lab_id and backtest_id from filename
            if '_' in filename:
                parts = filename.replace('.json', '').split('_', 1)
                lab_id = parts[0]
                backtest_id = parts[1]
                
                # Load cached data
                cached_data = cache.load_backtest_cache(lab_id, backtest_id)
                if cached_data:
                    # Create BacktestAnalysis from cached data
                    backtest_analysis = analyzer._create_analysis_from_cache(cached_data, lab_id, None)
                    
                    # Run robustness analysis
                    robustness_metrics = robustness_analyzer.analyze_backtest_robustness(backtest_analysis)
                    all_robustness_results[backtest_id] = robustness_metrics
                    
                    # Track lab statistics
                    lab_stats[lab_id].append({
                        'backtest_id': backtest_id,
                        'roi': backtest_analysis.roi_percentage,
                        'calculated_roi': backtest_analysis.calculated_roi_percentage,
                        'win_rate': backtest_analysis.win_rate,
                        'starting_balance': backtest_analysis.starting_balance,
                        'final_balance': backtest_analysis.final_balance,
                        'robustness_score': robustness_metrics.robustness_score,
                        'risk_level': robustness_metrics.risk_level
                    })
                    
        except Exception as e:
            print(f'Error processing {filename}: {e}')
            continue
    
    print(f'\nAnalyzed {len(all_robustness_results)} backtests from {len(lab_stats)} labs')
    
    # Generate comprehensive report
    report = []
    report.append("=" * 100)
    report.append("COMPREHENSIVE ROBUSTNESS ANALYSIS REPORT")
    report.append("=" * 100)
    report.append(f"Total Backtests Analyzed: {len(all_robustness_results)}")
    report.append(f"Total Labs: {len(lab_stats)}")
    report.append("")
    
    # Summary statistics
    all_scores = [metrics.robustness_score for metrics in all_robustness_results.values()]
    all_risk_levels = [metrics.risk_level for metrics in all_robustness_results.values()]
    all_starting_balances = [metrics.starting_balance for metrics in all_robustness_results.values()]
    all_final_balances = [metrics.final_balance for metrics in all_robustness_results.values()]
    
    report.append("OVERALL SUMMARY STATISTICS:")
    report.append("-" * 50)
    report.append(f"Average Robustness Score: {sum(all_scores) / len(all_scores):.1f}/100")
    report.append(f"Highest Robustness Score: {max(all_scores):.1f}/100")
    report.append(f"Lowest Robustness Score: {min(all_scores):.1f}/100")
    report.append("")
    
    # Balance statistics
    non_zero_starting = [b for b in all_starting_balances if b > 0]
    non_zero_final = [b for b in all_final_balances if b > 0]
    
    report.append("BALANCE STATISTICS:")
    report.append("-" * 50)
    report.append(f"Backtests with non-zero starting balance: {len(non_zero_starting)}/{len(all_starting_balances)}")
    report.append(f"Backtests with non-zero final balance: {len(non_zero_final)}/{len(all_final_balances)}")
    if non_zero_starting:
        report.append(f"Average starting balance: {sum(non_zero_starting) / len(non_zero_starting):.0f} USDT")
        report.append(f"Range: {min(non_zero_starting):.0f} - {max(non_zero_starting):.0f} USDT")
    if non_zero_final:
        report.append(f"Average final balance: {sum(non_zero_final) / len(non_zero_final):.0f} USDT")
        report.append(f"Range: {min(non_zero_final):.0f} - {max(non_zero_final):.0f} USDT")
    report.append("")
    
    # Risk level distribution
    risk_distribution = {}
    for risk_level in all_risk_levels:
        risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
    
    report.append("RISK LEVEL DISTRIBUTION:")
    report.append("-" * 50)
    for risk_level, count in risk_distribution.items():
        percentage = (count / len(all_risk_levels)) * 100
        report.append(f"{risk_level}: {count} backtests ({percentage:.1f}%)")
    report.append("")
    
    # Top performing backtests
    sorted_backtests = sorted(all_robustness_results.items(), 
                            key=lambda x: x[1].robustness_score, reverse=True)
    
    report.append("TOP 10 ROBUST BACKTESTS:")
    report.append("-" * 50)
    for i, (backtest_id, metrics) in enumerate(sorted_backtests[:10]):
        report.append(f"{i+1:2d}. Backtest: {backtest_id[:8]}...")
        report.append(f"    Lab ROI: {metrics.overall_roi:.1f}% | Calculated ROI: {metrics.calculated_roi:.1f}%")
        report.append(f"    Win Rate: {metrics.win_rate:.1%} | Max Drawdown: {metrics.drawdown_analysis.max_drawdown_percentage:.1f}%")
        report.append(f"    Balance: Starting={metrics.starting_balance:.0f} USDT | Max DD={metrics.drawdown_analysis.lowest_balance:.0f} USDT | Final={metrics.final_balance:.0f} USDT")
        report.append(f"    Robustness Score: {metrics.robustness_score:.1f}/100 | Risk: {metrics.risk_level}")
        report.append("")
    
    # Lab performance summary
    report.append("LAB PERFORMANCE SUMMARY:")
    report.append("-" * 50)
    lab_performance = []
    for lab_id, backtests in lab_stats.items():
        if backtests:
            avg_roi = sum(bt['roi'] for bt in backtests) / len(backtests)
            avg_robustness = sum(bt['robustness_score'] for bt in backtests) / len(backtests)
            best_robustness = max(bt['robustness_score'] for bt in backtests)
            lab_performance.append({
                'lab_id': lab_id,
                'backtest_count': len(backtests),
                'avg_roi': avg_roi,
                'avg_robustness': avg_robustness,
                'best_robustness': best_robustness
            })
    
    # Sort labs by best robustness score
    lab_performance.sort(key=lambda x: x['best_robustness'], reverse=True)
    
    for i, lab in enumerate(lab_performance[:10]):
        report.append(f"{i+1:2d}. Lab: {lab['lab_id'][:8]}...")
        report.append(f"    Backtests: {lab['backtest_count']} | Avg ROI: {lab['avg_roi']:.1f}%")
        report.append(f"    Avg Robustness: {lab['avg_robustness']:.1f}/100 | Best: {lab['best_robustness']:.1f}/100")
        report.append("")
    
    # Save report to file
    report_text = "\n".join(report)
    with open("comprehensive_robustness_report.txt", "w") as f:
        f.write(report_text)
    
    print("\n" + report_text)
    print(f"\nReport saved to: comprehensive_robustness_report.txt")

if __name__ == '__main__':
    main()
