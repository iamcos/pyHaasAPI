#!/usr/bin/env python3
"""
Debug Backtest Structure

This script examines the actual structure of backtest objects to understand
what data is available and how to access it properly.
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


def debug_backtest_object(backtest, index=0):
    """Debug a single backtest object to understand its structure"""
    print(f"\n🔍 Debugging Backtest {index}:")
    print(f"  Type: {type(backtest)}")
    print(f"  Class: {backtest.__class__.__name__}")
    
    # Get all attributes
    attrs = dir(backtest)
    print(f"  Attributes ({len(attrs)}): {attrs}")
    
    # Try to get common performance metrics
    metrics = [
        'WinRate', 'ROI', 'MaxDrawdown', 'TotalTrades', 'StartingBalance',
        'win_rate', 'roi', 'max_drawdown', 'total_trades', 'starting_balance',
        'RealizedProfits', 'realized_profits', 'ProfitFactor', 'profit_factor',
        'SharpeRatio', 'sharpe_ratio', 'ScriptName', 'script_name',
        'ScriptId', 'script_id', 'MarketTag', 'market_tag'
    ]
    
    print(f"\n  Performance Metrics:")
    for metric in metrics:
        try:
            value = getattr(backtest, metric, None)
            print(f"    {metric}: {value}")
        except Exception as e:
            print(f"    {metric}: Error - {e}")
    
    # Try to convert to dict if possible
    try:
        if hasattr(backtest, 'model_dump'):
            data = backtest.model_dump()
            print(f"\n  Model Dump Keys: {list(data.keys())}")
            for key, value in data.items():
                if isinstance(value, (int, float, str)) and value != 0:
                    print(f"    {key}: {value}")
        elif hasattr(backtest, '__dict__'):
            data = backtest.__dict__
            print(f"\n  Dict Keys: {list(data.keys())}")
            for key, value in data.items():
                if isinstance(value, (int, float, str)) and value != 0:
                    print(f"    {key}: {value}")
    except Exception as e:
        print(f"  Error getting data: {e}")


async def main():
    """Main debug function"""
    print("🚀 Debugging srv01 Backtest Structure")
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
        
        # Step 3: Get first lab and its backtests
        print("\n📋 Getting first lab...")
        labs = api.get_all_labs(executor)
        if not labs:
            print("❌ No labs found")
            return 1
        
        first_lab = labs[0]
        lab_id = first_lab.lab_id
        lab_name = getattr(first_lab, 'lab_name', f'Lab {lab_id}')
        print(f"✅ Using lab: {lab_name}")
        
        # Step 4: Get backtests for this lab
        print(f"\n📊 Getting backtests for lab {lab_id}...")
        
        from pyHaasAPI.model import GetBacktestResultRequest
        request = GetBacktestResultRequest(
            lab_id=lab_id,
            next_page_id=0,
            page_lenght=10
        )
        backtest_results = api.get_backtest_result(executor, request)
        
        if not backtest_results:
            print("❌ No backtest results found")
            return 1
        
        print(f"✅ Got backtest results: {type(backtest_results)}")
        
        # Step 5: Debug the structure
        if hasattr(backtest_results, '__iter__'):
            backtest_list = list(backtest_results)
            print(f"✅ Converted to list: {len(backtest_list)} items")
            
            if backtest_list:
                # Debug first few backtests
                for i, backtest in enumerate(backtest_list[:3]):
                    debug_backtest_object(backtest, i)
            else:
                print("❌ Empty backtest list")
        else:
            print(f"❌ Backtest results not iterable: {type(backtest_results)}")
            debug_backtest_object(backtest_results, 0)
        
        print("\n🎉 Debug complete!")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
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
