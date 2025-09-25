#!/usr/bin/env python3
"""
Direct analysis of cached backtest data and bot creation
Works with the cached data we have from multiple servers
"""

import json
import os
import glob
from collections import defaultdict
from typing import Dict, List, Any
import time

def analyze_cached_labs():
    """Analyze all cached lab data and find top performers"""
    
    cache_dir = "unified_cache/backtests"
    if not os.path.exists(cache_dir):
        print("❌ No cache directory found")
        return
    
    # Group files by lab ID
    lab_data = defaultdict(list)
    
    print("🔍 Scanning cached backtest files...")
    for file_path in glob.glob(f"{cache_dir}/*.json"):
        filename = os.path.basename(file_path)
        lab_id = filename.split('_')[0]
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                lab_data[lab_id].append({
                    'file': filename,
                    'data': data
                })
        except Exception as e:
            print(f"⚠️ Error reading {filename}: {e}")
    
    print(f"📊 Found {len(lab_data)} labs with cached data")
    
    # Analyze each lab
    lab_analysis = []
    
    for lab_id, backtests in lab_data.items():
        print(f"\n🔬 Analyzing lab {lab_id} ({len(backtests)} backtests)...")
        
        lab_results = []
        
        for backtest in backtests:
            try:
                data = backtest['data']
                
                # Extract key metrics from the cached data
                reports = data.get('Reports', {})
                if not reports:
                    continue
                
                # Get the first report (usually the main one)
                report_key = list(reports.keys())[0]
                report = reports[report_key]
                
                # Extract performance metrics
                roi = report.get('ROI', 0)
                win_rate = report.get('WinRate', 0)
                total_trades = report.get('TotalTrades', 0)
                max_drawdown = report.get('MaxDrawdown', 0)
                profit_factor = report.get('ProfitFactor', 0)
                
                # Extract script and market info
                script_name = "ADX BB STOCH Scalper"  # Default from lab names
                market_tag = report_key.split('_')[-1] if '_' in report_key else "UNKNOWN"
                
                # Create analysis result
                result = {
                    'lab_id': lab_id,
                    'backtest_id': backtest['file'].split('_')[1].replace('.json', ''),
                    'script_name': script_name,
                    'market_tag': market_tag,
                    'roi_percentage': roi,
                    'win_rate': win_rate,
                    'total_trades': total_trades,
                    'max_drawdown': max_drawdown,
                    'profit_factor': profit_factor,
                    'realized_profits_usdt': roi * 10000 / 100 if roi > 0 else 0  # Estimate
                }
                
                lab_results.append(result)
                
            except Exception as e:
                print(f"⚠️ Error analyzing backtest {backtest['file']}: {e}")
                continue
        
        if lab_results:
            # Sort by ROI
            lab_results.sort(key=lambda x: x['roi_percentage'], reverse=True)
            
            lab_summary = {
                'lab_id': lab_id,
                'total_backtests': len(lab_results),
                'top_backtests': lab_results[:5],  # Top 5
                'best_roi': lab_results[0]['roi_percentage'] if lab_results else 0,
                'best_win_rate': max(bt['win_rate'] for bt in lab_results) if lab_results else 0
            }
            
            lab_analysis.append(lab_summary)
            
            print(f"  ✅ Found {len(lab_results)} valid backtests")
            print(f"  🏆 Best ROI: {lab_summary['best_roi']:.2f}%")
            print(f"  🎯 Best Win Rate: {lab_summary['best_win_rate']:.2f}%")
    
    # Sort labs by best ROI
    lab_analysis.sort(key=lambda x: x['best_roi'], reverse=True)
    
    print(f"\n📊 ANALYSIS SUMMARY")
    print(f"=" * 60)
    print(f"Total Labs Analyzed: {len(lab_analysis)}")
    
    for i, lab in enumerate(lab_analysis[:10], 1):  # Top 10 labs
        print(f"{i:2d}. Lab {lab['lab_id'][:8]}... - ROI: {lab['best_roi']:6.2f}% - Win Rate: {lab['best_win_rate']:5.2f}% - Backtests: {lab['total_backtests']}")
    
    return lab_analysis

def create_bot_creation_script(lab_analysis):
    """Create a script to generate bots from the analysis"""
    
    print(f"\n🤖 BOT CREATION RECOMMENDATIONS")
    print(f"=" * 60)
    
    bot_commands = []
    
    for lab in lab_analysis[:5]:  # Top 5 labs
        lab_id = lab['lab_id']
        top_backtests = lab['top_backtests'][:2]  # Top 2 from each lab
        
        print(f"\n📋 Lab {lab_id[:8]}... (Best ROI: {lab['best_roi']:.2f}%)")
        
        for i, backtest in enumerate(top_backtests, 1):
            bot_name = f"{lab_id[:8]} - {backtest['script_name']} - {backtest['roi_percentage']:.1f}% pop/gen {backtest['win_rate']:.0f}%"
            
            print(f"  {i}. {bot_name}")
            print(f"     ROI: {backtest['roi_percentage']:6.2f}% | Win Rate: {backtest['win_rate']:5.2f}% | Trades: {backtest['total_trades']}")
            
            # Create bot creation command
            command = {
                'lab_id': lab_id,
                'backtest_id': backtest['backtest_id'],
                'bot_name': bot_name,
                'market_tag': backtest['market_tag'],
                'roi': backtest['roi_percentage'],
                'win_rate': backtest['win_rate']
            }
            bot_commands.append(command)
    
    # Save recommendations to file
    with open('bot_creation_recommendations.json', 'w') as f:
        json.dump(bot_commands, f, indent=2)
    
    print(f"\n💾 Saved {len(bot_commands)} bot creation recommendations to 'bot_creation_recommendations.json'")
    
    return bot_commands

if __name__ == "__main__":
    print("🚀 Starting cached lab analysis...")
    
    # Analyze cached data
    lab_analysis = analyze_cached_labs()
    
    if lab_analysis:
        # Create bot recommendations
        bot_commands = create_bot_creation_script(lab_analysis)
        
        print(f"\n✅ Analysis complete!")
        print(f"📊 Analyzed {len(lab_analysis)} labs")
        print(f"🤖 Generated {len(bot_commands)} bot creation recommendations")
        print(f"\n💡 Next steps:")
        print(f"   1. Review the recommendations in 'bot_creation_recommendations.json'")
        print(f"   2. Connect to your HaasOnline server")
        print(f"   3. Use the mass bot creator with specific lab IDs")
    else:
        print("❌ No valid lab data found in cache")




