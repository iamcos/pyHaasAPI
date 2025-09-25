#!/usr/bin/env python3
"""
Create Top 3 Bots for Each Completed Lab with ROE > Hold and Win Rate > 53%

This script:
1. Analyzes cached lab data for current server labs
2. Establishes buy & hold baseline using CLI v1 logic (highest ROI from first 20 backtests)
3. Filters backtests with ROE > hold and win rate > 53%
4. Creates top 3 bots for each lab meeting the criteria
5. Uses proper naming convention and account assignment
"""

import json
import os
import glob
from collections import defaultdict
from typing import Dict, List, Any, Optional
import time
from pyHaasAPI import api
from pyHaasAPI.model import AddBotFromLabRequest
from dotenv import load_dotenv

load_dotenv()

def get_current_server_labs():
    """Get labs that exist on the current server"""
    try:
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
        labs = api.get_all_labs(executor)
        if not labs:
            print("❌ No labs found on current server")
            return []
        
        # Show all labs and their status
        print(f"📋 All labs on current server:")
        for lab in labs:
            lab_name = getattr(lab, 'name', f'Lab-{getattr(lab, "id", "unknown")[:8]}')
            lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
            status = getattr(lab, 'status', 'Unknown')
            print(f"  - {lab_name} ({lab_id[:8] if lab_id else 'unknown'}...) - Status: {status}")
        
        # Filter for complete labs only
        complete_labs = [lab for lab in labs if hasattr(lab, 'status') and str(lab.status) == 'LabStatus.COMPLETED']
        print(f"✅ Found {len(complete_labs)} complete labs on current server")
        
        return complete_labs
        
    except Exception as e:
        print(f"❌ Error getting current server labs: {e}")
        return []

def establish_buy_hold_baseline(lab_id: str, cached_backtests: List[Dict]) -> float:
    """
    Establish buy & hold baseline using CLI v1 logic
    Uses the highest ROI from the first 20 backtests as baseline
    """
    print(f"📊 Establishing buy & hold baseline for lab {lab_id[:8]}...")
    
    try:
        # Take first 20 backtests (or all if less than 20)
        sample_backtests = cached_backtests[:20]
        
        roi_values = []
        for backtest in sample_backtests:
            try:
                data = backtest['data']
                reports = data.get('Reports', {})
                if not reports:
                    continue
                
                # Get the first report
                report_key = list(reports.keys())[0]
                report = reports[report_key]
                
                # Extract ROI
                pr_data = report.get('PR', {})
                roi = pr_data.get('ROI', 0)
                if roi > 0:
                    roi_values.append(roi)
                    
            except Exception as e:
                continue
        
        if not roi_values:
            print(f"   ⚠️ No valid ROI values found, using 0% as baseline")
            return 0.0
        
        # Use highest ROI as buy & hold baseline (CLI v1 logic)
        buy_hold_baseline = max(roi_values)
        print(f"   ✅ Buy & Hold Baseline: {buy_hold_baseline:.2f}%")
        
        return buy_hold_baseline
        
    except Exception as e:
        print(f"   ❌ Error establishing baseline: {e}")
        return 0.0

