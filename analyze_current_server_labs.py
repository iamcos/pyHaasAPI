#!/usr/bin/env python3
"""
Analyze labs that are currently available on the server
Only process labs that exist on the current server from our cached data
"""

import json
import os
import glob
from collections import defaultdict
from typing import Dict, List, Any
from pyHaasAPI import api
from dotenv import load_dotenv

def get_current_server_labs():
    """Get labs currently available on the server"""
    try:
        load_dotenv()
        
        # Create API connection
        haas_api = api.RequestsExecutor(
            host='127.0.0.1',
            port=8090,
            state=api.Guest()
        )
        
        # Authenticate
        executor = haas_api.authenticate(
            os.getenv('API_EMAIL'), 
            os.getenv('API_PASSWORD')
        )
        
        # Get all labs
        all_labs = api.get_all_labs(executor)
        
        # Filter for complete labs only
        complete_labs = []
        for lab in all_labs:
            if hasattr(lab, 'status') and hasattr(lab.status, 'value') and lab.status.value == 3:
                lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
                lab_name = getattr(lab, 'name', f'Lab-{lab_id[:8]}')
                complete_labs.append({
                    'id': lab_id,
                    'name': lab_name
                })
        
        print(f"✅ Found {len(complete_labs)} complete labs on current server")
        return complete_labs
        
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        print("⚠️ Will analyze all cached labs instead")
        return []

def analyze_cached_labs_for_server(server_labs):
    """Analyze cached data only for labs that exist on current server"""
    
    cache_dir = "unified_cache/backtests"
    if not os.path.exists(cache_dir):
        print("❌ No cache directory found")
        return
    
    # Get server lab IDs
    server_lab_ids = {lab['id'] for lab in server_labs} if server_labs else set()
    
    # Group files by lab ID
    lab_data = defaultdict(list)
    
    print("🔍 Scanning cached backtest files...")
    for file_path in glob.glob(f"{cache_dir}/*.json"):
        filename = os.path.basename(file_path)
        lab_id = filename.split('_')[0]
        
        # Only process labs that are on current server
        if server_lab_ids and lab_id not in server_lab_ids:
            continue
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                lab_data[lab_id].append({
                    'file': filename,
                    'data': data
                })
        except Exception as e:
            print(f"⚠️ Error reading {filename}: {e}")
    
    if server_lab_ids:
        print(f"📊 Found {len(lab_data)} labs with cached data that exist on current server")
    else:
        print(f"📊 Found {len(lab_data)} labs with cached data")
    
    # Analyze each lab
    lab_analysis = []
    
    for lab_id, backtests in lab_data.items():
        # Get lab name from server data
        lab_name = "Unknown Lab"
        if server_labs:
            for lab in server_labs:
                if lab['id'] == lab_id:
                    lab_name = lab['name']
                    break
        
        print(f"\n🔬 Analyzing {lab_name} ({lab_id[:8]}...) - {len(backtests)} backtests")
        
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
                
                # Extract performance metrics from the correct structure
                pr_data = report.get('PR', {})
                t_data = report.get('T', {})
                o_data = report.get('O', {})
                
                roi = pr_data.get('ROI', 0)
                win_rate = t_data.get('WP', 0) * 100  # Convert to percentage
                total_trades = o_data.get('F', 0)  # F = Filled orders
                max_drawdown = abs(t_data.get('BL', 0))  # BL = Biggest Loss (negative)
                profit_factor = t_data.get('PF', 0)
                
                # Extract script and market info
                script_name = "ADX BB STOCH Scalper"  # Default from lab names
                # Extract full market name (e.g., BINANCEFUTURES_BTC_USDT_PERPETUAL)
                market_parts = report_key.split('_')
                if len(market_parts) >= 4:
                    market_tag = '_'.join(market_parts[1:])  # Skip the first part (AID)
                else:
                    market_tag = "UNKNOWN"
                
                # Calculate ROE using CLI v1 logic
                starting_balance = 10000.0  # Standard starting balance
                # ROE = (Net Profit / Starting Balance) * 100
                # Net Profit = ROI% * Starting Balance / 100
                net_profit = roi * starting_balance / 100 if roi > 0 else 0
                roe_percentage = (net_profit / starting_balance) * 100 if starting_balance > 0 else 0
                
                # Create analysis result
                result = {
                    'lab_id': lab_id,
                    'lab_name': lab_name,
                    'backtest_id': backtest['file'].split('_')[1].replace('.json', ''),
                    'script_name': script_name,
                    'market_tag': market_tag,
                    'roi_percentage': roi,
                    'roe_percentage': roe_percentage,
                    'win_rate': win_rate,
                    'total_trades': total_trades,
                    'max_drawdown': max_drawdown,
                    'profit_factor': profit_factor,
                    'realized_profits_usdt': net_profit,
                    'starting_balance': starting_balance
                }
                
                lab_results.append(result)
                
            except Exception as e:
                print(f"⚠️ Error analyzing backtest {backtest['file']}: {e}")
                continue
        
        if lab_results:
            # Sort by ROE (Return on Equity) - CLI v1 logic
            lab_results.sort(key=lambda x: x['roe_percentage'], reverse=True)
            
            lab_summary = {
                'lab_id': lab_id,
                'lab_name': lab_name,
                'total_backtests': len(lab_results),
                'top_backtests': lab_results[:5],  # Top 5
                'best_roe': lab_results[0]['roe_percentage'] if lab_results else 0,
                'best_win_rate': max(bt['win_rate'] for bt in lab_results) if lab_results else 0
            }
            
            lab_analysis.append(lab_summary)
            
            print(f"  ✅ Found {len(lab_results)} valid backtests")
            print(f"  🏆 Best ROE: {lab_summary['best_roe']:.2f}%")
            print(f"  🎯 Best Win Rate: {lab_summary['best_win_rate']:.2f}%")
    
    # Sort labs by best ROE
    lab_analysis.sort(key=lambda x: x['best_roe'], reverse=True)
    
    return lab_analysis

