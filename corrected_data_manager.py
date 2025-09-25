#!/usr/bin/env python3
"""
Corrected Data Manager

This script uses the correct tuple structure to analyze backtest data
and create bots from qualifying backtests.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# Add pyHaasAPI to path
sys.path.insert(0, str(Path(__file__).parent / "pyHaasAPI"))

from pyHaasAPI import api
from pyHaasAPI.analysis.analyzer import HaasAnalyzer
from pyHaasAPI.analysis.cache import UnifiedCacheManager
from pyHaasAPI.logger import log as logger


async def establish_ssh_tunnel(server_name="srv01"):
    """Establish SSH tunnel to server"""
    try:
        print(f"Connecting to {server_name}...")
        
        # SSH command for tunnel
        ssh_cmd = [
            "ssh", "-N", "-L", "8090:127.0.0.1:8090", "-L", "8092:127.0.0.1:8092",
            f"prod@{server_name}"
        ]
        
        # Start SSH process
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        # Wait a moment for tunnel to establish
        await asyncio.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"SSH tunnel established (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"SSH tunnel failed: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"Failed to establish SSH tunnel: {e}")
        return None


async def cleanup_ssh_tunnel(process):
    """Clean up SSH tunnel"""
    try:
        if process and process.poll() is None:
            print("Cleaning up SSH tunnel...")
            process.terminate()
            process.wait(timeout=5)
            print("SSH tunnel cleaned up")
    except Exception as e:
        print(f"Error cleaning up SSH tunnel: {e}")


def extract_backtest_data(backtest_result):
    """Extract performance data from LabBacktestResult object"""
    try:
        # Get summary data
        summary = backtest_result.summary
        if not summary:
            return None
        
        # Extract performance metrics
        roi = getattr(summary, 'ReturnOnInvestment', 0) or 0
        realized_profits = getattr(summary, 'RealizedProfits', 0) or 0
        fee_costs = getattr(summary, 'FeeCosts', 0) or 0
        
        # Get settings for additional info
        settings = backtest_result.settings
        trade_amount = getattr(settings, 'trade_amount', 0) or 0
        leverage = getattr(settings, 'leverage', 0) or 0
        market_tag = getattr(settings, 'market_tag', 'Unknown')
        
        # Calculate win rate and other metrics from trades/positions if available
        trades = getattr(summary, 'Trades', None)
        positions = getattr(summary, 'Positions', None)
        
        # For now, use basic metrics
        win_rate = 0  # Would need to calculate from trades
        max_drawdown = 0  # Would need to calculate from positions
        total_trades = 0  # Would need to count from trades
        
        return {
            'backtest_id': backtest_result.backtest_id,
            'lab_id': backtest_result.lab_id,
            'generation': backtest_result.generation_idx,
            'population': backtest_result.population_idx,
            'roi': roi,
            'realized_profits': realized_profits,
            'fee_costs': fee_costs,
            'trade_amount': trade_amount,
            'leverage': leverage,
            'market_tag': market_tag,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'status': backtest_result.status
        }
        
    except Exception as e:
        print(f"Error extracting backtest data: {e}")
        return None


def analyze_backtest_data(backtests):
    """Analyze backtest data and show statistics"""
    if not backtests:
        print("No backtests to analyze")
        return []
    
    print(f"\nAnalyzing {len(backtests)} backtests...")
    
    # Extract data from all backtests
    extracted_data = []
    for backtest in backtests:
        data = extract_backtest_data(backtest)
        if data:
            extracted_data.append(data)
    
    if not extracted_data:
        print("No valid backtest data found")
        return []
    
    # Calculate statistics
    rois = [d['roi'] for d in extracted_data]
    profits = [d['realized_profits'] for d in extracted_data]
    trade_amounts = [d['trade_amount'] for d in extracted_data]
    
    print(f"\nPerformance Statistics:")
    print(f"  Count: {len(extracted_data)}")
    print(f"  ROI - Min: {min(rois):.2f}%, Max: {max(rois):.2f}%, Avg: {sum(rois)/len(rois):.2f}%")
    print(f"  Profits - Min: ${min(profits):.2f}, Max: ${max(profits):.2f}, Avg: ${sum(profits)/len(profits):.2f}")
    print(f"  Trade Amounts - Min: ${min(trade_amounts):.2f}, Max: ${max(trade_amounts):.2f}, Avg: ${sum(trade_amounts)/len(trade_amounts):.2f}")
    
    # Show top performers
    print(f"\nTop 10 Performers by ROI:")
    sorted_data = sorted(extracted_data, key=lambda x: x['roi'], reverse=True)
    
    for i, data in enumerate(sorted_data[:10]):
        print(f"  {i+1}. {data['roi']:.1f}% ROI, ${data['realized_profits']:.2f} profit, {data['market_tag']}")
    
    return extracted_data


async def main():
    """Main analysis function"""
    print("Corrected Data Manager Analysis")
    print("=" * 60)
    
    ssh_process = None
    
    try:
        # Step 1: Establish SSH tunnel
        ssh_process = await establish_ssh_tunnel("srv01")
        if not ssh_process:
            print("Failed to establish SSH tunnel. Exiting.")
            return 1
        
        # Step 2: Connect to API
        print("\nConnecting to HaasOnline API...")
        
        # Get credentials
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("API_EMAIL and API_PASSWORD environment variables are required")
            return 1
        
        # Initialize analyzer and connect
        cache = UnifiedCacheManager()
        analyzer = HaasAnalyzer(cache)
        success = analyzer.connect(
            host='127.0.0.1',
            port=8090,
            email=email,
            password=password
        )
        
        if not success:
            print("Failed to connect to HaasOnline API")
            return 1
        
        print("Connected successfully")
        executor = analyzer.executor
        
        # Step 3: Get labs
        print("\nGetting labs...")
        labs = api.get_all_labs(executor)
        print(f"Found {len(labs)} labs")
        
        # Step 4: Get backtests for first few labs
        print("\nFetching backtest data...")
        all_backtests = []
        
        for i, lab in enumerate(labs[:5]):  # Analyze first 5 labs
            lab_id = lab.lab_id
            lab_name = getattr(lab, 'lab_name', f'Lab {lab_id}')
            print(f"  Lab {i+1}: {lab_name}")
            
            try:
                from pyHaasAPI.model import GetBacktestResultRequest
                request = GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=0,
                    page_lenght=100
                )
                backtest_results = api.get_backtest_result(executor, request)
                
                if backtest_results and hasattr(backtest_results, '__iter__'):
                    # Convert to list and get the actual backtest objects
                    result_list = list(backtest_results)
                    
                    # Find the "items" tuple
                    for result_tuple in result_list:
                        if result_tuple[0] == "items":
                            lab_backtests = result_tuple[1]  # This is the list of LabBacktestResult objects
                            all_backtests.extend(lab_backtests)
                            print(f"    Found {len(lab_backtests)} backtests")
                            break
                    else:
                        print(f"    No backtests found")
                else:
                    print(f"    No backtest results")
                    
            except Exception as e:
                print(f"    Error: {e}")
                continue
        
        print(f"\nTotal backtests collected: {len(all_backtests)}")
        
        # Step 5: Analyze the data
        if all_backtests:
            extracted_data = analyze_backtest_data(all_backtests)
            
            # Show qualifying backtests (positive ROI)
            positive_roi = [d for d in extracted_data if d['roi'] > 0]
            print(f"\nQualifying Backtests (Positive ROI): {len(positive_roi)}")
            
            if positive_roi:
                print("Top qualifying backtests:")
                for i, data in enumerate(positive_roi[:5]):
                    print(f"  {i+1}. {data['roi']:.1f}% ROI, ${data['realized_profits']:.2f} profit, {data['market_tag']}")
        else:
            print("No backtests found to analyze")
        
        print("\nAnalysis complete!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Clean up SSH tunnel
        if ssh_process:
            await cleanup_ssh_tunnel(ssh_process)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