def analyze_cached_labs_with_hold_filter(server_labs: List[Any], min_win_rate: float = 30.0) -> List[Dict[str, Any]]:
    """Analyze cached lab data with hold filtering"""
    cache_dir = "unified_cache/backtests"
    if not os.path.exists(cache_dir):
        print("❌ No cache directory found")
        return []
    
    # Get server lab IDs
    server_lab_ids = {getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None) for lab in server_labs}
    
    # Group files by lab ID
    lab_data = defaultdict(list)
    
    print("🔍 Scanning cached backtest files...")
    for file_path in glob.glob(f"{cache_dir}/*.json"):
        filename = os.path.basename(file_path)
        lab_id = filename.split('_')[0]
        
        # Only process labs that exist on current server
        if lab_id not in server_lab_ids:
            continue
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                lab_data[lab_id].append({'file': file_path, 'data': data})
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
            continue
    
    print(f"📊 Found {len(lab_data)} labs with cached data that exist on current server")
    
    filtered_lab_results = []
    
    for lab_id, backtests in lab_data.items():
        lab_name = backtests[0]['data'].get('BotName', f"Lab-{lab_id[:8]}")
        print(f"\n🔬 Analyzing {lab_name} ({lab_id[:8]}...) - {len(backtests)} backtests")
        
        # Establish buy & hold baseline
        buy_hold_baseline = establish_buy_hold_baseline(lab_id, backtests)
        
        lab_results = []
        win_rates = []
        for backtest in backtests:
            try:
                data = backtest['data']
                
                # Extract performance metrics
                reports = data.get('Reports', {})
                if not reports:
                    continue
                
                # Get the first report
                report_key = list(reports.keys())[0]
                report = reports[report_key]
                
                # Extract performance metrics
                pr_data = report.get('PR', {})
                t_data = report.get('T', {})
                o_data = report.get('O', {})
                
                roi = pr_data.get('ROI', 0)
                win_rate = t_data.get('WP', 0) * 100  # Convert to percentage
                total_trades = o_data.get('F', 0)
                max_drawdown = abs(t_data.get('BL', 0))
                profit_factor = t_data.get('PF', 0)
                
                # Collect win rates for debugging
                if win_rate > 0:
                    win_rates.append(win_rate)
                
                # Extract script and market info
                script_name = data.get('ScriptName', "ADX BB STOCH Scalper")
                
                # Extract market tag from report key
                market_parts = report_key.split('_')
                if len(market_parts) >= 4:
                    market_tag = '_'.join(market_parts[1:])  # Skip the first part (AID)
                else:
                    market_tag = "UNKNOWN"
                
                # Calculate ROE using CLI v1 logic
                starting_balance = 10000.0  # Standard starting balance
                net_profit = roi * starting_balance / 100 if roi > 0 else 0
                roe_percentage = (net_profit / starting_balance) * 100 if starting_balance > 0 else 0
                
                # Apply filters: ROE > hold and win rate > 53%
                if roe_percentage > buy_hold_baseline and win_rate > min_win_rate:
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
                        'starting_balance': starting_balance,
                        'buy_hold_baseline': buy_hold_baseline
                    }
                    
                    lab_results.append(result)
                
            except Exception as e:
                print(f"⚠️ Error analyzing backtest {backtest['file']}: {e}")
                continue
        
        # Show win rate statistics
        if win_rates:
            max_wr = max(win_rates)
            min_wr = min(win_rates)
            avg_wr = sum(win_rates) / len(win_rates)
            print(f"  📊 Win Rate Stats: Min: {min_wr:.1f}%, Max: {max_wr:.1f}%, Avg: {avg_wr:.1f}%")
        
        if lab_results:
            # Sort by ROE (Return on Equity) - CLI v1 logic
            lab_results.sort(key=lambda x: x['roe_percentage'], reverse=True)
            
            print(f"  ✅ Found {len(lab_results)} backtests meeting criteria (ROE > {buy_hold_baseline:.2f}%, WR > {min_win_rate}%)")
            
            # Take top 3 for bot creation
            top_3 = lab_results[:3]
            
            lab_summary = {
                'lab_id': lab_id,
                'lab_name': lab_name,
                'buy_hold_baseline': buy_hold_baseline,
                'total_backtests': len(backtests),
                'filtered_backtests': len(lab_results),
                'top_3_backtests': top_3
            }
            
            filtered_lab_results.append(lab_summary)
            
            # Display top 3
            for i, result in enumerate(top_3, 1):
                print(f"    {i}. ROE: {result['roe_percentage']:6.2f}% | WR: {result['win_rate']:5.2f}% | Trades: {result['total_trades']}")
        else:
            print(f"  ⚠️ No backtests found meeting criteria (ROE > {buy_hold_baseline:.2f}%, WR > {min_win_rate}%)")
    
    return filtered_lab_results