def create_bot_recommendations(lab_analysis):
    """Create bot creation recommendations for current server labs"""
    
    print(f"\n🤖 BOT CREATION RECOMMENDATIONS FOR CURRENT SERVER")
    print(f"=" * 70)
    
    bot_commands = []
    
    for lab in lab_analysis[:5]:  # Top 5 labs
        lab_id = lab['lab_id']
        lab_name = lab['lab_name']
        top_backtests = lab['top_backtests'][:2]  # Top 2 from each lab
        
        print(f"\n📋 {lab_name}")
        print(f"   Lab ID: {lab_id[:8]}... (Best ROE: {lab['best_roe']:.2f}%)")
        
        for i, backtest in enumerate(top_backtests, 1):
            # Create bot name following the naming convention
            bot_name = f"{lab_name} - {backtest['script_name']} - {backtest['roi_percentage']:.1f}% pop/gen {backtest['win_rate']:.0f}%"
            
            print(f"  {i}. {bot_name}")
            print(f"     ROE: {backtest['roe_percentage']:6.2f}% | Win Rate: {backtest['win_rate']:5.2f}% | Trades: {backtest['total_trades']}")
            print(f"     Market: {backtest['market_tag']}")
            
            # Create bot creation command
            command = {
                'lab_id': lab_id,
                'lab_name': lab_name,
                'backtest_id': backtest['backtest_id'],
                'bot_name': bot_name,
                'market_tag': backtest['market_tag'],
                'roi': backtest['roi_percentage'],
                'roe': backtest['roe_percentage'],
                'win_rate': backtest['win_rate'],
                'total_trades': backtest['total_trades']
            }
            bot_commands.append(command)
    
    # Save recommendations to file
    with open('current_server_bot_recommendations.json', 'w') as f:
        json.dump(bot_commands, f, indent=2)
    
    print(f"\n💾 Saved {len(bot_commands)} bot creation recommendations to 'current_server_bot_recommendations.json'")
    
    return bot_commands

if __name__ == "__main__":
    print("🚀 Starting analysis for current server labs...")
    
    # Get labs from current server
    server_labs = get_current_server_labs()
    
    if server_labs:
        print(f"\n📋 Current server labs:")
        for lab in server_labs:
            print(f"  - {lab['name']} ({lab['id'][:8]}...)")
    
    # Analyze cached data for server labs only
    lab_analysis = analyze_cached_labs_for_server(server_labs)
    
    if lab_analysis:
        print(f"\n📊 ANALYSIS SUMMARY FOR CURRENT SERVER")
        print(f"=" * 50)
        print(f"Total Labs Analyzed: {len(lab_analysis)}")
        
        for i, lab in enumerate(lab_analysis[:10], 1):  # Top 10 labs
            print(f"{i:2d}. {lab['lab_name'][:40]} - ROE: {lab['best_roe']:6.2f}% - Win Rate: {lab['best_win_rate']:5.2f}%")
        
        # Create bot recommendations
        bot_commands = create_bot_recommendations(lab_analysis)
        
        print(f"\n✅ Analysis complete!")
        print(f"📊 Analyzed {len(lab_analysis)} labs from current server")
        print(f"🤖 Generated {len(bot_commands)} bot creation recommendations")
        print(f"\n💡 Next steps:")
        print(f"   1. Review recommendations in 'current_server_bot_recommendations.json'")
        print(f"   2. Use mass bot creator with specific lab IDs from current server")
    else:
        print("❌ No valid lab data found in cache for current server")
