#!/usr/bin/env python3
"""
Analyze backtest data with runtime analytics and WFO metrics
"""

import json
import csv
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our API modules
from pyHaasAPI import api
from pyHaasAPI.model import GetBacktestResultRequest
from pyHaasAPI.backtest_object import BacktestObject

def parse_backtest_string(backtest_str: str) -> Dict[str, Any]:
    """Parse a backtest string representation into a dictionary"""
    try:
        data = {}
        
        # Extract backtest_id
        if "backtest_id='" in backtest_str:
            start = backtest_str.find("backtest_id='") + 13
            end = backtest_str.find("'", start)
            data['backtest_id'] = backtest_str[start:end]
        
        # Extract generation_idx
        if "generation_idx=" in backtest_str:
            start = backtest_str.find("generation_idx=") + 15
            end = backtest_str.find(" ", start)
            data['generation_idx'] = int(backtest_str[start:end])
        
        # Extract population_idx
        if "population_idx=" in backtest_str:
            start = backtest_str.find("population_idx=") + 15
            end = backtest_str.find(" ", start)
            data['population_idx'] = int(backtest_str[start:end])
        
        # Extract parameters
        if "parameters={" in backtest_str:
            start = backtest_str.find("parameters={") + 12
            end = backtest_str.find("} runtime=", start)
            if end == -1:
                end = backtest_str.find("} summary=", start)
            if end != -1:
                params_str = backtest_str[start:end]
                params = {}
                parts = params_str.split("'")
                for i in range(1, len(parts), 4):
                    if i + 2 < len(parts):
                        key = parts[i]
                        value = parts[i + 2]
                        params[key] = value
                data['parameters'] = params
        
        # Extract settings information
        if "settings=HaasScriptSettings(" in backtest_str:
            start = backtest_str.find("settings=HaasScriptSettings(") + 29
            end = backtest_str.find(") parameters=", start)
            if end != -1:
                settings_str = backtest_str[start:end]
                # Extract interval
                if "interval=" in settings_str:
                    interval_start = settings_str.find("interval=") + 9
                    interval_end = settings_str.find(" ", interval_start)
                    if interval_end == -1:
                        interval_end = settings_str.find(",", interval_start)
                    if interval_end != -1:
                        interval_str = settings_str[interval_start:interval_end]
                        if interval_str.endswith(','):
                            interval_str = interval_str[:-1]
                        try:
                            data['interval'] = int(interval_str)
                        except ValueError:
                            pass
                
                # Extract trade_amount
                if "trade_amount=" in settings_str:
                    amount_start = settings_str.find("trade_amount=") + 13
                    amount_end = settings_str.find(" ", amount_start)
                    if amount_end == -1:
                        amount_end = settings_str.find(",", amount_start)
                    if amount_end != -1:
                        amount_str = settings_str[amount_start:amount_end]
                        if amount_str.endswith(','):
                            amount_str = amount_str[:-1]
                        try:
                            data['trade_amount'] = float(amount_str)
                        except ValueError:
                            pass
        
        return data
    except Exception as e:
        print(f"Error parsing backtest string: {e}")
        return {}

def fetch_backtest_runtime_data(executor, lab_id: str, backtest_id: str) -> Optional[Dict[str, Any]]:
    """Fetch runtime data for a specific backtest"""
    try:
        # Get full runtime data
        runtime_data = api.get_full_backtest_runtime_data(executor, lab_id, backtest_id)
        
        # Create BacktestObject to get analytics
        backtest_obj = BacktestObject(executor, lab_id, backtest_id)
        
        # Extract analytics
        analytics = {}
        
        if backtest_obj.runtime:
            analytics.update({
                'total_trades': backtest_obj.runtime.total_trades,
                'winning_trades': backtest_obj.runtime.winning_trades,
                'losing_trades': backtest_obj.runtime.losing_trades,
                'win_rate': backtest_obj.runtime.win_rate,
                'total_profit': backtest_obj.runtime.total_profit,
                'max_drawdown': backtest_obj.runtime.max_drawdown,
                'sharpe_ratio': backtest_obj.runtime.sharpe_ratio,
                'profit_factor': backtest_obj.runtime.profit_factor,
            })
        
        # Extract PC value (Buy & Hold %) from runtime data
        pc_value = 0.0
        if hasattr(runtime_data, 'raw_data') and runtime_data.raw_data:
            try:
                # Find the report key
                report_key = None
                if hasattr(runtime_data, 'Reports') and runtime_data.Reports:
                    # Get the first report key
                    report_key = list(runtime_data.Reports.keys())[0]
                
                if report_key and 'Reports' in runtime_data.raw_data:
                    if report_key in runtime_data.raw_data['Reports']:
                        if 'PR' in runtime_data.raw_data['Reports'][report_key]:
                            pc_value = runtime_data.raw_data['Reports'][report_key]['PR'].get('PC', 0.0)
            except Exception as e:
                print(f"Error extracting PC value: {e}")
        
        analytics['pc_value'] = pc_value
        
        # Calculate ROI if we have the data
        if 'total_profit' in analytics and analytics['total_profit'] is not None:
            # Assuming initial balance of 10,000 USDT (based on your setup)
            initial_balance = 10000.0
            analytics['roi_percentage'] = (analytics['total_profit'] / initial_balance) * 100
            analytics['beats_buy_hold'] = analytics['roi_percentage'] >= pc_value
        else:
            analytics['roi_percentage'] = None
            analytics['beats_buy_hold'] = None
        
        return analytics
        
    except Exception as e:
        print(f"Error fetching runtime data for {backtest_id}: {e}")
        return None