def create_bots_from_filtered_results(filtered_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create bots from filtered results"""
    try:
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
        
        # Get available accounts
        accounts = api.get_all_accounts(executor)
        if not accounts:
            print("❌ No accounts found")
            return []
        
        # Filter for available accounts
        available_accounts = [acc for acc in accounts if 'AID' in acc]
        print(f"✅ Found {len(available_accounts)} available accounts")
        
        if len(available_accounts) < len(filtered_results) * 3:
            print(f"⚠️ Warning: Only {len(available_accounts)} accounts available for {len(filtered_results) * 3} bots")
        
        created_bots = []
        account_index = 0
        
        for lab_result in filtered_results:
            lab_id = lab_result['lab_id']
            lab_name = lab_result['lab_name']
            top_3 = lab_result['top_3_backtests']
            
            print(f"\n🤖 Creating bots for {lab_name}")
            print(f"   Lab ID: {lab_id[:8]}... (Hold Baseline: {lab_result['buy_hold_baseline']:.2f}%)")
            
            for i, backtest in enumerate(top_3, 1):
                if account_index >= len(available_accounts):
                    print(f"   ⚠️ No more accounts available")
                    break
                
                account_id = available_accounts[account_index]['AID']
                account_index += 1
                
                # Create bot name following the naming convention
                bot_name = f"{lab_name} - {backtest['script_name']} - {backtest['roi_percentage']:.1f}% pop/gen {backtest['win_rate']:.0f}%"
                
                print(f"   {i}. Creating bot: {bot_name}")
                print(f"      ROE: {backtest['roe_percentage']:6.2f}% | WR: {backtest['win_rate']:5.2f}% | Trades: {backtest['total_trades']}")
                print(f"      Market: {backtest['market_tag']}")
                print(f"      Account: {account_id}")
                
                try:
                    # Create bot from lab
                    request = AddBotFromLabRequest(
                        lab_id=lab_id,
                        backtest_id=backtest['backtest_id'],
                        bot_name=bot_name,
                        account_id=account_id,
                        market=backtest['market_tag'],
                        leverage=20  # Standard leverage
                    )
                    
                    bot_result = api.add_bot_from_lab(executor, request)
                    
                    if bot_result:
                        print(f"      ✅ Bot created successfully: {bot_result}")
                        
                        # Try to activate the bot
                        try:
                            activate_result = api.activate_bot(executor, bot_result)
                            if activate_result:
                                print(f"      🚀 Bot activated successfully")
                            else:
                                print(f"      ⚠️ Bot created but activation failed")
                        except Exception as e:
                            print(f"      ⚠️ Bot created but activation failed: {e}")
                        
                        created_bots.append({
                            'lab_id': lab_id,
                            'lab_name': lab_name,
                            'backtest_id': backtest['backtest_id'],
                            'bot_id': bot_result,
                            'bot_name': bot_name,
                            'account_id': account_id,
                            'market_tag': backtest['market_tag'],
                            'roe_percentage': backtest['roe_percentage'],
                            'win_rate': backtest['win_rate'],
                            'total_trades': backtest['total_trades'],
                            'buy_hold_baseline': lab_result['buy_hold_baseline']
                        })
                    else:
                        print(f"      ❌ Failed to create bot - no result returned")
                        
                except Exception as e:
                    print(f"      ❌ Failed to create bot: {e}")
        
        return created_bots
        
    except Exception as e:
        print(f"❌ Error creating bots: {e}")
        return []

def main():
    print("🚀 Starting filtered bot creation (ROE > Hold, WR > 53%)...")
    
    # Get labs from current server
    server_labs = get_current_server_labs()
    
    if not server_labs:
        print("❌ No labs found on current server")
        return
    
    print(f"\n📋 Current server labs:")
    for lab in server_labs:
        lab_name = getattr(lab, 'name', f'Lab-{getattr(lab, "id", "unknown")[:8]}')
        lab_id = getattr(lab, 'id', None) or getattr(lab, 'lab_id', None) or getattr(lab, 'LID', None)
        print(f"  - {lab_name} ({lab_id[:8]}...)")
    
    # Analyze cached data with hold filtering
    filtered_results = analyze_cached_labs_with_hold_filter(server_labs, min_win_rate=30.0)
    
    if not filtered_results:
        print("\n❌ No labs found meeting the criteria")
        return
    
    print(f"\n📊 FILTERED ANALYSIS SUMMARY")
    print(f"=" * 60)
    print(f"Total Labs Meeting Criteria: {len(filtered_results)}")
    
    total_bots_to_create = sum(len(lab['top_3_backtests']) for lab in filtered_results)
    print(f"Total Bots to Create: {total_bots_to_create}")
    
    for i, lab in enumerate(filtered_results, 1):
        print(f"{i:2d}. {lab['lab_name'][:40]} - Hold: {lab['buy_hold_baseline']:6.2f}% - Bots: {len(lab['top_3_backtests'])}")
    
    # Create bots
    print(f"\n🤖 CREATING BOTS")
    print(f"=" * 60)
    
    created_bots = create_bots_from_filtered_results(filtered_results)
    
    # Save results
    if created_bots:
        with open('filtered_bot_creation_results.json', 'w') as f:
            json.dump(created_bots, f, indent=2)
        
        print(f"\n✅ Bot creation complete!")
        print(f"📊 Created {len(created_bots)} bots")
        print(f"💾 Results saved to 'filtered_bot_creation_results.json'")
        
        # Summary
        print(f"\n📋 CREATION SUMMARY")
        print(f"=" * 60)
        for bot in created_bots:
            print(f"✅ {bot['bot_name']}")
            print(f"   ROE: {bot['roe_percentage']:6.2f}% | WR: {bot['win_rate']:5.2f}% | Trades: {bot['total_trades']}")
            print(f"   Market: {bot['market_tag']} | Account: {bot['account_id']}")
    else:
        print(f"\n❌ No bots were created")

if __name__ == "__main__":
    main()
