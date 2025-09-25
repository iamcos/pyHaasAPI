#!/usr/bin/env python3
"""
Analyze srv01 Backtest Data

This script connects to srv01, fetches all backtest data, and analyzes
the actual performance metrics to understand what we're working with.
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
        print(f"🔗 Establishing SSH tunnel to {server_name}...")
        
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
        await asyncio.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ SSH tunnel established (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ SSH tunnel failed: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to establish SSH tunnel: {e}")
        return None


async def cleanup_ssh_tunnel(process):
    """Clean up SSH tunnel"""
    try:
        if process and process.poll() is None:
            print("🧹 Cleaning up SSH tunnel...")
            process.terminate()
            process.wait(timeout=5)
            print("✅ SSH tunnel cleaned up")
    except Exception as e:
        print(f"⚠️ Error cleaning up SSH tunnel: {e}")


def analyze_backtest_data(backtests):
    """Analyze backtest data and show statistics"""
    if not backtests:
        print("No backtests to analyze")
        return
    
    print(f"\n📊 Analyzing {len(backtests)} backtests...")
    
    # Collect all metrics
    winrates = []
    roes = []
    max_drawdowns = []
    trades = []
    starting_balances = []
    
    for backtest in backtests:
        try:
            winrate = getattr(backtest, 'WinRate', 0) or 0
            roe = getattr(backtest, 'ROI', 0) or 0
            max_dd = getattr(backtest, 'MaxDrawdown', 0) or 0
            trade_count = getattr(backtest, 'TotalTrades', 0) or 0
            start_balance = getattr(backtest, 'StartingBalance', 0) or 0
            
            winrates.append(winrate)
            roes.append(roe)
            max_drawdowns.append(max_dd)
            trades.append(trade_count)
            starting_balances.append(start_balance)
            
        except Exception as e:
            print(f"Error analyzing backtest: {e}")
            continue
    
    if not winrates:
        print("No valid backtest data found")
        return
    
    # Calculate statistics
    def stats(data, name):
        if not data:
            return
        print(f"\n{name} Statistics:")
        print(f"  Count: {len(data)}")
        print(f"  Min: {min(data):.2f}")
        print(f"  Max: {max(data):.2f}")
        print(f"  Avg: {sum(data)/len(data):.2f}")
        print(f"  Median: {sorted(data)[len(data)//2]:.2f}")
    
    stats(winrates, "Win Rate (%)")
    stats(roes, "ROE (%)")
    stats(max_drawdowns, "Max Drawdown (%)")
    stats(trades, "Total Trades")
    stats(starting_balances, "Starting Balance (USDT)")
    
    # Show distribution
    print(f"\n📈 Performance Distribution:")
    
    # Win rate distribution
    high_wr = len([w for w in winrates if w >= 60])
    medium_wr = len([w for w in winrates if 40 <= w < 60])
    low_wr = len([w for w in winrates if w < 40])
    
    print(f"  Win Rate: {high_wr} high (60%+), {medium_wr} medium (40-60%), {low_wr} low (<40%)")
    
    # ROE distribution
    high_roe = len([r for r in roes if r >= 100])
    medium_roe = len([r for r in roes if 0 <= r < 100])
    negative_roe = len([r for r in roes if r < 0])
    
    print(f"  ROE: {high_roe} high (100%+), {medium_roe} medium (0-100%), {negative_roe} negative")
    
    # Drawdown distribution
    no_dd = len([d for d in max_drawdowns if d <= 0])
    low_dd = len([d for d in max_drawdowns if 0 < d <= 10])
    high_dd = len([d for d in max_drawdowns if d > 10])
    
    print(f"  Drawdown: {no_dd} none (0%), {low_dd} low (0-10%), {high_dd} high (>10%)")
    
    # Show top performers
    print(f"\n🏆 Top 10 Performers by ROE:")
    backtest_list = []
    for i, backtest in enumerate(backtests):
        try:
            roe = getattr(backtest, 'ROI', 0) or 0
            winrate = getattr(backtest, 'WinRate', 0) or 0
            max_dd = getattr(backtest, 'MaxDrawdown', 0) or 0
            trade_count = getattr(backtest, 'TotalTrades', 0) or 0
            script_name = getattr(backtest, 'script_name', 'Unknown')
            
            backtest_list.append({
                'index': i,
                'roe': roe,
                'winrate': winrate,
                'max_dd': max_dd,
                'trades': trade_count,
                'script_name': script_name
            })
        except Exception as e:
            continue
    
    # Sort by ROE
    backtest_list.sort(key=lambda x: x['roe'], reverse=True)
    
    for i, bt in enumerate(backtest_list[:10]):
        print(f"  {i+1}. {bt['roe']:.1f}% ROE, {bt['winrate']:.1f}% WR, {bt['max_dd']:.1f}% DD, {bt['trades']} trades - {bt['script_name']}")
    
    # Show qualifying backtests with different criteria
    print(f"\n🔍 Qualifying Backtests Analysis:")
    
    criteria = [
        ("55+ WR, no drawdown", lambda bt: bt['winrate'] >= 55 and bt['max_dd'] <= 0),
        ("50+ WR, no drawdown", lambda bt: bt['winrate'] >= 50 and bt['max_dd'] <= 0),
        ("60+ WR, <5% drawdown", lambda bt: bt['winrate'] >= 60 and bt['max_dd'] <= 5),
        ("50+ WR, <10% drawdown", lambda bt: bt['winrate'] >= 50 and bt['max_dd'] <= 10),
        ("40+ WR, <5% drawdown", lambda bt: bt['winrate'] >= 40 and bt['max_dd'] <= 5),
    ]
    
    for criteria_name, criteria_func in criteria:
        qualifying = [bt for bt in backtest_list if criteria_func(bt)]
        print(f"  {criteria_name}: {len(qualifying)} backtests")
        
        if qualifying:
            print(f"    Top 3:")
            for i, bt in enumerate(qualifying[:3]):
                print(f"      {i+1}. {bt['roe']:.1f}% ROE, {bt['winrate']:.1f}% WR, {bt['max_dd']:.1f}% DD - {bt['script_name']}")


async def main():
    """Main analysis function"""
    print("🚀 Analyzing srv01 Backtest Data")
    print("=" * 60)
    
    ssh_process = None
    
    try:
        # Step 1: Establish SSH tunnel
        ssh_process = await establish_ssh_tunnel("srv01")
        if not ssh_process:
            print("❌ Failed to establish SSH tunnel. Exiting.")
            return 1
        
        # Step 2: Connect to API
        print("\n🔐 Connecting to HaasOnline API...")
        
        # Get credentials
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        email = os.getenv('API_EMAIL')
        password = os.getenv('API_PASSWORD')
        
        if not email or not password:
            print("❌ API_EMAIL and API_PASSWORD environment variables are required")
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
            print("❌ Failed to connect to HaasOnline API")
            return 1
        
        print("✅ Connected successfully")
        executor = analyzer.executor
        
        # Step 3: Get labs
        print("\n📋 Getting labs...")
        labs = api.get_all_labs(executor)
        print(f"✅ Found {len(labs)} labs")
        
        # Step 4: Get backtests for each lab
        print("\n📊 Fetching backtest data...")
        all_backtests = []
        
        for lab in labs:
            lab_id = lab.lab_id
            lab_name = getattr(lab, 'lab_name', f'Lab {lab_id}')
            print(f"  📊 Lab: {lab_name}")
            
            try:
                from pyHaasAPI.model import GetBacktestResultRequest
                request = GetBacktestResultRequest(
                    lab_id=lab_id,
                    next_page_id=0,
                    page_lenght=1000
                )
                backtest_results = api.get_backtest_result(executor, request)
                
                if backtest_results and hasattr(backtest_results, '__iter__'):
                    lab_backtests = list(backtest_results)
                    all_backtests.extend(lab_backtests)
                    print(f"    ✅ {len(lab_backtests)} backtests")
                else:
                    print(f"    ⚠️ No backtests found")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                continue
        
        print(f"\n✅ Total backtests collected: {len(all_backtests)}")
        
        # Step 5: Analyze the data
        analyze_backtest_data(all_backtests)
        
        print("\n🎉 Analysis complete!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        # Clean up SSH tunnel
        if ssh_process:
            await cleanup_ssh_tunnel(ssh_process)


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