def analyze_backtest_data_with_analytics(output_dir: str, sample_size: int = 20):
    """Analyze the backtest data with runtime analytics"""
    
    # Initialize API connection
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("API_PORT", 8090))
    api_email = os.getenv("API_EMAIL")
    api_password = os.getenv("API_PASSWORD")

    if not api_email or not api_password:
        print("API_EMAIL and API_PASSWORD must be set in .env file")
        return

    print(f"Connecting to HaasOnline API: {api_host}:{api_port}")

    # Create API connection
    haas_api = api.RequestsExecutor(
        host=api_host,
        port=api_port,
        state=api.Guest()
    )

    # Authenticate
    executor = haas_api.authenticate(api_email, api_password)
    print("Successfully connected to HaasOnline API")
    
    # Read the backtests list
    backtests_list_file = os.path.join(output_dir, "backtests_list.json")
    if not os.path.exists(backtests_list_file):
        print(f"Backtests list file not found: {backtests_list_file}")
        return
    
    with open(backtests_list_file, 'r') as f:
        backtests_list = json.load(f)
    
    print(f"Found {len(backtests_list)} backtests")
    
    # Parse basic data for all backtests
    parsed_backtests = []
    for i, backtest_str in enumerate(backtests_list):
        data = parse_backtest_string(backtest_str)
        if data:
            parsed_backtests.append(data)
    
    print(f"Successfully parsed {len(parsed_backtests)} backtests")
    
    # Take a sample for detailed analysis
    sample_backtests = parsed_backtests[:sample_size]
    lab_id = "caed4df4-bcf9-4d4c-a8af-a51af6b7982e"
    
    # Fetch runtime data for sample
    print(f"\nFetching runtime data for {len(sample_backtests)} backtests...")
    backtests_with_analytics = []
    
    for i, backtest in enumerate(sample_backtests):
        print(f"Processing {i+1}/{len(sample_backtests)}: {backtest.get('backtest_id', 'unknown')}")
        
        # Fetch runtime analytics
        analytics = fetch_backtest_runtime_data(executor, lab_id, backtest['backtest_id'])
        
        # Combine basic data with analytics
        combined_data = {**backtest}
        if analytics:
            combined_data.update(analytics)
        
        backtests_with_analytics.append(combined_data)
        
        # Small delay to avoid overwhelming the API
        time.sleep(0.1)
    
    # Create comprehensive CSV report
    csv_file = os.path.join(output_dir, "backtests_with_analytics.csv")
    
    # Define CSV headers
    headers = [
        'backtest_id', 'generation_idx', 'population_idx', 'interval', 'trade_amount',
        'rising_length', 'vwap_window', 'stop_loss_percentage', 'stop_loss_shrinkage',
        'total_trades', 'winning_trades', 'losing_trades', 'win_rate', 'total_profit',
        'max_drawdown', 'sharpe_ratio', 'profit_factor', 'roi_percentage', 'pc_value', 'beats_buy_hold'
    ]
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for backtest in backtests_with_analytics:
            row = {
                'backtest_id': backtest.get('backtest_id', ''),
                'generation_idx': backtest.get('generation_idx', ''),
                'population_idx': backtest.get('population_idx', ''),
                'interval': backtest.get('interval', ''),
                'trade_amount': backtest.get('trade_amount', ''),
                'rising_length': backtest.get('parameters', {}).get('3-3-21-26.Rising Length', ''),
                'vwap_window': backtest.get('parameters', {}).get('4-4-19-24.VWAP Window', ''),
                'stop_loss_percentage': backtest.get('parameters', {}).get('6-6-27-32.Stop Loss Percentage', ''),
                'stop_loss_shrinkage': backtest.get('parameters', {}).get('7-7-26-31.Stop Loss Shrinkage', ''),
                'total_trades': backtest.get('total_trades', ''),
                'winning_trades': backtest.get('winning_trades', ''),
                'losing_trades': backtest.get('losing_trades', ''),
                'win_rate': backtest.get('win_rate', ''),
                'total_profit': backtest.get('total_profit', ''),
                'max_drawdown': backtest.get('max_drawdown', ''),
                'sharpe_ratio': backtest.get('sharpe_ratio', ''),
                'profit_factor': backtest.get('profit_factor', ''),
                'roi_percentage': backtest.get('roi_percentage', ''),
                'pc_value': backtest.get('pc_value', ''),
                'beats_buy_hold': backtest.get('beats_buy_hold', '')
            }
            writer.writerow(row)
    
    print(f"Comprehensive CSV report created: {csv_file}")
    
    # Print summary statistics
    print("\n=== ANALYTICS SUMMARY ===")
    
    # Filter backtests with valid analytics
    valid_analytics = [bt for bt in backtests_with_analytics if bt.get('roi_percentage') is not None]
    
    if valid_analytics:
        print(f"Backtests with valid analytics: {len(valid_analytics)}")
        
        # ROI statistics
        rois = [bt['roi_percentage'] for bt in valid_analytics]
        print(f"ROI range: {min(rois):.2f}% to {max(rois):.2f}%")
        print(f"Average ROI: {sum(rois)/len(rois):.2f}%")
        
        # Buy & Hold comparison
        beats_buy_hold = [bt for bt in valid_analytics if bt.get('beats_buy_hold')]
        print(f"Backtests beating buy & hold: {len(beats_buy_hold)}/{len(valid_analytics)} ({len(beats_buy_hold)/len(valid_analytics)*100:.1f}%)")
        
        # Top performers
        sorted_by_roi = sorted(valid_analytics, key=lambda x: x.get('roi_percentage', 0), reverse=True)
        print(f"\n=== TOP 5 PERFORMERS BY ROI ===")
        for i, backtest in enumerate(sorted_by_roi[:5]):
            print(f"{i+1}. {backtest.get('backtest_id', 'Unknown')[:8]}... - ROI: {backtest.get('roi_percentage', 0):.2f}%, Win Rate: {backtest.get('win_rate', 0):.1f}%, Trades: {backtest.get('total_trades', 0)}")
        
        # Win rate statistics
        win_rates = [bt['win_rate'] for bt in valid_analytics if bt.get('win_rate') is not None]
        if win_rates:
            print(f"\nWin Rate range: {min(win_rates):.1f}% to {max(win_rates):.1f}%")
            print(f"Average Win Rate: {sum(win_rates)/len(win_rates):.1f}%")
        
        # Trade count statistics
        trade_counts = [bt['total_trades'] for bt in valid_analytics if bt.get('total_trades') is not None]
        if trade_counts:
            print(f"\nTrade Count range: {min(trade_counts)} to {max(trade_counts)}")
            print(f"Average Trade Count: {sum(trade_counts)/len(trade_counts):.1f}")
    
    else:
        print("No valid analytics data found")

if __name__ == "__main__":
    # Find the output directory in cache folder
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        print("No cache directory found")
        exit(1)
    
    output_dirs = [d for d in os.listdir(cache_dir) if d.startswith("lab_backtests_") and os.path.isdir(os.path.join(cache_dir, d))]
    
    if not output_dirs:
        print("No backtest output directory found in cache")
        exit(1)
    
    # Use the most recent directory
    output_dir = os.path.join(cache_dir, sorted(output_dirs)[-1])
    print(f"Using output directory: {output_dir}")
    
    # Analyze with analytics (sample size of 20 for reasonable processing time)
    analyze_backtest_data_with_analytics(output_dir, sample_size=20)
